# D008 — Vision fallback covers standalone images only; summary is best-effort

- **Date / milestone:** 2026-11-21 · M07
- **Spec:** [SPEC-03 §8](../specs/SPEC-03-ingestion.md#8-images-and-vision-fallback-m07), [M07](../milestones/done/M07-vision-and-summaries.md)
- **Status:** Resolved → spec updated (folded at M99, 2026-11-21)

## Spec says
- Vision fallback applies to images and to picture elements in PDFs classified as diagrams (Docling picture classification, or filename `chart`/`diagram`).
- One `fast` call per document for `summary` and `tags`.

## Implementation does
- Vision runs for PNG/JPG only, when OCR text is shorter than `OCR_MIN_CHARS` or the filename contains `chart`/`diagram`. No Docling picture classification, and no vision for pictures inside PDFs.
- The vision result replaces the OCR chunks with one `image_text` chunk (OCR text, `--- description ---`, vision text). An image with no OCR text is no longer failed as `empty` until vision has also returned nothing.
- The summary call is soft: a provider error leaves `summary` empty and `tags` `[]`; it never fails or retries the job. Each ingestion overwrites summary and tags.
- The orchestration lives in `app/ingestion/vision.py`, called from the worker (providers are async; `extract` runs in a thread).

## Why
- The org chart (the only vision-dependent eval documents, Q23-25) is a standalone image. Picture classification needs extra Docling models baked into the worker image and page-image cropping; not worth it for the demo.
- A summary is a nicety; a flaky `fast` model must not block ingestion.

## Consequences
- Diagrams embedded in PDFs are still read as text only. Revisit if a demo document needs it.
- Ingesting a document now writes one more `usage` row (`fast`, `ingestion`).
