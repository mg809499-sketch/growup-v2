from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.catalog.models import (
    Category,
    ProductDetail,
    ProductMedia,
    ProductMediaVariant,
    ProductStatus,
    ProductSummary,
    ProductVariant,
)

_SLUG_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=63, pattern=_SLUG_PATTERN)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    position: int = Field(default=0, ge=0)


class CategoryResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    position: int

    @classmethod
    def from_domain(cls, category: Category) -> CategoryResponse:
        return cls(
            id=category.id,
            slug=category.slug,
            name=category.name,
            description=category.description,
            position=category.position,
        )


class VariantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    price_cents: int = Field(gt=0)
    compare_at_price_cents: int | None = Field(default=None, ge=0)
    cost_cents: int | None = Field(default=None, ge=0)
    weight_grams: int | None = Field(default=None, ge=0)
    stock: int = Field(default=0, ge=0)
    option_values: dict[str, str] = Field(default_factory=dict)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_compare_at(self) -> VariantCreate:
        if (
            self.compare_at_price_cents is not None
            and self.compare_at_price_cents < self.price_cents
        ):
            raise ValueError("compare_at_price_cents debe ser >= price_cents")
        return self


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=63, pattern=_SLUG_PATTERN)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    category_id: UUID | None = None
    status: Literal["draft", "active"] = "draft"
    brand: str | None = Field(default=None, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=20)
    variants: list[VariantCreate] = Field(min_length=1, max_length=100)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    category_id: UUID | None = None
    status: Literal["draft", "active", "archived"] | None = None
    brand: str | None = Field(default=None, max_length=100)
    tags: list[str] | None = Field(default=None, max_length=20)


class MediaAttachRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    media_asset_id: UUID
    position: int | None = Field(default=None, ge=0)
    is_primary: bool | None = None


class VariantResponse(BaseModel):
    id: UUID
    sku: str
    name: str
    price_cents: int
    compare_at_price_cents: int | None
    option_values: dict[str, str]
    is_active: bool
    stock_available: int

    @classmethod
    def from_domain(cls, variant: ProductVariant) -> VariantResponse:
        return cls(
            id=variant.id,
            sku=variant.sku,
            name=variant.name,
            price_cents=variant.price_cents,
            compare_at_price_cents=variant.compare_at_price_cents,
            option_values=variant.option_values,
            is_active=variant.is_active,
            stock_available=variant.stock_available,
        )


class ProductSummaryResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    status: ProductStatus
    category_id: UUID | None
    min_price_cents: int
    max_price_cents: int

    @classmethod
    def from_domain(cls, product: ProductSummary) -> ProductSummaryResponse:
        return cls(
            id=product.id,
            slug=product.slug,
            name=product.name,
            status=product.status,
            category_id=product.category_id,
            min_price_cents=product.min_price_cents,
            max_price_cents=product.max_price_cents,
        )


class ProductMediaVariantResponse(BaseModel):
    format: str
    width: int
    height: int
    r2_key: str

    @classmethod
    def from_domain(
        cls,
        variant: ProductMediaVariant,
    ) -> ProductMediaVariantResponse:
        return cls(
            format=variant.format,
            width=variant.width,
            height=variant.height,
            r2_key=variant.r2_key,
        )


class ProductMediaResponse(BaseModel):
    media_asset_id: UUID
    r2_key: str
    alt: str | None
    blurhash: str | None
    width: int | None
    height: int | None
    position: int
    is_primary: bool
    status: str
    variants: list[ProductMediaVariantResponse]

    @classmethod
    def from_domain(cls, media: ProductMedia) -> ProductMediaResponse:
        return cls(
            media_asset_id=media.media_asset_id,
            r2_key=media.r2_key,
            alt=media.alt,
            blurhash=media.blurhash,
            width=media.width,
            height=media.height,
            position=media.position,
            is_primary=media.is_primary,
            status=media.status,
            variants=[
                ProductMediaVariantResponse.from_domain(variant)
                for variant in media.variants
            ],
        )


class ProductDetailResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    status: ProductStatus
    category_id: UUID | None
    brand: str | None
    tags: list[str]
    min_price_cents: int
    max_price_cents: int
    variants: list[VariantResponse]
    images: list[str]
    media: list[ProductMediaResponse]

    @classmethod
    def from_domain(cls, detail: ProductDetail) -> ProductDetailResponse:
        return cls(
            id=detail.summary.id,
            slug=detail.summary.slug,
            name=detail.summary.name,
            description=detail.description,
            status=detail.summary.status,
            category_id=detail.summary.category_id,
            brand=detail.brand,
            tags=list(detail.tags),
            min_price_cents=detail.summary.min_price_cents,
            max_price_cents=detail.summary.max_price_cents,
            variants=[VariantResponse.from_domain(variant) for variant in detail.variants],
            images=list(detail.images),
            media=[ProductMediaResponse.from_domain(media) for media in detail.media],
        )


class ProductListResponse(BaseModel):
    items: list[ProductSummaryResponse]
    next_cursor: str | None
