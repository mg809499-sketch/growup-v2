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
from app.domains.commerce.repository import PostgresCommerceRepository
from app.domains.commerce.service import CommerceService
from app.domains.content.repository import PostgresPageRepository
from app.domains.content.service import PageService
from app.domains.governance.repository import PostgresDecisionLogRepository
from app.domains.governance.service import GovernanceService
from app.domains.identity.repository import PostgresMembershipRepository
from app.domains.identity.service import AuthService
from app.domains.inventory.repository import PostgresInventoryRepository
from app.domains.inventory.service import InventoryService
from app.domains.media.repository import PostgresMediaRepository
from app.domains.media.service import MediaService
from app.domains.media.storage import R2Storage
from app.domains.onboarding.repository import PostgresOnboardingRepository
from app.domains.onboarding.service import OnboardingService
from app.domains.tenants.platform_service import PlatformTenantService
from app.domains.tenants.repository import PostgresTenantRepository
from app.domains.tenants.service import InMemoryTenantCache, TenantResolver
from app.domains.webhooks.repository import PostgresWebhookRepository
from app.domains.webhooks.service import WebhookService

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

onboarding_repository: PostgresOnboardingRepository | None = (
    PostgresOnboardingRepository(database) if database is not None else None
)
onboarding_service: OnboardingService | None = (
    OnboardingService(onboarding_repository)
    if onboarding_repository is not None
    else None
)

auth_service: AuthService | None
if jwt_verifier is not None and membership_repository is not None:
    auth_service = AuthService(jwt_verifier, membership_repository)
else:
    auth_service = None

catalog_repository: PostgresCatalogRepository | None = (
    PostgresCatalogRepository(database) if database is not None else None
)

media_public_base_url = settings.r2_public_base_url or (
    f"{settings.r2_endpoint_url.rstrip('/')}/{settings.r2_catalog_bucket}"
    if settings.r2_endpoint_url
    else ""
)

catalog_service: CatalogService | None = (
    CatalogService(catalog_repository, media_public_base_url)
    if catalog_repository is not None
    else None
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

inventory_repository: PostgresInventoryRepository | None = (
    PostgresInventoryRepository(database) if database is not None else None
)

inventory_service: InventoryService | None = (
    InventoryService(
        inventory_repository,
        default_ttl_seconds=settings.inventory_reservation_ttl_seconds,
    )
    if inventory_repository is not None
    else None
)

page_repository: PostgresPageRepository | None = (
    PostgresPageRepository(database) if database is not None else None
)

page_service: PageService | None = (
    PageService(page_repository) if page_repository is not None else None
)

commerce_repository: PostgresCommerceRepository | None = (
    PostgresCommerceRepository(database) if database is not None else None
)

commerce_service: CommerceService | None = (
    CommerceService(commerce_repository) if commerce_repository is not None else None
)

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
        public_base_url=media_public_base_url
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

webhook_repository: PostgresWebhookRepository | None = (
    PostgresWebhookRepository(database) if database is not None else None
)
webhook_service: WebhookService | None = (
    WebhookService(webhook_repository) if webhook_repository is not None else None
)
