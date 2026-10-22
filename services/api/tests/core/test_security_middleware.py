from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.middleware import SecurityMiddleware
from app.main import app as main_app


def _app(max_request_bytes: int = 1024) -> FastAPI:
    test_app = FastAPI()
    test_app.add_middleware(SecurityMiddleware, max_request_bytes=max_request_bytes)

    @test_app.get("/v1/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    @test_app.get("/healthz")
    async def healthz() -> dict[str, bool]:
        return {"ok": True}

    @test_app.post("/v1/echo")
    async def echo() -> dict[str, bool]:
        return {"ok": True}

    return test_app


def test_security_headers_on_api_paths() -> None:
    response = TestClient(_app()).get("/v1/ping")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["content-security-policy"] == (
        "default-src 'none'; frame-ancestors 'none'"
    )
    assert "strict-transport-security" not in response.headers


def test_healthz_has_headers_but_no_csp() -> None:
    response = TestClient(_app()).get("/healthz")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert "content-security-policy" not in response.headers


def test_hsts_is_added_outside_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")

    response = TestClient(_app()).get("/v1/ping")

    assert response.headers["strict-transport-security"].startswith("max-age=31536000")


def test_request_too_large_is_rejected() -> None:
    response = TestClient(_app(max_request_bytes=10)).post(
        "/v1/echo",
        content=b"x" * 11,
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"


def test_request_within_limit_passes() -> None:
    response = TestClient(_app(max_request_bytes=10)).post(
        "/v1/echo",
        content=b"x" * 10,
    )

    assert response.status_code == 200


def test_main_app_wires_security_middleware() -> None:
    response = TestClient(main_app).get("/healthz")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
