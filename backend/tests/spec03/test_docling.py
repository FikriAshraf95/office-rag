"""SPEC-03 §10 checks 5, 7, 12 with the real parser. Slow: marked `docling`; needs cached Docling models."""

from pathlib import Path

import pytest

from app.config import get_settings
from app.ingestion.chunking import hf_counter
from app.ingestion.extract import DocInfo, extract
from app.ingestion.types import IngestResult

pytestmark = pytest.mark.docling

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "serimaju"


@pytest.fixture(scope="module", autouse=True)
def _offline() -> None:
    """Models come from the local cache; a download attempt would hit the network guard."""
    import os

    os.environ["HF_HUB_OFFLINE"] = "1"


def run(filename: str, file_type: str, title: str) -> IngestResult:
    settings = get_settings()
    return extract(FIXTURES / filename, DocInfo(title, filename, file_type), settings, hf_counter(settings))


@pytest.fixture(scope="module")
def handbook() -> IngestResult:
    return run("HR_Employee_Handbook_2024.pdf", "pdf", "HR Employee Handbook 2024")


def test_spec03_ac05_pdf_section_chunk_has_path_section_page_and_title_prefix(handbook: IngestResult) -> None:
    chunk = next(c for c in handbook.chunks if c.section == "1")
    assert chunk.heading_path[0] == "Employee Handbook 2024"
    assert chunk.heading_path[-1] == "1. About Serimaju"
    assert chunk.page_start is not None
    assert chunk.text.startswith("Employee Handbook 2024 > 1. About Serimaju\n\n")
    assert handbook.meta.page_count == 4
    assert all(0 < c.token_count <= 800 + 40 for c in handbook.chunks)


def test_spec03_ac07_pdf_first_page_superseded_is_detected(handbook: IngestResult) -> None:
    assert handbook.meta.superseded is True
    assert handbook.meta.doc_type == "handbook"


def test_spec03_ac12_markdown_front_matter_fills_metadata_through_the_real_parser() -> None:
    result = run("Travel_and_Claims_SOP.md", "md", "Travel and Claims SOP")
    meta = result.meta
    assert (meta.title, meta.version, str(meta.effective_date), meta.department) == (
        "Travel and Claims SOP",
        "2.3",
        "2026-02-01",
        "Finance",
    )
    assert result.chunks[0].heading_path == ["Travel and Claims SOP"]
    assert any(c.section == "1" for c in result.chunks)
