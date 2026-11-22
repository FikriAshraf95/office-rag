"""Invariant: a superseded document never appears in search (SPEC-04 §8 check 2, SPEC-03 §6.1)."""

from collections.abc import Callable

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.providers.registry import Providers
from tests.spec04.test_retrieval import Corpus


async def test_superseded_document_never_appears_in_search(
    client: httpx.AsyncClient,
    client_as: Callable[[str | None], httpx.AsyncClient],
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "min_vector_sim", 0.0)  # fake vectors are far apart
    corpus = Corpus(client, client_as, sessions, providers, monkeypatch)
    text = ["maximum consecutive leave days", "annual leave application HR-F07"]
    old = await corpus.add("Handbook 2024", text)
    new = await corpus.add("Handbook 2026", text)
    await client.patch(f"/api/v1/documents/{old}", json={"status": "superseded"})
    for query in ["maximum consecutive leave days", "HR-F07", "Handbook 2024", "annual leave"]:
        resp = await client.post("/api/v1/search", json={"query": query, "topK": 20})
        found = {h["documentId"] for h in resp.json()["hits"]}
        assert old not in found, query
        assert new in found, query
        assert "Handbook 2024" not in resp.text, query
