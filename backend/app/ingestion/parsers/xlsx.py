"""XLSX parser (SPEC-03 §4, §5.2): openpyxl with cached formula values. Docling is not used here."""

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import structlog
from openpyxl import load_workbook

from app.ingestion.types import IngestError

log = structlog.get_logger()

NO_VALUE = "(formula, no value)"
MIN_HEADER_CELLS = 3


@dataclass(slots=True)
class Sheet:
    name: str
    preamble: list[str] = field(default_factory=list)  # lines above the header (titles, notes)
    header: list[str] = field(default_factory=list)  # empty: no table, `pairs` holds Label: value lines
    rows: list[list[str]] = field(default_factory=list)
    pairs: list[tuple[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class ParsedWorkbook:
    title: str | None
    sheets: list[Sheet]


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, datetime):
        return value.date().isoformat() if value.time().isoformat() == "00:00:00" else value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _find_header(rows: list[list[str]], raw: list[list[Any]]) -> int | None:
    """First row with several non-empty text cells whose next row has values (SPEC-03 §5.2)."""
    for i in range(len(rows) - 1):
        if sum(_is_text(v) for v in raw[i]) >= MIN_HEADER_CELLS and any(rows[i + 1]):
            return i
    return None


def _sheet(name: str, values: list[list[Any]], formulas: list[list[Any]], warnings: list[int]) -> Sheet:
    texts: list[list[str]] = []
    for r, row in enumerate(values):
        cells = []
        for c, value in enumerate(row):
            formula = formulas[r][c] if r < len(formulas) and c < len(formulas[r]) else None
            if value is None and isinstance(formula, str) and formula.startswith("="):
                warnings.append(1)
                cells.append(NO_VALUE)
            else:
                cells.append(_text(value))
        texts.append(cells)
    while texts and not any(texts[-1]):
        texts.pop()
        values.pop()
    sheet = Sheet(name=name)
    header_at = _find_header(texts, values)
    if header_at is None:
        # Calculator or notes: every non-empty row is `Label: value`, or a lone line.
        for row in texts:
            cells = [c for c in row if c]
            if len(cells) >= 2:
                sheet.pairs.append((cells[0], "; ".join(cells[1:])))
            elif cells:
                sheet.preamble.append(cells[0])
        return sheet
    sheet.preamble = [" ".join(c for c in row if c) for row in texts[:header_at] if any(row)]
    width = max(i for i, h in enumerate(texts[header_at]) if h) + 1
    sheet.header = [h or f"Column {i + 1}" for i, h in enumerate(texts[header_at][:width])]
    sheet.rows = [row[:width] + [""] * (width - len(row)) for row in texts[header_at + 1 :] if any(row)]
    return sheet


def parse_xlsx(path: Path) -> ParsedWorkbook:
    try:
        cached = load_workbook(path, data_only=True)
        formulas = load_workbook(path, data_only=False)
    except Exception as exc:
        raise IngestError(
            "parse", "This spreadsheet could not be read. Check that the file is not damaged."
        ) from exc
    warnings: list[int] = []
    sheets = []
    for ws in cached.worksheets:
        values = [list(row) for row in ws.iter_rows(values_only=True)]
        formula_ws = formulas[ws.title]
        formula_values = [list(row) for row in formula_ws.iter_rows(values_only=True)]
        sheets.append(_sheet(ws.title, values, formula_values, warnings))
    if warnings:
        log.warning("xlsx_formula_without_value", count=len(warnings))
    title = (cached.properties.title or "").strip() or None
    cached.close()
    formulas.close()
    return ParsedWorkbook(title=title, sheets=sheets)
