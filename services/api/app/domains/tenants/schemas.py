from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.tenants.models import (
    PlatformTenant,
    PlatformTenantPage,
    TenantBootstrap,
    TenantStatus,
)

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
    theme: dict[str, Any] | None = None

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
            theme=bootstrap.theme,
        )


class TenantCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=63, pattern=_SLUG_PATTERN)
    name: str = Field(min_length=1, max_length=200)
    legal_name: str | None = Field(default=None, max_length=200)
    plan_id: UUID | None = None
    owner_user_id: UUID
    owner_email: str = Field(min_length=3, max_length=320, pattern=_EMAIL_PATTERN)


class TenantPlanRef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    code: str
    name: str


class TenantBrief(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    slug: str
    name: str
    status: TenantStatus
    created_at: datetime | None = None
    trial_ends_at: datetime | None = None
    host: str | None = None
    plan: TenantPlanRef | None = None


class SubscriptionRef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    provider: str
    status: str
    current_period_end: datetime | None = None
    created_at: datetime | None = None


class PlatformOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    tenants_total: int
    tenants_active: int
    tenants_trialing: int
    tenants_suspended: int
    tenants_canceled: int
    trials_ending_7d: int
    gmv_last_7d_cents: int
    gmv_last_30d_cents: int
    orders_last_30d: int
    products_total: int
    media_bytes_total: int
    media_failed: int
    outbox_stuck: int
    audit_decisions_last_7d: int
    audit_denied_last_7d: int
    subscriptions_active: int
    computed_at: datetime


class PlatformTenantOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    tenant: TenantBrief
    subscription: SubscriptionRef | None = None
    gmv_last_7d_cents: int
    gmv_last_30d_cents: int
    orders_last_30d: int
    products_total: int
    media_bytes_total: int
    media_failed: int
    outbox_stuck: int
    audit_decisions_last_7d: int
    audit_denied_last_7d: int
    audit_chain_valid: bool
    computed_at: datetime


class PlatformAlert(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    alert_key: str = Field(min_length=1, max_length=200)
    tenant_id: UUID
    slug: str = Field(min_length=1, max_length=63)
    name: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=300)
    severity: str = Field(pattern="^(critical|warning|info)$")


class PlatformAlertListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alerts: list[PlatformAlert]
    count: int


class PlatformAlertDismissRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    alert_key: str = Field(min_length=1, max_length=200)


class TenantCreatedResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    status: TenantStatus
    host: str
    owner_user_id: UUID


class PlatformTenantResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    status: TenantStatus
    host: str | None
    plan_id: UUID | None
    trial_ends_at: datetime | None
    created_at: datetime

    @classmethod
    def from_domain(cls, tenant: PlatformTenant) -> PlatformTenantResponse:
        return cls(
            id=tenant.id,
            slug=tenant.slug,
            name=tenant.name,
            status=tenant.status,
            host=tenant.host,
            plan_id=tenant.plan_id,
            trial_ends_at=tenant.trial_ends_at,
            created_at=tenant.created_at,
        )


class PlatformTenantListResponse(BaseModel):
    items: list[PlatformTenantResponse]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_domain(cls, page: PlatformTenantPage) -> PlatformTenantListResponse:
        return cls(
            items=[PlatformTenantResponse.from_domain(item) for item in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )
