"""Provider interfaces (SPEC-01 §4). App code sees roles and these protocols, never an SDK."""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

Role = Literal["answer", "fast", "fallback", "judge"]
UsageRole = Literal["answer", "fast", "fallback", "vision", "embed", "rerank", "judge"]
Purpose = Literal["question", "ingestion", "eval", "reembed"]
Reasoning = Literal["off", "low", "medium", "high"]
Message = dict[str, Any]


@dataclass(frozen=True, slots=True)
class Capabilities:
    supports_thinking: bool = False
    supports_image_input: bool = False
    supports_json_mode: bool = False
    has_reranker: bool = False


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0


@dataclass(slots=True)
class ChatResult:
    text: str
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)


@dataclass(slots=True)
class ChatDelta:
    """One streamed piece. The last item has `usage` set (and usually empty text)."""

    text: str
    usage: TokenUsage | None = None


@dataclass(frozen=True, slots=True)
class RerankHit:
    index: int
    score: float


class ChatModel(Protocol):
    role: str
    model: str
    capabilities: Capabilities

    async def complete(
        self,
        messages: list[Message],
        *,
        json_mode: bool = False,
        reasoning: Reasoning = "off",
        max_tokens: int | None = None,
        purpose: Purpose,
        ref_id: str | None = None,
    ) -> ChatResult: ...

    def stream(
        self,
        messages: list[Message],
        *,
        reasoning: Reasoning = "off",
        max_tokens: int | None = None,
        temperature: float | None = None,
        purpose: Purpose,
        ref_id: str | None = None,
    ) -> AsyncIterator[ChatDelta]: ...


class VisionModel(Protocol):
    model: str

    async def describe(
        self, image: bytes, mime: str, instruction: str, *, purpose: Purpose, ref_id: str | None = None
    ) -> ChatResult: ...


class Embedder(Protocol):
    model: str
    dim: int

    async def embed(
        self, texts: list[str], *, purpose: Purpose, ref_id: str | None = None
    ) -> list[list[float]]: ...


class Reranker(Protocol):
    model: str

    async def rerank(
        self, query: str, documents: list[str], top_n: int, *, purpose: Purpose, ref_id: str | None = None
    ) -> list[RerankHit]: ...
