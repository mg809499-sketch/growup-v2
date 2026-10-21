from __future__ import annotations

import json
import os
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.core.errors import AppError
from app.domains.governance.repository import (
    DecisionLogEntry,
    PostgresDecisionLogRepository,
)
from app.domains.governance.service import GovernanceService
from app.domains.tenants.models import TenantStatus
from app.domains.tenants.platform_service import PlatformTenantService
from app.domains.tenants.repository import PostgresTenantRepository

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


async def test_decision_log_chain_and_onboarding() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=2)
    await database.connect()
    created_tenants: list[UUID] = []
    suffix = uuid4().hex[:8]
    slug = f"it-gov-{suffix}"
    owner_user_id = uuid4()
    owner_email = "Owner@Example.com"

    try:
        tenants = PostgresTenantRepository(database)
        governance_repository = PostgresDecisionLogRepository(database)
        governance = GovernanceService(governance_repository)
        service = PlatformTenantService(tenants, governance)

        tenant = await service.create_tenant(
            actor_id="platform-1",
            actor_type="platform_admin",
            slug=slug,
            name="Governance Test",
            owner_user_id=owner_user_id,
            owner_email=owner_email,
            trace_id=f"trace-{suffix}",
        )
        created_tenants.append(tenant.id)

        assert tenant.slug == slug
        assert tenant.status is TenantStatus.TRIALING

        async with database.pool.acquire() as connection:
            membership = await connection.fetchrow(
                "select role, email, status from app.memberships "
                "where tenant_id = $1 and user_id = $2",
                tenant.id,
                owner_user_id,
            )
            host = await connection.fetchval(
                "select host from app.domains where tenant_id = $1 and is_primary",
                tenant.id,
            )
            decision = await connection.fetchrow(
                "select decision, policy_id, policy_version, context_summary "
                "from app.decision_logs where trace_id = $1",
                f"trace-{suffix}",
            )

        assert membership is not None
        assert membership["role"] == "owner"
        assert membership["email"] == owner_email.lower()
        assert membership["status"] == "active"
        assert host == f"{slug}.growup.com"

        assert decision is not None
        assert decision["decision"] == "ALLOW"
        assert decision["policy_id"] == "platform.create_tenant"
        assert decision["policy_version"] == "v1"
        summary = decision["context_summary"]
        if isinstance(summary, str):
            summary = json.loads(summary)
        assert summary["slug"] == slug
        assert "owner_user_id" not in summary

        assert await governance_repository.verify_chain("platform") is True

        # La cadena del tenant se crea con su primera decisión.
        assert await governance_repository.append(
            DecisionLogEntry(
                tenant_id=tenant.id,
                actor_type="staff",
                actor_id=str(owner_user_id),
                action="content.publish",
                resource_type="page",
                resource_id="home",
                policy_id="content.publish",
                policy_version="v1",
                decision="ALLOW",
                reason_code="VALID",
                input_hash="a" * 64,
                context_summary={"page_id": "home"},
                latency_ms=3,
                trace_id=f"trace-page-{suffix}",
            )
        )
        assert await governance_repository.verify_chain(str(tenant.id)) is True
    finally:
        if created_tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    created_tenants,
                )
        await database.close()


async def test_duplicate_slug_is_rejected() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=2)
    await database.connect()
    created_tenants: list[UUID] = []
    suffix = uuid4().hex[:8]
    slug = f"it-dup-{suffix}"

    try:
        repository = PostgresTenantRepository(database)
        tenant_id = await repository.create_tenant_with_owner(
            slug=slug,
            host=f"{slug}.growup.com",
            name="Duplicado",
            owner_user_id=uuid4(),
            owner_email="owner@example.com",
        )
        created_tenants.append(tenant_id)

        with pytest.raises(AppError) as exc_info:
            await repository.create_tenant_with_owner(
                slug=slug,
                host=f"{slug}2.growup.com",
                name="Duplicado 2",
                owner_user_id=uuid4(),
                owner_email="owner2@example.com",
            )

        assert exc_info.value.code == "SLUG_TAKEN"
    finally:
        if created_tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    created_tenants,
                )
        await database.close()
