# M100 — Public preview via Cloudflare Tunnel *(after the presentation)*

> **Depends on:** [M99](done/M99-release-and-demo.md) · **Blocks:** —
> **Read first:** [SPEC-11 §5–6](../specs/SPEC-11-deployment.md#5-public-preview-via-cloudflare-tunnel-m100) · [SPEC-09 §3, §6](../specs/SPEC-09-security-and-access.md#3-identity) · [SPEC-08 §2](../specs/SPEC-08-api-contract.md#2-error-shape) · [SPEC-07 §8](../specs/SPEC-07-frontend.md#8-identity)
> **Model:** Opusplan. Authentication and exposure to the internet: get the session cookie, the login lock and the admin/rate-limit boundaries right. Write `M100-plan.md` first.
> **Changed 2026-11-23 ([D010](../deviations/D010-public-preview-details.md)):** the app's own password login for three named users replaces Cloudflare Access.

## Goal
Run the stack like production on the home PC, reachable at a Cloudflare hostname. Users sign in with a username and password listed in `.env`, a tunnel means no ports are opened, and the app trusts only its own signed session cookie. Only admins can change documents, and per-user limits protect the ILMU quota. The data stays fictional (Serimaju).

## Prerequisites (user)
- [ ] A domain on Cloudflare and a Zero Trust team. Create a remotely managed tunnel and copy its token to `.env` as `TUNNEL_TOKEN`.
- [x] A public hostname on the tunnel (`officerag.myradiantvision.com`) with service `http://frontend:80`.
- [ ] `LOGIN_USERS` (three users, hashes from `python -m app.security.passwords`) and `SESSION_SECRET` in `.env`.

## Tasks
### Backend
- [x] `security/identity.py`: `password` mode (signed session cookie, `LOGIN_USERS`), `security/passwords.py` (scrypt hashes + the hash command), `POST /auth/login` and `/auth/logout`, the failed-login lock; the startup guards for `AUTH_MODE=demo` in production and for `password` mode's settings.
- [x] `require_admin` dependency on upload, patch, delete, re-ingest and usage.
- [x] Per-user chat rate limit and daily cap (in-process token bucket plus a daily count from `questions`); PAYG low-balance alert.
- [x] SPEC-08 §2: add `bad_credentials`, `admin_only`, `user_rate_limited`; §1: endpoints 16 and 17.
### Frontend
- [x] A login page in password mode; hide the user switcher; show the user's name and Sign out; hide admin actions for non-admins (the server still enforces them).
### Deploy
- [x] The `cloudflared` service under the `public` profile; `restart: unless-stopped` on every service; nginx real-IP and SSE headers; `.env.example` entries.
### Tests
- [x] SPEC-11 §6 checks 5–8.
- [x] Invariants: private marker for a non-member password user.

## Acceptance criteria
1. The tests above are green, along with the full gates.
2. **Walkthrough:** on a phone with mobile data, open `https://officerag.myradiantvision.com` → the login page appears → sign in → ask Q01 → the answer streams with citations. A wrong password is refused. As a non-admin, the upload controls are hidden and the API returns 403. Ports 8000 and 5433 can't be reached from outside (SPEC-11 §6 check 9).
3. **Deviations recorded**, or *"Deviations: none"*.

**Status:** IMPLEMENTED (2026-11-23), walkthrough pending. Password login replaced the Cloudflare Access version of 2026-11-22 before it was committed. Backend `pytest -q` 199 passed; ruff, mypy and lint-imports clean. Frontend lint, typecheck, 98 tests and build green. Acceptance 1 met. Acceptance 2 (phone walkthrough, SPEC-11 §6 check 9) needs `TUNNEL_TOKEN`, `LOGIN_USERS` and `SESSION_SECRET` in `.env`. Deviations: D010.
