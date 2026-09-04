from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.academic import router as academic_router
from api.cache_headers import SensitiveApiCacheControlMiddleware
from api.rate_limit import (
    InMemoryRateLimiter,
    RateLimitMiddleware,
    RateLimitSettings,
)
from api.security_headers import SecurityHeadersMiddleware
from api.settings import (
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_EXPOSE_HEADERS,
    cors_origins_from_env,
    enable_api_docs_from_env,
    enable_hsts_from_env,
)
from api.transcripts import router as transcripts_router

logger = logging.getLogger("gradepilot.api")

GENERIC_SERVER_ERROR = "Beklenmeyen bir sunucu hatası oluştu."


def create_app(
    rate_limit_settings: RateLimitSettings | None = None,
    *,
    cors_origins: list[str] | None = None,
    enable_api_docs: bool | None = None,
    enable_hsts: bool | None = None,
) -> FastAPI:
    settings = rate_limit_settings or RateLimitSettings.from_env()
    limiter = InMemoryRateLimiter(max_keys=settings.max_client_keys)
    docs_enabled = (
        enable_api_docs if enable_api_docs is not None else enable_api_docs_from_env()
    )
    hsts_enabled = enable_hsts if enable_hsts is not None else enable_hsts_from_env()
    origins = cors_origins if cors_origins is not None else cors_origins_from_env()

    app = FastAPI(
        title="GradePilot API",
        version="0.1.0",
        description=(
            "HTTP API for GradePilot transcript analysis. "
            "Academic calculations remain in the Python core."
        ),
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        debug=False,
    )
    app.state.rate_limiter = limiter
    app.state.rate_limit_settings = settings
    app.state.cors_origins = origins
    app.state.enable_api_docs = docs_enabled
    app.state.enable_hsts = hsts_enabled

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, StarletteHTTPException):
            return await http_exception_handler(request, exc)
        if isinstance(exc, RequestValidationError):
            return await request_validation_exception_handler(request, exc)
        logger.exception(
            "Unhandled error method=%s path=%s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": GENERIC_SERVER_ERROR},
            headers={"Cache-Control": "no-store"},
        )

    # Inner → outer: cache, security headers, rate limit, CORS.
    app.add_middleware(SensitiveApiCacheControlMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=hsts_enabled)
    app.add_middleware(
        RateLimitMiddleware,
        limiter=limiter,
        settings=settings,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=list(CORS_ALLOW_METHODS),
        allow_headers=list(CORS_ALLOW_HEADERS),
        expose_headers=list(CORS_EXPOSE_HEADERS),
    )

    app.include_router(transcripts_router)
    app.include_router(academic_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
