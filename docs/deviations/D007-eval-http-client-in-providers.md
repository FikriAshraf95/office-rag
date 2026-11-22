# D007 — Eval HTTP client lives in `providers/api_client.py`

- **Date / milestone:** 2026-11-21 · M06
- **Spec:** [SPEC-01 §2](../specs/SPEC-01-architecture.md) (module layout, boundaries), [SPEC-10 §5](../specs/SPEC-10-testing-and-eval.md#5-eval-script)
- **Status:** Resolved → spec updated (2026-11-21)

## Spec says
- `eval/` talks to the HTTP API only; no module outside `app/providers/` imports httpx (invariant `test_providers_boundary`).

## Implementation does
- `app/providers/api_client.py` exports `make_api_client`, `ApiClient`, `ApiResponse` and `TRANSPORT_ERRORS`; `app/eval/run.py` imports those instead of httpx.

## Why
- The eval is an SSE client, which needs httpx, and the invariant forbids importing it elsewhere. Loosening the invariant was the worse option.

## Consequences
- SPEC-01 §2 now lists the file and the eval row names it. No behaviour change.
