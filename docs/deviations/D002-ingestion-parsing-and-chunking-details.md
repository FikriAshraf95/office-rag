# D002 - Ingestion parsing and chunking differ from SPEC-03 in six details

- **Date / milestone:** 2026-11-20 · M02
- **Spec:** [SPEC-03 §4, §5.1, §5.2, §6](../specs/SPEC-03-ingestion.md)
- **Status:** Resolved → spec updated (folded at M99, 2026-11-21)

## Spec says
1. §5.1: adjacent tiny sections (< 60 tokens) under the same parent are merged; an oversize section is split at paragraph boundaries.
2. §4: OCR is on only for PDF pages with no text layer.
3. §6: `title` falls back to the PDF title before the first H1.
4. §5.2: the header row is the first row with >= 2 non-empty string cells whose next row has values.
5. §4: Markdown front matter is read with `yaml.safe_load`.
6. §4: Docling reads Markdown with its Markdown backend.

## Implementation does
1. Uses Docling's `HybridChunker` with `merge_peers=True` and `repeat_table_header=True` as is. It merges undersized *peer* chunks (same headings) up to `CHUNK_MAX_TOKENS`, with no 60-token threshold, and splits only at document-item boundaries, then by tokens inside one oversize item. Short heading-only chunks (for example "Contents", about 50 tokens) stay as their own chunk.
2. Turns Docling OCR on for every PDF and image (`do_ocr=True`, no full-page forcing). Docling OCRs bitmap regions, so a scanned page is read, but there is no per-page "has a text layer" gate.
3. Does not read the PDF title property. The order is form, front matter, DOCX core title, first title/H1, filename.
4. Needs >= 3 non-empty string header cells. Two-column sheets (label and value, such as the entitlement calculator) are emitted as `Label: value` lines, which is what §5.2 asks for calculator sheets. A genuine two-column table gets the same lines instead of a Markdown table.
5. Uses `yaml.safe_load` first. If the block is not valid YAML (the sample `Travel_and_Claims_SOP.md` has `owner: Finance (Finance Manager: Kumar Selvam)`), it falls back to a plain `key: value` line reader with string values. Nothing is ever executed.
6. Strips the front matter and hands the body to Docling as an in-memory stream, so the front matter is not indexed as text.

## Why
1. Re-implementing merge and split rules over Docling's output would duplicate the chunker for little gain in a demo; the section structure, heading path and page numbers are what retrieval needs.
2. Docling 2.x has no page-level text-layer switch; the default bitmap OCR gives the same result for the demo files.
3. Docling does not expose the PDF title, and the sample PDFs open with a real title heading.
4. The calculator sheet is two columns and would otherwise be taken for a table with the header "Grade band | Manager".
5. The sample file is invalid YAML as written; dropping all its metadata would break SPEC-03 §10 check 12.
6. Front matter in the index would make every Markdown document match on its own metadata.

## Consequences
- A few short heading-only chunks exist; they cost little and rank low.
- A scanned page inside a mostly-digital PDF is OCRed too (slower, not wrong).
- Fold into SPEC-03 at M99: §5.1 "HybridChunker defaults (merge_peers) replace the 60-token rule", §4 "OCR on for every PDF and image", §5.2 "header needs >= 3 cells", §4 front-matter fallback. Revisit item 1 if the M06 eval shows heading-only chunks hurting retrieval.
