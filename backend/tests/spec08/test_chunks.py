"""SPEC-08 §4.6-4.7: re-ingest and chunks."""

from collections.abc import Callable
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.ingestion import extract as extraction
from app.ingestion.chunking import WhitespaceCounter
from app.ingestion.types import ChunkDraft, DocMeta, IngestResult
from app.ingestion.worker import process_one_job
from app.providers.registry import Providers
from tests import uploads
from tests.spec08.test_api_contract import assert_problem
from tests.uploads import upload

CHUNK_KEYS = {
    "id",
    "ordinal",
    "chunkType",
    "text",
    "headingPath",
    "section",
    "pageStart",
    "pageEnd",
    "sheet",
    "tokenCount",
}


def five_chunks(*_: Any, **__: Any) -> IngestResult:
    drafts = [
        ChunkDraft("text", f"Doc > S{i}\n\nbody {i}", ["Doc", f"S{i}"], 5, section=str(i), page_start=1)
        for i in range(5)
    ]
    return IngestResult(drafts, DocMeta(language="en"))


async def ingest(
    client: httpx.AsyncClient,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
    seed: str,
) -> str:
    monkeypatch.setattr(extraction, "extract", five_chunks)
    doc_id = str((await upload(client, uploads.pdf(seed), "d.pdf")).json()["id"])
    await process_one_job(sessions, get_settings(), providers, WhitespaceCounter(), "w")
    return doc_id


async def test_spec08_chunks_page_and_around(
    client: httpx.AsyncClient,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doc_id = await ingest(client, sessions, providers, monkeypatch, "pg")
    page = (await client.get(f"/api/v1/documents/{doc_id}/chunks?offset=1&limit=2")).json()
    assert page["total"] == 5
    assert [c["ordinal"] for c in page["items"]] == [1, 2]
    assert set(page["items"][0]) == CHUNK_KEYS
    assert page["items"][0]["headingPath"] == ["Doc", "S1"]
    centre = page["items"][1]["id"]
    near = (await client.get(f"/api/v1/documents/{doc_id}/chunks?around={centre}&radius=1")).json()
    assert [c["ordinal"] for c in near["items"]] == [1, 2, 3]


async def test_spec08_chunks_around_a_foreign_chunk_is_404(
    client: httpx.AsyncClient,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one = await ingest(client, sessions, providers, monkeypatch, "f1")
    other = await ingest(client, sessions, providers, monkeypatch, "f2")
    foreign = (await client.get(f"/api/v1/documents/{other}/chunks?limit=1")).json()["items"][0]["id"]
    assert_problem(await client.get(f"/api/v1/documents/{one}/chunks?around={foreign}"), 404, "not_found")


async def test_spec08_reingest_is_202_then_409_while_pending(
    client: httpx.AsyncClient,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doc_id = await ingest(client, sessions, providers, monkeypatch, "re")
    first = await client.post(f"/api/v1/documents/{doc_id}/reingest")
    assert first.status_code == 202
    assert first.json()["ingestStatus"] == "queued"
    assert_problem(await client.post(f"/api/v1/documents/{doc_id}/reingest"), 409, "ingest_in_progress")


async def test_spec08_reingest_of_a_hidden_document_is_404(
    client: httpx.AsyncClient, client_as: Callable[[str | None], httpx.AsyncClient]
) -> None:
    async with client_as("aisyah") as aisyah:
        doc_id = (await upload(aisyah, uploads.pdf("hid"), "h.pdf", accessGroups=["hr"])).json()["id"]
    assert_problem(await client.post(f"/api/v1/documents/{doc_id}/reingest"), 404, "not_found")
    assert_problem(await client.get(f"/api/v1/documents/{doc_id}/chunks"), 404, "not_found")
