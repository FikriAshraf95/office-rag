"""Chat, streaming, embeddings and vision over any OpenAI-compatible API (SPEC-06 §2)."""

import asyncio
import base64
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, cast

import httpx
import httpx2
import openai
from openai import AsyncOpenAI, omit
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletionMessageParam
from openai.types.shared_params import ResponseFormatJSONObject

from app.providers.base import (
    Capabilities,
    ChatDelta,
    ChatResult,
    Message,
    Purpose,
    Reasoning,
    TokenUsage,
    UsageRole,
)
from app.providers.errors import ProviderError, from_response, network_error
from app.providers.retry import DEFAULT_MAX_ATTEMPTS, Sleep, Throttle, backoff_delay, with_retries
from app.providers.usage import UsageEntry, UsageRecorder

# SPEC-06 §3. Unknown models get JSON mode only.
MODEL_CAPABILITIES: dict[str, Capabilities] = {
    "nemo-super": Capabilities(supports_thinking=True, supports_image_input=True, supports_json_mode=True),
    "ilmu-nemo-nano": Capabilities(
        supports_thinking=True, supports_image_input=True, supports_json_mode=True
    ),
    "ilmu-glm-5.3-flash": Capabilities(supports_thinking=True, supports_json_mode=True),
}
ALWAYS_THINKING = {"ilmu-glm-5.3-flash"}  # thinking can't be disabled: `none` → `low`


def capabilities_for(model: str) -> Capabilities:
    return MODEL_CAPABILITIES.get(model, Capabilities(supports_json_mode=True))


def make_client(
    base_url: str, api_key: str, *, provider: str, http_client: httpx2.AsyncClient | None
) -> AsyncOpenAI:
    headers = {"api-key": api_key} if provider == "azure" else None
    return AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
        max_retries=0,
        timeout=60,
        default_headers=headers,
        http_client=http_client,
    )


def _convert(exc: Exception) -> ProviderError:
    if isinstance(exc, openai.APIStatusError):
        try:
            body: Any = exc.response.json()
        except ValueError:
            body = None
        return from_response(exc.status_code, exc.response.headers, body)
    return network_error()


def _usage(usage: CompletionUsage | None) -> TokenUsage:
    if usage is None:
        return TokenUsage()
    details = usage.completion_tokens_details
    return TokenUsage(
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        reasoning_tokens=(details.reasoning_tokens or 0) if details else 0,
        total_tokens=usage.total_tokens,
    )


# The OpenAI SDK runs on httpx2; mid-stream transport errors may surface unwrapped.
JSON_OBJECT: ResponseFormatJSONObject = {"type": "json_object"}

CALL_ERRORS = (openai.APIError, httpx2.HTTPError, httpx.HTTPError)


class _OpenAICompat:
    def __init__(
        self,
        client: AsyncOpenAI,
        *,
        provider: str,
        model: str,
        usage_role: UsageRole,
        recorder: UsageRecorder,
        throttle: Throttle,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self.client = client
        self.provider = provider
        self.model = model
        self.capabilities = capabilities_for(model)
        self._usage_role: UsageRole = usage_role
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
        error_code: str | None = None,
    ) -> None:
        await self._recorder.record(
            UsageEntry(
                provider=self.provider,
                model=self.model,
                role=self._usage_role,
                purpose=purpose,
                ref_id=ref_id,
                usage=usage,
                latency_ms=int((time.monotonic() - started) * 1000),
                status=status,
                error_code=error_code,
            )
        )

    async def _call[R](
        self,
        send: Callable[[], Awaitable[Any]],
        parse: Callable[[Any], tuple[R, TokenUsage]],
        purpose: Purpose,
        ref_id: str | None,
    ) -> R:
        async def attempt() -> R:
            await self._throttle.acquire(self.model)
            started = time.monotonic()
            try:
                raw = await send()
            except CALL_ERRORS as exc:
                err = _convert(exc)
                await self._record(purpose, ref_id, TokenUsage(), started, "error", err.code)
                raise err from None
            self._recorder.note_balances(raw.headers)
            result, usage = parse(raw.parse())
            await self._record(purpose, ref_id, usage, started, "ok")
            return result

        return await with_retries(attempt, max_attempts=self._max_attempts, sleep=self._sleep)

    def _reasoning_effort(self, reasoning: Reasoning) -> str | None:
        if not self.capabilities.supports_thinking:
            return None
        effort = "none" if reasoning == "off" else reasoning
        if effort == "none" and self.model in ALWAYS_THINKING:
            effort = "low"
        return effort

    def _extra_body(self, reasoning: Reasoning) -> dict[str, Any] | None:
        effort = self._reasoning_effort(reasoning)
        return {"reasoning_effort": effort} if effort else None


class OpenAICompatChat(_OpenAICompat):
    def __init__(self, client: AsyncOpenAI, *, role: str, usage_role: UsageRole, **kwargs: Any) -> None:
        super().__init__(client, usage_role=usage_role, **kwargs)
        self.role = role

    async def complete(
        self,
        messages: list[Message],
        *,
        json_mode: bool = False,
        reasoning: Reasoning = "off",
        max_tokens: int | None = None,
        purpose: Purpose,
        ref_id: str | None = None,
    ) -> ChatResult:
        def send() -> Awaitable[Any]:
            return self.client.chat.completions.with_raw_response.create(
                model=self.model,
                messages=cast(list[ChatCompletionMessageParam], messages),
                max_tokens=max_tokens if max_tokens is not None else omit,
                response_format=JSON_OBJECT if json_mode else omit,
                extra_body=self._extra_body(reasoning),
            )

        def parse(resp: Any) -> tuple[ChatResult, TokenUsage]:
            usage = _usage(resp.usage)
            text = resp.choices[0].message.content or "" if resp.choices else ""
            return ChatResult(text=text, model=self.model, usage=usage), usage

        return await self._call(send, parse, purpose, ref_id)

    async def stream(
        self,
        messages: list[Message],
        *,
        reasoning: Reasoning = "off",
        max_tokens: int | None = None,
        temperature: float | None = None,
        purpose: Purpose,
        ref_id: str | None = None,
    ) -> AsyncIterator[ChatDelta]:
        """Yields text deltas; the last item carries usage. Retries only before the first delta."""
        for attempt in range(self._max_attempts):
            await self._throttle.acquire(self.model)
            started = time.monotonic()
            usage = TokenUsage()
            emitted = False
            status: str = "error"
            error_code: str | None = "cancelled"
            try:
                raw = await self.client.chat.completions.with_raw_response.create(
                    model=self.model,
                    messages=cast(list[ChatCompletionMessageParam], messages),
                    max_tokens=max_tokens if max_tokens is not None else omit,
                    temperature=temperature if temperature is not None else omit,
                    stream=True,
                    stream_options={"include_usage": True},
                    extra_body=self._extra_body(reasoning),
                )
                self._recorder.note_balances(raw.headers)
                async for chunk in raw.parse():
                    if chunk.usage is not None:
                        usage = _usage(chunk.usage)
                    for choice in chunk.choices:
                        if choice.delta.content:
                            emitted = True
                            yield ChatDelta(text=choice.delta.content)
                status, error_code = "ok", None
            except CALL_ERRORS as exc:
                err = _convert(exc)
                error_code = err.code
                if err.retryable and not emitted and attempt < self._max_attempts - 1:
                    await self._record(purpose, ref_id, usage, started, "error", error_code)
                    status = "recorded"
                    await self._sleep(backoff_delay(attempt, err.retry_after))
                    continue
                raise err from None
            finally:
                if status != "recorded":
                    await self._record(purpose, ref_id, usage, started, status, error_code)
            yield ChatDelta(text="", usage=usage)
            return


class OpenAICompatVision(_OpenAICompat):
    async def describe(
        self, image: bytes, mime: str, instruction: str, *, purpose: Purpose, ref_id: str | None = None
    ) -> ChatResult:
        data_url = f"data:{mime};base64,{base64.b64encode(image).decode()}"
        messages: list[Message] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                ],
            }
        ]

        def send() -> Awaitable[Any]:
            return self.client.chat.completions.with_raw_response.create(
                model=self.model,
                messages=cast(list[ChatCompletionMessageParam], messages),
                extra_body=self._extra_body("off"),
            )

        def parse(resp: Any) -> tuple[ChatResult, TokenUsage]:
            usage = _usage(resp.usage)
            text = resp.choices[0].message.content or "" if resp.choices else ""
            return ChatResult(text=text, model=self.model, usage=usage), usage

        return await self._call(send, parse, purpose, ref_id)


class OpenAICompatEmbedder(_OpenAICompat):
    def __init__(self, client: AsyncOpenAI, *, dim: int, **kwargs: Any) -> None:
        super().__init__(client, usage_role="embed", **kwargs)
        self.dim = dim

    async def embed(
        self, texts: list[str], *, purpose: Purpose, ref_id: str | None = None
    ) -> list[list[float]]:
        def send() -> Awaitable[Any]:
            return self.client.embeddings.with_raw_response.create(
                model=self.model, input=texts, encoding_format="float"
            )

        def parse(resp: Any) -> tuple[list[list[float]], TokenUsage]:
            vectors = [list(d.embedding) for d in sorted(resp.data, key=lambda d: d.index)]
            u = resp.usage
            usage = (
                TokenUsage(prompt_tokens=u.prompt_tokens, total_tokens=u.total_tokens) if u else TokenUsage()
            )
            return vectors, usage

        return await self._call(send, parse, purpose, ref_id)
