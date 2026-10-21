from __future__ import annotations

from app.core.errors import AppError
from app.domains.identity.models import Permission, RequestContext, Role

_TENANT_ALL = frozenset(
    {
        Permission.CATALOG_READ,
        Permission.CATALOG_WRITE,
        Permission.CONTENT_READ,
        Permission.CONTENT_WRITE,
        Permission.CONTENT_PUBLISH,
        Permission.ORDERS_READ,
        Permission.ORDERS_FULFILL,
        Permission.PAYMENTS_READ,
        Permission.PAYMENTS_REFUND,
        Permission.BILLING_READ,
        Permission.BILLING_WRITE,
        Permission.TEAM_READ,
        Permission.TEAM_WRITE,
        Permission.SETTINGS_READ,
        Permission.SETTINGS_WRITE,
        Permission.CUSTOMERS_READ,
        Permission.AUDIT_READ,
    }
)

_MATRIX: dict[Role, frozenset[Permission]] = {
    Role.OWNER: _TENANT_ALL,
    Role.MANAGER: frozenset(
        {
            Permission.CATALOG_READ,
            Permission.CATALOG_WRITE,
            Permission.CONTENT_READ,
            Permission.CONTENT_WRITE,
            Permission.CONTENT_PUBLISH,
            Permission.ORDERS_READ,
            Permission.ORDERS_FULFILL,
            Permission.PAYMENTS_READ,
            Permission.TEAM_READ,
            Permission.SETTINGS_READ,
            Permission.SETTINGS_WRITE,
            Permission.CUSTOMERS_READ,
        }
    ),
    Role.TREASURER: frozenset(
        {
            Permission.ORDERS_READ,
            Permission.PAYMENTS_READ,
            Permission.PAYMENTS_REFUND,
            Permission.BILLING_READ,
            Permission.BILLING_WRITE,
            Permission.CUSTOMERS_READ,
            Permission.AUDIT_READ,
        }
    ),
    Role.PACKER: frozenset(
        {
            Permission.ORDERS_READ,
            Permission.ORDERS_FULFILL,
        }
    ),
    Role.SUPPORT: frozenset(
        {
            Permission.CATALOG_READ,
            Permission.CONTENT_READ,
            Permission.ORDERS_READ,
            Permission.CUSTOMERS_READ,
        }
    ),
    Role.PLATFORM_ADMIN: frozenset(
        {
            Permission.PLATFORM_TENANTS,
            Permission.PLATFORM_AUDIT,
            Permission.PLATFORM_SUPPORT,
        }
    ),
}


def permissions_for(role: Role) -> frozenset[Permission]:
    return _MATRIX.get(role, frozenset())


def require_permission(context: RequestContext, permission: Permission) -> None:
    if permission not in context.permissions:
        raise AppError("FORBIDDEN", "Permiso insuficiente", 403)
