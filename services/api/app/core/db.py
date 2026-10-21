from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]

from app.core.errors import AppError

_SET_TENANT_SQL = "SELECT set_config('app.tenant_id', $1, true)"
_SET_ROLE_SQL = "SET LOCAL ROLE app_rw"


class Database:
    """Pool asyncpg y transacciones con contexto de tenant."""

    def __init__(
        self,
        dsn: str,
        *,
        min_size: int = 1,
        max_size: int = 10,
    ) -> None:
        if not dsn:
            raise ValueError("database_url es obligatorio")
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database no está conectada")
        return self._pool

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=self._min_size,
                max_size=self._max_size,
            )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def ping(self) -> bool:
        try:
            await self.pool.fetchval("SELECT 1")
        except (asyncpg.PostgresError, OSError, RuntimeError):
            return False
        return True

    @asynccontextmanager
    async def tenant_transaction(self, tenant_id: UUID) -> AsyncIterator[asyncpg.Connection]:
        """Abre una transacción y fija `app.tenant_id` con SET LOCAL.

        `set_config(..., true)` es equivalente a `SET LOCAL`: el valor vive
        solo hasta el final de la transacción y no contamina la conexión.
        """
        if not isinstance(tenant_id, UUID):
            raise AppError("TENANT_NOT_FOUND", "Tenant requerido", 400)

        async with self.pool.acquire() as connection, connection.transaction():
            await connection.execute(_SET_ROLE_SQL)
            await connection.fetchval(_SET_TENANT_SQL, str(tenant_id))
            yield connection
