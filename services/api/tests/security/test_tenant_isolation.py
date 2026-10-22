"""Vectores de aislamiento multi-tenant sobre HTTP real.

Cada test usa la base de datos de pruebas con RLS forzado: las peticiones
pasan por los routers, los servicios y el repositorio, de modo que una fuga
entre tenants se detectaría en la base de datos, no en un mock.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import (
    get_admin_context,
    get_catalog_service,
    get_media_service,
    get_tenant_context,
    get_tenant_resolver,
)
from app.core.db import Database
from app.domains.catalog.models import ProductInput, VariantInput
from app.domains.catalog.repository import PostgresCatalogRepository
from app.domains.catalog.service import CatalogService
from app.domains.identity.models import Actor, RequestContext, Role
from app.domains.identity.permissions import permissions_for
from app.domains.media.repository import PostgresMediaRepository
from app.domains.media.service import MediaService
from app.domains.tenants.repository import PostgresTenantRepository
from app.domains.tenants.service import TenantResolver
from app.main import app

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def presigned_put(
        self,
        key: str,
        *,
        content_type: str,
        expires_in: int = 900,
    ) -> str:
        return f"https://r2.example/{key}?sig=1"

    async def download(self, key: str, *, max_bytes: int) -> bytes:
        return self.objects[key]

    async def upload(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        cache_control: str = "public, max-age=31536000, immutable",
    ) -> None:
        self.objects[key] = data

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    def public_url(self, key: str) -> str:
        return f"https://cdn.example/{key}"


@dataclass
class IsolationEnv:
    database: Database
    tenant_a: UUID
    tenant_b: UUID
    host_a: str
    host_b: str
    product_a: UUID
    product_b: UUID
    product_a_slug: str
    product_b_slug: str
    media_asset_b: UUID
    catalog_service: CatalogService
    media_service: MediaService
    resolver: TenantResolver


def _context(tenant_id: UUID, role: Role = Role.OWNER) -> RequestContext:
    actor = Actor(
        user_id=uuid4(),
        tenant_id=tenant_id,
        role=role,
        email="owner@example.com",
    )
    return RequestContext(
        tenant_id=tenant_id,
        actor=actor,
        permissions=permissions_for(role),
        trace_id="trace-1",
        request_id="req-1",
    )


def _platform_context() -> RequestContext:
    actor = Actor(
        user_id=uuid4(),
        tenant_id=None,
        role=Role.PLATFORM_ADMIN,
        email="platform@example.com",
    )
    return RequestContext(
        tenant_id=None,
        actor=actor,
        permissions=permissions_for(Role.PLATFORM_ADMIN),
        trace_id="trace-1",
        request_id="req-1",
    )


async def _create_product(
    catalog: PostgresCatalogRepository,
    tenant_id: UUID,
    slug: str,
    sku: str,
) -> UUID:
    detail = await catalog.create_product(
        tenant_id,
        ProductInput(
            slug=slug,
            name="Producto aislado",
            description=None,
            category_id=None,
            status="active",
            brand=None,
            tags=(),
            variants=(
                VariantInput(
                    sku=sku,
                    name="M",
                    price_cents=5000000,
                    stock=2,
                ),
            ),
        ),
    )
    return detail.summary.id


@pytest.fixture
async def env() -> AsyncIterator[IsolationEnv]:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    suffix = uuid4().hex[:8]
    tenants: list[UUID] = []

    try:
        async with database.pool.acquire() as connection:
            tenant_a = await connection.fetchval(
                "select app.create_tenant($1, $2, $3)",
                f"sec-a-{suffix}",
                f"sec-a-{suffix}.growup.com",
                "Tenant A",
            )
            tenant_b = await connection.fetchval(
                "select app.create_tenant($1, $2, $3)",
                f"sec-b-{suffix}",
                f"sec-b-{suffix}.growup.com",
                "Tenant B",
            )
        tenants.extend([tenant_a, tenant_b])

        catalog = PostgresCatalogRepository(database)
        media = PostgresMediaRepository(database)
        product_a_slug = f"producto-a-{suffix}"
        product_b_slug = f"producto-b-{suffix}"
        product_a = await _create_product(
            catalog,
            tenant_a,
            product_a_slug,
            f"SKU-A-{suffix}",
        )
        product_b = await _create_product(
            catalog,
            tenant_b,
            product_b_slug,
            f"SKU-B-{suffix}",
        )

        media_asset_b = await media.create_asset(
            tenant_b,
            r2_key=f"tenant/{tenant_b}/originals/{uuid4()}.jpg",
            mime="image/jpeg",
            size_bytes=100,
            original_filename="b.jpg",
        )
        await media.set_alt(tenant_b, media_asset_b, "Imagen de B")
        await media.mark_ready(
            tenant_b,
            media_asset_b,
            r2_key=f"tenant/{tenant_b}/originals/{media_asset_b}.jpg",
            mime="image/jpeg",
            size_bytes=90,
            width=800,
            height=600,
            blurhash="LDT9R{]9fQ]9",
        )

        yield IsolationEnv(
            database=database,
            tenant_a=tenant_a,
            tenant_b=tenant_b,
            host_a=f"sec-a-{suffix}.growup.com",
            host_b=f"sec-b-{suffix}.growup.com",
            product_a=product_a,
            product_b=product_b,
            product_a_slug=product_a_slug,
            product_b_slug=product_b_slug,
            media_asset_b=media_asset_b,
            catalog_service=CatalogService(catalog),
            media_service=MediaService(media, FakeStorage()),
            resolver=TenantResolver(PostgresTenantRepository(database)),
        )
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()


@pytest.fixture
async def client(env: IsolationEnv) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_admin_context] = lambda: _context(env.tenant_a)
    app.dependency_overrides[get_tenant_context] = lambda: _context(env.tenant_a)
    app.dependency_overrides[get_catalog_service] = lambda: env.catalog_service
    app.dependency_overrides[get_media_service] = lambda: env.media_service
    app.dependency_overrides[get_tenant_resolver] = lambda: env.resolver
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://api.test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_admin_cannot_read_product_of_other_tenant(
    client: AsyncClient,
    env: IsolationEnv,
) -> None:
    response = await client.get(f"/v1/admin/products/{env.product_b}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


async def test_admin_cannot_update_product_of_other_tenant(
    client: AsyncClient,
    env: IsolationEnv,
) -> None:
    response = await client.patch(
        f"/v1/admin/products/{env.product_b}",
        json={"name": "Secuestrado"},
    )

    assert response.status_code == 404
    async with env.database.pool.acquire() as connection:
        name = await connection.fetchval(
            "select name from app.products where tenant_id = $1 and id = $2",
            env.tenant_b,
            env.product_b,
        )
    assert name == "Producto aislado"


async def test_admin_list_only_returns_own_tenant_products(
    client: AsyncClient,
    env: IsolationEnv,
) -> None:
    response = await client.get("/v1/admin/products")

    assert response.status_code == 200
    slugs = [item["slug"] for item in response.json()["items"]]
    assert slugs == [env.product_a_slug]


async def test_body_cannot_force_another_tenant(
    client: AsyncClient,
    env: IsolationEnv,
) -> None:
    response = await client.post(
        "/v1/admin/products",
        json={
            "slug": "intento",
            "name": "Intento",
            "status": "draft",
            "tenant_id": str(env.tenant_b),
            "variants": [
                {
                    "sku": "INTENTO-1",
                    "name": "M",
                    "price_cents": 1000,
                    "stock": 1,
                }
            ],
        },
    )

    assert response.status_code == 422


async def test_x_tenant_id_header_is_ignored(
    client: AsyncClient,
    env: IsolationEnv,
) -> None:
    response = await client.get(
        "/v1/admin/products",
        headers={"X-Tenant-ID": str(env.tenant_b)},
    )

    assert response.status_code == 200
    slugs = [item["slug"] for item in response.json()["items"]]
    assert slugs == [env.product_a_slug]


async def test_storefront_ignores_tenant_id_query(
    client: AsyncClient,
    env: IsolationEnv,
) -> None:
    response = await client.get(
        f"/v1/storefront/products?tenant_id={env.tenant_b}",
        headers={"X-Storefront-Host": env.host_a},
    )

    assert response.status_code == 200
    slugs = [item["slug"] for item in response.json()["items"]]
    assert slugs == [env.product_a_slug]


async def test_storefront_resolves_tenant_by_host(
    client: AsyncClient,
    env: IsolationEnv,
) -> None:
    response = await client.get(
        "/v1/storefront/products",
        headers={
            "X-Storefront-Host": env.host_b,
            "X-Tenant-ID": str(env.tenant_a),
        },
    )

    assert response.status_code == 200
    slugs = [item["slug"] for item in response.json()["items"]]
    assert slugs == [env.product_b_slug]


async def test_media_of_other_tenant_cannot_be_attached(
    client: AsyncClient,
    env: IsolationEnv,
) -> None:
    response = await client.post(
        f"/v1/admin/products/{env.product_a}/media",
        json={"media_asset_id": str(env.media_asset_b)},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEDIA_NOT_FOUND"


async def test_media_list_only_returns_own_tenant(
    client: AsyncClient,
    env: IsolationEnv,
) -> None:
    response = await client.get("/v1/admin/media")

    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_platform_admin_has_no_tenant_scope(
    env: IsolationEnv,
) -> None:
    app.dependency_overrides[get_admin_context] = lambda: _platform_context()
    app.dependency_overrides[get_catalog_service] = lambda: env.catalog_service
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://api.test") as http:
            response = await http.get("/v1/admin/products")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
