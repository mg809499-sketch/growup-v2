from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.domains.tenants.repository import PostgresTenantRepository
from app.domains.tenants.service import InMemoryTenantCache, TenantResolver

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


async def test_bootstrap_reads_tenant_and_settings() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=2)
    await database.connect()
    created: list[UUID] = []
    suffix = uuid4().hex[:8]
    slug = f"it-bootstrap-{suffix}"

    try:
        repository = PostgresTenantRepository(database)
        tenant_id = await repository.create_tenant(
            slug=slug,
            host=f"{slug}.growup.com",
            name="Bootstrap Test",
        )
        created.append(tenant_id)

        resolver = TenantResolver(repository, InMemoryTenantCache())
        result = await resolver.bootstrap(f"  {slug.upper()}.GROWUP.COM:443 ")

        assert result.tenant.id == tenant_id
        assert result.tenant.slug == slug
        assert result.tenant.name == "Bootstrap Test"
        assert result.settings.currency == "COP"
        assert result.settings.locale == "es-CO"
        assert result.settings.navigation == {}
        assert result.settings.shipping_zones == []
    finally:
        if created:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    created,
                )
        await database.close()
