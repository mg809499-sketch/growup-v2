from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_admin_context
from app.domains.identity.models import RequestContext
from app.domains.identity.schemas import MeResponse

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/me", response_model=MeResponse)
async def me(
    context: Annotated[RequestContext, Depends(get_admin_context)],
) -> MeResponse:
    return MeResponse.from_context(context)
