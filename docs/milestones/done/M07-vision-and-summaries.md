# M07 — Vision fallback and document summaries *(stretch)*

> **Depends on:** [M06](M06-evaluation.md) · **Blocks:** —
> **Read first:** [SPEC-03 §4, §8](../../specs/SPEC-03-ingestion.md#4-parsing-per-file-type) · [SPEC-06 §2–3](../../specs/SPEC-06-ai-providers.md#2-clients)
> **Model:** Sonnet. Small, bounded additions to a working pipeline. (Switch to Opus if the vision output needs prompt design beyond the spec.)

## Goal
Images whose OCR text is thin or that are diagrams (the org chart) get a nemo-super vision description, so reporting-line questions can be answered. Optionally each document gets a short summary and tags from the fast model.

## Tasks
### Backend
- [x] Vision fallback for images (`ingestion/vision.py`, called by the worker); `image_text` chunks; usage logged. PDF pictures not done (D008).
- [x] Optional: summary + tags via the `fast` role after chunking; shown in the documents list (tooltip) and detail page.
### Frontend
- [x] Show `summary` and `tags` on the detail page if present.
### Tests
- [x] Vision path with FakeVisionModel: short OCR → vision called; long OCR on a non-diagram → not called.
- [x] Re-run the eval; compare vision questions with the M06 baseline.

## Acceptance criteria
1. The tests above are green, along with the full gates.
2. **Walkthrough:** re-ingest `Org_Chart_2026.jpg` → its chunk lists people and reporting lines; ask the org-chart eval questions → correct with a citation to the chart. New eval report committed.
3. **Deviations recorded**, or *"Deviations: none"*.

**Status:** DONE (2026-11-21). Acceptance verified: tests and full gates green (153 passed, Docling excluded); `Org_Chart_2026.jpg` re-ingested and its chunk lists all 12 people with reporting lines plus the free-standing team captions; eval `nemo-super-m07-run3` 27.5/32 and `run4` 26.5/32 against baseline 25 (target 26). Q23 and Q25 correct in every run since the fix; Q24 correct in run 3, partial in run 4 (right direction but omits Kumar Selvam: answer terseness, SPEC-05, accepted). Not done: vision for pictures inside PDFs (D008). Deviations: D008, D009.
