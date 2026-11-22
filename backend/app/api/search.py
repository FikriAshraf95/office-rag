"""Endpoint 12: hybrid search debug (SPEC-08 §5). Calls the same function as answering."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.api.schemas import SearchHitOut, SearchIn, SearchOut
from app.db.engine import get_session
from app.retrieval.search import MAX_QUERY_CHARS, Hit, prepare_query, search
from app.security.identity import CurrentUser

router = APIRouter(prefix="/api/v1", tags=["search"])

Session = Annotated[AsyncSession, Depends(get_session)]
SNIPPET_CHARS = 300


def _hit_out(hit: Hit) -> SearchHitOut:
    return SearchHitOut(
        chunk_id=hit.chunk_id,
        document_id=hit.document_id,
        title=hit.title,
        file_type=hit.file_type,
        heading_path=hit.heading_path,
        section=hit.section,
        page_start=hit.page_start,
        page_end=hit.page_end,
        sheet=hit.sheet,
        effective_date=hit.effective_date,
        score=hit.score,
        vec_rank=hit.vec_rank,
        fts_rank=hit.fts_rank,
        vec_sim=hit.vec_sim,
        rerank_score=hit.rerank_score,
        snippet=" ".join(hit.text.split())[:SNIPPET_CHARS],
    )


@router.post("/search", response_model=SearchOut)
async def search_documents(body: SearchIn, session: Session, user: CurrentUser) -> SearchOut:
    query = body.query.strip()
    if len(query) > MAX_QUERY_CHARS:
        raise ApiError(
            422, "query_too_long", f"Keep the question under {MAX_QUERY_CHARS} characters and try again."
        )
    if not prepare_query(query):
        raise ApiError(
            422,
            "validation_failed",
            "Some fields are not valid.",
            errors={"query": ["Type a question."]},
        )
    hits = await search(session, query, user, body.top_k)
    return SearchOut(hits=[_hit_out(h) for h in hits])
