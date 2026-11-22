"""M08: `POST /documents/{id}/file` replaces a document's file in place and re-ingests it."""

import uuid
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.db.models import Chunk, Document
from app.ingestion import extract as extraction
from app.providers.registry import Providers
from tests import uploads
from tests.spec03.test_worker import fake_extract, new_doc, run_job


async def replace(client: httpx.AsyncClient, doc_id: str, content: bytes, filename: str) -> httpx.Response:
    return await client.post(f"/api/v1/documents/{doc_id}/file", files={"file": (filename, content)})


async def test_replace_file_swaps_chunks_and_keeps_the_id(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract(chunks=2))
    doc_id = await new_doc(client, "v1", "Policy.pdf")
    await run_job(sessions, providers)
    old = set((await db.execute(select(Chunk.id).where(Chunk.document_id == uuid.UUID(doc_id)))).scalars())
    before = (await client.get(f"/api/v1/documents/{doc_id}")).json()

    monkeypatch.setattr(extraction, "extract", fake_extract(chunks=3))
    resp = await replace(client, doc_id, uploads.markdown("v2"), "Policy v2.md")
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert (body["id"], body["ingestStatus"], body["fileType"]) == (doc_id, "queued", "md")
    assert body["title"] == before["title"]

    await run_job(sessions, providers)
    doc = (await db.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    await db.refresh(doc)
    assert (doc.ingest_status, doc.filename, doc.chunk_count) == ("ready", "Policy v2.md", 3)
    new = set((await db.execute(select(Chunk.id).where(Chunk.document_id == doc.id))).scalars())
    assert len(new) == 3
    assert not new & old
    folder = Path(get_settings().storage_dir) / doc_id
    assert sorted(p.name for p in folder.iterdir()) == ["Policy v2.md"]


async def test_replace_file_rejects_same_bytes_and_pending_ingest(
    client: httpx.AsyncClient,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract())
    content = uploads.pdf("same")
    doc_id = await new_doc(client, "same", content=content)
    pending = await replace(client, doc_id, uploads.pdf("other"), "Other.pdf")
    assert pending.status_code == 409
    assert pending.json()["code"] == "ingest_in_progress"
    await run_job(sessions, providers)
    same = await replace(client, doc_id, content, "Policy.pdf")
    assert (same.status_code, same.json()["code"]) == (409, "duplicate_document")


async def test_replace_file_is_hidden_from_other_groups(
    client: httpx.AsyncClient, client_as: Callable[[str | None], httpx.AsyncClient]
) -> None:
    async with client_as("aisyah") as aisyah:
        doc_id = await new_doc(aisyah, "hidden", accessGroups=["hr"])
    resp = await replace(client, doc_id, uploads.pdf("x"), "X.pdf")
    assert (resp.status_code, resp.json()["code"]) == (404, "not_found")
