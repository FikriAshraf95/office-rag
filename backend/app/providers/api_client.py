"""HTTP client for talking to this app's own API (the eval script, SPEC-10 §5).

Lives here because httpx may only be imported under `app/providers/` (SPEC-01 §2).
"""

import httpx

ApiClient = httpx.AsyncClient
ApiResponse = httpx.Response
TRANSPORT_ERRORS = (httpx.HTTPError,)


def make_api_client(base_url: str, user: str, *, timeout_s: float = 180.0) -> ApiClient:
    return httpx.AsyncClient(
        base_url=base_url, headers={"X-Demo-User": user}, timeout=httpx.Timeout(timeout_s, connect=10.0)
    )
