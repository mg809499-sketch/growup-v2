from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.core.errors import AppError
from app.core.security.jwt import TokenClaims
from app.domains.identity.models import Membership, Role
from app.domains.identity.permissions import Permission
from app.domains.identity.service import AuthService, build_context


class FakeVerifier:
    def __init__(self, claims: TokenClaims) -> None:
        self.claims = claims
        self.tokens: list[str] = []

    async def verify(self, token: str) -> TokenClaims:
        self.tokens.append(token)
        return self.claims


class FakeMembershipRepository:
    def __init__(
        self,
        membership: Membership | None = None,
        *,
        platform_admin: bool = False,
    ) -> None:
        self.membership = membership
        self.platform_admin = platform_admin
        self.calls: list[tuple[UUID, UUID]] = []

    async def find_active(self, tenant_id: UUID, user_id: UUID) -> Membership | None:
        self.calls.append((tenant_id, user_id))
        return self.membership

    async def is_platform_admin(self, user_id: UUID) -> bool:
        return self.platform_admin


def _claims(
    *,
    tenant_id: UUID | None,
    role: str,
    subject: UUID,
    email: str = "user@example.com",
) -> TokenClaims:
    return TokenClaims(
        subject=str(subject),
        tenant_id=tenant_id,
        role=role,
        email=email,
        audience="authenticated",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        raw={},
    )


async def test_authenticate_uses_role_from_membership() -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    membership = Membership(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        email="manager@example.com",
        role=Role.MANAGER,
        status="active",
    )
    service = AuthService(
        FakeVerifier(_claims(tenant_id=tenant_id, role="owner", subject=user_id)),
        FakeMembershipRepository(membership),
    )

    actor = await service.authenticate("token")

    assert actor.user_id == user_id
    assert actor.tenant_id == tenant_id
    assert actor.role == Role.MANAGER
    assert actor.email == "manager@example.com"


async def test_authenticate_rejects_tenant_mismatch() -> None:
    user_id = uuid4()
    tenant_a = uuid4()
    tenant_b = uuid4()
    service = AuthService(
        FakeVerifier(_claims(tenant_id=tenant_a, role="owner", subject=user_id)),
        FakeMembershipRepository(),
    )

    with pytest.raises(AppError) as exc_info:
        await service.authenticate("token", expected_tenant_id=tenant_b)

    assert exc_info.value.code == "TENANT_MISMATCH"
    assert exc_info.value.status_code == 403


async def test_authenticate_rejects_missing_or_inactive_membership() -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    service = AuthService(
        FakeVerifier(_claims(tenant_id=tenant_id, role="owner", subject=user_id)),
        FakeMembershipRepository(None),
    )

    with pytest.raises(AppError) as exc_info:
        await service.authenticate("token")

    assert exc_info.value.code == "FORBIDDEN"
    assert exc_info.value.status_code == 403


async def test_platform_admin_requires_database_membership() -> None:
    user_id = uuid4()
    service = AuthService(
        FakeVerifier(_claims(tenant_id=None, role="platform_admin", subject=user_id)),
        FakeMembershipRepository(platform_admin=True),
    )

    actor = await service.authenticate("token")

    assert actor.tenant_id is None
    assert actor.role == Role.PLATFORM_ADMIN


async def test_platform_admin_without_database_row_is_forbidden() -> None:
    user_id = uuid4()
    service = AuthService(
        FakeVerifier(_claims(tenant_id=None, role="platform_admin", subject=user_id)),
        FakeMembershipRepository(platform_admin=False),
    )

    with pytest.raises(AppError) as exc_info:
        await service.authenticate("token")

    assert exc_info.value.code == "FORBIDDEN"


async def test_token_without_tenant_and_not_platform_is_invalid() -> None:
    user_id = uuid4()
    service = AuthService(
        FakeVerifier(_claims(tenant_id=None, role="owner", subject=user_id)),
        FakeMembershipRepository(),
    )

    with pytest.raises(AppError) as exc_info:
        await service.authenticate("token")

    assert exc_info.value.code == "TOKEN_INVALID"
    assert exc_info.value.status_code == 401


async def test_invalid_subject_is_rejected() -> None:
    invalid_claims = TokenClaims(
        subject="not-a-uuid",
        tenant_id=uuid4(),
        role="owner",
        email=None,
        audience="authenticated",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        raw={},
    )
    service = AuthService(
        FakeVerifier(invalid_claims),
        FakeMembershipRepository(),
    )

    with pytest.raises(AppError) as exc_info:
        await service.authenticate("token")

    assert exc_info.value.code == "TOKEN_INVALID"


async def test_build_context_contains_permissions() -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    service = AuthService(
        FakeVerifier(_claims(tenant_id=tenant_id, role="owner", subject=user_id)),
        FakeMembershipRepository(
            Membership(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                email="manager@example.com",
                role=Role.MANAGER,
                status="active",
            )
        ),
    )
    actor = await service.authenticate("token")

    context = build_context(actor, request_id="req-1", trace_id="trace-1")

    assert context.tenant_id == tenant_id
    assert Permission.CONTENT_PUBLISH in context.permissions
    assert context.request_id == "req-1"
    assert context.trace_id == "trace-1"
