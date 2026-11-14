"""Consumidor ARQ de la outbox `app.outbox_events`.

Versión inicial:
  - `content.published` / `content.unpublished` → POST al Deploy Hook de Vercel
    (o directo a la API de revalidación) si `GROWUP_VERCEL_PURGE_URL` existe.
  - Limpieza: borra eventos procesados hace más de 7 días.

Notas de seguridad:
  - Sin `GROWUP_VERCEL_PURGE_URL` configurada, NO se marca nada como procesado.
    Se prefiere perder el trabajo de purga pero conservar el evento visible en la
    outbox (la página sigue conteniendo el stale content, pero detectable).
  - Todos los accesos son `worker_transaction` (rol `app_worker`).
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.db import Database
from app.core.observability import get_logger

logger = get_logger("growup.worker.outbox")

_COMMIT_LIMIT = 25
_RETENTION_DAYS = 7
_REQUEST_TIMEOUT_SECONDS = 10.0


def _purge_payload(event: dict[str, object]) -> dict[str, object]:
    return {
        "event_id": str(event.get("id", "")),
        "type": event.get("type"),
        "tenant_id": str(event["tenant_id"]) if event.get("tenant_id") is not None else None,
        "payload": event.get("payload") if isinstance(event.get("payload"), dict) else {},
    }


async def process_unprocessed(
    database: Database,
    *,
    purge_url: str | None,
    http: httpx.AsyncClient | None = None,
) -> int:
    """Procesa un lote de outbox; devuelve cuántos eventos marcó como procesados."""
    if not purge_url:
        async with database.worker_transaction() as connection:
            count = await connection.fetchval(
                "select count(*) from app.outbox_events where processed_at is null"
            )
        if count:
            logger.warning(
                "outbox_purge_disabled",
                pending=count,
                hint="Set GROWUP_VERCEL_PURGE_URL to enable cache purge",
            )
        return 0

    processed = 0
    client = http or httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS)
    own_client = http is None
    try:
        async with database.worker_transaction() as connection:
            rows = await connection.fetch(
                """
                select id, tenant_id, type, payload
                from app.outbox_events
                where processed_at is null
                order by created_at, id
                limit $1
                for update skip locked
                """,
                _COMMIT_LIMIT,
            )
            for row in rows:
                event = dict(row)
                body = _purge_payload(event)
                try:
                    response = await client.post(purge_url, json=body)
                    status = getattr(response, "status_code", 500)
                except Exception as exc:  # noqa: BLE001 - un POST fallido no debe tumbar el worker
                    logger.warning(
                        "outbox_purge_http_error",
                        error=str(exc),
                        event_id=str(event["id"]),
                    )
                    continue
                if 200 <= status < 300:
                    await connection.execute(
                        "update app.outbox_events set processed_at = now() where id = $1",
                        event["id"],
                    )
                    processed += 1
                else:
                    logger.warning(
                        "outbox_purge_http_status",
                        status=status,
                        event_id=str(event["id"]),
                    )
            if processed:
                await connection.execute(
                    """
                    delete from app.outbox_events
                     where processed_at is not null
                       and processed_at < now() - interval '7 days'
                    """
                )
    finally:
        if own_client:
            await client.aclose()
    if processed:
        logger.info("outbox_purge_batch_done", processed=processed)
    return processed


async def publish_purge(ctx: dict[str, object]) -> None:
    """ARQ cron: drena outbox y purga cachés del storefront."""
    database = ctx.get("database")
    if not isinstance(database, Database):
        logger.error("outbox_purge_missing_database")
        return
    await process_unprocessed(database, purge_url=settings.vercel_purge_url)
