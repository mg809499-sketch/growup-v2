from __future__ import annotations

from app.core.config import settings
from app.core.db import Database
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

tenant_resolver: TenantResolver | None
if database is not None:
    tenant_resolver = TenantResolver(
        PostgresTenantRepository(database),
        InMemoryTenantCache(),
        ttl_seconds=settings.tenant_cache_ttl_seconds,
    )
else:
    tenant_resolver = None
