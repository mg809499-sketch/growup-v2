from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class MediaStatus(StrEnum):
    UPLOADING = "uploading"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class MediaAsset:
    id: UUID
    tenant_id: UUID
    r2_key: str
    mime: str
    size_bytes: int
    original_filename: str | None
    width: int | None
    height: int | None
    alt: str | None
    blurhash: str | None
    status: MediaStatus


@dataclass(frozen=True, slots=True)
class MediaVariant:
    format: str
    width: int
    height: int
    r2_key: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class UploadTicket:
    asset_id: UUID
    upload_url: str
    r2_key: str
    expires_in: int
