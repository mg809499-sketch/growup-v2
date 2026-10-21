from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.core.errors import AppError
from app.core.security.jwt import TokenClaims
from app.domains.identity.models import Actor, RequestContext, Role
from app.domains.identity.permissions import permissions_for
from app.domains.identity.repository import MembershipRepository


class TokenVerifier(Protocol):
    async def verify(self, token: str) -> TokenClaims: ...


class AuthService:
    def __init__(self, verifier: TokenVerifier, memberships: MembershipRepository) -> None:
        self._verifier = verifier
        self._memberships = memberships

    async def authenticate(
        self,
        token: str,
        *,
        expected_tenant_id: UUID | None = None,
    ) -> Actor:
        claims = await self._verifier.verify(token)

        try:
            user_id = UUID(claims.subject)
        except (TypeError, ValueError) as exc:
            raise AppError("TOKEN_INVALID", "sub inválido", 401) from exc

        if claims.tenant_id is None:
            if claims.role != Role.PLATFORM_ADMIN.value:
                raise AppError("TOKEN_INVALID", "Token sin tenant", 401)
            if await self._memberships.is_platform_admin(user_id):
                return Actor(
                    user_id=user_id,
                    tenant_id=None,
                    role=Role.PLATFORM_ADMIN,
                    email=claims.email,
                )
            raise AppError("FORBIDDEN", "Se requiere platform admin", 403)

        if expected_tenant_id is not None and claims.tenant_id != expected_tenant_id:
            raise AppError(
                "TENANT_MISMATCH",
                "El token no pertenece al tenant resuelto",
                403,
            )

        membership = await self._memberships.find_active(claims.tenant_id, user_id)
        if membership is None:
            raise AppError("FORBIDDEN", "Membresía inactiva o inexistente", 403)

        return Actor(
            user_id=user_id,
            tenant_id=claims.tenant_id,
            role=membership.role,
            email=membership.email,
        )


def build_context(
    actor: Actor,
    *,
    request_id: str,
    trace_id: str | None = None,
) -> RequestContext:
    return RequestContext(
        tenant_id=actor.tenant_id,
        actor=actor,
        permissions=permissions_for(actor.role),
        trace_id=trace_id or request_id,
        request_id=request_id,
    )
