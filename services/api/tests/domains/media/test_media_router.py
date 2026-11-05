from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_admin_context, get_media_service
from app.core.errors import AppError
from app.domains.identity.models import Actor, RequestContext, Role
from app.domains.identity.permissions import permissions_for
from app.domains.media.models import MediaAsset, MediaStatus, MediaVariant, UploadTicket
from app.main import app


def _asset(
    *,
    asset_id: UUID | None = None,
    alt: str | None = "Camisa roja",
    status: MediaStatus = MediaStatus.READY,
) -> MediaAsset:
    return MediaAsset(
        id=asset_id or uuid4(),
        tenant_id=uuid4(),
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
        width=800,
        height=600,
        alt=alt,
        blurhash="LDT9R{]9fQ]9",
        status=status,
    )


class FakeMediaService:
    def __init__(self) -> None:
        self.uploads: list[dict[str, object]] = []
        self.completions: list[dict[str, object]] = []
        self.listed: list[dict[str, object]] = []
        self.updated: list[dict[str, object]] = []
        self.deleted: list[object] = []
        self.assets: tuple[MediaAsset, ...] = ()
        self.variants: tuple[MediaVariant, ...] = ()
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
        return _asset(asset_id=asset_id, alt=alt, status=MediaStatus.UPLOADING)

    async def list_assets(
        self,
        tenant_id: object,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[tuple[MediaAsset, ...], int]:
        if self.error is not None:
            raise self.error
        self.listed.append(
            {"tenant_id": tenant_id, "status": status, "limit": limit, "offset": offset}
        )
        return self.assets[offset : offset + limit], len(self.assets)

    async def get_asset_detail(
        self,
        tenant_id: object,
        asset_id: object,
    ) -> tuple[MediaAsset, tuple[MediaVariant, ...]]:
        if self.error is not None:
            raise self.error
        if not self.assets:
            raise AppError("MEDIA_NOT_FOUND", "El media asset no existe", 404)
        return self.assets[0], self.variants

    async def update_alt(
        self,
        tenant_id: object,
        asset_id: object,
        *,
        alt: str,
    ) -> MediaAsset:
        if self.error is not None:
            raise self.error
        self.updated.append({"asset_id": asset_id, "alt": alt})
        return _asset(asset_id=asset_id, alt=alt)

    async def delete_asset(self, tenant_id: object, asset_id: object) -> None:
        if self.error is not None:
            raise self.error
        self.deleted.append(asset_id)


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


def test_list_media_assets() -> None:
    fake = FakeMediaService()
    fake.assets = (_asset(),)
    app.dependency_overrides[get_admin_context] = lambda: _context()
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/v1/admin/media?status=ready&limit=10&offset=0")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["total"] == 1
    assert payload["limit"] == 10
    assert payload["offset"] == 0
    assert payload["items"][0]["status"] == "ready"
    assert fake.listed[0]["status"] == "ready"
    assert fake.listed[0]["limit"] == 10
    assert fake.listed[0]["offset"] == 0


def test_get_media_asset_detail() -> None:
    fake = FakeMediaService()
    asset = _asset()
    fake.assets = (asset,)
    fake.variants = (
        MediaVariant(
            format="webp",
            width=320,
            height=240,
            r2_key="tenant/t/variants/a/320.webp",
            size_bytes=100,
        ),
    )
    app.dependency_overrides[get_admin_context] = lambda: _context()
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.get(f"/v1/admin/media/{asset.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(asset.id)
    assert payload["variants"][0]["format"] == "webp"


def test_get_media_asset_not_found() -> None:
    fake = FakeMediaService()
    app.dependency_overrides[get_admin_context] = lambda: _context()
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.get(f"/v1/admin/media/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MEDIA_NOT_FOUND"


def test_update_media_alt() -> None:
    fake = FakeMediaService()
    asset_id = uuid4()
    app.dependency_overrides[get_admin_context] = lambda: _context()
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.patch(
        f"/v1/admin/media/{asset_id}",
        json={"alt": "Camisa azul"},
    )

    assert response.status_code == 200
    assert response.json()["alt"] == "Camisa azul"
    assert fake.updated[0]["alt"] == "Camisa azul"


def test_delete_media_asset() -> None:
    fake = FakeMediaService()
    asset_id = uuid4()
    app.dependency_overrides[get_admin_context] = lambda: _context()
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.delete(f"/v1/admin/media/{asset_id}")

    assert response.status_code == 204
    assert fake.deleted == [asset_id]


def test_packer_cannot_delete_media() -> None:
    fake = FakeMediaService()
    app.dependency_overrides[get_admin_context] = lambda: _context(Role.PACKER)
    app.dependency_overrides[get_media_service] = lambda: fake
    client = TestClient(app)

    response = client.delete(f"/v1/admin/media/{uuid4()}")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert fake.deleted == []
