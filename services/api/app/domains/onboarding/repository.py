from __future__ import annotations

from typing import Protocol, cast
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]

from app.core.db import Database
from app.core.errors import AppError
from app.domains.onboarding.schemas import SignupRequest


class OnboardingRepository(Protocol):
    async def complete_client_signup(
        self,
        *,
        user_id: UUID,
        email: str,
        payload: SignupRequest,
        host: str,
    ) -> UUID: ...


class PostgresOnboardingRepository:
    """Acceso via funcion SECURITY DEFINER acotada (app.complete_client_signup)."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def complete_client_signup(
        self,
        *,
        user_id: UUID,
        email: str,
        payload: SignupRequest,
        host: str,
    ) -> UUID:
        try:
            async with self._database.public_transaction(actor_id=user_id) as connection:
                tenant_id = await connection.fetchval(
                    """
                    select app.complete_client_signup(
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                    )
                    """,
                    user_id,
                    email,
                    payload.full_name.strip(),
                    payload.phone.strip(),
                    payload.doc_type,
                    payload.doc_number.strip(),
                    payload.store_name.strip(),
                    payload.store_type,
                    payload.plan_code,
                    payload.slug,
                    host,
                    payload.domain_choice,
                    payload.custom_domain.lower() if payload.custom_domain else None,
                    payload.wants_subdomain and payload.domain_choice == "subdomain",
                )
        except asyncpg.UniqueViolationError as exc:
            constraint = getattr(exc, "constraint_name", "") or ""
            if "clients_user_id" in constraint:
                raise AppError(
                    "SIGNUP_ALREADY_COMPLETED",
                    "Este usuario ya completo su registro",
                    409,
                ) from exc
            if "domains_host" in constraint:
                raise AppError(
                    "DOMAIN_TAKEN",
                    "El dominio ya está registrado por otra tienda",
                    409,
                ) from exc
            raise AppError(
                "SLUG_TAKEN",
                "El slug o el host ya existen",
                409,
            ) from exc
        except asyncpg.PostgresError as exc:
            sqlstate = getattr(exc, "sqlstate", "") or ""
            message = str(getattr(exc, "message", "") or "")
            if sqlstate == "P0001" and "PLAN_NOT_FOUND" in message:
                raise AppError(
                    "PLAN_NOT_FOUND",
                    "El plan no existe o está inactivo",
                    400,
                ) from exc
            raise

        return cast(UUID, tenant_id)
