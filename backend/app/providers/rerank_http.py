"""Reranking over `POST {AI_BASE_URL}/rerank`, which the OpenAI SDK doesn't cover (SPEC-06 §2)."""

import asyncio
import time
from typing import Any

import httpx

from app.providers.base import Purpose, RerankHit, TokenUsage
from app.providers.errors import from_response, network_error
from app.providers.retry import DEFAULT_MAX_ATTEMPTS, Sleep, Throttle, with_retries
from app.providers.usage import UsageEntry, UsageRecorder


def make_http_client(
    base_url: str, api_key: str, *, transport: httpx.AsyncBaseTransport | None
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url.rstrip("/") + "/",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60,
        transport=transport,
    )


class HttpReranker:
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        provider: str,
        model: str,
        recorder: UsageRecorder,
        throttle: Throttle,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self.client = client
        self.provider = provider
        self.model = model
        self._recorder = recorder
        self._throttle = throttle
        self._max_attempts = max_attempts
        self._sleep = sleep

    async def _record(
        self,
        purpose: Purpose,
        ref_id: str | None,
        usage: TokenUsage,
        started: float,
        status: str,
        code: str | None,
    ) -> None:
        await self._recorder.record(
            UsageEntry(
                provider=self.provider,
                model=self.model,
                role="rerank",
                purpose=purpose,
                ref_id=ref_id,
                usage=usage,
                latency_ms=int((time.monotonic() - started) * 1000),
                status=status,
                error_code=code,
            )
        )

    async def rerank(
        self, query: str, documents: list[str], top_n: int, *, purpose: Purpose, ref_id: str | None = None
    ) -> list[RerankHit]:
        payload = {"model": self.model, "query": query, "documents": documents, "top_n": top_n}

        async def attempt() -> list[RerankHit]:
            await self._throttle.acquire(self.model)
            started = time.monotonic()
            try:
                resp = await self.client.post("rerank", json=payload)
            except httpx.HTTPError:
                err = network_error()
                await self._record(purpose, ref_id, TokenUsage(), started, "error", err.code)
                raise err from None
            if resp.status_code >= 400:
                try:
                    body: Any = resp.json()
                except ValueError:
                    body = None
                err = from_response(resp.status_code, resp.headers, body)
                await self._record(purpose, ref_id, TokenUsage(), started, "error", err.code)
                raise err
            self._recorder.note_balances(resp.headers)
            data = resp.json()
            raw_usage = data.get("usage") or {}
            usage = TokenUsage(
                prompt_tokens=int(raw_usage.get("prompt_tokens", 0)),
                total_tokens=int(raw_usage.get("total_tokens", raw_usage.get("prompt_tokens", 0))),
            )
            await self._record(purpose, ref_id, usage, started, "ok", None)
            hits = [
                RerankHit(index=int(r["index"]), score=float(r["relevance_score"])) for r in data["results"]
            ]
            return sorted(hits, key=lambda h: h.score, reverse=True)[:top_n]

        return await with_retries(attempt, max_attempts=self._max_attempts, sleep=self._sleep)
