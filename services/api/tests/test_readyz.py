import pytest
from fastapi.testclient import TestClient

import app.main as main_module


class FakeDatabase:
    def __init__(self, ready: bool) -> None:
        self.ready = ready
        self.connected = False
        self.closed = False

    async def connect(self) -> None:
        self.connected = True

    async def close(self) -> None:
        self.closed = True

    async def ping(self) -> bool:
        return self.ready


def test_readyz_without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main_module, "database", None)
    with TestClient(main_module.app) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "not_configured"},
    }


def test_readyz_with_database_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeDatabase(ready=True)
    monkeypatch.setattr(main_module, "database", fake)
    with TestClient(main_module.app) as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok"}}
    assert fake.connected is True
    assert fake.closed is True


def test_readyz_with_database_down(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeDatabase(ready=False)
    monkeypatch.setattr(main_module, "database", fake)
    with TestClient(main_module.app) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"database": "down"}}
    assert fake.connected is True
    assert fake.closed is True
