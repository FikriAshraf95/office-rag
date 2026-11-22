# Feature 1300 — Ask questions

> **Mock Azure DevOps export.** Parent: Epic 1000 — Company Docs Assistant · Created by Nurul Huda (PM) · State: New · 7 stories, 22 points

Staff ask questions in a chat and get short, sourced answers they can trust.

## User Story 1301 — Ask a question and see the answer appear as it is written

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 5 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** staff member, **I want** to type a question and see the answer appear quickly, **so that** it feels like talking to a colleague, not waiting for a report.

**Details**

- Empty page shows a few example questions.

**Acceptance criteria**

1. The answer starts appearing within about 3 seconds.
2. Enter sends, Shift+Enter adds a new line.
3. I can stop an answer while it is being written.
4. "New chat" clears the conversation.

## User Story 1302 — See where each answer comes from

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 5 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** staff member, **I want** every fact in an answer to show its source, and to open that source, **so that** I can trust the answer and read the full rule.

**Acceptance criteria**

1. Every fact has a numbered reference like [1].
2. Under the answer I see the sources used: document, section, page and effective date.
3. Clicking a reference opens the document at that page (PDF), the image, or the extracted text.
4. An answer without any source is never shown.

## User Story 1303 — Say so when the answer isn't in the documents

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 3 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** staff member, **I want** the assistant to tell me when it doesn't know, and who to ask, **so that** I never act on a guess.

**Details**

- Examples: "What is the ESOS vesting schedule?", "Can I bring my pet to the office?" — not in any document.

**Acceptance criteria**

1. When no document answers the question, I see "I couldn't find this…" with a contact (HR, Finance or IT).
2. The assistant never makes up an answer.

**Questions for the developers**

- Who is the right contact for each topic?

## User Story 1304 — Use the latest rule when documents disagree

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 3 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** staff member, **I want** answers to follow the newest rule, **so that** I don't apply a policy that has been changed.

**Details**

- The 2024 handbook says 5 days per leave application, the 2026 handbook says 7, and the Sept 2026 memo says 10.

**Acceptance criteria**

1. Old versions are never used.
2. When a newer memo changes a handbook rule, the answer uses the memo and says it replaces the handbook.

## User Story 1305 — Ask in Bahasa Malaysia

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 2 | 2 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** staff member, **I want** to ask in Bahasa Malaysia and get the answer in Bahasa Malaysia, **so that** I can use the language I'm comfortable with.

**Details**

- The year-end closure notice is bilingual.

**Acceptance criteria**

1. A question in Malay gets an answer in Malay, with sources.
2. Malay and English documents are both found, whatever the language of the question.

## User Story 1306 — Ask follow-up questions

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 3 | 2 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** staff member, **I want** to ask a follow-up like "and for managers?", **so that** I don't have to repeat the whole question.

**Acceptance criteria**

1. The assistant understands a short follow-up in the same conversation.
2. Follow-up answers still cite documents, not earlier answers.

**Questions for the developers**

- How far back should it remember?

## User Story 1307 — Clear messages when the AI service has a problem

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 2 | 2 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** staff member, **I want** to understand what went wrong when I can't get an answer, **so that** I know whether to try again or tell someone.

**Acceptance criteria**

1. If the quota is used up, I'm told to contact the admin, with no Retry button.
2. If the service is busy or unavailable, I'm told to try again, with a Retry button.
3. If the connection drops mid-answer, the partial answer stays and is marked as cut off.
