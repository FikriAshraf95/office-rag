# SPEC-11 — Deployment

> **Status:** v1 (2026-11-19) · **Owner of:** Docker Compose, images, env, ports, the run book

## 1. Services (`docker-compose.yml`)

| Service | Image | Port (host) | Notes |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:pg17` | `127.0.0.1:5433 → 5432` | 5433 avoids clashing with other local Postgres instances. Volume `pgdata`. Healthcheck `pg_isready` |
| `api` | `backend` image, target `api` | `127.0.0.1:8000` | `alembic upgrade head` then `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Volume `storage:/data/storage` |
| `worker` | `backend` image, target `worker` | — | `python -m app.ingestion.worker`. Same `storage` volume. Depends on `api` healthy (migrations done) |
| `frontend` | `frontend` image (nginx) | `127.0.0.1:8080` | Serves `dist/`; proxies `/api` and `/health` to `api:8000` with `proxy_buffering off` for SSE |

All config comes from `.env` (via `env_file`). Ports bind to loopback only.

## 2. Images

- **backend** (multi-stage, `python:3.14-slim`, `uv`):
  - `base`: `uv sync --frozen --no-dev` without the `worker` dependency group.
  - `api`: from `base`.
  - `worker`: from `base` + `uv sync --group worker` (Docling, CPU-only `torch` from the PyTorch CPU index) + `docling-tools models download` (layout, tableformer, RapidOCR) and the `BAAI/bge-m3` tokenizer into `/models`, with `DOCLING_ARTIFACTS_PATH=/models` and `HF_HUB_OFFLINE=1`. No model downloads at runtime.
- **frontend**: `node:22-alpine` build → `nginx:alpine` with `nginx/default.conf` (copy from Office Suite `frontend/nginx/`, adjust upstream; CSP `default-src 'self'; img-src 'self' blob: data:; worker-src 'self' blob:` for pdf.js).

## 3. Environment (`.env.example`)

```
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://rag:rag@localhost:5433/rag
STORAGE_DIR=./storage
MAX_UPLOAD_MB=25
DEMO_USERS={"aisyah":{"name":"Aisyah (HR)","groups":["all","hr"]},"ben":{"name":"Ben (Staff)","groups":["all"]}}
ORG_NAME=Serimaju Technologies
AI_PROVIDER=ilmu
AI_BASE_URL=https://api.ilmu.ai/v1
AI_API_KEY=
LLM_ANSWER_MODEL=nemo-super
LLM_FAST_MODEL=ilmu-nemo-nano
LLM_FALLBACK_MODEL=ilmu-glm-5.3-flash
LLM_VISION_MODEL=nemo-super
LLM_JUDGE_MODEL=nemo-super
EMBED_MODEL=bge-m3
EMBED_DIM=1024
RERANK_MODEL=
AI_MAX_RPM=50
TOP_K=8
MIN_VECTOR_SIM=0.53
WORKER_CONCURRENCY=1
NOT_FOUND_CONTACTS={"HR":"HR, hr@serimaju.example","Finance":"Finance, finance@serimaju.example","IT":"IT, it@serimaju.example","default":"HR, hr@serimaju.example"}
AUTH_MODE=demo
# Tuning settings, shown with their defaults:
# QUERY_REWRITE=false
# K_VEC=40
# K_FTS=40
# RRF_K=60
# RERANK_CANDIDATES=30
# MIN_RERANK_SCORE=0.1
# MAX_CHUNKS_PER_DOC=4
# MAX_CONTEXT_TOKENS=12000
# CHUNK_MAX_TOKENS=800
# XLSX_ROWS_PER_CHUNK=20
# EMBED_BATCH=64
# OCR_MIN_CHARS=80
# TOKENIZER_ID=BAAI/bge-m3      # tokenizer for chunk sizing; cached in /models in the worker image
# DOCLING_ARTIFACTS_PATH=       # Docling models dir; /models in the worker image, unset = Hugging Face cache
```

`.env.example` lists every setting the app reads ([SPEC-09 §5](SPEC-09-security-and-access.md)); a new setting is added here in the same change.

Inside Compose, `DATABASE_URL` points at `postgres:5432` and `STORAGE_DIR=/data/storage` (overridden in the compose file).

## 4. Run book

**Full stack**
1. `cp .env.example .env` and set `AI_API_KEY`.
2. `docker compose up -d --build` (first worker build downloads the Docling models, ~1–2 GB; later builds are cached).
3. Open `http://localhost:8080`, pick a demo user, go to Documents, upload `samples/serimaju/documents/*`.
4. Wait for all rows to show **Ready**; check the 2024 handbook shows **Superseded**.
5. Ask the example questions in Chat.

**Local dev** (hybrid: Postgres in Docker, API, worker and frontend on the host; decided 2026-11-19)
- One-time: `uv python install 3.14` (uv-managed; the system Python is untouched; `backend/.python-version` selects it)
- `docker compose up -d postgres`
- Backend: `cd backend && uv sync --all-groups && uv run alembic upgrade head && uv run uvicorn app.main:app --reload --port 8000`
- Worker: `cd backend && uv run python -m app.ingestion.worker`
- Frontend: `cd frontend && npm ci && npm run dev` → `http://localhost:5173`

**Eval:** `cd backend && uv run python -m app.eval --base-url http://localhost:8000 --user ben --label nemo-super`

**Reset demo data:** `docker compose down -v` (drops DB and storage volumes).

## 5. Public preview via Cloudflare Tunnel (M100)

After the presentation the stack runs in a production-like way on the home PC and is reachable from the internet. It still serves the **fictional Serimaju data only** ([SPEC-09 §1](SPEC-09-security-and-access.md#1-data-rules)).

**Prerequisites:** a domain on Cloudflare (Cloudflare Access needs one; `trycloudflare.com` quick tunnels can't be protected); a Cloudflare Zero Trust team (the free plan covers 50 users).

### 5.1 Topology
```
browser ──HTTPS──▶ Cloudflare edge (Access login) ──tunnel──▶ cloudflared ──▶ frontend (nginx :80) ──▶ api :8000
                                                                                                      worker, postgres (internal only)
```
- A `cloudflared` service in `docker-compose.yml` under the **`public` profile** (`docker compose --profile public up -d`). It uses a pinned `cloudflare/cloudflared` image and runs `tunnel --no-autoupdate run` with `TUNNEL_TOKEN` from `.env`. The tunnel is remotely managed: the public hostname (e.g. `rag.<domain>`) maps to `http://frontend:80` in the Cloudflare dashboard.
- Only `frontend` is reachable through the tunnel. The api, worker and Postgres stay on the Compose network; the host ports stay bound to loopback. No ports are opened on the router.

### 5.2 Authentication: Cloudflare Access
- A Cloudflare Access application on the hostname, with a policy that allows listed emails (one-time PIN or Google login). Nobody reaches nginx without passing Access.
- `AUTH_MODE=cloudflare_access`: `get_identity()` verifies the `Cf-Access-Jwt-Assertion` header. It checks the signature against `https://<CF_ACCESS_TEAM_DOMAIN>/cdn-cgi/access/certs` (keys cached for 1 h), the `aud` against `CF_ACCESS_AUD`, and expiry. It then maps the email through `ACCESS_USERS` (env JSON: `email → {name, groups}`). Admins are listed in `ADMIN_EMAILS`. An invalid or missing JWT gives 401; an email that isn't listed gives 403 `not_invited`.
- The demo `X-Demo-User` header is ignored in this mode. The frontend hides the user switcher, shows the email from `/me`, and links **Sign out** to `/cdn-cgi/access/logout`.

### 5.3 Production hardening
- `APP_ENV=production`. Startup refuses `AUTH_MODE=demo` and `AI_PROVIDER=fake` (both guards exist from M00, [SPEC-09 §6](SPEC-09-security-and-access.md#6-startup-guards)).
- Only admins may upload, patch, delete, re-ingest and open `/usage`. Everyone else can only chat and read documents (403 `admin_only`).
- **Quota protection:** per-user chat limits `CHAT_RATE_PER_MIN=6` and `CHAT_DAILY_CAP=100` (429 `user_rate_limited`). Uploads count as admin-only work. A low-PAYG-balance warning is logged and shown on `/usage` below `PAYG_ALERT_MYR=5`.
- nginx: `real_ip_header CF-Connecting-IP` from the Docker network, for logs and the rate limiter. SSE responses send `X-Accel-Buffering: no` and are never gzipped. The 15 s keep-alive ping stays well under Cloudflare's 100 s idle timeout. The Cloudflare request limit (100 MB on the free plan) is above `MAX_UPLOAD_MB`.
- All containers have `restart: unless-stopped`. The PC must not sleep while the preview is up.
- New env vars (`CF_ACCESS_TEAM_DOMAIN`, `CF_ACCESS_AUD`, `ACCESS_USERS`, `ADMIN_EMAILS`, `TUNNEL_TOKEN`, `CHAT_RATE_PER_MIN`, `CHAT_DAILY_CAP`, `PAYG_ALERT_MYR`) go in `.env.example`, with no values. New error codes go in [SPEC-08 §2](SPEC-08-api-contract.md#2-error-shape) in the same change.

## 6. Acceptance checks

1. On a clean clone with `.env` set, `docker compose up -d --build` reaches healthy `postgres`, `api`, `frontend` and a running `worker`; `GET http://localhost:8080/health` returns ok.
2. SSE through nginx streams deltas as they arrive (no buffering): first delta visible in the browser before `done`.
3. The worker container starts with no network access to huggingface.co (models are baked in).
4. No secret value is present in any image layer (`docker history` / build args check) or in the repo.
5. *(M100)* With `AUTH_MODE=cloudflare_access`, a request without a valid Access JWT returns 401, a JWT with the wrong `aud` returns 401, and an unlisted email returns 403 `not_invited` (tests use a locally generated key set; no network).
6. *(M100)* `X-Demo-User` has no effect in `cloudflare_access` mode.
7. *(M100)* A non-admin gets 403 `admin_only` on upload, patch, delete, re-ingest and `/usage`; the 7th question within a minute returns 429 `user_rate_limited`.
8. *(M100)* `APP_ENV=production` with `AUTH_MODE=demo` refuses to start.
9. *(M100)* From an outside network: the hostname shows the Access login first; after login, a question streams in the browser before `done`; `api`, `postgres` and port 8000 are not reachable from outside.
