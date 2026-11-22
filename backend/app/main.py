"""create_app(): routers, error handlers, lifespan."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import auth, chat, documents, health, search, usage
from app.api.errors import INTERNAL_DETAIL, TraceIdMiddleware, install_error_handlers, problem
from app.api.schemas import ProblemOut
from app.config import check_startup, get_settings
from app.log import configure_logging
from app.providers.errors import ProviderError, user_message
from app.security.limits import ChatLimiter, LoginLimiter

log = structlog.get_logger()

# ProviderError codes → HTTP status when one reaches a request (SPEC-08 §2, SPEC-06 §5).
PROVIDER_STATUS = {
    "rate_limited": 429,
    "quota_exhausted": 503,
    "provider_unavailable": 503,
    "provider_auth": 503,
    "model_not_allowed": 503,
}


async def provider_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ProviderError)
    log.warning("provider_error", code=exc.code, http_status=exc.http_status, provider_code=exc.provider_code)
    status = PROVIDER_STATUS.get(exc.code)
    if status is None:  # context_too_long / request_too_large
        return problem(request, 500, "internal", INTERNAL_DETAIL)
    return problem(request, status, exc.code, user_message(exc.code, exc.http_status))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    log.info(
        "api_started",
        app_env=settings.app_env,
        ai_provider=settings.ai_provider,
        auth_mode=settings.auth_mode,
    )
    yield


def create_app(*, guards: bool = True) -> FastAPI:
    """`guards=False` only for exporting the OpenAPI document, which serves nothing."""
    configure_logging()
    if guards:
        check_startup(get_settings())
    app = FastAPI(
        title="Company Docs RAG",
        version="0.1.0",
        lifespan=lifespan,
        responses={"default": {"model": ProblemOut, "description": "application/problem+json"}},
    )
    app.state.chat_limiter = ChatLimiter(get_settings().chat_rate_per_min)
    app.state.login_limiter = LoginLimiter()
    app.add_middleware(TraceIdMiddleware)
    install_error_handlers(app)
    app.add_exception_handler(ProviderError, provider_error_handler)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(documents.router)
    app.include_router(documents.upload_router)
    app.include_router(search.router)
    app.include_router(chat.router)
    app.include_router(usage.router)
    return app


_app: FastAPI | None = None


def __getattr__(name: str) -> FastAPI:
    """`app.main:app` for uvicorn, built on first access so importing this module has no side effects."""
    global _app
    if name != "app":
        raise AttributeError(name)
    if _app is None:
        _app = create_app()
    return _app
