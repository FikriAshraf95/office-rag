"""File -> chunks, without any database or provider (SPEC-03 §4-6). Synchronous and CPU-heavy: the worker
runs it in a thread."""

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.ingestion import metadata
from app.ingestion.chunking import TokenCounter, chunk_sheets
from app.ingestion.parsers.xlsx import ParsedWorkbook, parse_xlsx
from app.ingestion.types import DocMeta, IngestError, IngestResult

LANGUAGE_SAMPLE_CHARS = 6000
FIRST_TEXT_CHARS = 2000
DIAGRAM_WORDS = ("chart", "diagram")
EMPTY_MESSAGE = "No text could be read from this file. Upload a clearer copy or a different format."


@dataclass(frozen=True, slots=True)
class DocInfo:
    """What the worker knows from the document row before parsing."""

    title: str
    filename: str
    file_type: str


def needs_vision(ocr_text: str, filename: str, settings: Settings) -> bool:
    """SPEC-03 §8: thin OCR, or a diagram by its filename."""
    name = filename.lower()
    return len(ocr_text) < settings.ocr_min_chars or any(w in name for w in DIAGRAM_WORDS)


def _base_meta(info: DocInfo, first_text: str, sample: str) -> DocMeta:
    return DocMeta(
        doc_type=metadata.doc_type_from_filename(info.filename),
        version=metadata.version_from_filename(info.filename),
        effective_date=metadata.find_effective_date(first_text),
        language=metadata.detect_language(sample[:LANGUAGE_SAMPLE_CHARS]),
        superseded=metadata.is_superseded(first_text),
    )


def _extract_xlsx(path: Path, info: DocInfo, settings: Settings, counter: TokenCounter) -> IngestResult:
    book: ParsedWorkbook = parse_xlsx(path)
    notes = [line for s in book.sheets for line in (*s.preamble, *(f"{a}: {b}" for a, b in s.pairs))]
    joined = "\n".join(notes)
    meta = _base_meta(info, joined[:FIRST_TEXT_CHARS], joined)
    meta.title = book.title
    title = metadata.resolve_title(info.title, info.filename, book.title)
    chunks = chunk_sheets(
        title,
        book.sheets,
        counter,
        rows_per_chunk=settings.xlsx_rows_per_chunk,
        max_tokens=settings.chunk_max_tokens,
    )
    return IngestResult(chunks=chunks, meta=meta)


def _extract_docling(path: Path, info: DocInfo, settings: Settings, counter: TokenCounter) -> IngestResult:
    from app.ingestion.parsers.docling_parse import parse_docling
    from app.ingestion.parsers.prose import chunk_docling

    parsed = parse_docling(path, info.file_type, settings.docling_artifacts_path)
    meta = _base_meta(info, parsed.first_text, parsed.full_text)
    front = parsed.front_matter
    meta.title = parsed.file_title
    meta.page_count = parsed.page_count
    if (front_version := front.get("version")) is not None:
        meta.version = str(front_version)
    if (front_date := metadata.parse_date(front.get("effective"))) is not None:
        meta.effective_date = front_date
    meta.department = metadata.department_from_owner(front.get("owner"))
    title = metadata.resolve_title(info.title, info.filename, parsed.file_title)
    chunks = chunk_docling(parsed.doc, title, counter, settings)
    result = IngestResult(chunks=chunks, meta=meta)
    if info.file_type in ("png", "jpg"):
        for chunk in chunks:
            chunk.chunk_type = "image_text"
        result.ocr_text = parsed.full_text.strip()
        result.vision_candidate = needs_vision(result.ocr_text, info.filename, settings)
    return result


def extract(path: Path, info: DocInfo, settings: Settings, counter: TokenCounter) -> IngestResult:
    """Parse, chunk and describe one file. Raises IngestError (`parse`, `empty`)."""
    if info.file_type == "xlsx":
        result = _extract_xlsx(path, info, settings, counter)
    else:
        result = _extract_docling(path, info, settings, counter)
    if not result.chunks and not result.vision_candidate:  # a candidate may still get text from vision
        raise IngestError("empty", EMPTY_MESSAGE)
    return result
