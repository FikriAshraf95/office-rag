"""One ProviderError for every provider failure, and the response → code mapping (SPEC-06 §5)."""

from collections.abc import Mapping
from typing import Any, Literal

ProviderCode = Literal[
    "rate_limited",
    "quota_exhausted",
    "provider_auth",
    "model_not_allowed",
    "context_too_long",
    "request_too_large",
    "provider_unavailable",
]

USER_MESSAGES: dict[str, str] = {
    "rate_limited": "The AI service is busy. Try again in a minute.",
    "quota_exhausted": (
        "The AI plan's monthly quota is used up. Ask the admin to top up or wait for the next cycle."
    ),
    "provider_auth": "The AI service rejected the API key. Check AI_API_KEY.",
    "model_not_allowed": "This AI model isn't available on the current plan.",
    "provider_unavailable": "The AI service isn't responding. Try again shortly.",
}

ILMU_ERROR_HEADER = "x-ilmu-error-code"


class ProviderError(Exception):
    def __init__(
        self,
        code: ProviderCode,
        *,
        retryable: bool,
        http_status: int | None = None,
        provider_code: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(f"{code} (http {http_status}, provider {provider_code})")
        self.code: ProviderCode = code
        self.retryable = retryable
        self.http_status = http_status
        self.provider_code = provider_code
        self.retry_after = retry_after


PAYG_EXHAUSTED = "The AI pay-as-you-go balance is used up. Ask the admin to top up."


def user_message(code: str, http_status: int | None = None) -> str:
    if code == "quota_exhausted" and http_status == 402:
        return PAYG_EXHAUSTED
    return USER_MESSAGES.get(code, USER_MESSAGES["provider_unavailable"])


def _retry_after(headers: Mapping[str, str]) -> float | None:
    value = headers.get("retry-after")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def _body_code(body: Any) -> str | None:
    """`error.code` (OpenAI style) or a top-level `code`."""
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict) and isinstance(error.get("code"), str):
            return str(error["code"])
        if isinstance(body.get("code"), str):
            return str(body["code"])
    return None


def from_response(status: int, headers: Mapping[str, str], body: Any) -> ProviderError:
    """Map a non-2xx provider response to a ProviderError."""
    header_code = headers.get(ILMU_ERROR_HEADER)
    body_code = _body_code(body)
    provider_code = header_code or body_code
    retry_after = _retry_after(headers)

    def err(code: ProviderCode, retryable: bool) -> ProviderError:
        return ProviderError(
            code,
            retryable=retryable,
            http_status=status,
            provider_code=provider_code,
            retry_after=retry_after,
        )

    if status == 429:
        if header_code == "billing.token_quota_exhausted" or body_code == "billing.token_quota_exhausted":
            return err("quota_exhausted", False)
        return err("rate_limited", True)
    if status == 402:
        return err("quota_exhausted", False)
    if status == 401:
        return err("provider_auth", False)
    if status == 403:
        return err("model_not_allowed" if provider_code == "model_not_allowed" else "provider_auth", False)
    if status == 400 and provider_code == "context_length_exceeded":
        return err("context_too_long", False)
    if status == 413:
        return err("request_too_large", False)
    if status in (500, 502, 503, 504):
        return err("provider_unavailable", True)
    return err("provider_unavailable", False)


def network_error() -> ProviderError:
    return ProviderError("provider_unavailable", retryable=True)
