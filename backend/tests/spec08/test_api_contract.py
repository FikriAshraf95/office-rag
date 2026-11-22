"""SPEC-08 §8 checks 1, 2, 4, 5 and 6."""

import re
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI

from app.export_openapi import build
from app.providers.errors import ProviderError

PROBLEM = "application/problem+json"


def assert_problem(resp: httpx.Response, status: int, code: str) -> dict[str, Any]:
    assert resp.status_code == status
    assert resp.headers["content-type"].startswith(PROBLEM)
    body: dict[str, Any] = resp.json()
    assert body["status"] == status
    assert body["code"] == code
    assert body["detail"]
    assert body["traceId"] == resp.headers["x-trace-id"]
    return body


async def test_spec08_ac02_every_error_is_problem_json(
    app: FastAPI, client: httpx.AsyncClient, client_as: Callable[[str | None], httpx.AsyncClient]
) -> None:
    async def boom() -> None:
        raise RuntimeError("secret internals")

    async def quota() -> None:
        raise ProviderError("quota_exhausted", retryable=False, http_status=429)

    async def too_long() -> None:
        raise ProviderError("context_too_long", retryable=False, http_status=400)

    app.add_api_route("/api/v1/_test/boom", boom)
    app.add_api_route("/api/v1/_test/quota", quota)
    app.add_api_route("/api/v1/_test/too-long", too_long)

    async with client_as(None) as anonymous:
        assert_problem(await anonymous.get("/api/v1/me"), 401, "unknown_user")
    async with client_as("mallory") as stranger:
        assert_problem(await stranger.get("/api/v1/me"), 401, "unknown_user")
    assert_problem(await client.get("/api/v1/nope"), 404, "not_found")
    assert_problem(await client.post("/api/v1/me"), 405, "method_not_allowed")
    body = assert_problem(await client.get("/api/v1/_test/boom"), 500, "internal")
    assert "secret internals" not in body["detail"]
    assert_problem(await client.get("/api/v1/_test/quota"), 503, "quota_exhausted")
    assert_problem(await client.get("/api/v1/_test/too-long"), 500, "internal")


async def test_spec08_ac04_missing_demo_user_is_401_except_config(
    app: FastAPI, client_as: Callable[[str | None], httpx.AsyncClient]
) -> None:
    paths = {p: ops for p, ops in app.openapi()["paths"].items() if p.startswith("/api/v1")}
    assert "/api/v1/me" in paths
    async with client_as(None) as anonymous:
        for template, operations in paths.items():
            path = template.replace("{id}", str(uuid.uuid4()))
            for method in operations:
                resp = await anonymous.request(method.upper(), path)
                if template == "/api/v1/config":
                    assert resp.status_code == 200
                else:
                    assert_problem(resp, 401, "unknown_user")


def _keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [k for k in value] + [k for v in value.values() for k in _keys(v)]
    if isinstance(value, list):
        return [k for v in value for k in _keys(v)]
    return []


async def test_spec08_ac05_json_is_camel_case(client: httpx.AsyncClient) -> None:
    for path in ("/health", "/api/v1/config", "/api/v1/me"):
        resp = await client.get(path)
        assert resp.status_code == 200, path
        assert all("_" not in key for key in _keys(resp.json())), path
    config = (await client.get("/api/v1/config")).json()
    assert {"allowedExtensions", "maxUploadBytes", "demoUsers", "accessGroups", "docTypes", "orgName"} <= set(
        config
    )


async def test_system_endpoints(
    client: httpx.AsyncClient, client_as: Callable[[str | None], httpx.AsyncClient]
) -> None:
    assert (await client.get("/health")).json() == {"status": "ok", "db": "ok", "aiProvider": "fake"}
    config = (await client.get("/api/v1/config")).json()
    assert [u["name"] for u in config["demoUsers"]] == ["Aisyah (HR)", "Ben (Staff)"]
    assert config["accessGroups"][0] == "all"
    assert config["maxUploadBytes"] == 25 * 1024 * 1024
    assert (await client.get("/api/v1/me")).json() == {"id": "ben", "name": "Ben (Staff)", "groups": ["all"]}
    async with client_as("aisyah") as aisyah:
        assert (await aisyah.get("/api/v1/me")).json()["groups"] == ["all", "hr"]


SPEC08 = Path(__file__).resolve().parents[3] / "docs" / "specs" / "SPEC-08-api-contract.md"
INDEX_ROW = re.compile(r"^\| \d+ \| `(GET|POST|PATCH|PUT|DELETE) (/[^`]*)` \|", re.MULTILINE)


async def test_spec08_ac01_routes_match_the_endpoint_index(app: FastAPI) -> None:
    documented = set(INDEX_ROW.findall(SPEC08.read_text(encoding="utf-8")))
    assert len(documented) == 15
    for document in (app.openapi(), build()):
        served = {(m.upper(), p) for p, ops in document["paths"].items() for m in ops}
        assert served == documented


def test_spec08_ac06_openapi_has_the_sse_event_schemas() -> None:
    schemas = build()["components"]["schemas"]
    for name in ("SseMeta", "SseSources", "SseDelta", "SseDone", "SseError"):
        assert name in schemas, name
    assert set(schemas["SseDone"]["properties"]) == {
        "found",
        "cited",
        "finalText",
        "model",
        "usage",
        "latencyMs",
        "firstTokenMs",
    }
    assert schemas["SseSources"]["properties"]["sources"]["items"]["$ref"] == "#/components/schemas/SseSource"
