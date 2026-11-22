# M02 — Ingestion pipeline

> **Depends on:** [M01](M01-upload-and-documents.md) · **Blocks:** [M03](M03-retrieval.md)
> **Read first:** [SPEC-03 (whole file)](../../specs/SPEC-03-ingestion.md) · [SPEC-02 §3–4](../../specs/SPEC-02-database-schema.md#3-chunks) · [SPEC-06 §2, §4–6](../../specs/SPEC-06-ai-providers.md#2-clients) · [SPEC-08 §4.6–4.7](../../specs/SPEC-08-api-contract.md#46-re-ingest) · [SPEC-11 §2](../../specs/SPEC-11-deployment.md#2-images)
> **Model:** Opusplan. The hard parts are Docling integration, structure-aware chunking for 5 formats, and correct job states under errors. Write `M02-plan.md` first.

## Goal
A separate worker turns queued documents into embedded, structure-aware chunks for PDF, DOCX, Markdown, XLSX and PNG/JPG (OCR), with metadata, superseded detection and correct handling of rate-limit and quota errors. All 10 Serimaju documents reach **Ready** (the org chart may have only OCR text until M07).

## Tasks
### Backend
- [x] Add the `worker` dependency group (docling, CPU torch) and verify `docling` 2.x imports on Python 3.14; record install size and per-page time (open items O2, O3 in SPEC-00 §8).
- [x] `ingestion/worker.py`: claim loop with `SKIP LOCKED`, `LISTEN jobs_new`, stale-lock recovery, `process_one_job()`.
- [x] `ingestion/parsers/`: `pdf.py`, `docx.py`, `markdown.py` (front matter), `xlsx.py` (openpyxl, header detection, row groups, `Header: value` lines), `image.py` (OCR).
- [x] `ingestion/chunking.py`: HybridChunker with the bge-m3 tokenizer, merge/split rules, embedded-text prefix.
- [x] `ingestion/metadata.py`: title, effective date, version, department, doc type, language, superseded detection.
- [x] Embedding in batches through `providers.embedder()`, usage logged per document.
- [x] Atomic chunk swap in `service.py`; job/document state transitions per SPEC-03 §3.
- [x] Endpoints 10–11.
### Frontend
- [x] Re-ingest action and failed-state banner with Retry; **Chunks** tab on the detail page.
### Tests
- [x] SPEC-03 §10 checks 3–9, 12 (`@pytest.mark.docling` where Docling runs).
- [x] Invariants: private marker on `/chunks`.

## Acceptance criteria
1. The tests above are green, along with the full gates.
2. **Walkthrough (real ILMU, bge-m3):** start the worker, upload the 10 Serimaju files → all **Ready**; 2024 handbook shows **Superseded** automatically; the leave XLSX chunk for M2 shows the header row and `22`; the memo PNG's chunk contains "10" and "30 April 2027" from OCR; `usage` shows embedding tokens per document. Record ingestion time and tokens for the slides.
3. **Deviations recorded**, or *"Deviations: none"*.

**Status:** IMPLEMENTED (2026-11-20), awaiting human review before DONE.
Verified: backend ruff, ruff format, mypy --strict, lint-imports (4 contracts kept) and pytest (93 passed, network guard on, including 3 real-Docling tests); frontend lint, typecheck, test (76 passed) and build. Tests: SPEC-03 §10 checks 3-9, 12-14, 16, 17 (check 15 was already covered in M01), SPEC-08 §4.6-4.7 (re-ingest 202/409/404, chunks page/around/foreign chunk), and the private-marker invariant on `/chunks`, `?around` and `/reingest`.
Walkthrough (real ILMU, bge-m3, dev database, worker + API running locally, 2026-11-20): all 10 Serimaju files uploaded as Ben reached **Ready** in about 3.5 minutes (69 chunks, all embedded, one `embedding_model`). The 2024 handbook became **Superseded** on its own and its chunks carry `doc_status = superseded`; a re-ingest of all ten kept that status. `Leave_Entitlement_by_Grade_2026.xlsx` chunk for the Annual Leave sheet has the header row and `Manager ... More than 5 years: 22`; the memo PNG's OCR chunk contains "10" and "30 April 2027". Markdown front matter gave title, version 2.3, effective 2026-02-01 and department Finance. Ingestion usage (re-ingest run, embeddings only): 8,415 tokens over 10 calls, about RM 0.0005, 130-530 ms per call. Docling timing for the slides: about 6.5 s per PDF page, DOCX/Markdown under 1 s, JPG 14 s, scanned PNG 76 s, first run adds about 3 minutes of model downloads (SPEC-00 O2, O3 updated). The dev database still holds the 10 ingested documents for M03.
Found and fixed on the way: (1) M00's `UsageRecorder` raised `ArgumentError` when bound to an engine, so no `usage` row was ever written outside tests; fixed with a regression test (`test_spec06_ac04_usage_is_written_when_bound_to_an_engine`). (2) The chunk swap re-read the document under a lock but got the stale in-session object; the locking reads now use `populate_existing`, which SPEC-03 §10 checks 13 and 14 caught. (3) M01's `test_list_filters_and_order` was flaky (both uploads share the test transaction's `now()`); made deterministic.
Scope notes (no deviation): the Dockerfile and Compose worker image stay M99; Docling models were downloaded to the local Hugging Face cache for the run, and the Docling tests set `HF_HUB_OFFLINE=1`. `TOKENIZER_ID` (default `BAAI/bge-m3`) is a new env var, added to SPEC-11 §3 and `.env.example`, because the model name may not appear in app code outside `config.py`. The Chunks tab is the default tab on the detail page; the row menu's Re-ingest is disabled while a document is queued or processing.
Opus review (2026-11-20), fixes with no new deviation: `DOCLING_ARTIFACTS_PATH` is now a setting (was read from `os.environ` in the parser; added to `.env.example` and SPEC-11 §3); a retryable 5xx requeue records `provider`, not `rate_limit`; a job whose document was deleted before it failed ends `done`, not `failed` (§1 rule 5); stale recovery uses the ORM instead of raw SQL; the engine hides SQL parameters so a logged DB error carries no chunk text; one failed worker step no longer stops the worker; the Docling import contract now covers the non-parser `app.ingestion` modules and `docling_core`; the detail page polls when opened on a queued/processing document. New tests: embedding-model mix guard (§9), outage requeue code, failure after delete. Gates: pytest 96 passed, frontend 76 passed.
Deviations: D002.
