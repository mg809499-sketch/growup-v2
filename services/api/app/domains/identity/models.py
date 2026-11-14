from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    TREASURER = "treasurer"
    PACKER = "packer"
    SUPPORT = "support"
    PLATFORM_ADMIN = "platform_admin"


class Permission(StrEnum):
    CATALOG_READ = "catalog:read"
    CATALOG_WRITE = "catalog:write"
    CONTENT_READ = "content:read"
    CONTENT_WRITE = "content:write"
    CONTENT_PUBLISH = "content:publish"
    ORDERS_READ = "orders:read"
    ORDERS_FULFILL = "orders:fulfill"
    PAYMENTS_READ = "payments:read"
    PAYMENTS_REFUND = "payments:refund"
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"
    TEAM_READ = "team:read"
    TEAM_WRITE = "team:write"
    SETTINGS_READ = "settings:read"
    SETTINGS_WRITE = "settings:write"
    CUSTOMERS_READ = "customers:read"
    AUDIT_READ = "audit:read"
    WEBHOOKS_MANAGE = "webhooks:manage"
    PLATFORM_TENANTS = "platform:tenants"
    PLATFORM_AUDIT = "platform:audit"
    PLATFORM_SUPPORT = "platform:support"


@dataclass(frozen=True, slots=True)
class Membership:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    email: str
    role: Role
    status: str


@dataclass(frozen=True, slots=True)
class Actor:
    user_id: UUID
    tenant_id: UUID | None
    role: Role
    email: str | None


@dataclass(frozen=True, slots=True)
class RequestContext:
    tenant_id: UUID | None
    actor: Actor
    permissions: frozenset[Permission]
    trace_id: str
    request_id: str
