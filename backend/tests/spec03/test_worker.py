"""SPEC-03 §10 checks 3, 4, 6, 7, 8, 9, 13, 14, 16, 17: the queue, the worker and the chunk swap.

Docling is not loaded here: tests that need a prose parse replace `extract`; the XLSX path is real.
"""

import asyncio
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.config import get_settings
from app.db.models import Chunk, Document, Job
from app.ingestion import extract as extraction
from app.ingestion import jobs, service
from app.ingestion.chunking import WhitespaceCounter
from app.ingestion.types import ChunkDraft, DocMeta, IngestResult
from app.ingestion.worker import process_one_job
from app.providers.errors import ProviderError
from app.providers.registry import Providers
from app.security.identity import Identity
from tests import uploads
from tests.uploads import upload

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "serimaju"
ADMIN = Identity(id="aisyah", name="Aisyah", groups=("all", "hr"), is_admin=True)


async def run_job(
    sessions: async_sessionmaker[AsyncSession], providers: Providers, wid: str = "test-worker"
) -> bool:
    return await process_one_job(sessions, get_settings(), providers, WhitespaceCounter(), wid)


def fake_extract(
    *, superseded: bool = False, chunks: int = 2, title: str | None = None
) -> Callable[..., IngestResult]:
    def _extract(*_: Any, **__: Any) -> IngestResult:
        drafts = [
            ChunkDraft("text", f"Doc > Section {i}\n\nbody {i}", ["Doc", f"Section {i}"], 4)
            for i in range(chunks)
        ]
        return IngestResult(drafts, DocMeta(title=title, language="en", superseded=superseded))

    return _extract


async def new_doc(
    client: httpx.AsyncClient, seed: str, filename: str = "Policy.pdf", content: bytes | None = None, **f: Any
) -> str:
    resp = await upload(client, content or uploads.pdf(seed), filename, **f)
    assert resp.status_code == 202, resp.text
    return str(resp.json()["id"])


async def doc_row(db: AsyncSession, doc_id: str) -> Document:
    db.expire_all()
    return (await db.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()


async def job_row(db: AsyncSession, doc_id: str) -> Job:
    db.expire_all()
    return (
        await db.execute(select(Job).where(Job.document_id == uuid.UUID(doc_id)).order_by(Job.id.desc()))
    ).scalars().first() or pytest.fail("no job")


# --- ac03 ---


async def test_spec03_ac03_two_workers_never_claim_the_same_job(committed_db: AsyncEngine) -> None:
    maker = async_sessionmaker(committed_db, expire_on_commit=False)
    async with maker() as session:
        session.add_all(Job(kind=jobs.INGEST_DOCUMENT) for _ in range(6))
        await session.commit()

    async def claim(worker: str) -> jobs.ClaimedJob | None:
        async with maker() as session:
            return await jobs.claim(session, worker)

    claimed = await asyncio.gather(*(claim(f"w{i}") for i in range(12)))
    ids = [c.id for c in claimed if c is not None]
    assert len(ids) == 6
    assert len(set(ids)) == 6


# --- ac04, ac06: the real XLSX path ---


async def test_spec03_ac04_ac06_xlsx_becomes_ready_with_header_and_lookup_lines(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
) -> None:
    content = (FIXTURES / "Leave_Entitlement_by_Grade_2026.xlsx").read_bytes()
    doc_id = await new_doc(client, "x", "Leave_Entitlement_by_Grade_2026.xlsx", content)
    assert await run_job(sessions, providers) is True

    doc = await doc_row(db, doc_id)
    assert (doc.ingest_status, doc.doc_type, doc.language) == ("ready", "spreadsheet", "en")
    assert doc.chunk_count > 0
    chunks = (
        await db.execute(select(Chunk).where(Chunk.document_id == doc.id).order_by(Chunk.ordinal))
    ).scalars()
    rows = list(chunks)
    assert len(rows) == doc.chunk_count
    for chunk in rows:
        assert chunk.embedding is not None
        assert chunk.embedding_model == providers.embedder().model
        assert chunk.doc_status == doc.status
        assert chunk.access_groups == doc.access_groups
    table = next(c for c in rows if c.chunk_type == "table_rows" and c.sheet == "Annual Leave 2026")
    assert table.heading_path == ["Leave Entitlement by Grade 2026", "Annual Leave 2026"]
    assert "| Grade band | Grades | Less than 2 years | 2 to 5 years | More than 5 years |" in table.text
    lookup = "Grade band: Manager; Grades: M1, M2, M3; Less than 2 years: 18; 2 to 5 years: 20"
    assert f"{lookup}; More than 5 years: 22" in table.text
    assert table.text.startswith("Leave Entitlement by Grade 2026 > Annual Leave 2026\n\n")
    calculator = next(c for c in rows if c.sheet == "Entitlement Calculator")
    assert "Annual leave entitlement (days): 22" in calculator.text
    job = await job_row(db, doc_id)
    assert (job.status, job.attempts) == ("done", 1)


async def test_spec03_xlsx_ingestion_logs_embedding_usage_per_document(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
) -> None:
    from app.db.models import Usage

    content = (FIXTURES / "Leave_Entitlement_by_Grade_2026.xlsx").read_bytes()
    doc_id = await new_doc(client, "u", "Leave.xlsx", content)
    await run_job(sessions, providers)
    rows = (await db.execute(select(Usage).where(Usage.ref_id == doc_id))).scalars().all()
    assert rows
    assert {(r.role, r.purpose, r.status) for r in rows} == {
        ("embed", "ingestion", "ok"),
        ("fast", "ingestion", "ok"),
    }
    assert sum(r.prompt_tokens for r in rows) > 0


# --- ac07, ac16 ---


async def test_spec03_ac07_superseded_first_page_sets_status_on_document_and_chunks(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract(superseded=True))
    doc_id = await new_doc(client, "ac07")
    await run_job(sessions, providers)
    doc = await doc_row(db, doc_id)
    assert doc.status == "superseded"
    states = (await db.execute(select(Chunk.doc_status).where(Chunk.document_id == doc.id))).scalars().all()
    assert set(states) == {"superseded"}


async def test_spec03_ac16_manual_current_survives_a_reingest(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract(superseded=True))
    doc_id = await new_doc(client, "ac16")
    await run_job(sessions, providers)
    assert (await client.patch(f"/api/v1/documents/{doc_id}", json={"status": "current"})).status_code == 200
    assert (await client.post(f"/api/v1/documents/{doc_id}/reingest")).status_code == 202
    await run_job(sessions, providers)
    doc = await doc_row(db, doc_id)
    assert (doc.status, doc.ingest_status) == ("current", "ready")
    states = (await db.execute(select(Chunk.doc_status).where(Chunk.document_id == doc.id))).scalars().all()
    assert set(states) == {"current"}


# --- ac08 ---


def failing_embedder(providers: Providers, error: ProviderError) -> None:
    async def boom(*_: Any, **__: Any) -> list[list[float]]:
        raise error

    providers.embedder().embed = boom  # type: ignore[method-assign]


async def test_spec03_ac08_rate_limit_requeues_with_backoff(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract())
    failing_embedder(providers, ProviderError("rate_limited", retryable=True, http_status=429))
    doc_id = await new_doc(client, "ac08a")
    await run_job(sessions, providers)
    job = await job_row(db, doc_id)
    assert (job.status, job.attempts, job.error_code) == ("queued", 1, "rate_limit")
    delay = (
        await db.execute(select(func.extract("epoch", Job.run_after - func.now())).where(Job.id == job.id))
    ).scalar_one()
    assert 55 <= float(delay) <= 61  # 30 s * 2^1
    assert (await doc_row(db, doc_id)).ingest_status == "processing"
    assert await run_job(sessions, providers) is False  # not due yet


async def test_spec03_ac08_rate_limit_after_last_attempt_fails_with_rate_limit(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract())
    failing_embedder(providers, ProviderError("rate_limited", retryable=True, http_status=429))
    doc_id = await new_doc(client, "ac08b")
    await db.execute(update(Job).where(Job.document_id == uuid.UUID(doc_id)).values(attempts=2))
    await db.commit()
    await run_job(sessions, providers)
    doc = await doc_row(db, doc_id)
    assert (doc.ingest_status, doc.ingest_error_code) == ("failed", "rate_limit")
    assert (await job_row(db, doc_id)).status == "failed"


async def test_spec03_ac08_quota_fails_at_once_and_is_not_retried(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract())
    failing_embedder(providers, ProviderError("quota_exhausted", retryable=False, http_status=429))
    doc_id = await new_doc(client, "ac08c")
    await run_job(sessions, providers)
    doc = await doc_row(db, doc_id)
    assert (doc.ingest_status, doc.ingest_error_code) == ("failed", "quota")
    assert doc.ingest_error == service.QUOTA_MESSAGE
    job = await job_row(db, doc_id)
    assert (job.status, job.attempts, job.error_code) == ("failed", 1, "quota")
    assert await run_job(sessions, providers) is False


async def test_spec03_unreadable_file_fails_with_parse_and_keeps_old_chunks(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract())
    doc_id = await new_doc(client, "parse")
    await run_job(sessions, providers)
    assert (await client.post(f"/api/v1/documents/{doc_id}/reingest")).status_code == 202

    def broken(*_: Any, **__: Any) -> IngestResult:
        from app.ingestion.types import IngestError

        raise IngestError("parse", "This file could not be read.")

    monkeypatch.setattr(extraction, "extract", broken)
    await run_job(sessions, providers)
    doc = await doc_row(db, doc_id)
    assert (doc.ingest_status, doc.ingest_error_code, doc.chunk_count) == ("failed", "parse", 2)
    count = (
        await db.execute(select(func.count()).select_from(Chunk).where(Chunk.document_id == doc.id))
    ).scalar_one()
    assert count == 2


# --- ac09, ac13, ac14: the swap ---


async def test_spec03_ac09_reingest_swaps_chunks_atomically(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract(chunks=2))
    doc_id = await new_doc(client, "ac09")
    await run_job(sessions, providers)
    old = set((await db.execute(select(Chunk.id).where(Chunk.document_id == uuid.UUID(doc_id)))).scalars())
    assert len(old) == 2

    await client.post(f"/api/v1/documents/{doc_id}/reingest")
    monkeypatch.setattr(extraction, "extract", fake_extract(chunks=3))
    embedder = providers.embedder()
    original = embedder.embed
    seen: list[set[uuid.UUID]] = []

    async def spying(texts: list[str], **kw: Any) -> list[list[float]]:
        # Mid-ingestion a reader still sees the complete old set.
        seen.append(
            set((await db.execute(select(Chunk.id).where(Chunk.document_id == uuid.UUID(doc_id)))).scalars())
        )
        return await original(texts, **kw)

    embedder.embed = spying  # type: ignore[method-assign]
    await run_job(sessions, providers)
    new = set((await db.execute(select(Chunk.id).where(Chunk.document_id == uuid.UUID(doc_id)))).scalars())
    assert seen == [old]
    assert len(new) == 3
    assert not new & old


async def committed_doc(engine: AsyncEngine, groups: list[str]) -> uuid.UUID:
    """A queued document with a stored file and a job, really committed (these tests use two connections)."""
    doc_id = uuid.uuid4()
    folder = Path(get_settings().storage_dir) / str(doc_id)
    folder.mkdir(parents=True)
    (folder / "p.pdf").write_bytes(uploads.pdf(str(doc_id)))
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add(
            Document(
                id=doc_id,
                title="p",
                filename="p.pdf",
                content_type="application/pdf",
                file_type="pdf",
                size_bytes=10,
                sha256=doc_id.hex * 2,
                storage_path=f"{doc_id}/p.pdf",
                access_groups=groups,
                uploaded_by="aisyah",
            )
        )
        await session.flush()
        await jobs.enqueue(session, jobs.INGEST_DOCUMENT, doc_id)
        await session.commit()
    return doc_id


async def chunk_groups(engine: AsyncEngine, doc_id: uuid.UUID) -> list[list[str]]:
    async with engine.connect() as conn:
        rows = await conn.execute(select(Chunk.access_groups).where(Chunk.document_id == doc_id))
        return [list(r[0]) for r in rows]


async def test_spec03_ac13_patch_during_ingestion_wins_over_the_copy_taken_at_start(
    committed_db: AsyncEngine, providers: Providers, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract())
    doc_id = await committed_doc(committed_db, ["all", "hr"])
    maker = async_sessionmaker(committed_db, expire_on_commit=False)
    embedder = providers.embedder()
    original = embedder.embed

    async def patching(texts: list[str], **kw: Any) -> list[list[float]]:
        async with maker() as other:
            await service.update_document(other, ADMIN, doc_id, {"access_groups": ["hr"]})
        return await original(texts, **kw)

    embedder.embed = patching  # type: ignore[method-assign]
    await process_one_job(maker, get_settings(), providers, WhitespaceCounter(), "w")
    groups = await chunk_groups(committed_db, doc_id)
    assert groups
    assert all(g == ["hr"] for g in groups)


async def test_spec03_ac14_delete_during_ingestion_leaves_no_chunks(
    committed_db: AsyncEngine, providers: Providers, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract())
    doc_id = await committed_doc(committed_db, ["all"])
    maker = async_sessionmaker(committed_db, expire_on_commit=False)
    embedder = providers.embedder()
    original = embedder.embed

    async def deleting(texts: list[str], **kw: Any) -> list[list[float]]:
        async with maker() as other:
            await service.delete_document(other, get_settings(), ADMIN, doc_id)
        return await original(texts, **kw)

    embedder.embed = deleting  # type: ignore[method-assign]
    await process_one_job(maker, get_settings(), providers, WhitespaceCounter(), "w")
    assert await chunk_groups(committed_db, doc_id) == []
    async with maker() as session:
        job = (await session.execute(select(Job).where(Job.document_id == doc_id))).scalar_one()
    assert job.status == "done"


# --- ac17 and stale recovery ---


async def test_spec03_ac17_heartbeat_keeps_a_long_job_from_being_requeued(db: AsyncSession) -> None:
    db.add(Job(kind=jobs.INGEST_DOCUMENT))
    await db.commit()
    job = await jobs.claim(db, "w1")
    assert job is not None
    old = text("now() - interval '20 minutes'")
    await db.execute(update(Job).where(Job.id == job.id).values(locked_at=old))
    await db.commit()
    await jobs.heartbeat(db, job.id, "w1")
    assert await jobs.requeue_stale(db) == 0
    db.expire_all()
    assert (await db.get(Job, job.id)).status == "running"  # type: ignore[union-attr]


async def test_spec03_job_without_heartbeat_for_15_minutes_goes_back_to_the_queue(db: AsyncSession) -> None:
    db.add(Job(kind=jobs.INGEST_DOCUMENT))
    await db.commit()
    job = await jobs.claim(db, "w1")
    assert job is not None
    await db.execute(
        update(Job).where(Job.id == job.id).values(locked_at=text("now() - interval '16 minutes'"))
    )
    await db.commit()
    assert await jobs.requeue_stale(db) == 1
    db.expire_all()
    row = await db.get(Job, job.id)
    assert row is not None
    assert (row.status, row.locked_by) == ("queued", None)
    assert (await jobs.claim(db, "w2")) is not None  # claimable again


# --- error mapping details ---


async def test_spec03_provider_outage_requeues_with_provider_code(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract())
    failing_embedder(providers, ProviderError("provider_unavailable", retryable=True, http_status=503))
    doc_id = await new_doc(client, "outage")
    await run_job(sessions, providers)
    job = await job_row(db, doc_id)
    assert (job.status, job.error_code) == ("queued", "provider")
    assert (await doc_row(db, doc_id)).ingest_status == "processing"


async def test_spec03_failure_after_delete_finishes_the_job_without_failing(
    committed_db: AsyncEngine, providers: Providers, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§1 rule 5: a document deleted during its job is not a failure; the job ends `done`."""
    monkeypatch.setattr(extraction, "extract", fake_extract())
    doc_id = await committed_doc(committed_db, ["all"])
    maker = async_sessionmaker(committed_db, expire_on_commit=False)

    async def delete_then_fail(*_: Any, **__: Any) -> list[list[float]]:
        async with maker() as other:
            await service.delete_document(other, get_settings(), ADMIN, doc_id)
        raise ProviderError("quota_exhausted", retryable=False, http_status=429)

    providers.embedder().embed = delete_then_fail  # type: ignore[method-assign]
    await process_one_job(maker, get_settings(), providers, WhitespaceCounter(), "w")
    async with maker() as session:
        job = (await session.execute(select(Job).where(Job.document_id == doc_id))).scalar_one()
        doc = await session.get(Document, doc_id)
    assert job.status == "done"
    assert doc is not None and doc.ingest_error_code is None


# --- §9 embedding model guard ---


async def test_spec03_embedding_model_mix_fails_with_provider(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract())
    first = await new_doc(client, "mix1")
    await run_job(sessions, providers)
    await db.execute(
        update(Chunk).where(Chunk.document_id == uuid.UUID(first)).values(embedding_model="older-model")
    )
    await db.commit()

    second = await new_doc(client, "mix2")
    await run_job(sessions, providers)
    doc = await doc_row(db, second)
    assert (doc.ingest_status, doc.ingest_error_code, doc.chunk_count) == ("failed", "provider", 0)
    count = (
        await db.execute(select(func.count()).select_from(Chunk).where(Chunk.document_id == doc.id))
    ).scalar_one()
    assert count == 0
    assert (await job_row(db, second)).status == "failed"
