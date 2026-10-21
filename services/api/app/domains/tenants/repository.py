from __future__ import annotations

import json
from typing import Any, Protocol, cast
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]

from app.core.db import Database
from app.core.errors import AppError
from app.domains.tenants.models import Tenant, TenantSettings, TenantStatus


class TenantRepository(Protocol):
    async def find_by_host(self, host: str) -> Tenant | None: ...

    async def get_settings(self, tenant_id: UUID) -> TenantSettings | None: ...

    async def create_tenant(
        self,
        *,
        slug: str,
        host: str,
        name: str,
        legal_name: str | None = None,
        plan_id: UUID | None = None,
    ) -> UUID: ...

    async def create_tenant_with_owner(
        self,
        *,
        slug: str,
        host: str,
        name: str,
        owner_user_id: UUID,
        owner_email: str,
        legal_name: str | None = None,
        plan_id: UUID | None = None,
    ) -> UUID: ...


class PostgresTenantRepository:
    """Acceso a tenants mediante funciones SECURITY DEFINER acotadas."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def find_by_host(self, host: str) -> Tenant | None:
        async with self._database.public_transaction() as connection:
            row = await connection.fetchrow(
                "select id, slug, name, status from app.resolve_tenant($1)",
                host,
            )

        if row is None:
            return None

        return Tenant(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            status=TenantStatus(row["status"]),
        )

    async def get_settings(self, tenant_id: UUID) -> TenantSettings | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select currency, locale, navigation, seo_defaults,
                       shipping_zones, contact, social
                from app.tenant_settings
                where tenant_id = $1
                """,
                tenant_id,
            )

        if row is None:
            return None

        return TenantSettings(
            currency=row["currency"],
            locale=row["locale"],
            navigation=_as_dict(row["navigation"]),
            seo_defaults=_as_dict(row["seo_defaults"]),
            shipping_zones=_as_list(row["shipping_zones"]),
            contact=_as_dict(row["contact"]),
            social=_as_dict(row["social"]),
        )

    async def create_tenant(
        self,
        *,
        slug: str,
        host: str,
        name: str,
        legal_name: str | None = None,
        plan_id: UUID | None = None,
    ) -> UUID:
        try:
            async with self._database.public_transaction() as connection:
                tenant_id = await connection.fetchval(
                    "select app.create_tenant($1, $2, $3, $4, $5)",
                    slug,
                    host,
                    name,
                    legal_name,
                    plan_id,
                )
        except asyncpg.UniqueViolationError as exc:
            raise AppError("SLUG_TAKEN", "El slug o el host ya existen", 409) from exc
        except asyncpg.ForeignKeyViolationError as exc:
            raise AppError("PLAN_NOT_FOUND", "El plan no existe", 400) from exc

        return cast(UUID, tenant_id)

    async def create_tenant_with_owner(
        self,
        *,
        slug: str,
        host: str,
        name: str,
        owner_user_id: UUID,
        owner_email: str,
        legal_name: str | None = None,
        plan_id: UUID | None = None,
    ) -> UUID:
        try:
            async with self._database.public_transaction() as connection:
                tenant_id = await connection.fetchval(
                    "select app.create_tenant_with_owner($1, $2, $3, $4, $5, $6, $7)",
                    slug,
                    host,
                    name,
                    legal_name,
                    plan_id,
                    owner_user_id,
                    owner_email,
                )
        except asyncpg.UniqueViolationError as exc:
            constraint = getattr(exc, "constraint_name", "") or ""
            if "memberships" in constraint:
                raise AppError(
                    "OWNER_MEMBERSHIP_CONFLICT",
                    "El owner ya tiene membresía en el tenant",
                    409,
                ) from exc
            raise AppError("SLUG_TAKEN", "El slug o el host ya existen", 409) from exc
        except asyncpg.ForeignKeyViolationError as exc:
            raise AppError("PLAN_NOT_FOUND", "El plan no existe", 400) from exc

        return cast(UUID, tenant_id)


def _as_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    return {}


def _as_list(value: object) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    return []
