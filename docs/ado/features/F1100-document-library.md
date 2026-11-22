# Feature 1100 — Document library

> **Mock Azure DevOps export.** Parent: Epic 1000 — Company Docs Assistant · Created by Nurul Huda (PM) · State: New · 5 stories, 16 points

Document owners can add, review, correct and remove the documents the assistant answers from.

## User Story 1101 — Upload documents

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 5 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** document owner, **I want** upload PDF, Word, Excel, Markdown and image files, several at once, **so that** staff can ask questions about them.

**Details**

- Supported: PDF, DOCX, XLSX, MD, PNG, JPG/JPEG.
- Optional details on upload: title, document type, department, effective date, who can see it.

**Acceptance criteria**

1. Given I select several supported files, when I upload them, then each appears in the list straight away and I don't have to wait for processing.
2. Given a file is over the size limit, when I upload it, then I see a message with the limit and nothing is saved.
3. Given a file type we don't support, when I upload it, then I'm told which types are allowed.
4. Given the exact same file was already uploaded, when I upload it again, then I'm told it already exists, with a link to it.
5. Given I set "who can see it", then I can only choose groups I belong to myself.

**Questions for the developers**

- What should the size limit be? 25 MB feels enough for policies.
- Can we spot a duplicate even if the file was renamed?

## User Story 1102 — See all documents and their processing status

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 3 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** document owner, **I want** see every document with its details and whether it is ready to answer questions, **so that** I know when the assistant can use it and spot problems.

**Details**

- Columns: title, type, department, effective date, current/old version, processing status, who can see it, uploaded date.

**Acceptance criteria**

1. Processing status shows as Queued, Processing, Ready or Failed, and updates on its own without refreshing the page.
2. Failed documents show the reason in plain words.
3. I can filter to All, Current, Old versions or Failed, and search by title.
4. On a phone the list is readable without scrolling sideways.

## User Story 1103 — Correct document details and mark old versions

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 3 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** document owner, **I want** edit a document's details and mark it as replaced by a newer version, **so that** the assistant never answers from an outdated policy.

**Details**

- Example: HR Handbook 2024 is replaced by HR Handbook 2026.

**Acceptance criteria**

1. I can change title, type, department, effective date, version and who can see it.
2. When I mark a document as an old version, then from that moment it is never used in answers.
3. I can mark it as current again, and it is used again.
4. Changing who can see a document takes effect immediately everywhere.

**Questions for the developers**

- Should uploading a document with the same title replace the old one automatically?

## User Story 1104 — Delete a document

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 2 | 2 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** document owner, **I want** delete a document I uploaded by mistake, **so that** it is no longer shown or used.

**Acceptance criteria**

1. I must confirm before it is deleted.
2. After deleting, it disappears from the list and is never used in answers again.
3. The stored file is removed too.

## User Story 1105 — Open a document and see what the system read from it

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 2 | 3 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** document owner, **I want** open the original file and see the text the system extracted, **so that** I can check it was read correctly.

**Acceptance criteria**

1. PDFs and images open in the browser; other files can be downloaded.
2. I can see the extracted pieces in order, with their headings and page numbers.
3. If processing failed, I can retry from this page.
