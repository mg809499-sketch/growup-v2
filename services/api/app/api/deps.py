from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import runtime
from app.core.errors import AppError
from app.domains.identity.models import Actor, RequestContext
from app.domains.identity.service import AuthService, build_context
from app.domains.tenants.service import TenantResolver

_bearer_scheme = HTTPBearer(auto_error=False)


def get_tenant_resolver() -> TenantResolver:
    if runtime.tenant_resolver is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "La base de datos no está configurada",
            503,
        )
    return runtime.tenant_resolver


def get_auth_service() -> AuthService:
    if runtime.auth_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "La autenticación no está configurada",
            503,
        )
    return runtime.auth_service


async def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("TOKEN_INVALID", "Falta el token Bearer", 401)
    return credentials.credentials


async def get_current_actor(
    token: Annotated[str, Depends(get_bearer_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Actor:
    return await auth_service.authenticate(token)


async def get_admin_context(
    request: Request,
    actor: Annotated[Actor, Depends(get_current_actor)],
) -> RequestContext:
    request_id = getattr(request.state, "request_id", None) or str(uuid4())
    return build_context(
        actor,
        request_id=request_id,
        trace_id=request.headers.get("traceparent"),
    )


async def get_tenant_context(
    context: Annotated[RequestContext, Depends(get_admin_context)],
) -> RequestContext:
    if context.tenant_id is None:
        raise AppError("FORBIDDEN", "Se requiere un tenant", 403)
    return context
