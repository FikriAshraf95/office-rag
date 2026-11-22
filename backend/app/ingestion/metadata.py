"""Document metadata rules (SPEC-03 §6): pure functions over text and filenames, no I/O."""

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
VERSION_IN_NAME = re.compile(r"(?<![A-Za-z0-9])v(\d+(?:\.\d+)?)(?![A-Za-z0-9])", re.IGNORECASE)
EFFECTIVE = re.compile(
    r"(?:Effective(?:\s+date)?|Berkuat\s+kuasa)\s*:?\s*"
    r"(\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})",
    re.IGNORECASE,
)
SUPERSEDED = re.compile(r"\b(?:SUPERSEDED|DIGANTIKAN)\b")
SUPERSEDED_WINDOW = 2000

DOC_TYPE_KEYWORDS: list[tuple[str, str]] = [
    ("org_chart", "chart"),
    ("org chart", "chart"),
    ("handbook", "handbook"),
    ("memo", "memo"),
    ("sop", "sop"),
    ("policy", "policy"),
    ("notis", "notice"),
    ("notice", "notice"),
]

MONTHS = {
    name: i
    for i, names in enumerate(
        [
            ("jan", "january", "januari"),
            ("feb", "february", "februari"),
            ("mar", "march", "mac"),
            ("apr", "april"),
            ("may", "mei"),
            ("jun", "june"),
            ("jul", "july", "julai"),
            ("aug", "august", "ogos"),
            ("sep", "sept", "september"),
            ("oct", "october", "oktober"),
            ("nov", "november"),
            ("dec", "december", "disember"),
        ],
        start=1,
    )
    for name in names
}

MALAY_STOP_WORDS = frozenset(
    [
        "yang",
        "dan",
        "di",
        "ke",
        "dari",
        "untuk",
        "dengan",
        "ini",
        "itu",
        "pada",
        "adalah",
        "akan",
        "tidak",
        "oleh",
        "atau",
        "dalam",
        "kepada",
        "juga",
        "kami",
        "anda",
        "mereka",
        "telah",
        "boleh",
        "semua",
        "tahun",
        "hari",
        "bagi",
        "sebagai",
        "serta",
        "jika",
        "setiap",
        "apabila",
        "kakitangan",
        # Question words, so a short chat question in Malay is detected too (SPEC-05 §5).
        "saya",
        "adakah",
        "apakah",
        "berapa",
        "bagaimana",
        "bila",
        "siapa",
        "perlu",
    ]
)


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """YAML front matter (read with `safe_load`) and the body without it. A bad block falls back to lines."""
    text = text.replace(chr(13) + chr(10), chr(10))
    match = FRONT_MATTER.match(text)
    if match is None:
        return {}, text
    block = match.group(1)
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        data = _simple_pairs(block)  # e.g. `owner: Finance (Finance Manager: Kumar)` is not valid YAML
    return (data if isinstance(data, dict) else {}), text[match.end() :]


def _simple_pairs(block: str) -> dict[str, str]:
    """Lenient fallback: one `key: value` per line, values kept as plain strings."""
    pairs = (line.split(":", 1) for line in block.splitlines() if re.match(r"[A-Za-z_][\w-]*\s*:", line))
    return {key.strip(): value.strip() for key, value in pairs}


def parse_date(value: Any) -> date | None:
    """A `date`, ISO `2026-02-01`, `1 January 2026` or `January 1, 2026`; None when unreadable."""
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    raw = value.strip().rstrip(".")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None
    for pattern, order in (
        (r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", "dmy"),
        (r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", "mdy"),
    ):
        if m := re.fullmatch(pattern, raw):
            day, month_name, year = (m[1], m[2], m[3]) if order == "dmy" else (m[2], m[1], m[3])
            month = MONTHS.get(month_name.lower())
            if month is None:
                return None
            try:
                return date(int(year), month, int(day))
            except ValueError:
                return None
    return None


def find_effective_date(text: str) -> date | None:
    """First `Effective: <date>` / `Berkuat kuasa <date>` in the text (callers pass the first page)."""
    for match in EFFECTIVE.finditer(text):
        if (parsed := parse_date(match.group(1))) is not None:
            return parsed
    return None


def is_superseded(text: str) -> bool:
    """SPEC-03 §6.1: whole word SUPERSEDED (case-sensitive) or DIGANTIKAN in the first 2,000 characters."""
    return SUPERSEDED.search(text[:SUPERSEDED_WINDOW]) is not None


def version_from_filename(filename: str) -> str | None:
    match = VERSION_IN_NAME.search(Path(filename).stem)
    return f"v{match.group(1)}" if match else None


def doc_type_from_filename(filename: str) -> str:
    if Path(filename).suffix.lower() == ".xlsx":
        return "spreadsheet"
    lowered = Path(filename).stem.lower().replace("_", " ")
    for keyword, doc_type in DOC_TYPE_KEYWORDS:
        if re.search(rf"(?<![a-z]){keyword}(?![a-z])", lowered):
            return doc_type
    return "other"


def title_from_filename(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").strip() or filename


def department_from_owner(owner: Any) -> str | None:
    """First word of the front-matter `owner` (`Finance (Finance Manager: Kumar)` -> `Finance`)."""
    if not isinstance(owner, str):
        return None
    words = owner.split()
    return words[0].strip(",;:()") if words else None


def detect_language(text: str) -> str:
    """`ms` when >= 30% of words are Malay stop words, `mixed` from 10%, else `en` (SPEC-03 §6)."""
    words = re.findall(r"[A-Za-z]+", text.lower())
    if not words:
        return "en"
    share = sum(1 for w in words if w in MALAY_STOP_WORDS) / len(words)
    if share >= 0.30:
        return "ms"
    if share >= 0.10:
        return "mixed"
    return "en"


def resolve_title(current: str, filename: str, from_file: str | None) -> str:
    """The upload form's title wins; a title still equal to the filename default may be replaced (§6)."""
    return from_file if from_file and current == title_from_filename(filename) else current
