# Backend rules (`backend/`)

Python 3.14 (uv-managed, pinned in `.python-version`), uv, FastAPI, Pydantic v2, SQLAlchemy 2 (async, asyncpg), Alembic, pgvector. Layout and boundaries: [SPEC-01](../docs/specs/SPEC-01-architecture.md).

## Structure
- `app/api/` routers: validate input, call **one** service function, map the result to a response schema. No SQL, no provider calls, no business rules.
- `app/ingestion/service.py` is the only writer of `documents` and `chunks`. Status/access-group changes update the chunk copies in the same transaction.
- `app/retrieval/search.py` is the only reader of chunks for search; filters live inside the SQL, never as a post-filter.
- `app/providers/` is the only place that imports `openai`/`httpx` for AI or names a model. Ask for a role: `providers.chat("answer")`.
- `docling` is imported only in `app/ingestion/parsers/` and only by the worker.

## Conventions
- Type hints everywhere; `mypy --strict` on `app/`. Modern syntax is fine (`X | None`, `Self`, `asyncio.TaskGroup`, PEP 695 generics); no free-threaded build.
- Pydantic schemas in `app/api/schemas.py` use `alias_generator=to_camel`, `populate_by_name=True`; responses are camelCase.
- Errors: raise `ApiError(status, code, detail, **extra)` from `app/api/errors.py`; the handler renders problem+json with `traceId`. Codes are listed in SPEC-08 §2 — add new ones there first.
- DB sessions: one `AsyncSession` per request via dependency; services take the session as the first argument; commit in the service, not the router.
- Raw SQL only for the search statement and the job claim (`sqlalchemy.text` with bound parameters). Never f-string SQL.
- Settings via `app.config.get_settings()` (cached). Never read `os.environ` elsewhere.
- Logging: `structlog` JSON; never log `AI_API_KEY`, chunk text or questions above DEBUG.
- New table/column → SPEC-02 + migration `M<nn>_<topic>` in the same change. New endpoint → SPEC-08 row.
- Every provider call logs a `usage` row (the provider wrappers do this; don't bypass them).
