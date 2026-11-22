# M06 — Evaluation

> **Depends on:** [M04](M04-answering.md) · **Blocks:** [M99](M99-release-and-demo.md)
> **Read first:** [SPEC-10 §5–6](../../specs/SPEC-10-testing-and-eval.md#5-eval-script) · [SPEC-08 §6](../../specs/SPEC-08-api-contract.md#6-chat) · [SPEC-05 §6](../../specs/SPEC-05-answering.md#6-sse-events)
> **Model:** Sonnet. A script against a fixed API and a clear scoring rule.

## Goal
One command scores the system on the 32 Serimaju questions with an LLM judge plus a source check, and writes a JSON and Markdown report. The first baseline on nemo-super is committed.

## Tasks
### Backend
- [x] `app/eval/run.py` (CLI, SSE client), `judge.py` (JSON-mode prompt, `purpose = 'eval'`), `report.py` (score, by category, failures, latency, tokens, cost).
- [x] Baseline run on nemo-super → `eval-results/2026-11-2x-nemo-super.{json,md}`.
- [x] Triage failures: for each wrong/partial, note whether the cause is parsing, chunking, retrieval or answering (a table in the report). Fix only cheap, clearly-scoped issues here; log the rest for M07/M08.
### Tests
- [x] SPEC-10 §6 checks 2–3.

## Acceptance criteria
1. The tests above are green, along with the full gates.
2. **Walkthrough:** run the eval on the live stack; the report shows the score /32 and per-category results; Q01, Q28, Q30, Q31 results are visible. Target ≥ 26/32 (SPEC-00 §7); if below, the triage table explains why.
3. **Deviations recorded**, or *"Deviations: none"*.

**Status:** DONE (2026-11-21), awaiting human review.
- **Verified:** `uv run pytest -q -m "not docling"` (145 passed, incl. `tests/spec10/test_eval.py`), ruff, mypy, import-linter green. Live run on the stack (ILMU, `AI_PROVIDER=ilmu`, user `ben`, 10 Serimaju documents ready): `eval-results/2026-11-21-nemo-super.{json,md}`.
- **Baseline: 25 / 32 (78%)**, below the 26 target. Q01 partial; Q28 correct; Q30 and Q31 correct. Misses and the triage table are in the report: Q23-25 need M07 vision, Q02/Q05/Q27/Q01/Q12 are answering issues, logged for M07/M08. No fixes were made here.
- **Deviations:** D007 (eval's HTTP client in `providers/api_client.py`).
