from __future__ import annotations

import re
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.core.config import settings
from app.core.errors import AppError, app_error_handler
from app.core.middleware import SecurityMiddleware
from app.core.observability import configure_logging, configure_sentry, get_logger
from app.core.ratelimit import RateLimitMiddleware
from app.domains.catalog.router import admin_router as catalog_admin_router
from app.domains.catalog.router import storefront_router as catalog_storefront_router
from app.domains.commerce.admin_router import router as orders_admin_router
from app.domains.commerce.storefront_router import router as commerce_storefront_router
from app.domains.commerce.webhook_router import router as webhooks_router
from app.domains.content.router import admin_router as content_admin_router
from app.domains.content.router import storefront_router as content_storefront_router
from app.domains.governance.router import router as audit_router
from app.domains.identity.router import router as identity_router
from app.domains.inventory.router import router as inventory_router
from app.domains.media.router import router as media_router
from app.domains.onboarding.router import router as onboarding_router
from app.domains.tenants.platform_router import platform_router
from app.domains.tenants.router import router as storefront_router
from app.runtime import close_media_queue, database
from app.schemas.ops import HealthResponse, ReadyResponse

configure_logging()
configure_sentry()

logger = get_logger("growup.api")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if database is not None:
        await database.connect()
    try:
        yield
    finally:
        await close_media_queue()
        if database is not None:
            await database.close()


_IS_PRODUCTION = settings.environment == "production"

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url=None if _IS_PRODUCTION else "/docs",
    redoc_url=None,
    openapi_url=None if _IS_PRODUCTION else "/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Storefront-Host",
        "traceparent",
    ],
)

app.add_middleware(
    SecurityMiddleware,
    max_request_bytes=settings.max_request_bytes,
)

app.add_middleware(RateLimitMiddleware, redis_url=settings.redis_url)


async def _app_error_adapter(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, AppError):
        raise exc
    return await app_error_handler(request, exc)


app.add_exception_handler(AppError, _app_error_adapter)


async def _validation_error_adapter(request: Request, exc: Exception) -> Response:
    """422 de Pydantic/FastAPI dentro del envelope uniforme."""
    if not isinstance(exc, RequestValidationError):
        raise exc
    request_id = getattr(request.state, "request_id", None)
    fields = [
        {
            "loc": [str(part) for part in error.get("loc", ())],
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "La solicitud no es válida",
                "details": {"fields": fields},
                "request_id": request_id,
            }
        },
    )


app.add_exception_handler(RequestValidationError, _validation_error_adapter)

app.include_router(storefront_router)
app.include_router(content_storefront_router)
app.include_router(commerce_storefront_router)
app.include_router(webhooks_router)
app.include_router(identity_router)
app.include_router(catalog_admin_router)
app.include_router(catalog_storefront_router)
app.include_router(content_admin_router)
app.include_router(orders_admin_router)
app.include_router(media_router)
app.include_router(inventory_router)
app.include_router(audit_router)
app.include_router(platform_router)
app.include_router(onboarding_router)


_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9-]{1,64}$")


def _sanitize_request_id(value: str | None) -> str:
    if value and _REQUEST_ID_RE.match(value):
        return value
    return str(uuid4())


@app.middleware("http")
async def add_request_id(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = _sanitize_request_id(request.headers.get("X-Request-ID"))
    request.state.request_id = request_id
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=500,
            duration_ms=_elapsed_ms(start),
            request_id=request_id,
            tenant_id=getattr(request.state, "tenant_id", None),
        )
        raise

    response.headers["X-Request-ID"] = request_id
    if request.url.path.startswith(("/v1/admin", "/v1/platform", "/v1/onboarding")):
        response.headers["Cache-Control"] = "no-store"
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=_elapsed_ms(start),
        request_id=request_id,
        tenant_id=getattr(request.state, "tenant_id", None),
    )
    return response


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


@app.get("/", tags=["ops"])
async def root() -> JSONResponse:
    """Punto de entrada legible para humanos: dirección y enlaces."""
    return JSONResponse(
        {
            "service": "growup-api",
            "environment": "hidden" if _IS_PRODUCTION else settings.environment,
            "links": {
                "docs": None if _IS_PRODUCTION else "/docs",
                "health": "/healthz",
                "ready": "/readyz",
                "storefront": "https://{slug}.growup.com",
            },
        }
    )


@app.get("/healthz", response_model=HealthResponse, tags=["ops"])
async def healthz() -> HealthResponse:
    """Liveness probe. No toca base de datos ni servicios externos."""
    return HealthResponse(
        status="ok",
        service="growup-api",
        environment="hidden" if _IS_PRODUCTION else settings.environment,
    )


@app.get(
    "/readyz",
    response_model=ReadyResponse,
    responses={503: {"model": ReadyResponse}},
    tags=["ops"],
)
async def readyz() -> ReadyResponse | JSONResponse:
    """Readiness: exige base de datos; Redis si está configurado (colas/rate limit)."""
    checks: dict[str, str] = {}

    if database is None:
        checks["database"] = "not_configured"
        return JSONResponse(
            status_code=503,
            content=ReadyResponse(
                status="not_ready",
                checks=checks,
            ).model_dump(),
        )

    checks["database"] = "ok" if await database.ping() else "down"

    if settings.redis_url:
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(  # type: ignore[no-untyped-call]
                settings.redis_url, socket_timeout=1.5
            )
            try:
                await client.ping()
                checks["redis"] = "ok"
            finally:
                await client.aclose()
        except Exception:
            checks["redis"] = "down"
    else:
        checks["redis"] = "not_configured"

    if settings.supabase_url:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.head(settings.supabase_jwks_url)
            checks["jwks"] = "ok" if response.status_code < 500 else "degraded"
        except Exception:
            checks["jwks"] = "degraded"
    else:
        checks["jwks"] = "not_configured"

    ready = checks["database"] == "ok" and checks.get("redis") != "down"
    if ready:
        return ReadyResponse(status="ready", checks=checks)

    return JSONResponse(
        status_code=503,
        content=ReadyResponse(
            status="not_ready",
            checks=checks,
        ).model_dump(),
    )
