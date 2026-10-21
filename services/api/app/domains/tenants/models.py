from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID


class TenantStatus(StrEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    CANCELED = "canceled"


@dataclass(frozen=True, slots=True)
class Tenant:
    id: UUID
    slug: str
    name: str
    status: TenantStatus


@dataclass(frozen=True, slots=True)
class TenantSettings:
    currency: str
    locale: str
    navigation: dict[str, Any] = field(default_factory=dict)
    seo_defaults: dict[str, Any] = field(default_factory=dict)
    shipping_zones: list[Any] = field(default_factory=list)
    contact: dict[str, Any] = field(default_factory=dict)
    social: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def defaults(cls) -> TenantSettings:
        return cls(currency="COP", locale="es-CO")


@dataclass(frozen=True, slots=True)
class TenantBootstrap:
    tenant: Tenant
    settings: TenantSettings
