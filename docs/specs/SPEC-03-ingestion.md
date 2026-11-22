# SPEC-03 — Ingestion

> **Status:** v1 (2026-11-19) · **Owner of:** upload flow, the job queue, parsing per type, chunking, metadata, superseded detection, re-ingest, delete
> Tables: [SPEC-02 §2–4](SPEC-02-database-schema.md) · Endpoints: [SPEC-08 §4](SPEC-08-api-contract.md) · Validation: [SPEC-09 §2](SPEC-09-security-and-access.md)

## 1. Rules

1. **`app/ingestion/service.py` is the only writer** of `documents` and `chunks` (insert, update, delete).
2. Ingestion never runs inside a web request. Upload stores the file and enqueues a job; the worker does the rest.
3. Re-ingesting a document replaces all its chunks **in one transaction**: delete old chunks + insert new ones + update the document. A reader never sees a half-ingested document.
4. A document change to `status` or `access_groups` updates the denormalized copies on its chunks in the same transaction.
5. **The chunk swap at the end of a job re-reads the document under a row lock.** In the swap transaction the service runs `SELECT … FROM documents WHERE id = :id FOR UPDATE`, copies `status` and `access_groups` from that row **at that moment** onto the new chunks, and, if `deleted_at` is set, writes no chunks and marks the job `done`. A `PATCH` or delete during ingestion therefore can never be overwritten by a copy read when the job started.

## 2. Upload flow

1. Validate ([SPEC-09 §2](SPEC-09-security-and-access.md)): type by magic bytes, size ≤ `MAX_UPLOAD_MB` (default 25), sanitized filename.
2. Compute `sha256`. If a non-deleted document has the same hash → `409 duplicate_document`. The response carries `existingId` and the title **only if the caller can see that document**; otherwise it says only that the file is already uploaded (an id or title would reveal a document outside the caller's groups). A concurrent duplicate that trips the unique index maps to the same 409.
3. In one transaction: insert `documents` (`ingest_status = 'queued'`), write the file to `STORAGE_DIR/<id>/<filename>` (temp name, then rename), insert `jobs` (`kind = 'ingest_document'`).
4. Return `202` with the document.

If the transaction fails after the file is written, the file is deleted.

## 3. Job queue

- **Claim:** `UPDATE jobs SET status='running', locked_by=:w, locked_at=now(), attempts=attempts+1 WHERE id = (SELECT id FROM jobs WHERE status='queued' AND run_after <= now() ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *`.
- On claim the document goes to `ingest_status = 'processing'` (through the service, like every document write).
- **Success:** job `done`, document `ready`, `chunk_count` set, error cleared.
- **Retryable failure** (rate limit, 5xx, network; [SPEC-06 §5](SPEC-06-ai-providers.md)) with `attempts < max_attempts`: job back to `queued`, `run_after = now() + 30 s × 2^attempts`, document stays `processing`.
- **Quota exhausted** (plan quota 429 or PAYG 402): job `failed` with `error_code = 'quota'`, document `failed`, message *"The AI service quota is used up. Top up or wait for the next cycle, then select Retry."* No retry until the user re-ingests.
- **Other failures** (`parse`, `empty`, `provider`, `unknown`, and `rate_limit` once attempts are used up): job `failed`, document `failed` with the code and a short message.
- **Heartbeat:** while processing, the worker sets `locked_at = now()` on its job every minute, so a slow Docling run is never mistaken for a dead one.
- **Stale locks:** at worker start and every minute, jobs `running` with `locked_at < now() - 15 min` (no heartbeat for 15 min) go back to `queued`.

## 4. Parsing per file type

All parsing is in `app/ingestion/parsers/`, one function per type returning a list of **blocks** (`kind`, `text`, `heading_path`, `section`, `page`, `sheet`, `table` rows if any), plus document-level metadata.

| Type | Parser | Notes |
|---|---|---|
| PDF | Docling `DocumentConverter` (layout + table structure; `do_ocr=True` for every PDF: Docling OCRs bitmap regions, so a scanned page is read; there is no per-page text-layer switch) | Keep headings, lists and tables. Page numbers from provenance. |
| DOCX | Docling | Headings from Word styles; numbered sections keep their numbers in `section`. |
| Markdown | Front matter stripped, then the body goes to Docling (Markdown backend) as an in-memory stream, so front matter is never indexed as text. Front matter is read with `yaml.safe_load`; if the block is not valid YAML, a plain `key: value` line reader with string values is used instead (nothing is ever executed) | Front matter gives `title`, `version`, `effective`, `owner`/department. |
| XLSX | `openpyxl` with `data_only=True` (cached formula values) | See §5.2. Docling is not used: we need the header-per-chunk control. |
| PNG / JPG | Docling image pipeline with RapidOCR | If OCR text is shorter than `OCR_MIN_CHARS` (default 80) or the filename contains `chart`/`diagram` → M07 vision fallback ([§8](#8-images-and-vision-fallback-m07)). Before M07: keep what OCR found; if nothing, fail with `empty`. |

Docling runs with `artifacts_path` pointing at models baked into the worker image ([SPEC-11 §2](SPEC-11-deployment.md)); it never downloads at runtime in Compose.

## 5. Chunking

### 5.1 Prose (PDF, DOCX, MD, OCR text)
- Chunk **by structure**: one chunk per smallest heading section, using Docling's `HybridChunker` (docling-core `chunking` extra) with the `BAAI/bge-m3` tokenizer.
- `CHUNK_MAX_TOKENS = 800`. `HybridChunker` runs with `merge_peers=True` and `repeat_table_header=True`: undersized *peer* chunks (same headings) are merged up to the limit; an oversize section is split at document-item boundaries, then by tokens inside one oversize item. Each piece keeps the same `heading_path` and `section`. Short heading-only chunks (e.g. "Contents") may stay on their own; they rank low.
- **Text that is embedded** (and stored in `chunks.text`) = `"<heading_path joined with ' > '>\n\n<body>"`. `heading_path` always starts with the document title, so the title appears once. The heading context is part of the vector and of the full-text index.
- Tables inside prose become a Markdown table chunk (`chunk_type = 'table'`) with the heading path of the section that holds them. A table over the limit is split by rows with the header row repeated.

### 5.2 Spreadsheets (XLSX)
- Each sheet: find the header row (the first row where ≥ 3 cells are non-empty strings and the next row has values). Rows above the header (title lines, notes) become a short `text` chunk for the sheet. A sheet with no such row (e.g. a two-column label/value calculator) is emitted as `Label: value` lines; a genuine two-column table gets the same lines instead of a Markdown table.
- Data rows are grouped into chunks of up to `XLSX_ROWS_PER_CHUNK = 20`, each rendered as a Markdown table **with the header row repeated** (`chunk_type = 'table_rows'`, `sheet` set, `heading_path = {title, sheet name}`).
- Also add one line per row in `"Header: value; Header: value"` form below the table. This makes exact lookups (`Manager | More than 5 years | 22`) match both full-text and vector search.
- Formula cells use the cached value. A formula cell with no cached value is written as `(formula, no value)`; ingestion logs a warning, not a failure.
- Calculator sheets (cells with inputs and formulas, no table) are emitted as `Label: value` lines.

### 5.3 Token counting
`token_count` uses the same tokenizer as the chunker. A chunk is never above 8,192 tokens (the bge-m3 limit).

## 6. Metadata

| Field | Source, in priority order |
|---|---|
| `title` | Upload form → MD front matter `title` / DOCX core title → first title/H1 → filename without extension, underscores to spaces (the PDF title property is not read: Docling doesn't expose it) |
| `effective_date` | Upload form → front matter `effective` → first match of `Effective( date)?:? <date>` / `Berkuat kuasa` in the first page → null |
| `version` | Form → front matter `version` → `v\d+(\.\d+)?` in the filename → null |
| `department` | Form → front matter `owner` (first word) → null |
| `doc_type` | Form → filename keywords (`Handbook`→handbook, `Memo`→memo, `SOP`→sop, `Policy`→policy, `Notis`/`Notice`→notice, `Org_Chart`→chart, `.xlsx`→spreadsheet) → `other` |
| `language` | `ms` if ≥ 30% of words hit a small Malay stop-word list, `mixed` if 10–30%, else `en` |
| `page_count` | Docling (PDF), else null |

### 6.1 Superseded detection
- If the first page (or first 2,000 characters) contains the word `SUPERSEDED` (case-sensitive, whole word) or `DIGANTIKAN`, set `status = 'superseded'` when the job finishes. This happens **only on the first ingestion**: a re-ingest keeps the current `status`, so a manual change sticks.
- Users can change `status` at any time (`PATCH`); that update goes through the service and updates chunks.
- Uploading a document with the same title as a current one does **not** auto-supersede (titles collide too easily). The UI offers the action instead (M05).

## 7. Re-ingest and delete

- `POST /documents/{id}/reingest`: enqueue a new job; chunks stay searchable until the new set replaces them in one transaction.
- Re-upload of a changed file under the same title is a new document (different hash). `POST /documents/{id}/file` (M08, [SPEC-08 §4.8](SPEC-08-api-contract.md)) replaces the file of the same document: new hash, new filename, same id, then a re-ingest job.
- `DELETE /documents/{id}`: set `deleted_at`, delete chunks, delete the stored file, cancel queued jobs. One transaction for the DB part; the file is deleted after commit. A job already running finds `deleted_at` set at its swap and writes nothing (§1 rule 5).

## 8. Images and vision fallback (M07)

- **Standalone PNG/JPG only.** When OCR text is shorter than `OCR_MIN_CHARS` or the filename contains `chart`/`diagram`, send the image to the `vision` role (image input as a base64 data URI, ≤ 20 MB). Pictures inside PDFs are not sent to vision, and there is no Docling picture classification (it would need extra baked models and page-image cropping).
- The instruction (`VISION_INSTRUCTION` in `app/ingestion/vision.py`, verbatim): *"Extract all text, including captions and labels outside the boxes. Then describe the structure. For org charts, write one line per person, top to bottom, in exactly this form: "&lt;Name&gt;, &lt;Title&gt; - reports to &lt;Name&gt;, &lt;Title&gt;" ("- reports to no one" for the top person). Then, for every caption or label that is not inside a box (such as a team name or staff count), add one line "Label directly below the box of &lt;Name&gt;, &lt;Title&gt;: &lt;label text&gt;", naming the box it sits closest to. Do not add anything not visible."* Labels are tied to a box by position only, never by inferred leadership (eval Q24). A changed instruction needs a re-ingest of the images.
- The result replaces the OCR chunks with one `chunk_type = 'image_text'` chunk: OCR text first, then a `--- description ---` line, then the vision text. An image with no OCR text fails as `empty` only when vision also returned nothing.
- Vision usage is logged with `purpose = 'ingestion'`. The orchestration lives in `app/ingestion/vision.py`, called from the worker (providers are async; `extract` runs in a thread).
- One `fast`-role call per document for `summary` (≤ 60 words) and up to 5 `tags`. It is best-effort: a provider error leaves `summary` empty and `tags` `[]` and never fails or retries the job. Each ingestion overwrites both.

## 9. Embedding

- Batch up to `EMBED_BATCH = 64` chunks per `/embeddings` request.
- Store `embedding_model` with each chunk. Ingestion refuses to mix: if `EMBED_MODEL` differs from the model already used by existing chunks, the job fails with `provider` and a message pointing to the re-embed command ([SPEC-06 §7](SPEC-06-ai-providers.md)).

## 10. Acceptance checks

1. Uploading a valid PDF returns `202`, creates a document `queued` and one `jobs` row; the file exists under `STORAGE_DIR/<id>/`.
2. Uploading the same bytes again returns `409 duplicate_document` with the existing id.
3. Two workers never claim the same job (concurrent claim test).
4. After the worker runs, the document is `ready`, `chunk_count > 0`, every chunk has an embedding, `embedding_model`, `doc_status` and `access_groups` matching the document.
5. A PDF section chunk carries `heading_path`, `section` and `page_start`; the embedded text starts with the title and heading path.
6. An XLSX chunk repeats the header row and contains `Header: value` lines; `Leave_Entitlement_by_Grade_2026.xlsx` yields a chunk containing `22` beside `More than 5 years` for grade M2 (fixture copy).
7. A PDF whose first page says `SUPERSEDED` ends up `status = 'superseded'`, and its chunks have `doc_status = 'superseded'`.
8. A rate-limit error during embedding requeues the job with backoff; a quota error marks the document `failed` with `ingest_error_code = 'quota'` and does not retry.
9. Re-ingest swaps chunks atomically: a search running during re-ingest returns either the old or the new chunks, never none and never both.
10. Changing `access_groups` or `status` through `PATCH` updates every chunk of that document in the same transaction.
11. Delete removes chunks and the stored file, and the document disappears from lists and search.
12. Markdown front matter fills `title`, `version`, `effective_date` and `department` for `Travel_and_Claims_SOP.md`.
13. A `PATCH` that narrows `access_groups` while the document's job is running: after the job finishes, every chunk carries the new groups.
14. Deleting a document while its job is running leaves no chunks once the job finishes.
15. Uploading the bytes of a document outside the caller's groups returns `409 duplicate_document` with no `existingId` and no title.
16. A document whose first page says `SUPERSEDED`, set back to `current` by `PATCH`, stays `current` after a re-ingest.
17. A job whose worker keeps its heartbeat is not requeued after 15 minutes.
