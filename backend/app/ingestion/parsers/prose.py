"""Prose chunking through Docling's HybridChunker (SPEC-03 §5.1). Docling is imported only under parsers/."""

from typing import Any

from app.config import Settings
from app.ingestion.chunking import TokenCounter, hf_tokenizer, make_draft, section_number
from app.ingestion.types import ChunkDraft


def _page_range(chunk: Any) -> tuple[int | None, int | None]:
    pages = [p.page_no for item in chunk.meta.doc_items for p in getattr(item, "prov", [])]
    return (min(pages), max(pages)) if pages else (None, None)


def _is_table_only(chunk: Any) -> bool:
    labels = {str(getattr(item.label, "value", item.label)) for item in chunk.meta.doc_items}
    return labels == {"table"}


def chunk_docling(
    doc: Any,
    title: str,
    counter: TokenCounter,
    settings: Settings,
    *,
    tokenizer: Any | None = None,
) -> list[ChunkDraft]:
    """Chunk a DoclingDocument by heading section (embedding tokenizer); tables become Markdown."""
    from docling_core.transforms.chunker.hierarchical_chunker import (
        ChunkingDocSerializer,
        ChunkingSerializerProvider,
    )
    from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
    from docling_core.transforms.serializer.markdown import MarkdownTableSerializer

    class MarkdownTables(ChunkingSerializerProvider):
        def get_serializer(self, doc: Any) -> ChunkingDocSerializer:
            return ChunkingDocSerializer(doc=doc, table_serializer=MarkdownTableSerializer())

    hf = tokenizer if tokenizer is not None else hf_tokenizer(settings.tokenizer_id)
    chunker = HybridChunker(
        tokenizer=HuggingFaceTokenizer(tokenizer=hf, max_tokens=settings.chunk_max_tokens),
        merge_peers=True,
        repeat_table_header=True,
        serializer_provider=MarkdownTables(),
    )
    out: list[ChunkDraft] = []
    for chunk in chunker.chunk(dl_doc=doc):
        body = chunk.text.strip()
        if not body:
            continue
        headings = [h.strip() for h in (getattr(chunk.meta, "headings", None) or []) if h.strip()]
        if headings and headings[0].lower() == title.lower():
            headings = headings[1:]
        path = [title, *headings]
        start, end = _page_range(chunk)
        kind = "table" if _is_table_only(chunk) else "text"
        out.append(
            make_draft(
                kind,
                path,
                body,
                counter,
                section=section_number(headings[-1]) if headings else None,
                page_start=start,
                page_end=end,
            )
        )
    return out
