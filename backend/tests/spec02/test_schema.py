"""SPEC-02 §8 acceptance checks."""

import asyncio
import uuid

import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from tests.dbutil import downgrade, migrate, recreate_database

MIGRATION_DB = "rag_test_migrations"
MIGRATION_URL = f"postgresql+asyncpg://rag:rag@127.0.0.1:5433/{MIGRATION_DB}"
MIGRATION_DSN = f"postgresql://rag:rag@127.0.0.1:5433/{MIGRATION_DB}"
TEST_DSN = "postgresql://rag:rag@127.0.0.1:5433/rag_test"

COLUMNS = {
    "documents": {
        "id", "title", "filename", "content_type", "file_type", "size_bytes", "sha256", "storage_path",
        "doc_type", "department", "effective_date", "version", "language", "status", "access_groups",
        "page_count", "summary", "tags", "ingest_status", "ingest_error_code", "ingest_error", "chunk_count",
        "uploaded_by", "created_at", "updated_at", "deleted_at",
    },
    "chunks": {
        "id", "document_id", "ordinal", "chunk_type", "text", "heading_path", "section", "page_start",
        "page_end", "sheet", "token_count", "embedding", "embedding_model", "doc_status", "access_groups",
        "tsv", "created_at",
    },
    "jobs": {
        "id", "kind", "document_id", "payload", "status", "attempts", "max_attempts", "run_after",
        "locked_by", "locked_at", "error_code", "error", "created_at", "finished_at",
    },
    "questions": {
        "id", "user_id", "question", "answer", "found", "sources", "cited", "model", "latency_ms",
        "first_token_ms", "error_code", "created_at",
    },
    "usage": {
        "id", "at", "provider", "model", "role", "purpose", "ref_id", "prompt_tokens", "completion_tokens",
        "reasoning_tokens", "total_tokens", "cost_myr", "latency_ms", "status", "error_code",
    },
}  # fmt: skip

INDEXES = {
    "uq_documents_sha256_live", "ix_documents_status", "ix_documents_access_groups",
    "ix_documents_created_at",
    "ix_chunks_embedding_hnsw", "ix_chunks_tsv", "ix_chunks_access_groups", "uq_chunks_document_ordinal",
    "ix_chunks_doc_status", "ix_jobs_queued", "ix_usage_at", "ix_usage_purpose_model",
}  # fmt: skip

CONSTRAINTS = {"ck_documents_status", "ck_documents_access_groups_not_empty", "ck_documents_ingest_status"}
FUNCTIONS = {"immutable_array_to_string", "jobs_notify_new"}


async def _catalog() -> dict[str, set[str]]:
    conn = await asyncpg.connect(MIGRATION_DSN)
    try:
        rows = await conn.fetch(
            "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'"
        )
        columns: dict[str, set[str]] = {}
        for r in rows:
            columns.setdefault(r["table_name"], set()).add(r["column_name"])
        catalog = {f"columns:{t}": cols for t, cols in columns.items()}
        catalog["indexes"] = {
            r[0] for r in await conn.fetch("SELECT indexname FROM pg_indexes WHERE schemaname='public'")
        }
        catalog["constraints"] = {r[0] for r in await conn.fetch("SELECT conname FROM pg_constraint")}
        catalog["functions"] = {
            r[0]
            for r in await conn.fetch(
                "SELECT proname FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace"
                " WHERE nspname = 'public'"
            )
        }
        catalog["extensions"] = {r[0] for r in await conn.fetch("SELECT extname FROM pg_extension")}
        catalog["triggers"] = {
            r[0] for r in await conn.fetch("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")
        }
        catalog["generated"] = {
            r[0]
            for r in await conn.fetch(
                "SELECT column_name FROM information_schema.columns WHERE is_generated = 'ALWAYS'"
            )
        }
        return catalog
    finally:
        await conn.close()


async def test_spec02_ac01_upgrade_creates_everything_and_downgrade_removes_it() -> None:
    await asyncio.to_thread(recreate_database, MIGRATION_DB)
    await asyncio.to_thread(migrate, MIGRATION_URL, "head")
    catalog = await _catalog()
    for table, columns in COLUMNS.items():
        assert catalog.get(f"columns:{table}") == columns, table
    assert catalog["indexes"] >= INDEXES
    assert catalog["constraints"] >= CONSTRAINTS
    assert catalog["functions"] >= FUNCTIONS
    assert {"vector", "pgcrypto"} <= catalog["extensions"]
    assert "jobs_new" in catalog["triggers"]
    assert "tsv" in catalog["generated"]

    await asyncio.to_thread(downgrade, MIGRATION_URL, "base")
    catalog = await _catalog()
    assert not any(key.startswith("columns:") and key != "columns:alembic_version" for key in catalog)
    assert not INDEXES & catalog["indexes"]
    assert not FUNCTIONS & catalog["functions"]
    assert not {"vector", "pgcrypto"} & catalog["extensions"]


INSERT_DOC = text(
    "INSERT INTO documents (title, filename, content_type, file_type, size_bytes, sha256, storage_path,"
    " uploaded_by, access_groups, deleted_at)"
    " VALUES ('T', 't.md', 'text/markdown', 'md', 1, :sha, 'x/t.md', 'ben', :groups, :deleted_at)"
    " RETURNING id"
)


async def _insert_doc(
    db: AsyncSession, sha: str, groups: list[str] | None = None, deleted: bool = False
) -> uuid.UUID:
    result = await db.execute(
        INSERT_DOC,
        {"sha": sha, "groups": groups or ["all"], "deleted_at": None},
    )
    doc_id: uuid.UUID = result.scalar_one()
    if deleted:
        await db.execute(text("UPDATE documents SET deleted_at = now() WHERE id = :id"), {"id": doc_id})
    return doc_id


async def test_spec02_ac02_empty_access_groups_fails_check(db: AsyncSession) -> None:
    with pytest.raises(IntegrityError, match="ck_documents_access_groups_not_empty"):
        async with db.begin_nested():
            await db.execute(INSERT_DOC, {"sha": "a" * 64, "groups": [], "deleted_at": None})


async def test_spec02_ac03_duplicate_live_sha256_fails_unique_index(db: AsyncSession) -> None:
    await _insert_doc(db, "b" * 64)
    with pytest.raises(IntegrityError, match="uq_documents_sha256_live"):
        async with db.begin_nested():
            await _insert_doc(db, "b" * 64)
    # A soft-deleted document no longer blocks the same content.
    await _insert_doc(db, "c" * 64, deleted=True)
    await _insert_doc(db, "c" * 64)


async def test_spec02_ac04_tsv_matches_malay_unchanged_and_english_stemmed(db: AsyncSession) -> None:
    doc_id = await _insert_doc(db, "d" * 64)
    await db.execute(
        text(
            "INSERT INTO chunks (document_id, ordinal, chunk_type, text, heading_path, token_count,"
            " doc_status, access_groups)"
            " VALUES (:doc, 0, 'text', :body, :path, 12, 'current', '{all}')"
        ),
        {
            "doc": doc_id,
            "body": "Cuti tahunan untuk gred M2. Employees may carry forward unused leaves.",
            "path": ["HR Handbook", "4. Leave"],
        },
    )

    async def matches(config: str, query: str) -> bool:
        result = await db.execute(
            text("SELECT count(*) FROM chunks WHERE document_id = :doc AND tsv @@ plainto_tsquery(:cfg, :q)"),
            {"doc": doc_id, "cfg": config, "q": query},
        )
        return bool(result.scalar_one())

    assert await matches("simple", "tahunan")
    assert await matches("simple", "m2")
    assert await matches("english", "leave")  # stored as "leaves"
    assert await matches("english", "handbook")  # heading path is indexed
    assert not await matches("simple", "perubatan")


async def test_spec02_ac05_insert_into_jobs_notifies_jobs_new(committed_db: AsyncEngine) -> None:
    received: asyncio.Queue[str] = asyncio.Queue()
    listener = await asyncpg.connect(TEST_DSN)
    try:
        await listener.add_listener("jobs_new", lambda *args: received.put_nowait(args[3]))
        async with committed_db.begin() as conn:
            job_id = (
                await conn.execute(text("INSERT INTO jobs (kind) VALUES ('ingest_document') RETURNING id"))
            ).scalar_one()
        payload = await asyncio.wait_for(received.get(), timeout=5)
        assert payload == str(job_id)
    finally:
        await listener.close()
