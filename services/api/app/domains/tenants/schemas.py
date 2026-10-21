from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.domains.tenants.models import TenantBootstrap, TenantStatus


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
