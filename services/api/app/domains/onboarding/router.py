from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import VerifiedUser, get_onboarding_service, get_verified_user
from app.domains.onboarding.schemas import SignupRequest, SignupResponse
from app.domains.onboarding.service import OnboardingService

router = APIRouter(prefix="/v1/onboarding", tags=["onboarding"])


@router.post("/complete", response_model=SignupResponse, status_code=201)
async def complete_signup(
    payload: SignupRequest,
    user: Annotated[VerifiedUser, Depends(get_verified_user)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> SignupResponse:
    result = await service.complete_signup(
        user_id=user.user_id,
        email=user.email,
        payload=payload,
    )
    return SignupResponse(
        tenant_id=result.tenant_id,
        slug=result.slug,
        host=result.host,
        store_name=result.store_name,
    )
