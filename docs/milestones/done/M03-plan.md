# M03 plan — Retrieval

> Written 2026-11-20 before any code (Opus plans, Sonnet builds). Specs: SPEC-04 §1–5, §7–8 (and §6 for the reranker hook), SPEC-02 §3, SPEC-08 §5, SPEC-09 §4.
> Environment facts checked: pgvector **0.8.7** (iterative scan available), PostgreSQL 17. The dev DB holds the 10 Serimaju documents from the M02 walkthrough (55 current + 14 superseded chunks, real bge-m3).

## Design decisions

1. **One module, small pure steps.** `app/retrieval/search.py` exposes:
   - `prepare_query(text: str) -> str` — trim, collapse whitespace, cut to 1,000 chars (the API refuses longer input before this).
   - `async fetch_candidates(session, query, qvec, groups, settings) -> list[Hit]` — the SPEC-04 §3 statement, verbatim in structure (both CTEs carry all three filters). Used by `search()` and by the inspect script (which wants pre-gate `vec_sim`).
   - `passes_gate(query, candidates, settings) -> bool` — SPEC-04 §4.
   - `cap_per_document(hits, max_per_doc) -> list[Hit]` — keeps order, drops the 5th+ hit of a document.
   - `async search(session, query, user, top_k=None, *, settings=None, providers=None) -> list[Hit]` — the public entry point (signature from SPEC-04 §1 plus keyword-only overrides for tests; defaults are `get_settings()` / `get_providers()`).
2. **SQL details.**
   - Run with `sqlalchemy.text()` on the caller's `AsyncSession`. Execute `SET LOCAL hnsw.ef_search = 100` and `SET LOCAL hnsw.iterative_scan = relaxed_order` as separate statements **on the same session immediately before** the query (the session is already in a transaction; in tests it's a savepoint inside the test transaction, which is fine).
   - Binds: `CAST(:qvec AS vector)` with the vector as the pgvector text literal `'[0.1,0.2,…]'`; `CAST(:groups AS text[])` with a Python list; never `::` after a bind name (SQLAlchemy `text()` parses colons).
   - tsquery built **in SQL** from the raw query text, inside the `s` subquery: `(replace(plainto_tsquery('english', :q)::text, '&', '|')::tsquery || replace(plainto_tsquery('simple', :q)::text, '&', '|')::tsquery)`. If both sides are empty (query of only stop words/punctuation in `english` and nothing in `simple` — practically never), the fts arm returns nothing; that's fine.
   - `k_cand = settings.rerank_candidates` (30). Return columns per §3 and map rows to `Hit`.
   - Groups come from `user.groups` (a tuple → list).
3. **`Hit` dataclass** (frozen, slots): `chunk_id, document_id, ordinal, chunk_type, text, heading_path, section, page_start, page_end, sheet, title, filename, file_type, effective_date, version, doc_type, score, vec_rank, fts_rank, vec_sim, rerank_score=None`. M04 numbers these `[1]…[n]` and needs `text`.
4. **Relevance gate (§4).** Pass if `max(vec_sim) >= settings.min_vector_sim`, or if the query has a code token that occurs (case-insensitive, whole-word, regex `(?<![\w-])TOKEN(?![\w-])`) in the `text` of a candidate whose `fts_rank` is set. **Code token = a `[\w-]+` word containing at least one letter and at least one digit** (`M2`, `Q4`, `E1`, `HR-F07`). Pure numbers (`6`, `2026`, `10`) are *not* code tokens: "pet policy 2026" would otherwise pass on almost any document. This narrows SPEC-04 §4's "a word with a digit" → log **D003** and add the spec note at SPEC-04 §4.
5. **Reranker hook (§6) now, minimal, because check 7 needs it.** `app/retrieval/rerank.py`: `async rerank(query, hits, reranker, settings) -> list[Hit] | None` — calls `reranker.rerank(query, [h.text for h in hits], top_n=len(hits), purpose="question")`, returns hits reordered with `rerank_score` set and those below `MIN_RERANK_SCORE` dropped; on any `Exception` logs `rerank_failed` (warning, error code only, no text) and returns `None`. Order in `search()`:
   1. candidates = fetch (empty → `[]`);
   2. if `providers.reranker()` is not None: `reranked = await rerank(...)`; if not None → that is the gated list (the reranker score *is* the gate, §4 last bullet); if None (error) → fall through to step 3 on fused order;
   3. otherwise `passes_gate` → `[]` if it fails;
   4. `cap_per_document(…, settings.max_chunks_per_doc)`, then cut to `top_k or settings.top_k`.
   M08 wires/measures the real reranker; nothing else of M08 is done here.
6. **Embedding the query:** `providers.embedder().embed([query], purpose="question")` once; the configured `settings.embed_model` is the `:model` bind (not the embedder's attribute, so check 4 is driven by config).
7. **Endpoint 12** in new `app/api/search.py` (router prefix `/api/v1`, tag `search`): body `SearchIn {query: str, topK: int | None (ge=1, le=20)}`; after trimming, `len > 1000` → `ApiError(422, "query_too_long", …)`; empty → 422 `validation_failed` with `errors={"query": [...]}`; calls `search()` once; maps to `SearchOut {hits: [SearchHitOut]}` with the SPEC-08 §5 fields, `snippet` = first 300 chars of `text` with whitespace collapsed. `rerankScore` null when no reranker. Router must not import `app.providers.*` (import-linter `api-boundaries`) — it only imports `app.retrieval.search`.
8. **Import contracts.** Add `app.retrieval` to the source modules of `sdk-only-in-providers` and `docling-only-in-parsers`, and to the forbidden modules of `providers-are-low-level`. Add a forbidden contract `app.retrieval` must not import `app.api` or `app.ingestion` (reads only; writes live in `ingestion/service.py`).
9. **No schema change.** SPEC-02 §3 indexes already exist (HNSW, GIN tsv, GIN access_groups). No migration.

## Tests (`tests/spec04/test_retrieval.py`, names `test_spec04_acNN_…`)

Setup pattern (same as `tests/spec08/test_chunks.py`): upload via the API, monkeypatch `app.ingestion.extract.extract` to return chosen `ChunkDraft`s, run `process_one_job(sessions, settings, providers, WhitespaceCounter(), "w")`. Fake embedder (bag-of-words hash) gives controllable similarity. Call `search()` directly with `settings=get_settings().model_copy(update={...})` to set `min_vector_sim`, `top_k`, `max_chunks_per_doc`, `rerank_model`. Only setup that cannot go through the service (check 4's foreign `embedding_model`) uses a direct `UPDATE chunks` in the test.

1. ac01: chunk containing `Grade M2 … 22 days` among many chunks with a closer bag-of-words to the query; query `M2 annual leave 6 years`; assert the M2 chunk is in the result with `fts_rank` set (vector rank low or absent).
2. ac02: both handbooks (2024 set `superseded` via PATCH or first-ingestion logic) with the same text; no hit has the 2024 document id, for several queries.
3. ac03: private doc (`accessGroups=["hr"]`, text with `ZQX-PRIVATE-7`) + ≥ `TOP_K` other `all` chunks; as `ben`, query = the marker text → no hit from the private doc and `len(hits) == top_k`. As `aisyah` the private chunk is returned (sanity).
4. ac04: chunks whose `embedding_model` is updated to `other-model` are never returned.
5. ac05: one doc with 8 matching chunks → at most `MAX_CHUNKS_PER_DOC` from it.
6. ac06: "pet policy" against unrelated fixtures with `min_vector_sim` set high (e.g. 0.6) → `[]`.
7. ac07: fake reranker (`rerank_model="fake-rerank"` on a fresh `Providers`) → order follows `rerank_score` descending; with a reranker whose `rerank` raises `ProviderError` → fused order, no exception.
8. ac08: fixtures contain "policy"; "pet policy" gated out although `fts_rank` is set on candidates; "M2 …" passes via full-text with `min_vector_sim` above its best `vec_sim`. Plus unit tests for the code-token rule (`M2`, `HR-F07` yes; `6`, `2026` no).
9. ac09: > TOP_K relevant chunks over 3 docs, one with 6 → exactly `TOP_K` hits, ≤ 4 from that doc.
- Endpoint (`tests/spec08/test_search.py`): response keys = SPEC-08 §5 field set; `topK` 0/21 → 422 `validation_failed`; 1,001-char query → 422 `query_too_long`; missing user → 401.
- Invariants: extend `tests/invariants/test_private_marker.py` with `/search` for ben (query = marker text and "salary bands") → marker and title absent; new `tests/invariants/test_superseded.py`: superseded document never appears in `/search` hits.

## Inspect script (`app/eval/inspect_search.py`)

`uv run python -m app.eval.inspect_search [--user ben] [--only Q01,Q02] [--k 8]` against the dev DB with real providers (needs `.env`). For each row of `samples/serimaju/eval/eval_questions.csv`: embed, `fetch_candidates`, print the gate decision, best `vec_sim`, and the top 8 after the full `search()` (title, section/sheet, score, vec_rank, fts_rank, vec_sim); compute whether each expected source filename (split `expected_sources` on `;`, take the filename part, match against `documents.filename`; "Memo scan" style shorthands matched by a small alias rule or reported as unmatched) is in the top 8. Print a summary: recall@8, list of misses, and best `vec_sim` for answerable vs not-found-category questions so `MIN_VECTOR_SIM` can be chosen. Create `app/eval/__init__.py` (empty; M06 adds the rest). Never ingests the CSV.

Tuning rule: choose `MIN_VECTOR_SIM` just below the lowest best-`vec_sim` of answerable questions, provided it stays above the highest of the not-found questions. If it changes from 0.35, update `config.py`, `.env.example` and the number in SPEC-04 §4 (a spec update, not a deviation). If no threshold separates them, keep 0.35 and record the overlap in the milestone status for M06/M08.

## Order of work

1. `app/retrieval/__init__.py`, `search.py`, `rerank.py`; import contracts.
2. `tests/spec04/` checks 1–9 (fast, fake AI). Iterate until green.
3. `app/api/search.py` + schemas + `main.py` include; endpoint tests; invariants.
4. `uv run python -m app.export_openapi`; `cd frontend && npm run gen:api` (types only, no UI).
5. Full gates: `ruff check`, `ruff format --check`, `mypy app`, `lint-imports`, `pytest -q`; frontend `lint typecheck test build`.
6. D003 file + index row + SPEC-04 §4 note.
7. Inspect script on the dev DB (real bge-m3); tune `MIN_VECTOR_SIM`; record recall@8 and misses.
8. Walkthrough: API running on :8000 against the dev DB; `POST /api/v1/search` as ben for the three acceptance queries; record results.
9. Milestone file: tick boxes, Status; move M03 + plan to `done/`; update CLAUDE.md Status line (next: M04).

## Out of scope
Query rewrite (`QUERY_REWRITE`, only if the eval shows it helps — M06), real reranker measurement (M08), search debug UI (optional, not done), answering (M04).

## Deviations expected
D003 — code-token definition (letter + digit). Anything else found while building gets the next number.
