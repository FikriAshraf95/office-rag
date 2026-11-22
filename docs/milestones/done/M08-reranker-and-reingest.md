# M08 — Reranker and hash-based re-ingest *(stretch)*

> **Depends on:** [M06](done/M06-evaluation.md) · **Blocks:** —
> **Read first:** [SPEC-04 §4, §6](../specs/SPEC-04-retrieval.md#4-relevance-gate) · [SPEC-06 §1–2](../specs/SPEC-06-ai-providers.md#1-provider-profile-env) · [SPEC-03 §7](../specs/SPEC-03-ingestion.md#7-re-ingest-and-delete)
> **Model:** Sonnet. Interfaces and fallbacks already exist; this wires them up and measures.

## Goal
`bge-reranker` reorders the top 30 fused hits to the final 8 when enabled, with graceful fallback, and the eval shows whether it helps. Uploading a changed version of a document can replace that document's file in place (hash-based re-ingest).

## Tasks
### Backend
- [x] Wire `retrieval/rerank.py` into search behind `RERANK_MODEL`; `MIN_RERANK_SCORE` gate; usage logged.
- [x] `POST /documents/{id}/file` (replace the file; same id; new hash; re-ingest; SPEC-08 row added in the same change) — or log a deviation to skip it if time is short.
### Frontend
- [x] "Replace file" action on the document detail page (if the endpoint is built).
### Tests
- [x] SPEC-04 §8 check 7 against the real code path (already written in M03 with the fake; extend).
- [x] Replace-file: old chunks gone, new chunks present, same document id.

## Acceptance criteria
1. The tests above are green, along with the full gates.
2. **Walkthrough:** run the eval with `RERANK_MODEL=bge-reranker` and without; commit both reports; keep the reranker on only if the score improves.
3. **Deviations recorded**, or *"Deviations: none"*.

**Status:** DONE (2026-11-21). Verified: backend and frontend gates green (full suite green: 157 backend, 94 frontend); replace-file driven live through the UI with Playwright (same id and title, new filename, old chunks gone, new chunks present, old stored file removed); eval walkthrough run on nemo-super:

| Run | Score |
|---|---|
| No reranker (`RERANK_MODEL=`) | 26 / 32 |
| **Reranker on, `MIN_RERANK_SCORE=0.1` (kept)** | **28 / 32** |
| Reranker on, `MIN_RERANK_SCORE=0.005` | 27 / 32 |

Reports in `eval-results/` (`*-m08-norerank`, `*-m08-rerank`, `*-m08-rerank-min0005`). The reranker stays on. Known trade-off at 0.1: Q14 and Q18 (inference questions whose best reranker score is 0.008 and 0.03) are falsely refused. Lowering the gate to 0.005 fixes them but loses Q01, Q03, Q05 and Q10, so the default stays 0.1. Single runs with an LLM judge vary by about a point. Fixed after M08: `test_spec05_sse_pings_while_waiting_and_cancels_on_disconnect` was a test-timing race (a ping could land during retrieval, before the model stream was held), not an app bug and not caused by M08; the test now counts only pings sent while the stream is held (`tests/spec05/test_answering.py`). Deviations: none.
