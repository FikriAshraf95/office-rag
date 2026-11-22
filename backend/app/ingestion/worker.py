"""Worker process: `python -m app.ingestion.worker` (SPEC-01 §3, SPEC-03 §3).

Claims jobs with SKIP LOCKED, parses and chunks in a thread, embeds in batches, swaps the chunks in one
transaction. A heartbeat keeps a slow Docling run from looking dead; stale locks are recovered every minute.
"""

import asyncio
import contextlib
import os
import socket
import uuid
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings, check_startup, get_settings
from app.db.engine import get_engine, get_sessionmaker
from app.ingestion import extract as extraction
from app.ingestion import jobs, metadata, service, vision
from app.ingestion.chunking import HfCounter, TokenCounter, hf_counter
from app.ingestion.extract import EMPTY_MESSAGE
from app.ingestion.types import ChunkDraft, IngestError, IngestResult
from app.log import configure_logging
from app.providers.errors import ProviderError, user_message
from app.providers.registry import Providers, get_providers
from app.security.uploads import resolve_stored

log = structlog.get_logger()

IDLE_POLL_S = 5.0
HEARTBEAT_S = 60.0
STALE_CHECK_S = 60.0
UNKNOWN_MESSAGE = (
    "Something went wrong while processing this file. Select Retry, or ask an admin to check the logs."
)
EMBED_MIX_MESSAGE = (
    "This document would be embedded with a different model than the existing chunks. "
    "Run the re-embed command first."
)
TOO_LARGE_MESSAGE = "This file is too large for the AI service to process. Split it into smaller files."


def worker_id() -> str:
    return f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:6]}"


async def _heartbeat_loop(
    sessions: async_sessionmaker[AsyncSession], job_id: int, wid: str, interval: float
) -> None:
    while True:
        await asyncio.sleep(interval)
        try:
            async with sessions() as session:
                await jobs.heartbeat(session, job_id, wid)
        except Exception as exc:
            log.warning("heartbeat_failed", job_id=job_id, error_type=type(exc).__name__)


async def _embed(providers: Providers, settings: Settings, result: IngestResult, doc_id: uuid.UUID) -> str:
    """Embed every chunk in batches of EMBED_BATCH, one batch at a time. Returns the model name."""
    embedder = providers.embedder()
    chunks: list[ChunkDraft] = result.chunks
    for start in range(0, len(chunks), settings.embed_batch):
        batch = chunks[start : start + settings.embed_batch]
        vectors = await embedder.embed([c.text for c in batch], purpose="ingestion", ref_id=str(doc_id))
        for chunk, vector in zip(batch, vectors, strict=True):
            chunk.embedding = vector
    return str(embedder.model)


async def _ingest(
    session: AsyncSession,
    job: jobs.ClaimedJob,
    settings: Settings,
    providers: Providers,
    counter: TokenCounter,
) -> None:
    assert job.document_id is not None
    doc = await service.begin_ingest(session, job.document_id)
    if doc is None:  # deleted while queued: nothing to do (SPEC-03 §7)
        await jobs.mark_done(session, job.id)
        await session.commit()
        return
    path = resolve_stored(settings.storage_dir, doc.storage_path)
    if path is None or not path.is_file():
        raise IngestError("parse", "The stored file is missing. Upload the document again.")
    info = extraction.DocInfo(title=doc.title, filename=doc.filename, file_type=doc.file_type)
    result = await asyncio.to_thread(extraction.extract, Path(path), info, settings, counter)
    title = metadata.resolve_title(doc.title, doc.filename, result.meta.title)
    await vision.apply_vision(
        result,
        Path(path),
        title=title,
        filename=doc.filename,
        file_type=doc.file_type,
        providers=providers,
        counter=counter,
        doc_id=str(doc.id),
    )
    if not result.chunks:
        raise IngestError("empty", EMPTY_MESSAGE)
    await vision.apply_summary(result, title=title, providers=providers, doc_id=str(doc.id))
    model = providers.embedder().model
    if await service.foreign_embedding_model(session, doc.id, str(model)) is not None:
        raise IngestError("provider", EMBED_MIX_MESSAGE)
    await _embed(providers, settings, result, doc.id)
    count = await service.swap_chunks(session, job.id, doc.id, result, str(model))
    log.info("ingest_done", job_id=job.id, document_id=str(doc.id), chunks=count)


async def process_one_job(
    sessions: async_sessionmaker[AsyncSession],
    settings: Settings,
    providers: Providers,
    counter: TokenCounter,
    wid: str,
    *,
    heartbeat_s: float = HEARTBEAT_S,
) -> bool:
    """Claim and run one job. Returns False when there was nothing to claim."""
    async with sessions() as session:
        job = await jobs.claim(session, wid)
    if job is None:
        return False
    beat = asyncio.create_task(_heartbeat_loop(sessions, job.id, wid, heartbeat_s))
    try:
        async with sessions() as session:
            try:
                if job.kind != jobs.INGEST_DOCUMENT or job.document_id is None:
                    raise IngestError("unknown", UNKNOWN_MESSAGE)
                await _ingest(session, job, settings, providers, counter)
            except Exception as exc:
                await session.rollback()
                await _handle_failure(session, job, exc)
    finally:
        beat.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await beat
    return True


async def _handle_failure(session: AsyncSession, job: jobs.ClaimedJob, exc: Exception) -> None:
    """SPEC-03 §3: quota never retries; retryable errors back off; everything else fails with a code."""
    doc_id = job.document_id
    if isinstance(exc, ProviderError):
        if exc.code == "quota_exhausted":
            await service.fail_ingest(session, job.id, doc_id, "quota", service.QUOTA_MESSAGE)
        elif exc.code == "request_too_large":
            await service.fail_ingest(session, job.id, doc_id, "parse", TOO_LARGE_MESSAGE)
        else:
            code = "rate_limit" if exc.code == "rate_limited" else "provider"
            message = user_message(exc.code, exc.http_status)
            if exc.retryable and job.can_retry:
                await service.retry_ingest(session, job, code, message)
            else:
                await service.fail_ingest(session, job.id, doc_id, code, message)
    elif isinstance(exc, IngestError):
        await service.fail_ingest(session, job.id, doc_id, exc.code, exc.message)
    else:
        log.exception("ingest_unexpected", job_id=job.id, error_type=type(exc).__name__)
        await service.fail_ingest(session, job.id, doc_id, "unknown", UNKNOWN_MESSAGE)


async def _stale_loop(sessions: async_sessionmaker[AsyncSession], stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            async with sessions() as session:
                if n := await jobs.requeue_stale(session):
                    log.warning("stale_jobs_requeued", count=n)
        except Exception as exc:
            log.warning("stale_check_failed", error_type=type(exc).__name__)
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=STALE_CHECK_S)


async def _loop(
    sessions: async_sessionmaker[AsyncSession],
    settings: Settings,
    providers: Providers,
    counter: TokenCounter,
    wid: str,
    wake: asyncio.Event,
    stop: asyncio.Event,
) -> None:
    while not stop.is_set():
        try:
            if await process_one_job(sessions, settings, providers, counter, wid):
                continue
        except Exception as exc:
            # A database hiccup must not end the worker; a job left `running` is recovered as stale.
            log.error("worker_step_failed", error_type=type(exc).__name__)
        wake.clear()
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(wake.wait(), timeout=IDLE_POLL_S)


async def run(stop: asyncio.Event) -> None:
    settings = get_settings()
    check_startup(settings)
    counter: HfCounter = hf_counter(settings)
    sessions = get_sessionmaker()
    providers = get_providers()
    wake = asyncio.Event()
    wid = worker_id()

    def on_notify(*_: Any) -> None:
        wake.set()

    # LISTEN needs its own long-lived connection; the poll above covers a missed notification.
    listener = await get_engine().connect()
    raw = await listener.get_raw_connection()
    await raw.driver_connection.add_listener("jobs_new", on_notify)  # type: ignore[union-attr]
    log.info(
        "worker_started",
        worker_id=wid,
        ai_provider=settings.ai_provider,
        concurrency=settings.worker_concurrency,
    )
    try:
        if not stop.is_set():
            await asyncio.to_thread(counter.warm)  # fail at startup, not on the first job
        async with asyncio.TaskGroup() as group:
            group.create_task(_stale_loop(sessions, stop))
            for n in range(settings.worker_concurrency):
                group.create_task(_loop(sessions, settings, providers, counter, f"{wid}-{n}", wake, stop))
    finally:
        await listener.close()
    log.info("worker_stopped")


def main() -> None:
    configure_logging()
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run(asyncio.Event()))


if __name__ == "__main__":
    main()
