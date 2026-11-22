"""Vision fallback for images and the optional summary + tags (SPEC-03 §8). Async: needs the providers, so it
runs in the worker after `extract`, never inside the parsing thread."""

import asyncio
import json
from pathlib import Path

import structlog

from app.ingestion.chunking import TokenCounter, make_draft
from app.ingestion.types import IngestResult
from app.providers.errors import ProviderError
from app.providers.registry import Providers

log = structlog.get_logger()

MAX_IMAGE_BYTES = 20 * 1024 * 1024
DESCRIPTION_MARK = "--- description ---"
MIME = {"png": "image/png", "jpg": "image/jpeg"}
# D009: the spec wording, made explicit about direction and about free-standing labels (team names, staff
# counts) under a box; without them "Finance team" never reaches the index. Labels are tied to a box by
# position only: asking who "leads" a label made the model attach it to the wrong level.
VISION_INSTRUCTION = (
    "Extract all text, including captions and labels outside the boxes. Then describe the structure. "
    "For org charts, write one line per person, top to bottom, in exactly this form: "
    '"<Name>, <Title> - reports to <Name>, <Title>" ("- reports to no one" for the top person). '
    "Then, for every caption or label that is not inside a box (such as a team name or staff count), add "
    'one line "Label directly below the box of <Name>, <Title>: <label text>", naming the box it sits '
    "closest to. Do not add anything not visible."
)
SUMMARY_PROMPT = (
    "Summarise the document below for a search index. Reply with JSON only: "
    '{"summary": "<at most 60 words, plain text>", "tags": ["<up to 5 short lowercase topic tags>"]}. '
    "Use only what the text says."
)
SUMMARY_INPUT_CHARS = 6000
MAX_SUMMARY_WORDS = 60
MAX_TAGS = 5
MAX_TAG_CHARS = 40


async def apply_vision(
    result: IngestResult,
    path: Path,
    *,
    title: str,
    filename: str,
    file_type: str,
    providers: Providers,
    counter: TokenCounter,
    doc_id: str,
) -> None:
    """Replace the OCR chunks with one `image_text` chunk: OCR text, then the vision description."""
    if not result.vision_candidate or file_type not in MIME:
        return
    image = await asyncio.to_thread(path.read_bytes)
    if len(image) > MAX_IMAGE_BYTES:
        log.warning("vision_skipped_too_large", document_id=doc_id)
        return
    reply = await providers.vision().describe(
        image,
        MIME[file_type],
        f"{filename}\n{VISION_INSTRUCTION}",  # first line is the filename (the fake echoes it)
        purpose="ingestion",
        ref_id=doc_id,
    )
    description = reply.text.strip()
    if not description:
        return
    body = f"{result.ocr_text}\n\n{DESCRIPTION_MARK}\n{description}" if result.ocr_text else description
    chunk = make_draft("image_text", [title], body, counter)
    result.chunks = [chunk]


def parse_summary(raw: str) -> tuple[str | None, list[str]]:
    """Tolerant reader for the `fast` model's JSON; anything unusable gives (None, [])."""
    try:
        data = json.loads(raw)
    except ValueError:
        return None, []
    if not isinstance(data, dict):
        return None, []
    summary = data.get("summary")
    words = summary.split() if isinstance(summary, str) else []
    text = " ".join(words[:MAX_SUMMARY_WORDS]) or None
    raw_tags = data.get("tags")
    tags: list[str] = []
    for tag in raw_tags if isinstance(raw_tags, list) else []:
        clean = tag.strip().lower()[:MAX_TAG_CHARS] if isinstance(tag, str) else ""
        if clean and clean not in tags:
            tags.append(clean)
    return text, tags[:MAX_TAGS]


async def apply_summary(result: IngestResult, *, title: str, providers: Providers, doc_id: str) -> None:
    """One `fast` call per document. Optional: a provider failure leaves summary and tags empty."""
    text = "\n\n".join(c.text for c in result.chunks)[:SUMMARY_INPUT_CHARS]
    if not text.strip():
        return
    try:
        reply = await providers.chat("fast").complete(
            [
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user", "content": f"Title: {title}\n\n{text}"},
            ],
            json_mode=True,
            max_tokens=300,
            purpose="ingestion",
            ref_id=doc_id,
        )
    except ProviderError as exc:
        log.warning("summary_failed", document_id=doc_id, code=exc.code)
        return
    result.summary, result.tags = parse_summary(reply.text)
