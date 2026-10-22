from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.core.config import settings
from app.core.errors import AppError, app_error_handler
from app.core.middleware import SecurityMiddleware
from app.domains.catalog.router import admin_router as catalog_admin_router
from app.domains.catalog.router import storefront_router as catalog_storefront_router
from app.domains.governance.router import router as audit_router
from app.domains.identity.router import router as identity_router
from app.domains.media.router import router as media_router
from app.domains.tenants.platform_router import platform_router
from app.domains.tenants.router import router as storefront_router
from app.runtime import close_media_queue, database
from app.schemas.ops import HealthResponse, ReadyResponse


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


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SecurityMiddleware,
    max_request_bytes=settings.max_request_bytes,
)


async def _app_error_adapter(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, AppError):
        raise exc
    return await app_error_handler(request, exc)


app.add_exception_handler(AppError, _app_error_adapter)

app.include_router(storefront_router)
app.include_router(identity_router)
app.include_router(catalog_admin_router)
app.include_router(catalog_storefront_router)
app.include_router(media_router)
app.include_router(audit_router)
app.include_router(platform_router)


@app.middleware("http")
async def add_request_id(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/healthz", response_model=HealthResponse, tags=["ops"])
async def healthz() -> HealthResponse:
    """Liveness probe. No toca base de datos ni servicios externos."""
    return HealthResponse(
        status="ok",
        service="growup-api",
        environment=settings.environment,
    )


@app.get(
    "/readyz",
    response_model=ReadyResponse,
    responses={503: {"model": ReadyResponse}},
    tags=["ops"],
)
async def readyz() -> ReadyResponse | JSONResponse:
    """Readiness probe: exige base de datos configurada y disponible."""
    if database is None:
        return JSONResponse(
            status_code=503,
            content=ReadyResponse(
                status="not_ready",
                checks={"database": "not_configured"},
            ).model_dump(),
        )

    if await database.ping():
        return ReadyResponse(status="ready", checks={"database": "ok"})

    return JSONResponse(
        status_code=503,
        content=ReadyResponse(
            status="not_ready",
            checks={"database": "down"},
        ).model_dump(),
    )
