from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.errors import AppError
from app.domains.identity.models import Actor, Permission, RequestContext, Role
from app.domains.identity.permissions import permissions_for, require_permission


def _context(role: Role) -> RequestContext:
    actor = Actor(
        user_id=uuid4(),
        tenant_id=uuid4(),
        role=role,
        email="user@example.com",
    )
    return RequestContext(
        tenant_id=actor.tenant_id,
        actor=actor,
        permissions=permissions_for(role),
        trace_id="trace-1",
        request_id="req-1",
    )


def test_owner_has_all_tenant_permissions() -> None:
    permissions = permissions_for(Role.OWNER)

    assert Permission.CONTENT_PUBLISH in permissions
    assert Permission.BILLING_WRITE in permissions
    assert Permission.TEAM_WRITE in permissions
    assert Permission.PAYMENTS_REFUND in permissions
    assert Permission.PLATFORM_TENANTS not in permissions


def test_manager_can_publish_but_not_billing_or_team_write() -> None:
    permissions = permissions_for(Role.MANAGER)

    assert Permission.CONTENT_PUBLISH in permissions
    assert Permission.CATALOG_WRITE in permissions
    assert Permission.BILLING_WRITE not in permissions
    assert Permission.TEAM_WRITE not in permissions
    assert Permission.PAYMENTS_REFUND not in permissions


def test_treasurer_handles_money_but_not_content() -> None:
    permissions = permissions_for(Role.TREASURER)

    assert Permission.PAYMENTS_REFUND in permissions
    assert Permission.BILLING_WRITE in permissions
    assert Permission.AUDIT_READ in permissions
    assert Permission.CONTENT_PUBLISH not in permissions


def test_packer_only_handles_orders() -> None:
    permissions = permissions_for(Role.PACKER)

    assert permissions == frozenset(
        {
            Permission.ORDERS_READ,
            Permission.ORDERS_FULFILL,
        }
    )


def test_support_is_read_only() -> None:
    permissions = permissions_for(Role.SUPPORT)

    assert Permission.ORDERS_READ in permissions
    assert Permission.CATALOG_READ in permissions
    assert Permission.ORDERS_FULFILL not in permissions
    assert Permission.CATALOG_WRITE not in permissions


def test_platform_admin_has_only_platform_permissions() -> None:
    permissions = permissions_for(Role.PLATFORM_ADMIN)

    assert Permission.PLATFORM_TENANTS in permissions
    assert Permission.PLATFORM_AUDIT in permissions
    assert Permission.CONTENT_PUBLISH not in permissions


def test_require_permission_allows_and_denies() -> None:
    require_permission(_context(Role.OWNER), Permission.CONTENT_PUBLISH)

    with pytest.raises(AppError) as exc_info:
        require_permission(_context(Role.PACKER), Permission.CONTENT_PUBLISH)

    assert exc_info.value.code == "FORBIDDEN"
    assert exc_info.value.status_code == 403
