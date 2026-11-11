from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class PageStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class Page:
    id: UUID
    tenant_id: UUID
    slug: str
    title: str
    status: PageStatus
    published_version_id: UUID | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PageVersion:
    id: UUID
    tenant_id: UUID
    page_id: UUID
    version: int
    layout: dict[str, object]
    created_by: UUID | None
    created_at: datetime
