"""SPEC-08 §8 check 3 for the document routes that exist in M01 (chunks and reingest arrive in M02)."""

import uuid
from collections.abc import Callable
from typing import Any

import httpx

from tests import uploads
from tests.spec08.test_api_contract import assert_problem
from tests.uploads import upload


async def _hr_document(client_as: Callable[[str | None], httpx.AsyncClient]) -> str:
    async with client_as("aisyah") as aisyah:
        resp = await upload(aisyah, uploads.markdown("hr only"), "hr.md", accessGroups=["hr"])
        assert resp.status_code == 202, resp.text
        doc: dict[str, Any] = resp.json()
        return str(doc["id"])


async def test_spec08_ac03_hidden_document_is_404_on_get_patch_delete_and_file(
    client: httpx.AsyncClient, client_as: Callable[[str | None], httpx.AsyncClient]
) -> None:
    doc_id = await _hr_document(client_as)
    url = f"/api/v1/documents/{doc_id}"
    assert_problem(await client.get(url), 404, "not_found")
    assert_problem(await client.patch(url, json={"title": "Mine now"}), 404, "not_found")
    assert_problem(await client.delete(url), 404, "not_found")
    assert_problem(await client.get(f"{url}/file"), 404, "not_found")
    # A genuinely unknown id looks exactly the same.
    unknown = f"/api/v1/documents/{uuid.uuid4()}"
    assert (await client.get(unknown)).json()["detail"] == (await client.get(url)).json()["detail"]
    # The owner is unaffected by the failed attempts.
    async with client_as("aisyah") as aisyah:
        body = (await aisyah.get(url)).json()
        assert body["title"] == "hr"


async def test_hidden_document_is_not_listed(
    client: httpx.AsyncClient, client_as: Callable[[str | None], httpx.AsyncClient]
) -> None:
    doc_id = await _hr_document(client_as)
    assert doc_id not in [d["id"] for d in (await client.get("/api/v1/documents")).json()["items"]]
    async with client_as("aisyah") as aisyah:
        assert doc_id in [d["id"] for d in (await aisyah.get("/api/v1/documents")).json()["items"]]


async def test_malformed_id_is_422(client: httpx.AsyncClient) -> None:
    assert_problem(await client.get("/api/v1/documents/not-a-uuid"), 422, "validation_failed")


async def test_spec03_ac15_duplicate_of_a_hidden_document_reveals_nothing(
    client: httpx.AsyncClient, client_as: Callable[[str | None], httpx.AsyncClient]
) -> None:
    async with client_as("aisyah") as aisyah:
        private = (
            await upload(
                aisyah, uploads.markdown("secret"), "secret.md", title="Salary bands", accessGroups=["hr"]
            )
        ).json()
    resp = await upload(client, uploads.markdown("secret"), "copy.md")
    body = assert_problem(resp, 409, "duplicate_document")
    assert "existingId" not in body
    assert "Salary bands" not in resp.text
    assert private["id"] not in resp.text
