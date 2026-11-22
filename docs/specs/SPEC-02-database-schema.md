# SPEC-02 — Database schema

> **Status:** v1 (2026-11-19) · **Owner of:** every table, index and extension
> PostgreSQL 17 + pgvector ≥ 0.8 (`pgvector/pgvector:pg17`). Migrations with Alembic, named `M<nn>_<topic>`.

## 1. Extensions

`CREATE EXTENSION IF NOT EXISTS vector;` and `CREATE EXTENSION IF NOT EXISTS pgcrypto;` (for `gen_random_uuid()`), both in `M00_initial`.

`M00_initial` also creates one helper function, because `array_to_string` is only `STABLE` and Postgres rejects it in a generated column:

```sql
CREATE FUNCTION immutable_array_to_string(text[]) RETURNS text
  LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$ SELECT array_to_string($1, ' ') $$;
```

## 2. `documents`

| Column | Type | Rules |
|---|---|---|
| `id` | uuid PK | `gen_random_uuid()` |
| `title` | text not null | From upload form, else file metadata/first heading, else the filename without extension |
| `filename` | text not null | Sanitized original name ([SPEC-09 §2](SPEC-09-security-and-access.md)) |
| `content_type` | text not null | Detected from bytes, not the browser |
| `file_type` | text not null | `pdf`, `docx`, `xlsx`, `md`, `png`, `jpg` |
| `size_bytes` | bigint not null | |
| `sha256` | char(64) not null | Content hash |
| `storage_path` | text not null | Relative to `STORAGE_DIR` (`<id>/<filename>`) |
| `doc_type` | text not null default `'other'` | `policy`, `handbook`, `memo`, `sop`, `spreadsheet`, `notice`, `chart`, `other` |
| `department` | text null | Free text, e.g. `HR`, `Finance`, `IT` |
| `effective_date` | date null | From form, metadata or text ([SPEC-03 §6](SPEC-03-ingestion.md)) |
| `version` | text null | |
| `language` | text null | `en`, `ms`, `mixed` |
| `status` | text not null default `'current'` | `current` \| `superseded` (check constraint) |
| `access_groups` | text[] not null default `'{all}'` | Never empty (check constraint `cardinality(access_groups) > 0`) |
| `page_count` | int null | |
| `summary` | text null | M07 |
| `tags` | text[] not null default `'{}'` | M07 |
| `ingest_status` | text not null default `'queued'` | `queued`, `processing`, `ready`, `failed` (check constraint) |
| `ingest_error_code` | text null | `quota`, `rate_limit`, `parse`, `empty`, `provider`, `unknown` |
| `ingest_error` | text null | Human-readable, no secrets |
| `chunk_count` | int not null default 0 | |
| `uploaded_by` | text not null | Demo user id |
| `created_at`, `updated_at` | timestamptz not null default now() | |
| `deleted_at` | timestamptz null | Soft delete; chunks are hard-deleted |

Indexes: unique `(sha256) WHERE deleted_at IS NULL`; `(status)`; GIN `(access_groups)`; `(created_at DESC)`.

## 3. `chunks`

| Column | Type | Rules |
|---|---|---|
| `id` | uuid PK | |
| `document_id` | uuid not null FK → documents ON DELETE CASCADE | |
| `ordinal` | int not null | Order within the document; unique with `document_id` |
| `chunk_type` | text not null | `text`, `table`, `table_rows`, `image_text` |
| `text` | text not null | What is embedded and shown: heading prefix + body ([SPEC-03 §5.1](SPEC-03-ingestion.md)), including repeated table headers |
| `heading_path` | text[] not null default `'{}'` | Always starts with the document title, e.g. `{HR Employee Handbook 2026, 4. Leave, 4.2 Applying for leave}` |
| `section` | text null | Section number if found, e.g. `4.2` |
| `page_start`, `page_end` | int null | 1-based; null for formats without pages |
| `sheet` | text null | XLSX sheet name |
| `token_count` | int not null | |
| `embedding` | vector(1024) null | Null until embedded |
| `embedding_model` | text null | e.g. `bge-m3`; never mix models in one search ([SPEC-06 §7](SPEC-06-ai-providers.md)) |
| `doc_status` | text not null | **Denormalized** copy of `documents.status` |
| `access_groups` | text[] not null | **Denormalized** copy of `documents.access_groups` |
| `tsv` | tsvector | Generated, stored: `setweight(to_tsvector('english', immutable_array_to_string(heading_path)), 'A') \|\| to_tsvector('english', text) \|\| to_tsvector('simple', text)` |
| `created_at` | timestamptz not null default now() | |

The denormalized `doc_status` and `access_groups` are kept in step by `ingestion/service.py` in the **same transaction** as any document change. They exist so both search arms filter on the chunk row before ranking.

Indexes: HNSW `(embedding vector_cosine_ops)` with `m = 16, ef_construction = 64`; GIN `(tsv)`; GIN `(access_groups)`; `(document_id, ordinal)` unique; `(doc_status)`.

`english` + `simple` together: English stemming for English text, and `simple` keeps Malay words and codes (form numbers, grades like `M2`) intact.

## 4. `jobs`

| Column | Type | Rules |
|---|---|---|
| `id` | bigserial PK | |
| `kind` | text not null | `ingest_document`, `reembed` (M99) |
| `document_id` | uuid null FK → documents ON DELETE CASCADE | |
| `payload` | jsonb not null default `'{}'` | |
| `status` | text not null default `'queued'` | `queued`, `running`, `done`, `failed` |
| `attempts` | int not null default 0 | |
| `max_attempts` | int not null default 3 | |
| `run_after` | timestamptz not null default now() | Backoff target |
| `locked_by` | text null | Worker id |
| `locked_at` | timestamptz null | Stale after 15 min → requeued |
| `error_code`, `error` | text null | Same codes as `documents.ingest_error_code` |
| `created_at` | timestamptz not null default now() | |
| `finished_at` | timestamptz null | |

Index: `(status, run_after) WHERE status = 'queued'`. A trigger runs `pg_notify('jobs_new', id::text)` on insert.

## 5. `questions`

One row per chat question (for the eval, usage per question and later "unanswered questions" analytics).

| Column | Type | Rules |
|---|---|---|
| `id` | uuid PK | |
| `user_id` | text not null | |
| `question` | text not null | |
| `answer` | text null | Final text after citation checks |
| `found` | boolean null | False for the not-found answer |
| `sources` | jsonb not null default `'[]'` | The numbered sources sent to the model (ids, titles, pages; no chunk text) |
| `cited` | int[] not null default `'{}'` | The `[n]` numbers that survived validation |
| `model` | text null | |
| `latency_ms` | int null | Total |
| `first_token_ms` | int null | |
| `error_code` | text null | |
| `created_at` | timestamptz not null default now() | |

## 6. `usage`

| Column | Type | Rules |
|---|---|---|
| `id` | bigserial PK | |
| `at` | timestamptz not null default now() | |
| `provider` | text not null | `ilmu`, `openai`, `azure`, `fake` |
| `model` | text not null | |
| `role` | text not null | `answer`, `fast`, `fallback`, `vision`, `embed`, `rerank`, `judge` |
| `purpose` | text not null | `question`, `ingestion`, `eval`, `reembed` |
| `ref_id` | text null | `questions.id` or `documents.id` |
| `prompt_tokens`, `completion_tokens`, `reasoning_tokens`, `total_tokens` | int not null default 0 | |
| `cost_myr` | numeric(12,6) null | From the price table; null for plan models (quota) |
| `latency_ms` | int not null | |
| `status` | text not null | `ok`, `error` |
| `error_code` | text null | [SPEC-06 §5](SPEC-06-ai-providers.md) codes |

Index: `(at DESC)`, `(purpose, model)`.

## 7. Table → milestone map

| Table / object | Created in | Changed in |
|---|---|---|
| extensions, `immutable_array_to_string()`, `documents`, `chunks`, `jobs`, `questions`, `usage` | M00 (`M00_initial`) | — |
| HNSW, GIN, tsv generated column | M00 | — |
| `documents.summary`, `documents.tags` filled | — (columns exist from M00) | M07 |
| Second embedding column or table for re-embed ([SPEC-06 §7](SPEC-06-ai-providers.md)) | — | M99, only if built; its shape is added to this spec in the same change |

## 8. Acceptance checks

1. `alembic upgrade head` on an empty database creates every table, column, index, constraint and function above; `alembic downgrade base` removes them.
2. Inserting a document with an empty `access_groups` array fails the check constraint.
3. Inserting a second non-deleted document with the same `sha256` fails the unique index.
4. `chunks.tsv` matches Malay words unchanged (`simple`) and stemmed English (`leaves` matches `leave`).
5. Inserting into `jobs` sends a `jobs_new` notification.
