"""Docling parsing for PDF, DOCX, Markdown and images (SPEC-03 §4). Worker only; models load once per process.

Docling never downloads at runtime in Compose: `DOCLING_ARTIFACTS_PATH` points at the baked models.
"""

from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

import structlog

from app.ingestion import metadata
from app.ingestion.types import IngestError

log = structlog.get_logger()

FIRST_TEXT_CHARS = 2000
PARSE_MESSAGE = "This file could not be read. Check that it is not damaged or password-protected."


@dataclass(slots=True)
class ParsedDocling:
    doc: Any  # DoclingDocument
    file_title: str | None
    first_text: str  # first page (or first 2,000 characters): superseded and effective-date checks
    full_text: str
    page_count: int | None
    front_matter: dict[str, Any]


@lru_cache
def _converter(artifacts: str | None) -> Any:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, ImageFormatOption, PdfFormatOption

    options = PdfPipelineOptions(do_ocr=True, do_table_structure=True, artifacts_path=artifacts)
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options),
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=options),
        }
    )


def _docx_core_title(path: Path) -> str | None:
    try:
        from docx import Document

        return (Document(str(path)).core_properties.title or "").strip() or None
    except Exception:
        return None


def _label(item: Any) -> str:
    return str(getattr(item.label, "value", item.label))


def _first_h1(doc: Any) -> str | None:
    for item in doc.texts:
        if _label(item) == "title":
            return str(item.text).strip() or None
    for item in doc.texts:
        if _label(item) == "section_header" and getattr(item, "level", 1) == 1:
            return str(item.text).strip() or None
    return None


def parse_docling(path: Path, file_type: str, artifacts_path: str | None = None) -> ParsedDocling:
    front: dict[str, Any] = {}
    try:
        if file_type == "md":
            from docling.datamodel.base_models import DocumentStream

            front, body = metadata.split_front_matter(path.read_text(encoding="utf-8", errors="replace"))
            source: Any = DocumentStream(name=path.name, stream=BytesIO(body.encode("utf-8")))
        else:
            source = path
        doc = _converter(artifacts_path or None).convert(source).document
    except Exception as exc:
        log.warning("docling_failed", error_type=type(exc).__name__)
        raise IngestError("parse", PARSE_MESSAGE) from exc
    pages = len(doc.pages) if file_type == "pdf" and doc.pages else None
    full = doc.export_to_markdown()
    first = doc.export_to_markdown(page_no=1) if pages else full
    file_title = front.get("title") if isinstance(front.get("title"), str) else None
    if file_title is None and file_type == "docx":
        file_title = _docx_core_title(path)
    return ParsedDocling(
        doc=doc,
        file_title=file_title or _first_h1(doc),
        first_text=first[:FIRST_TEXT_CHARS],
        full_text=full,
        page_count=pages,
        front_matter=front,
    )
