"""Builds provider instances from Settings once; app code asks for a role (SPEC-01 §4)."""

import asyncio
from typing import Literal

import httpx
import httpx2

from app.config import Settings, get_settings
from app.db.engine import get_engine
from app.providers.base import ChatModel, Embedder, Reranker, Role, VisionModel
from app.providers.fakes import FakeChatModel, FakeEmbedder, FakeReranker, FakeVisionModel
from app.providers.openai_compat import (
    OpenAICompatChat,
    OpenAICompatEmbedder,
    OpenAICompatVision,
    make_client,
)
from app.providers.rerank_http import HttpReranker, make_http_client
from app.providers.retry import Sleep, Throttle
from app.providers.usage import UsageRecorder


class Providers:
    def __init__(
        self,
        settings: Settings,
        recorder: UsageRecorder,
        *,
        transport: httpx2.AsyncBaseTransport | None = None,
        rerank_transport: httpx.AsyncBaseTransport | None = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        """`transport` (OpenAI SDK, httpx2), `rerank_transport` (httpx) and `sleep` are for tests."""
        self.settings = settings
        self.recorder = recorder
        self.fake = settings.ai_provider == "fake"
        self._sleep = sleep
        self._throttle = Throttle(settings.ai_max_rpm, sleep=sleep)
        self._chat: dict[str, ChatModel] = {}
        self._vision: VisionModel | None = None
        self._embedder: Embedder | None = None
        self._reranker: Reranker | None = None
        key = settings.ai_api_key.get_secret_value()
        self._http = httpx2.AsyncClient(transport=transport) if transport is not None else None
        self._client = make_client(
            settings.ai_base_url, key, provider=settings.ai_provider, http_client=self._http
        )
        self._rerank_http = make_http_client(settings.ai_base_url, key, transport=rerank_transport)

    def chat(self, role: Role) -> ChatModel:
        if role not in self._chat:
            s = self.settings
            model = {
                "answer": s.llm_answer_model,
                "fast": s.llm_fast_model,
                "fallback": s.llm_fallback_model,
                "judge": s.llm_judge_model,
            }[role]
            if self.fake:
                self._chat[role] = FakeChatModel(
                    role=role, model=model, usage_role=role, recorder=self.recorder
                )
            else:
                self._chat[role] = OpenAICompatChat(
                    self._client,
                    role=role,
                    usage_role=role,
                    provider=s.ai_provider,
                    model=model,
                    recorder=self.recorder,
                    throttle=self._throttle,
                    sleep=self._sleep,
                )
        return self._chat[role]

    def vision(self) -> VisionModel:
        if self._vision is None:
            model = self.settings.llm_vision_model
            usage_role: Literal["vision"] = "vision"
            self._vision = (
                FakeVisionModel(model=model, usage_role=usage_role, recorder=self.recorder)
                if self.fake
                else OpenAICompatVision(
                    self._client,
                    provider=self.settings.ai_provider,
                    model=model,
                    usage_role=usage_role,
                    recorder=self.recorder,
                    throttle=self._throttle,
                    sleep=self._sleep,
                )
            )
        return self._vision

    def embedder(self) -> Embedder:
        if self._embedder is None:
            s = self.settings
            self._embedder = (
                FakeEmbedder(model=s.embed_model, dim=s.embed_dim, recorder=self.recorder)
                if self.fake
                else OpenAICompatEmbedder(
                    self._client,
                    dim=s.embed_dim,
                    provider=s.ai_provider,
                    model=s.embed_model,
                    recorder=self.recorder,
                    throttle=self._throttle,
                    sleep=self._sleep,
                )
            )
        return self._embedder

    def reranker(self) -> Reranker | None:
        """None when RERANK_MODEL is empty."""
        model = self.settings.rerank_model
        if not model:
            return None
        if self._reranker is None:
            self._reranker = (
                FakeReranker(model=model, recorder=self.recorder)
                if self.fake
                else HttpReranker(
                    self._rerank_http,
                    provider=self.settings.ai_provider,
                    model=model,
                    recorder=self.recorder,
                    throttle=self._throttle,
                    sleep=self._sleep,
                )
            )
        return self._reranker


_providers: Providers | None = None


def get_providers() -> Providers:
    global _providers
    if _providers is None:
        _providers = Providers(get_settings(), UsageRecorder(get_engine()))
    return _providers


def set_providers(providers: Providers | None) -> None:
    """Tests install providers bound to the test connection; None resets."""
    global _providers
    _providers = providers
