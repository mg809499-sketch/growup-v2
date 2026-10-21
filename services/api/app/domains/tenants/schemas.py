from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domains.tenants.models import TenantBootstrap, TenantStatus

_SLUG_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class TenantPublic(BaseModel):
    slug: str
    name: str
    status: TenantStatus


class StorefrontSettings(BaseModel):
    currency: str
    locale: str
    navigation: dict[str, Any]
    seo_defaults: dict[str, Any]
    shipping_zones: list[Any]
    contact: dict[str, Any]
    social: dict[str, Any]


class BootstrapResponse(BaseModel):
    tenant: TenantPublic
    settings: StorefrontSettings

    @classmethod
    def from_domain(cls, bootstrap: TenantBootstrap) -> BootstrapResponse:
        return cls(
            tenant=TenantPublic(
                slug=bootstrap.tenant.slug,
                name=bootstrap.tenant.name,
                status=bootstrap.tenant.status,
            ),
            settings=StorefrontSettings(
                currency=bootstrap.settings.currency,
                locale=bootstrap.settings.locale,
                navigation=bootstrap.settings.navigation,
                seo_defaults=bootstrap.settings.seo_defaults,
                shipping_zones=bootstrap.settings.shipping_zones,
                contact=bootstrap.settings.contact,
                social=bootstrap.settings.social,
            ),
        )


class TenantCreateRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=63, pattern=_SLUG_PATTERN)
    name: str = Field(min_length=1, max_length=200)
    legal_name: str | None = Field(default=None, max_length=200)
    plan_id: UUID | None = None
    owner_user_id: UUID
    owner_email: str = Field(min_length=3, max_length=320, pattern=_EMAIL_PATTERN)


class TenantCreatedResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    status: TenantStatus
    host: str
    owner_user_id: UUID
