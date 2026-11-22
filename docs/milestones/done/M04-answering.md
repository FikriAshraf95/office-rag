# M04 — Answering and chat API

> **Depends on:** [M03](M03-retrieval.md) · **Blocks:** [M06](M06-evaluation.md)
> **Read first:** [SPEC-05 (whole file)](../../specs/SPEC-05-answering.md) · [SPEC-06 §2, §5–6](../../specs/SPEC-06-ai-providers.md#2-clients) · [SPEC-08 §6–7](../../specs/SPEC-08-api-contract.md#6-chat) · [SPEC-02 §5–6](../../specs/SPEC-02-database-schema.md#5-questions)
> **Model:** Opus. The prompt, refusal behaviour and citation validation decide answer quality and safety.

## Goal
`POST /api/v1/chat` streams grounded answers with validated citations over SSE, refuses with a contact when the documents don't answer, falls back to the fallback model when needed, and logs every question and its usage.

## Tasks
### Backend
- [x] `answering/prompt.py` (v1 prompt, context budget), `answering/citations.py`, `answering/service.py` (event generator, NOT_FOUND buffering, uncited rule, fallback, cancellation).
- [x] Endpoint 13 (`StreamingResponse`, `text/event-stream`, keep-alive pings, disconnect handling) and 14 (`/usage/summary`, balances from headers).
- [x] Not-found contacts from config, Malay template.
### Frontend
- [x] None required (M05 builds the chat UI). Provide a recorded SSE fixture of a real answer for `src/fixtures/`.
### Tests
- [x] SPEC-05 §7 checks 1–9.
- [x] SPEC-08 §8 check 1 (full route list now complete).
- [x] Invariants: private marker on `/chat` events and `questions` rows; no uncited answers.

## Acceptance criteria
1. The tests above are green, along with the full gates.
2. **Walkthrough (real ILMU):** `curl -N` the chat endpoint with Q01 → streamed answer says 10 days with citations to the memo and handbook; Q28 in Malay → answer in Malay; Q30 (ESOS) → not-found with a contact and no LLM call or a NOT_FOUND reply; `/usage/summary` shows tokens per question. Record first-token latency.
3. **Deviations recorded**, or *"Deviations: none"*.

**Status:** DONE (2026-11-21), awaiting human review.
Verified: backend ruff, ruff format, mypy --strict, lint-imports (6 contracts kept: `app.answering` added to the SDK, Docling and `providers-are-low-level` contracts, plus a new `answering-boundaries` contract) and pytest (143 passed, network guard on); frontend `gen:api`, lint, typecheck, test (76 passed) and build. Tests: SPEC-05 §7 checks 1-11 (`tests/spec05/test_answering.py`, 23 tests, including the Malay not-found, fallback for plan quota vs PAYG 402, no fallback for `provider_auth`, `context_too_long` shrink-once, keep-alive ping and both disconnect paths: task cancellation and stream close), SPEC-08 §8 checks 1 (route list = the 14 rows of the §1 table, parsed from the spec) and 6 (five SSE schemas in the exported OpenAPI), `/usage/summary` (`tests/spec08/test_usage.py`), and invariants: `ZQX-PRIVATE-7` and the private title absent from every `/chat` event and every `questions` row written for Ben (`tests/invariants/test_private_marker.py`); no `found = true` answer without a valid citation, on screen or in the row (`tests/invariants/test_cited_answers.py`).
Walkthrough (real ILMU, API on :8010 because :8000 was taken by another process, dev database, as Ben, `curl -N`): **Q01** → "10 working days (with immediate supervisor approval) [3]", source 3 = the memo (effective 2026-10-01), first token 290-676 ms over three runs; **gap:** it cites only the memo, not also the handbook, and does not say the memo replaces the handbook's 7 days (a rule-3 wording change, "…and cite both", did not change this; left to M06 tuning). **Q28** → with prompt v1 the answer came back in English; with the v2 Malay line (D004): "Tidak perlu. 29 Disember 2026 adalah cuti syarikat … [1][2]", first token 393 ms. **Q30** → gate refused, not-found with "HR, hr@serimaju.example", no LLM call, `model: null`, 120 ms. `/usage/summary` → 7 questions, avgTokens 1,743 per question, avgFirstTokenMs 409, avgLatencyMs 492, byModel per role/purpose, plan balance 49,910,491 tokens with `readAt`. Recorded SSE fixtures: `frontend/src/fixtures/chat-answer.sse` (Q01) and `chat-not-found.sse` (Q30).
Also noticed (M02, not changed here): the memo PNG's title is "SERIMAJU TECHNOLOGIES SDN BHD" (OCR letterhead) and its heading path "INTERNAL N MEMO"; citations show that title.
Deviations: D004 (Malay language line, prompt v2; resolved → spec updated), D005 (history search query fits 1,000 chars, `done.model` null without a model call, `detect_language` imported from `ingestion.metadata`).
