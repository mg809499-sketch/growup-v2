from __future__ import annotations

from app.core import runtime
from app.core.errors import AppError
from app.domains.tenants.service import TenantResolver


def get_tenant_resolver() -> TenantResolver:
    if runtime.tenant_resolver is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "La base de datos no está configurada",
            503,
        )
    return runtime.tenant_resolver
