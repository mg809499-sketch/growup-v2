from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.core.errors import AppError
from app.domains.tenants.models import Tenant, TenantSettings, TenantStatus
from app.domains.tenants.service import InMemoryTenantCache, TenantResolver

TENANT = Tenant(
    id=uuid4(),
    slug="ropa",
    name="Ropa",
    status=TenantStatus.ACTIVE,
)


class FakeTenantRepository:
    def __init__(
        self,
        tenants: dict[str, Tenant] | None = None,
        settings: TenantSettings | None = None,
    ) -> None:
        self.tenants = tenants or {}
        self.settings = settings
        self.host_calls: list[str] = []
        self.settings_calls: list[UUID] = []
        self.created: list[dict[str, object]] = []

    async def find_by_host(self, host: str) -> Tenant | None:
        self.host_calls.append(host)
        return self.tenants.get(host)

    async def get_settings(self, tenant_id: UUID) -> TenantSettings | None:
        self.settings_calls.append(tenant_id)
        return self.settings

    async def create_tenant(
        self,
        *,
        slug: str,
        host: str,
        name: str,
        legal_name: str | None = None,
        plan_id: UUID | None = None,
    ) -> UUID:
        self.created.append(
            {
                "slug": slug,
                "host": host,
                "name": name,
                "legal_name": legal_name,
                "plan_id": plan_id,
            }
        )
        return uuid4()


class FakeCache:
    def __init__(self) -> None:
        self.items: dict[str, Tenant] = {}
        self.sets: list[tuple[str, int]] = []
        self.invalidated: list[str] = []

    async def get(self, host: str) -> Tenant | None:
        return self.items.get(host)

    async def set(self, host: str, tenant: Tenant, ttl_seconds: int) -> None:
        self.items[host] = tenant
        self.sets.append((host, ttl_seconds))

    async def invalidate(self, host: str) -> None:
        self.invalidated.append(host)
        self.items.pop(host, None)


async def test_resolve_normalizes_host_and_caches() -> None:
    repository = FakeTenantRepository({"ropa.growup.com": TENANT})
    cache = FakeCache()
    resolver = TenantResolver(repository, cache, ttl_seconds=120)

    tenant = await resolver.resolve("  Ropa.Growup.COM:443 ")

    assert tenant == TENANT
    assert repository.host_calls == ["ropa.growup.com"]
    assert cache.sets == [("ropa.growup.com", 120)]


async def test_resolve_uses_cache_without_hitting_repository() -> None:
    repository = FakeTenantRepository()
    cache = FakeCache()
    cache.items["ropa.growup.com"] = TENANT
    resolver = TenantResolver(repository, cache)

    tenant = await resolver.resolve("ropa.growup.com")

    assert tenant == TENANT
    assert repository.host_calls == []


async def test_resolve_unknown_host_raises() -> None:
    resolver = TenantResolver(FakeTenantRepository(), FakeCache())

    with pytest.raises(AppError) as exc_info:
        await resolver.resolve("nadie.growup.com")

    assert exc_info.value.code == "TENANT_NOT_FOUND"
    assert exc_info.value.status_code == 404


async def test_in_memory_cache_expires() -> None:
    now = [0.0]
    cache = InMemoryTenantCache(clock=lambda: now[0])

    await cache.set("ropa.growup.com", TENANT, 10)
    assert await cache.get("ropa.growup.com") == TENANT

    now[0] = 11.0
    assert await cache.get("ropa.growup.com") is None


async def test_bootstrap_returns_settings() -> None:
    settings = TenantSettings(
        currency="COP",
        locale="es-CO",
        navigation={"main": [{"label": "Inicio", "href": "/"}]},
        shipping_zones=[{"name": "Nacional", "price_cents": 1200000}],
    )
    repository = FakeTenantRepository({"ropa.growup.com": TENANT}, settings)
    resolver = TenantResolver(repository, FakeCache())

    result = await resolver.bootstrap("ropa.growup.com")

    assert result.tenant == TENANT
    assert result.settings == settings
    assert repository.settings_calls == [TENANT.id]


async def test_bootstrap_defaults_when_settings_missing() -> None:
    repository = FakeTenantRepository({"ropa.growup.com": TENANT}, settings=None)
    resolver = TenantResolver(repository, FakeCache())

    result = await resolver.bootstrap("ropa.growup.com")

    assert result.settings == TenantSettings.defaults()


async def test_create_tenant_delegates_to_repository() -> None:
    repository = FakeTenantRepository()
    resolver = TenantResolver(repository)

    await resolver.create_tenant(
        slug="joyeria",
        host="joyeria.growup.com",
        name="Joyería",
    )

    assert repository.created == [
        {
            "slug": "joyeria",
            "host": "joyeria.growup.com",
            "name": "Joyería",
            "legal_name": None,
            "plan_id": None,
        }
    ]
