from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

VARIANT_PATCH_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "price_cents",
        "compare_at_price_cents",
        "cost_cents",
        "weight_grams",
        "option_values",
        "is_active",
        "position",
    }
)


class ProductStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class Category:
    id: UUID
    slug: str
    name: str
    description: str | None
    position: int


@dataclass(frozen=True, slots=True)
class CategoryInput:
    slug: str
    name: str
    description: str | None = None
    position: int = 0


@dataclass(frozen=True, slots=True)
class VariantInput:
    sku: str
    name: str
    price_cents: int
    compare_at_price_cents: int | None = None
    cost_cents: int | None = None
    weight_grams: int | None = None
    stock: int = 0
    option_values: dict[str, str] = field(default_factory=dict)
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class ProductInput:
    slug: str
    name: str
    description: str | None
    category_id: UUID | None
    status: str
    brand: str | None
    tags: tuple[str, ...]
    variants: tuple[VariantInput, ...]


@dataclass(frozen=True, slots=True)
class ProductPatch:
    name: str | None = None
    description: str | None = None
    category_id: UUID | None = None
    status: str | None = None
    brand: str | None = None
    tags: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class ProductVariant:
    id: UUID
    sku: str
    name: str
    price_cents: int
    compare_at_price_cents: int | None
    option_values: dict[str, str]
    is_active: bool
    stock_available: int


@dataclass(frozen=True, slots=True)
class ProductSummary:
    id: UUID
    slug: str
    name: str
    status: ProductStatus
    category_id: UUID | None
    min_price_cents: int
    max_price_cents: int
    created_at: datetime
    primary_image_key: str | None = None


@dataclass(frozen=True, slots=True)
class ProductMediaVariant:
    format: str
    width: int
    height: int
    r2_key: str
    url: str = ""


@dataclass(frozen=True, slots=True)
class ProductMedia:
    media_asset_id: UUID
    r2_key: str
    alt: str | None
    blurhash: str | None
    width: int | None
    height: int | None
    position: int
    is_primary: bool
    status: str
    variants: tuple[ProductMediaVariant, ...]
    url: str = ""


@dataclass(frozen=True, slots=True)
class ProductDetail:
    summary: ProductSummary
    description: str | None
    brand: str | None
    tags: tuple[str, ...]
    variants: tuple[ProductVariant, ...]
    media: tuple[ProductMedia, ...] = ()
    images: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProductPage:
    items: tuple[ProductSummary, ...]
    next_cursor: str | None
