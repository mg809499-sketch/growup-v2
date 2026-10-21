from __future__ import annotations

from app.core.config import settings
from app.core.db import Database
from app.core.security.jwt import JWTVerifier
from app.domains.catalog.repository import PostgresCatalogRepository
from app.domains.catalog.service import CatalogService
from app.domains.governance.repository import PostgresDecisionLogRepository
from app.domains.governance.service import GovernanceService
from app.domains.identity.repository import PostgresMembershipRepository
from app.domains.identity.service import AuthService
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
