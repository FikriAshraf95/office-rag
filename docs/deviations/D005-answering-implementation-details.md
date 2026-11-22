# D005 — Answering differs from SPEC-05 and SPEC-01 in three details

- **Date / milestone:** 2026-11-21 · M04
- **Spec:** [SPEC-05 §1, §6](../specs/SPEC-05-answering.md#1-flow) · [SPEC-01 §2](../specs/SPEC-01-architecture.md#2-module-boundaries)
- **Status:** Resolved → spec updated (folded at M99, 2026-11-21)

## Spec says
1. Search query with history: `"<previous question>\n<question>"`, the previous question capped at 1,000 characters. Retrieval (SPEC-04) cuts any query to 1,000 characters.
2. `done` carries `model` (the model actually used). The table gives no type.
3. `answering/` may import `retrieval.search`, `providers.registry` and `db`.

## Implementation does
1. The previous question is cut to whatever room the current question leaves, so `previous + "\n" + question` is never over 1,000 characters (`search_query()` in `backend/app/answering/service.py`). If the current question is close to 1,000 characters, the previous one is dropped.
2. `done.model` is `null` when no model was called (empty retrieval → not-found). `SseDone.model` is `string | null` in the OpenAPI document. `questions.model` is null too.
3. `answering/service.py` also imports `detect_language` from `app.ingestion.metadata`, a pure function with no I/O. The import-linter contract `answering-boundaries` forbids `api` and the ingestion writers (`service`, `worker`, `jobs`, `extract`).

## Why
1. Taken literally, two 1,000-character questions would join into a 2,001-character query, and retrieval would cut off the end: the *current* question, which matters most.
2. Reporting the answer model when it was never called would be false, and the eval (M06) uses `model` to attribute answers.
3. The not-found template and the prompt's Malay line (D004) must use the same detection as ingestion (SPEC-03 §6). A copy would drift.

## Consequences
1. Long follow-ups use less context from the previous question. This is rare: the UI's questions are short.
2. The frontend must accept `model: null` (generated types already do).
3. At M99, either fold `ingestion.metadata` into the SPEC-01 §2 allowed list or move `detect_language` to a shared module.
