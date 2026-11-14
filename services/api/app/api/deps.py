from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import runtime
from app.core.errors import AppError
from app.domains.catalog.service import CatalogService
from app.domains.governance.service import GovernanceService
from app.domains.identity.models import Actor, RequestContext
from app.domains.identity.service import AuthService, build_context
from app.domains.media.service import MediaService
from app.domains.onboarding.service import OnboardingService
from app.domains.tenants.models import Tenant
from app.domains.tenants.platform_service import PlatformTenantService
from app.domains.tenants.service import TenantResolver
from app.domains.webhooks.service import WebhookService

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


@dataclass(frozen=True)
class VerifiedUser:
    """Usuario con JWT verificado (p. ej. Google OAuth) y aún sin tenant."""

    user_id: UUID
    email: str


async def get_verified_user(
    token: Annotated[str, Depends(get_bearer_token)],
) -> VerifiedUser:
    """Verifica el JWT vía JWKS sin exigir membresía ni tenant.

    Único camino abierto a usuarios sin tenant: el alta self-service. El JWT
    debe incluir email (Google lo provee). Cualquier otro endpoint exige
    get_current_actor, que sí valida membresía/rol/tenant.
    """
    if runtime.jwt_verifier is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "La autenticación no está configurada",
            503,
        )
    claims = await runtime.jwt_verifier.verify(token)

    try:
        user_id = UUID(claims.subject)
    except (TypeError, ValueError) as exc:
        raise AppError("TOKEN_INVALID", "sub inválido", 401) from exc

    if not claims.email:
        raise AppError(
            "TOKEN_INVALID",
            "El token no incluye email; el alta requiere un correo",
            401,
        )

    return VerifiedUser(user_id=user_id, email=claims.email)


def get_onboarding_service() -> OnboardingService:
    if runtime.onboarding_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El alta de comerciantes no está configurada",
            503,
        )
    return runtime.onboarding_service


def get_catalog_service() -> CatalogService:
    if runtime.catalog_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El catálogo no está configurado",
            503,
        )
    return runtime.catalog_service


def get_webhook_service() -> WebhookService:
    if runtime.webhook_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El servicio de webhooks no está configurado",
            503,
        )
    return runtime.webhook_service


def get_platform_tenant_service() -> PlatformTenantService:
    if runtime.platform_tenant_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El onboarding de tenants no está configurado",
            503,
        )
    return runtime.platform_tenant_service


def get_governance_service() -> GovernanceService:
    if runtime.governance_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "La gobernanza no está configurada",
            503,
        )
    return runtime.governance_service


def get_media_service() -> MediaService:
    if runtime.media_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El servicio de media no está configurado",
            503,
        )
    return runtime.media_service


async def get_storefront_tenant(
    request: Request,
    resolver: Annotated[TenantResolver, Depends(get_tenant_resolver)],
) -> Tenant:
    host = request.headers.get("X-Storefront-Host") or request.headers.get("host")
    if not host:
        raise AppError("TENANT_NOT_FOUND", "Host requerido", 404)
    tenant = await resolver.resolve(host)
    request.state.tenant_id = str(tenant.id)
    return tenant


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
    if actor.tenant_id is not None:
        request.state.tenant_id = str(actor.tenant_id)
    return build_context(
        actor,
        request_id=request_id,
        trace_id=request.headers.get("traceparent"),
    )


async def get_tenant_context(
    request: Request,
    context: Annotated[RequestContext, Depends(get_admin_context)],
) -> RequestContext:
    if context.tenant_id is None:
        raise AppError("FORBIDDEN", "Se requiere un tenant", 403)
    request.state.tenant_id = str(context.tenant_id)
    return context


def require_tenant_id(context: RequestContext) -> UUID:
    """Extrae el tenant del contexto ya validado por get_tenant_context.

    Falla cerrado (403) en lugar de un assert: el assert nunca debe quedar
    como última línea de defensa en el camino de un request.
    """
    if context.tenant_id is None:
        raise AppError("FORBIDDEN", "Se requiere un tenant", 403)
    return context.tenant_id
