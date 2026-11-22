"""Citation markers (SPEC-05 §4): `[n]`, `[n][m]` and `[n, m]`, numbered from the retrieved sources."""

import re

# One bracket of 1-3 digit numbers separated by commas; leading spaces go with it when it is removed.
MARKER = re.compile(r"([ \t]*)\[(\d{1,3}(?:\s*,\s*\d{1,3})*)\]")


def _numbers(group: str) -> list[int]:
    return [int(part) for part in group.split(",")]


def validate(text: str, source_count: int) -> tuple[str, list[int]]:
    """(text with markers outside 1..source_count removed, the valid numbers used, ascending)."""
    cited: set[int] = set()

    def keep_valid(match: re.Match[str]) -> str:
        valid = [n for n in _numbers(match.group(2)) if 1 <= n <= source_count]
        if not valid:
            return ""
        cited.update(valid)
        if len(valid) == len(_numbers(match.group(2))):
            return match.group(0)
        return f"{match.group(1)}[{', '.join(str(n) for n in valid)}]"

    return MARKER.sub(keep_valid, text), sorted(cited)


def strip_markers(text: str) -> str:
    """Text without any citation marker (history answers are context, never a source)."""
    return MARKER.sub("", text)
