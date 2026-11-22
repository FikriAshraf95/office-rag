# SPEC-06 — AI providers

> **Status:** v1 (2026-11-19) · **Owner of:** provider profiles, roles, retries, error mapping, usage and cost logging, provider switching
> Interfaces and fakes: [SPEC-01 §4–5](SPEC-01-architecture.md) · Verified against docs.ilmu.ai on 2026-11-19

## 1. Provider profile (env)

| Variable | ILMU demo value | Notes |
|---|---|---|
| `AI_PROVIDER` | `ilmu` | `ilmu`, `openai`, `azure`, `fake` |
| `AI_BASE_URL` | `https://api.ilmu.ai/v1` | Azure: the resource's OpenAI v1 endpoint (verify in M99) |
| `AI_API_KEY` | *(secret)* | Bearer token. Never logged. |
| `LLM_ANSWER_MODEL` | `nemo-super` | Plan quota (Claw). 256K context, thinking, JSON mode, image input |
| `LLM_FAST_MODEL` | `ilmu-nemo-nano` | Plan quota. Deeper Bahasa Malaysia training |
| `LLM_FALLBACK_MODEL` | `ilmu-glm-5.3-flash` | PAYG (RM 0.55 / 1M input, RM 1.85 / 1M output). Thinking can't be disabled (`none` → `low`) |
| `LLM_VISION_MODEL` | `nemo-super` | |
| `LLM_JUDGE_MODEL` | `nemo-super` | Eval only |
| `EMBED_MODEL` / `EMBED_DIM` | `bge-m3` / `1024` | PAYG, RM 0.04 / 1M. Max input 8,192 tokens. No `dimensions` truncation. No query/document prefixes |
| `RERANK_MODEL` | *(empty)* → `bge-reranker` in M08 | PAYG, RM 0.04 / 1M. `POST /v1/rerank`, not in the OpenAI SDK |
| `AI_MAX_RPM` | `50` | Client-side throttle per model (PAYG default limit is 60/min per model) |

Each provider has a small adapter in `providers/` for its differences (Azure: deployment names, `api-key` header). App code only sees roles.

## 2. Clients

- **Chat, vision, embeddings:** official `openai` Python SDK, `AsyncOpenAI(base_url=AI_BASE_URL, api_key=AI_API_KEY, max_retries=0, timeout=60)`. Retries are ours (§4), so the SDK's own retries are off.
- **Thinking:** pass `reasoning_effort="none"` for normal answers (`extra_body` if the SDK rejects the value). Only when `capabilities.supports_thinking`.
- **Streaming:** `stream=True` with `stream_options={"include_usage": True}`; ILMU puts `usage` on the final chunk.
- **Images:** content part `{"type": "image_url", "image_url": {"url": "data:image/png;base64,…", "detail": "high"}}`. Limits: 20 MB per image, 25 MB per request.
- **Rerank:** `httpx.AsyncClient` `POST {AI_BASE_URL}/rerank` with `{model, query, documents, top_n}`; results are `{index, relevance_score}` sorted descending.

## 3. Capabilities

| Provider/model | thinking | image input | JSON mode | reranker |
|---|---|---|---|---|
| ILMU nemo-super, ilmu-nemo-nano | on/off | yes | yes | — |
| ILMU ilmu-glm-5.3-flash | always on | no (assume) | yes | — |
| ILMU bge-reranker | — | — | — | yes |
| fake | off | yes | yes | yes |

## 4. Retries and throttling

- Token-bucket throttle per model at `AI_MAX_RPM`. The worker additionally runs one embedding batch at a time.
- **Retryable:** `429` with `x-ilmu-error-code: rate_limit.exceeded` (or no header on non-ILMU providers), `500`, `502`, `503`, `504`, connection errors and timeouts.
- Backoff: honour `Retry-After` when present; else `min(30 s, 1 s × 2^attempt) + jitter(0–1 s)`. Max 5 attempts in the API path for embeddings and up to the job's attempts in the worker. For a streaming answer, retry only before the first delta.
- **Not retryable:** everything below.
- Each attempt is one provider call and writes its own `usage` row (§6).

## 5. Error mapping

`providers/errors.py` raises one `ProviderError(code, retryable, http_status, provider_code)`:

| Provider response | `code` | Retry | User-facing |
|---|---|---|---|
| 429 + `x-ilmu-error-code: rate_limit.exceeded` | `rate_limited` | yes | "The AI service is busy. Try again in a minute." |
| 429 + `x-ilmu-error-code: billing.token_quota_exhausted` | `quota_exhausted` | **no** | "The AI plan's monthly quota is used up. Ask the admin to top up or wait for the next cycle." |
| 402 (`billing.no_allocation`) | `quota_exhausted` | **no** | "The AI pay-as-you-go balance is used up. Ask the admin to top up." |
| 401 | `provider_auth` | no | "The AI service rejected the API key. Check AI_API_KEY." (admin wording; logged) |
| 403 `model_not_allowed` | `model_not_allowed` | no | "This AI model isn't available on the current plan." |
| 400 `context_length_exceeded` | `context_too_long` | no | Internal: shrink context and retry once |
| 413 | `request_too_large` | no | Ingestion: `parse` failure with a size message |
| 5xx, timeout, network | `provider_unavailable` | yes | "The AI service isn't responding. Try again shortly." |

Ingestion maps `quota_exhausted` → `ingest_error_code = 'quota'`, `rate_limited` after retries → `rate_limit`, others → `provider` ([SPEC-03 §3](SPEC-03-ingestion.md)).

`context_too_long` and `request_too_large` are handled inside the app (shrink once; or an ingestion `parse` failure). If one still reaches an API request, it is returned as `500 internal` ([SPEC-08 §2](SPEC-08-api-contract.md)).

## 6. Usage and cost logging

- Every provider call (success or failure) writes one `usage` row ([SPEC-02 §6](SPEC-02-database-schema.md)) with role, purpose, ref id, tokens and latency. Reasoning tokens come from `usage.completion_tokens_details.reasoning_tokens` when present.
- Cost: `pricing.py` holds a price table per `(provider, model)`: input and output MYR per 1M tokens. Plan-quota models (nemo-super, ilmu-nemo-nano) have `cost_myr = null` and are reported as tokens against the monthly quota.
- Read and log (at INFO, no secrets) `x-ilmu-token-balance` and `x-ilmu-payg-balance-myr` when present; expose the latest values in `GET /api/v1/usage/summary`.
- Writes happen in their own short transaction so a failed request still logs usage. In tests that roll back, the writer is bound to the test connection so its rows roll back too ([SPEC-10 §2](SPEC-10-testing-and-eval.md)).

## 7. Switching provider (production)

1. Set the new profile env (`AI_PROVIDER`, `AI_BASE_URL`, `AI_API_KEY`, model names, `EMBED_MODEL`, `EMBED_DIM`).
2. If `EMBED_MODEL` changed: run `python -m app.ingestion.reembed` — a background, resumable, rate-limit-aware job that re-embeds every chunk in batches into a second embedding column or table sized `EMBED_DIM` (its shape goes into [SPEC-02](SPEC-02-database-schema.md) in the same change) (≤ 2,000 for `vector` HNSW, ≤ 4,000 with `halfvec`), then switches search over. Never mix models in one index. (Built in M99 if time allows; otherwise documented as the procedure.)
3. Turn reranking off if the provider has none.
4. Run the eval (all 32 questions) and compare with the ILMU baseline. **The eval is the acceptance gate for a provider switch.**
5. Check data residency of the provider/region against company policy before go-live.

## 8. Acceptance checks

1. A rate-limit 429 with `Retry-After: 2` is retried after ≥ 2 s and then succeeds (mocked transport).
2. A 429 with `billing.token_quota_exhausted` raises `quota_exhausted` immediately, with no retry.
3. A 402 raises `quota_exhausted`, with no retry.
4. Every call writes a `usage` row with the right role, purpose, tokens and `status`, including failed calls.
5. Cost is computed for PAYG models from the price table and is null for plan models.
6. Streaming collects usage from the final chunk.
7. No module outside `app/providers/` contains a model name string or imports `openai` (import-linter + a grep test for the configured model names in `app/` outside `providers/` and `config.py`).
8. `reasoning_effort` is sent as `none` for answers on models that support thinking.
