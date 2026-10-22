from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_catalog_service, get_storefront_tenant, get_tenant_context
from app.domains.catalog.models import (
    Category,
    ProductDetail,
    ProductMedia,
    ProductMediaVariant,
    ProductPage,
    ProductStatus,
    ProductSummary,
    ProductVariant,
)
from app.domains.identity.models import Actor, RequestContext, Role
from app.domains.identity.permissions import permissions_for
from app.domains.tenants.models import Tenant, TenantStatus
from app.main import app

TENANT_ID = uuid4()


def _context(role: Role = Role.OWNER) -> RequestContext:
    actor = Actor(
        user_id=uuid4(),
        tenant_id=TENANT_ID,
        role=role,
        email="owner@example.com",
    )
    return RequestContext(
        tenant_id=TENANT_ID,
        actor=actor,
        permissions=permissions_for(role),
        trace_id="trace-1",
        request_id="req-1",
    )


def _tenant() -> Tenant:
    return Tenant(
        id=TENANT_ID,
        slug="ropa",
        name="Ropa",
        status=TenantStatus.ACTIVE,
    )


def _summary() -> ProductSummary:
    return ProductSummary(
        id=uuid4(),
        slug="camiseta",
        name="Camiseta",
        status=ProductStatus.ACTIVE,
        category_id=None,
        min_price_cents=8900000,
        max_price_cents=8900000,
        created_at=datetime.now(UTC),
    )


def _media() -> ProductMedia:
    return ProductMedia(
        media_asset_id=uuid4(),
        r2_key="tenant/t/originals/camiseta.jpg",
        alt="Camiseta roja",
        blurhash="LDT9R{]9fQ]9",
        width=800,
        height=600,
        position=0,
        is_primary=True,
        status="ready",
        variants=(
            ProductMediaVariant(
                format="webp",
                width=320,
                height=240,
                r2_key="tenant/t/variants/camiseta/320.webp",
            ),
        ),
    )


def _detail(*, media: tuple[ProductMedia, ...] = ()) -> ProductDetail:
    variant = ProductVariant(
        id=uuid4(),
        sku="CAM-1",
        name="M",
        price_cents=8900000,
        compare_at_price_cents=None,
        option_values={"Talla": "M"},
        is_active=True,
        stock_available=5,
    )
    return ProductDetail(
        summary=_summary(),
        description="Camiseta de algodón",
        brand="Growup",
        tags=("nuevo",),
        variants=(variant,),
        media=media,
        images=tuple(item.r2_key for item in media),
    )


class FakeCatalogService:
    def __init__(
        self,
        *,
        page: ProductPage | None = None,
        detail: ProductDetail | None = None,
        category: Category | None = None,
        categories: tuple[Category, ...] = (),
        detach_result: bool = True,
    ) -> None:
        self.page = page or ProductPage(items=(), next_cursor=None)
        self.detail = detail
        self.category = category
        self.categories = categories
        self.detach_result = detach_result
        self.calls: list[tuple[str, object]] = []

    async def list_products(self, tenant_id: object, **kwargs: object) -> ProductPage:
        self.calls.append(("list_products", kwargs))
        return self.page

    async def create_product(self, tenant_id: object, data: object) -> ProductDetail:
        self.calls.append(("create_product", data))
        assert self.detail is not None
        return self.detail

    async def get_product_by_id(
        self,
        tenant_id: object,
        product_id: object,
    ) -> ProductDetail | None:
        return self.detail

    async def update_product(
        self,
        tenant_id: object,
        product_id: object,
        patch: object,
    ) -> ProductDetail | None:
        return self.detail

    async def attach_media(
        self,
        tenant_id: object,
        product_id: object,
        media_asset_id: object,
        *,
        position: int | None,
        is_primary: bool | None,
    ) -> ProductDetail | None:
        self.calls.append(
            (
                "attach_media",
                {
                    "product_id": product_id,
                    "media_asset_id": media_asset_id,
                    "position": position,
                    "is_primary": is_primary,
                },
            )
        )
        return self.detail

    async def detach_media(
        self,
        tenant_id: object,
        product_id: object,
        media_asset_id: object,
    ) -> bool:
        self.calls.append(
            (
                "detach_media",
                {
                    "product_id": product_id,
                    "media_asset_id": media_asset_id,
                },
            )
        )
        return self.detach_result

    async def update_variant(
        self,
        tenant_id: object,
        product_id: object,
        variant_id: object,
        *,
        changes: object,
    ) -> ProductDetail | None:
        self.calls.append(
            (
                "update_variant",
                {
                    "product_id": product_id,
                    "variant_id": variant_id,
                    "changes": changes,
                },
            )
        )
        return self.detail

    async def delete_variant(
        self,
        tenant_id: object,
        product_id: object,
        variant_id: object,
    ) -> bool:
        self.calls.append(
            (
                "delete_variant",
                {
                    "product_id": product_id,
                    "variant_id": variant_id,
                },
            )
        )
        return self.detach_result

    async def list_categories(self, tenant_id: object) -> tuple[Category, ...]:
        return self.categories

    async def create_category(self, tenant_id: object, data: object) -> Category:
        assert self.category is not None
        return self.category

    async def get_product(
        self,
        tenant_id: object,
        slug: str,
        *,
        public_only: bool,
    ) -> ProductDetail | None:
        return self.detail


@pytest.fixture(autouse=True)
def _clear_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def test_admin_list_products() -> None:
    fake = FakeCatalogService(
        page=ProductPage(items=(_summary(),), next_cursor="next-cursor")
    )
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/v1/admin/products")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["slug"] == "camiseta"
    assert payload["next_cursor"] == "next-cursor"


def test_admin_create_product() -> None:
    fake = FakeCatalogService(detail=_detail())
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        "/v1/admin/products",
        json={
            "slug": "camiseta",
            "name": "Camiseta",
            "status": "draft",
            "variants": [
                {
                    "sku": "CAM-1",
                    "name": "M",
                    "price_cents": 8900000,
                    "stock": 5,
                    "option_values": {"Talla": "M"},
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["slug"] == "camiseta"
    assert payload["variants"][0]["sku"] == "CAM-1"
    assert payload["variants"][0]["stock_available"] == 5


def test_admin_product_not_found() -> None:
    fake = FakeCatalogService(detail=None)
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.get(f"/v1/admin/products/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_admin_list_products_forbidden_for_packer() -> None:
    fake = FakeCatalogService()
    app.dependency_overrides[get_tenant_context] = lambda: _context(Role.PACKER)
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/v1/admin/products")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_create_category() -> None:
    category = Category(
        id=uuid4(),
        slug="ropa",
        name="Ropa",
        description=None,
        position=0,
    )
    fake = FakeCatalogService(category=category)
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        "/v1/admin/categories",
        json={"slug": "ropa", "name": "Ropa"},
    )

    assert response.status_code == 201
    assert response.json()["slug"] == "ropa"


def test_admin_update_product() -> None:
    fake = FakeCatalogService(detail=_detail())
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.patch(
        f"/v1/admin/products/{uuid4()}",
        json={"status": "active"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_admin_attach_media() -> None:
    media = _media()
    fake = FakeCatalogService(detail=_detail(media=(media,)))
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)
    product_id = uuid4()

    response = client.post(
        f"/v1/admin/products/{product_id}/media",
        json={
            "media_asset_id": str(media.media_asset_id),
            "position": 2,
            "is_primary": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["media"][0]["r2_key"] == media.r2_key
    assert payload["media"][0]["status"] == "ready"
    assert payload["media"][0]["variants"][0]["format"] == "webp"
    assert payload["images"] == [media.r2_key]
    assert fake.calls[-1] == (
        "attach_media",
        {
            "product_id": product_id,
            "media_asset_id": media.media_asset_id,
            "position": 2,
            "is_primary": True,
        },
    )


def test_admin_attach_media_product_not_found() -> None:
    fake = FakeCatalogService(detail=None)
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        f"/v1/admin/products/{uuid4()}/media",
        json={"media_asset_id": str(uuid4())},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_admin_detach_media() -> None:
    fake = FakeCatalogService(detail=_detail())
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.delete(
        f"/v1/admin/products/{uuid4()}/media/{uuid4()}",
    )

    assert response.status_code == 204
    assert response.content == b""


def test_admin_detach_media_not_found() -> None:
    fake = FakeCatalogService(detail=_detail(), detach_result=False)
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.delete(
        f"/v1/admin/products/{uuid4()}/media/{uuid4()}",
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PRODUCT_MEDIA_NOT_FOUND"


def test_attach_media_forbidden_for_packer() -> None:
    fake = FakeCatalogService(detail=_detail())
    app.dependency_overrides[get_tenant_context] = lambda: _context(Role.PACKER)
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        f"/v1/admin/products/{uuid4()}/media",
        json={"media_asset_id": str(uuid4())},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert fake.calls == []


def test_storefront_product_detail_includes_media() -> None:
    media = _media()
    fake = FakeCatalogService(detail=_detail(media=(media,)))
    app.dependency_overrides[get_storefront_tenant] = lambda: _tenant()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/v1/storefront/products/camiseta")

    assert response.status_code == 200
    assert response.json()["media"][0]["alt"] == "Camiseta roja"
    assert response.json()["media"][0]["is_primary"] is True


def test_admin_update_variant() -> None:
    fake = FakeCatalogService(detail=_detail())
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)
    product_id = uuid4()
    variant_id = uuid4()

    response = client.patch(
        f"/v1/admin/products/{product_id}/variants/{variant_id}",
        json={"price_cents": 9900000, "is_active": False},
    )

    assert response.status_code == 200
    call = fake.calls[-1][1]
    assert isinstance(call, dict)
    assert call["product_id"] == product_id
    assert call["variant_id"] == variant_id
    assert call["changes"] == {"price_cents": 9900000, "is_active": False}


def test_admin_update_variant_not_found() -> None:
    fake = FakeCatalogService(detail=None)
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.patch(
        f"/v1/admin/products/{uuid4()}/variants/{uuid4()}",
        json={"price_cents": 9900000},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VARIANT_NOT_FOUND"


def test_admin_delete_variant() -> None:
    fake = FakeCatalogService(detail=_detail())
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)
    product_id = uuid4()
    variant_id = uuid4()

    response = client.delete(
        f"/v1/admin/products/{product_id}/variants/{variant_id}",
    )

    assert response.status_code == 204
    assert fake.calls[-1] == (
        "delete_variant",
        {"product_id": product_id, "variant_id": variant_id},
    )


def test_admin_delete_variant_not_found() -> None:
    fake = FakeCatalogService(detail=_detail(), detach_result=False)
    app.dependency_overrides[get_tenant_context] = lambda: _context()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.delete(
        f"/v1/admin/products/{uuid4()}/variants/{uuid4()}",
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VARIANT_NOT_FOUND"


def test_storefront_list_products_uses_active_status() -> None:
    fake = FakeCatalogService(page=ProductPage(items=(_summary(),), next_cursor=None))
    app.dependency_overrides[get_storefront_tenant] = lambda: _tenant()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/v1/storefront/products")

    assert response.status_code == 200
    assert response.json()["items"][0]["slug"] == "camiseta"
    assert fake.calls[-1][0] == "list_products"
    assert fake.calls[-1][1]["status"] == "active"  # type: ignore[index]


def test_storefront_product_detail() -> None:
    fake = FakeCatalogService(detail=_detail())
    app.dependency_overrides[get_storefront_tenant] = lambda: _tenant()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/v1/storefront/products/camiseta")

    assert response.status_code == 200
    assert response.json()["variants"][0]["option_values"] == {"Talla": "M"}


def test_storefront_product_not_found() -> None:
    fake = FakeCatalogService(detail=None)
    app.dependency_overrides[get_storefront_tenant] = lambda: _tenant()
    app.dependency_overrides[get_catalog_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/v1/storefront/products/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PRODUCT_NOT_FOUND"
