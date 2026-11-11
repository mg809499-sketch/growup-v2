from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.core.errors import AppError
from app.domains.onboarding.repository import PostgresOnboardingRepository
from app.domains.onboarding.schemas import SignupRequest

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


def _payload(slug: str, **overrides: object) -> SignupRequest:
    data: dict[str, object] = {
        "full_name": "Comerciante Prueba",
        "phone": "+57 300 123 4567",
        "doc_type": "CC",
        "doc_number": "1234567890",
        "store_name": "Tienda Prueba",
        "store_type": "ropa",
        "plan_code": "starter",
        "slug": slug,
        "domain_choice": "subdomain",
        "custom_domain": None,
        "wants_subdomain": True,
    }
    data.update(overrides)
    return SignupRequest(**data)  # type: ignore[arg-type]


async def _cleanup(database: Database, tenant_id: UUID, user_id: UUID) -> None:
    async with database.pool.acquire() as connection:
        await connection.execute("delete from app.clients where user_id = $1", user_id)
        await connection.execute("delete from app.tenants where id = $1", tenant_id)


async def test_complete_client_signup_happy_path() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=2)
    await database.connect()
    suffix = uuid4().hex[:8]
    slug = f"it-signup-{suffix}"
    user_id = uuid4()
    email = f"it-signup-{suffix}@example.com"
    repository = PostgresOnboardingRepository(database)
    tenant_id: UUID | None = None

    try:
        tenant_id = await repository.complete_client_signup(
            user_id=user_id,
            email=email,
            payload=_payload(slug),
            host=f"{slug}.growup.com",
        )
        assert isinstance(tenant_id, UUID)

        async with database.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                select role, wants_subdomain, domain_choice, plan_code
                from app.clients where user_id = $1
                """,
                user_id,
            )
            assert row is not None
            assert row["role"] == "owner"
            assert row["wants_subdomain"] is True
            assert row["domain_choice"] == "subdomain"
            assert row["plan_code"] == "starter"

            membership = await connection.fetchrow(
                """
                select role, status from app.memberships
                where tenant_id = $1 and user_id = $2
                """,
                tenant_id,
                user_id,
            )
            assert membership is not None
            assert membership["role"] == "owner"
            assert membership["status"] == "active"

            tenant = await connection.fetchrow(
                "select status, plan_id from app.tenants where id = $1",
                tenant_id,
            )
            assert tenant is not None
            assert tenant["status"] == "trialing"

            domain = await connection.fetchrow(
                """
                select host, is_primary, type from app.domains
                where tenant_id = $1 and is_primary
                """,
                tenant_id,
            )
            assert domain is not None
            assert domain["host"] == f"{slug}.growup.com"
            assert domain["type"] == "subdomain"
    finally:
        if tenant_id is not None:
            await _cleanup(database, tenant_id, user_id)
        await database.close()


async def test_complete_client_signup_custom_domain() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=2)
    await database.connect()
    suffix = uuid4().hex[:8]
    slug = f"it-signupc-{suffix}"
    custom_domain = f"www.it-signup-{suffix}.co"
    user_id = uuid4()
    email = f"it-signupc-{suffix}@example.com"
    repository = PostgresOnboardingRepository(database)
    tenant_id: UUID | None = None

    try:
        tenant_id = await repository.complete_client_signup(
            user_id=user_id,
            email=email,
            payload=_payload(
                slug,
                plan_code="pro",
                store_type="joyeria",
                doc_type="NIT",
                doc_number="900123456",
                domain_choice="custom",
                custom_domain=custom_domain,
                wants_subdomain=False,
            ),
            host=f"{slug}.growup.com",
        )

        async with database.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                select host, type, is_primary, verified_at from app.domains
                where tenant_id = $1 and type = 'custom'
                """,
                tenant_id,
            )
            assert row is not None
            assert row["host"] == custom_domain
            assert row["is_primary"] is False
            assert row["verified_at"] is None
    finally:
        if tenant_id is not None:
            await _cleanup(database, tenant_id, user_id)
        await database.close()


async def test_complete_client_signup_idempotency() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=2)
    await database.connect()
    suffix = uuid4().hex[:8]
    slug = f"it-signupi-{suffix}"
    user_id = uuid4()
    email = f"it-signupi-{suffix}@example.com"
    repository = PostgresOnboardingRepository(database)
    tenant_id: UUID | None = None

    try:
        tenant_id = await repository.complete_client_signup(
            user_id=user_id,
            email=email,
            payload=_payload(slug),
            host=f"{slug}.growup.com",
        )

        with pytest.raises(AppError) as exc_info:
            await repository.complete_client_signup(
                user_id=user_id,
                email=email,
                payload=_payload(f"{slug}-2", store_name="Tienda Otra"),
                host=f"{slug}-2.growup.com",
            )
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "SIGNUP_ALREADY_COMPLETED"

        async with database.pool.acquire() as connection:
            count = await connection.fetchval(
                "select count(*)::int from app.tenants where slug like $1",
                f"{slug}%",
            )
            assert count == 1
    finally:
        if tenant_id is not None:
            await _cleanup(database, tenant_id, user_id)
        await database.close()


async def test_complete_client_signup_slug_taken() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=2)
    await database.connect()
    suffix = uuid4().hex[:8]
    slug = f"it-signupt-{suffix}"
    first_user = uuid4()
    second_user = uuid4()
    repository = PostgresOnboardingRepository(database)
    tenant_id: UUID | None = None

    try:
        tenant_id = await repository.complete_client_signup(
            user_id=first_user,
            email=f"first-{suffix}@example.com",
            payload=_payload(slug),
            host=f"{slug}.growup.com",
        )

        with pytest.raises(AppError) as exc_info:
            await repository.complete_client_signup(
                user_id=second_user,
                email=f"second-{suffix}@example.com",
                payload=_payload(slug, store_name="Tienda Rival"),
                host=f"{slug}.growup.com",
            )
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "SLUG_TAKEN"
    finally:
        if tenant_id is not None:
            await _cleanup(database, tenant_id, first_user)
        await database.close()


async def test_complete_client_signup_plan_not_found() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=2)
    await database.connect()
    suffix = uuid4().hex[:8]
    slug = f"it-signupp-{suffix}"
    user_id = uuid4()
    repository = PostgresOnboardingRepository(database)

    try:
        with pytest.raises(AppError) as exc_info:
            await repository.complete_client_signup(
                user_id=user_id,
                email=f"plan-{suffix}@example.com",
                payload=_payload(slug, plan_code="plan-que-no-existe"),
                host=f"{slug}.growup.com",
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "PLAN_NOT_FOUND"
    finally:
        await database.close()
