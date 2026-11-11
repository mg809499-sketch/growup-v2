from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.config import settings
from app.core.tenancy import validate_slug
from app.domains.onboarding.repository import OnboardingRepository
from app.domains.onboarding.schemas import SignupRequest


@dataclass(frozen=True)
class SignupResult:
    tenant_id: UUID
    slug: str
    host: str
    store_name: str


class OnboardingService:
    """Alta self-service: el comerciante crea su cuenta y su tenant en un paso."""

    def __init__(self, repository: OnboardingRepository) -> None:
        self._repository = repository

    async def complete_signup(
        self,
        *,
        user_id: UUID,
        email: str,
        payload: SignupRequest,
    ) -> SignupResult:
        validate_slug(payload.slug)
        host = f"{payload.slug}.{settings.root_domain}"
        tenant_id = await self._repository.complete_client_signup(
            user_id=user_id,
            email=email,
            payload=payload,
            host=host,
        )
        return SignupResult(
            tenant_id=tenant_id,
            slug=payload.slug,
            host=host,
            store_name=payload.store_name.strip(),
        )
