from __future__ import annotations

import os
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import asyncpg
import pytest

from app.core.db import Database

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


@pytest.fixture
async def database() -> AsyncIterator[Database]:
    assert TEST_DSN is not None
    db = Database(TEST_DSN, min_size=1, max_size=2)
    await db.connect()
    try:
        yield db
    finally:
        await db.close()


async def test_tenant_transaction_enforces_rls(database: Database) -> None:
    suffix = uuid4().hex[:8]
    ropa_slug = f"it-ropa-{suffix}"
    joyeria_slug = f"it-joyeria-{suffix}"
    created: list[UUID] = []

    try:
        async with database.pool.acquire() as connection:
            ropa_id = await connection.fetchval(
                "select app.create_tenant($1, $2, $3)",
                ropa_slug,
                f"{ropa_slug}.growup.com",
                "Ropa",
            )
            created.append(ropa_id)
            joyeria_id = await connection.fetchval(
                "select app.create_tenant($1, $2, $3)",
                joyeria_slug,
                f"{joyeria_slug}.growup.com",
                "Joyería",
            )
            created.append(joyeria_id)

        async with database.tenant_transaction(ropa_id) as connection:
            current = await connection.fetchval("select app.current_tenant()")
            assert current == ropa_id

            assert await connection.fetchval("select count(*) from app.tenants") == 1
            assert await connection.fetchval("select count(*) from app.domains") == 1

            resolved = await connection.fetchval(
                "select id from app.resolve_tenant($1)",
                f"{ropa_slug}.growup.com",
            )
            assert resolved == ropa_id

            with pytest.raises(asyncpg.PostgresError) as exc_info:
                await connection.execute(
                    "insert into app.domains (tenant_id, host) values ($1, $2)",
                    joyeria_id,
                    f"hack-{suffix}.growup.com",
                )
            assert exc_info.value.sqlstate == "42501"
    finally:
        if created:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    created,
                )
