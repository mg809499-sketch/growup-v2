from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_tenant_resolver
from app.core.errors import AppError
from app.domains.tenants.schemas import BootstrapResponse
from app.domains.tenants.service import TenantResolver

router = APIRouter(prefix="/v1/storefront", tags=["storefront"])


@router.get("/bootstrap", response_model=BootstrapResponse)
async def bootstrap(
    request: Request,
    resolver: Annotated[TenantResolver, Depends(get_tenant_resolver)],
) -> BootstrapResponse:
    host = request.headers.get("X-Storefront-Host") or request.headers.get("host")
    if not host:
        raise AppError("TENANT_NOT_FOUND", "Host requerido", 404)

    return BootstrapResponse.from_domain(await resolver.bootstrap(host))
