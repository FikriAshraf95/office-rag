# SPEC-04 — Retrieval

> **Status:** v1 (2026-11-19) · **Owner of:** hybrid search, RRF, filters, reranker, the search debug endpoint
> Tables: [SPEC-02 §3](SPEC-02-database-schema.md) · Endpoint: [SPEC-08 §5](SPEC-08-api-contract.md)

## 1. Rules

1. All retrieval goes through `app/retrieval/search.py`: `async def search(session, query: str, user: Identity, top_k: int | None = None) -> list[Hit]`.
2. **Filters are applied before ranking, inside both search arms:** `c.doc_status = 'current'` and `c.access_groups && :user_groups` (array overlap). Deleted documents have no chunks ([SPEC-03 §7](SPEC-03-ingestion.md)).
3. Only chunks whose `embedding_model` equals the configured `EMBED_MODEL` are searched, in both arms.
4. No post-filtering of results is allowed as a substitute for rule 2.

## 2. Query preparation

- Trim, collapse whitespace, cap at 1,000 characters (`422 query_too_long` above that at the API).
- Embed the query once with the `embed` role (`purpose = 'question'`).
- Full-text query: `websearch_to_tsquery` is too strict for questions (it ANDs every word), so build an OR query: `replace(plainto_tsquery('english', :q)::text, '&', '|')::tsquery || replace(plainto_tsquery('simple', :q)::text, '&', '|')::tsquery`.
- Optional (behind `QUERY_REWRITE=true`, off by default): a `fast`-role call that rewrites the question into a keyword query. Only if the eval shows it helps.

## 3. Hybrid search SQL (one query, in one transaction)

The two `SET LOCAL` lines only last for the current transaction, so they and the query run in the same one.

```sql
SET LOCAL hnsw.ef_search = 100;
SET LOCAL hnsw.iterative_scan = relaxed_order;   -- pgvector 0.8: keeps filtered HNSW results full
WITH vec AS (
  SELECT c.id, 1 - (c.embedding <=> :qvec) AS sim,
         row_number() OVER (ORDER BY c.embedding <=> :qvec) AS rnk
  FROM chunks c
  WHERE c.doc_status = 'current' AND c.access_groups && :groups AND c.embedding_model = :model
  ORDER BY c.embedding <=> :qvec
  LIMIT :k_vec
),
fts AS (
  SELECT c.id, row_number() OVER (ORDER BY ts_rank_cd(c.tsv, q) DESC) AS rnk
  FROM chunks c, (SELECT :tsquery::tsquery AS q) s
  WHERE c.doc_status = 'current' AND c.access_groups && :groups AND c.embedding_model = :model
    AND c.tsv @@ s.q
  ORDER BY ts_rank_cd(c.tsv, q) DESC
  LIMIT :k_fts
),
fused AS (
  SELECT id, SUM(1.0 / (:rrf_k + rnk)) AS score,
         MIN(rnk) FILTER (WHERE src = 'vec') AS vec_rank,
         MIN(rnk) FILTER (WHERE src = 'fts') AS fts_rank,
         MAX(sim) AS vec_sim
  FROM (SELECT id, rnk, sim, 'vec' AS src FROM vec
        UNION ALL SELECT id, rnk, NULL::float8, 'fts' FROM fts) u
  GROUP BY id
)
SELECT f.score, f.vec_rank, f.fts_rank, f.vec_sim, c.*, d.title, d.filename, d.file_type, d.effective_date, d.version, d.doc_type
FROM fused f JOIN chunks c ON c.id = f.id JOIN documents d ON d.id = c.document_id
ORDER BY f.score DESC
LIMIT :k_cand;
```

Defaults (config): `K_VEC = 40`, `K_FTS = 40`, `RRF_K = 60`, `TOP_K = 8`, `RERANK_CANDIDATES = 30`. The query always returns `k_cand = RERANK_CANDIDATES` candidates. Then, in Python and in this order: the relevance gate (§4), the reranker if configured (§6), the per-document cap (§5), and the cut to `TOP_K`.

## 4. Relevance gate

- RRF scores are rank-based, so they can't say "nothing is relevant". The gate passes when either holds:
  1. the best `vec_sim` among the candidates is ≥ `MIN_VECTOR_SIM` (default 0.53 for bge-m3, tuned on the Serimaju set in M03, re-checked in M06), or
  2. the query contains a **code token** (a `[\w-]+` word with at least one letter **and** at least one digit, e.g. `M2`, `Q4`, `E1`, `HR-F07`) and a candidate found by the full-text arm (`fts_rank` set) contains that token as a whole word (not inside a longer word such as `M20`), case-insensitive. Bare numbers (`6`, `2026`) are not code tokens: questions are full of them, and they would open the gate for unrelated questions. A query whose only distinctive token is a bare number is decided by vector similarity alone.
- Otherwise the result is empty and answering returns not-found without calling the LLM.
- A full-text match on ordinary words never passes the gate on its own: the OR query (§2) plus the `simple` config (which keeps stop words) matches almost every chunk, so "the full-text arm returned something" says nothing about relevance.
- With a reranker, the gate is the reranker score: drop hits below `MIN_RERANK_SCORE` (default 0.1, tuned in M08).

## 5. Diversity and ordering

- At most `MAX_CHUNKS_PER_DOC = 4` hits per document in the final list (keeps one long handbook from crowding out the memo). The cap runs on the `k_cand` candidates **before** the cut to `TOP_K`, so it replaces crowded hits with hits from other documents instead of shrinking the list.
- Final hits keep fused order (or reranker order, §6). The answering step numbers them `[1]…[n]` in that order.

## 6. Reranker (M08)

- `app/retrieval/rerank.py`: if `providers.reranker()` is not `None`, rerank the gated `k_cand` candidates with the query; the per-document cap and the `TOP_K` cut (§5) follow.
- Off by default (`RERANK_MODEL=` empty). Retrieval must work fully without it.
- On reranker error: log, fall back to the fused order (never fail the question).

## 7. Search debug endpoint

`POST /api/v1/search` returns hits with `score`, `vecRank`, `ftsRank`, `vecSim`, `rerankScore`, title, heading path, page and a 300-char snippet. It applies exactly the same filters (it calls the same function). Used by the eval and the demo ("why did it pick this?").

## 8. Acceptance checks

1. A query for an exact form number or grade code (e.g. `M2`) finds the chunk through the full-text arm even when the vector arm ranks it low.
2. **Superseded documents are never retrieved:** with both handbooks ingested, no hit comes from the 2024 handbook for any eval question.
3. **Access filter before ranking:** a user without the `hr-restricted` group never receives a chunk from the private-marker document, even when the query is the marker text itself; and the result still has `TOP_K` hits from other documents if available (the filter is not a post-filter that shrinks results).
4. Chunks with a different `embedding_model` are never returned.
5. No more than `MAX_CHUNKS_PER_DOC` hits come from one document.
6. A query with no related content (e.g. "pet policy") returns an empty list under the relevance gate (fixture-based, fake embedder thresholds set in the test).
7. With a fake reranker configured, the final order follows reranker scores; with the reranker raising an error, results fall back to fused order.
8. A query that shares only common words with the documents (e.g. "pet policy" against fixtures containing "policy") is gated out even though the full-text arm matches; a query with a code token (`M2`) passes the gate through the full-text arm when its vector similarity is below `MIN_VECTOR_SIM`.
9. With more than `TOP_K` relevant chunks spread over several documents, one of which has more than `MAX_CHUNKS_PER_DOC` of them, the result has exactly `TOP_K` hits and at most `MAX_CHUNKS_PER_DOC` from that document.
