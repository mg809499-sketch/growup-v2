from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.core.db import Database
from app.domains.identity.models import Membership, Role


class MembershipRepository(Protocol):
    async def find_active(self, tenant_id: UUID, user_id: UUID) -> Membership | None: ...

    async def is_platform_admin(self, user_id: UUID) -> bool: ...


class PostgresMembershipRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def find_active(self, tenant_id: UUID, user_id: UUID) -> Membership | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select id, tenant_id, user_id, email, role, status
                from app.memberships
                where tenant_id = $1
                  and user_id = $2
                  and status = 'active'
                """,
                tenant_id,
                user_id,
            )

        if row is None:
            return None

        return Membership(
            id=row["id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            email=row["email"],
            role=Role(row["role"]),
            status=row["status"],
        )

    async def is_platform_admin(self, user_id: UUID) -> bool:
        async with self._database.public_transaction() as connection:
            return bool(
                await connection.fetchval(
                    "select app.is_platform_admin($1)",
                    user_id,
                )
            )
