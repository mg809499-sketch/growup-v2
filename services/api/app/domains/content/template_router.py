from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app import runtime
from app.api.deps import get_tenant_context, require_tenant_id
from app.core.errors import AppError
from app.domains.content.service import PageService
from app.domains.content.templates import TemplateSummary
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission

router = APIRouter(prefix="/v1/admin", tags=["admin-content-templates"])


class ApplyTemplateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    expected_version: int | None = Field(default=None, ge=0)


class ApplyTemplateResponse(BaseModel):
    id: str
    version: int


def get_page_service() -> PageService:
    if runtime.page_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El servicio de contenido no está configurado",
            503,
        )
    return runtime.page_service


@router.get("/templates", response_model=list[TemplateSummary])
async def list_templates(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
) -> list[TemplateSummary]:
    require_permission(context, Permission.CONTENT_READ)
    require_tenant_id(context)
    return await service.list_templates()


@router.post("/pages/{page_id}/apply-template", response_model=ApplyTemplateResponse)
async def apply_template(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    page_id: UUID,
    body: ApplyTemplateRequest,
) -> ApplyTemplateResponse:
    require_permission(context, Permission.CONTENT_WRITE)
    tenant_id = require_tenant_id(context)
    version = await service.apply_template(
        tenant_id,
        page_id,
        body.template_id,
        actor_id=context.actor.user_id,
        expected_version=body.expected_version,
    )
    return ApplyTemplateResponse(id=str(version.id), version=version.version)
