# D010 — Public preview uses the app's own password login instead of Cloudflare Access

- **Date / milestone:** 2026-11-23 · M100
- **Spec:** [SPEC-11 §3–6](../specs/SPEC-11-deployment.md#5-public-preview-via-cloudflare-tunnel-m100), [SPEC-09 §3, §6](../specs/SPEC-09-security-and-access.md#3-identity), [SPEC-08 §1–3, §7](../specs/SPEC-08-api-contract.md#2-error-shape), [SPEC-07 §8](../specs/SPEC-07-frontend.md#8-identity), [M100](../milestones/M100-public-preview.md)
- **Status:** Resolved → spec updated

## Spec said
- Cloudflare Access does the login (email allow-list, one-time PIN). `AUTH_MODE=cloudflare_access` verifies the `Cf-Access-Jwt-Assertion` JWT against the team's key set and maps the email through `ACCESS_USERS` and `ADMIN_EMAILS`. An unlisted email gets 403 `not_invited`, and Sign out goes to `/cdn-cgi/access/logout`.
- Per-user chat limits with no mode named. New env vars listed "with no values".

## Implementation does
1. **`AUTH_MODE=password`** replaces `cloudflare_access`. Users come from `LOGIN_USERS` (`username → {name, groups, admin, passwordHash}`), with stdlib scrypt hashes made by `python -m app.security.passwords`. `POST /api/v1/auth/login` sets an HS256-signed `rag_session` cookie: HttpOnly, `SameSite=Strict`, `Secure` in production, `SESSION_DAYS=7`, and stamped with the password hash so a password change ends old sessions. `POST /api/v1/auth/logout` clears it. These are two new endpoints (SPEC-08 #16, #17).
2. Error codes: `bad_credentials` (401, the same message for a wrong username or password) instead of `not_invited`. A missing or invalid session is 401 `unknown_user`. 10 failed sign-ins per username in 15 minutes give 429 `user_rate_limited`.
3. The chat limits and the failed-login lock apply **only in `password` mode**: in demo mode the eval asks 32 questions back to back. Limits are keyed by username; the real IP from `CF-Connecting-IP` is for the nginx log only.
4. `/config` gains `authMode`, `/me` gains `isAdmin`, and `/usage/summary` `balances` gains `paygLow`. The frontend shows a login page while there is no session, hides the Usage nav entry for non-admins, and returns to the login page on any 401.
5. `.env.example`: `LOGIN_USERS={}` (an empty value can't be parsed as JSON), `SESSION_SECRET=` and `TUNNEL_TOKEN=` empty, the limits and `SESSION_DAYS` with their defaults. Startup refuses `password` mode without users, with a `SESSION_SECRET` under 32 characters, or with a user lacking a `scrypt:` hash.
6. Dependency: `pyjwt` (HS256 only; no `cryptography`).

## Why
- The owner's decision on 2026-11-23: three named users will use the preview, and a simple login in the app is easier to run than a Zero Trust Access application and email allow-list. The tunnel stays, so still no router ports and no exposed API or Postgres.
- A first version with Cloudflare Access was built and tested on 2026-11-22 but never committed. It was replaced before landing.

## Consequences
- The app itself is now the only gate in front of the data, so the cookie flags, the failed-login lock and the startup guards carry the weight that Cloudflare Access carried. All of them are covered by `tests/spec11/test_login.py`.
- Cloudflare Access can still be added later in front of the hostname as an extra layer; the app needs no change for that.
- SPEC-00 §8, SPEC-07 §8, SPEC-08 §1–3/§7, SPEC-09 §3/§6 and SPEC-11 §3–6 are updated in the same change.
