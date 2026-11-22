# SPEC-01 — Architecture

> **Status:** v1 (2026-11-19) · **Owner of:** repo layout, module boundaries, provider interfaces and fakes

## 1. Repo layout

```
CLAUDE.md                     root rules (short)
docker-compose.yml            api, worker, postgres, frontend
.env.example                  every env var, no secrets
backend/
  CLAUDE.md
  pyproject.toml              uv, Python 3.14 (uv-managed)
  alembic.ini
  alembic/versions/           M00_initial.py, …
  app/
    main.py                   create_app(): routers, error handlers, lifespan
    config.py                 Settings (pydantic-settings), provider profiles
    db/                       engine.py (async engine, session), models.py (SQLAlchemy 2 typed models)
    api/                      routers: health.py, me.py, documents.py, search.py, chat.py, usage.py; errors.py; schemas.py
    security/                 identity.py (demo user → groups), uploads.py (validation)
    ingestion/                service.py (the only writer), jobs.py (queue), worker.py (loop), parsers/, chunking.py, metadata.py,
                              reembed.py (M99, optional)
    retrieval/                search.py (hybrid + RRF SQL), rerank.py
    answering/                prompt.py, service.py (stream), citations.py
    providers/                base.py (interfaces), openai_compat.py, rerank_http.py, api_client.py (the eval's HTTP client, D007), fakes.py, registry.py, errors.py, usage.py, pricing.py
    eval/                     run.py (python -m app.eval), judge.py, report.py
  tests/
    CLAUDE.md
    conftest.py               test DB, network guard, fake providers, client
    fixtures/                 small docs incl. the private-marker doc
frontend/
  CLAUDE.md
  src/ (see SPEC-07 §2)
docs/                         IDEA, design-system, specs, milestones, deviations
samples/serimaju/             sample docs, eval CSV, fact sheet
storage/                      uploaded originals (gitignored, a mounted volume in Compose)
```

## 2. Module boundaries

| Module | May import | Must not |
|---|---|---|
| `api/` | `ingestion.service`, `retrieval.search`, `answering.service`, `security`, `db.engine` (session dependency), `providers.usage` (read-only summary) | SQL, provider SDKs, parsers |
| `ingestion/` | `db`, `providers.registry`, `docling` | `api/`, `answering/` |
| `retrieval/` | `db`, `providers.registry` | write to `documents`/`chunks` |
| `answering/` | `retrieval.search`, `providers.registry`, `db` (write `questions` only), `ingestion.metadata` (the pure `detect_language`) | write to `documents`/`chunks`; the ingestion writers (`service`, `worker`, `jobs`, `extract`) |
| `providers/` | `openai`, `httpx`, `httpx2` (the OpenAI SDK's own HTTP client, for transports and errors), `config` | anything app-level except `db` for usage rows |
| `eval/` | the HTTP API only (it calls `/api/v1/chat` like a user, through `providers.api_client` because httpx stays under `providers/`, D007), `providers.registry` for the judge | Any DB access of its own. The judge's `usage` rows are written by `providers`, so the eval process needs `DATABASE_URL` |

`docling` is imported **only** in `ingestion/parsers/` and only in the worker process. The API process never loads it (startup time and memory).

## 3. Processes

- **api**: `uvicorn app.main:app`. Stateless. Upload stores the file, inserts the document and a `jobs` row in one transaction, and returns `202`.
- **worker**: `python -m app.ingestion.worker`. Loop: claim one job with `FOR UPDATE SKIP LOCKED`, process, commit; sleep 1 s when the queue is empty (also `LISTEN jobs_new` to wake early). Concurrency is set by `WORKER_CONCURRENCY` (default 1, because Docling is CPU-heavy).
- Both processes share `app/` and one Docker image; the worker image stage adds Docling and its models ([SPEC-11 §2](SPEC-11-deployment.md)).

## 4. Provider interfaces

`app/providers/base.py` (Protocols, async):

```python
class ChatModel(Protocol):
    role: str; model: str; capabilities: Capabilities
    async def complete(self, messages: list[Message], *, json_mode: bool = False,
                       reasoning: Reasoning = "off", max_tokens: int | None = None,
                       purpose: Purpose, ref_id: str | None = None) -> ChatResult: ...
    def stream(self, messages: list[Message], *, reasoning: Reasoning = "off",
               max_tokens: int | None = None, temperature: float | None = None, purpose: Purpose,
               ref_id: str | None = None) -> AsyncIterator[ChatDelta]: ...  # last item carries usage

class VisionModel(Protocol):
    async def describe(self, image: bytes, mime: str, instruction: str, *, purpose: Purpose,
                       ref_id: str | None = None) -> ChatResult: ...

class Embedder(Protocol):
    model: str; dim: int
    async def embed(self, texts: list[str], *, purpose: Purpose, ref_id: str | None = None) -> list[list[float]]: ...

class Reranker(Protocol):
    async def rerank(self, query: str, documents: list[str], top_n: int, *, purpose: Purpose,
                     ref_id: str | None = None) -> list[RerankHit]: ...  # (index, score), sorted
```

`Capabilities`: `supports_thinking`, `supports_image_input`, `supports_json_mode`, `has_reranker`.

`registry.py` builds instances from `Settings` once: `providers.chat("answer" | "fast" | "fallback" | "judge")`, `providers.vision()`, `providers.embedder()`, `providers.reranker()` (returns `None` when `RERANK_MODEL` is empty).

## 5. Fakes

`app/providers/fakes.py`, selected by `AI_PROVIDER=fake`:

- **FakeEmbedder**: deterministic 1,024-dim unit vectors. It hashes lowercased word tokens into buckets (a bag-of-words hash) so texts sharing words are close. Same input → same vector.
- **FakeChatModel**: answers from the prompt. If the user message contains a source block, it returns `"<first sentence of source 1> [1]"`; if there are no sources, it returns the not-found sentinel ([SPEC-05 §5](SPEC-05-answering.md)). With `json_mode=True` it returns `{"verdict": "correct", "reason": "fake"}` (what the eval judge parses). `stream` yields its text in 3 chunks. It can be scripted in tests (`fake.script(["…"])`) and can be told to raise a given `ProviderError`.
- **FakeVisionModel**: returns `"[image] <filename>"` text.
- **FakeReranker**: scores by word overlap with the query.
- All fakes report usage (tokens = word count) so usage logging is testable.

Fake mode is refused at startup when `APP_ENV=production` ([SPEC-09 §6](SPEC-09-security-and-access.md)).

## 6. Acceptance checks

1. No module imports `openai`, `httpx` (for AI calls) or `docling` outside its allowed modules: an import-linter contract (`lint-imports`), part of the full gates.
2. With `AI_PROVIDER=fake`, the API and worker start and the full test suite passes with the network guard on.
3. `APP_ENV=production` with `AI_PROVIDER=fake` → the process exits at startup with a clear message.
4. FakeEmbedder returns the same vector for the same text, and texts sharing words have a higher cosine similarity than texts that don't.
