# M00 — Foundation and contracts

> **Depends on:** — · **Blocks:** everything
> **Read first:** [SPEC-00 §6](../specs/SPEC-00-overview.md#6-global-conventions) · [SPEC-01 (whole file)](../specs/SPEC-01-architecture.md) · [SPEC-02 (whole file)](../specs/SPEC-02-database-schema.md) · [SPEC-08 §1–3](../specs/SPEC-08-api-contract.md#1-endpoint-index) · [SPEC-06 §1–2, §5–6](../specs/SPEC-06-ai-providers.md#1-provider-profile-env) · [SPEC-09 §3, §5–6](../specs/SPEC-09-security-and-access.md#3-identity-demo) · [SPEC-10 §2–3](../specs/SPEC-10-testing-and-eval.md#2-backend-test-host) · [SPEC-11 §1, §3](../specs/SPEC-11-deployment.md#1-services-docker-composeyml) · [SPEC-07 §1–3](../specs/SPEC-07-frontend.md#1-stack)
> **Model:** Opus. Every later milestone builds on these contracts. **Human review after.**

## Goal
Lay the foundations every later milestone builds on: the repo layout, the Compose services, the database with every SPEC-02 table, the FastAPI app with the error shape and system endpoints, provider interfaces with fakes and usage logging, the test host with its network guard, and a frontend shell copied from the Office Suite kit that passes all its gates. No ingestion, search or chat yet.

## Tasks
### Repo
- [x] `git init`, `.gitignore` (`.env`, `storage/`, `node_modules/`, `.venv/`, `dist/`, `__pycache__/`), `.env.example` ([SPEC-11 §3](../specs/SPEC-11-deployment.md#3-environment-envexample)).
- [x] `docker-compose.yml` with `postgres` (pgvector, 5433) only; the other services are added as stubs and completed in M99.
### Backend
- [x] `backend/pyproject.toml` (uv, `requires-python = ">=3.14,<3.15"`, `.python-version` = `3.14`): fastapi, uvicorn[standard], pydantic v2, pydantic-settings, sqlalchemy[asyncio] 2, asyncpg, alembic, pgvector, openai, httpx, python-multipart, pyyaml, structlog; dev: pytest, pytest-asyncio, pytest-socket, ruff, mypy, import-linter; group `worker`: docling (added in M02).
- [x] `app/config.py`: `Settings` with every env var, `AI_API_KEY` masked in `repr`, startup guards ([SPEC-09 §6](../specs/SPEC-09-security-and-access.md#6-startup-guards)).
- [x] `app/db/models.py` + Alembic `M00_initial`: all tables, indexes, constraints, the generated `tsv`, the `jobs_new` notify trigger ([SPEC-02](../specs/SPEC-02-database-schema.md)).
- [x] `app/main.py`, `app/api/errors.py` (problem+json for every error, `traceId`), camelCase schemas base.
- [x] `app/security/identity.py` (`X-Demo-User` → `Identity(id, name, groups, is_admin)`), selected by `AUTH_MODE` (only `demo` exists until M100). Routes get the user only through the `get_identity` dependency.
- [x] Endpoints 1–3: `/health`, `/config`, `/me`.
- [x] `app/providers/`: `base.py` interfaces, `fakes.py`, `registry.py`, `errors.py` (mapping table), `usage.py` (writes `usage` rows), `pricing.py`, `openai_compat.py` (chat + stream + embed + vision via the OpenAI SDK, retries/throttle) and `rerank_http.py`.
- [x] `app/export_openapi.py` writes `backend/openapi.json`.
- [x] `.importlinter` contracts ([SPEC-01 §2](../specs/SPEC-01-architecture.md#2-module-boundaries)).
### Frontend
- [x] Copy the kit per [SPEC-07 §3](../specs/SPEC-07-frontend.md#3-reuse-map-copy-dont-reinvent): config files, `styles/`, fonts, `gen-tokens.mjs`, eslint rule, `components/ui/*` listed in SPEC-07 §2, common components, `lib/`, `api/http.ts`. Trim `package.json` to what is used; add `markdown-it`, `pdfjs-dist`.
- [x] App shell: `AppLayout` with sidebar (Chat, Documents, Usage), top bar with the demo user `Select` (from `/config`) and theme toggle, placeholder pages, router, NotFound.
- [x] `npm run gen:api` against `backend/openapi.json`.
### Tests
- [x] `tests/conftest.py`: test DB create + migrate, per-test rollback, `AI_PROVIDER=fake`, `pytest-socket` guard, `client` fixture with a demo user header.
- [x] SPEC-01 §6 checks 1–4 as `test_spec01_ac01_…` … `ac04`.
- [x] SPEC-02 §8 checks 1–5.
- [x] SPEC-06 §8 checks 1–8 (mocked HTTP transport for the OpenAI client and rerank).
- [x] SPEC-08 §8 checks 2, 4, 5 (for the endpoints that exist).
- [x] SPEC-09 §8 checks 5–6.
- [x] SPEC-10 §6 check 1.
- [x] Invariant skeleton `tests/invariants/` with the private-marker fixture document and the "no provider name outside providers/" check.
- [x] Frontend: a smoke test that the app shell renders and the demo user select lists users from a fixture.

## Acceptance criteria
1. The tests above are green, along with the full gates (backend ruff, mypy, pytest; frontend lint, typecheck, test, build).
2. **Walkthrough:** `docker compose up -d postgres` → `uv run alembic upgrade head` → `uv run uvicorn …` → `GET /health` ok → `npm run dev` → the shell loads at :5173 in light and dark, the user switcher lists Aisyah and Ben, and `/api/v1/me` returns the chosen user.
3. **Deviations recorded**, or *"Deviations: none"*.

## Checks finished in later milestones
| Check | Finished in |
|---|---|
| SPEC-08 §8 checks 1 and 3 (full route list, 404 for hidden docs) | M04 / M01 |

**Status:** IMPLEMENTED (2026-11-20), awaiting human review before DONE.
Verified: backend ruff, ruff format, mypy --strict, lint-imports (4 contracts) and pytest (31 passed, network guard on); frontend lint, typecheck, test (59 passed) and build. Walkthrough run from the terminal: `alembic upgrade head`, `/health` ok, `/api/v1/config` lists Aisyah (HR) and Ben (Staff) through the Vite proxy, and `/api/v1/me` returns each chosen user. Still to check by eye: the shell in light and dark at :5173 and the user switcher.
Spec updates (no deviation): SPEC-08 §2 adds 405 `method_not_allowed`; SPEC-01 §2 allows `httpx2` (the OpenAI SDK's client) in providers; SPEC-10 §2 notes the selector event loop; SPEC-07 §2 adds `stores/user.ts` and `features/config/api.ts`.
Deviations: D001.
