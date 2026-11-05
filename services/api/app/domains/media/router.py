from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_admin_context, get_media_service
from app.core.errors import AppError
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission
from app.domains.media.models import MediaAsset, MediaVariant
from app.domains.media.schemas import (
    CompleteUploadRequest,
    MediaAssetDetailResponse,
    MediaAssetListResponse,
    MediaAssetResponse,
    MediaAssetUpdate,
    MediaVariantResponse,
    UploadUrlRequest,
    UploadUrlResponse,
)
from app.domains.media.service import MediaService

router = APIRouter(prefix="/v1/admin/media", tags=["admin-media"])


def _tenant_id(context: RequestContext) -> UUID:
    if context.tenant_id is None:
        raise AppError("FORBIDDEN", "Se requiere un tenant", 403)
    return context.tenant_id


def _asset_response(asset: MediaAsset) -> MediaAssetResponse:
    return MediaAssetResponse(
        id=asset.id,
        status=asset.status,
        mime=asset.mime,
        size_bytes=asset.size_bytes,
        width=asset.width,
        height=asset.height,
        alt=asset.alt,
        blurhash=asset.blurhash,
        original_filename=asset.original_filename,
        r2_key=asset.r2_key,
    )


def _variant_response(variant: MediaVariant) -> MediaVariantResponse:
    return MediaVariantResponse(
        format=variant.format,
        width=variant.width,
        height=variant.height,
        r2_key=variant.r2_key,
        size_bytes=variant.size_bytes,
    )


@router.post(
    "/upload-url",
    response_model=UploadUrlResponse,
    status_code=201,
)
async def create_upload_url(
    payload: UploadUrlRequest,
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[MediaService, Depends(get_media_service)],
) -> UploadUrlResponse:
    require_permission(context, Permission.CATALOG_WRITE)
    ticket = await service.create_upload(
        _tenant_id(context),
        filename=payload.filename,
        content_type=payload.content_type,
        size_bytes=payload.size_bytes,
    )
    return UploadUrlResponse(
        asset_id=ticket.asset_id,
        upload_url=ticket.upload_url,
        r2_key=ticket.r2_key,
        expires_in=ticket.expires_in,
    )


@router.post(
    "/{asset_id}/complete",
    response_model=MediaAssetResponse,
    status_code=202,
)
async def complete_upload(
    asset_id: UUID,
    payload: CompleteUploadRequest,
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[MediaService, Depends(get_media_service)],
) -> MediaAssetResponse:
    require_permission(context, Permission.CATALOG_WRITE)
    asset = await service.complete_upload(
        _tenant_id(context),
        asset_id,
        alt=payload.alt,
    )
    return _asset_response(asset)


@router.get("", response_model=MediaAssetListResponse)
async def list_media_assets(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[MediaService, Depends(get_media_service)],
    status: Annotated[Literal["uploading", "ready", "failed"] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
) -> MediaAssetListResponse:
    require_permission(context, Permission.CATALOG_READ)
    assets, total = await service.list_assets(
        _tenant_id(context),
        status=status,
        limit=limit,
        offset=offset,
    )
    return MediaAssetListResponse(
        items=[_asset_response(asset) for asset in assets],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{asset_id}", response_model=MediaAssetDetailResponse)
async def get_media_asset(
    asset_id: UUID,
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[MediaService, Depends(get_media_service)],
) -> MediaAssetDetailResponse:
    require_permission(context, Permission.CATALOG_READ)
    asset, variants = await service.get_asset_detail(_tenant_id(context), asset_id)
    return MediaAssetDetailResponse(
        id=asset.id,
        status=asset.status,
        mime=asset.mime,
        size_bytes=asset.size_bytes,
        width=asset.width,
        height=asset.height,
        alt=asset.alt,
        blurhash=asset.blurhash,
        original_filename=asset.original_filename,
        r2_key=asset.r2_key,
        variants=[_variant_response(variant) for variant in variants],
    )


@router.patch("/{asset_id}", response_model=MediaAssetResponse)
async def update_media_asset(
    asset_id: UUID,
    payload: MediaAssetUpdate,
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[MediaService, Depends(get_media_service)],
) -> MediaAssetResponse:
    require_permission(context, Permission.CATALOG_WRITE)
    asset = await service.update_alt(
        _tenant_id(context),
        asset_id,
        alt=payload.alt,
    )
    return _asset_response(asset)


@router.delete("/{asset_id}", status_code=204)
async def delete_media_asset(
    asset_id: UUID,
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[MediaService, Depends(get_media_service)],
) -> Response:
    require_permission(context, Permission.CATALOG_WRITE)
    await service.delete_asset(_tenant_id(context), asset_id)
    return Response(status_code=204)
