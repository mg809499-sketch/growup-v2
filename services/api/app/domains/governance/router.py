from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_governance_service, get_tenant_context
from app.core.errors import AppError
from app.domains.governance.models import Decision
from app.domains.governance.schemas import (
    AuditLogListResponse,
    AuditLogResponse,
    AuditVerifyResponse,
)
from app.domains.governance.service import GovernanceService
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission

router = APIRouter(prefix="/v1/admin/audit", tags=["admin-audit"])


def _tenant_id(context: RequestContext) -> UUID:
    if context.tenant_id is None:
        raise AppError("FORBIDDEN", "Se requiere un tenant", 403)
    return context.tenant_id


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[GovernanceService, Depends(get_governance_service)],
    action: Annotated[str | None, Query(max_length=120)] = None,
    decision: Annotated[Decision | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    before_seq: Annotated[int | None, Query(ge=1)] = None,
) -> AuditLogListResponse:
    require_permission(context, Permission.AUDIT_READ)
    records, next_cursor = await service.list_logs(
        _tenant_id(context),
        action=action,
        decision=decision.value if decision is not None else None,
        limit=limit,
        before_seq=before_seq,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.from_record(record) for record in records],
        next_cursor=next_cursor,
    )


@router.get("/verify", response_model=AuditVerifyResponse)
async def verify_audit_chain(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[GovernanceService, Depends(get_governance_service)],
) -> AuditVerifyResponse:
    require_permission(context, Permission.AUDIT_READ)
    tenant_id = _tenant_id(context)
    valid = await service.verify_tenant_chain(tenant_id)
    return AuditVerifyResponse(chain_key=str(tenant_id), valid=valid)
