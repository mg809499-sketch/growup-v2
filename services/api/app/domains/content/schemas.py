from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.content.blocks import PageLayout
from app.domains.content.models import Page, PageStatus, PageVersion

_SLUG_PATTERN = r"^[a-z0-9](?:[a-z0-9/-]{0,126}[a-z0-9])?$"


class PageSummary(BaseModel):
    id: UUID
    slug: str
    title: str
    status: PageStatus
    published_version_id: UUID | None
    updated_at: datetime


class PageDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    status: PageStatus
    published_version_id: UUID | None
    updated_at: datetime
    latest_version: int | None


class PageListResponse(BaseModel):
    items: list[PageSummary]
    total: int
    limit: int
    offset: int


class PageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=128, pattern=_SLUG_PATTERN)
    title: str = Field(min_length=1, max_length=200)


class PageUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=128, pattern=_SLUG_PATTERN)


class PageDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layout: PageLayout


class PublishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_id: UUID
    expected_version: int = Field(ge=1)


class StorefrontPageResponse(BaseModel):
    slug: str
    title: str
    version: int
    layout: dict[str, Any]


class ThemeResponse(BaseModel):
    tokens: dict[str, Any] | None


class ThemeUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tokens: dict[str, Any] = Field(min_length=1)


def page_summary(page: Page) -> PageSummary:
    return PageSummary(
        id=page.id,
        slug=page.slug,
        title=page.title,
        status=page.status,
        published_version_id=page.published_version_id,
        updated_at=page.updated_at,
    )


def page_detail(page: Page, latest_version: int | None) -> PageDetail:
    return PageDetail(
        id=page.id,
        slug=page.slug,
        title=page.title,
        status=page.status,
        published_version_id=page.published_version_id,
        updated_at=page.updated_at,
        latest_version=latest_version,
    )


def version_response(version: PageVersion) -> dict[str, Any]:
    return {
        "id": version.id,
        "page_id": version.page_id,
        "version": version.version,
        "layout": version.layout,
        "created_by": version.created_by,
        "created_at": version.created_at,
    }
