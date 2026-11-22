"""The only writer of `documents` and `chunks` (SPEC-03 §1). Each write is one transaction, committed here."""

import shutil
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.config import Settings
from app.db.models import Chunk, Document, Job
from app.ingestion import jobs, metadata
from app.ingestion.types import IngestResult
from app.security.identity import Identity
from app.security.uploads import StagedUpload, resolve_stored

log = structlog.get_logger()

# PATCH fields that may be set to null; the others must keep a value.
NULLABLE_FIELDS = {"department", "effective_date", "version"}


@dataclass(frozen=True, slots=True)
class UploadMeta:
    title: str | None = None
    doc_type: str | None = None
    department: str | None = None
    effective_date: date | None = None
    access_groups: Sequence[str] = ("all",)


def _visible(user: Identity) -> Any:
    """The filter every document read and write uses: live and overlapping the caller's groups."""
    return (Document.deleted_at.is_(None)) & Document.access_groups.overlap(list(user.groups))


def _not_found() -> ApiError:
    return ApiError(404, "not_found", "This document does not exist, or you do not have access to it.")


def _default_title(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").strip() or filename


def _store_dir(settings: Settings, doc_id: uuid.UUID) -> Path:
    return Path(settings.storage_dir) / str(doc_id)


async def _duplicate_error(session: AsyncSession, sha256: str, user: Identity) -> ApiError | None:
    """409 for a live document with these bytes; names it only when the caller may see it (SPEC-03 §2)."""
    existing = (
        await session.execute(
            select(Document).where(Document.sha256 == sha256, Document.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if existing is None:
        return None
    if set(existing.access_groups) & set(user.groups):
        return ApiError(
            409,
            "duplicate_document",
            f'This file is already uploaded as "{existing.title}".',
            existingId=str(existing.id),
        )
    return ApiError(409, "duplicate_document", "This file is already uploaded.")


async def create_document(
    session: AsyncSession, settings: Settings, user: Identity, staged: StagedUpload, meta: UploadMeta
) -> Document:
    """Insert the document, place the file and enqueue the ingest job in one transaction."""
    try:
        if (duplicate := await _duplicate_error(session, staged.sha256, user)) is not None:
            raise duplicate
    except BaseException:
        staged.discard()
        raise
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        title=meta.title or _default_title(staged.filename),
        filename=staged.filename,
        content_type=staged.content_type,
        file_type=staged.file_type,
        size_bytes=staged.size_bytes,
        sha256=staged.sha256,
        storage_path=f"{doc_id}/{staged.filename}",
        doc_type=meta.doc_type or "other",
        department=meta.department,
        effective_date=meta.effective_date,
        access_groups=list(meta.access_groups),
        ingest_status="queued",
        uploaded_by=user.id,
    )
    folder = _store_dir(settings, doc_id)
    try:
        session.add(doc)
        await session.flush()
        folder.mkdir(parents=True, exist_ok=True)
        part = folder / f"{staged.filename}.part"
        shutil.move(staged.path, part)
        part.replace(folder / staged.filename)
        await jobs.enqueue(session, jobs.INGEST_DOCUMENT, doc_id)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        shutil.rmtree(folder, ignore_errors=True)
        # A concurrent upload of the same bytes tripped the unique index: same 409 as the check above.
        if (duplicate := await _duplicate_error(session, staged.sha256, user)) is not None:
            raise duplicate from None
        raise
    except BaseException:
        await session.rollback()
        shutil.rmtree(folder, ignore_errors=True)
        raise
    finally:
        staged.discard()
    await session.refresh(doc)
    log.info("document_created", document_id=str(doc_id), file_type=doc.file_type, size_bytes=doc.size_bytes)
    return doc


async def list_documents(
    session: AsyncSession, user: Identity, *, status: str | None = None, ingest_status: str | None = None
) -> list[Document]:
    query = select(Document).where(_visible(user)).order_by(Document.created_at.desc(), Document.id)
    if status:
        query = query.where(Document.status == status)
    if ingest_status:
        query = query.where(Document.ingest_status == ingest_status)
    return list((await session.execute(query)).scalars())


async def get_document(session: AsyncSession, user: Identity, doc_id: uuid.UUID) -> Document:
    doc = (
        await session.execute(select(Document).where(Document.id == doc_id, _visible(user)))
    ).scalar_one_or_none()
    if doc is None:
        raise _not_found()
    return doc


async def _lock_visible(session: AsyncSession, user: Identity, doc_id: uuid.UUID) -> Document:
    """The document under a row lock: a PATCH, delete or job swap on it waits its turn (SPEC-03 §1 rule 5)."""
    query = (
        select(Document)
        .where(Document.id == doc_id, _visible(user))
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    doc = (await session.execute(query)).scalar_one_or_none()
    if doc is None:
        raise _not_found()
    return doc


async def update_document(
    session: AsyncSession, user: Identity, doc_id: uuid.UUID, changes: dict[str, Any]
) -> Document:
    """Apply a PATCH. A change to `status` or `access_groups` reaches the chunks in the same transaction."""
    doc = await _lock_visible(session, user, doc_id)
    for field, value in changes.items():
        if value is None and field not in NULLABLE_FIELDS:
            raise ApiError(
                422,
                "validation_failed",
                "Some fields are not valid.",
                errors={field: ["This field cannot be empty."]},
            )
        setattr(doc, field, value)
    propagate = {f: changes[f] for f in ("status", "access_groups") if f in changes}
    if propagate:
        chunk_values = {("doc_status" if f == "status" else f): v for f, v in propagate.items()}
        await session.execute(update(Chunk).where(Chunk.document_id == doc.id).values(**chunk_values))
    if changes:
        doc.updated_at = func.now()
    await session.commit()
    await session.refresh(doc)
    return doc


async def delete_document(
    session: AsyncSession, settings: Settings, user: Identity, doc_id: uuid.UUID
) -> None:
    """Soft-delete, drop the chunks and queued jobs in one transaction, then remove the stored file."""
    doc = await _lock_visible(session, user, doc_id)
    doc.deleted_at = func.now()
    doc.updated_at = func.now()
    await session.execute(delete(Chunk).where(Chunk.document_id == doc.id))
    await session.execute(delete(Job).where(Job.document_id == doc.id, Job.status == "queued"))
    await session.commit()
    shutil.rmtree(_store_dir(settings, doc_id), ignore_errors=True)
    log.info("document_deleted", document_id=str(doc_id))


async def get_file(
    session: AsyncSession, settings: Settings, user: Identity, doc_id: uuid.UUID
) -> tuple[Document, Path]:
    """The document and the path of its original, or 404 (hidden document, or the file is gone)."""
    doc = await get_document(session, user, doc_id)
    path = resolve_stored(settings.storage_dir, doc.storage_path)
    if path is None or not path.is_file():
        raise _not_found()
    return doc, path


# --- Re-ingest and chunk reads (SPEC-08 §4.6-4.7) ---


async def request_reingest(session: AsyncSession, user: Identity, doc_id: uuid.UUID) -> Document:
    """Queue a new ingest job; the old chunks stay searchable until the swap. 409 while one is pending."""
    doc = await _lock_visible(session, user, doc_id)
    pending = (
        await session.execute(
            select(func.count())
            .select_from(Job)
            .where(Job.document_id == doc.id, Job.kind == jobs.INGEST_DOCUMENT)
            .where(Job.status.in_(("queued", "running")))
        )
    ).scalar_one()
    if pending:
        raise ApiError(
            409, "ingest_in_progress", "This document is already being ingested. Wait for it to finish."
        )
    doc.ingest_status = "queued"
    doc.ingest_error_code = None
    doc.ingest_error = None
    doc.updated_at = func.now()
    await jobs.enqueue(session, jobs.INGEST_DOCUMENT, doc.id)
    await session.commit()
    await session.refresh(doc)
    return doc


async def replace_file(
    session: AsyncSession,
    settings: Settings,
    user: Identity,
    doc_id: uuid.UUID,
    staged: StagedUpload,
) -> Document:
    """Swap the stored file for a new version of the same document and queue ingestion (SPEC-03 §7).

    The id, title and access groups stay; the old chunks stay searchable until the new set swaps in.
    """
    try:
        doc = await _lock_visible(session, user, doc_id)
        pending = (
            await session.execute(
                select(func.count())
                .select_from(Job)
                .where(Job.document_id == doc.id, Job.kind == jobs.INGEST_DOCUMENT)
                .where(Job.status.in_(("queued", "running")))
            )
        ).scalar_one()
        if pending:
            raise ApiError(
                409, "ingest_in_progress", "This document is already being ingested. Wait for it to finish."
            )
        if doc.sha256 == staged.sha256:
            raise ApiError(
                409,
                "duplicate_document",
                "This is the same file the document already has.",
                existingId=str(doc.id),
            )
        if (duplicate := await _duplicate_error(session, staged.sha256, user)) is not None:
            raise duplicate
    except BaseException:
        await session.rollback()
        staged.discard()
        raise
    folder = _store_dir(settings, doc.id)
    old_path = resolve_stored(settings.storage_dir, doc.storage_path)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        part = folder / f"{staged.filename}.part"
        shutil.move(staged.path, part)
        doc.filename = staged.filename
        doc.content_type = staged.content_type
        doc.file_type = staged.file_type
        doc.size_bytes = staged.size_bytes
        doc.sha256 = staged.sha256
        doc.storage_path = f"{doc.id}/{staged.filename}"
        doc.ingest_status = "queued"
        doc.ingest_error_code = None
        doc.ingest_error = None
        doc.updated_at = func.now()
        await session.flush()
        part.replace(folder / staged.filename)
        await jobs.enqueue(session, jobs.INGEST_DOCUMENT, doc.id)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        (folder / staged.filename).unlink(missing_ok=True)
        # A concurrent upload of the same bytes tripped the unique index: same 409 as the check above.
        if (duplicate := await _duplicate_error(session, staged.sha256, user)) is not None:
            raise duplicate from None
        raise
    except BaseException:
        await session.rollback()
        (folder / f"{staged.filename}.part").unlink(missing_ok=True)
        raise
    finally:
        staged.discard()
    if old_path is not None and old_path.name != staged.filename:
        old_path.unlink(missing_ok=True)
    await session.refresh(doc)
    log.info("document_file_replaced", document_id=str(doc.id), file_type=doc.file_type)
    return doc


async def list_chunks(
    session: AsyncSession,
    user: Identity,
    doc_id: uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 50,
    around: uuid.UUID | None = None,
    radius: int = 2,
) -> tuple[list[Chunk], int]:
    """A page of the document's chunks in order, or the neighbours of one chunk (`around`)."""
    doc = await get_document(session, user, doc_id)
    total = (
        await session.execute(select(func.count()).select_from(Chunk).where(Chunk.document_id == doc.id))
    ).scalar_one()
    query = select(Chunk).where(Chunk.document_id == doc.id).order_by(Chunk.ordinal)
    if around is not None:
        centre = (
            await session.execute(
                select(Chunk.ordinal).where(Chunk.id == around, Chunk.document_id == doc.id)
            )
        ).scalar_one_or_none()
        if centre is None:
            raise _not_found()
        query = query.where(Chunk.ordinal.between(centre - radius, centre + radius))
    else:
        query = query.offset(offset).limit(limit)
    return list((await session.execute(query)).scalars()), total


# --- Ingestion state transitions (SPEC-03 §3). Called by the worker only. ---

QUOTA_MESSAGE = "The AI service quota is used up. Top up or wait for the next cycle, then select Retry."


async def begin_ingest(session: AsyncSession, doc_id: uuid.UUID) -> Document | None:
    """Mark the document `processing`. None when it is gone (deleted): the caller finishes the job."""
    doc = (
        await session.execute(
            select(Document)
            .where(Document.id == doc_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if doc is None or doc.deleted_at is not None:
        await session.rollback()
        return None
    doc.ingest_status = "processing"
    doc.ingest_error_code = None
    doc.ingest_error = None
    doc.updated_at = func.now()
    await session.commit()
    return doc


async def foreign_embedding_model(session: AsyncSession, doc_id: uuid.UUID, model: str) -> str | None:
    """A different embedding model already used by other documents' chunks, if any (SPEC-03 §9)."""
    return (
        await session.execute(
            select(Chunk.embedding_model)
            .where(Chunk.document_id != doc_id, Chunk.embedding_model.is_not(None))
            .where(Chunk.embedding_model != model)
            .limit(1)
        )
    ).scalar_one_or_none()


async def swap_chunks(
    session: AsyncSession, job_id: int, doc_id: uuid.UUID, result: IngestResult, embedding_model: str
) -> int:
    """Replace the document's chunks and finish the job in ONE transaction (SPEC-03 §1 rules 3 and 5).

    The document is re-read under a row lock and `status` / `access_groups` are copied from it now, so a
    PATCH or delete that ran during ingestion is never overwritten. Returns the new chunk count.
    """
    doc = (
        await session.execute(
            select(Document)
            .where(Document.id == doc_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if doc is None or doc.deleted_at is not None:
        await jobs.mark_done(session, job_id)
        await session.commit()
        return 0
    first_ingestion = (
        await session.execute(select(func.count()).select_from(Chunk).where(Chunk.document_id == doc_id))
    ).scalar_one() == 0
    _apply_metadata(doc, result, first_ingestion)
    await session.execute(delete(Chunk).where(Chunk.document_id == doc_id))
    session.add_all(
        Chunk(
            document_id=doc_id,
            ordinal=i,
            chunk_type=c.chunk_type,
            text=c.text,
            heading_path=c.heading_path,
            section=c.section,
            page_start=c.page_start,
            page_end=c.page_end,
            sheet=c.sheet,
            token_count=c.token_count,
            embedding=c.embedding,
            embedding_model=embedding_model if c.embedding is not None else None,
            doc_status=doc.status,
            access_groups=list(doc.access_groups),
        )
        for i, c in enumerate(result.chunks)
    )
    doc.chunk_count = len(result.chunks)
    doc.ingest_status = "ready"
    doc.ingest_error_code = None
    doc.ingest_error = None
    doc.updated_at = func.now()
    await jobs.mark_done(session, job_id)
    await session.commit()
    return len(result.chunks)


def _apply_metadata(doc: Document, result: IngestResult, first_ingestion: bool) -> None:
    """Fill only what the user left unset (form values and PATCH edits win), SPEC-03 §6."""
    meta = result.meta
    doc.title = metadata.resolve_title(doc.title, doc.filename, meta.title)
    if doc.doc_type == "other" and meta.doc_type:
        doc.doc_type = meta.doc_type
    if doc.department is None:
        doc.department = meta.department
    if doc.effective_date is None:
        doc.effective_date = meta.effective_date
    if doc.version is None:
        doc.version = meta.version
    doc.language = meta.language
    doc.page_count = meta.page_count
    doc.summary = result.summary
    doc.tags = result.tags
    # SPEC-03 §6.1: only the first ingestion may set `superseded`, so a manual status change sticks.
    if first_ingestion and meta.superseded:
        doc.status = "superseded"


async def fail_ingest(
    session: AsyncSession, job_id: int, doc_id: uuid.UUID | None, code: str, message: str
) -> None:
    """Job and document go to `failed` with the code and a short message. Old chunks stay.

    A document deleted meanwhile is not a failure: the job is `done` with nothing written (SPEC-03 §1 rule 5).
    """
    if doc_id is not None:
        live = (
            await session.execute(
                update(Document)
                .where(Document.id == doc_id, Document.deleted_at.is_(None))
                .values(
                    ingest_status="failed",
                    ingest_error_code=code,
                    ingest_error=message,
                    updated_at=func.now(),
                )
                .returning(Document.id)
            )
        ).scalar_one_or_none()
        if live is None:
            await jobs.mark_done(session, job_id)
            await session.commit()
            log.info("ingest_skipped_document_gone", job_id=job_id, document_id=str(doc_id))
            return
    await jobs.mark_failed(session, job_id, code, message)
    await session.commit()
    log.warning("ingest_failed", job_id=job_id, document_id=str(doc_id), error_code=code)


async def retry_ingest(session: AsyncSession, job: jobs.ClaimedJob, code: str, message: str) -> None:
    """Retryable failure with attempts left: requeue with backoff; the document stays `processing`."""
    await jobs.mark_retry(session, job, code, message)
    await session.commit()
    log.info("ingest_retry", job_id=job.id, attempts=job.attempts, error_code=code)
