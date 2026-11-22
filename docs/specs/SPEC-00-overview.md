# SPEC-00 — Overview

> **Status:** v1 (2026-11-19) · **Owner of:** concepts, glossary, global conventions, success criteria, open items
> **Read with:** [IDEA](../IDEA.md)

## 1. What we build

A company-docs question-answering system that answers only from uploaded documents, with citations.

Pipeline: **upload → background ingestion (parse → chunk → embed) → hybrid search (vector + full-text, RRF) → grounded answer with citations, streamed over SSE**.

Parts:
- `api`: FastAPI. Upload, document list, search, chat (SSE), usage.
- `worker`: a separate process that claims ingestion jobs from a Postgres `jobs` table (`SELECT … FOR UPDATE SKIP LOCKED`).
- `postgres`: PostgreSQL 17 + pgvector. One database for documents, chunks, vectors, full-text and usage.
- `frontend`: Vue 3 + Vite + TypeScript, built on the Office Suite UI kit (Tailwind v4 + shadcn-vue + design tokens), served by nginx.

## 2. Concepts

- **Document**: one uploaded file plus its metadata (title, type, department, effective date, version, `status`, `access_groups`).
- **Chunk**: a structure-aware piece of a document (a section, a table, a group of spreadsheet rows or an image's text), with its heading path, page or section, and an embedding.
- **Ingestion job**: one row in `jobs`. Its state is mirrored onto `documents.ingest_status` for the UI.
- **Source**: a chunk sent to the LLM, numbered `[1]…[n]` for one answer.
- **Citation**: a `[n]` marker in the answer that points at a source. It is clickable in the UI.
- **Not found**: the standard refusal, used when no source answers the question. It suggests a contact.
- **Superseded**: a document replaced by a newer version. It is never retrieved.
- **Access group**: a label on a document (e.g. `all`, `hr`). A user sees and retrieves only documents sharing at least one group with them.
- **Provider role**: `answer`, `fast`, `fallback`, `vision`, `embed`, `rerank`, `judge`. Each role maps to a model in config ([SPEC-06](SPEC-06-ai-providers.md)).

## 3. Glossary

| Term | Meaning |
|---|---|
| RRF | Reciprocal Rank Fusion: `score = Σ 1 / (k + rank)`, with k = 60 |
| HNSW | pgvector's approximate nearest-neighbour index |
| SSE | Server-Sent Events, the streaming format of `POST /api/v1/chat` |
| ILMU | ILMU AI, a Malaysia-hosted, OpenAI-compatible LLM provider (demo provider) |
| Fake mode | `AI_PROVIDER=fake`: deterministic fakes for every role, no network. Used in tests and for UI work |
| Private marker | `ZQX-PRIVATE-7`, a string placed only in a restricted test document ([SPEC-09 §4](SPEC-09-security-and-access.md)) |
| Serimaju | The fictional sample company and document set in `samples/serimaju/` |

## 4. Non-goals

See [IDEA](../IDEA.md#non-goals-for-this-build). Also: no conversation memory on the server (each question stands alone; the thread lives in the browser), no OCR model training, no PPTX.

## 5. Spec map

| Spec | Owns |
|---|---|
| [SPEC-01](SPEC-01-architecture.md) | Repo layout, module boundaries, provider interfaces + fakes |
| [SPEC-02](SPEC-02-database-schema.md) | **Every** table shape, plus the table → milestone map |
| [SPEC-03](SPEC-03-ingestion.md) | Upload validation, jobs, parsing per type, chunking, metadata, superseded detection, re-ingest |
| [SPEC-04](SPEC-04-retrieval.md) | Hybrid search, RRF, filters before ranking, reranker |
| [SPEC-05](SPEC-05-answering.md) | Prompt, citations, refusal, streaming events |
| [SPEC-06](SPEC-06-ai-providers.md) | Provider config, roles, retries, 429/402, usage logging, portability |
| [SPEC-07](SPEC-07-frontend.md) | Pages, components, states, reuse of the Office Suite kit |
| [SPEC-08](SPEC-08-api-contract.md) | **Every** endpoint and the one error shape |
| [SPEC-09](SPEC-09-security-and-access.md) | Uploads, secrets, identity, access groups, data rules |
| [SPEC-10](SPEC-10-testing-and-eval.md) | Test conventions, invariants, eval script and scoring |
| [SPEC-11](SPEC-11-deployment.md) | Docker Compose, env, run book |

## 6. Global conventions

These apply everywhere. A rule here beats any other spec, and a conflict is a deviation ([DEVIATIONS](../DEVIATIONS.md)).

### 6.1 Source of truth
1. Specs are the source of truth. Code that disagrees with a spec is either a bug or a logged deviation.
2. **SPEC-02 owns every table.** A new column or table is a SPEC-02 change in the same change as the migration.
3. **SPEC-08 indexes every endpoint.** A new endpoint is a SPEC-08 row in the same change.
4. Milestones are worked in number order, one at a time; a milestone's *Read first* line lists the sections to load.

### 6.2 Names and formats
- IDs are UUID v4 (`documents`, `chunks`, `questions`). `jobs.id` and `usage.id` are `bigserial`.
- Timestamps are `timestamptz` in UTC and ISO 8601 in JSON. The UI formats them in `Asia/Kuala_Lumpur`.
- JSON fields are `camelCase` in the API (Pydantic alias generator), `snake_case` in Python and SQL.
- Enumerations are lowercase strings (`queued`, `current`, `superseded`).
- Migrations are named `M<nn>_<topic>` after the milestone that adds them (e.g. `M00_initial`).
- Money is `numeric(12,6)` in MYR.

### 6.3 Layering (backend)
- Routers in `app/api/` only validate, call one service, and map results. **No SQL in routers.**
- **All document and chunk writes go through `app/ingestion/service.py`** (upload, status change, re-ingest, delete).
- **All retrieval goes through `app/retrieval/search.py`**, which always filters chunks by `doc_status = 'current'`, the configured `embedding_model` and the caller's `access_groups` **before** ranking, in both search arms. Deleted documents have no chunks.
- **No provider SDK import and no model name outside `app/providers/`** (model names may also appear as defaults in `config.py`). Code asks for a role (`providers.chat("answer")`).
- Every provider call logs a `usage` row ([SPEC-06 §6](SPEC-06-ai-providers.md)).

### 6.4 Errors
- One error shape, `application/problem+json` ([SPEC-08 §2](SPEC-08-api-contract.md)). Error codes are stable `snake_case` strings; the UI branches on `code`, never on `detail`.
- Error messages say what happened and how to fix it. Secrets, stack traces and prompt text are never in responses.

### 6.5 Answers
- Answers come **only** from retrieved chunks, and every factual sentence carries at least one `[n]` citation.
- No relevant source → the standard not-found answer with a contact ([SPEC-05 §5](SPEC-05-answering.md)). Never a guess.
- When sources conflict, the newer effective date wins and the answer says so.

### 6.6 Security
- Secrets only in env (`.env` is gitignored). Never in specs, prompts, logs or committed files.
- The private marker never appears for a non-member: not in search results, answers, citations, document lists or file downloads.
- Fake provider mode is refused when `APP_ENV=production`.

### 6.7 Tests
- Every numbered acceptance check in a spec becomes a test named after it: pytest `test_spec04_ac02_superseded_never_retrieved`, Vitest `it('Spec07_Ac03 …')`.
- Tests never call the network. A guard fails any outbound connection except the test database.
- Full gates: backend `ruff check`, `ruff format --check`, `mypy`, `pytest`; frontend `lint`, `typecheck`, `test`, `build`.

### 6.8 Copy and UI
- Sentence case, buttons name their action, no emoji, errors say how to fix the problem ([design system §1](../design-system.md)).
- No raw colours in the frontend: tokens only (ESLint rule).

## 7. Success criteria

1. All 10 Serimaju documents ingest to `ready`, with the 2024 handbook marked `superseded`.
2. Eval score **≥ 26 / 32** on nemo-super (baseline target). Q01 (memo override), Q28 (Malay) and Q30–Q31 (not found) are correct.
3. First answer token arrives in **≤ 3 s** at p50 on the demo machine (with thinking off).
4. The private-marker invariant suite is green.
5. `docker compose up` brings up the whole stack on a clean machine following the [SPEC-11](SPEC-11-deployment.md) run book.
6. The repo shows the SDD artifacts: specs, milestones in `done/`, deviation log, CLAUDE.md files, plan files.

## 8. Schedule and open items

**Schedule** (presentation **Thu 2026-11-26**; adjust to your working days):

| Day | Target |
|---|---|
| Thu 19 | Specs, milestones, CLAUDE.md, review of SPEC-00/02/08 and M00 |
| Fri 20 | M00, M01 |
| Sat 21 – Sun 22 | M02, M03 (M05 can run in a parallel session) |
| Mon 23 | M04, M05 |
| Tue 24 | M06 baseline eval, M07 (vision) |
| Wed 25 | M08 if time, M99, slides, dry run |
| After 26 | M100 public preview (Cloudflare Tunnel + Access) |

**Open items**

| # | Item | Owner | Status |
|---|---|---|---|
| O1 | Company policy for ILMU with real documents (demo uses fictional data only) | User | Not needed for the demo |
| O2 | ILMU rate limit for plan models (PAYG default is 60 requests/min per model; read `x-ratelimit-limit-requests`) | M02 | Partly answered (2026-11-20): 10 documents, 20 embedding calls in about 7 minutes, no 429. The plan-model (chat) limit is still to be read in M04 |
| O3 | Docling CPU time per page on the demo machine; first run downloads layout and OCR models | M02 | Answered (2026-11-20, Windows laptop, CPU, torch 2.15): about 6.5 s per PDF page (4-page handbook 26.6 s, 1-page notice 4.2 s); DOCX and Markdown under 1 s; JPG org chart 14 s; 1 scanned PNG memo 76 s. First run adds model downloads (about 3 minutes). Whole venv with all groups 1.3 GB. All 10 samples are Ready in about 3.5 minutes |
| O4 | Contact list for the not-found answer (default: HR and Finance mailboxes from the samples) | M04 | Open |
| O5 | Azure AI Foundry endpoint and auth details for the production profile | M99 (README) | Open |
