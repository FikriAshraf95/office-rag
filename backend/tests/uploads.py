"""Builders for upload tests: tiny valid files of each type, unique per `seed`."""

import io
import zipfile
from pathlib import Path

import httpx

from app.config import get_settings

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16


def pdf(seed: str = "a") -> bytes:
    return b"%PDF-1.4\n% " + seed.encode() + b"\n%%EOF\n"


def zip_file(*names: str, seed: str = "a") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name in names:
            archive.writestr(name, f"<x>{seed}</x>")
    return buffer.getvalue()


def docx(seed: str = "a") -> bytes:
    return zip_file("word/document.xml", seed=seed)


def xlsx(seed: str = "a") -> bytes:
    return zip_file("xl/workbook.xml", seed=seed)


def markdown(seed: str = "a") -> bytes:
    return f"# Title {seed}\n\nBody text.\n".encode()


async def upload(
    client: httpx.AsyncClient, content: bytes, filename: str = "doc.pdf", **fields: str | list[str]
) -> httpx.Response:
    return await client.post("/api/v1/documents", files={"file": (filename, content)}, data=fields)


def stored_files() -> list[Path]:
    root = Path(get_settings().storage_dir)
    return [p for p in root.rglob("*") if p.is_file()]
