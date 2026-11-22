# Presentation numbers (collected at M99, 2026-11-22)

Sources are linked so each figure can be rechecked. Rows marked **(fill in)** aren't recorded anywhere in the repo; take them from your own notes or the Claude Code session history.

## Build

| Figure | Value | Source |
|---|---|---|
| Specs | 12 (SPEC-00 … SPEC-11), v1 on 2026-11-19 | `docs/specs/` |
| Milestones | 10 built (M00–M08, M99); M100 after the talk | `docs/milestones/` |
| Calendar time, specs → release | 2026-11-19 → 2026-11-22 (4 days) | milestone status lines |
| M00–M03 | implemented 2026-11-20 | milestone status lines |
| M04–M08 | implemented 2026-11-21 | milestone status lines |
| M99 | 2026-11-22, one Opus session | this file |
| Hours per milestone | **(fill in)** | |
| Subagents spawned | **(fill in)** (M99: 0) | |
| Deviations logged | **9** (D001–D009), all folded into the specs; **0 open** | `docs/DEVIATIONS.md` |
| Deviations by milestone | M00 1 · M01 0 · M02 1 · M03 1 · M04 2 · M05 1 · M06 1 · M07 2 · M08 0 · M99 0 | `docs/DEVIATIONS.md` |
| Backend tests | 167 (fake AI, no network) | `uv run pytest` |
| Frontend tests | 94 | `npm run test` |

## Quality (eval, 32 questions, judge nemo-super)

| Run | Score |
|---|---|
| M06 baseline | 25 / 32 |
| M07 vision (4 runs) | 24 – 27.5 |
| M08 reranker off / on | 26 / 28 |
| **M99 full stack, nemo-super** | **28.5 / 32 (89%)** |
| M99 ilmu-nemo-nano | 25.5 |
| M99 ilmu-glm-5.3-flash | 28 |

Details: [eval-results/comparison.md](../eval-results/comparison.md).

## Speed and cost per question (nemo-super, reranker on)

| Figure | Value |
|---|---|
| Latency p50 / p95 | 455 / 734 ms |
| First token p50 | 355 ms |
| Tokens per answer | ~760 in, ~22 out (plan quota, 50M tokens/month) |
| PAYG cost per question | **≈ MYR 0.0002** (embed + rerank; the reranker is ~99%) |
| Questions per MYR 19.80 balance | ≈ 90,000 |
| Ingesting the 10 Serimaju files | ~1 minute on CPU; MYR 0.0004 of embeddings |

The `usage` table (`/usage` page) holds the raw calls.
