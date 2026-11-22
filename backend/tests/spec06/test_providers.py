"""SPEC-06 §8 acceptance checks, with mocked HTTP transports for the OpenAI client and rerank."""

import json
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import httpx
import httpx2
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession

from app.config import Settings
from app.db.models import Usage
from app.providers.base import TokenUsage
from app.providers.errors import ProviderError
from app.providers.pricing import cost_myr
from app.providers.registry import Providers
from app.providers.usage import UsageEntry, UsageRecorder
from tests.conftest import TEST_API_KEY
from tests.helpers import provider_leaks

Handler = Callable[[httpx2.Request], httpx2.Response]


def completion(text: str = "Hello [1]", prompt: int = 10, completion_tokens: int = 5) -> dict[str, Any]:
    return {
        "id": "c1",
        "object": "chat.completion",
        "created": 0,
        "model": "m",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens": prompt,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt + completion_tokens,
            "completion_tokens_details": {"reasoning_tokens": 2},
        },
    }


class Recorder:
    """Mocked transport that records requests and replays responses in order."""

    def __init__(self, *responses: httpx2.Response) -> None:
        self.responses = list(responses)
        self.requests: list[httpx2.Request] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        return self.responses.pop(0)

    def body(self, i: int = 0) -> dict[str, Any]:
        result: dict[str, Any] = json.loads(self.requests[i].content)
        return result


@pytest.fixture
def sleeps() -> list[float]:
    return []


@pytest.fixture
def real(connection: AsyncConnection, sleeps: list[float]) -> Callable[..., Providers]:
    """Providers for the ILMU profile over mocked transports; sleeps are recorded, not waited."""

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    def build(
        openai_handler: Handler | None = None,
        rerank_handler: Callable[[httpx.Request], httpx.Response] | None = None,
    ) -> Providers:
        settings = Settings(
            _env_file=None,
            ai_provider="ilmu",
            ai_api_key=TEST_API_KEY,
            rerank_model="bge-reranker",
            ai_max_rpm=10_000,
        )
        return Providers(
            settings,
            UsageRecorder(connection),
            transport=httpx2.MockTransport(openai_handler) if openai_handler else None,
            rerank_transport=httpx.MockTransport(rerank_handler) if rerank_handler else None,
            sleep=fake_sleep,
        )

    return build


async def usage_rows(db: AsyncSession) -> list[Usage]:
    return list((await db.execute(select(Usage).order_by(Usage.id))).scalars())


ANSWER = [{"role": "user", "content": "Hi"}]


async def test_spec06_ac01_rate_limit_retried_after_retry_after(
    real: Callable[..., Providers], sleeps: list[float], db: AsyncSession
) -> None:
    mock = Recorder(
        httpx2.Response(
            429, headers={"x-ilmu-error-code": "rate_limit.exceeded", "Retry-After": "2"}, json={}
        ),
        httpx2.Response(200, json=completion()),
    )
    result = await real(mock).chat("answer").complete(ANSWER, purpose="question")
    assert result.text == "Hello [1]"
    assert len(mock.requests) == 2
    assert sleeps and sleeps[0] >= 2
    assert [(r.status, r.error_code) for r in await usage_rows(db)] == [
        ("error", "rate_limited"),
        ("ok", None),
    ]


async def test_spec06_ac02_token_quota_exhausted_not_retried(
    real: Callable[..., Providers], sleeps: list[float]
) -> None:
    mock = Recorder(
        httpx2.Response(429, headers={"x-ilmu-error-code": "billing.token_quota_exhausted"}, json={})
    )
    with pytest.raises(ProviderError) as info:
        await real(mock).chat("answer").complete(ANSWER, purpose="question")
    assert info.value.code == "quota_exhausted"
    assert len(mock.requests) == 1
    assert sleeps == []


async def test_spec06_ac03_payment_required_is_quota_exhausted_not_retried(
    real: Callable[..., Providers], sleeps: list[float]
) -> None:
    mock = Recorder(httpx2.Response(402, json={"error": {"code": "billing.no_allocation"}}))
    with pytest.raises(ProviderError) as info:
        await real(mock).embedder().embed(["x"], purpose="ingestion")
    assert info.value.code == "quota_exhausted"
    assert len(mock.requests) == 1
    assert sleeps == []


async def test_spec06_ac04_every_call_writes_a_usage_row(
    real: Callable[..., Providers], db: AsyncSession
) -> None:
    embedding = {
        "object": "list",
        "model": "bge-m3",
        "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
        "usage": {"prompt_tokens": 3, "total_tokens": 3},
    }
    mock = Recorder(
        httpx2.Response(200, json=completion(prompt=10, completion_tokens=5)),
        httpx2.Response(200, json=embedding),
        httpx2.Response(200, json=completion("[image] memo")),
        httpx2.Response(401, json={"error": {"code": "invalid_api_key"}}),
    )
    rerank = httpx.Response(
        200, json={"results": [{"index": 0, "relevance_score": 0.9}], "usage": {"prompt_tokens": 7}}
    )
    providers = real(mock, lambda _req: rerank)

    await providers.chat("answer").complete(ANSWER, purpose="question", ref_id="q1")
    await providers.embedder().embed(["x"], purpose="ingestion", ref_id="d1")
    await providers.vision().describe(b"png", "image/png", "memo.png", purpose="ingestion")
    reranker = providers.reranker()
    assert reranker is not None
    await reranker.rerank("q", ["a"], 1, purpose="question")
    with pytest.raises(ProviderError):
        await providers.chat("judge").complete(ANSWER, purpose="eval")

    rows = [
        (r.role, r.purpose, r.ref_id, r.prompt_tokens, r.completion_tokens, r.status)
        for r in await usage_rows(db)
    ]
    assert rows == [
        ("answer", "question", "q1", 10, 5, "ok"),
        ("embed", "ingestion", "d1", 3, 0, "ok"),
        ("vision", "ingestion", None, 10, 5, "ok"),
        ("rerank", "question", None, 7, 0, "ok"),
        ("judge", "eval", None, 0, 0, "error"),
    ]
    first = (await usage_rows(db))[0]
    assert first.reasoning_tokens == 2 and first.total_tokens == 15
    assert first.provider == "ilmu" and first.latency_ms >= 0


async def test_spec06_ac04_fakes_write_usage_rows(providers: Providers, db: AsyncSession) -> None:
    await providers.chat("answer").complete([{"role": "user", "content": "two words"}], purpose="question")
    await providers.embedder().embed(["three little words"], purpose="ingestion")
    rows = await usage_rows(db)
    assert [(r.provider, r.role, r.status) for r in rows] == [
        ("fake", "answer", "ok"),
        ("fake", "embed", "ok"),
    ]
    assert rows[1].prompt_tokens == 3


async def test_spec06_ac05_cost_for_payg_models_null_for_plan_models(
    real: Callable[..., Providers], db: AsyncSession
) -> None:
    mock = Recorder(
        httpx2.Response(200, json=completion(prompt=1000, completion_tokens=2000)),
        httpx2.Response(200, json=completion(prompt=1000, completion_tokens=2000)),
    )
    providers = real(mock)
    await providers.chat("fallback").complete(ANSWER, purpose="question")  # ilmu-glm-5.3-flash, PAYG
    await providers.chat("answer").complete(ANSWER, purpose="question")  # nemo-super, plan quota
    fallback, answer = await usage_rows(db)
    assert fallback.cost_myr == Decimal("0.004250")  # (0.55 x 1000 + 1.85 x 2000) / 1M
    assert answer.cost_myr is None
    assert cost_myr("ilmu", "bge-m3", 1_000_000, 0) == Decimal("0.040000")


def _sse(*events: dict[str, Any]) -> bytes:
    return b"".join(f"data: {json.dumps(e)}\n\n".encode() for e in events) + b"data: [DONE]\n\n"


def _chunk(content: str | None, usage: dict[str, int] | None = None) -> dict[str, Any]:
    choices = [] if content is None else [{"index": 0, "delta": {"content": content}, "finish_reason": None}]
    return {
        "id": "s",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": "m",
        "choices": choices,
        "usage": usage,
    }


async def test_spec06_ac06_streaming_collects_usage_from_final_chunk(
    real: Callable[..., Providers], db: AsyncSession
) -> None:
    body = _sse(
        _chunk("Annual leave "),
        _chunk("is 14 days [1]"),
        _chunk(None, {"prompt_tokens": 40, "completion_tokens": 6, "total_tokens": 46}),
    )
    mock = Recorder(httpx2.Response(200, content=body, headers={"content-type": "text/event-stream"}))
    deltas = [d async for d in real(mock).chat("answer").stream(ANSWER, purpose="question")]

    assert "".join(d.text for d in deltas) == "Annual leave is 14 days [1]"
    final = deltas[-1].usage
    assert final is not None and (final.prompt_tokens, final.completion_tokens) == (40, 6)
    assert mock.body()["stream_options"] == {"include_usage": True}
    (row,) = await usage_rows(db)
    assert (row.prompt_tokens, row.completion_tokens, row.status) == (40, 6, "ok")


def test_spec06_ac07_no_model_name_or_sdk_import_outside_providers() -> None:
    assert provider_leaks() == []


async def test_spec06_ac08_reasoning_effort_none_for_answers_on_thinking_models(
    real: Callable[..., Providers],
) -> None:
    mock = Recorder(*(httpx2.Response(200, json=completion()) for _ in range(2)))
    providers = real(mock)
    await providers.chat("answer").complete(ANSWER, purpose="question")  # nemo-super
    await providers.chat("fallback").complete(ANSWER, purpose="question")  # thinking can't be disabled
    assert mock.body(0)["reasoning_effort"] == "none"
    assert mock.body(1)["reasoning_effort"] == "low"


async def test_spec06_ac04_usage_is_written_when_bound_to_an_engine(committed_db: AsyncEngine) -> None:
    """Production binds the recorder to the engine (tests bind it to a connection); the row must land."""
    recorder = UsageRecorder(committed_db)
    await recorder.record(
        UsageEntry("fake", "m", "embed", "ingestion", "ref-1", TokenUsage(prompt_tokens=7), 5, "ok")
    )
    async with committed_db.connect() as conn:
        rows = (await conn.execute(select(Usage.ref_id, Usage.prompt_tokens))).all()
    assert [tuple(r) for r in rows] == [("ref-1", 7)]
