# Feature 1200 — Document processing

> **Mock Azure DevOps export.** Parent: Epic 1000 — Company Docs Assistant · Created by Nurul Huda (PM) · State: New · 8 stories, 39 points

Uploaded documents are read correctly, whatever their format, so answers can quote the right section, page or table row.

## User Story 1201 — Process documents in the background

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 8 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** document owner, **I want** documents to be processed automatically after upload, **so that** I don't have to wait, and chat stays fast for everyone.

**Details**

- The AI service has a monthly plan quota and a pay-as-you-go balance. Running out must be handled gracefully.

**Acceptance criteria**

1. Upload returns immediately; processing happens separately and does not slow down chat.
2. If the AI service is briefly busy, processing retries by itself.
3. If the AI quota or balance is used up, the document shows Failed with a message saying so, and does not keep retrying. I can retry it later.
4. If the system restarts during processing, the document is picked up again.

**Questions for the developers**

- How many documents can we process at the same time?

## User Story 1202 — Read PDF and Word documents with their structure

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 8 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** staff member, **I want** answers to point at the exact section and page, **so that** I can check the policy myself.

**Details**

- Handbooks have numbered sections (e.g. §4.2) and tables.

**Acceptance criteria**

1. Headings, section numbers, page numbers and tables are kept.
2. An answer from the HR Handbook can cite something like "HR Handbook 2026, §4.2, p.2".
3. A long section is not cut in the middle of a sentence or table row.

## User Story 1203 — Read Excel spreadsheets correctly

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 5 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** staff member, **I want** to ask questions that need a lookup in a spreadsheet, **so that** I don't have to open the file and find the row myself.

**Details**

- Example: Leave_Entitlement_by_Grade_2026.xlsx — "How many days of annual leave does a Grade M2 manager with 6 years of service get?" → 22.

**Acceptance criteria**

1. Each row is understood together with its column headers.
2. Cells with formulas use the calculated value.
3. All sheets in the workbook are read.

**Questions for the developers**

- Do we need to handle very large spreadsheets (thousands of rows)?

## User Story 1204 — Read scanned documents and images

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 5 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** staff member, **I want** scanned memos to count as much as typed documents, **so that** I get the latest rule even when it was only sent as a scan.

**Details**

- Example: the scanned HR memo of Sept 2026 raises the leave limit per application from 7 to 10 days.

**Acceptance criteria**

1. Text in a scanned PNG/JPG is read and can be found by questions.
2. If no text can be read at all, the document shows Failed with a clear reason.

**Questions for the developers**

- What about diagrams like the org chart? (see 1205)

## User Story 1205 — Understand diagrams such as org charts

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 3 | 5 | Sprint 2026-11 (19–26 Nov) | stretch |

**As a** staff member, **I want** to ask who reports to whom, **so that** I can find the right person without the org chart open.

**Details**

- Example: Org_Chart_2026.jpg.

**Acceptance criteria**

1. Reporting lines and job titles in the org chart can be found by questions.
2. Answers cite the org chart.

## User Story 1206 — Detect old versions automatically

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 2 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** document owner, **I want** documents marked SUPERSEDED to be treated as old versions without my help, **so that** nobody gets an answer from an outdated policy by mistake.

**Details**

- The 2024 handbook says SUPERSEDED on page 1.

**Acceptance criteria**

1. A document with SUPERSEDED (or DIGANTIKAN) on its first page is marked as an old version after processing.
2. I can still change it by hand.

## User Story 1207 — Fill in document details automatically

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 2 | 3 | Sprint 2026-11 (19–26 Nov) | mvp; stretch |

**As a** document owner, **I want** title, effective date, version and department filled in from the file, **so that** I don't have to type them for every upload.

**Details**

- A short summary and topic tags per document would be nice to have.

**Acceptance criteria**

1. When I don't give details, they are taken from the file where possible.
2. Details I typed myself always win.
3. (Nice to have) Each document gets a short summary and up to 5 tags.

## User Story 1208 — Replace a document with a new version of the file

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 3 | 3 | Sprint 2026-11 (19–26 Nov) | stretch |

**As a** document owner, **I want** to upload a newer file for an existing document, **so that** links and settings stay the same.

**Acceptance criteria**

1. The document keeps its details and who-can-see settings.
2. Only the new content is used in answers once processing is done.
