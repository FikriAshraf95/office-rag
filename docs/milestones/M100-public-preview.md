# M100 — Public preview via Cloudflare Tunnel *(after the presentation)*

> **Depends on:** [M99](M99-release-and-demo.md) · **Blocks:** —
> **Read first:** [SPEC-11 §5–6](../specs/SPEC-11-deployment.md#5-public-preview-via-cloudflare-tunnel-m100) · [SPEC-09 §3, §6](../specs/SPEC-09-security-and-access.md#3-identity-demo) · [SPEC-08 §2](../specs/SPEC-08-api-contract.md#2-error-shape) · [SPEC-07 §8](../specs/SPEC-07-frontend.md#8-demo-identity)
> **Model:** Opusplan. Authentication and exposure to the internet: get the JWT checks and the admin/rate-limit boundaries right. Write `M100-plan.md` first.

## Goal
Run the stack like production on the home PC, reachable at a Cloudflare hostname. Cloudflare Access handles login, a tunnel means no ports are opened, and the app trusts only verified Access identities. Only admins can change documents, and per-user limits protect the ILMU quota. The data stays fictional (Serimaju).

## Prerequisites (user)
- [ ] A domain on Cloudflare and a Zero Trust team. Create a remotely managed tunnel and copy its token to `.env` as `TUNNEL_TOKEN`.
- [ ] An Access application on `rag.<domain>` with an email allow-list. Note the team domain and the AUD tag.

## Tasks
### Backend
- [ ] `security/identity.py`: `cloudflare_access` mode (JWT verification with cached JWKS, `ACCESS_USERS`, `ADMIN_EMAILS`); the startup guard for `AUTH_MODE=demo` in production.
- [ ] `require_admin` dependency on upload, patch, delete, re-ingest and usage.
- [ ] Per-user chat rate limit and daily cap (in-process token bucket plus a daily count from `questions`); PAYG low-balance alert.
- [ ] SPEC-08 §2: add `not_invited`, `admin_only`, `user_rate_limited`.
### Frontend
- [ ] Hide the user switcher in Access mode; show the email from `/me` and a Sign out link; hide admin actions for non-admins (the server still enforces them).
### Deploy
- [ ] The `cloudflared` service under the `public` profile; `restart: unless-stopped` on every service; nginx real-IP and SSE headers; `.env.example` entries.
### Tests
- [ ] SPEC-11 §6 checks 5–8.
- [ ] Invariants: private marker for a non-member Access user.

## Acceptance criteria
1. The tests above are green, along with the full gates.
2. **Walkthrough:** on a phone with mobile data, open `https://rag.<domain>` → the Access login appears → sign in with an allowed email → ask Q01 → the answer streams with citations. A non-allowed email is refused. As a non-admin, the upload controls are hidden and the API returns 403. Ports 8000 and 5433 can't be reached from outside (SPEC-11 §6 check 9).
3. **Deviations recorded**, or *"Deviations: none"*.

**Status:**
