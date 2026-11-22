"""SPEC-01 §6 acceptance checks."""

import asyncio
import math
import os
import subprocess
import sys
from pathlib import Path

import httpx
from fastapi import FastAPI

from app.ingestion.worker import run as run_worker
from app.providers.registry import Providers

BACKEND = Path(__file__).resolve().parents[2]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True)) / (
        math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    )


def test_spec01_ac01_import_linter_contracts_kept() -> None:
    exe = Path(sys.executable).parent / ("lint-imports.exe" if os.name == "nt" else "lint-imports")
    result = subprocess.run([str(exe)], cwd=BACKEND, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "broken" in result.stdout and "0 broken" in result.stdout


async def test_spec01_ac02_api_and_worker_start_in_fake_mode(app: FastAPI, client: httpx.AsyncClient) -> None:
    async with app.router.lifespan_context(app):
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["aiProvider"] == "fake"

    stop = asyncio.Event()
    stop.set()
    await asyncio.wait_for(run_worker(stop), timeout=10)


def _start(module_args: list[str]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "APP_ENV": "production", "AI_PROVIDER": "fake", "AUTH_MODE": "demo"}
    return subprocess.run(
        [sys.executable, *module_args],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_spec01_ac03_production_with_fake_provider_exits_at_startup() -> None:
    for args in (["-c", "from app.main import app"], ["-m", "app.ingestion.worker"]):
        result = _start(args)
        assert result.returncode != 0, args
        assert "Fake AI provider is not allowed in production." in result.stderr, args


async def test_spec01_ac04_fake_embedder_is_deterministic_and_word_sensitive(providers: Providers) -> None:
    embedder = providers.embedder()
    a, a_again, shared, unrelated = await embedder.embed(
        [
            "Annual leave entitlement for grade M2",
            "Annual leave entitlement for grade M2",
            "How much annual leave does grade M2 get",
            "Printer toner replacement procedure",
        ],
        purpose="question",
    )
    assert a == a_again
    assert len(a) == 1024
    assert math.isclose(_cosine(a, a), 1.0)
    assert _cosine(a, shared) > _cosine(a, unrelated)
