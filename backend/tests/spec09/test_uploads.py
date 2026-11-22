"""SPEC-09 §8 checks 1, 2, 3, 4 (list/get/file paths only) and 7."""

import io
import os
from pathlib import Path

import httpx
import pytest

from app.api.errors import ApiError
from app.config import get_settings
from app.security.uploads import MAX_ZIP_ENTRIES, sanitize_filename, stage_upload
from tests import uploads
from tests.uploads import upload


async def test_spec09_ac01_type_comes_from_bytes_not_extension(client: httpx.AsyncClient) -> None:
    png = await upload(client, uploads.PNG + b"1", "scan.pdf")
    assert png.status_code == 202
    assert (png.json()["fileType"], png.json()["contentType"]) == ("png", "image/png")

    exe = await upload(client, b"MZ\x90\x00 not a pdf", "setup.pdf")
    assert exe.status_code == 415
    assert exe.json()["code"] == "unsupported_type"


async def test_spec09_ac01_each_allowed_type_is_detected(client: httpx.AsyncClient) -> None:
    cases = {
        "a.pdf": (uploads.pdf("t"), "pdf"),
        "a.docx": (uploads.docx("t"), "docx"),
        "a.xlsx": (uploads.xlsx("t"), "xlsx"),
        "a.png": (uploads.PNG + b"t", "png"),
        "a.jpg": (uploads.JPEG + b"t", "jpg"),
        "a.md": (uploads.markdown("t"), "md"),
    }
    for name, (content, expected) in cases.items():
        resp = await upload(client, content, name)
        assert resp.status_code == 202, (name, resp.text)
        assert resp.json()["fileType"] == expected, name


@pytest.mark.parametrize(
    ("content", "filename"),
    [
        (b"plain text but not markdown", "notes.txt"),
        (b"# markdown\x00with nul", "bad.md"),
        (b"\xff\xfe invalid utf8 \xc3\x28", "latin.md"),
        (uploads.zip_file("readme.txt"), "other.docx"),
        (b"PK\x03\x04 truncated", "broken.xlsx"),
    ],
)
async def test_spec09_ac01_everything_else_is_415(
    client: httpx.AsyncClient, content: bytes, filename: str
) -> None:
    resp = await upload(client, content, filename)
    assert resp.status_code == 415
    assert resp.json()["code"] == "unsupported_type"


async def test_spec09_zip_with_too_many_entries_is_rejected(client: httpx.AsyncClient) -> None:
    names = ["word/document.xml", *(f"f{i}.txt" for i in range(MAX_ZIP_ENTRIES))]
    resp = await upload(client, uploads.zip_file(*names), "bomb.docx")
    assert resp.status_code == 415


async def test_spec09_ac02_oversized_upload_is_413_and_leaves_no_file(client: httpx.AsyncClient) -> None:
    before = uploads.stored_files()
    resp = await upload(client, b"%PDF-" + b"0" * (26 * 1024 * 1024), "big.pdf")
    assert resp.status_code == 413
    assert resp.json()["code"] == "file_too_large"
    assert uploads.stored_files() == before


async def test_spec09_ac02_streaming_limit_stops_without_content_length(tmp_path: Path) -> None:
    class Source:
        def __init__(self) -> None:
            self.stream = io.BytesIO(b"%PDF-" + b"0" * 5000)

        async def read(self, size: int = -1, /) -> bytes:
            return self.stream.read(1024)

    with pytest.raises(ApiError) as info:
        await stage_upload(Source(), "x.pdf", max_bytes=2048, tmp_dir=tmp_path)
    assert info.value.status == 413
    assert not os.listdir(tmp_path)


async def test_spec09_ac03_path_traversal_name_is_stored_under_the_documents_folder(
    client: httpx.AsyncClient,
) -> None:
    resp = await upload(client, uploads.pdf("trav"), "../../etc/passwd.pdf")
    body = resp.json()
    assert resp.status_code == 202
    assert body["filename"] == "passwd.pdf"
    assert (Path(get_settings().storage_dir) / body["id"] / "passwd.pdf").is_file()


@pytest.mark.parametrize(
    ("raw", "clean"),
    [
        ("..\\..\\windows\\evil.pdf", "evil.pdf"),
        ("Laporan Kewangan (2026) é.pdf", "Laporan Kewangan _2026_ _.pdf"),
        ("", "file"),
        ("..", "file"),
        (("a" * 200) + ".pdf", ("a" * 116) + ".pdf"),
    ],
)
def test_spec09_filename_sanitizing(raw: str, clean: str) -> None:
    assert sanitize_filename(raw) == clean


async def test_spec09_ac04_file_is_served_with_nosniff_and_stored_type(client: httpx.AsyncClient) -> None:
    doc = (await upload(client, uploads.pdf("file"), "Policy Doc.pdf")).json()
    resp = await client.get(f"/api/v1/documents/{doc['id']}/file")
    assert resp.status_code == 200
    assert resp.content == uploads.pdf("file")
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["content-disposition"] == "inline; filename*=UTF-8''Policy%20Doc.pdf"


async def test_spec09_ac07_access_groups_outside_the_callers_are_422(client: httpx.AsyncClient) -> None:
    resp = await upload(client, uploads.pdf("grp"), "g.pdf", accessGroups=["all", "hr"])
    assert resp.status_code == 422
    assert resp.json()["code"] == "validation_failed"
    assert "accessGroups" in resp.json()["errors"]
    doc = (await upload(client, uploads.pdf("grp2"), "g2.pdf")).json()
    patch = await client.patch(f"/api/v1/documents/{doc['id']}", json={"accessGroups": ["hr"]})
    assert patch.status_code == 422
