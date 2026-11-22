# M02 plan — Ingestion pipeline

> Written 2026-11-20 before any code. Specs: SPEC-03 (whole), SPEC-02 §3–4, SPEC-06 §4–5, SPEC-08 §4.6–4.7.

## Design decisions

1. **Parsers return plain data, chunking is pure.** `parsers/*.py` return `ParsedDocument(blocks, meta)`; `chunking.py` turns blocks into `ChunkDraft`s with no I/O. Only `parsers/pdf|docx|markdown|image.py` import Docling (lazy, inside the function) so the API image and the fast tests never load it.
2. **Docling-free fast path.** XLSX (openpyxl), Markdown front matter + heading splitter, chunking rules and metadata are testable without Docling. `@pytest.mark.docling` covers PDF/DOCX/image only.
3. **Tokenizer.** `chunking.py` uses a `TokenCounter` protocol. Production: the `BAAI/bge-m3` tokenizer (`transformers` AutoTokenizer, offline from the models dir). Tests: a whitespace counter, so the fast subset needs no model.
4. **Service owns every write.** New in `service.py`: `claim_started`, `swap_chunks`, `mark_failed`, `mark_requeued`, `mark_done`, `request_reingest`, `list_chunks`. The swap does `SELECT … FOR UPDATE` on the document, copies `status`/`access_groups` at that moment, and writes nothing if `deleted_at` is set (SPEC-03 §1 rule 5).
5. **Queue in `jobs.py`.** `claim()` (the only raw SQL besides search), `heartbeat()`, `requeue_stale()`, `finish()`, `fail()`, `retry_later()`.
6. **Worker loop.** Claim → process → repeat; when idle, wait on `LISTEN jobs_new` with a 5 s poll fallback. A heartbeat task bumps `locked_at` every 60 s; stale recovery at start and every 60 s.
7. **Error mapping** in `process_one_job`: `ProviderError.quota_exhausted` → `quota` (no retry); retryable with attempts left → requeue with `30 s × 2^attempts`; retryable exhausted → `rate_limit`/`provider`; parser failure → `parse`; no text → `empty`; anything else → `unknown`.
8. **Superseded** only on first ingestion (document has no chunks and `chunk_count = 0` and no prior `ready`). Re-ingest keeps `status`.
9. **Embedding model guard** (SPEC-03 §9): before embedding, fail `provider` if existing chunks of other documents use a different `embedding_model`.

## Order of work

1. Docling install on Python 3.14 (`worker` group); record size and per-page time (O2, O3). **Risk:** if it does not install, log a deviation and stop to ask.
2. `jobs.py` + `worker.py` claim loop + `service.py` transitions. Tests: concurrent claim (ac03), requeue/quota (ac08), heartbeat (ac17), stale lock.
3. `metadata.py`, `chunking.py`, `parsers/xlsx.py`, `parsers/markdown.py`. Tests: ac06, ac12, ac07, ac16, metadata table.
4. `parsers/pdf.py`, `docx.py`, `image.py` (Docling). Tests marked `docling`: ac05.
5. Embedding step + atomic swap. Tests: ac04, ac09, ac13, ac14.
6. Endpoints 10–11, SPEC-08 rows, OpenAPI export, frontend types.
7. Frontend: re-ingest action, failed banner Retry, Chunks tab.
8. Invariant: private marker on `/chunks`. Full gates. Walkthrough with real ILMU.

## Out of scope (stays for later milestones)
Vision fallback (M07), summary/tags (M07), reranker (M08), re-embed command (M99).

## Deviations expected
None planned. If Docling needs a different Python or install route, log D002.
