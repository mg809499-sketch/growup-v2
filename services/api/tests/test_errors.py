from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import AppError, app_error_handler
from app.main import app as main_app


def test_app_error_str() -> None:
    error = AppError("TEST_CODE", "algo falló", 409, {"campo": "valor"})

    assert str(error) == "TEST_CODE: algo falló"
    assert error.status_code == 409
    assert error.details == {"campo": "valor"}


def test_app_error_handler_returns_stable_envelope() -> None:
    test_app = FastAPI()
    test_app.add_exception_handler(AppError, app_error_handler)

    @test_app.get("/boom")
    async def boom() -> None:
        raise AppError("TEST_CODE", "boom", 418, {"field": "value"})

    client = TestClient(test_app, raise_server_exceptions=False)
    response = client.get("/boom")

    assert response.status_code == 418
    assert response.json() == {
        "error": {
            "code": "TEST_CODE",
            "message": "boom",
            "details": {"field": "value"},
            "request_id": None,
        }
    }


def test_main_app_sets_request_id_header() -> None:
    client = TestClient(main_app)
    response = client.get("/healthz", headers={"X-Request-ID": "req-test-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-test-1"


def test_main_app_generates_request_id_when_missing() -> None:
    client = TestClient(main_app)
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
