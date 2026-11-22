"""Invariant: no provider SDK or model name outside app/providers/ (SPEC-10 §3)."""

from tests.helpers import provider_leaks


def test_no_provider_sdk_or_model_name_outside_providers() -> None:
    assert provider_leaks() == []
