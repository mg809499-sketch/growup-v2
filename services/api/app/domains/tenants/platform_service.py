from __future__ import annotations

from typing import Any
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]

from app.core.config import settings
from app.core.errors import AppError
from app.core.safe_json import report_anomaly
from app.core.tenancy import validate_slug
from app.domains.governance.models import PolicyInput
from app.domains.governance.service import GovernanceService
from app.domains.tenants.models import PlatformTenantPage, Tenant, TenantStatus
from app.domains.tenants.repository import TenantRepository
from app.domains.tenants.schemas import (
    PlanOut,
    PlanUpdateRequest,
    PlatformAlert,
    PlatformAlertListResponse,
    PlatformOverviewResponse,
    PlatformTenantOverviewResponse,
)

_VALID_STATUSES = {status.value for status in TenantStatus}


class PlatformTenantService:
    """Onboarding de tenants: decide con gobernanza y crea de forma atómica."""

    def __init__(
        self,
        tenants: TenantRepository,
        governance: GovernanceService,
    ) -> None:
        self._tenants = tenants
        self._governance = governance

    async def create_tenant(
        self,
        *,
        actor_id: str,
        actor_type: str,
        slug: str,
        name: str,
        owner_user_id: UUID,
        owner_email: str,
        legal_name: str | None = None,
        plan_id: UUID | None = None,
        trace_id: str | None = None,
    ) -> Tenant:
        validate_slug(slug)
        host = f"{slug}.{settings.root_domain}"

        policy_input = PolicyInput(
            tenant_id=None,
            actor_id=actor_id,
            actor_type=actor_type,
            action="platform.create_tenant",
            resource_type="tenant",
            resource_id=None,
            context={
                "slug": slug,
                "host": host,
                "plan_id": str(plan_id) if plan_id is not None else None,
                "owner_user_id": str(owner_user_id),
            },
            trace_id=trace_id,
        )

        # Evalúa y audita. Si la política deniega o la auditoría falla, no crea nada.
        await self._governance.evaluate_and_record(
            "platform.create_tenant",
            policy_input,
        )

        tenant_id = await self._tenants.create_tenant_with_owner(
            slug=slug,
            host=host,
            name=name,
            owner_user_id=owner_user_id,
            owner_email=owner_email,
            legal_name=legal_name,
            plan_id=plan_id,
        )

        return Tenant(
            id=tenant_id,
            slug=slug,
            name=name,
            status=TenantStatus.TRIALING,
        )

    async def list_tenants(
        self,
        *,
        actor_id: UUID,
        status: str | None,
        query: str | None,
        limit: int,
        offset: int,
    ) -> PlatformTenantPage:
        if status is not None and status not in _VALID_STATUSES:
            raise AppError("INVALID_STATUS", "Estado de tenant inválido", 422)
        if limit < 1 or limit > 100:
            raise AppError("INVALID_LIMIT", "El límite debe estar entre 1 y 100", 422)
        if offset < 0:
            raise AppError("INVALID_OFFSET", "El offset no puede ser negativo", 422)

        normalized_query = query.strip() if query else None
        if normalized_query is not None and len(normalized_query) > 100:
            raise AppError("QUERY_TOO_LONG", "La búsqueda es demasiado larga", 422)

        items, total = await self._tenants.list_tenants(
            actor_id=actor_id,
            status=status,
            query=normalized_query,
            limit=limit,
            offset=offset,
        )
        return PlatformTenantPage(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_overview(self, actor_id: UUID) -> PlatformOverviewResponse:
        raw = await self._tenants.overview(actor_id)
        if not raw:
            raise AppError(
                "PLATFORM_OVERVIEW_UNAVAILABLE",
                "No se pudo calcular el resumen ejecutivo",
                503,
            )
        return PlatformOverviewResponse.model_validate(raw)

    async def get_tenant_overview(
        self, actor_id: UUID, tenant_id: UUID
    ) -> PlatformTenantOverviewResponse:
        raw = await self._tenants.tenant_overview(actor_id, tenant_id)
        if raw is None:
            raise AppError("TENANT_NOT_FOUND", "Tenant no encontrado", 404)
        return PlatformTenantOverviewResponse.model_validate(raw)

    async def list_alerts(self, actor_id: UUID) -> PlatformAlertListResponse:
        raw = await self._tenants.alerts(actor_id)
        alerts: list[PlatformAlert] = []
        for item in raw:
            if not isinstance(item, dict):
                report_anomaly(
                    "platform.alerts",
                    f"alerta no-objeto ignorada: {type(item).__name__}",
                )
                continue
            try:
                alerts.append(PlatformAlert.model_validate(item))
            except Exception as exc:  # noqa: BLE001 - un item malformado no debe tumbar el feed
                report_anomaly("platform.alerts", f"alerta inválida ignorada: {item!r} ({exc})")
        return PlatformAlertListResponse(alerts=alerts, count=len(alerts))

    async def dismiss_alert(
        self, actor_id: UUID, tenant_id: UUID, alert_key: str
    ) -> None:
        if not alert_key.strip():
            raise AppError("ALERT_KEY_REQUIRED", "alert_key requerido", 422)
        try:
            await self._tenants.dismiss_alert(actor_id, tenant_id, alert_key)
        except asyncpg.ForeignKeyViolationError as exc:
            raise AppError("TENANT_NOT_FOUND", "Tenant no encontrado", 404) from exc

    async def list_plans(self, actor_id: UUID) -> list[PlanOut]:
        raw = await self._tenants.list_plans()
        plans: list[PlanOut] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            features = item.get("features")
            if isinstance(features, list):
                item = {**item, "features": [str(f) for f in features]}
            try:
                plans.append(PlanOut.model_validate(item))
            except Exception:
                continue
        return plans

    async def update_plan(
        self, actor_id: UUID, plan_id: UUID, payload: PlanUpdateRequest
    ) -> PlanOut:
        features_list = payload.features if payload.features is not None else None
        raw = await self._tenants.update_plan(
            actor_id,
            plan_id,
            name=payload.name,
            price_cents=payload.price_cents,
            currency=payload.currency,
            billing_interval=payload.billing_interval,
            trial_days=payload.trial_days,
            features=features_list,
            active=payload.active,
            badge=payload.badge,
            description=payload.description,
            sort_order=payload.sort_order,
            list_price_cop_cents=payload.list_price_cop_cents,
            list_price_usd_cents=payload.list_price_usd_cents,
        )
        features = raw.get("features")
        if isinstance(features, list):
            raw = {**raw, "features": [str(f) for f in features]}
        return PlanOut.model_validate(raw)

    async def pause_tenant(
        self, actor_id: UUID, tenant_id: UUID, status: str
    ) -> dict[str, Any]:
        if status not in {"active", "suspended"}:
            raise AppError("INVALID_STATUS", "Estado inválido", 422)
        raw = await self._tenants.pause_tenant(actor_id, tenant_id, status)
        return raw

    async def tenants_csv(self, actor_id: UUID) -> str:
        rows = await self._tenants.list_tenants_with_plan()
        out = [
            "id,slug,name,host,plan_code,plan_name,status,trial_ends_at,created_at",
        ]
        for row in rows:
            out.append(
                ",".join(
                    [
                        str(row.get("id", "")),
                        str(row.get("slug", "")),
                        str(row.get("name", "")).replace(",", " "),
                        str(row.get("host") or ""),
                        str(row.get("plan_code") or ""),
                        str(row.get("plan_name") or "").replace(",", " "),
                        str(row.get("status", "")),
                        str(row.get("trial_ends_at") or ""),
                        str(row.get("created_at") or ""),
                    ]
                )
            )
        return "\n".join(out) + "\n"
