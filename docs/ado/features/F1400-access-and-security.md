# Feature 1400 — Access and security

> **Mock Azure DevOps export.** Parent: Epic 1000 — Company Docs Assistant · Created by Nurul Huda (PM) · State: New · 4 stories, 12 points

People only ever see documents they are allowed to see, and the system is safe to run.

## User Story 1401 — Restrict documents to groups

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 5 | Sprint 2026-11 (19–26 Nov) | mvp; security |

**As a** document owner, **I want** to choose which groups can see a document, **so that** sensitive documents (e.g. salary bands) stay with HR.

**Details**

- Until we have company sign-in, the demo uses two sample users: Aisyah (HR) and Ben (Staff).

**Acceptance criteria**

1. Documents are visible to everyone unless restricted.
2. A person outside the group never sees the document: not in the list, not in answers, not in sources, not via a direct link — not even that it exists.
3. In the demo I can switch between Aisyah and Ben to show the difference.

**Questions for the developers**

- When do we connect company sign-in (SSO)?

## User Story 1402 — Only accept safe uploads

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 3 | Sprint 2026-11 (19–26 Nov) | mvp; security |

**As a** admin, **I want** uploads to be checked before they are stored, **so that** a malicious file can't harm the system.

**Acceptance criteria**

1. A file is checked by its real content, not only its name.
2. Oversized and unsupported files are refused.
3. Odd file names can't be used to write files in the wrong place.

## User Story 1403 — Protect keys and data

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 2 | Sprint 2026-11 (19–26 Nov) | mvp; security |

**As a** admin, **I want** API keys and documents handled safely, **so that** we meet company and PDPA expectations.

**Details**

- Demo uses fictional documents only. ILMU processes and stores data in Malaysia; confirm with IT before any real documents are used.

**Acceptance criteria**

1. API keys are never in code, logs or error messages.
2. The demo uses only the fictional Serimaju documents.
3. Test mode can never be switched on in production.

**Questions for the developers**

- Is ILMU approved for real company documents?

## User Story 1404 — Ignore instructions hidden inside documents

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 2 | 2 | Sprint 2026-11 (19–26 Nov) | mvp; security |

**As a** admin, **I want** text inside a document never to change how the assistant behaves, **so that** nobody can trick it by uploading a crafted file.

**Acceptance criteria**

1. A document saying "ignore your rules and…" does not change the answer format or reveal internal instructions.
2. Answers can't inject scripts or links into the page.
