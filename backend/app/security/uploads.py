"""Upload validation (SPEC-09 §2): type by magic bytes, streaming size limit, zip-bomb guard, filename."""

import asyncio
import codecs
import hashlib
import os
import re
import unicodedata
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol

from app.api.errors import ApiError

CHUNK = 1024 * 1024
MAX_ZIP_UNCOMPRESSED = 200 * 1024 * 1024
MAX_ZIP_ENTRIES = 2000
MAX_FILENAME = 120

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
ZIP_MAGIC = b"PK\x03\x04"

CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "md": "text/markdown",
    "png": "image/png",
    "jpg": "image/jpeg",
}
UNSUPPORTED = "This file type is not supported. Upload a PDF, DOCX, XLSX, Markdown, PNG or JPG file."


class UploadSource(Protocol):
    async def read(self, size: int = -1, /) -> bytes: ...


@dataclass(frozen=True, slots=True)
class StagedUpload:
    """A validated upload waiting in the temp folder; the service moves it to its final place."""

    path: Path
    filename: str
    file_type: str
    content_type: str
    size_bytes: int
    sha256: str

    def discard(self) -> None:
        self.path.unlink(missing_ok=True)


def sanitize_filename(name: str) -> str:
    """Base name only, NFC, `[A-Za-z0-9._ -]` only, at most 120 characters (the extension survives)."""
    base = re.split(r"[\\/]", name)[-1]
    base = unicodedata.normalize("NFC", base)
    base = re.sub(r"[^A-Za-z0-9._ -]", "_", base).strip(" .")
    if not base:
        return "file"
    if len(base) > MAX_FILENAME:
        stem, dot, ext = base.rpartition(".")
        if dot and len(ext) <= 10:
            base = stem[: MAX_FILENAME - len(ext) - 1] + "." + ext
        else:
            base = base[:MAX_FILENAME]
    return base


def _check_zip(path: Path) -> set[str]:
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ZIP_ENTRIES or sum(i.file_size for i in infos) > MAX_ZIP_UNCOMPRESSED:
                raise ApiError(
                    415, "unsupported_type", "This file is too large once unpacked. Upload a smaller file."
                )
            return {i.filename for i in infos}
    except zipfile.BadZipFile:
        raise ApiError(415, "unsupported_type", UNSUPPORTED) from None


def _is_utf8_text(path: Path) -> bool:
    decoder = codecs.getincrementaldecoder("utf-8")()
    with path.open("rb") as handle:
        while block := handle.read(CHUNK):
            if b"\x00" in block:
                return False
            try:
                decoder.decode(block)
            except UnicodeDecodeError:
                return False
    try:
        decoder.decode(b"", final=True)
    except UnicodeDecodeError:
        return False
    return True


def detect_type(path: Path, filename: str) -> str:
    """The file type (`pdf`, `docx`, …) from the bytes. Raises 415 when it is not an allowed type."""
    with path.open("rb") as handle:
        head = handle.read(16)
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head.startswith(PNG_MAGIC):
        return "png"
    if head.startswith(JPEG_MAGIC):
        return "jpg"
    if head.startswith(ZIP_MAGIC):
        names = _check_zip(path)
        if "word/document.xml" in names:
            return "docx"
        if "xl/workbook.xml" in names:
            return "xlsx"
        raise ApiError(415, "unsupported_type", UNSUPPORTED)
    if filename.lower().endswith(".md") and _is_utf8_text(path):
        return "md"
    raise ApiError(415, "unsupported_type", UNSUPPORTED)


def _open_temp(tmp_dir: Path) -> tuple[Path, BinaryIO]:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp = tmp_dir / f"{uuid.uuid4().hex}.part"
    return tmp, tmp.open("wb")


def _finish(tmp: Path, filename: str) -> tuple[str, str]:
    safe_name = sanitize_filename(filename)
    return safe_name, detect_type(tmp, safe_name)


async def stage_upload(source: UploadSource, filename: str, *, max_bytes: int, tmp_dir: Path) -> StagedUpload:
    """Stream to a temp file (stopping at `max_bytes`), hash it, detect its type. Nothing is left behind."""
    tmp, out = await asyncio.to_thread(_open_temp, tmp_dir)
    digest = hashlib.sha256()
    size = 0
    try:
        try:
            while block := await source.read(CHUNK):
                size += len(block)
                if size > max_bytes:
                    limit_mb = max_bytes // (1024 * 1024)
                    raise ApiError(
                        413,
                        "file_too_large",
                        f"This file is over the {limit_mb} MB limit. Upload a smaller file.",
                    )
                digest.update(block)
                await asyncio.to_thread(out.write, block)
        finally:
            await asyncio.to_thread(out.close)
        if size == 0:
            raise ApiError(415, "unsupported_type", "This file is empty. Choose a file with content.")
        safe_name, file_type = await asyncio.to_thread(_finish, tmp, filename)
    except BaseException:
        await asyncio.to_thread(tmp.unlink, missing_ok=True)
        raise
    return StagedUpload(
        path=tmp,
        filename=safe_name,
        file_type=file_type,
        content_type=CONTENT_TYPES[file_type],
        size_bytes=size,
        sha256=digest.hexdigest(),
    )


def resolve_stored(storage_dir: str, storage_path: str) -> Path | None:
    """The absolute path of a stored original, or None when it would leave `storage_dir`."""
    root = Path(storage_dir).resolve()
    target = (root / storage_path).resolve()
    return target if os.path.commonpath([root, target]) == str(root) else None
