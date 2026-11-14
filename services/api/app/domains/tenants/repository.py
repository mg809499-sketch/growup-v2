from __future__ import annotations

import json
from typing import Any, Protocol, cast
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]

from app.core.db import Database
from app.core.errors import AppError
from app.core.safe_json import safe_json_list, safe_json_object
from app.domains.tenants.models import (
    PlatformTenant,
    Tenant,
    TenantSettings,
    TenantStatus,
)
from app.domains.tenants.zones import parse_shipping_zones


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

    async def overview(self, actor_id: UUID) -> dict[str, Any]: ...

    async def list_plans(self) -> list[dict[str, Any]]: ...

    async def update_plan(
        self,
        actor_id: UUID,
        plan_id: UUID,
        *,
        name: str | None,
        price_cents: int | None,
        currency: str | None,
        billing_interval: str | None,
        trial_days: int | None,
        features: list[str] | None,
        active: bool | None,
        badge: str | None,
        description: str | None,
        sort_order: int | None,
        list_price_cop_cents: int | None,
        list_price_usd_cents: int | None,
    ) -> dict[str, Any]: ...

    async def pause_tenant(
        self, actor_id: UUID, tenant_id: UUID, status: str
    ) -> dict[str, Any]: ...

    async def list_tenants_with_plan(self) -> list[dict[str, Any]]: ...

    async def tenant_overview(self, actor_id: UUID, tenant_id: UUID) -> dict[str, Any] | None: ...

    async def alerts(self, actor_id: UUID) -> list[dict[str, Any]]: ...

    async def dismiss_alert(
        self, actor_id: UUID, tenant_id: UUID, alert_key: str
    ) -> None: ...

    async def list_tenants(
        self,
        *,
        actor_id: UUID,
        status: str | None,
        query: str | None,
        limit: int,
        offset: int,
    ) -> tuple[tuple[PlatformTenant, ...], int]: ...

    async def get_theme(self, tenant_id: UUID) -> dict[str, Any] | None: ...


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
            shipping_zones=parse_shipping_zones(
                _as_list(row["shipping_zones"]), context="tenant_settings.shipping_zones"
            ),
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

    async def list_tenants(
        self,
        *,
        actor_id: UUID,
        status: str | None,
        query: str | None,
        limit: int,
        offset: int,
    ) -> tuple[tuple[PlatformTenant, ...], int]:
        try:
            async with self._database.public_transaction(actor_id=actor_id) as connection:
                rows = await connection.fetch(
                    "select * from app.list_tenants($1, $2, $3, $4, $5)",
                    actor_id,
                    status,
                    query,
                    limit,
                    offset,
                )
        except asyncpg.InsufficientPrivilegeError as exc:
            raise AppError(
                "PLATFORM_ADMIN_REQUIRED",
                "Se requiere un platform admin",
                403,
            ) from exc

        total = int(rows[0]["total_count"]) if rows else 0
        return tuple(_platform_tenant(row) for row in rows), total

    async def list_plans(self) -> list[dict[str, Any]]:
        async with self._database.public_transaction() as connection:
            rows = await connection.fetch(
                """
                select id, code, name, price_cents, currency, billing_interval,
                       trial_days, features, active, badge, description,
                       sort_order, list_price_cop_cents, list_price_usd_cents,
                       created_at, updated_at
                from app.plans
                order by sort_order, name
                """
            )
        return [dict(row) for row in rows]

    async def update_plan(
        self,
        actor_id: UUID,
        plan_id: UUID,
        *,
        name: str | None,
        price_cents: int | None,
        currency: str | None,
        billing_interval: str | None,
        trial_days: int | None,
        features: list[str] | None,
        active: bool | None,
        badge: str | None,
        description: str | None,
        sort_order: int | None,
        list_price_cop_cents: int | None,
        list_price_usd_cents: int | None,
    ) -> dict[str, Any]:
        async with self._database.public_transaction(actor_id=actor_id) as connection:
            row = await connection.fetchrow(
                """
                select app.update_plan_admin(
                    $1, $2, $3, $4, $5, $6, $7, $8::jsonb,
                    $9, $10, $11, $12, $13, $14
                ) as data
                """,
                actor_id,
                plan_id,
                name,
                price_cents,
                currency,
                billing_interval,
                trial_days,
                json.dumps(features) if features is not None else None,
                active,
                badge,
                description,
                sort_order,
                list_price_cop_cents,
                list_price_usd_cents,
            )
        if row is None or row["data"] is None:
            raise AppError("PLAN_UPDATE_FAILED", "No se pudo actualizar el plan", 500)
        return safe_json_object(row["data"], context="platform.update_plan")

    async def pause_tenant(self, actor_id: UUID, tenant_id: UUID, status: str) -> dict[str, Any]:
        async with self._database.public_transaction(actor_id=actor_id) as connection:
            row = await connection.fetchrow(
                "select app.pause_tenant_admin($1, $2, $3) as data",
                actor_id,
                tenant_id,
                status,
            )
        if row is None or row["data"] is None:
            raise AppError("TENANT_NOT_FOUND", "Tenant no encontrado", 404)
        return safe_json_object(row["data"], context="platform.pause_tenant")

    async def list_tenants_with_plan(self) -> list[dict[str, Any]]:
        async with self._database.public_transaction() as connection:
            rows = await connection.fetch(
                """
                select t.id, t.slug, t.name, t.status, t.trial_ends_at, t.plan_id,
                       d.host, p.code as plan_code, p.name as plan_name
                from app.tenants t
                left join app.domains d on d.tenant_id = t.id and d.is_primary
                left join app.plans p on p.id = t.plan_id
                order by t.created_at desc
                """
            )
        return [dict(row) for row in rows]

    async def overview(self, actor_id: UUID) -> dict[str, Any]:
        async with self._database.public_transaction(actor_id=actor_id) as connection:
            row = await connection.fetchrow(
                "select app.platform_overview($1) as data", actor_id
            )
        if row is None:
            return {}
        return safe_json_object(row["data"], context="platform.overview")

    async def tenant_overview(
        self, actor_id: UUID, tenant_id: UUID
    ) -> dict[str, Any] | None:
        async with self._database.public_transaction(actor_id=actor_id) as connection:
            row = await connection.fetchrow(
                "select app.tenant_overview($1, $2) as data", actor_id, tenant_id
            )
        if row is None or row["data"] is None:
            return None
        data = safe_json_object(row["data"], context="platform.tenant_overview")
        return data or None

    async def alerts(self, actor_id: UUID) -> list[dict[str, Any]]:
        async with self._database.public_transaction(actor_id=actor_id) as connection:
            row = await connection.fetchrow(
                "select app.platform_alerts($1) as data", actor_id
            )
        if row is None:
            return []
        return safe_json_list(row["data"], context="platform.alerts")

    async def dismiss_alert(
        self, actor_id: UUID, tenant_id: UUID, alert_key: str
    ) -> None:
        async with self._database.public_transaction(actor_id=actor_id) as connection:
            await connection.execute(
                "select app.dismiss_platform_alert($1, $2, $3)",
                actor_id,
                tenant_id,
                alert_key,
            )

    async def get_theme(self, tenant_id: UUID) -> dict[str, Any] | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                "select tokens from app.themes where tenant_id = $1",
                tenant_id,
            )
        if row is None:
            return None
        return _as_dict(row["tokens"]) or None


def _platform_tenant(row: Any) -> PlatformTenant:
    return PlatformTenant(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        status=TenantStatus(row["status"]),
        host=row["host"],
        plan_id=row["plan_id"],
        trial_ends_at=row["trial_ends_at"],
        created_at=row["created_at"],
    )


def _as_dict(value: object) -> dict[str, Any]:
    return safe_json_object(value, context="tenant_settings")


def _as_list(value: object) -> list[Any]:
    return safe_json_list(value, context="tenant_settings")
