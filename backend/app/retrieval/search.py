"""Hybrid retrieval (SPEC-04): one SQL statement fuses vector and full-text ranks with RRF.

Both arms filter on `doc_status`, `access_groups` and `embedding_model` before ranking. The relevance
gate, the reranker, the per-document cap and the cut to TOP_K run in Python afterwards.
"""

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.providers.registry import Providers, get_providers
from app.retrieval import rerank as reranking
from app.security.identity import Identity

MAX_QUERY_CHARS = 1000
_WORD = re.compile(r"[\w-]+", re.UNICODE)

HYBRID_SQL = text(
    """
WITH vec AS (
  SELECT c.id, 1 - (c.embedding <=> CAST(CAST(:qvec AS text) AS vector)) AS sim,
         row_number() OVER (ORDER BY c.embedding <=> CAST(CAST(:qvec AS text) AS vector)) AS rnk
  FROM chunks c
  WHERE c.doc_status = 'current' AND c.access_groups && CAST(:groups AS text[])
    AND c.embedding_model = :model
  ORDER BY c.embedding <=> CAST(CAST(:qvec AS text) AS vector)
  LIMIT :k_vec
),
fts AS (
  SELECT c.id, row_number() OVER (ORDER BY ts_rank_cd(c.tsv, s.q) DESC) AS rnk
  FROM chunks c,
       (SELECT (replace(plainto_tsquery('english', :q)::text, '&', '|')::tsquery
             || replace(plainto_tsquery('simple', :q)::text, '&', '|')::tsquery) AS q) s
  WHERE c.doc_status = 'current' AND c.access_groups && CAST(:groups AS text[])
    AND c.embedding_model = :model
    AND c.tsv @@ s.q
  ORDER BY ts_rank_cd(c.tsv, s.q) DESC
  LIMIT :k_fts
),
fused AS (
  SELECT id, SUM(1.0 / (CAST(:rrf_k AS float8) + rnk)) AS score,
         MIN(rnk) FILTER (WHERE src = 'vec') AS vec_rank,
         MIN(rnk) FILTER (WHERE src = 'fts') AS fts_rank,
         MAX(sim) AS vec_sim
  FROM (SELECT id, rnk, sim, 'vec' AS src FROM vec
        UNION ALL SELECT id, rnk, NULL::float8, 'fts' FROM fts) u
  GROUP BY id
)
SELECT f.score, f.vec_rank, f.fts_rank, f.vec_sim,
       c.id AS chunk_id, c.document_id, c.ordinal, c.chunk_type, c.text, c.heading_path, c.section,
       c.page_start, c.page_end, c.sheet, c.token_count,
       d.title, d.filename, d.file_type, d.effective_date, d.version, d.doc_type, d.department
FROM fused f JOIN chunks c ON c.id = f.id JOIN documents d ON d.id = c.document_id
ORDER BY f.score DESC
LIMIT :k_cand
"""
)


@dataclass(frozen=True, slots=True)
class Hit:
    chunk_id: Any
    document_id: Any
    ordinal: int
    chunk_type: str
    text: str
    heading_path: list[str]
    section: str | None
    page_start: int | None
    page_end: int | None
    sheet: str | None
    title: str
    filename: str
    file_type: str
    effective_date: date | None
    version: str | None
    doc_type: str | None
    score: float
    vec_rank: int | None
    fts_rank: int | None
    vec_sim: float | None
    rerank_score: float | None = None
    department: str | None = None
    token_count: int = 0


def prepare_query(raw: str) -> str:
    """Trim, collapse whitespace, cut to 1,000 characters (the API refuses longer input first)."""
    return " ".join(raw.split())[:MAX_QUERY_CHARS]


def code_tokens(query: str) -> list[str]:
    """Words with at least one letter and one digit: `M2`, `Q4`, `HR-F07` (D003: pure numbers excluded)."""
    return [w for w in _WORD.findall(query) if any(c.isalpha() for c in w) and any(c.isdigit() for c in w)]


def _vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(repr(float(v)) for v in vec) + "]"


async def fetch_candidates(
    session: AsyncSession, query: str, qvec: list[float], groups: list[str], settings: Settings
) -> list[Hit]:
    """The SPEC-04 §3 statement: up to RERANK_CANDIDATES fused hits, before gate, cap and cut."""
    await session.execute(text("SET LOCAL hnsw.ef_search = 100"))
    await session.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))
    result = await session.execute(
        HYBRID_SQL,
        {
            "qvec": _vector_literal(qvec),
            "q": query,
            "groups": groups,
            "model": settings.embed_model,
            "k_vec": settings.k_vec,
            "k_fts": settings.k_fts,
            "rrf_k": settings.rrf_k,
            "k_cand": settings.rerank_candidates,
        },
    )
    return [Hit(**row) for row in result.mappings()]


def passes_gate(query: str, candidates: list[Hit], settings: Settings) -> bool:
    """SPEC-04 §4: enough vector similarity, or a code token found by the full-text arm."""
    sims = [h.vec_sim for h in candidates if h.vec_sim is not None]
    if sims and max(sims) >= settings.min_vector_sim:
        return True
    for token in code_tokens(query):
        pattern = re.compile(rf"(?<![\w-]){re.escape(token)}(?![\w-])", re.IGNORECASE)
        if any(h.fts_rank is not None and pattern.search(h.text) for h in candidates):
            return True
    return False


def cap_per_document(hits: list[Hit], max_per_doc: int) -> list[Hit]:
    """Keeps order; drops a document's hits beyond the cap."""
    seen: dict[Any, int] = {}
    kept: list[Hit] = []
    for hit in hits:
        n = seen.get(hit.document_id, 0)
        if n < max_per_doc:
            kept.append(hit)
            seen[hit.document_id] = n + 1
    return kept


async def search(
    session: AsyncSession,
    query: str,
    user: Identity,
    top_k: int | None = None,
    *,
    settings: Settings | None = None,
    providers: Providers | None = None,
    ref_id: str | None = None,
) -> list[Hit]:
    """`ref_id` links the query embedding's usage row to a question (SPEC-05 §7 check 8)."""
    settings = settings or get_settings()
    providers = providers or get_providers()
    query = prepare_query(query)
    if not query:
        return []
    (qvec,) = await providers.embedder().embed([query], purpose="question", ref_id=ref_id)
    candidates = await fetch_candidates(session, query, qvec, list(user.groups), settings)
    if not candidates:
        return []
    reranker = providers.reranker()
    gated: list[Hit] | None = None
    if reranker is not None:
        gated = await reranking.rerank(query, candidates, reranker, settings, ref_id)
    if gated is None:
        if not passes_gate(query, candidates, settings):
            return []
        gated = candidates
    return cap_per_document(gated, settings.max_chunks_per_doc)[: top_k or settings.top_k]
