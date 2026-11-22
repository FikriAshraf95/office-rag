"""SPEC-09 §8 checks 5 and 6."""

import logging
from typing import Any

import httpx2
import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from app.config import Settings, StartupError, check_startup, get_settings
from app.providers.errors import ProviderError
from app.providers.registry import Providers
from app.providers.usage import UsageRecorder
from tests.conftest import TEST_API_KEY


def _settings(**overrides: Any) -> Settings:
    return Settings(_env_file=None, **{"ai_api_key": "k", **overrides})


async def test_spec09_ac05_api_key_never_in_repr_or_logs(
    connection: AsyncConnection, caplog: pytest.LogCaptureFixture
) -> None:
    settings = get_settings()
    assert settings.ai_api_key.get_secret_value() == TEST_API_KEY
    for text in (repr(settings), str(settings), settings.model_dump_json()):
        assert TEST_API_KEY not in text

    # A rejected key on a real-provider call is logged as an error code, never with the key.
    ilmu = Settings(_env_file=None, ai_provider="ilmu", ai_api_key=TEST_API_KEY)
    transport = httpx2.MockTransport(
        lambda req: httpx2.Response(401, json={"error": {"code": "invalid_api_key"}})
    )
    providers = Providers(ilmu, UsageRecorder(connection), transport=transport)
    caplog.set_level(logging.DEBUG)
    with pytest.raises(ProviderError) as info:
        await providers.chat("answer").complete([{"role": "user", "content": "hi"}], purpose="question")
    assert info.value.code == "provider_auth"
    assert TEST_API_KEY not in str(info.value)
    assert TEST_API_KEY not in caplog.text
    # The whole run's log lines are checked again in conftest.pytest_sessionfinish.


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"app_env": "production", "ai_provider": "fake", "auth_mode": "demo"},
            "Fake AI provider is not allowed",
        ),
        (
            {"app_env": "production", "ai_provider": "ilmu", "auth_mode": "demo"},
            "Demo identity is not allowed",
        ),
        ({"ai_provider": "ilmu", "ai_api_key": ""}, "AI_API_KEY"),
    ],
)
def test_spec09_ac06_startup_guards(overrides: dict[str, Any], message: str) -> None:
    with pytest.raises(StartupError, match=message):
        check_startup(_settings(**overrides))


def test_spec09_ac06_valid_configurations_start() -> None:
    check_startup(_settings(ai_provider="fake"))
    check_startup(_settings(ai_provider="ilmu"))
