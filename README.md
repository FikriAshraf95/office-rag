# Company Docs RAG

Ask questions about your company's documents and get streamed answers that cite the exact page, section or spreadsheet row they came from. When the documents don't say, it says so and tells you who to ask. It never guesses.

- **Upload** PDF, DOCX, XLSX, Markdown, PNG and JPG. A background worker parses them with Docling (layout, tables, OCR), splits them by heading structure, and stores bge-m3 embeddings in PostgreSQL + pgvector.
- **Ask** in English or Malay. Hybrid search (vector + full text, fused with RRF, optional reranker) runs with access-group and "current version only" filters applied *before* ranking. The model answers only from the retrieved passages; every claim carries a `[n]` citation that opens the source at the right page.
- **Stack:** FastAPI, a worker process, PostgreSQL 17 + pgvector, Vue 3. The demo provider is [ILMU](https://docs.ilmu.ai) (OpenAI-compatible, data in Malaysia). Switching providers is a config change plus an eval run (see below).
- **Demo data:** `samples/serimaju/` is a fully fictional company, with deliberate traps: a superseded handbook, a scanned memo that overrides it, an org chart that exists only as an image, a Malay notice, and questions with no answer.

This repo is also the case study for spec-driven development (SDD): every behaviour is specified in [`docs/specs/`](docs/specs/) before it's built, work is cut into [milestones](docs/milestones/), and every place where the code knowingly differs from a spec is logged in [`docs/DEVIATIONS.md`](docs/DEVIATIONS.md).

## Run it

**Needs:** Docker with Compose v2, and an ILMU API key.

```bash
cp .env.example .env            # then set AI_API_KEY
docker compose up -d --build    # first build bakes the Docling models into the worker image (~1–2 GB)
```

Open **http://localhost:8080**.

1. Pick a demo user in the top bar: **Ben (Staff)** sees `all` documents; **Aisyah (HR)** also sees `hr` documents.
2. Go to **Documents** and upload everything in `samples/serimaju/documents/`.
3. Wait until every row shows **Ready**. The 2024 handbook shows **Superseded**, so it is never searched.
4. Ask questions in **Chat**. Example questions with expected answers are in `samples/serimaju/eval/eval_questions.csv`; the demo script is in [`docs/demo-script.md`](docs/demo-script.md).

| Service | Host port | |
|---|---|---|
| `frontend` (nginx) | `127.0.0.1:8080` | The app. Proxies `/api` and `/health` to the API; SSE unbuffered |
| `api` | `127.0.0.1:8000` | Runs migrations, then uvicorn. OpenAPI at `/docs` |
| `worker` | — | Ingestion jobs. Models are baked in; no downloads at run time |
| `postgres` | `127.0.0.1:5433` | pgvector/pgvector:pg17 |

All ports bind to loopback. **Reset everything:** `docker compose down -v` (drops the database and stored files).

### Local development

Postgres in Docker; API, worker and frontend on the host ([SPEC-11 §4](docs/specs/SPEC-11-deployment.md#4-run-book)).

```bash
uv python install 3.14                                   # once
docker compose up -d postgres
cd backend && uv sync --all-groups && uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000         # API
uv run python -m app.ingestion.worker                    # worker (second terminal)
cd frontend && npm ci && npm run dev                     # http://localhost:5173
```

Checks: `uv run pytest -q` (fake AI, no network), `uv run ruff check . && uv run mypy app && uv run lint-imports`, and in `frontend/` `npm run lint && npm run typecheck && npm run test`.

### Evaluation

```bash
cd backend && uv run python -m app.eval --base-url http://localhost:8000 --user ben --label <name>
```

Asks all 32 questions through the API like a user, has a judge model score each answer (correct 1, partial 0.5, wrong 0), and writes a report to `eval-results/`. Model comparison: [`eval-results/comparison.md`](eval-results/comparison.md).

## How to switch provider

The app only knows *roles* (`answer`, `fast`, `vision`, `embed`, `rerank`); provider and model names live in `.env` and `backend/app/providers/`. To move from ILMU to, say, Azure OpenAI ([SPEC-06 §7](docs/specs/SPEC-06-ai-providers.md#7-switching-provider-production)):

1. **Set the profile** in `.env`: `AI_PROVIDER`, `AI_BASE_URL`, `AI_API_KEY`, the `LLM_*_MODEL` names, `EMBED_MODEL`, `EMBED_DIM`.
2. **If the embedding model changed, re-embed.** Vectors from different models can't share an index, and ingestion refuses to mix them. The re-embed procedure: add a second embedding column (or table) sized `EMBED_DIM` in a migration (≤ 2,000 dims for `vector` HNSW, ≤ 4,000 with `halfvec`; record the shape in SPEC-02), re-embed every chunk in batches with the throttled embed client, then switch search over and drop the old column. Never mix models in one index. (`python -m app.ingestion.reembed` is specified but not built yet; until then, the simple path for a small corpus is `docker compose down -v` and re-upload.)
3. **Turn the reranker off** (`RERANK_MODEL=`) if the provider has none. The vector-similarity gate (`MIN_VECTOR_SIM`) then decides relevance; re-tune it for the new embedding model.
4. **Run the eval** on all 32 questions and compare with the ILMU baseline in `eval-results/`. **The eval is the acceptance gate for a provider switch.**
5. **Check data residency** of the provider and region against company policy and client contracts before go-live.

## Why no LangChain

The pipeline is five steps of thin, plain code: parse → chunk → embed → search → answer. Each step is one module you can read top to bottom.

- **Traceable.** When an answer is wrong, a developer (or an agent) can follow it from the SQL query to the prompt to the citation check without stepping through framework abstractions.
- **The rules that matter are ours.** Access filters inside both search arms before ranking, the relevance gate, "cite every claim or say not found", the private-marker test. These are a few lines each here; in a framework they would be callbacks and subclasses fighting its defaults.
- **Specs map to files.** Each spec section names the module that implements it, which is what makes spec-driven development work. A framework would put the behaviour that matters in someone else's code.
- **Fewer moving parts.** The only AI dependency is the `openai` SDK (pointed at any OpenAI-compatible endpoint) plus `httpx` for rerank.

Docling is used for parsing because document layout, tables and OCR are a real library's job.

## Security notes

- Fictional data only until company policy approves real documents on this setup ([SPEC-09 §1](docs/specs/SPEC-09-security-and-access.md#1-data-rules)).
- Uploads are checked by magic bytes, size-limited while streaming, zip-bomb guarded, and stored under server-chosen paths.
- Secrets come only from `.env` (gitignored); the key is masked in settings and never logged. Images contain no secrets.
- A test-only private document with the marker `ZQX-PRIVATE-7` must never reach a user outside its group through any endpoint, event or log line; a test suite enforces it.
- Demo identity (`X-Demo-User`) is a stand-in for SSO and is refused when `APP_ENV=production`.

## Repo map

```
backend/        FastAPI app, worker, eval (Python 3.14, uv)
frontend/       Vue 3 SPA + nginx config
docs/specs/     SPEC-00 … SPEC-11: the source of truth
docs/milestones milestones, worked in order; done/ holds the finished ones
docs/DEVIATIONS.md  every knowing difference between code and spec
samples/serimaju    fictional demo documents + 32 eval questions
eval-results/   eval reports per run
```
