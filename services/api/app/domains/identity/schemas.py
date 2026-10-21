from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.domains.identity.models import Permission, RequestContext, Role


class MeResponse(BaseModel):
    user_id: UUID
    tenant_id: UUID | None
    role: Role
    email: str | None
    permissions: list[Permission]

    @classmethod
    def from_context(cls, context: RequestContext) -> MeResponse:
        return cls(
            user_id=context.actor.user_id,
            tenant_id=context.tenant_id,
            role=context.actor.role,
            email=context.actor.email,
            permissions=sorted(context.permissions, key=lambda permission: permission.value),
        )
