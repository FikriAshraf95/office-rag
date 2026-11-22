"""SPEC-08 §5: POST /api/v1/search."""

from collections.abc import Callable

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.providers.registry import Providers
from tests.spec04.test_retrieval import Corpus
from tests.spec08.test_api_contract import assert_problem

HIT_KEYS = {
    "chunkId",
    "documentId",
    "title",
    "fileType",
    "headingPath",
    "section",
    "pageStart",
    "pageEnd",
    "sheet",
    "effectiveDate",
    "score",
    "vecRank",
    "ftsRank",
    "vecSim",
    "rerankScore",
    "snippet",
}


async def test_spec08_search_returns_the_documented_hit_shape(
    client: httpx.AsyncClient,
    client_as: Callable[[str | None], httpx.AsyncClient],
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "min_vector_sim", 0.0)  # fake vectors are far apart
    corpus = Corpus(client, client_as, sessions, providers, monkeypatch)
    doc_id = await corpus.add("Leave", ["annual   leave\n" + "word " * 100])
    resp = await client.post("/api/v1/search", json={"query": "annual leave", "topK": 3})
    assert resp.status_code == 200, resp.text
    hits = resp.json()["hits"]
    assert len(hits) == 1
    assert set(hits[0]) == HIT_KEYS
    assert hits[0]["documentId"] == doc_id
    assert hits[0]["rerankScore"] is None
    assert hits[0]["headingPath"] == ["Leave"]
    assert hits[0]["snippet"].startswith("annual leave word")
    assert len(hits[0]["snippet"]) == 300


@pytest.mark.parametrize("top_k", [0, 21])
async def test_spec08_search_top_k_out_of_range_is_422(client: httpx.AsyncClient, top_k: int) -> None:
    body = assert_problem(
        await client.post("/api/v1/search", json={"query": "leave", "topK": top_k}), 422, "validation_failed"
    )
    assert "topK" in body["errors"]


async def test_spec08_search_query_limits(client: httpx.AsyncClient) -> None:
    assert_problem(await client.post("/api/v1/search", json={"query": "x" * 1001}), 422, "query_too_long")
    body = assert_problem(
        await client.post("/api/v1/search", json={"query": "   "}), 422, "validation_failed"
    )
    assert "query" in body["errors"]
    assert (await client.post("/api/v1/search", json={"query": "x" * 1000})).status_code == 200


async def test_spec08_search_needs_a_user(client_as: Callable[[str | None], httpx.AsyncClient]) -> None:
    async with client_as(None) as anonymous:
        assert_problem(await anonymous.post("/api/v1/search", json={"query": "leave"}), 401, "unknown_user")
