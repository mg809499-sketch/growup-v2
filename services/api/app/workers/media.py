from __future__ import annotations

from typing import Any
from uuid import UUID

from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.db import Database
from app.core.observability import get_logger
from app.domains.media.repository import PostgresMediaRepository
from app.domains.media.service import MediaService
from app.domains.media.storage import R2Storage
from app.workers.outbox_purge import publish_purge

logger = get_logger("growup.worker.media")

_CTX_DATABASE = "database"
_CTX_MEDIA_SERVICE = "media_service"


async def process_media(ctx: dict[str, Any], tenant_id: str, asset_id: str) -> None:
    service = ctx.get(_CTX_MEDIA_SERVICE)
    if service is None:
        # Startup inválido: reintentar no lo arregla; fail-closed y se descarta.
        logger.error("process_media_missing_service", tenant_id=tenant_id, asset_id=asset_id)
        return
    try:
        tenant_uuid = UUID(tenant_id)
        asset_uuid = UUID(asset_id)
    except (ValueError, TypeError, AttributeError):
        # Mensaje envenenado: reintentar siempre fallaría; se registra y se suelta.
        logger.error("process_media_invalid_id", tenant_id=tenant_id, asset_id=asset_id)
        return
    await service.process_asset(tenant_uuid, asset_uuid)


async def cleanup_uploads(ctx: dict[str, Any]) -> None:
    """Marca como `failed` los uploads que nunca se completaron.

    La función SECURITY DEFINER solo es ejecutable por el rol app_worker.
    """
    database: Database = ctx[_CTX_DATABASE]
    async with database.worker_transaction() as connection:
        await connection.fetchval(
            "select app.expire_stale_uploads($1)",
            settings.media_stale_upload_seconds,
        )


async def startup(ctx: dict[str, Any]) -> None:
    if not settings.worker_database_url:
        raise RuntimeError("GROWUP_WORKER_DATABASE_URL es obligatoria para el worker")
    if not (
        settings.r2_endpoint_url
        and settings.r2_access_key_id
        and settings.r2_secret_access_key
    ):
        raise RuntimeError("R2 no está configurado para el worker")

    database = Database(
        settings.worker_database_url,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
    )
    await database.connect()

    storage = R2Storage(
        endpoint_url=settings.r2_endpoint_url,
        access_key_id=settings.r2_access_key_id,
        secret_access_key=settings.r2_secret_access_key,
        bucket=settings.r2_catalog_bucket,
        public_base_url=settings.r2_public_base_url
        or f"{settings.r2_endpoint_url.rstrip('/')}/{settings.r2_catalog_bucket}",
    )
    service = MediaService(
        PostgresMediaRepository(database),
        storage,
        max_image_bytes=settings.media_max_image_bytes,
    )
    ctx[_CTX_DATABASE] = database
    ctx[_CTX_MEDIA_SERVICE] = service


async def shutdown(ctx: dict[str, Any]) -> None:
    database: Database | None = ctx.get(_CTX_DATABASE)
    if database is not None:
        await database.close()


class WorkerSettings:
    functions = [process_media, publish_purge]
    cron_jobs = [cron(cleanup_uploads, minute=0), cron(publish_purge, minute=5)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = (
        RedisSettings.from_dsn(settings.redis_url)
        if settings.redis_url
        else RedisSettings()
    )
    max_tries = 3
