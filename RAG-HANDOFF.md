# HANDOFF — Company Docs RAG (built with Spec-Driven Development)

> Context brief carried over from a planning conversation in Claude (claude.ai), 2026-11-19.
> Purpose: give Claude Code everything needed to write the SDD specs and milestones, then build.

---

## 1. Why this project exists

- The user's boss asked them to **present their SDD workflow** to the other developers, so the team can standardize on using AI agents efficiently. **All developers have Claude Code seats.**
- The user will **build a company-docs RAG system using that SDD workflow** and present it as a **real case study**: actual specs, milestone files, deviation log, CLAUDE.md, and how an Opus orchestrator plus Sonnet subagents built it.
- **Deadline: next week** (presentation ~week of Nov 23–27, 2026; confirm the exact date with the user). Target the build done by about day 4–5, leaving time for slides and a dry run.

## 2. What the system does

Users upload company documents (PDF, DOCX, XLSX, Markdown, PNG/JPG/JPEG). The system extracts, chunks, embeds and stores them. Users ask questions in a chat UI and get **answers grounded in the documents, with citations** to the exact source and page/section.

**Example:** "What's the maximum leave I can take per application?" → finds the current HR policy section → "Up to 10 consecutive working days per application; longer needs HOD approval. Source: HR Handbook 2026, §4.2, p.12."

If nothing relevant is found, it says so and suggests who to contact. **It never guesses** (a wrong policy answer is worse than none).

## 3. The user's SDD workflow (to follow AND to showcase)

**Use the user's real SDD format.** It's modelled on their production project (*Office Suite*: 27 specs, 22+ milestones, 23 deviations), plus a few token-saving improvements from a review of that project. Mirror the structure and the file conventions below exactly.

### 3.1 File layout

```
CLAUDE.md                         ← root: short. What the repo is, how to work, status, commands, "never break" rules
backend/CLAUDE.md                 ← backend architecture rules (loaded only when working in backend/)
backend/tests/CLAUDE.md           ← test conventions (loaded only when working on tests)
frontend/CLAUDE.md                ← frontend architecture rules (loaded only when working in frontend/)
docs/
  IDEA.md                         ← the locked product idea (what, who, why, non-goals)
  design-system.md                ← UI tokens and component look (source for frontend tokens)
  DEVIATIONS.md                   ← deviation rules, template and index (newest first)
  specs/
    SPEC-00-overview.md           ← what we build, concepts, glossary, non-goals, §6 GLOBAL CONVENTIONS, success criteria, open items
    SPEC-01-architecture.md       ← layout, module boundaries, provider interfaces + fakes
    SPEC-02-database-schema.md    ← owns EVERY table shape + a table → milestone map
    SPEC-03-ingestion.md          ← upload, jobs, parsing per file type, chunking, metadata, re-ingest
    SPEC-04-retrieval.md          ← hybrid search, RRF, filters (status, access_groups), reranker
    SPEC-05-answering.md          ← prompt, citations, refusal ("not found"), streaming
    SPEC-06-ai-providers.md       ← ILMU config, roles, 429/402 handling, usage logging, provider portability
    SPEC-07-frontend.md           ← pages, components, states
    SPEC-08-api-contract.md       ← indexes every endpoint; one error shape
    SPEC-09-security-and-access.md← uploads, secrets, access_groups, data rules
    SPEC-10-testing-and-eval.md   ← test conventions, invariants, the eval script and scoring
    SPEC-11-deployment.md         ← Docker Compose, env, run book
  milestones/
    M00-foundation.md … M99-…md   ← active milestones, worked IN NUMBER ORDER, one at a time
    M03-plan.md                   ← optional Opus plan for a hard milestone (see 3.4)
    done/                         ← finished milestones and their plan files are MOVED here
  deviations/
    D001-<short-kebab-title>.md   ← one file per deviation
samples/serimaju/                 ← the fictional test documents (see §5a)
```

**No separate constitution or memory file.** Project-wide rules live in **SPEC-00 §6 Global conventions** and the CLAUDE.md files. Lasting lessons go into the relevant spec or CLAUDE.md rule, not a diary.

### 3.2 CLAUDE.md (root): keep it SHORT

Loaded into every session and every subagent, so every line costs tokens every time. Target **≤ ~5KB**. Sections, in this order:
1. **What this repo is** (5–8 lines) + "The repo is spec-driven" rules: specs are the source of truth; read **SPEC-00 §6** before non-trivial work; **SPEC-02 owns every table**; **SPEC-08 indexes every endpoint**; milestones are worked in number order; each milestone's *Read first* line lists the spec sections to load; deviations are a mandatory log (see 3.5).
2. **How to read specs (token rule):** *"To read a spec section, run `grep -n '^## ' <spec>` to find its line range, then Read with offset/limit. Never read a whole spec unless the milestone says '(whole file)'."*
3. **Status:** one line: which milestones are done, which is next (link). When a milestone is done: tick its boxes, set its **Status** line `DONE (date)` + how acceptance was verified + deviations logged (`D003, D004` or *"Deviations: none"*), then **move it (and its plan file) to `milestones/done/`**.
4. **Model per milestone** table for the **remaining** milestones only (prune rows once done): Milestone · Model (Opus / Sonnet / Opusplan) · Why. Start each milestone in a fresh session (`/clear`). *Opusplan* = `/model opusplan` (plan on Opus, build on Sonnet). If on a different model than the row says, say so first. On Sonnet, if the same test fails twice or a design question comes up, suggest switching to Opus. After a Sonnet milestone, a short Opus session reviews the diff for unlogged deviations and access leaks.
5. **Commands:** infra, backend run/test (one test, CI subset), migrations (named `M<nn>_<topic>`), frontend dev/lint/typecheck/test/build, full stack, eval run.
6. **Never break** (5–8 one-liners that apply everywhere), e.g.: all document/chunk writes go through the ingestion service; every retrieval filters by `status = current` and `access_groups` **before** ranking; answers only from retrieved chunks, with citations; no provider SDK or model name outside `providers/`; secrets only in env, never in files or logs; the private marker (3.6) never appears for a non-member.

Detailed backend, frontend and test rules go in the **nested CLAUDE.md files**, so a frontend subagent never pays for backend rules and vice versa.

### 3.3 Milestone file format

```markdown
# M03 — Retrieval: Hybrid Search and RRF

> **Depends on:** [M02](M02-ingestion.md) · **Blocks:** [M04](M04-answering.md)
> **Read first:** [SPEC-04 §1–4](../specs/SPEC-04-retrieval.md#1-...) →
> [SPEC-02 §3](../specs/SPEC-02-database-schema.md#3-...) · [SPEC-08 §4](../specs/SPEC-08-api-contract.md#4-...)
> **Model:** Opusplan. One-line reason (the hard part).

## Goal
2–4 sentences.

## Tasks
### Backend
- [ ] …
### Frontend
- [ ] …
### Tests
- [ ] SPEC-04 §9 checks 1–5 as `Spec04_Ac01_…`
- [ ] …

## Acceptance criteria
1. The tests above are green, along with the full gates (lint, typecheck, tests, build).
2. **Walkthrough:** concrete, observable steps on the running stack (e.g. with the Serimaju samples).
3. **Deviations recorded**, or *"Deviations: none"*.

**Status:** (filled in when done: DONE (date), test counts, how verified, anything added beyond the list, what's left for later, deviations)
```
- *Read first* names **sections**, not whole files, unless a whole file is genuinely needed ("(whole file)").
- Add a *Checks finished in later milestones* table when a check spans milestones.

### 3.4 Plan files (for Opus/Opusplan milestones)

`M<nn>-plan.md`, written by Opus before building, for Sonnet subagents to follow. Header: source-of-truth spec sections, the milestone file, "Follow CLAUDE.md exactly", and the deviation rule (check the highest D-number first). Then:
- **"What already exists (copy, don't reinvent)"**: a table of *Need → file/class to copy from*. This is a major token saver: subagents don't explore for patterns.
- **"Decisions made here"**: numbered, and **written into the spec** (the plan only points to them).
- **Work split for subagents:** each subagent's tasks, the **files/folders it may touch** (ownership, so parallel subagents don't collide), and what it returns: a short summary (changes, tests green, deviations), not its full work.

### 3.5 Deviations

- `docs/DEVIATIONS.md` holds the rules, the template and the index (newest first).
- **When to log:** a spec instruction is impossible or wrong in practice; two spec sections contradict; a materially different approach (library, table shape, endpoint contract); a deliberately skipped item. **When not:** naming/formatting the specs don't dictate; bug fixes that move code closer to the spec. More than a couple per milestone means the *Read first* list needs re-reading.
- **How:** new `docs/deviations/D<nnn>-<kebab-title>.md` (next free number, never reused) **in the same change as the code** + a row at the top of the index + a `> **DEVIATION:** see [D<nnn>](…) — one-line summary` note at the spec section. If it should become the rule, update the spec instead, set the file to **Resolved → spec updated**, and remove the note. **An unlogged deviation is a bug.**
- Template: `# D<nnn> — title` · Date/milestone · Spec · Status (Open | Resolved → spec updated) · *Spec says* · *Implementation does* · *Why* · *Consequences*.
- **Fold open deviations into the specs at the final milestone** (and whenever a spec collects several), so agents read one current spec instead of spec + deviations.

### 3.6 Tests and invariants

- **Every numbered acceptance check in a spec becomes a test named after it** (e.g. `Spec04_Ac02_SupersededDocsNeverRetrieved`).
- **Providers behind interfaces with fakes:** `FakeChatModel`, `FakeEmbedder` (deterministic vectors), `FakeReranker`, so the full test suite runs **without ILMU tokens or network**. A guard fails any real outbound call in tests. Fake mode is refused in production.
- **Invariant suite** that grows every milestone. A **private marker** (e.g. `ZQX-PRIVATE-7`) is put in a document whose `access_groups` exclude the test user; it must **never** appear in any search result, answer, citation or API response for that user, even before access enforcement is switched on in the UI.
- Acceptance = tests green + walkthrough + deviations recorded. Opus verifies before setting DONE.

### 3.7 Working rules

- Human review at milestone boundaries, especially after M00 (contracts).
- Git: one branch per milestone; commits reference the milestone (`M03: …`).
- Keep stale docs out of the way: anything describing an old state is updated or moved to `done/`. Agents trust what they read.

## 4. Tech stack (agreed)

| Layer | Choice | Notes |
|---|---|---|
| Backend | **FastAPI**, Python 3.10, `uv`, Pydantic v2 | Async API; SSE for streaming answers |
| DB | **PostgreSQL + pgvector** (HNSW) + Postgres full-text (`tsvector`) | One DB for docs, chunks, vectors, keyword search, metadata. Hybrid search merged with **RRF in SQL**. |
| DB access | SQLAlchemy 2 + Alembic | |
| Parsing | **Docling** | PDF, DOCX, XLSX, images (OCR), Markdown; keeps headings/tables. Verify current format support and install weight (models) early. |
| Images/diagrams | nemo-super image input where OCR isn't enough | |
| Background jobs | Separate **worker** process + Postgres `jobs` table using `SELECT … FOR UPDATE SKIP LOCKED` | No Redis/Celery for the MVP. Ingestion never runs inside a web request. |
| AI provider | **ILMU AI (Malaysia)**, **OpenAI-compatible API** | Data processed and stored in Malaysia (provider states PDPA 2010 support). One OpenAI-compatible client for all models; model names in config. See §4a. |
| LLM (answers + vision) | **nemo-super** (plan quota) | 256K context, function calling, thinking, JSON mode, **image input**. Thinking off/low for normal questions. |
| LLM (cheap/Malay steps) | **ilmu-nemo-nano** (plan quota) | Faster; deeper Bahasa Malaysia training. Query rewriting, per-document summaries/tags; test on Malay questions. |
| LLM fallback | **ilmu-glm-5.3-flash** (PAYG) | Only if nemo models fail a task; compare on the eval set. Not glm-5.3 (coding model, pricier). |
| Embeddings | **bge-m3** via ILMU (PAYG, RM 0.04/1M tokens) | Multilingual (English + Malay), **1,024 dims**, up to 8,192 input tokens. **Do not use ilmu-embedding-v1**: 4,096 dims exceeds pgvector's HNSW index limit (2,000 for `vector`, 4,000 for `halfvec`), forcing full scans. |
| Reranker | **bge-reranker** via ILMU (PAYG, RM 0.04/1M tokens) | **Later milestone**, behind an interface. Retrieve ~30–50, rerank to 5–8. |
| Frontend | **Vue 3 + Vite + TypeScript**, Pinia, Vue Router | |
| UI | Tailwind + **PrimeVue** | Upload, tables, dialogs built in |
| Chat UX | SSE streaming, Markdown rendering (markdown-it), **clickable citations** opening the source at the right page (pdf.js) | |
| Deploy | **Docker Compose**: `api`, `worker`, `postgres`, `frontend` (nginx) | One command to run |
| Tests | pytest, Vitest, plus an **eval script** (~30 real Q&A pairs) | The eval score is also a presentation slide |

### 4a. ILMU AI provider details (confirmed by user, 2026-11-19)

- **OpenAI-compatible API.** Use the official `openai` Python SDK with ILMU's base URL; API key via env (`ILMU_API_KEY`, `ILMU_BASE_URL`). Keep model names in config (`LLM_ANSWER_MODEL=nemo-super`, `LLM_FAST_MODEL=ilmu-nemo-nano`, `LLM_FALLBACK_MODEL=ilmu-glm-5.3-flash`, `EMBED_MODEL=bge-m3`, `RERANK_MODEL=bge-reranker`). Check ILMU docs for the exact base URL, and whether embeddings and rerank use the OpenAI-style `/embeddings` endpoint or a separate rerank endpoint.
- **Billing modes:**
  - **Plan (token quota):** the user's **Claw plan, 50M tokens**. ILMU's docs describe plan quota as a *monthly allocation per seat*; confirm whether 50M is monthly or a one-off prepaid amount. Covers **nemo-super and ilmu-nemo-nano**.
  - **PAYG (RM credit):** any model outside the plan, i.e. **bge-m3, bge-reranker, GLM**. The user needs PAYG credit topped up for embeddings and reranking (cost is tiny).
- **Error handling (must be in specs):**
  - **HTTP 429:** per-minute rate limit → retry with exponential backoff + jitter, honour `Retry-After` if present. The ingestion worker throttles itself (concurrency limit, batch embeddings).
  - **HTTP 402:** plan quota or PAYG balance exhausted → **don't retry**. Surface a clear error (UI + logs), mark ingestion jobs as `failed: quota` so they can be resumed, and optionally fall back to the fallback model for answers.
- **Budget estimate:** a RAG question with 5–8 retrieved chunks ≈ 5–10K tokens → 50M ≈ several thousand questions. Vision ingestion of images costs more per file. Log token usage per request (from API responses) to a `usage` table, so cost per question and per ingestion can be shown, which is also a good presentation slide.
- **Data residency:** ILMU states all data is processed and stored in Malaysia, with PDPA support. Mention this in the presentation's data/guardrails section. Still confirm the company policy allows this provider.
- **Model evaluation:** run the eval set with nemo-super (main), then ilmu-nemo-nano and ilmu-glm-5.3-flash, and compare scores, latency and tokens. Key checks: memo override (Q01), Malay question (Q28), not-found questions (Q30–31).

### 4b. Provider portability (production will NOT use ILMU)

ILMU is for the user's **experiments and the build/demo only**. If the company adopts the system for production, it must run on **a different OpenAI-compatible provider or Azure AI Foundry**. Design for switching providers by **config, not code changes**:

- **Provider profiles in config/env:** `base_url`, `api_key`, auth style, and model/deployment names per role (answer, fast, fallback, vision, embed, rerank). Azure uses *deployment names*, and its auth/endpoint style differs from plain OpenAI. Verify Azure's current OpenAI-compatible (v1) endpoint and auth in its docs before speccing, and keep an adapter layer so Azure-specific details stay in one module.
- **Role-based interfaces:** `ChatModel`, `VisionModel`, `Embedder`, `Reranker`. App code never imports a provider SDK or hardcodes model names.
- **Capability flags per provider:** e.g. `supports_thinking`, `supports_image_input`, `supports_json_mode`, `has_reranker`. Not every provider offers a reranker (on Azure it may be a separately deployed model such as a Cohere rerank model, or absent), so retrieval must work **with reranking turned off**.
- **Embeddings are the hard part of switching.** A different embedding model means different vectors and dimensions, so **all chunks must be re-embedded**. Therefore:
  - Store `embedding_model` and `embedding_dim` with each chunk (or per embedding table), and never mix models in one index.
  - Provide a **re-embed command/job** (background, resumable, batch, rate-limit aware) that fills a new embedding column/table, then switches over.
  - Keep vector dims within pgvector index limits (≤ 2,000 for `vector`, ≤ 4,000 for `halfvec`). If a production model outputs more, use a model option to shorten embeddings, if offered, or `halfvec`.
- **Prompts may need re-tuning** for different models. The **eval set is the acceptance gate for any provider switch**: run all 32 questions and compare with the ILMU baseline before going live.
- **Usage/cost logging per provider and model**, with price config, so cost comparisons are easy.
- **Data residency for production:** check where the chosen provider/region processes and stores data (e.g. which Azure region, and whether the needed models are available there) against company policy and client contracts.
- **README / presentation:** document "How to switch provider" as a short procedure: set env, run re-embed, run eval, compare, go live.

**Deliberate choice: no LangChain/LlamaIndex.** Thin custom code (parse → chunk → embed → search → answer) is easier for developers and agents to trace, and fits the SDD message. Explain this in the presentation.

## 5. Key design rules

**Ingestion**
- Parse by file type; keep structure (headings, lists, tables).
- **Excel:** don't chunk as prose. Convert each sheet/table to structured rows or a Markdown table, with column headers repeated in every chunk.
- **Chunk by structure** (e.g. a whole policy section), not fixed size. Attach the heading path ("HR Handbook > Leave > Annual Leave").
- **Metadata on every chunk:** source document, page/section, heading path, document type, department, effective date / version, `access_groups`.
- **Re-ingest by content hash:** only changed files; delete chunks of removed or replaced files. Track job status (queued / processing / done / failed + error) for the UI.
- Optional: an ilmu-nemo-nano-generated short summary + topic tags per document.
- **Images and scanned pages:** OCR via Docling first; if the text is empty or poor, or the image is a diagram, send it to **nemo-super (image input)** for a text description/extraction.
- **Superseded documents:** store `status` (current / superseded) as metadata (e.g. detected from the "SUPERSEDED" marker or set by an admin) and filter out superseded docs at retrieval. Don't rely on the LLM to notice.

## 5a. Test data

A **fictional document set** (`serimaju-demo-docs.zip`) was generated for development and the demo: **Serimaju Technologies Sdn Bhd**, a KL tech startup whose clients are a bank, a manufacturer and an asset manager. Contents:
- `documents/`: 10 files (3 PDFs incl. a superseded 2024 handbook and a Malay/English notice; 2 DOCX; 2 XLSX; 1 Markdown; a scanned-looking memo PNG that overrides the handbook; an org chart JPG). **Ingest these.**
- `eval/eval_questions.csv`: 32 questions with expected answers, sources and categories (version traps, OCR override, vision, multi-hop, Malay, not-found). **Never ingest.**
- `FACT_SHEET.md`: ground truth. **Never ingest.**
Put the zip contents under `samples/serimaju/` in the repo. The eval script (SPEC-10, milestone M06) should read the CSV, query the API, and score each answer as correct (1), partial (0.5) or wrong (0), using an LLM judge (nemo-super) against `expected_answer` plus a check of cited sources.

**Retrieval**
- Hybrid: vector (meaning) + full-text (exact terms like form numbers, day counts), fused with RRF.
- Filter by metadata **before** ranking (current version only; later, permissions).

**Answering**
- Answer only from retrieved context; cite every claim (doc title, section, page). No relevant context → say so, suggest a contact.
- Stream the response.

## 6. Security & data rules (raise these with the user before building)

1. **Don't use real company documents on a personal home server.** Use company infrastructure, or demo with sample or non-sensitive documents.
2. **Confirm company policy** allows sending company documents to ILMU AI (embeddings + LLM). ILMU processes and stores data in Malaysia (PDPA support), which should help. If an external API isn't allowed, bge-m3 can run locally. Good material for the presentation's "guardrails" section.
3. **Permissions:** design the `access_groups` field on documents **now**, even though the MVP won't enforce it. Don't ingest anything not everyone may see until filtering exists (filter **before** search, not after).
4. Secrets via env / `.env` (gitignored); never in specs, prompts or committed files.
5. Upload validation: allowed types, size limits, filename sanitization; store originals in a mounted volume (S3/MinIO later).

## 7. MVP scope

- **Must-have:** upload PDF/DOCX/MD → background ingestion with status → hybrid search → streaming chat answers with clickable citations → document list page → Docker Compose → basic tests.
- **If time allows:** XLSX, images (OCR + vision), reranker, eval script + score, re-ingest changed files, per-document summaries.
- **Later (present as next steps):** permission enforcement with company SSO, version/superseded-policy handling, sync from SharePoint/Google Drive, admin analytics (unanswered questions), Malay/English evaluation.

## 8. Suggested milestones (Opus to refine into milestone files, format §3.3)

Worked in number order, one at a time, each in a fresh session. Inside a milestone, Opus may run parallel Sonnet subagents with file ownership (§3.4). Initial **model per milestone** table for CLAUDE.md:

| Milestone | Model | Why |
|---|---|---|
| M00 Foundation and contracts | Opus | Repo layout, Compose, DB + first migration, SPEC-02 tables, SPEC-08 API contract, provider interfaces + fakes, test host. Everything later depends on it. **Human review after.** |
| M01 Upload and documents | Sonnet | Upload validation, file storage, document list/status API |
| M02 Ingestion pipeline | Opusplan | Worker + `jobs` table (`SKIP LOCKED`), Docling for PDF/DOCX/MD, structure-aware chunking, metadata, bge-m3 embeddings, 429/402 handling |
| M03 Retrieval | Opusplan | Hybrid SQL search + RRF; `status`/`access_groups` filters before ranking; private-marker invariant |
| M04 Answering and chat API | Opus | Prompt, citations, refusal on not-found, SSE streaming, usage logging |
| M05 Frontend | Sonnet | Upload page, documents list with status, chat with streaming + clickable citations (pdf.js). Can start after M00 against the API contract with mocks. |
| M06 Evaluation | Sonnet | Eval script over `samples/serimaju/eval/eval_questions.csv`, LLM judge, score report; baseline run on nemo-super |
| M07 XLSX and images *(stretch)* | Opusplan | Excel rows with headers; OCR, then nemo-super vision fallback; superseded-status detection |
| M08 Reranker and re-ingest *(stretch)* | Sonnet | bge-reranker behind its interface (off by default); hash-based re-ingest and deletions |
| M99 Release and demo | Opus | Security sweep, fold open deviations into specs, README, demo script, final eval run, model comparison (nemo-super / nemo-nano / glm-5.3-flash) |

M00 is the serial "contracts" milestone. Human review there catches design drift before everything builds on it. M05 can be developed in parallel with M02–M04 if time is short (separate Claude Code session, frontend-only file ownership).

## 9. Presentation (after the build)

The presentation is **the story of building this project with SDD**:
- The workflow: IDEA → specs (SPEC-00 §6 conventions) → milestones in order with *Read first* sections → model per milestone (Opus / Sonnet / Opusplan) → plan file with "copy, don't reinvent" → Sonnet subagents build with file ownership → spec checks as named tests + invariants → deviations logged in the same change → DONE status block → move to `done/`.
- Show **real artifacts** from this repo (the model table, a *Read first* line, a plan file's "copy from" table, a deviation file, a DONE status block, CLAUDE.md).
- Token-saving rules and their effect (section reads instead of whole specs, short root CLAUDE.md + nested ones, archived milestones).
- What went wrong and how deviations captured it; how file ownership/worktrees prevented collisions.
- Numbers if available: time per milestone, eval score, number of subagents/tasks.
- Guardrails for team adoption: permissions/allowlists, sandboxing, no prod secrets, protected paths, PR + CI gates, human review at milestone boundaries, prompt-injection awareness, data policy for company documents.
- A **starter template** (root + nested CLAUDE.md, SPEC-00 skeleton with §6 conventions, milestone/plan/deviation templates, DEVIATIONS.md) other developers can copy. That's the "standardize" outcome the boss wants.
- Deck can be made later (Claude Slides or PowerPoint, user's choice).

## 10. First instructions for Claude Code

1. Read this file fully.
2. Ask the user: (a) exact presentation date; (b) company approval for ILMU AI and where the system will run (sample vs. real docs); (c) whether the 50M ILMU plan tokens are monthly or one-off, and that PAYG credit is topped up for bge-m3 / bge-reranker.
3. Verify current Docling format support and install size, and ILMU's API docs (base URL, embeddings/rerank endpoints, bge-m3 dimensions, rate limits) before fixing them in specs.
4. Write the docs in the §3 format: `docs/IDEA.md`, `SPEC-00`…`SPEC-11`, `DEVIATIONS.md` (rules + template + empty index), the milestone files M00–M99, the root CLAUDE.md (≤ ~5KB) and the nested `backend/`, `backend/tests/`, `frontend/` CLAUDE.md files. Every spec gets numbered `##` sections and a final *Acceptance checks* section. Get the user's review of SPEC-00, SPEC-02, SPEC-08 and M00 before building.
5. Then build milestone by milestone: Opus (or Opusplan) writes the plan file where the model table says so, Sonnet subagents build with file ownership, tests prove acceptance, deviations are logged in the same change, the Status block is filled in, and the finished milestone moves to `milestones/done/`.
