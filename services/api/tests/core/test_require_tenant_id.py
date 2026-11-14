from __future__ import annotations

from uuid import uuid4

import pytest

from app.api.deps import require_tenant_id
from app.core.errors import AppError
from app.domains.identity.models import Actor, RequestContext, Role

_TENANT = uuid4()
_USER = uuid4()


def _context(tenant_id) -> RequestContext:  # type: ignore[no-untyped-def]
    return RequestContext(
        tenant_id=tenant_id,
        actor=Actor(user_id=_USER, tenant_id=tenant_id, role=Role.OWNER, email="a@b.c"),
        permissions=frozenset(),
        trace_id="t",
        request_id="r",
    )


def test_require_tenant_id_returns_tenant() -> None:
    assert require_tenant_id(_context(_TENANT)) == _TENANT


def test_require_tenant_id_fails_closed_without_tenant() -> None:
    with pytest.raises(AppError) as excinfo:
        require_tenant_id(_context(None))
    assert excinfo.value.code == "FORBIDDEN"
    assert excinfo.value.status_code == 403
