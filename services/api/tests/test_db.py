from __future__ import annotations

from typing import Any
from uuid import uuid4

import asyncpg
import pytest

from app.core.db import Database
from app.core.errors import AppError


class FakeTransaction:
    def __init__(self, connection: FakeConnection) -> None:
        self._connection = connection

    async def __aenter__(self) -> None:
        self._connection.transaction_entered = True

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._connection.transaction_exited = True


class FakeConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []
        self.statements: list[str] = []
        self.transaction_entered = False
        self.transaction_exited = False
        self.fetchval_result: Any = None
        self.fetchval_error: Exception | None = None
        self.execute_error: Exception | None = None

    async def execute(self, query: str) -> str:
        self.statements.append(query)
        if self.execute_error is not None:
            raise self.execute_error
        return "OK"

    async def fetchval(self, query: str, *args: object) -> Any:
        self.executed.append((query, args))
        if self.fetchval_error is not None:
            raise self.fetchval_error
        return self.fetchval_result

    def transaction(self) -> FakeTransaction:
        return FakeTransaction(self)


class FakeAcquire:
    def __init__(self, connection: FakeConnection) -> None:
        self._connection = connection

    async def __aenter__(self) -> FakeConnection:
        return self._connection

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class FakePool:
    def __init__(self, connection: FakeConnection | None = None) -> None:
        self.connection = connection or FakeConnection()
        self.closed = False
        self.fetchval_result: Any = 1
        self.fetchval_error: Exception | None = None

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self.connection)

    async def fetchval(self, query: str, *args: object) -> Any:
        if self.fetchval_error is not None:
            raise self.fetchval_error
        return self.fetchval_result

    async def close(self) -> None:
        self.closed = True


def _database_with_pool(pool: FakePool) -> Database:
    database = Database("postgresql://test")
    database._pool = pool  # type: ignore[assignment]
    return database


def test_database_requires_dsn() -> None:
    with pytest.raises(ValueError):
        Database("")


def test_pool_requires_connection() -> None:
    database = Database("postgresql://test")

    with pytest.raises(RuntimeError):
        _ = database.pool


async def test_connect_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    pool = FakePool()
    calls = 0

    async def fake_create_pool(**kwargs: object) -> FakePool:
        nonlocal calls
        calls += 1
        assert kwargs["dsn"] == "postgresql://test"
        assert kwargs["min_size"] == 2
        assert kwargs["max_size"] == 5
        return pool

    monkeypatch.setattr("app.core.db.asyncpg.create_pool", fake_create_pool)
    database = Database("postgresql://test", min_size=2, max_size=5)

    await database.connect()
    await database.connect()

    assert database.pool is pool
    assert calls == 1


async def test_close_releases_pool() -> None:
    pool = FakePool()
    database = _database_with_pool(pool)

    await database.close()

    assert pool.closed is True
    with pytest.raises(RuntimeError):
        _ = database.pool


async def test_tenant_transaction_sets_local_tenant() -> None:
    pool = FakePool()
    database = _database_with_pool(pool)
    tenant_id = uuid4()

    async with database.tenant_transaction(tenant_id) as connection:
        assert connection is pool.connection

    assert pool.connection.statements == ["SET LOCAL ROLE app_rw"]
    assert pool.connection.executed == [
        ("SELECT set_config('app.tenant_id', $1, true)", (str(tenant_id),))
    ]
    assert pool.connection.transaction_entered is True
    assert pool.connection.transaction_exited is True


async def test_tenant_transaction_rejects_non_uuid() -> None:
    database = _database_with_pool(FakePool())

    with pytest.raises(AppError) as exc_info:
        async with database.tenant_transaction("not-a-uuid"):  # type: ignore[arg-type]
            pass

    assert exc_info.value.code == "TENANT_NOT_FOUND"


async def test_tenant_transaction_propagates_database_error() -> None:
    pool = FakePool()
    pool.connection.fetchval_error = asyncpg.PostgresError("boom")
    database = _database_with_pool(pool)

    with pytest.raises(asyncpg.PostgresError):
        async with database.tenant_transaction(uuid4()):
            pass


async def test_tenant_transaction_propagates_role_error() -> None:
    pool = FakePool()
    pool.connection.execute_error = asyncpg.PostgresError("role denied")
    database = _database_with_pool(pool)

    with pytest.raises(asyncpg.PostgresError):
        async with database.tenant_transaction(uuid4()):
            pass


async def test_ping_true_when_database_responds() -> None:
    database = _database_with_pool(FakePool())

    assert await database.ping() is True


async def test_ping_false_when_database_fails() -> None:
    pool = FakePool()
    pool.fetchval_error = OSError("down")
    database = _database_with_pool(pool)

    assert await database.ping() is False


async def test_ping_false_when_pool_is_not_connected() -> None:
    database = Database("postgresql://test")

    assert await database.ping() is False
