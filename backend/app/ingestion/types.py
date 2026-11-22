"""Plain data passed between parsers, chunking and the service. No I/O, no Docling, no SQL."""

from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class ChunkDraft:
    chunk_type: str  # text | table | table_rows | image_text
    text: str  # heading prefix + body: what is embedded and shown (SPEC-03 §5.1)
    heading_path: list[str]
    token_count: int
    section: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    sheet: str | None = None
    embedding: list[float] | None = None


@dataclass(slots=True)
class DocMeta:
    """What the file itself says about the document (SPEC-03 §6). None means "not found"."""

    title: str | None = None
    effective_date: date | None = None
    version: str | None = None
    department: str | None = None
    doc_type: str | None = None
    language: str | None = None
    page_count: int | None = None
    superseded: bool = False


@dataclass(slots=True)
class IngestResult:
    chunks: list[ChunkDraft] = field(default_factory=list)
    meta: DocMeta = field(default_factory=DocMeta)
    ocr_text: str = ""  # images only: what OCR read, for the vision fallback (SPEC-03 §8)
    vision_candidate: bool = False  # images only: OCR was thin or the image looks like a diagram
    summary: str | None = None
    tags: list[str] = field(default_factory=list)


class IngestError(Exception):
    """A failure with an `ingest_error_code` (SPEC-02 §2): parse, empty, provider, unknown."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
