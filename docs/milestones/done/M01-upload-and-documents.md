# M01 — Upload and documents

> **Depends on:** [M00](M00-foundation.md) · **Blocks:** [M02](M02-ingestion.md)
> **Read first:** [SPEC-03 §1–2, §7](../specs/SPEC-03-ingestion.md#1-rules) · [SPEC-08 §2, §4.1–4.5](../specs/SPEC-08-api-contract.md#2-error-shape) · [SPEC-09 §2–4](../specs/SPEC-09-security-and-access.md#2-upload-validation-securityuploadspy) · [SPEC-02 §2, §4](../specs/SPEC-02-database-schema.md#2-documents)
> **Model:** Sonnet. Well-specified CRUD and validation.

## Goal
Users can upload files, see them listed with metadata and ingestion status, edit metadata (including `status` and `access_groups`), download the original and delete documents. Upload enqueues a job but nothing processes it yet.

## Tasks
### Backend
- [x] `security/uploads.py`: magic-byte detection, streaming size limit, zip-bomb guard, filename sanitizing.
- [x] `ingestion/service.py`: `create_document`, `update_document` (propagates `status`/`access_groups` to chunks), `delete_document`, all in one transaction each; file write with temp + rename and cleanup on failure.
- [x] `ingestion/jobs.py`: `enqueue(kind, document_id)`.
- [x] Endpoints 4–9 with group filtering and 404-for-hidden.
### Frontend
- [x] `features/documents`: `api.ts`, `store.ts`, `DocumentsPage` (UploadPanel with multi-file FileDrop + details, DataTable, filters, row actions, polling), `DocumentDetailPage` (metadata + Original tab; Chunks tab arrives in M02), `IngestStatusPill`, `DocumentMetaDialog`, ConfirmDialog for delete.
### Tests
- [x] SPEC-03 §10 checks 1, 2, 10, 11.
- [x] SPEC-08 §8 check 3.
- [x] SPEC-09 §8 checks 1–4 (4: list/get/file paths only), 7.
- [x] SPEC-07 §11 checks 8, 9.
- [x] Invariants: private marker on documents list/get/file.

## Acceptance criteria
1. The tests above are green, along with the full gates.
2. **Walkthrough:** as Ben, upload all 10 Serimaju files → each shows **Queued**; uploading one again shows "Already uploaded"; edit one document's department; mark the 2024 handbook superseded; download a PDF original; delete a document and see it disappear. As Aisyah, upload `backend/tests/fixtures/private_salary_bands.md` with access group `hr`; switch to Ben → it is not listed and its URL returns 404.
3. **Deviations recorded**, or *"Deviations: none"*.

**Status:** IMPLEMENTED (2026-11-20), awaiting human review before DONE.
Verified: backend ruff, ruff format, mypy --strict, lint-imports (4 contracts) and pytest (60 passed, network guard on); frontend lint, typecheck, test (72 passed) and build. Walkthrough run against a live API from the terminal (fake AI, dev database, since cleaned): Ben uploaded all 10 Serimaju files, each `queued`; the same bytes again gave `409 duplicate_document` naming the existing title; PATCH changed a department and marked the 2024 handbook superseded; the downloaded PDF was byte-identical with `nosniff`; delete returned 204 and the list shrank 10 → 9; Aisyah uploaded `private_salary_bands.md` with group `hr`, and for Ben it was absent from the list and its URL returned 404. Then a live browser pass with Playwright MCP (2026-11-20, API on :8000 with fake AI, Vite on :5173): Ben uploaded all 10 files in one batch (all Queued); a duplicate showed "Already uploaded as" with a working link; the edit dialog saved department, version and effective date; Mark superseded moved the row under the Superseded filter; the detail page and Download original worked (byte-identical file); delete went through the confirm dialog; Aisyah uploaded the private file with group `hr`, and for Ben it was absent from the list and its URL showed "Document not found"; dark theme and the 390 px card layout rendered without contrast or overflow problems. The pass found the Documents nav entry unhighlighted on the detail page; fixed (`alsoActiveFor` in `navigation.ts`, with a test). Known and left for M00 follow-up: resizing the window from desktop to phone width without a reload leaves the sidebar open over the content (a fresh load at phone width is correct).
Scope notes (no deviation): the **Re-ingest** row action and the **Retry** button on the failed banner wait for M02, which adds `POST /documents/{id}/reingest`; the detail page has the Original tab only until M02 adds Chunks; the original viewer shows images inline and offers Download for other types until the M05 source panel. A zip over 2,000 entries or 200 MB uncompressed returns 415 `unsupported_type` (SPEC-09 §2 names no status). The upload route also refuses an oversized `Content-Length` before the multipart body is parsed, in addition to the streaming limit.
Deviations: none.
