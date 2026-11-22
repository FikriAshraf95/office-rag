"""Structure-aware chunking (SPEC-03 §5). Prose goes through Docling's HybridChunker, sheets through our own
row grouping. The text that is embedded and stored is `<heading path>\n\n<body>`."""

import re
from functools import lru_cache
from typing import Any, Protocol

from app.config import Settings
from app.ingestion.parsers.xlsx import Sheet
from app.ingestion.types import ChunkDraft

PATH_SEP = " > "
BGE_M3_LIMIT = 8192
SECTION_NUMBER = re.compile(r"^(\d+(?:\.\d+)*)[.)]?\s")


class TokenCounter(Protocol):
    def count(self, text: str) -> int: ...


class WhitespaceCounter:
    """Test double: one token per whitespace-separated word."""

    def count(self, text: str) -> int:
        return len(text.split())


@lru_cache
def hf_tokenizer(tokenizer_id: str) -> Any:
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(tokenizer_id)


class HfCounter:
    """The embedding model's own tokenizer, so `token_count` matches what the provider counts (§5.3).

    Loaded on first use (or `warm()`), so processes that never chunk do not pay for it.
    """

    def __init__(self, tokenizer_id: str) -> None:
        self._id = tokenizer_id

    def warm(self) -> None:
        hf_tokenizer(self._id)

    def count(self, text: str) -> int:
        return len(hf_tokenizer(self._id).encode(text, add_special_tokens=False))


def hf_counter(settings: Settings) -> HfCounter:
    return HfCounter(settings.tokenizer_id)


def with_prefix(heading_path: list[str], body: str) -> str:
    return f"{PATH_SEP.join(heading_path)}\n\n{body}" if heading_path else body


def make_draft(
    chunk_type: str, heading_path: list[str], body: str, counter: TokenCounter, **where: Any
) -> ChunkDraft:
    text = with_prefix(heading_path, body)
    return ChunkDraft(
        chunk_type=chunk_type,
        text=text,
        heading_path=heading_path,
        token_count=min(counter.count(text), BGE_M3_LIMIT),
        **where,
    )


# --- Spreadsheets (§5.2) ---


def _md_row(cells: list[str]) -> str:
    return "| " + " | ".join(c.replace("|", r"\|").replace("\n", " ") for c in cells) + " |"


def _table_block(header: list[str], rows: list[list[str]]) -> str:
    table = [_md_row(header), _md_row(["---"] * len(header)), *(_md_row(r) for r in rows)]
    lookups = ["; ".join(f"{h}: {v}" for h, v in zip(header, row, strict=False) if v) for row in rows]
    return "\n".join(table) + "\n\n" + "\n".join(lookups)


def chunk_sheets(
    title: str, sheets: list[Sheet], counter: TokenCounter, *, rows_per_chunk: int, max_tokens: int
) -> list[ChunkDraft]:
    """A text chunk for a sheet's notes, then row groups: header repeated plus `Header: value` lines."""
    out: list[ChunkDraft] = []
    for sheet in sheets:
        path = [title, sheet.name]
        notes = [*sheet.preamble, *(f"{label}: {value}" for label, value in sheet.pairs)]
        if notes:
            out.append(make_draft("text", path, "\n".join(notes), counter, sheet=sheet.name))
        pending: list[list[str]] = []

        def flush(sheet: Sheet = sheet, path: list[str] = path, pending: list[list[str]] = pending) -> None:
            if pending:
                out.append(
                    make_draft(
                        "table_rows", path, _table_block(sheet.header, pending), counter, sheet=sheet.name
                    )
                )
                pending.clear()

        for row in sheet.rows:
            candidate = [*pending, row]
            too_big = counter.count(_table_block(sheet.header, candidate)) > max_tokens
            if pending and (len(candidate) > rows_per_chunk or too_big):
                flush()
            pending.append(row)
        flush()
    return out


def section_number(heading: str) -> str | None:
    match = SECTION_NUMBER.match(heading.strip())
    return match.group(1) if match else None
