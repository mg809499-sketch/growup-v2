from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.domains.governance.repository import DecisionLogEntry, PostgresDecisionLogRepository

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


def _entry(
    tenant_id: UUID,
    suffix: str,
    action: str = "catalog.update_product",
) -> DecisionLogEntry:
    return DecisionLogEntry(
        tenant_id=tenant_id,
        actor_type="staff",
        actor_id="actor-1",
        action=action,
        resource_type="product",
        resource_id=suffix,
        policy_id=action,
        policy_version="v1",
        decision="ALLOW",
        reason_code="ALLOWED",
        input_hash=f"{suffix:0>64}"[:64],
        context_summary={"slug": f"camisa-{suffix}"},
        latency_ms=1,
        trace_id=f"trace-{suffix}",
    )


async def test_audit_log_pagination_and_chain_verification() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        async with database.pool.acquire() as connection:
            tenant_id = await connection.fetchval(
                "select app.create_tenant($1, $2, $3)",
                f"it-audit-{suffix}",
                f"it-audit-{suffix}.growup.com",
                "Audit Test",
            )
        tenants.append(tenant_id)
        repository = PostgresDecisionLogRepository(database)

        for index in range(3):
            await repository.append(_entry(tenant_id, f"{suffix}{index}"))

        first_page, cursor = await repository.list_logs(
            tenant_id,
            action=None,
            decision=None,
            limit=2,
            before_seq=None,
        )
        assert len(first_page) == 2
        assert cursor is not None
        assert first_page[0].seq > first_page[1].seq
        assert first_page[0].context_summary

        second_page, next_cursor = await repository.list_logs(
            tenant_id,
            action=None,
            decision=None,
            limit=2,
            before_seq=cursor,
        )
        assert len(second_page) == 1
        assert next_cursor is None
        assert second_page[0].seq < first_page[-1].seq

        filtered, _ = await repository.list_logs(
            tenant_id,
            action="catalog.update_product",
            decision="ALLOW",
            limit=50,
            before_seq=None,
        )
        assert len(filtered) == 3

        assert await repository.verify_chain(str(tenant_id)) is True
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()
