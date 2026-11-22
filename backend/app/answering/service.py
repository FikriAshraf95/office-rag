"""Answering (SPEC-05): one question in, a stream of events out, one `questions` row written.

`answer_stream` yields `meta → sources → delta* → done`, or ends with `error`. The first 16 characters of the
model reply are buffered so the NOT_FOUND sentinel is never streamed. Retries and the fallback model are
used only before the first delta reaches the client. Closing or cancelling the stream stops the model stream
and records `error_code = 'cancelled'`.
"""

import time
import uuid
from collections.abc import AsyncGenerator, Sequence
from contextlib import aclosing
from dataclasses import dataclass, field
from typing import Any, Literal, cast

import anyio
import structlog
from sqlalchemy import insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.answering.citations import validate
from app.answering.prompt import Prompt, Turn, build_prompt
from app.answering.scope import about_assistant, scope_text
from app.config import Settings, get_settings
from app.db.models import Question
from app.ingestion.metadata import detect_language
from app.providers.base import ChatDelta, Role, TokenUsage
from app.providers.errors import ProviderError, user_message
from app.providers.registry import Providers, get_providers
from app.providers.usage import LATEST_BALANCES
from app.retrieval.search import MAX_QUERY_CHARS, Hit, search
from app.security.identity import Identity

__all__ = ["Event", "Turn", "answer_stream"]

log = structlog.get_logger()

NOT_FOUND = "NOT_FOUND"
SENTINEL_BUFFER = 16
ANSWER_MAX_TOKENS = 1024
ANSWER_TEMPERATURE = 0.1
SNIPPET_CHARS = 300
NOT_FOUND_TEMPLATE = "I couldn't find this in the documents I have access to. Please contact {contact}."
NOT_FOUND_TEMPLATE_MS = (
    "Saya tidak menjumpai maklumat ini dalam dokumen yang boleh saya akses. Sila hubungi {contact}."
)
FALLBACK_CONTACT = "HR"
INTERNAL_DETAIL = "Something went wrong on our side. Try again; if it keeps happening, tell the admin."
# Provider codes that reach the client as `internal` (SPEC-06 §5: handled inside the app).
INTERNAL_PROVIDER_CODES = {"context_too_long", "request_too_large"}

EventName = Literal["meta", "sources", "delta", "done", "error"]


@dataclass(frozen=True, slots=True)
class Event:
    """One SSE event; `data` uses snake_case keys (the API renders camelCase)."""

    name: EventName
    data: dict[str, Any]


@dataclass(slots=True)
class _Run:
    """What the `questions` row will record."""

    id: uuid.UUID
    started: float
    malay: bool
    sources: list[dict[str, Any]] = field(default_factory=list)
    answer: str | None = None
    found: bool | None = None
    cited: list[int] = field(default_factory=list)
    model: str | None = None
    first_token_ms: int | None = None
    latency_ms: int | None = None
    error_code: str | None = None
    finished: bool = False

    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self.started) * 1000)

    def delta(self, text: str) -> Event:
        if self.first_token_ms is None:
            self.first_token_ms = self.elapsed_ms()
        return Event("delta", {"text": text})

    def fail(self, code: str) -> Event:
        self.answer, self.found, self.cited, self.error_code = None, None, [], code
        self.latency_ms, self.finished = self.elapsed_ms(), True
        if code in INTERNAL_PROVIDER_CODES or code == "internal":
            return Event("error", {"code": "internal", "detail": INTERNAL_DETAIL})
        return Event("error", {"code": code, "detail": user_message(code)})

    def done(self, usage: TokenUsage, final_text: str | None) -> Event:
        self.latency_ms, self.finished = self.elapsed_ms(), True
        data: dict[str, Any] = {
            "found": bool(self.found),
            "cited": self.cited,
            "model": self.model,
            "usage": {"prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens},
            "latency_ms": self.latency_ms,
            "first_token_ms": self.first_token_ms,
        }
        if final_text is not None:
            data["final_text"] = final_text
        return Event("done", data)


def not_found_text(malay: bool, department: str | None, contacts: dict[str, str]) -> str:
    """SPEC-05 §5: the contact for the top document's department, else the default."""
    by_department = {k.lower(): v for k, v in contacts.items()}
    contact = by_department.get((department or "").lower()) or by_department.get("default", FALLBACK_CONTACT)
    return (NOT_FOUND_TEMPLATE_MS if malay else NOT_FOUND_TEMPLATE).format(contact=contact)


def search_query(question: str, history: Sequence[Turn]) -> str:
    """The last history question, then the question; the previous one gives way so the whole fits."""
    question = " ".join(question.split())
    if not history:
        return question
    room = MAX_QUERY_CHARS - len(question) - 1
    previous = " ".join(history[-1].question.split())[: max(room, 0)]
    return f"{previous}\n{question}" if previous else question


def is_not_found(reply: str) -> bool:
    return reply.strip().lstrip("*`\"' ").startswith(NOT_FOUND)


def _source_event(n: int, hit: Hit) -> dict[str, Any]:
    return {
        "n": n,
        "document_id": hit.document_id,
        "chunk_id": hit.chunk_id,
        "title": hit.title,
        "file_type": hit.file_type,
        "heading_path": hit.heading_path,
        "section": hit.section,
        "page_start": hit.page_start,
        "page_end": hit.page_end,
        "sheet": hit.sheet,
        "effective_date": hit.effective_date,
        "snippet": " ".join(hit.text.split())[:SNIPPET_CHARS],
    }


def _source_row(n: int, hit: Hit) -> dict[str, Any]:
    """`questions.sources`: ids, titles and pages, no chunk text (SPEC-02 §5)."""
    return {
        "n": n,
        "documentId": str(hit.document_id),
        "chunkId": str(hit.chunk_id),
        "title": hit.title,
        "section": hit.section,
        "pageStart": hit.page_start,
        "pageEnd": hit.page_end,
        "sheet": hit.sheet,
    }


def _can_fall_back(err: ProviderError, settings: Settings) -> bool:
    """SPEC-05 §3: never for a bad key; for quota only when the plan ran out and PAYG may still pay."""
    if not settings.llm_fallback_model or err.code == "provider_auth":
        return False
    if err.code == "quota_exhausted":
        payg = LATEST_BALANCES.payg_myr
        return err.http_status != 402 and (payg is None or payg > 0)
    return True


async def answer_stream(
    session: AsyncSession,
    question: str,
    user: Identity,
    history: Sequence[Turn] = (),
    *,
    settings: Settings | None = None,
    providers: Providers | None = None,
) -> AsyncGenerator[Event]:
    settings = settings or get_settings()
    providers = providers or get_providers()
    run = _Run(id=uuid.uuid4(), started=time.monotonic(), malay=detect_language(question) == "ms")
    await session.execute(insert(Question).values(id=run.id, user_id=user.id, question=question))
    await session.commit()
    try:
        yield Event("meta", {"question_id": run.id})
        async with aclosing(
            _answer(session, run, question, user, list(history), settings, providers)
        ) as events:
            async for event in events:
                yield event
    except Exception as exc:
        # Never the message: it may carry SQL or provider text. The trace id ties the log to the request.
        log.error("answer_failed", question_id=str(run.id), error_type=type(exc).__name__)
        if not run.finished:
            yield run.fail("internal")
    except BaseException:  # client disconnect: GeneratorExit from aclose(), or task cancellation
        if not run.finished:
            run.fail("cancelled")
        raise
    finally:
        await _save(session, run)


async def _answer(
    session: AsyncSession,
    run: _Run,
    question: str,
    user: Identity,
    history: list[Turn],
    settings: Settings,
    providers: Providers,
) -> AsyncGenerator[Event]:
    query = search_query(question, history)
    hits = await search(session, query, user, settings=settings, providers=providers, ref_id=str(run.id))
    await session.commit()  # no transaction stays open while the model streams
    if not hits:
        yield Event("sources", {"sources": []})
        run.found = False
        scope = about_assistant(question)
        if scope is not None:  # SPEC-05 §5.1: say what can be asked instead of "contact HR"
            run.answer = scope_text(run.malay or scope == "ms", settings.org_name)
        else:
            run.answer = not_found_text(run.malay, None, settings.not_found_contacts)
        yield run.delta(run.answer)
        yield run.done(TokenUsage(), None)
        return

    def prompt_for(budget: int) -> Prompt:
        return build_prompt(
            question,
            hits,
            history,
            org_name=settings.org_name,
            max_context_tokens=budget,
            chunk_max_tokens=settings.chunk_max_tokens,
            malay=run.malay,
        )

    prompt = prompt_for(settings.max_context_tokens)
    run.sources = [_source_row(n, h) for n, h in enumerate(prompt.sources, 1)]
    yield Event("sources", {"sources": [_source_event(n, h) for n, h in enumerate(prompt.sources, 1)]})

    role: Role = "answer"
    shrunk = False
    while True:
        model = providers.chat(role)
        reply, shown, usage = "", "", TokenUsage()
        decided = False
        try:
            stream = model.stream(  # an async generator in every implementation
                prompt.messages,
                reasoning="off",
                max_tokens=ANSWER_MAX_TOKENS,
                temperature=ANSWER_TEMPERATURE,
                purpose="question",
                ref_id=str(run.id),
            )
            async with aclosing(cast(AsyncGenerator[ChatDelta], stream)) as deltas:
                async for piece in deltas:
                    if piece.usage is not None:
                        usage = piece.usage
                    reply += piece.text
                    if not decided and len(reply) >= SENTINEL_BUFFER:
                        decided = True
                    if decided and not is_not_found(reply) and len(reply) > len(shown):
                        yield run.delta(reply[len(shown) :])
                        shown = reply
        except ProviderError as err:
            if not shown and err.code == "context_too_long" and not shrunk:
                shrunk = True
                prompt = prompt_for(settings.max_context_tokens // 2)
                log.warning("answer_context_shrunk", question_id=str(run.id), sources=len(prompt.sources))
                continue
            if not shown and role == "answer" and _can_fall_back(err, settings):
                log.warning("answer_fallback", question_id=str(run.id), code=err.code)
                role = "fallback"
                continue
            log.warning("answer_provider_error", question_id=str(run.id), code=err.code, streamed=bool(shown))
            run.model = model.model
            yield run.fail(err.code)
            return
        break

    run.model = model.model
    department = prompt.sources[0].department
    if is_not_found(reply):
        run.found, final = False, not_found_text(run.malay, department, settings.not_found_contacts)
    else:
        final, run.cited = validate(reply, len(prompt.sources))
        run.found = bool(run.cited)
        if not run.cited:  # SPEC-05 §4: an uncited claim must not stay on screen
            run.error_code = "uncited"
            final = not_found_text(run.malay, department, settings.not_found_contacts)
    run.answer = final
    if not shown:
        yield run.delta(final)
        yield run.done(usage, None)
    else:
        yield run.done(usage, final if final != shown else None)
    log.info(
        "answered",
        question_id=str(run.id),
        found=run.found,
        cited=len(run.cited),
        model=run.model,
        first_token_ms=run.first_token_ms,
        latency_ms=run.latency_ms,
    )


async def _save(session: AsyncSession, run: _Run) -> None:
    """Writes the outcome; shielded so a cancelled request still records it."""
    with anyio.CancelScope(shield=True):
        try:
            if session.in_transaction():  # a step cancelled mid-query
                await session.rollback()
            await session.execute(
                update(Question)
                .where(Question.id == run.id)
                .values(
                    answer=run.answer,
                    found=run.found,
                    sources=run.sources,
                    cited=run.cited,
                    model=run.model,
                    latency_ms=run.latency_ms if run.latency_ms is not None else run.elapsed_ms(),
                    first_token_ms=run.first_token_ms,
                    error_code=run.error_code,
                )
            )
            await session.commit()
        except Exception as exc:
            log.error("question_save_failed", question_id=str(run.id), error_type=type(exc).__name__)
