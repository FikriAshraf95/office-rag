"""Optional reranker step (SPEC-04 §6). The reranker score is the relevance gate when one is configured."""

from dataclasses import replace
from typing import TYPE_CHECKING

import structlog

from app.config import Settings

if TYPE_CHECKING:
    from app.providers.base import Reranker
    from app.retrieval.search import Hit

log = structlog.get_logger()


async def rerank(
    query: str, hits: list[Hit], reranker: Reranker, settings: Settings, ref_id: str | None = None
) -> list[Hit] | None:
    """Hits in reranker order, below MIN_RERANK_SCORE dropped. None on any error (caller falls back)."""
    try:
        ranked = await reranker.rerank(
            query, [h.text for h in hits], top_n=len(hits), purpose="question", ref_id=ref_id
        )
    except Exception as exc:
        log.warning("rerank_failed", error=str(getattr(exc, "code", type(exc).__name__)))
        return None
    return [
        replace(hits[r.index], rerank_score=r.score) for r in ranked if r.score >= settings.min_rerank_score
    ]
