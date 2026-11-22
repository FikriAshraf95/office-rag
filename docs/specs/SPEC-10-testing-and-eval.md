# SPEC-10 — Testing and evaluation

> **Status:** v1 (2026-11-19) · **Owner of:** test conventions, the test host, invariants, the eval script and scoring

## 1. Test naming

- Every numbered acceptance check becomes a test named after it: pytest `test_spec03_ac06_xlsx_repeats_headers`, Vitest `it('Spec07_Ac02 renders citations and strips scripts')`.
- Extra tests (not from a check) use plain descriptive names.
- A check that spans milestones is listed in the milestone's *Checks finished in later milestones* table.

## 2. Backend test host

- pytest + pytest-asyncio (`asyncio_mode = auto`) + httpx `AsyncClient` with `ASGITransport`.
- **Real Postgres** with pgvector from the Compose `postgres` service; the test database `rag_test` is created and migrated once per session (`alembic upgrade head`), and each test runs in a transaction rolled back at the end. The `usage` writer is bound to the test connection in these tests so its rows roll back too ([SPEC-06 §6](SPEC-06-ai-providers.md)). Tests that need real commits use a truncate fixture instead: worker and concurrent-claim tests, and `jobs_new` notifications (Postgres delivers them only on commit).
- `AI_PROVIDER=fake` forced in `conftest.py`.
- **Network guard:** `pytest-socket` with `--disable-socket --allow-hosts=127.0.0.1,localhost,::1`, so any real ILMU call fails the test. Async tests run on the selector event loop on every platform: on Windows the default Proactor loop connects through `ConnectEx`, which bypasses the guard.
- Fixtures in `tests/fixtures/`: tiny PDF/DOCX/XLSX/MD/PNG files, the private-marker document, and copies of two Serimaju files (2026 handbook, leave XLSX) for the realistic parsing checks. Docling tests are marked `@pytest.mark.docling` (slow); they are part of the full gate but can be skipped locally with `-m "not docling"`.
- Worker tests call `process_one_job()` directly; no background loop in tests.

## 3. Invariant suite

`tests/invariants/` runs after every milestone and grows:

| Invariant | From |
|---|---|
| Private marker never visible to a non-member (all read paths) | M00 skeleton, grows M01–M04 |
| Superseded chunks never retrieved | M03 |
| No answer without a valid citation unless it's the not-found answer | M04 |
| No provider SDK or model name outside `providers/` | M00 |
| No real network in tests | M00 |

## 4. Frontend tests

Vitest + jsdom + `@vue/test-utils`, colocated `*.test.ts`. No Playwright for the MVP; the walkthrough is manual.

## 5. Eval script

`uv run python -m app.eval --base-url http://localhost:8000 --user ben --label nemo-super [--only Q01,Q28]`

1. Reads `samples/serimaju/eval/eval_questions.csv` (`id, question, expected_answer, expected_sources, category, notes`). **The CSV and FACT_SHEET.md are never ingested.**
2. For each question, calls `POST /api/v1/chat` like a user and collects the final answer, cited sources, `found`, model, latency, first-token time and tokens.
3. **Judge** (role `judge`, nemo-super, JSON mode, reasoning on `low`): given question, expected answer, notes and the system's answer, returns `{"verdict": "correct" | "partial" | "wrong", "reason": "…"}`.
   - correct (1): right facts, current version, conditions kept.
   - partial (0.5): right core fact but a missing condition or weak wording.
   - wrong (0): wrong or outdated value, or a guess on a not-found question.
4. **Source check:** expected source filenames (split on `;`, matched on the filename stem, case-insensitive) vs the cited documents' filenames. A `correct` verdict whose citations miss every expected source is downgraded to `partial`. Not-found questions pass the source check when `found = false`.
5. Writes `eval-results/<YYYY-MM-DD>-<label>.json` (all rows) and `.md` (score /32, % by category, failures with reasons, p50/p95 latency, first-token p50, tokens and cost per question). The answer model in the report header is the one named in the answers' `done.model`, not the eval process's own settings. Cost per question is the answer cost from the price table: a gate refusal (`done.model` null, no answer call) costs 0, and a run on a plan-quota model has no cost figure. `eval-results/` is committed (they're presentation material).
6. The judge's usage is logged with `purpose = 'eval'`. This is the eval process's only database use, and it goes through `providers` ([SPEC-01 §2](SPEC-01-architecture.md)), so the eval needs `DATABASE_URL`.

**Model comparison (M99):** run with `LLM_ANSWER_MODEL` set to `nemo-super`, `ilmu-nemo-nano` and `ilmu-glm-5.3-flash` (separate API restarts) and produce one comparison table. Keep GLM runs to one full pass (PAYG balance). Done 2026-11-22: [`eval-results/comparison.md`](../../eval-results/comparison.md).

## 6. Acceptance checks

1. The full backend suite passes with `AI_PROVIDER=fake` and the network guard on; a deliberate real HTTP call in a test fails.
2. The eval script, run against the API in fake mode with `--only Q01,Q30` (the fake judge returns a JSON verdict, [SPEC-01 §5](SPEC-01-architecture.md)), produces both report files with the expected structure (scores may be anything).
3. The source check downgrades a `correct` verdict with no matching source to `partial`, and passes a not-found question with `found = false`.
