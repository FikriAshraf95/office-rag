"""Endpoint 13: ask a question, answer over SSE (SPEC-08 §6, SPEC-05 §6)."""

import asyncio
import contextlib
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Annotated

import anyio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.answering.service import Event, Turn, answer_stream
from app.api.errors import ApiError
from app.api.schemas import SSE_EVENTS, ChatIn
from app.db.engine import get_session
from app.retrieval.search import MAX_QUERY_CHARS
from app.security.identity import CurrentUser

router = APIRouter(prefix="/api/v1", tags=["chat"])

Session = Annotated[AsyncSession, Depends(get_session)]
PING_SECONDS = 15.0
PING = ": ping\n\n"


def format_event(event: Event) -> str:
    model = SSE_EVENTS[event.name].model_validate(event.data)
    return f"event: {event.name}\ndata: {model.model_dump_json(by_alias=True, exclude_unset=True)}\n\n"


async def _next(events: AsyncGenerator[Event]) -> Event:
    return await anext(events)


async def sse(events: AsyncGenerator[Event], ping_seconds: float = PING_SECONDS) -> AsyncIterator[str]:
    """Frames events and sends a keep-alive comment while waiting. When the client goes away, the pending
    step is cancelled and the event stream closed, which stops the model stream."""
    pending: asyncio.Task[Event] | None = None
    try:
        while True:
            if pending is None:
                pending = asyncio.create_task(_next(events))
            done, _ = await asyncio.wait({pending}, timeout=ping_seconds)
            if not done:
                yield PING
                continue
            step, pending = pending, None
            try:
                event = step.result()
            except StopAsyncIteration:
                return
            yield format_event(event)
    finally:
        with anyio.CancelScope(shield=True):
            if pending is not None:
                pending.cancel()
                with contextlib.suppress(BaseException):
                    await pending
            await events.aclose()


@router.post(
    "/chat",
    response_class=StreamingResponse,
    responses={
        200: {"content": {"text/event-stream": {}}, "description": "SSE: meta, sources, delta*, done | error"}
    },
)
async def chat(body: ChatIn, session: Session, user: CurrentUser) -> StreamingResponse:
    question = body.question.strip()
    if len(question) > MAX_QUERY_CHARS:
        raise ApiError(
            422, "query_too_long", f"Keep the question under {MAX_QUERY_CHARS} characters and try again."
        )
    if not question:
        raise ApiError(
            422, "validation_failed", "Some fields are not valid.", errors={"question": ["Type a question."]}
        )
    history = [Turn(t.question, t.answer) for t in body.history]
    return StreamingResponse(
        sse(answer_stream(session, question, user, history)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
