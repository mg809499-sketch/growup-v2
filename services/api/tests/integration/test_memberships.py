from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.domains.identity.models import Role
from app.domains.identity.repository import PostgresMembershipRepository

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


async def test_membership_repository_and_platform_admin() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=2)
    await database.connect()
    created_tenants: list[UUID] = []
    platform_user_id = uuid4()
    suffix = uuid4().hex[:8]
    slug = f"it-members-{suffix}"

    try:
        async with database.pool.acquire() as connection:
            tenant_id = await connection.fetchval(
                "select app.create_tenant($1, $2, $3)",
                slug,
                f"{slug}.growup.com",
                "Members Test",
            )
            created_tenants.append(tenant_id)

            user_id = uuid4()
            await connection.execute(
                """
                insert into app.memberships (tenant_id, user_id, email, role, status)
                values ($1, $2, $3, 'owner', 'active')
                """,
                tenant_id,
                user_id,
                "owner@example.com",
            )
            await connection.execute(
                """
                insert into app.platform_admins (user_id, email, role)
                values ($1, $2, 'owner')
                """,
                platform_user_id,
                "platform@example.com",
            )

        repository = PostgresMembershipRepository(database)

        membership = await repository.find_active(tenant_id, user_id)
        assert membership is not None
        assert membership.role == Role.OWNER
        assert membership.email == "owner@example.com"
        assert membership.tenant_id == tenant_id
        assert membership.user_id == user_id

        assert await repository.find_active(tenant_id, uuid4()) is None
        assert await repository.is_platform_admin(platform_user_id) is True
        assert await repository.is_platform_admin(user_id) is False
    finally:
        async with database.pool.acquire() as connection:
            await connection.execute(
                "delete from app.platform_admins where user_id = $1",
                platform_user_id,
            )
            if created_tenants:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    created_tenants,
                )
        await database.close()
