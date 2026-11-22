# syntax=docker/dockerfile:1
# Backend image (SPEC-11 §2): one multi-stage file, targets `api` and `worker`.
# No secrets at build time: no ARG or ENV holds a key; config comes from `.env` at run time.

FROM python:3.14-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
# Without the `worker` group (it is not a default group) and without dev tools.
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
RUN useradd --system --uid 10001 --home-dir /app app \
    && mkdir -p /data/storage && chown app:app /data/storage
ENV STORAGE_DIR=/data/storage

FROM base AS api
USER app
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --retries=30 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status != 200)"]
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

FROM base AS worker
# Docling + CPU-only torch (the lockfile pins torch to the PyTorch CPU index).
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --group worker
# Bake every model in so the worker never downloads at run time (SPEC-11 §6 check 3).
ARG TOKENIZER_ID=BAAI/bge-m3
ENV HF_HOME=/models/hf \
    DOCLING_ARTIFACTS_PATH=/models/docling \
    TOKENIZER_ID=$TOKENIZER_ID
RUN docling-tools models download -o /models/docling layout tableformer rapidocr \
    && python -c "import os; from transformers import AutoTokenizer; AutoTokenizer.from_pretrained(os.environ['TOKENIZER_ID'])" \
    && chmod -R a+rX /models
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1
USER app
CMD ["python", "-m", "app.ingestion.worker"]
