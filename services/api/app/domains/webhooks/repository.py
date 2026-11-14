from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.db import Database
from app.core.errors import AppError
from app.domains.webhooks.models import WebhookEndpoint


class PostgresWebhookRepository:
    """Acceso a webhooks y outbox: misma forma que el resto (tenant + RLS)."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def create_endpoint(
        self,
        tenant_id: UUID,
        *,
        event: str,
        target_url: str,
        secret_encrypted: str,
    ) -> UUID:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row_id = await connection.fetchval(
                """
                insert into app.webhook_endpoints (tenant_id, event, target_url, secret)
                values ($1, $2, $3, $4)
                returning id
                """,
                tenant_id,
                event,
                target_url,
                secret_encrypted,
            )
        if not isinstance(row_id, UUID):
            raise AppError("WEBHOOK_CREATE_FAILED", "No se pudo registrar el webhook", 500)
        return row_id

    async def list_endpoints(self, tenant_id: UUID) -> list[WebhookEndpoint]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            rows = await connection.fetch(
                """
                select id, event, target_url, secret, active, fail_count, created_at, updated_at
                from app.webhook_endpoints
                where tenant_id = $1
                order by created_at desc
                """,
                tenant_id,
            )
        return [
            WebhookEndpoint(
                id=row["id"],
                tenant_id=tenant_id,
                event=row["event"],
                target_url=row["target_url"],
                secret=row["secret"],
                active=row["active"],
                fail_count=row["fail_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    async def delete_endpoint(self, tenant_id: UUID, endpoint_id: UUID) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            result = await connection.execute(
                "delete from app.webhook_endpoints where tenant_id = $1 and id = $2",
                tenant_id,
                endpoint_id,
            )
        if result != "DELETE 1":
            raise AppError("WEBHOOK_NOT_FOUND", "Webhook no encontrado", 404)

    async def load_active_endpoints(self, tenant_id: UUID, event: str) -> list[WebhookEndpoint]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            rows = await connection.fetch(
                """
                select id, event, target_url, secret, active, fail_count, created_at, updated_at
                from app.webhook_endpoints
                where tenant_id = $1 and event = $2 and active = true
                """,
                tenant_id,
                event,
            )
        return [
            WebhookEndpoint(
                id=row["id"],
                tenant_id=tenant_id,
                event=row["event"],
                target_url=row["target_url"],
                secret=row["secret"],
                active=row["active"],
                fail_count=row["fail_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    async def mark_endpoint_success(self, tenant_id: UUID, endpoint_id: UUID) -> None:
        async with self._database.worker_transaction() as connection:
            await connection.execute(
                """
                update app.webhook_endpoints
                   set fail_count = 0, updated_at = now()
                 where tenant_id = $1 and id = $2
                """,
                tenant_id,
                endpoint_id,
            )

    async def mark_endpoint_failure(
        self, tenant_id: UUID, endpoint_id: UUID, max_fails: int = 5
    ) -> None:
        async with self._database.worker_transaction() as connection:
            await connection.execute(
                """
                update app.webhook_endpoints
                   set fail_count = fail_count + 1,
                       active = (fail_count + 1) < $3,
                       updated_at = now()
                 where tenant_id = $1 and id = $2
                """,
                tenant_id,
                endpoint_id,
                max_fails,
            )

    async def fetch_paid_events(self, limit: int = 25) -> list[dict[str, Any]]:
        async with self._database.worker_transaction() as connection:
            rows = await connection.fetch(
                """
                select id, tenant_id, type, payload
                from app.outbox_events
                where type = 'orders.paid' and processed_at is null
                order by created_at, id
                limit $1
                for update skip locked
                """,
                limit,
            )
        return [dict(row) for row in rows]

    async def mark_event_processed(self, event_id: str) -> None:
        async with self._database.worker_transaction() as connection:
            await connection.execute(
                "update app.outbox_events set processed_at = now() where id = $1",
                event_id,
            )
