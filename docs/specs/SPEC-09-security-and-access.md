# SPEC-09 — Security and access

> **Status:** v1 (2026-11-19) · **Owner of:** upload validation, identity, access groups, secrets, data rules, the private-marker invariant

## 1. Data rules

1. The demo runs on the fictional Serimaju documents only. **No real company documents** on personal machines or on ILMU until company policy approves it (open item O1).
2. ILMU states data is processed and stored in Malaysia (PDPA support). Production provider and region must be checked against company policy ([SPEC-06 §7](SPEC-06-ai-providers.md)).
3. Ingest nothing that not everyone may see unless its `access_groups` are set correctly. Filtering happens **before** search ranking ([SPEC-04 §1](SPEC-04-retrieval.md)).

## 2. Upload validation (`security/uploads.py`)

- Allowed by **magic bytes**, not extension or browser type: PDF (`%PDF-`), DOCX/XLSX (ZIP containing `word/document.xml` / `xl/workbook.xml`), PNG, JPEG, Markdown (UTF-8 text, no NUL bytes, `.md` extension). Anything else → 415.
- Size ≤ `MAX_UPLOAD_MB` (25). The server streams to a temp file and stops at the limit → 413.
- ZIP-based files: reject if total uncompressed size > 200 MB or > 2,000 entries (zip bomb guard).
- Filename: keep the base name only, NFC normalize, replace anything outside `[A-Za-z0-9._ -]` with `_`, cap at 120 characters. The stored path is `<document id>/<sanitized name>`; the user never controls a path.
- Files are served back only through `GET /documents/{id}/file`, with `nosniff` and the stored content type.

## 3. Identity

- `security/identity.py` reads `X-Demo-User` and looks it up in `DEMO_USERS` (env JSON): `{"aisyah": {"name": "Aisyah (HR)", "groups": ["all", "hr"]}, "ben": {"name": "Ben (Staff)", "groups": ["all"]}}`. Unknown or missing → 401 `unknown_user`. The one exception is `GET /api/v1/config`, which is public and returns no document data.
- This is a stand-in for SSO. Replacing it is one module: `get_identity()` returns `Identity(id, name, groups, is_admin)` from the SSO token instead. **Every route gets the user only through the `get_identity` dependency**; nothing else reads identity headers.
- `AUTH_MODE` selects the source: `demo` (this section, the default) or `password` (M100, [SPEC-11 §5.2](SPEC-11-deployment.md#52-authentication-password-login)), which signs users in with a username and password from `LOGIN_USERS`, reads only the `rag_session` cookie and never reads `X-Demo-User`. `Identity.is_admin` is true for every demo user; in password mode only for users with `admin: true`.
- Upload, replace file, patch, delete, re-ingest and `/usage/summary` go through the `require_admin` dependency (`AdminUser`) → 403 `admin_only`. It runs before any document lookup, so a non-admin learns nothing about which ids exist. Every demo user passes it. `accessGroups` on upload/patch must be a subset of the caller's groups.

## 4. Private-marker invariant

- Test fixture `backend/tests/fixtures/private_salary_bands.md` contains `ZQX-PRIVATE-7` and is ingested with `access_groups = {hr-restricted}`. The test user `ben` has groups `{all}`.
- For `ben`, the string `ZQX-PRIVATE-7` must never appear in: `/search` hits, `/chat` events (any), `questions` rows written for ben, `/documents` list, `/documents/{id}` (404), `/documents/{id}/file` (404), `/documents/{id}/chunks` (404), `chunks?around=` pointing at a chunk of the private document (404), a duplicate upload of the private document's bytes (409 with no `existingId` or title), logs at INFO or above.
- The invariant suite grows with every milestone that adds a read path.

## 5. Secrets and logging

- Secrets only from env; `.env` gitignored; `.env.example` has every variable with an empty or placeholder value.
- `AI_API_KEY` never logged, never in error details; the settings object's `repr` masks it.
- Logs are JSON lines with `traceId`. Questions and chunk text are logged only at DEBUG.

## 6. Startup guards

- `APP_ENV=production` with `AI_PROVIDER=fake` → exit with "Fake AI provider is not allowed in production."
- `APP_ENV=production` with `AUTH_MODE=demo` → exit with "Demo identity is not allowed in production. Set AUTH_MODE."
- `AUTH_MODE=password` without `LOGIN_USERS`, with a `SESSION_SECRET` shorter than 32 characters, or with a user whose `passwordHash` is not a `scrypt:` hash → exit naming the variable (M100).
- Missing `AI_API_KEY` with a real provider → exit with a message naming the variable.

## 7. Prompt injection

- Document text is placed only in the user message under "Sources:", and the system prompt says sources are data ([SPEC-05 §2](SPEC-05-answering.md)).
- Model output is rendered as Markdown with `html: false` and sanitized ([SPEC-07 §5.3](SPEC-07-frontend.md)); links in answers are not auto-linked.

## 8. Acceptance checks

1. A `.pdf` file whose bytes are a PNG is stored as PNG type, and an `.exe` renamed to `.pdf` is rejected with 415.
2. A 26 MB upload returns 413 and leaves no file behind.
3. A filename `../../etc/passwd.pdf` is stored as `passwd.pdf` under the document's own folder.
4. **Private marker:** for user `ben`, `ZQX-PRIVATE-7` appears in no response of: search, chat (all events), documents list/get/file/chunks (including `around=`), a duplicate upload of the private file; for `aisyah` with `hr-restricted` added in the test, it is found.
5. The settings `repr` and every log line from a full test run contain no value of `AI_API_KEY`.
6. Startup guards in §6 behave as described.
7. Uploading with `accessGroups` outside the caller's groups returns 422.
