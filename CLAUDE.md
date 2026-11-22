# CLAUDE.md

## What this repo is

Company Docs RAG: upload company documents (PDF, DOCX, XLSX, MD, PNG/JPG), ingest them in a background worker (Docling → structure-aware chunks → bge-m3 embeddings in Postgres + pgvector), and answer questions in a chat UI with streamed, cited answers that never guess. FastAPI + worker + PostgreSQL + Vue 3. Demo provider: ILMU AI (OpenAI-compatible); demo data: the fictional `samples/serimaju/` set. Also the case study for the team's spec-driven development (SDD) presentation on 2026-11-26.

**The repo is spec-driven.**
- Specs in `docs/specs/` are the source of truth. Read **[SPEC-00 §6](docs/specs/SPEC-00-overview.md) Global conventions** before non-trivial work.
- **SPEC-02 owns every table. SPEC-08 indexes every endpoint.** Change them in the same change as the code.
- Milestones in `docs/milestones/` are worked **in number order, one at a time**. Each one's *Read first* line lists the spec sections to load.
- **Deviations are a mandatory log** ([docs/DEVIATIONS.md](docs/DEVIATIONS.md)): check the highest D-number, add `docs/deviations/D<nnn>-….md` + index row + spec note **in the same change**. An unlogged deviation is a bug.

## How to read specs (token rule)

To read a spec section, run `grep -n '^## ' <spec>` to find its line range, then Read with offset/limit. Never read a whole spec unless the milestone says "(whole file)".

## Status

Specs v1 written (2026-11-19). M00–M03 implemented (2026-11-20), M04–M08 (2026-11-21) and [M99](docs/milestones/done/M99-release-and-demo.md) (2026-11-22), awaiting human review. Full stack verified with `scripts/release_check.sh`; demo script rehearsed. Eval 28.5/32 on nemo-super with the reranker on (baseline 25, target 26; model comparison in `eval-results/comparison.md`). No open deviations. [M100 Public preview](docs/milestones/M100-public-preview.md) implemented (2026-11-23, D010: password login for three users instead of Cloudflare Access): code, tests and specs done; the phone walkthrough waits for `TUNNEL_TOKEN`, `LOGIN_USERS` and `SESSION_SECRET` in `.env`. **Next: the presentation (2026-11-26), then the M100 walkthrough.**

When a milestone is done: tick its boxes, set **Status** to `DONE (date)` + how acceptance was verified + deviations (`D003, D004` or "Deviations: none"), then move it and its plan file to `docs/milestones/done/` and update this line.

## Model per milestone

Start each milestone in a fresh session (`/clear`). *Opusplan* = `/model opusplan` (plan on Opus, build on Sonnet); write `M<nn>-plan.md` first. If you are on a different model than the row says, say so first. On Sonnet, if the same test fails twice or a design question comes up, suggest switching to Opus. After a Sonnet milestone, a short Opus session reviews the diff for unlogged deviations and access leaks.

| Milestone | Model | Why |
|---|---|---|
| M00 Foundation | Opus | Contracts everything depends on. Human review after |
| M01 Upload and documents | Sonnet | Well-specified CRUD + validation |
| M02 Ingestion | Opusplan | Docling, 5 formats, chunking, job states |
| M03 Retrieval | Opusplan | One SQL with filters in both arms, gate |
| M04 Answering | Opus | Prompt, refusal, citation validation |
| M05 Frontend | Sonnet | Assembly from the Private Repo App kit; can run in parallel from M02 |
| M06 Evaluation | Sonnet | Script + scoring rule |
| M07 Vision *(stretch)* | Sonnet | Bounded addition |
| M08 Reranker *(stretch)* | Sonnet | Wire + measure |
| M99 Release and demo | Opus | Security sweep, fold deviations, story |
| M100 Public preview *(after 26 Nov)* | Opusplan | Password login, internet exposure |

## Commands

**Everything runs in Docker.** Never install Python, uv, Node or caches on the Windows host. The dev container has Python 3.14 + uv and Node 22; the repo is bind-mounted, and the venv, `node_modules` and caches live in named volumes. It shares Postgres's network namespace (Postgres listens on 5433), so `localhost:5433`, `:8000` and `:5173` behave as on a host. Stop the full-stack compose first if it is running (same ports). In Git Bash, prefix commands that pass container paths with `MSYS_NO_PATHCONV=1`.

```bash
# dev container: `dx` = docker compose -f docker-compose.dev.yml exec dev
docker compose -f docker-compose.dev.yml up -d dev                       # dev + Postgres/pgvector
dx sh -c "cd backend && uv sync --all-groups"                           # deps (worker group = Docling)
dx sh -c "cd frontend && npm ci"
dx sh -c "cd backend && uv run alembic upgrade head"                    # migrations, named M<nn>_<topic>
dx sh -c "cd backend && uv run alembic revision -m 'M02_chunks_index'"  # new migration
dx sh -c "cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"   # API
dx sh -c "cd backend && uv run python -m app.ingestion.worker"          # worker
dx sh -c "cd backend && uv run pytest -q"                               # all tests (fake AI, no network)
dx sh -c "cd backend && uv run pytest -q -m 'not docling'"              # fast subset
dx sh -c "cd backend && uv run pytest tests/test_x.py::test_name"       # one test
dx sh -c "cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run lint-imports"
dx sh -c "cd backend && uv run python -m app.export_openapi"            # -> backend/openapi.json
dx sh -c "cd frontend && npm run dev -- --host 0.0.0.0"                 # http://localhost:5173, proxies /api -> :8000
dx sh -c "cd frontend && npm run lint && npm run typecheck && npm run test && npm run build"
dx sh -c "cd frontend && npm run gen:api"                               # types from backend/openapi.json
docker compose up -d --build                                             # full stack on http://localhost:8080 (not the dev container)
dx sh -c "cd backend && uv run python -m app.eval --base-url http://localhost:8000 --user ben --label nemo-super"
```

## Never break

- All document/chunk writes go through `app/ingestion/service.py`.
- Every retrieval filters `doc_status = 'current'` and `access_groups` **before** ranking, in both search arms.
- Answers only from retrieved chunks, every claim cited; otherwise the not-found answer. Never a guess.
- No provider SDK import or model name outside `app/providers/` (and `config.py`).
- Secrets only in env; never in files, prompts, logs or error responses.
- `ZQX-PRIVATE-7` never appears in any response for a user outside its group.
- Tests never touch the network; fake AI mode is refused in production.
- Frontend: tokens only (no hex), user/model HTML only through `SafeHtml.vue`.
