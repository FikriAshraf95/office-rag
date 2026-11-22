"""Deterministic fakes for AI_PROVIDER=fake (SPEC-01 §5). Every fake still writes usage rows."""

import asyncio
import hashlib
import json
import math
import re
from collections import deque
from collections.abc import AsyncIterator

from app.providers.base import (
    Capabilities,
    ChatDelta,
    ChatResult,
    Message,
    Purpose,
    Reasoning,
    RerankHit,
    TokenUsage,
    UsageRole,
)
from app.providers.errors import ProviderError
from app.providers.usage import UsageEntry, UsageRecorder

PROVIDER = "fake"
NOT_FOUND = "NOT_FOUND"
FAKE_CAPABILITIES = Capabilities(
    supports_thinking=False, supports_image_input=True, supports_json_mode=True, has_reranker=True
)

_WORD = re.compile(r"\w+", re.UNICODE)
_SOURCE_ONE = re.compile(r"^\[1\][^\n]*\n(.+?)(?=\n\n\[2\]|\n\nQuestion:|\Z)", re.DOTALL | re.MULTILINE)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s")


def words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _text_of(messages: list[Message]) -> tuple[str, str]:
    """(all text, last user text) of a message list."""
    parts: list[str] = []
    last_user = ""
    for m in messages:
        content = m.get("content")
        text = (
            content
            if isinstance(content, str)
            else " ".join(str(p.get("text", "")) for p in content or [] if isinstance(p, dict))
        )
        parts.append(text)
        if m.get("role") == "user":
            last_user = text
    return "\n".join(parts), last_user


class _FakeBase:
    def __init__(self, *, model: str, usage_role: UsageRole, recorder: UsageRecorder) -> None:
        self.model = model
        self._usage_role: UsageRole = usage_role
        self._recorder = recorder

    async def _record(
        self,
        purpose: Purpose,
        ref_id: str | None,
        usage: TokenUsage,
        status: str = "ok",
        code: str | None = None,
    ) -> None:
        await self._recorder.record(
            UsageEntry(
                provider=PROVIDER,
                model=self.model,
                role=self._usage_role,
                purpose=purpose,
                ref_id=ref_id,
                usage=usage,
                latency_ms=0,
                status=status,
                error_code=code,
            )
        )


class FakeChatModel(_FakeBase):
    def __init__(self, *, role: str, model: str, usage_role: UsageRole, recorder: UsageRecorder) -> None:
        super().__init__(model=model, usage_role=usage_role, recorder=recorder)
        self.role = role
        self.capabilities = FAKE_CAPABILITIES
        self._script: deque[str] = deque()
        self._error: ProviderError | None = None
        self._error_after = 0
        self.calls: list[list[Message]] = []
        self.hold: asyncio.Event | None = None
        self.held = asyncio.Event()  # set when a stream starts waiting on `hold`
        self.cancelled = 0

    def script(self, replies: list[str]) -> None:
        """The next calls return these replies, in order."""
        self._script.extend(replies)

    def fail_with(self, error: ProviderError | None, *, after_deltas: int = 0) -> None:
        """Every call raises `error` until cleared with None; `stream` raises after `after_deltas` deltas."""
        self._error = error
        self._error_after = after_deltas

    def _answer(self, messages: list[Message], json_mode: bool) -> str:
        if self._script:
            return self._script.popleft()
        if json_mode:
            return json.dumps({"verdict": "correct", "reason": "fake"})
        _, user = _text_of(messages)
        match = _SOURCE_ONE.search(user.split("Sources:", 1)[1]) if "Sources:" in user else None
        if match is None or not match.group(1).strip():
            return NOT_FOUND
        first = _SENTENCE_END.split(match.group(1).strip(), maxsplit=1)[0].strip()
        return f"{first} [1]"

    def _usage(self, messages: list[Message], answer: str) -> TokenUsage:
        prompt, _ = _text_of(messages)
        p, c = len(words(prompt)), len(words(answer))
        return TokenUsage(prompt_tokens=p, completion_tokens=c, total_tokens=p + c)

    async def _check_error(self, purpose: Purpose, ref_id: str | None, *, delta: int = 0) -> None:
        if self._error is not None and delta == self._error_after:
            await self._record(purpose, ref_id, TokenUsage(), "error", self._error.code)
            raise self._error

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
        self.calls.append(messages)
        await self._check_error(purpose, ref_id)
        answer = self._answer(messages, json_mode)
        usage = self._usage(messages, answer)
        await self._record(purpose, ref_id, usage)
        return ChatResult(text=answer, model=self.model, usage=usage)

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
        """Yields the answer in 3 pieces. `hold` (if set) is awaited after the first piece; an early close
        or cancellation is counted in `cancelled`."""
        self.calls.append(messages)
        await self._check_error(purpose, ref_id)
        answer = self._answer(messages, False)
        third = math.ceil(len(answer) / 3) or 1
        finished = False
        try:
            for n, i in enumerate(range(0, len(answer), third), start=1):
                yield ChatDelta(text=answer[i : i + third])
                if n == 1 and self.hold is not None:
                    self.held.set()
                    await self.hold.wait()
                await self._check_error(purpose, ref_id, delta=n)
            usage = self._usage(messages, answer)
            await self._record(purpose, ref_id, usage)
            finished = True
            yield ChatDelta(text="", usage=usage)
        except GeneratorExit, asyncio.CancelledError:
            if not finished:
                self.cancelled += 1
            raise


class FakeVisionModel(_FakeBase):
    async def describe(
        self, image: bytes, mime: str, instruction: str, *, purpose: Purpose, ref_id: str | None = None
    ) -> ChatResult:
        """Returns `[image] <filename>`; callers put the filename on the instruction's first line."""
        filename = instruction.splitlines()[0].strip() if instruction.strip() else "image"
        text = f"[image] {filename}"
        usage = TokenUsage(prompt_tokens=len(words(instruction)), completion_tokens=len(words(text)))
        usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
        await self._record(purpose, ref_id, usage)
        return ChatResult(text=text, model=self.model, usage=usage)


class FakeEmbedder(_FakeBase):
    """Bag-of-words hash into `dim` buckets, L2-normalised: same text → same vector, shared words → closer."""

    def __init__(self, *, model: str, dim: int, recorder: UsageRecorder) -> None:
        super().__init__(model=model, usage_role="embed", recorder=recorder)
        self.dim = dim

    def vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = words(text) or [""]
        for token in tokens:
            bucket = int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), "big") % self.dim
            vec[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec]

    async def embed(
        self, texts: list[str], *, purpose: Purpose, ref_id: str | None = None
    ) -> list[list[float]]:
        tokens = sum(len(words(t)) for t in texts)
        await self._record(purpose, ref_id, TokenUsage(prompt_tokens=tokens, total_tokens=tokens))
        return [self.vector(t) for t in texts]


class FakeReranker(_FakeBase):
    """Scores by word overlap with the query."""

    def __init__(self, *, model: str, recorder: UsageRecorder) -> None:
        super().__init__(model=model, usage_role="rerank", recorder=recorder)

    async def rerank(
        self, query: str, documents: list[str], top_n: int, *, purpose: Purpose, ref_id: str | None = None
    ) -> list[RerankHit]:
        q = set(words(query))
        hits = [
            RerankHit(index=i, score=len(q & set(words(d))) / len(q) if q else 0.0)
            for i, d in enumerate(documents)
        ]
        tokens = len(words(query)) + sum(len(words(d)) for d in documents)
        await self._record(purpose, ref_id, TokenUsage(prompt_tokens=tokens, total_tokens=tokens))
        return sorted(hits, key=lambda h: (-h.score, h.index))[:top_n]
