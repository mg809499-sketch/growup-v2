from __future__ import annotations

from uuid import UUID

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import settings
from app.core.db import Database
from app.core.errors import AppError
from app.core.security.jwt import JWTVerifier
from app.domains.catalog.repository import PostgresCatalogRepository
from app.domains.catalog.service import CatalogService
from app.domains.governance.repository import PostgresDecisionLogRepository
from app.domains.governance.service import GovernanceService
from app.domains.identity.repository import PostgresMembershipRepository
from app.domains.identity.service import AuthService
from app.domains.media.repository import PostgresMediaRepository
from app.domains.media.service import MediaService
from app.domains.media.storage import R2Storage
from app.domains.tenants.platform_service import PlatformTenantService
from app.domains.tenants.repository import PostgresTenantRepository
from app.domains.tenants.service import InMemoryTenantCache, TenantResolver

database: Database | None = (
    Database(
        settings.database_url,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
    )
    if settings.database_url
    else None
)

tenant_repository: PostgresTenantRepository | None = (
    PostgresTenantRepository(database) if database is not None else None
)

tenant_resolver: TenantResolver | None
if tenant_repository is not None:
    tenant_resolver = TenantResolver(
        tenant_repository,
        InMemoryTenantCache(),
        ttl_seconds=settings.tenant_cache_ttl_seconds,
    )
else:
    tenant_resolver = None

jwt_verifier: JWTVerifier | None
if settings.supabase_url:
    jwt_verifier = JWTVerifier(
        jwks_url=settings.supabase_jwks_url,
        issuer=settings.supabase_issuer,
        audience=settings.supabase_jwt_audience,
    )
else:
    jwt_verifier = None

membership_repository: PostgresMembershipRepository | None = (
    PostgresMembershipRepository(database) if database is not None else None
)

auth_service: AuthService | None
if jwt_verifier is not None and membership_repository is not None:
    auth_service = AuthService(jwt_verifier, membership_repository)
else:
    auth_service = None

catalog_repository: PostgresCatalogRepository | None = (
    PostgresCatalogRepository(database) if database is not None else None
)

catalog_service: CatalogService | None = (
    CatalogService(catalog_repository) if catalog_repository is not None else None
)

governance_repository: PostgresDecisionLogRepository | None = (
    PostgresDecisionLogRepository(database) if database is not None else None
)

governance_service: GovernanceService | None = (
    GovernanceService(governance_repository)
    if governance_repository is not None
    else None
)

platform_tenant_service: PlatformTenantService | None
if tenant_repository is not None and governance_service is not None:
    platform_tenant_service = PlatformTenantService(tenant_repository, governance_service)
else:
    platform_tenant_service = None

media_repository: PostgresMediaRepository | None = (
    PostgresMediaRepository(database) if database is not None else None
)

media_storage: R2Storage | None = None
if (
    settings.r2_endpoint_url
    and settings.r2_access_key_id
    and settings.r2_secret_access_key
):
    media_storage = R2Storage(
        endpoint_url=settings.r2_endpoint_url,
        access_key_id=settings.r2_access_key_id,
        secret_access_key=settings.r2_secret_access_key,
        bucket=settings.r2_catalog_bucket,
        public_base_url=settings.r2_public_base_url
        or f"{settings.r2_endpoint_url.rstrip('/')}/{settings.r2_catalog_bucket}",
    )

_arq_pool: ArqRedis | None = None


async def enqueue_media(tenant_id: UUID, asset_id: UUID) -> None:
    global _arq_pool
    if not settings.redis_url:
        raise AppError(
            "MEDIA_QUEUE_UNAVAILABLE",
            "La cola de procesamiento no está configurada",
            503,
        )
    if _arq_pool is None:
        _arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await _arq_pool.enqueue_job("process_media", str(tenant_id), str(asset_id))


async def close_media_queue() -> None:
    global _arq_pool
    if _arq_pool is not None:
        await _arq_pool.close()
        _arq_pool = None


media_service: MediaService | None = (
    MediaService(
        media_repository,
        media_storage,
        enqueue=enqueue_media,
        upload_ttl_seconds=settings.media_upload_url_ttl_seconds,
        max_image_bytes=settings.media_max_image_bytes,
    )
    if media_repository is not None and media_storage is not None
    else None
)
