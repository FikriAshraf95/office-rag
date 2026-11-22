# Model comparison (M99, 2026-11-22)

One pass of all 32 questions per answer model, on the full Docker stack, as user `ben`. Everything else held fixed: same ingested corpus, bge-m3 embeddings, `bge-reranker` on (`MIN_RERANK_SCORE=0.1`), `MIN_VECTOR_SIM=0.53`, judge `nemo-super`. Only `LLM_ANSWER_MODEL` changed between runs.

| Answer model | Score | Correct / partial / wrong | Latency p50 / p95 | First token p50 | Tokens per question (in / out) | Answer cost per question | Billing |
|---|---|---|---|---|---|---|---|
| **nemo-super** (default) | **28.5 / 32 (89%)** | 28 / 1 / 3 | 455 / 734 ms | 355 ms | 761 / 22 | — | Plan quota |
| ilmu-nemo-nano | 25.5 / 32 (80%) | 22 / 7 / 3 | 351 / 624 ms | 301 ms | 761 / 30 | — | Plan quota |
| ilmu-glm-5.3-flash | 28 / 32 (88%) | 27 / 2 / 3 | 4,449 / 7,172 ms | 3,001 ms | 906 / 50 | MYR 0.0006 | PAYG |

Reports: [`2026-11-22-nemo-super-m99`](2026-11-22-nemo-super-m99.md), [`2026-11-22-ilmu-nemo-nano-m99`](2026-11-22-ilmu-nemo-nano-m99.md), [`2026-11-22-ilmu-glm-5.3-flash-m99`](2026-11-22-ilmu-glm-5.3-flash-m99.md).

**Retrieval cost is the same for every model:** bge-m3 query embedding plus bge-reranker over 30 candidates, about **MYR 0.0002 per question** (PAYG; the reranker is ~99% of it, ~5,400 tokens per question). Measured from the `usage` table over 109 questions.

## Reading it

- **Keep nemo-super.** It has the best score, sub-second answers, and no PAYG cost.
- **nano** is about 25% faster but loses 3 points, mostly as *partial* answers: it drops conditions ("plus toll and parking with receipts") and second facts in multi-part questions. Good enough for the `fast` role (summaries, tags), not for answers.
- **GLM** matches nemo-super on quality but is about 10× slower (first token ~3 s) and is the only paid one. It stays the `fallback` model only.
- **The misses are mostly retrieval, not the model.** Q14 and Q18 are refused by every model: their best reranker scores (0.008, 0.03) fall under the 0.1 gate (the known M08 trade-off). Q03 (E1 leave) failed for two of the three models in this pass. One run per model with an LLM judge varies by about ±1 point, so the nemo-super vs GLM gap is noise.

## Trend (nemo-super, same 32 questions)

| Run | Score |
|---|---|
| M06 baseline | 25 |
| M07 vision (4 runs) | 24 – 27.5 |
| M08 without reranker | 26 |
| M08 with reranker | 28 |
| **M99 full stack** | **28.5** |
