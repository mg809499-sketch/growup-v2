from __future__ import annotations

from uuid import UUID

from app.core.config import settings
from app.core.tenancy import validate_slug
from app.domains.governance.models import PolicyInput
from app.domains.governance.service import GovernanceService
from app.domains.tenants.models import Tenant, TenantStatus
from app.domains.tenants.repository import TenantRepository


class PlatformTenantService:
    """Onboarding de tenants: decide con gobernanza y crea de forma atómica."""

    def __init__(
        self,
        tenants: TenantRepository,
        governance: GovernanceService,
    ) -> None:
        self._tenants = tenants
        self._governance = governance

    async def create_tenant(
        self,
        *,
        actor_id: str,
        actor_type: str,
        slug: str,
        name: str,
        owner_user_id: UUID,
        owner_email: str,
        legal_name: str | None = None,
        plan_id: UUID | None = None,
        trace_id: str | None = None,
    ) -> Tenant:
        validate_slug(slug)
        host = f"{slug}.{settings.root_domain}"

        policy_input = PolicyInput(
            tenant_id=None,
            actor_id=actor_id,
            actor_type=actor_type,
            action="platform.create_tenant",
            resource_type="tenant",
            resource_id=None,
            context={
                "slug": slug,
                "host": host,
                "plan_id": str(plan_id) if plan_id is not None else None,
                "owner_user_id": str(owner_user_id),
            },
            trace_id=trace_id,
        )

        # Evalúa y audita. Si la política deniega o la auditoría falla, no crea nada.
        await self._governance.evaluate_and_record(
            "platform.create_tenant",
            policy_input,
        )

        tenant_id = await self._tenants.create_tenant_with_owner(
            slug=slug,
            host=host,
            name=name,
            owner_user_id=owner_user_id,
            owner_email=owner_email,
            legal_name=legal_name,
            plan_id=plan_id,
        )

        return Tenant(
            id=tenant_id,
            slug=slug,
            name=name,
            status=TenantStatus.TRIALING,
        )
