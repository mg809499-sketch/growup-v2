from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_admin_context, get_media_service
from app.core.errors import AppError
from app.domains.identity.models import Actor, RequestContext, Role
from app.domains.identity.permissions import permissions_for
from app.domains.media.models import MediaAsset, MediaStatus, UploadTicket
from app.main import app


class FakeMediaService:
    def __init__(self) -> None:
        self.uploads: list[dict[str, object]] = []
        self.completions: list[dict[str, object]] = []
        self.error: Exception | None = None

    async def create_upload(
        self,
        tenant_id: object,
        *,
        filename: str,
        content_type: str,
        size_bytes: int,
    ) -> UploadTicket:
        if self.error is not None:
            raise self.error
        asset_id = uuid4()
        self.uploads.append(
            {
                "tenant_id": tenant_id,
                "filename": filename,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "asset_id": asset_id,
            }
        )
        return UploadTicket(
            asset_id=asset_id,
            upload_url="https://r2.example/upload",
            r2_key=f"tenant/{tenant_id}/originals/{asset_id}.jpg",
            expires_in=900,
        )

    async def complete_upload(
        self,
        tenant_id: object,
        asset_id: object,
        *,
        alt: str,
    ) -> MediaAsset:
        if self.error is not None:
            raise self.error
        self.completions.append(
            {"tenant_id": tenant_id, "asset_id": asset_id, "alt": alt}
        )
        return MediaAsset(
            id=asset_id,  # type: ignore[arg-type]
            tenant_id=tenant_id,  # type: ignore[arg-type]
            r2_key="tenant/t/originals/a.jpg",
            mime="image/jpeg",
            size_bytes=10,
            original_filename="a.jpg",
            width=None,
            height=None,
            alt=alt,
            blurhash=None,
            status=MediaStatus.UPLOADING,
        )


def _context(role: Role = Role.OWNER) -> RequestContext:
    tenant_id = uuid4()
    actor = Actor(
        user_id=uuid4(),
        tenant_id=tenant_id,
        role=role,
        email="user@example.com",
    )
    return RequestContext(
        tenant_id=tenant_id,
        actor=actor,
        permissions=permissions_for(role),
        trace_id="trace-1",
        request_id="req-1",
    )


@pytest.fixture(autouse=True)
def _clear_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def test_create_upload_url() -> None:
    fake = FakeMediaService()
    app.dependency_overrides[get_admin_context] = lambda: _context()
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        "/v1/admin/media/upload-url",
        json={
            "filename": "camisa.jpg",
            "content_type": "image/jpeg",
            "size_bytes": 1024,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["upload_url"] == "https://r2.example/upload"
    assert payload["expires_in"] == 900
    assert fake.uploads[0]["filename"] == "camisa.jpg"


def test_complete_upload() -> None:
    fake = FakeMediaService()
    asset_id = uuid4()
    app.dependency_overrides[get_admin_context] = lambda: _context()
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        f"/v1/admin/media/{asset_id}/complete",
        json={"alt": "Camisa roja"},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["id"] == str(asset_id)
    assert payload["status"] == "uploading"
    assert payload["alt"] == "Camisa roja"
    assert fake.completions[0]["alt"] == "Camisa roja"


def test_support_cannot_upload_media() -> None:
    fake = FakeMediaService()
    app.dependency_overrides[get_admin_context] = lambda: _context(Role.SUPPORT)
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        "/v1/admin/media/upload-url",
        json={
            "filename": "camisa.jpg",
            "content_type": "image/jpeg",
            "size_bytes": 1024,
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert fake.uploads == []


def test_queue_unavailable_is_returned() -> None:
    fake = FakeMediaService()
    fake.error = AppError(
        "MEDIA_QUEUE_UNAVAILABLE",
        "La cola no está configurada",
        503,
    )
    app.dependency_overrides[get_admin_context] = lambda: _context()
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        f"/v1/admin/media/{uuid4()}/complete",
        json={"alt": "Camisa roja"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MEDIA_QUEUE_UNAVAILABLE"


def test_invalid_payload_is_rejected() -> None:
    fake = FakeMediaService()
    app.dependency_overrides[get_admin_context] = lambda: _context()
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        "/v1/admin/media/upload-url",
        json={"filename": "camisa.jpg", "content_type": "image/jpeg", "size_bytes": 0},
    )

    assert response.status_code == 422
    assert fake.uploads == []
