# M100 plan — Public preview via Cloudflare Tunnel

> Written 2026-11-22 before any code. Specs: SPEC-11 §5–6, SPEC-09 §3, §6, SPEC-08 §2, SPEC-07 §8.
> Environment facts: the tunnel is remotely managed; the user's dashboard hostname is `officerag.myradiantvision.com` (the spec's `rag.<domain>` is an example). Its service URL must be `http://frontend:80` (cloudflared runs on the Compose network), not `http://localhost:8000`.

## Design decisions

1. **JWT library.** Add `pyjwt[crypto]` to the main dependencies. `app.security` may not import `httpx` (import-linter `sdk-only-in-providers`), so the JWKS is fetched with stdlib `urllib.request` in a worker thread (5 s timeout). The fetch function is injectable, so tests use a locally generated RSA key set and never touch the network.
2. **`AccessVerifier`** (`security/identity.py`): caches the key set for 1 h; an unknown `kid` refetches at most once a minute (key rotation). `jwt.decode(..., algorithms=["RS256"], audience=CF_ACCESS_AUD, issuer="https://<team domain>", options={"require": ["exp", "aud", "iss"]})`. Missing header, bad signature, wrong `aud`/`iss`, expired, or no `email` claim (service tokens) → 401 `unknown_user` with a sign-in detail (reuses the existing 401 code; SPEC-08 §2 row widened). Email lowercased, then looked up in `ACCESS_USERS` → otherwise 403 `not_invited`. `is_admin` = email in `ADMIN_EMAILS`. A JWKS fetch failure is a 500 (logged), never an accept.
3. **Settings.** `CF_ACCESS_TEAM_DOMAIN` (e.g. `myteam.cloudflareaccess.com`), `CF_ACCESS_AUD`, `ACCESS_USERS` (JSON, same shape as `DEMO_USERS`, keys are emails), `ADMIN_EMAILS` (comma-separated), `CHAT_RATE_PER_MIN=6`, `CHAT_DAILY_CAP=100`, `PAYG_ALERT_MYR=5`. `TUNNEL_TOKEN` is read only by `cloudflared` (passed by Compose interpolation, not `env_file`, so cloudflared never sees `AI_API_KEY`). The `X-Demo-User` header is not read at all in Access mode.
4. **Startup guards** (SPEC-09 §6): drop the "not available yet" guard; `cloudflare_access` without `CF_ACCESS_TEAM_DOMAIN`, `CF_ACCESS_AUD` or `ACCESS_USERS` → exit naming the variable; an `ADMIN_EMAILS` entry missing from `ACCESS_USERS` → exit (an admin who can't sign in is a config mistake).
5. **`require_admin`** dependency (`AdminUser`) on upload, replace file, patch, delete, re-ingest and `/usage/summary` → 403 `admin_only`. It runs before any document lookup, so a non-admin learns nothing about existence. Demo users stay admins.
6. **Chat limits** (`security/limits.py`), applied **only in `cloudflare_access` mode** (they protect the public quota; the eval runs 32 questions in demo mode and must not hit them). Order in the chat route, after body validation: daily cap = count of `questions` rows for `user.id` since 00:00 UTC ≥ `CHAT_DAILY_CAP` → 429; then a per-user token bucket (capacity `CHAT_RATE_PER_MIN`, refill `CHAT_RATE_PER_MIN/60` per second) on `app.state` → 429 `user_rate_limited` with a `Retry-After` header. In-process state is fine: one API process.
7. **PAYG alert.** `UsageRecorder` takes the threshold; `note_balances` logs `payg_balance_low` (warning) when the PAYG balance drops below it. `/usage/summary` `balances` gains `paygLow: bool`; the Usage page shows a warning banner.
8. **API additions** (SPEC-08 §3): `/config` gains `authMode`; `accessGroups` comes from `ACCESS_USERS` in Access mode. `/me` gains `isAdmin`.
9. **Frontend.** User store loads `/me` after `/config` in Access mode; `isAdmin` (always true in demo mode), `current` = the `/me` user. No `X-Demo-User` sent in Access mode. Top bar: email + **Sign out** (`/cdn-cgi/access/logout`) instead of the switcher; a 403 `not_invited` shows a message. Non-admins: no upload panel, no edit/re-ingest/delete/replace actions, no Usage nav entry.
10. **Deploy.** `cloudflared` service, profile `public`, pinned `cloudflare/cloudflared:2026.11.0` (pin checked at build time), `tunnel --no-autoupdate run`, `TUNNEL_TOKEN: ${TUNNEL_TOKEN:-}`, depends on `frontend`. `restart: unless-stopped` everywhere. nginx: `set_real_ip_from` the private ranges + `real_ip_header CF-Connecting-IP`; the chat location adds `X-Accel-Buffering: no` and `Cache-Control: no-cache` already sent by the API.

## Tests
- `tests/spec11/test_access.py`: checks 5 (no header, garbage, wrong key, wrong `aud`, wrong `iss`, expired → 401; unlisted email → 403 `not_invited`; listed → 200 with groups), 6 (`X-Demo-User` ignored), 7 (non-admin 403 `admin_only` on the six routes; 7th chat → 429; daily cap → 429; admin passes), 8 (guards). An `access_app` fixture builds the app with Access settings and a fake JWKS.
- `tests/spec11/test_deployment.py`: cloudflared under `public` profile, no `env_file`, no host port; every service restarts; nginx real-IP.
- Invariant: private marker absent for a non-member Access user (search, chat, documents).
- Frontend: top bar in Access mode, admin actions hidden.

## Revision 2026-11-23: password login replaces Cloudflare Access ([D010](../deviations/D010-public-preview-details.md))

The owner chose a simple login inside the app for three named users. Decisions 1–4 and the Access half of 9 above are replaced by:

1. **`AUTH_MODE=password`.** Users are in `LOGIN_USERS` (env JSON `username → {name, groups, admin, passwordHash}`); no users table, so SPEC-02 is unchanged. Hashes are stdlib `hashlib.scrypt` in a `$`-free format (Compose interpolates `$` in `.env`). `python -m app.security.passwords` prints a hash, and `--secret` a session secret.
2. **Session** = an HS256 JWT (`pyjwt`, no `cryptography`) in the cookie `rag_session`: HttpOnly, `SameSite=Strict` (the CSRF answer), `Secure` in production, 7 days. It is stamped with a hash of the password hash, so a new password ends old sessions. No server-side session store.
3. **Endpoints** `POST /api/v1/auth/login` / `logout` (public; 404 in demo mode). A wrong username or password gives the same 401 `bad_credentials`, and an unknown username is checked against a dummy hash for equal timing. 10 failures per username per 15 minutes → 429 (in-process `LoginLimiter`).
4. **Frontend:** `App.vue` waits for `/config`, shows `LoginPage.vue` while `needsLogin`, and `http.ts` calls `onSignedOut` on a 401 `unknown_user`. Sign out posts `/auth/logout`.
5. Chat limits, admin-only routes, PAYG alert, deploy and nginx stay as above (the limits now apply in `password` mode).
