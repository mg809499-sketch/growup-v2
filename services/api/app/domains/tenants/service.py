from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError
from app.core.tenancy import normalize_host
from app.domains.tenants.models import Tenant, TenantBootstrap, TenantSettings
from app.domains.tenants.repository import TenantRepository


class TenantCache(Protocol):
    async def get(self, host: str) -> Tenant | None: ...

    async def set(self, host: str, tenant: Tenant, ttl_seconds: int) -> None: ...

    async def invalidate(self, host: str) -> None: ...


class InMemoryTenantCache:
    """Caché local con TTL. Se reemplaza por Redis cuando esté configurado."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._items: dict[str, tuple[float, Tenant]] = {}

    async def get(self, host: str) -> Tenant | None:
        item = self._items.get(host)
        if item is None:
            return None

        expires_at, tenant = item
        if self._clock() >= expires_at:
            self._items.pop(host, None)
            return None

        return tenant

    async def set(self, host: str, tenant: Tenant, ttl_seconds: int) -> None:
        self._items[host] = (self._clock() + ttl_seconds, tenant)

    async def invalidate(self, host: str) -> None:
        self._items.pop(host, None)


class TenantResolver:
    def __init__(
        self,
        repository: TenantRepository,
        cache: TenantCache | None = None,
        *,
        ttl_seconds: int = 300,
    ) -> None:
        self._repository = repository
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    async def resolve(self, raw_host: str) -> Tenant:
        host = normalize_host(raw_host)

        if self._cache is not None:
            cached = await self._cache.get(host)
            if cached is not None:
                return cached

        tenant = await self._repository.find_by_host(host)
        if tenant is None:
            raise AppError("TENANT_NOT_FOUND", "Tienda no encontrada", 404)

        if self._cache is not None:
            await self._cache.set(host, tenant, self._ttl_seconds)

        return tenant

    async def bootstrap(self, raw_host: str) -> TenantBootstrap:
        tenant = await self.resolve(raw_host)
        settings = await self._repository.get_settings(tenant.id)
        return TenantBootstrap(
            tenant=tenant,
            settings=settings or TenantSettings.defaults(),
        )

    async def create_tenant(
        self,
        *,
        slug: str,
        host: str,
        name: str,
        legal_name: str | None = None,
        plan_id: UUID | None = None,
    ) -> UUID:
        return await self._repository.create_tenant(
            slug=slug,
            host=host,
            name=name,
            legal_name=legal_name,
            plan_id=plan_id,
        )
