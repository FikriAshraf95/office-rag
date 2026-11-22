# M99 — Release and demo

> **Depends on:** M05, M06 (M07, M08 if done) · **Blocks:** the presentation (2026-11-26)
> **Read first:** [SPEC-11 (whole file)](../specs/SPEC-11-deployment.md) · [SPEC-09 §1, §5–8](../specs/SPEC-09-security-and-access.md#1-data-rules) · [SPEC-06 §7](../specs/SPEC-06-ai-providers.md#7-switching-provider-production) · [DEVIATIONS](../DEVIATIONS.md)
> **Model:** Opus. Security sweep, folding deviations into specs and the final story need judgment.

## Goal
The whole stack runs with one `docker compose up`, the security sweep is clean, open deviations are folded into the specs, the model comparison is done, and the repo is ready to show as the SDD case study.

## Tasks
### Deploy
- [x] Complete `docker-compose.yml` (api, worker, frontend), backend multi-stage Dockerfile with baked Docling models, frontend Dockerfile + nginx config (SSE unbuffered, CSP for pdf.js).
### Security and docs
- [x] Security sweep against SPEC-09 (uploads, secrets in repo/images/logs, private-marker suite, CSP).
- [x] Fold every open deviation into its spec (status → Resolved → spec updated).
- [x] README: what it is, run book, "How to switch provider" (SPEC-06 §7), "Why no LangChain".
- [x] Optional: `app/ingestion/reembed.py` command; otherwise the procedure is documented only. *(Documented only: README "How to switch provider" step 2.)*
### Eval and demo
- [x] Final eval on nemo-super; one-pass comparison with ilmu-nemo-nano and ilmu-glm-5.3-flash (score, latency, tokens, cost) in `eval-results/comparison.md`.
- [x] Demo script (5–7 questions showing: memo override, table lookup, Malay, not-found, citation click, superseded filter, private-marker user switch).
- [x] Collect presentation numbers: time per milestone, subagent count, deviations count, eval trend, cost per question.
### Tests
- [x] SPEC-11 §6 checks 1–4.

## Acceptance criteria
1. The tests above are green, along with the full gates.
2. **Walkthrough:** fresh clone → `.env` → `docker compose up -d --build` → upload the 10 files → run the demo script end to end at `http://localhost:8080` without errors.
3. **Deviations:** none open (all folded into specs).

**Status:** DONE (2026-11-22), awaiting human review. Verified:
1. **Gates green:** backend 167 passed (incl. Docling) + ruff, format, mypy, import-linter (6 kept); frontend lint, typecheck, 94 tests, build. SPEC-11 §6 checks 1–4: static in `tests/spec11/test_deployment.py` (6 tests) and live in `scripts/release_check.sh`, all PASS on the running stack (SSE first delta 295 ms before `done`; worker image parsed a PDF with `--network none`; no key in any image's history, config or filesystem).
2. **Walkthrough:** working tree at `c259627` (not a separate clone) with fresh volumes → existing `.env` → `docker compose build && up -d` → 10 Serimaju files + the private fixture uploaded through nginx on :8080 (all Ready in ~1 min) → demo script questions 1–7 run in the browser via Playwright: all as expected, citation click opens the memo image and the PDF viewer, no console errors (CSP clean). Found in rehearsal and written into the demo script: two weak auto-titles (renamed in prep), and a topic change in one chat can come back not-found (use **New chat**; logged as enhancement E4).
3. **Security sweep:** key value absent from tracked files, git history, root `*.log` files and images; `.env` gitignored and dockerignored; logs carry ids and codes only, `hide_parameters=True`, search is POST so no query text in access logs; upload and private-marker suites green.
4. **Eval:** nemo-super 28.5/32 (best so far); nano 25.5; GLM 28 → [`eval-results/comparison.md`](../../eval-results/comparison.md). Fixed while doing it: the eval report took the answer model from its own settings instead of the answers, and showed no cost when the gate refused a question (SPEC-10 §5 now states both rules; regression test added).
5. **Specs folded:** no open deviations (D001–D009 all resolved). SPEC-11 §2 (model paths), §4 (dev container replaces the hybrid host setup, eval from the API image, release check) and §6 updated to match the code. Presentation numbers in [`presentation-notes/numbers.md`](../../presentation-notes/numbers.md); hours per milestone and subagent count are left for the author to fill in (not recorded in the repo).

Deviations: none.
