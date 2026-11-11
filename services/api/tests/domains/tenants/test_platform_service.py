from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.core.errors import AppError
from app.domains.governance.models import Decision, PolicyInput, PolicyResult
from app.domains.tenants.models import PlatformTenant, Tenant, TenantStatus
from app.domains.tenants.platform_service import PlatformTenantService


class FakeGovernance:
    def __init__(
        self,
        *,
        decision: Decision = Decision.ALLOW,
        error: Exception | None = None,
    ) -> None:
        self.decision = decision
        self.error = error
        self.calls: list[tuple[str, PolicyInput]] = []

    async def evaluate_and_record(
        self,
        policy_id: str,
        input: PolicyInput,
    ) -> PolicyResult:
        self.calls.append((policy_id, input))
        if self.error is not None:
            raise self.error
        if self.decision is not Decision.ALLOW:
            raise AppError("GOVERNANCE_DENIED", "denegado", 403)
        return PolicyResult(
            decision=Decision.ALLOW,
            policy_id=policy_id,
            policy_version="v1",
            reason_code="PLATFORM_ADMIN_ALLOWED",
            latency_ms=1,
        )

    async def verify_chain(self, chain_key: str) -> bool:
        return True


class FakeTenantRepository:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.created: list[dict[str, object]] = []
        self.listed: list[dict[str, object]] = []
        self.tenants: tuple[PlatformTenant, ...] = ()
        self.total = 0

    async def find_by_host(self, host: str) -> Tenant | None:
        return None

    async def get_settings(self, tenant_id: UUID) -> object:
        return None

    async def get_theme(self, tenant_id: UUID) -> object:
        return None

    async def create_tenant(self, **kwargs: object) -> UUID:
        return uuid4()

    async def create_tenant_with_owner(self, **kwargs: object) -> UUID:
        if self.error is not None:
            raise self.error
        self.created.append(kwargs)
        return uuid4()

    async def list_tenants(self, **kwargs: object) -> tuple[tuple[PlatformTenant, ...], int]:
        if self.error is not None:
            raise self.error
        self.listed.append(kwargs)
        return self.tenants, self.total


async def test_create_tenant_allowed() -> None:
    tenants = FakeTenantRepository()
    governance = FakeGovernance()
    service = PlatformTenantService(tenants, governance)  # type: ignore[arg-type]
    owner_user_id = uuid4()
    owner_email = "owner@ropa.com"

    tenant = await service.create_tenant(
        actor_id="platform-1",
        actor_type="platform_admin",
        slug="ropa",
        name="Ropa",
        owner_user_id=owner_user_id,
        owner_email=owner_email,
        plan_id=None,
        trace_id="trace-1",
    )

    assert tenant.slug == "ropa"
    assert tenant.name == "Ropa"
    assert tenant.status is TenantStatus.TRIALING

    assert len(governance.calls) == 1
    policy_id, policy_input = governance.calls[0]
    assert policy_id == "platform.create_tenant"
    assert policy_input.tenant_id is None
    assert policy_input.actor_id == "platform-1"
    assert policy_input.actor_type == "platform_admin"
    assert policy_input.context["slug"] == "ropa"
    assert policy_input.context["host"] == "ropa.growup.com"
    assert policy_input.context["owner_user_id"] == str(owner_user_id)

    assert len(tenants.created) == 1
    created = tenants.created[0]
    assert created["slug"] == "ropa"
    assert created["host"] == "ropa.growup.com"
    assert created["owner_user_id"] == owner_user_id
    assert created["owner_email"] == owner_email


async def test_create_tenant_denied_does_not_touch_repository() -> None:
    tenants = FakeTenantRepository()
    governance = FakeGovernance(decision=Decision.DENY)
    service = PlatformTenantService(tenants, governance)  # type: ignore[arg-type]

    with pytest.raises(AppError) as exc_info:
        await service.create_tenant(
            actor_id="staff-1",
            actor_type="staff",
            slug="ropa",
            name="Ropa",
            owner_user_id=uuid4(),
            owner_email="owner@ropa.com",
        )

    assert exc_info.value.code == "GOVERNANCE_DENIED"
    assert tenants.created == []


async def test_reserved_slug_fails_before_governance() -> None:
    tenants = FakeTenantRepository()
    governance = FakeGovernance()
    service = PlatformTenantService(tenants, governance)  # type: ignore[arg-type]

    with pytest.raises(AppError) as exc_info:
        await service.create_tenant(
            actor_id="platform-1",
            actor_type="platform_admin",
            slug="admin",
            name="Admin",
            owner_user_id=uuid4(),
            owner_email="owner@ropa.com",
        )

    assert exc_info.value.code == "SLUG_RESERVED"
    assert governance.calls == []
    assert tenants.created == []


async def test_invalid_slug_fails_before_governance() -> None:
    tenants = FakeTenantRepository()
    governance = FakeGovernance()
    service = PlatformTenantService(tenants, governance)  # type: ignore[arg-type]

    with pytest.raises(AppError) as exc_info:
        await service.create_tenant(
            actor_id="platform-1",
            actor_type="platform_admin",
            slug="Ropa",
            name="Ropa",
            owner_user_id=uuid4(),
            owner_email="owner@ropa.com",
        )

    assert exc_info.value.code == "SLUG_INVALID"
    assert governance.calls == []


async def test_repository_error_propagates() -> None:
    tenants = FakeTenantRepository(error=AppError("SLUG_TAKEN", "ocupado", 409))
    governance = FakeGovernance()
    service = PlatformTenantService(tenants, governance)  # type: ignore[arg-type]

    with pytest.raises(AppError) as exc_info:
        await service.create_tenant(
            actor_id="platform-1",
            actor_type="platform_admin",
            slug="ropa",
            name="Ropa",
            owner_user_id=uuid4(),
            owner_email="owner@ropa.com",
        )

    assert exc_info.value.code == "SLUG_TAKEN"


async def test_list_tenants_validates_filters() -> None:
    service = PlatformTenantService(FakeTenantRepository(), FakeGovernance())  # type: ignore[arg-type]

    with pytest.raises(AppError) as invalid_status:
        await service.list_tenants(
            actor_id=uuid4(),
            status="bogus",
            query=None,
            limit=50,
            offset=0,
        )
    assert invalid_status.value.code == "INVALID_STATUS"

    with pytest.raises(AppError) as invalid_limit:
        await service.list_tenants(
            actor_id=uuid4(),
            status=None,
            query=None,
            limit=0,
            offset=0,
        )
    assert invalid_limit.value.code == "INVALID_LIMIT"

    with pytest.raises(AppError) as invalid_offset:
        await service.list_tenants(
            actor_id=uuid4(),
            status=None,
            query=None,
            limit=50,
            offset=-1,
        )
    assert invalid_offset.value.code == "INVALID_OFFSET"

    with pytest.raises(AppError) as long_query:
        await service.list_tenants(
            actor_id=uuid4(),
            status=None,
            query="x" * 101,
            limit=50,
            offset=0,
        )
    assert long_query.value.code == "QUERY_TOO_LONG"


async def test_list_tenants_delegates_and_returns_page() -> None:
    repository = FakeTenantRepository()
    tenant = PlatformTenant(
        id=uuid4(),
        slug="ropa",
        name="Ropa",
        status=TenantStatus.TRIALING,
        host="ropa.growup.com",
        plan_id=None,
        trial_ends_at=None,
        created_at=datetime.now(UTC),
    )
    repository.tenants = (tenant,)
    repository.total = 1
    service = PlatformTenantService(repository, FakeGovernance())  # type: ignore[arg-type]
    actor_id = uuid4()

    page = await service.list_tenants(
        actor_id=actor_id,
        status="trialing",
        query="  ropa  ",
        limit=10,
        offset=0,
    )

    assert page.items == (tenant,)
    assert page.total == 1
    assert page.limit == 10
    assert page.offset == 0
    assert repository.listed == [
        {
            "actor_id": actor_id,
            "status": "trialing",
            "query": "ropa",
            "limit": 10,
            "offset": 0,
        }
    ]


async def test_list_tenants_propagates_repository_error() -> None:
    repository = FakeTenantRepository(
        error=AppError("PLATFORM_ADMIN_REQUIRED", "denegado", 403)
    )
    service = PlatformTenantService(repository, FakeGovernance())  # type: ignore[arg-type]

    with pytest.raises(AppError) as exc_info:
        await service.list_tenants(
            actor_id=uuid4(),
            status=None,
            query=None,
            limit=50,
            offset=0,
        )

    assert exc_info.value.code == "PLATFORM_ADMIN_REQUIRED"
