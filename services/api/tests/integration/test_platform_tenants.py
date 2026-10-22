from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.core.errors import AppError
from app.domains.tenants.repository import PostgresTenantRepository

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


async def test_platform_tenant_list_requires_admin_and_paginates() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    admin_id = uuid4()
    suffix = uuid4().hex[:8]

    try:
        async with database.pool.acquire() as connection:
            for letter in ("a", "b"):
                tenant_id = await connection.fetchval(
                    "select app.create_tenant($1, $2, $3)",
                    f"it-platform-{suffix}-{letter}",
                    f"it-platform-{suffix}-{letter}.growup.com",
                    f"Platform {letter.upper()}",
                )
                tenants.append(tenant_id)
            await connection.execute(
                "insert into app.platform_admins (user_id, email, role) "
                "values ($1, $2, 'owner')",
                admin_id,
                f"platform-{suffix}@example.com",
            )

        repository = PostgresTenantRepository(database)
        items, total = await repository.list_tenants(
            actor_id=admin_id,
            status="trialing",
            query=f"it-platform-{suffix}",
            limit=50,
            offset=0,
        )

        assert total == 2
        assert {item.slug for item in items} == {
            f"it-platform-{suffix}-a",
            f"it-platform-{suffix}-b",
        }
        assert all(item.host and item.host.endswith(".growup.com") for item in items)
        assert all(item.status.value == "trialing" for item in items)

        page, page_total = await repository.list_tenants(
            actor_id=admin_id,
            status=None,
            query=f"it-platform-{suffix}",
            limit=1,
            offset=1,
        )
        assert page_total == 2
        assert len(page) == 1

        with pytest.raises(AppError) as exc_info:
            await repository.list_tenants(
                actor_id=uuid4(),
                status=None,
                query=None,
                limit=50,
                offset=0,
            )
        assert exc_info.value.code == "PLATFORM_ADMIN_REQUIRED"
    finally:
        async with database.pool.acquire() as connection:
            await connection.execute(
                "delete from app.platform_admins where user_id = $1",
                admin_id,
            )
            if tenants:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()
