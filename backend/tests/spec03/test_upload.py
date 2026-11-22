"""SPEC-03 §10 checks 1, 2, 10 and 11 (the parts M01 can reach: no worker yet)."""

import uuid
from collections.abc import Callable
from pathlib import Path

import httpx
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Chunk, Document, Job
from tests import uploads
from tests.uploads import upload


async def _add_chunks(db: AsyncSession, doc_id: str, count: int = 2) -> None:
    doc = (await db.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    for i in range(count):
        db.add(
            Chunk(
                document_id=doc.id,
                ordinal=i,
                chunk_type="section",
                text=f"chunk {i}",
                token_count=2,
                doc_status=doc.status,
                access_groups=list(doc.access_groups),
            )
        )
    await db.commit()


async def _chunk_state(db: AsyncSession) -> set[tuple[str, tuple[str, ...]]]:
    db.expire_all()
    rows = (await db.execute(select(Chunk.doc_status, Chunk.access_groups))).all()
    return {(status, tuple(groups)) for status, groups in rows}


async def test_spec03_ac01_valid_pdf_is_202_queued_with_job_and_file(
    client: httpx.AsyncClient, db: AsyncSession
) -> None:
    resp = await upload(
        client, uploads.pdf("ac01"), "Handbook 2026.pdf", title="HR Handbook", docType="handbook"
    )
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["ingestStatus"] == "queued"
    assert body["title"] == "HR Handbook"
    assert body["docType"] == "handbook"
    assert body["fileType"] == "pdf"
    assert body["contentType"] == "application/pdf"
    assert body["accessGroups"] == ["all"]
    assert body["uploadedBy"] == "ben"
    stored = Path(get_settings().storage_dir) / body["id"] / "Handbook 2026.pdf"
    assert stored.read_bytes() == uploads.pdf("ac01")
    jobs = (await db.execute(select(Job).where(Job.document_id == uuid.UUID(body["id"])))).scalars().all()
    assert [(j.kind, j.status) for j in jobs] == [("ingest_document", "queued")]
    assert not list((Path(get_settings().storage_dir) / ".tmp").glob("*"))


async def test_spec03_ac01_title_defaults_to_filename_and_metadata_is_saved(
    client: httpx.AsyncClient,
) -> None:
    resp = await upload(
        client,
        uploads.markdown("meta"),
        "Travel_and_Claims_SOP.md",
        department="Finance",
        effectiveDate="2026-01-15",
        accessGroups=["all"],
    )
    body = resp.json()
    assert resp.status_code == 202, resp.text
    assert body["title"] == "Travel and Claims SOP"
    assert body["department"] == "Finance"
    assert body["effectiveDate"] == "2026-01-15"
    assert body["docType"] == "other"


async def test_spec03_ac02_same_bytes_again_is_409_with_existing_id(client: httpx.AsyncClient) -> None:
    first = (await upload(client, uploads.pdf("ac02"), "one.pdf", title="First copy")).json()
    again = await upload(client, uploads.pdf("ac02"), "two.pdf")
    assert again.status_code == 409
    body = again.json()
    assert body["code"] == "duplicate_document"
    assert body["existingId"] == first["id"]
    assert "First copy" in body["detail"]
    assert not [p for p in uploads.stored_files() if p.name == "two.pdf"]


async def test_spec03_ac10_patch_status_and_groups_update_every_chunk(
    client_as: Callable[[str | None], httpx.AsyncClient], db: AsyncSession
) -> None:
    async with client_as("aisyah") as aisyah:
        doc = (await upload(aisyah, uploads.pdf("ac10"), "p.pdf", accessGroups=["all", "hr"])).json()
        await _add_chunks(db, doc["id"])

        resp = await aisyah.patch(f"/api/v1/documents/{doc['id']}", json={"status": "superseded"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "superseded"
        assert await _chunk_state(db) == {("superseded", ("all", "hr"))}

        resp = await aisyah.patch(
            f"/api/v1/documents/{doc['id']}", json={"accessGroups": ["hr"], "status": "current"}
        )
        assert resp.json()["accessGroups"] == ["hr"]
        assert await _chunk_state(db) == {("current", ("hr",))}


async def test_spec03_ac10_patch_edits_metadata_and_can_clear_nullable_fields(
    client: httpx.AsyncClient,
) -> None:
    doc = (await upload(client, uploads.pdf("meta2"), "m.pdf", department="HR")).json()
    url = f"/api/v1/documents/{doc['id']}"
    body = (await client.patch(url, json={"title": "New title", "version": "v2", "department": None})).json()
    assert (body["title"], body["version"], body["department"]) == ("New title", "v2", None)
    assert (await client.patch(url, json={"title": None})).status_code == 422
    assert (await client.patch(url, json={"docType": "nonsense"})).status_code == 422
    assert (await client.patch(url, json={"accessGroups": []})).status_code == 422


async def test_spec03_ac11_delete_removes_chunks_file_and_listing(
    client: httpx.AsyncClient, db: AsyncSession
) -> None:
    doc = (await upload(client, uploads.pdf("ac11"), "gone.pdf")).json()
    await _add_chunks(db, doc["id"])
    folder = Path(get_settings().storage_dir) / doc["id"]
    assert folder.exists()

    assert (await client.delete(f"/api/v1/documents/{doc['id']}")).status_code == 204

    assert not folder.exists()
    assert (await db.execute(select(func.count()).select_from(Chunk))).scalar_one() == 0
    jobs_left = select(func.count()).select_from(Job).where(Job.document_id == uuid.UUID(doc["id"]))
    assert (await db.execute(jobs_left)).scalar_one() == 0
    assert doc["id"] not in [d["id"] for d in (await client.get("/api/v1/documents")).json()["items"]]
    assert (await client.get(f"/api/v1/documents/{doc['id']}")).status_code == 404
    # The same bytes can be uploaded again once the first copy is deleted.
    assert (await upload(client, uploads.pdf("ac11"), "gone.pdf")).status_code == 202


async def test_list_filters_and_order(client: httpx.AsyncClient, db: AsyncSession) -> None:
    a = (await upload(client, uploads.pdf("l1"), "a.pdf")).json()
    b = (await upload(client, uploads.pdf("l2"), "b.pdf")).json()
    # Both rows share the test transaction's now(); make `a` older so the order does not depend on the id.
    await db.execute(
        update(Document)
        .where(Document.id == uuid.UUID(a["id"]))
        .values(created_at=text("now() - interval '1 hour'"))
    )
    await db.commit()
    await client.patch(f"/api/v1/documents/{a['id']}", json={"status": "superseded"})
    items = (await client.get("/api/v1/documents")).json()["items"]
    assert [d["id"] for d in items] == [b["id"], a["id"]]
    current = (await client.get("/api/v1/documents?status=current")).json()["items"]
    assert [d["id"] for d in current] == [b["id"]]
    assert (await client.get("/api/v1/documents?ingestStatus=failed")).json()["items"] == []
    assert (await client.get("/api/v1/documents?status=bogus")).status_code == 422
