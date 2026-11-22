# M99 — Release and demo

> **Depends on:** M05, M06 (M07, M08 if done) · **Blocks:** the presentation (2026-11-26)
> **Read first:** [SPEC-11 (whole file)](../specs/SPEC-11-deployment.md) · [SPEC-09 §1, §5–8](../specs/SPEC-09-security-and-access.md#1-data-rules) · [SPEC-06 §7](../specs/SPEC-06-ai-providers.md#7-switching-provider-production) · [DEVIATIONS](../DEVIATIONS.md)
> **Model:** Opus. Security sweep, folding deviations into specs and the final story need judgment.

## Goal
The whole stack runs with one `docker compose up`, the security sweep is clean, open deviations are folded into the specs, the model comparison is done, and the repo is ready to show as the SDD case study.

## Tasks
### Deploy
- [ ] Complete `docker-compose.yml` (api, worker, frontend), backend multi-stage Dockerfile with baked Docling models, frontend Dockerfile + nginx config (SSE unbuffered, CSP for pdf.js).
### Security and docs
- [ ] Security sweep against SPEC-09 (uploads, secrets in repo/images/logs, private-marker suite, CSP).
- [ ] Fold every open deviation into its spec (status → Resolved → spec updated).
- [ ] README: what it is, run book, "How to switch provider" (SPEC-06 §7), "Why no LangChain".
- [ ] Optional: `app/ingestion/reembed.py` command; otherwise the procedure is documented only.
### Eval and demo
- [ ] Final eval on nemo-super; one-pass comparison with ilmu-nemo-nano and ilmu-glm-5.3-flash (score, latency, tokens, cost) in `eval-results/comparison.md`.
- [ ] Demo script (5–7 questions showing: memo override, table lookup, Malay, not-found, citation click, superseded filter, private-marker user switch).
- [ ] Collect presentation numbers: time per milestone, subagent count, deviations count, eval trend, cost per question.
### Tests
- [ ] SPEC-11 §6 checks 1–4.

## Acceptance criteria
1. The tests above are green, along with the full gates.
2. **Walkthrough:** fresh clone → `.env` → `docker compose up -d --build` → upload the 10 files → run the demo script end to end at `http://localhost:8080` without errors.
3. **Deviations:** none open (all folded into specs).

**Status:**
