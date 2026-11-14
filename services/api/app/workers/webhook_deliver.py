"""Tarea ARQ de entrega de webhooks outbound al instante."""

from __future__ import annotations

from app.core.db import Database
from app.core.observability import get_logger
from app.domains.webhooks.repository import PostgresWebhookRepository
from app.domains.webhooks.service import WebhookService

logger = get_logger("growup.worker.webhooks")


async def deliver_paid_webhooks(ctx: dict[str, object]) -> None:
    database = ctx.get("database")
    if not isinstance(database, Database):
        logger.error("webhook_deliver_missing_database")
        return
    service = WebhookService(PostgresWebhookRepository(database))
    await service.deliver_pending_paid_events()
