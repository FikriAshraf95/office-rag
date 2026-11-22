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
  - `worker`: from `base` + `uv sync --group worker` (Docling, CPU-only `torch` from the PyTorch CPU index) + `docling-tools models download` (layout, tableformer, RapidOCR) into `/models/docling` and the `BAAI/bge-m3` tokenizer into the Hugging Face cache at `/models/hf`, with `DOCLING_ARTIFACTS_PATH=/models/docling`, `HF_HOME=/models/hf` and `HF_HUB_OFFLINE=1` set after the download step. No model downloads at runtime. The compose file pins `DOCLING_ARTIFACTS_PATH` and `HF_HUB_OFFLINE` for the worker, so a host value in `.env` can't point it elsewhere.
- **frontend**: `node:22-alpine` build → `nginx:alpine` with `nginx/default.conf` (copy from Private Repo App `frontend/nginx/`, adjust upstream; CSP `default-src 'self'; img-src 'self' blob: data:; worker-src 'self' blob:` for pdf.js).

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
# Public preview (SPEC-11 §5, M100). AUTH_MODE=password and APP_ENV=production; demo data only.
# LOGIN_USERS={"fikri":{"name":"Fikri","groups":["all","hr"],"admin":true,"passwordHash":"scrypt:..."}}
# Hash: python -m app.security.passwords · secret: python -m app.security.passwords --secret
LOGIN_USERS={}
SESSION_SECRET=
SESSION_DAYS=7
TUNNEL_TOKEN=
CHAT_RATE_PER_MIN=6
CHAT_DAILY_CAP=100
PAYG_ALERT_MYR=5
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
# TOKENIZER_ID=BAAI/bge-m3      # tokenizer for chunk sizing; cached in /models/hf in the worker image
# DOCLING_ARTIFACTS_PATH=       # Docling models dir; /models/docling in the worker image, unset = Hugging Face cache
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

**Local dev** (dev container, 2026-11-22; replaces the hybrid host setup of 2026-11-19. Nothing is installed on the Windows host)
- `docker-compose.dev.yml` runs Postgres (listening on 5433) and a `dev` container (`Dockerfile.dev`: Python 3.14 + uv, Node 22). The repo is bind-mounted at `/workspace`; the venv, `node_modules` and the uv, npm and Hugging Face caches live in named volumes. `dev` shares Postgres's network namespace, so `localhost:5433`, `:8000` and `:5173` behave as on a host. Stop the full-stack compose first (same ports).
- `docker compose -f docker-compose.dev.yml up -d`, then run each command as `docker compose -f docker-compose.dev.yml exec dev sh -c "cd backend && …"` (the full list is in the root `CLAUDE.md`).
- Backend: `uv sync --all-groups && uv run alembic upgrade head && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`; worker: `uv run python -m app.ingestion.worker`; frontend: `npm ci && npm run dev -- --host 0.0.0.0` → `http://localhost:5173`.
- The Docling tests run offline, so a new Hugging Face cache volume needs one warm-up: parse any PDF once outside pytest with `HF_HUB_OFFLINE=0`.

**Eval:** against the dev API, `uv run python -m app.eval --base-url http://localhost:8000 --user ben --label nemo-super`. Against the full stack, from the API image (inside the image the repo root is `/`): `docker compose run --rm --no-deps -v "$PWD/samples:/samples:ro" -v "$PWD/eval-results:/eval-results" api python -m app.eval --base-url http://api:8000 --user ben --label <name>`. To compare answer models, override `LLM_ANSWER_MODEL` for the `api` service only; the report takes the model name from the answers.

**Release check:** `bash scripts/release_check.sh` on the running full stack, after uploading the documents (§6 checks 1–4).

**Reset demo data:** `docker compose down -v` (drops DB and storage volumes).

**Public preview** (§5, M100)
1. In Cloudflare Zero Trust, add a public hostname to the remotely managed tunnel with service `http://frontend:80`.
2. Per user, make a password hash: `docker compose run --rm --no-deps api python -m app.security.passwords` (asks for the password twice). Make a session secret with `… python -m app.security.passwords --secret`.
3. In `.env`: `APP_ENV=production`, `AUTH_MODE=password`, `LOGIN_USERS` (`username → {name, groups, admin, passwordHash}`, on one line), `SESSION_SECRET`, `TUNNEL_TOKEN`.
4. `docker compose --profile public up -d --build`; `docker compose logs cloudflared` shows `Registered tunnel connection`.
5. To change a password, replace its hash and restart `api`; that user's old sessions stop working. `http://localhost:8080` shows the same login page.

## 5. Public preview via Cloudflare Tunnel (M100)

After the presentation the stack runs in a production-like way on the home PC and is reachable from the internet. It still serves the **fictional Serimaju data only** ([SPEC-09 §1](SPEC-09-security-and-access.md#1-data-rules)).

**Prerequisites:** a domain on Cloudflare and a Cloudflare Zero Trust team (free) for the remotely managed tunnel. The app does its own sign-in (§5.2); it is meant for a handful of named users (three at the start).

### 5.1 Topology
```
browser ──HTTPS──▶ Cloudflare edge ──tunnel──▶ cloudflared ──▶ frontend (nginx :80) ──▶ api :8000
                                                                                                      worker, postgres (internal only)
```
- A `cloudflared` service in `docker-compose.yml` under the **`public` profile** (`docker compose --profile public up -d`). It uses a pinned `cloudflare/cloudflared` image (`2026.10.3`) and runs `tunnel --no-autoupdate run`. Compose passes only `TUNNEL_TOKEN` (interpolated from `.env`, no `env_file`), so cloudflared never sees the app's secrets. The tunnel is remotely managed: the public hostname (e.g. `rag.<domain>`) maps to `http://frontend:80` in the Cloudflare dashboard. That is the Compose service name, not `localhost`: cloudflared runs in its own container.
- Only `frontend` is reachable through the tunnel. The api, worker and Postgres stay on the Compose network; the host ports stay bound to loopback. No ports are opened on the router.

### 5.2 Authentication: password login
- `AUTH_MODE=password`. The users are listed in `LOGIN_USERS` (env JSON: `username → {name, groups, admin, passwordHash}`); usernames are matched lowercased. No users table: a few named users, changed by editing `.env`.
- **Hashes:** `app/security/passwords.py`, stdlib `hashlib.scrypt` (n=2^14, r=8, p=1, 16-byte salt), stored as `scrypt:<n>:<r>:<p>:<salt>:<hash>` in base64url. There is no `$`, so Compose never interpolates it. `python -m app.security.passwords` prints a hash, and `--secret` prints a session secret. The hash is a `SecretStr`, never logged or shown in the settings repr.
- **Sign-in:** `POST /api/v1/auth/login {username, password}` ([SPEC-08 §3](SPEC-08-api-contract.md#3-system)). A wrong username and a wrong password give the same 401 `bad_credentials`, and an unknown username is checked against a dummy hash so both take the same time. On success the API sets the cookie `rag_session`: an HS256 JWT signed with `SESSION_SECRET` (≥ 32 characters), carrying `sub`, `exp` (`SESSION_DAYS=7`) and a stamp of the user's password hash, so changing a password ends that user's old sessions. The cookie is `HttpOnly`, `SameSite=Strict` (which also covers CSRF; no cross-site request carries it), `Path=/`, and `Secure` when `APP_ENV=production`. `POST /api/v1/auth/logout` clears it.
- **Guessing:** 10 failed sign-ins for one username within 15 minutes lock that username for the rest of the window (429 `user_rate_limited`, in-process).
- `get_identity()` reads only the cookie in this mode: missing, tampered, expired, a removed user or a changed password → 401 `unknown_user`. `X-Demo-User` is ignored.
- The frontend shows a login page instead of the app while there is no session, and returns to it on any 401 `unknown_user`. The top bar shows the user's name and **Sign out**.

### 5.3 Production hardening
- `APP_ENV=production`. Startup refuses `AUTH_MODE=demo` and `AI_PROVIDER=fake` (both guards exist from M00, [SPEC-09 §6](SPEC-09-security-and-access.md#6-startup-guards)).
- Only admins may upload, patch, delete, re-ingest and open `/usage`. Everyone else can only chat and read documents (403 `admin_only`).
- **Quota protection** (`security/limits.py`, `password` mode only, so the demo-mode eval isn't limited): per-user chat limits keyed by username, checked after body validation. First a daily cap of `CHAT_DAILY_CAP=100` questions, counted from `questions` since 00:00 UTC. Then an in-process token bucket of `CHAT_RATE_PER_MIN=6` (one API process). Either one gives 429 `user_rate_limited` with `Retry-After`. Uploads count as admin-only work. A low PAYG balance is logged as `payg_balance_low` and shown on `/usage` (`balances.paygLow`) below `PAYG_ALERT_MYR=5`.
- nginx: `real_ip_header CF-Connecting-IP`, trusted from the private ranges (the Docker network), for the access log. SSE responses send `X-Accel-Buffering: no` and are never gzipped. The 15 s keep-alive ping stays well under Cloudflare's 100 s idle timeout. The Cloudflare request limit (100 MB on the free plan) is above `MAX_UPLOAD_MB`.
- All containers have `restart: unless-stopped`. The PC must not sleep while the preview is up.
- New env vars (`LOGIN_USERS`, `SESSION_SECRET`, `SESSION_DAYS`, `TUNNEL_TOKEN`, `CHAT_RATE_PER_MIN`, `CHAT_DAILY_CAP`, `PAYG_ALERT_MYR`) go in `.env.example`. The secrets stay empty, `LOGIN_USERS={}`, and the others show their defaults. New error codes go in [SPEC-08 §2](SPEC-08-api-contract.md#2-error-shape) in the same change.

## 6. Acceptance checks

Checks 1–4 are covered twice: statically in `backend/tests/spec11/test_deployment.py` (compose file, Dockerfiles, nginx, repo; part of the normal suite) and live in `scripts/release_check.sh` (running stack, the worker image started with `--network none`, image history, config and filesystem).

1. On a clean clone with `.env` set, `docker compose up -d --build` reaches healthy `postgres`, `api`, `frontend` and a running `worker`; `GET http://localhost:8080/health` returns ok.
2. SSE through nginx streams deltas as they arrive (no buffering): first delta visible in the browser before `done`.
3. The worker container starts with no network access to huggingface.co (models are baked in).
4. No secret value is present in any image layer (`docker history` / build args check) or in the repo.
5. *(M100)* With `AUTH_MODE=password`, a request without a session cookie, or with a tampered, expired or foreign-secret one, returns 401 `unknown_user`. A wrong password or unknown username returns 401 `bad_credentials` with the same detail. A good login sets an `HttpOnly`, `SameSite=Strict` cookie (`Secure` in production), and a changed password ends the old session.
6. *(M100)* `X-Demo-User` has no effect in `password` mode.
7. *(M100)* A non-admin gets 403 `admin_only` on upload, replace file, patch, delete, re-ingest and `/usage`. The 7th question within a minute returns 429 `user_rate_limited`, and so does the 11th sign-in attempt after 10 failures for one username.
8. *(M100)* `APP_ENV=production` with `AUTH_MODE=demo` refuses to start, and so does `password` mode without `LOGIN_USERS`, without a `SESSION_SECRET` of at least 32 characters, or with a user who has no valid `passwordHash`.
9. *(M100)* From an outside network: the hostname shows the login page first; after login, a question streams in the browser before `done`; `api`, `postgres` and port 8000 are not reachable from outside.
