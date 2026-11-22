# Feature 1500 — Answer quality, usage and cost

> **Mock Azure DevOps export.** Parent: Epic 1000 — Company Docs Assistant · Created by Nurul Huda (PM) · State: New · 3 stories, 11 points

We can prove how good the answers are and what they cost.

## User Story 1501 — Measure answer accuracy on a test set

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 5 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** product manager, **I want** to score the assistant on a fixed set of questions, **so that** we know if a change made it better or worse.

**Details**

- Test set: 32 questions with expected answers and sources (samples/serimaju/eval). Includes tricky ones: old versions, the scanned memo, Malay, and questions with no answer.

**Acceptance criteria**

1. One command runs all 32 questions and scores each as correct, partial or wrong.
2. The report shows the total, the score per category and why each failure failed.
3. We reach at least 26/32 before the demo.
4. We can compare the three AI models on the same set.

## User Story 1502 — Track AI usage and cost

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 2 | 3 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** product manager, **I want** to see how many AI tokens and how much money each question and document uses, **so that** we can budget and show cost per question.

**Details**

- The monthly plan covers the main models; embeddings and the fallback model are pay-as-you-go.

**Acceptance criteria**

1. A Usage page shows totals by model and purpose, with cost in MYR where it applies.
2. It shows the remaining plan tokens and pay-as-you-go balance.
3. It shows average answer time and tokens per question.

## User Story 1503 — Improve result ranking

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 3 | 3 | Sprint 2026-11 (19–26 Nov) | stretch |

**As a** product manager, **I want** the most relevant passages ranked first, **so that** answers improve on hard questions.

**Details**

- Only keep it if the test score improves.

**Acceptance criteria**

1. Can be switched on and off by configuration.
2. Test scores with and without are compared and recorded.
