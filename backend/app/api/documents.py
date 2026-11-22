"""Document endpoints 4-9 (SPEC-08 §4). Routers validate, call one service function and map the result."""

import uuid
from collections.abc import Callable, Coroutine
from datetime import date
from pathlib import Path
from typing import Annotated, Any, Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi import Path as PathParam
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.api.schemas import ChunkListOut, ChunkOut, DocumentListOut, DocumentOut, DocumentPatch
from app.config import DOC_TYPES, Settings, get_settings
from app.db.engine import get_session
from app.ingestion import service
from app.security.identity import AdminUser, CurrentUser, Identity
from app.security.uploads import stage_upload

# Multipart framing and the text fields add a little on top of the file itself.
MULTIPART_OVERHEAD = 1024 * 1024


class UploadRoute(APIRoute):
    """Refuses an oversized body from its Content-Length before the multipart body is parsed (SPEC-09 §2)."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def guarded(request: Request) -> Response:
            settings = get_settings()
            declared = request.headers.get("content-length", "")
            if declared.isdigit() and int(declared) > settings.max_upload_bytes + MULTIPART_OVERHEAD:
                raise ApiError(
                    413,
                    "file_too_large",
                    f"This file is over the {settings.max_upload_mb} MB limit. Upload a smaller file.",
                )
            return await handler(request)

        return guarded


router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
upload_router = APIRouter(prefix="/api/v1/documents", tags=["documents"], route_class=UploadRoute)

Session = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
DocId = Annotated[uuid.UUID, PathParam(alias="id")]


def _invalid(field: str, message: str) -> ApiError:
    return ApiError(422, "validation_failed", "Some fields are not valid.", errors={field: [message]})


def _clean_groups(groups: list[str], user: Identity) -> list[str]:
    """Trimmed, de-duplicated, never empty and a subset of the caller's own groups (SPEC-09 §3)."""
    cleaned = list(dict.fromkeys(g.strip() for g in groups if g.strip()))
    if not cleaned:
        raise _invalid("accessGroups", "Choose at least one access group.")
    outside = [g for g in cleaned if g not in user.groups]
    if outside:
        raise _invalid("accessGroups", "You can only use access groups you belong to.")
    return cleaned


def _clean_doc_type(value: str) -> str:
    if value not in DOC_TYPES:
        raise _invalid("docType", f"Choose one of: {', '.join(DOC_TYPES)}.")
    return value


@upload_router.post("", status_code=202, response_model=DocumentOut)
async def upload_document(
    session: Session,
    settings: SettingsDep,
    user: AdminUser,
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
    doc_type: Annotated[str | None, Form(alias="docType")] = None,
    department: Annotated[str | None, Form()] = None,
    effective_date: Annotated[date | None, Form(alias="effectiveDate")] = None,
    access_groups: Annotated[list[str] | None, Form(alias="accessGroups")] = None,
) -> DocumentOut:
    meta = service.UploadMeta(
        title=(title or "").strip() or None,
        doc_type=_clean_doc_type(doc_type) if doc_type else None,
        department=(department or "").strip() or None,
        effective_date=effective_date,
        access_groups=_clean_groups(access_groups, user) if access_groups else ("all",),
    )
    staged = await stage_upload(
        file,
        file.filename or "file",
        max_bytes=settings.max_upload_bytes,
        tmp_dir=Path(settings.storage_dir) / ".tmp",
    )
    # create_document owns the temp file from here and removes it on every path.
    doc = await service.create_document(session, settings, user, staged, meta)
    return DocumentOut.model_validate(doc)


@router.get("", response_model=DocumentListOut)
async def list_documents(
    session: Session,
    user: CurrentUser,
    status: Literal["current", "superseded"] | None = None,
    ingest_status: Annotated[
        Literal["queued", "processing", "ready", "failed"] | None, Query(alias="ingestStatus")
    ] = None,
) -> DocumentListOut:
    docs = await service.list_documents(session, user, status=status, ingest_status=ingest_status)
    return DocumentListOut(items=[DocumentOut.model_validate(d) for d in docs])


@router.get("/{id}", response_model=DocumentOut)
async def get_document(session: Session, user: CurrentUser, doc_id: DocId) -> DocumentOut:
    return DocumentOut.model_validate(await service.get_document(session, user, doc_id))


@router.patch("/{id}", response_model=DocumentOut)
async def patch_document(
    session: Session, user: AdminUser, doc_id: DocId, body: DocumentPatch
) -> DocumentOut:
    changes = {name: getattr(body, name) for name in body.model_fields_set}
    if "doc_type" in changes and changes["doc_type"] is not None:
        _clean_doc_type(changes["doc_type"])
    if changes.get("access_groups") is not None:
        changes["access_groups"] = _clean_groups(changes["access_groups"], user)
    if "title" in changes and changes["title"] is not None:
        changes["title"] = changes["title"].strip() or None
    doc = await service.update_document(session, user, doc_id, changes)
    return DocumentOut.model_validate(doc)


@router.delete("/{id}", status_code=204)
async def delete_document(
    session: Session, settings: SettingsDep, user: AdminUser, doc_id: DocId
) -> Response:
    await service.delete_document(session, settings, user, doc_id)
    return Response(status_code=204)


@router.get("/{id}/file", response_class=FileResponse)
async def download_file(
    session: Session, settings: SettingsDep, user: CurrentUser, doc_id: DocId
) -> FileResponse:
    doc, path = await service.get_file(session, settings, user, doc_id)
    return FileResponse(
        path,
        media_type=doc.content_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(doc.filename)}",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/{id}/reingest", status_code=202, response_model=DocumentOut)
async def reingest_document(session: Session, user: AdminUser, doc_id: DocId) -> DocumentOut:
    return DocumentOut.model_validate(await service.request_reingest(session, user, doc_id))


@upload_router.post("/{id}/file", status_code=202, response_model=DocumentOut)
async def replace_document_file(
    session: Session,
    settings: SettingsDep,
    user: AdminUser,
    doc_id: DocId,
    file: Annotated[UploadFile, File()],
) -> DocumentOut:
    staged = await stage_upload(
        file,
        file.filename or "file",
        max_bytes=settings.max_upload_bytes,
        tmp_dir=Path(settings.storage_dir) / ".tmp",
    )
    # replace_file owns the temp file from here and removes it on every path.
    return DocumentOut.model_validate(await service.replace_file(session, settings, user, doc_id, staged))


@router.get("/{id}/chunks", response_model=ChunkListOut)
async def list_chunks(
    session: Session,
    user: CurrentUser,
    doc_id: DocId,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    around: uuid.UUID | None = None,
    radius: Annotated[int, Query(ge=0, le=10)] = 2,
) -> ChunkListOut:
    chunks, total = await service.list_chunks(
        session, user, doc_id, offset=offset, limit=limit, around=around, radius=radius
    )
    return ChunkListOut(items=[ChunkOut.model_validate(c) for c in chunks], total=total)
