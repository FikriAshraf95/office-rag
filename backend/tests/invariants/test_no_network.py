"""Invariant: no real network in tests (SPEC-10 §3; SPEC-10 §6 check 1)."""

import socket
import traceback

import httpx
import pytest
from pytest_socket import SocketConnectBlockedError

from app.config import get_settings


async def test_spec10_ac01_fake_provider_and_network_guard() -> None:
    assert get_settings().ai_provider == "fake"

    with pytest.raises(SocketConnectBlockedError):
        socket.create_connection(("1.1.1.1", 443), timeout=1)

    # Through httpx the blocked connect may arrive wrapped (ConnectError or an ExceptionGroup).
    with pytest.raises(BaseException) as info:
        async with httpx.AsyncClient(timeout=1) as c:
            await c.get("http://1.1.1.1/")
    assert "SocketConnectBlockedError" in "".join(traceback.format_exception(info.value))
