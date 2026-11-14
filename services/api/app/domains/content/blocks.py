"""Esquemas cerrados del block registry (ADR-0005). Sin HTML arbitrario jamás."""

from __future__ import annotations

import re
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_URL_PATTERN = r"^https?://[^\s<>\"']{1,2047}$"
_VIDEO_PATTERN = re.compile(
    r"^https://(www\.)?(youtube\.com|youtu\.be|player\.vimeo\.com)/[\w\-./?=&%]{1,300}$",
    re.IGNORECASE,
)
_HTML_TAG_PATTERN = re.compile(r"<[a-zA-Z]")


class ImageRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(max_length=2048, pattern=_URL_PATTERN)
    alt: str = Field(min_length=1, max_length=200)


class LinkRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=60)
    href: str = Field(max_length=2048, pattern=r"^(https?://|/)[^\s<>\"']*$")


class BlockBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class HeaderNavItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=60)
    href: str = Field(max_length=2048, pattern=r"^(https?://|/)[^\s<>\"']*$")


class HeaderBlock(BlockBase):
    type: Literal["header"] = "header"
    brand: str = Field(default="growup", min_length=1, max_length=100)
    nav: list[HeaderNavItem] = Field(default_factory=list, max_length=6)
    cta: LinkRef | None = None


class FooterColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=60)
    links: list[LinkRef] = Field(min_length=1, max_length=8)


class FooterBlock(BlockBase):
    type: Literal["footer"] = "footer"
    columns: list[FooterColumn] = Field(default_factory=list, max_length=4)
    legal_line: str | None = Field(default=None, max_length=300)


class HeroBlock(BlockBase):
    type: Literal["hero"] = "hero"
    eyebrow: str | None = Field(default=None, max_length=60)
    title: str = Field(min_length=1, max_length=120)
    subtitle: str | None = Field(default=None, max_length=300)
    image: ImageRef | None = None
    cta: LinkRef | None = None
    align: Literal["left", "center"] = "left"


class EditorialSplitBlock(BlockBase):
    type: Literal["editorial_split"] = "editorial_split"
    kicker: str | None = Field(default=None, max_length=60)
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=2000)
    image: ImageRef
    image_side: Literal["left", "right"] = "left"
    cta: LinkRef | None = None

    @field_validator("body")
    @classmethod
    def _no_html(cls, value: str) -> str:
        if _HTML_TAG_PATTERN.search(value):
            raise ValueError("El texto no puede contener HTML")
        return value


class ProductGridBlock(BlockBase):
    type: Literal["product_grid"] = "product_grid"
    title: str | None = Field(default=None, max_length=80)
    source: Literal["latest", "category", "manual"] = "latest"
    category_slug: str | None = Field(default=None, max_length=63, pattern=r"^[a-z0-9][a-z0-9-]*$")
    product_ids: list[UUID] = Field(default_factory=list, max_length=24)
    limit: int = Field(default=8, ge=1, le=24)
    show_price: bool = True


class ProductCarouselBlock(BlockBase):
    type: Literal["product_carousel"] = "product_carousel"
    title: str | None = Field(default=None, max_length=80)
    source: Literal["latest", "category", "manual"] = "latest"
    category_slug: str | None = Field(default=None, max_length=63, pattern=r"^[a-z0-9][a-z0-9-]*$")
    product_ids: list[UUID] = Field(default_factory=list, max_length=12)
    limit: int = Field(default=8, ge=1, le=12)


class CollectionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=80)
    href: str = Field(max_length=2048, pattern=r"^(https?://|/)[^\s<>\"']*$")
    image: ImageRef | None = None


class CollectionGridBlock(BlockBase):
    type: Literal["collection_grid"] = "collection_grid"
    title: str | None = Field(default=None, max_length=80)
    items: list[CollectionItem] = Field(min_length=1, max_length=12)


class ImageBannerBlock(BlockBase):
    type: Literal["image_banner"] = "image_banner"
    image: ImageRef
    href: str | None = Field(default=None, max_length=2048, pattern=r"^(https?://|/)[^\s<>\"']*$")
    title: str | None = Field(default=None, max_length=80)
    button_label: str | None = Field(default=None, max_length=40)
    ratio: Literal["16:9", "21:9", "4:3"] = "21:9"


class RichTextBlock(BlockBase):
    type: Literal["rich_text"] = "rich_text"
    markdown: str = Field(min_length=1, max_length=10000)
    width: Literal["narrow", "wide"] = "narrow"

    @field_validator("markdown")
    @classmethod
    def _no_html(cls, value: str) -> str:
        if _HTML_TAG_PATTERN.search(value):
            raise ValueError("El contenido no puede contener HTML")
        return value


class QuoteBlock(BlockBase):
    type: Literal["quote"] = "quote"
    text: str = Field(min_length=1, max_length=500)
    author: str | None = Field(default=None, max_length=120)


class GalleryImage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: ImageRef  # alt obligatorio por construcción


class GalleryBlock(BlockBase):
    type: Literal["gallery"] = "gallery"
    images: list[ImageRef] = Field(min_length=1, max_length=12)
    columns: Literal[2, 3, 4] = 3


class VideoEmbedBlock(BlockBase):
    type: Literal["video_embed"] = "video_embed"
    url: str = Field(max_length=600)
    title: str | None = Field(default=None, max_length=120)

    @field_validator("url")
    @classmethod
    def _video_url(cls, value: str) -> str:
        if not _VIDEO_PATTERN.match(value):
            raise ValueError("Solo se permiten URLs de YouTube o Vimeo")
        return value


class FaqItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=200)
    answer: str = Field(min_length=1, max_length=2000)


class FaqBlock(BlockBase):
    type: Literal["faq"] = "faq"
    title: str | None = Field(default=None, max_length=120)
    items: list[FaqItem] = Field(min_length=1, max_length=12)


class NewsletterBlock(BlockBase):
    type: Literal["newsletter"] = "newsletter"
    title: str | None = Field(default=None, max_length=120)
    subtitle: str | None = Field(default=None, max_length=300)
    cta_label: str = Field(default="Quiero recibir novedades", max_length=60)


class SpacerBlock(BlockBase):
    type: Literal["spacer"] = "spacer"
    height: Literal["sm", "md", "lg"] = "md"


class ColumnSlot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: int = Field(ge=1, le=12)
    blocks: list[Block] = Field(default_factory=list, max_length=12)


class ColumnsBlock(BlockBase):
    type: Literal["columns"] = "columns"
    columns: list[ColumnSlot] = Field(min_length=1, max_length=4)


Block = Annotated[
    HeaderBlock
    | FooterBlock
    | HeroBlock
    | EditorialSplitBlock
    | ProductGridBlock
    | ProductCarouselBlock
    | CollectionGridBlock
    | ImageBannerBlock
    | RichTextBlock
    | QuoteBlock
    | GalleryBlock
    | VideoEmbedBlock
    | FaqBlock
    | NewsletterBlock
    | SpacerBlock
    | ColumnsBlock,
    Field(discriminator="type"),
]

ColumnSlot.model_rebuild()

_MAX_BLOCKS_PER_PAGE = 256
_MAX_LAYOUT_BYTES = 65536


class PageLayout(BaseModel):
    """Layout completo de una versión de página."""

    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    blocks: list[Block] = Field(min_length=1, max_length=_MAX_BLOCKS_PER_PAGE)
