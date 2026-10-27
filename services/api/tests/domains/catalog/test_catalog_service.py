from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.errors import AppError
from app.domains.catalog.models import (
    ProductDetail,
    ProductInput,
    ProductMedia,
    ProductMediaVariant,
    ProductPage,
    ProductPatch,
    ProductStatus,
    ProductSummary,
    VariantInput,
)
from app.domains.catalog.repository import CatalogRepository
from app.domains.catalog.service import CatalogService


def _variant(
    *,
    sku: str = "CAM-1",
    price_cents: int = 8900000,
    compare_at_price_cents: int | None = None,
    is_active: bool = True,
) -> VariantInput:
    return VariantInput(
        sku=sku,
        name="M",
        price_cents=price_cents,
        compare_at_price_cents=compare_at_price_cents,
        stock=5,
        option_values={"Talla": "M"},
        is_active=is_active,
    )


def _product_input(
    *,
    variants: tuple[VariantInput, ...] | None = None,
    status: str = "draft",
) -> ProductInput:
    return ProductInput(
        slug="camiseta",
        name="Camiseta",
        description="Camiseta de algodón",
        category_id=None,
        status=status,
        brand="Growup",
        tags=("nuevo",),
        variants=variants if variants is not None else (_variant(),),
    )


def _detail() -> ProductDetail:
    summary = ProductSummary(
        id=uuid4(),
        slug="camiseta",
        name="Camiseta",
        status=ProductStatus.DRAFT,
        category_id=None,
        min_price_cents=8900000,
        max_price_cents=8900000,
        created_at=datetime.now(UTC),
    )
    return ProductDetail(
        summary=summary,
        description="Camiseta de algodón",
        brand="Growup",
        tags=("nuevo",),
        variants=(),
    )


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=CatalogRepository)


async def test_create_product_rejects_no_variants(repository: AsyncMock) -> None:
    service = CatalogService(repository)

    with pytest.raises(AppError) as exc_info:
        await service.create_product(uuid4(), _product_input(variants=()))

    assert exc_info.value.code == "PRODUCT_WITHOUT_VARIANTS"


async def test_create_product_rejects_duplicate_skus(repository: AsyncMock) -> None:
    service = CatalogService(repository)
    data = _product_input(
        variants=(
            _variant(sku="CAM-1"),
            _variant(sku="CAM-1"),
        )
    )

    with pytest.raises(AppError) as exc_info:
        await service.create_product(uuid4(), data)

    assert exc_info.value.code == "DUPLICATE_SKU"


async def test_create_product_rejects_invalid_price(repository: AsyncMock) -> None:
    service = CatalogService(repository)

    with pytest.raises(AppError) as exc_info:
        await service.create_product(uuid4(), _product_input(variants=(_variant(price_cents=0),)))

    assert exc_info.value.code == "INVALID_PRICE"


async def test_create_product_rejects_invalid_compare_at(repository: AsyncMock) -> None:
    service = CatalogService(repository)
    data = _product_input(
        variants=(_variant(price_cents=10000, compare_at_price_cents=9000),)
    )

    with pytest.raises(AppError) as exc_info:
        await service.create_product(uuid4(), data)

    assert exc_info.value.code == "INVALID_COMPARE_AT_PRICE"


async def test_active_product_requires_active_variant(repository: AsyncMock) -> None:
    service = CatalogService(repository)
    data = _product_input(
        variants=(_variant(is_active=False),),
        status="active",
    )

    with pytest.raises(AppError) as exc_info:
        await service.create_product(uuid4(), data)

    assert exc_info.value.code == "PRODUCT_WITHOUT_ACTIVE_VARIANTS"


async def test_create_product_delegates_to_repository(repository: AsyncMock) -> None:
    detail = _detail()
    repository.create_product.return_value = detail
    service = CatalogService(repository)

    result = await service.create_product(uuid4(), _product_input())

    assert result == detail
    repository.create_product.assert_awaited_once()


async def test_list_products_validates_limit(repository: AsyncMock) -> None:
    service = CatalogService(repository)

    with pytest.raises(AppError) as exc_info:
        await service.list_products(
            uuid4(),
            status=None,
            category=None,
            query=None,
            limit=0,
            cursor=None,
        )

    assert exc_info.value.code == "INVALID_LIMIT"


async def test_list_products_validates_status(repository: AsyncMock) -> None:
    service = CatalogService(repository)

    with pytest.raises(AppError) as exc_info:
        await service.list_products(
            uuid4(),
            status="bogus",
            category=None,
            query=None,
            limit=20,
            cursor=None,
        )

    assert exc_info.value.code == "INVALID_STATUS"


async def test_list_products_delegates_to_repository(repository: AsyncMock) -> None:
    page = ProductPage(items=(), next_cursor=None)
    repository.list_products.return_value = page
    service = CatalogService(repository)

    result = await service.list_products(
        uuid4(),
        status="active",
        category="ropa",
        query="camiseta",
        limit=20,
        cursor=None,
    )

    assert result == page
    repository.list_products.assert_awaited_once()


async def test_update_product_validates_status(repository: AsyncMock) -> None:
    service = CatalogService(repository)

    with pytest.raises(AppError) as exc_info:
        await service.update_product(
            uuid4(),
            uuid4(),
            ProductPatch(status="bogus"),
        )

    assert exc_info.value.code == "INVALID_STATUS"


async def test_attach_media_rejects_negative_position(repository: AsyncMock) -> None:
    service = CatalogService(repository)

    with pytest.raises(AppError) as exc_info:
        await service.attach_media(
            uuid4(),
            uuid4(),
            uuid4(),
            position=-1,
            is_primary=False,
        )

    assert exc_info.value.code == "INVALID_POSITION"


async def test_attach_media_delegates_to_repository(repository: AsyncMock) -> None:
    detail = _detail()
    repository.attach_media.return_value = detail
    service = CatalogService(repository)
    tenant_id = uuid4()
    product_id = uuid4()
    media_asset_id = uuid4()

    result = await service.attach_media(
        tenant_id,
        product_id,
        media_asset_id,
        position=2,
        is_primary=True,
    )

    assert result == detail
    repository.attach_media.assert_awaited_once_with(
        tenant_id,
        product_id,
        media_asset_id,
        position=2,
        is_primary=True,
    )


async def test_detach_media_delegates_to_repository(repository: AsyncMock) -> None:
    repository.detach_media.return_value = True
    service = CatalogService(repository)
    tenant_id = uuid4()
    product_id = uuid4()
    media_asset_id = uuid4()

    result = await service.detach_media(tenant_id, product_id, media_asset_id)

    assert result is True
    repository.detach_media.assert_awaited_once_with(
        tenant_id,
        product_id,
        media_asset_id,
    )


async def test_update_variant_rejects_invalid_changes(repository: AsyncMock) -> None:
    service = CatalogService(repository)
    tenant_id = uuid4()
    product_id = uuid4()
    variant_id = uuid4()

    cases = [
        ({"unknown": 1}, "INVALID_VARIANT_FIELD"),
        ({"name": "   "}, "INVALID_NAME"),
        ({"price_cents": 0}, "INVALID_PRICE"),
        ({"compare_at_price_cents": -1}, "INVALID_VARIANT_FIELD"),
        ({"position": -1}, "INVALID_POSITION"),
        ({"is_active": "yes"}, "INVALID_VARIANT_FIELD"),
        ({"option_values": []}, "INVALID_VARIANT_FIELD"),
    ]

    for changes, code in cases:
        with pytest.raises(AppError) as exc_info:
            await service.update_variant(
                tenant_id,
                product_id,
                variant_id,
                changes=changes,  # type: ignore[arg-type]
            )
        assert exc_info.value.code == code


async def test_update_variant_delegates_to_repository(repository: AsyncMock) -> None:
    detail = _detail()
    repository.update_variant.return_value = detail
    service = CatalogService(repository)
    tenant_id = uuid4()
    product_id = uuid4()
    variant_id = uuid4()
    changes = {"price_cents": 9900000, "is_active": False}

    result = await service.update_variant(
        tenant_id,
        product_id,
        variant_id,
        changes=changes,
    )

    assert result == detail
    repository.update_variant.assert_awaited_once_with(
        tenant_id,
        product_id,
        variant_id,
        changes,
    )


async def test_delete_variant_delegates_to_repository(repository: AsyncMock) -> None:
    repository.delete_variant.return_value = True
    service = CatalogService(repository)
    tenant_id = uuid4()
    product_id = uuid4()
    variant_id = uuid4()

    result = await service.delete_variant(tenant_id, product_id, variant_id)

    assert result is True
    repository.delete_variant.assert_awaited_once_with(
        tenant_id,
        product_id,
        variant_id,
    )


async def test_add_variant_validates_and_delegates(repository: AsyncMock) -> None:
    detail = _detail()
    repository.add_variant.return_value = detail
    service = CatalogService(repository)
    tenant_id = uuid4()
    product_id = uuid4()
    data = _variant()

    with pytest.raises(AppError) as invalid_price:
        await service.add_variant(
            tenant_id,
            product_id,
            _variant(price_cents=0),
        )
    assert invalid_price.value.code == "INVALID_PRICE"

    result = await service.add_variant(tenant_id, product_id, data)

    assert result == detail
    repository.add_variant.assert_awaited_once_with(tenant_id, product_id, data)


async def test_get_product_maps_media_urls(repository: AsyncMock) -> None:
    media = ProductMedia(
        media_asset_id=uuid4(),
        r2_key="tenant/t/originals/a.jpg",
        alt="Camisa",
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
                r2_key="tenant/t/variants/a/320.webp",
            ),
        ),
    )
    detail = replace(_detail(), media=(media,), images=(media.r2_key,))
    repository.get_product_by_slug.return_value = detail
    service = CatalogService(repository, "https://cdn.example/")

    result = await service.get_product(uuid4(), "camiseta", public_only=True)

    assert result is not None
    assert result.media[0].url == "https://cdn.example/tenant/t/originals/a.jpg"
    assert (
        result.media[0].variants[0].url
        == "https://cdn.example/tenant/t/variants/a/320.webp"
    )
    assert result.images == ("https://cdn.example/tenant/t/originals/a.jpg",)
