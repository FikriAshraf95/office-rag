"""One error shape for every response: application/problem+json with `traceId` (SPEC-08 §2)."""

import uuid
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

log = structlog.get_logger()

PROBLEM_JSON = "application/problem+json"
TRACE_HEADER = "X-Trace-Id"

TITLES = {
    "bad_request": "Bad request",
    "unknown_user": "Unknown user",
    "not_found": "Not found",
    "method_not_allowed": "Method not allowed",
    "duplicate_document": "Duplicate document",
    "ingest_in_progress": "Ingestion in progress",
    "file_too_large": "File too large",
    "unsupported_type": "Unsupported file type",
    "validation_failed": "Validation failed",
    "query_too_long": "Question too long",
    "rate_limited": "AI service busy",
    "quota_exhausted": "AI quota used up",
    "provider_unavailable": "AI service unavailable",
    "provider_auth": "AI service rejected the key",
    "model_not_allowed": "AI model not available",
    "internal": "Something went wrong",
}

INTERNAL_DETAIL = "Something went wrong on our side. Try again; if it keeps happening, quote the trace id."


class ApiError(Exception):
    def __init__(self, status: int, code: str, detail: str, **extra: Any) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail
        self.extra = extra


def trace_id(request: Request) -> str:
    value = getattr(request.state, "trace_id", None)
    return value if isinstance(value, str) else uuid.uuid4().hex


def problem(request: Request, status: int, code: str, detail: str, **extra: Any) -> JSONResponse:
    body: dict[str, Any] = {
        "status": status,
        "code": code,
        "title": TITLES.get(code, "Error"),
        "detail": detail,
        **extra,
        "traceId": trace_id(request),
    }
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


class TraceIdMiddleware:
    """Gives every request a trace id (request.state, structlog context and the X-Trace-Id header)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        tid = uuid.uuid4().hex
        scope.setdefault("state", {})["trace_id"] = tid
        structlog.contextvars.bind_contextvars(traceId=tid)

        async def send_with_trace(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append((TRACE_HEADER.lower().encode(), tid.encode()))
            await send(message)

        started = False

        async def send_tracked(message: Message) -> None:
            nonlocal started
            started = started or message["type"] == "http.response.start"
            await send_with_trace(message)

        try:
            await self.app(scope, receive, send_tracked)
        except Exception as exc:
            # Rendered here, not by Starlette's outer error middleware, so the 500 has a trace id.
            log.error("unhandled_error", error_type=type(exc).__name__, exc_info=exc)
            if not started:
                body = {
                    "status": 500,
                    "code": "internal",
                    "title": TITLES["internal"],
                    "detail": INTERNAL_DETAIL,
                }
                response = JSONResponse({**body, "traceId": tid}, status_code=500, media_type=PROBLEM_JSON)
                await response(scope, receive, send_with_trace)
        finally:
            structlog.contextvars.unbind_contextvars("traceId")


async def _api_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return problem(request, exc.status, exc.code, exc.detail, **exc.extra)


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors: dict[str, list[str]] = {}
    for err in exc.errors():
        loc = [str(part) for part in err.get("loc", ()) if part not in ("body", "query", "path", "header")]
        errors.setdefault(".".join(loc) or "request", []).append(str(err.get("msg", "Invalid value")))
    return problem(
        request, 422, "validation_failed", "Some fields are not valid. Fix them and try again.", errors=errors
    )


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    if exc.status_code == 404:
        return problem(request, 404, "not_found", "Nothing exists at this address. Check the URL.")
    if exc.status_code == 405:
        return problem(request, 405, "method_not_allowed", "This method is not allowed here.")
    if exc.status_code >= 500:
        return problem(request, exc.status_code, "internal", INTERNAL_DETAIL)
    return problem(request, exc.status_code, "bad_request", "The request is malformed. Check it and retry.")


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
