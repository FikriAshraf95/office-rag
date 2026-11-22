"""SPEC-03 §8 (M07): vision fallback for images, summary + tags. No Docling, no network."""

import json
from pathlib import Path

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.ingestion import extract as extraction
from app.ingestion.chunking import WhitespaceCounter
from app.ingestion.types import ChunkDraft, DocMeta, IngestResult
from app.ingestion.vision import (
    DESCRIPTION_MARK,
    VISION_INSTRUCTION,
    apply_summary,
    apply_vision,
    parse_summary,
)
from app.providers.base import ChatModel
from app.providers.registry import Providers
from tests.spec03.test_worker import doc_row, fake_extract, new_doc, run_job

LONG_OCR = "Quarterly leave policy " * 10


def image_result(ocr: str, filename: str = "scan.png") -> IngestResult:
    result = IngestResult(
        chunks=[ChunkDraft("image_text", ocr, [], 3)] if ocr else [],
        meta=DocMeta(),
        ocr_text=ocr,
        vision_candidate=extraction.needs_vision(ocr, filename, get_settings()),
    )
    return result


def test_vision_instruction_fixes_org_chart_line_and_team_labels() -> None:
    """D009: explicit reporting direction, and free-standing labels tied to the box they sit under."""
    assert "labels outside the boxes" in VISION_INSTRUCTION
    assert "<Name>, <Title> - reports to <Name>, <Title>" in VISION_INSTRUCTION
    assert "Label directly below the box of <Name>, <Title>: <label text>" in VISION_INSTRUCTION
    assert "Do not add anything not visible." in VISION_INSTRUCTION


def test_needs_vision_rules() -> None:
    s = get_settings()
    assert extraction.needs_vision("short", "photo.jpg", s)
    assert not extraction.needs_vision(LONG_OCR, "photo.jpg", s)
    assert extraction.needs_vision(LONG_OCR, "Org_Chart_2026.jpg", s)
    assert extraction.needs_vision(LONG_OCR, "network-diagram.png", s)


async def test_short_ocr_calls_vision_and_stores_ocr_then_description(
    providers: Providers, tmp_path: Path
) -> None:
    img = tmp_path / "scan.png"
    img.write_bytes(b"\x89PNG fake")
    result = image_result("tiny text")
    await apply_vision(
        result,
        img,
        title="Scan",
        filename="scan.png",
        file_type="png",
        providers=providers,
        counter=WhitespaceCounter(),
        doc_id="d1",
    )
    assert len(result.chunks) == 1
    chunk = result.chunks[0]
    assert chunk.chunk_type == "image_text"
    assert (
        chunk.text.index("tiny text")
        < chunk.text.index(DESCRIPTION_MARK)
        < chunk.text.index("[image] scan.png")
    )


async def test_empty_ocr_gets_description_only(providers: Providers, tmp_path: Path) -> None:
    img = tmp_path / "blank.jpg"
    img.write_bytes(b"\xff\xd8 fake")
    result = image_result("", "blank.jpg")
    await apply_vision(
        result,
        img,
        title="Blank",
        filename="blank.jpg",
        file_type="jpg",
        providers=providers,
        counter=WhitespaceCounter(),
        doc_id="d2",
    )
    assert [c.text for c in result.chunks] == ["Blank\n\n[image] blank.jpg"]


async def test_long_ocr_on_non_diagram_does_not_call_vision(
    providers: Providers, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: list[bool] = []

    async def spy(*_: object, **__: object) -> None:
        called.append(True)

    monkeypatch.setattr(providers.vision(), "describe", spy)
    img = tmp_path / "memo.jpg"
    img.write_bytes(b"\xff\xd8 fake")
    result = image_result(LONG_OCR, "memo.jpg")
    before = list(result.chunks)
    await apply_vision(
        result,
        img,
        title="Memo",
        filename="memo.jpg",
        file_type="jpg",
        providers=providers,
        counter=WhitespaceCounter(),
        doc_id="d3",
    )
    assert called == []
    assert result.chunks == before


def test_parse_summary_is_tolerant() -> None:
    long = " ".join(["w"] * 90)
    summary, tags = parse_summary(
        json.dumps({"summary": long, "tags": ["HR", "hr", " Leave ", 5, "a", "b", "c", "d"]})
    )
    assert summary is not None and len(summary.split()) == 60
    assert tags == ["hr", "leave", "a", "b", "c"]
    assert parse_summary("not json") == (None, [])
    assert parse_summary('{"verdict": "correct"}') == (None, [])


async def test_summary_failure_is_not_fatal(providers: Providers) -> None:
    from app.providers.errors import ProviderError

    fast: ChatModel = providers.chat("fast")
    fast.fail_with(ProviderError("provider_error", retryable=True, http_status=500))  # type: ignore[attr-defined]
    result = IngestResult(chunks=[ChunkDraft("text", "some body", [], 2)])
    await apply_summary(result, title="T", providers=providers, doc_id="d4")
    assert (result.summary, result.tags) == (None, [])


async def test_worker_stores_summary_and_tags(
    client: httpx.AsyncClient,
    db: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extraction, "extract", fake_extract())
    providers.chat("fast").script([json.dumps({"summary": "Leave rules.", "tags": ["hr", "leave"]})])  # type: ignore[attr-defined]
    doc_id = await new_doc(client, "m07-summary")
    await run_job(sessions, providers)
    doc = await doc_row(db, doc_id)
    assert (doc.summary, doc.tags) == ("Leave rules.", ["hr", "leave"])
