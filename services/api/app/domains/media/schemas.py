from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.media.models import MediaStatus


class UploadUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0)


class UploadUrlResponse(BaseModel):
    asset_id: UUID
    upload_url: str
    r2_key: str
    expires_in: int


class CompleteUploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alt: str = Field(min_length=1, max_length=300)


class MediaAssetResponse(BaseModel):
    id: UUID
    status: MediaStatus
    mime: str
    size_bytes: int
    width: int | None
    height: int | None
    alt: str | None
    blurhash: str | None
    original_filename: str | None
    r2_key: str


class MediaAssetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alt: str = Field(min_length=1, max_length=300)


class MediaVariantResponse(BaseModel):
    format: str
    width: int
    height: int
    r2_key: str
    size_bytes: int


class MediaAssetDetailResponse(BaseModel):
    id: UUID
    status: MediaStatus
    mime: str
    size_bytes: int
    width: int | None
    height: int | None
    alt: str | None
    blurhash: str | None
    original_filename: str | None
    r2_key: str
    variants: list[MediaVariantResponse]


class MediaAssetListResponse(BaseModel):
    items: list[MediaAssetResponse]
