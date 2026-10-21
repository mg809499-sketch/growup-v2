from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_admin_context, get_media_service
from app.core.errors import AppError
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission
from app.domains.media.schemas import (
    CompleteUploadRequest,
    MediaAssetResponse,
    UploadUrlRequest,
    UploadUrlResponse,
)
from app.domains.media.service import MediaService

router = APIRouter(prefix="/v1/admin/media", tags=["admin-media"])


def _tenant_id(context: RequestContext) -> UUID:
    if context.tenant_id is None:
        raise AppError("FORBIDDEN", "Se requiere un tenant", 403)
    return context.tenant_id


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
    )
