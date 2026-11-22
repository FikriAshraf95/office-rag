"""M00_initial: extensions, helper function, every SPEC-02 table, indexes and the jobs_new trigger.

Revision ID: m00_initial
Revises:
Create Date: 2026-11-20
"""

from collections.abc import Sequence

from alembic import op

revision: str = "m00_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    "CREATE EXTENSION IF NOT EXISTS pgcrypto",
    """
    CREATE FUNCTION immutable_array_to_string(text[]) RETURNS text
      LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$ SELECT array_to_string($1, ' ') $$
    """,
    """
    CREATE TABLE documents (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      title text NOT NULL,
      filename text NOT NULL,
      content_type text NOT NULL,
      file_type text NOT NULL,
      size_bytes bigint NOT NULL,
      sha256 char(64) NOT NULL,
      storage_path text NOT NULL,
      doc_type text NOT NULL DEFAULT 'other',
      department text,
      effective_date date,
      version text,
      language text,
      status text NOT NULL DEFAULT 'current',
      access_groups text[] NOT NULL DEFAULT '{all}',
      page_count int,
      summary text,
      tags text[] NOT NULL DEFAULT '{}',
      ingest_status text NOT NULL DEFAULT 'queued',
      ingest_error_code text,
      ingest_error text,
      chunk_count int NOT NULL DEFAULT 0,
      uploaded_by text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      deleted_at timestamptz,
      CONSTRAINT ck_documents_status CHECK (status IN ('current', 'superseded')),
      CONSTRAINT ck_documents_access_groups_not_empty CHECK (cardinality(access_groups) > 0),
      CONSTRAINT ck_documents_ingest_status
        CHECK (ingest_status IN ('queued', 'processing', 'ready', 'failed'))
    )
    """,
    "CREATE UNIQUE INDEX uq_documents_sha256_live ON documents (sha256) WHERE deleted_at IS NULL",
    "CREATE INDEX ix_documents_status ON documents (status)",
    "CREATE INDEX ix_documents_access_groups ON documents USING gin (access_groups)",
    "CREATE INDEX ix_documents_created_at ON documents (created_at DESC)",
    """
    CREATE TABLE chunks (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      document_id uuid NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
      ordinal int NOT NULL,
      chunk_type text NOT NULL,
      text text NOT NULL,
      heading_path text[] NOT NULL DEFAULT '{}',
      section text,
      page_start int,
      page_end int,
      sheet text,
      token_count int NOT NULL,
      embedding vector(1024),
      embedding_model text,
      doc_status text NOT NULL,
      access_groups text[] NOT NULL,
      tsv tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', immutable_array_to_string(heading_path)), 'A')
        || to_tsvector('english', text) || to_tsvector('simple', text)
      ) STORED,
      created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX ix_chunks_embedding_hnsw ON chunks
      USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)
    """,
    "CREATE INDEX ix_chunks_tsv ON chunks USING gin (tsv)",
    "CREATE INDEX ix_chunks_access_groups ON chunks USING gin (access_groups)",
    "CREATE UNIQUE INDEX uq_chunks_document_ordinal ON chunks (document_id, ordinal)",
    "CREATE INDEX ix_chunks_doc_status ON chunks (doc_status)",
    """
    CREATE TABLE jobs (
      id bigserial PRIMARY KEY,
      kind text NOT NULL,
      document_id uuid REFERENCES documents (id) ON DELETE CASCADE,
      payload jsonb NOT NULL DEFAULT '{}',
      status text NOT NULL DEFAULT 'queued',
      attempts int NOT NULL DEFAULT 0,
      max_attempts int NOT NULL DEFAULT 3,
      run_after timestamptz NOT NULL DEFAULT now(),
      locked_by text,
      locked_at timestamptz,
      error_code text,
      error text,
      created_at timestamptz NOT NULL DEFAULT now(),
      finished_at timestamptz
    )
    """,
    "CREATE INDEX ix_jobs_queued ON jobs (status, run_after) WHERE status = 'queued'",
    """
    CREATE FUNCTION jobs_notify_new() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      PERFORM pg_notify('jobs_new', NEW.id::text);
      RETURN NEW;
    END
    $$
    """,
    "CREATE TRIGGER jobs_new AFTER INSERT ON jobs FOR EACH ROW EXECUTE FUNCTION jobs_notify_new()",
    """
    CREATE TABLE questions (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id text NOT NULL,
      question text NOT NULL,
      answer text,
      found boolean,
      sources jsonb NOT NULL DEFAULT '[]',
      cited int[] NOT NULL DEFAULT '{}',
      model text,
      latency_ms int,
      first_token_ms int,
      error_code text,
      created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE usage (
      id bigserial PRIMARY KEY,
      at timestamptz NOT NULL DEFAULT now(),
      provider text NOT NULL,
      model text NOT NULL,
      role text NOT NULL,
      purpose text NOT NULL,
      ref_id text,
      prompt_tokens int NOT NULL DEFAULT 0,
      completion_tokens int NOT NULL DEFAULT 0,
      reasoning_tokens int NOT NULL DEFAULT 0,
      total_tokens int NOT NULL DEFAULT 0,
      cost_myr numeric(12, 6),
      latency_ms int NOT NULL,
      status text NOT NULL,
      error_code text
    )
    """,
    "CREATE INDEX ix_usage_at ON usage (at DESC)",
    "CREATE INDEX ix_usage_purpose_model ON usage (purpose, model)",
]

DOWNGRADE = [
    "DROP TABLE IF EXISTS usage",
    "DROP TABLE IF EXISTS questions",
    "DROP TRIGGER IF EXISTS jobs_new ON jobs",
    "DROP TABLE IF EXISTS jobs",
    "DROP FUNCTION IF EXISTS jobs_notify_new()",
    "DROP TABLE IF EXISTS chunks",
    "DROP TABLE IF EXISTS documents",
    "DROP FUNCTION IF EXISTS immutable_array_to_string(text[])",
    "DROP EXTENSION IF EXISTS pgcrypto",
    "DROP EXTENSION IF EXISTS vector",
]


def upgrade() -> None:
    for statement in UPGRADE:
        op.execute(statement)


def downgrade() -> None:
    for statement in DOWNGRADE:
        op.execute(statement)
