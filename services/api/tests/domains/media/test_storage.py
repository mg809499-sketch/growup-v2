from __future__ import annotations

from typing import Any

import pytest

from app.core.errors import AppError
from app.domains.media.storage import R2Storage


class FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class FakeS3Client:
    def __init__(self, objects: dict[str, bytes] | None = None) -> None:
        self.objects = objects or {}
        self.presigned: list[dict[str, Any]] = []
        self.puts: list[dict[str, Any]] = []
        self.deleted: list[str] = []

    def generate_presigned_url(
        self,
        operation: str,
        *,
        Params: dict[str, Any],
        ExpiresIn: int,
    ) -> str:
        self.presigned.append(
            {"operation": operation, "params": Params, "expires_in": ExpiresIn}
        )
        return "https://r2.example/upload"

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        data = self.objects[Key]
        return {
            "Bucket": Bucket,
            "Key": Key,
            "ContentLength": len(data),
            "Body": FakeBody(data),
        }

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        return {"ContentLength": len(self.objects[Key])}

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str,
        CacheControl: str,
    ) -> None:
        self.puts.append(
            {
                "bucket": Bucket,
                "key": Key,
                "body": Body,
                "content_type": ContentType,
                "cache_control": CacheControl,
            }
        )

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        self.deleted.append(Key)
        self.objects.pop(Key, None)


def _storage(client: FakeS3Client) -> R2Storage:
    return R2Storage(
        endpoint_url="https://r2.example",
        access_key_id="key",
        secret_access_key="secret",
        bucket="growup-catalog-test",
        public_base_url="https://cdn.example/",
        client=client,
    )


def test_presigned_put_includes_content_type_and_expiry() -> None:
    client = FakeS3Client()
    storage = _storage(client)

    url = storage.presigned_put(
        "tenant/t/originals/a.jpg",
        content_type="image/jpeg",
        content_length=1024,
        expires_in=600,
    )

    assert url == "https://r2.example/upload"
    assert client.presigned == [
        {
            "operation": "put_object",
            "params": {
                "Bucket": "growup-catalog-test",
                "Key": "tenant/t/originals/a.jpg",
                "ContentType": "image/jpeg",
                "ContentLength": 1024,
            },
            "expires_in": 600,
        }
    ]


async def test_download_enforces_max_bytes() -> None:
    client = FakeS3Client({"tenant/t/a.jpg": b"x" * 20})
    storage = _storage(client)

    assert await storage.download("tenant/t/a.jpg", max_bytes=20) == b"x" * 20

    with pytest.raises(AppError) as exc_info:
        await storage.download("tenant/t/a.jpg", max_bytes=10)

    assert exc_info.value.code == "MEDIA_TOO_LARGE"


async def test_upload_sets_cache_control_and_public_url() -> None:
    client = FakeS3Client()
    storage = _storage(client)

    await storage.upload(
        "tenant/t/variants/a/320.webp",
        b"data",
        content_type="image/webp",
    )

    assert client.puts[0]["content_type"] == "image/webp"
    assert client.puts[0]["cache_control"] == "public, max-age=31536000, immutable"
    assert (
        storage.public_url("tenant/t/variants/a/320.webp")
        == "https://cdn.example/tenant/t/variants/a/320.webp"
    )


def test_missing_credentials_without_client_are_rejected() -> None:
    with pytest.raises(ValueError):
        R2Storage(
            endpoint_url="",
            access_key_id="",
            secret_access_key="",
            bucket="bucket",
            public_base_url="https://cdn.example",
        )


async def test_delete_removes_object() -> None:
    client = FakeS3Client({"tenant/t/a.jpg": b"data"})
    storage = _storage(client)

    await storage.delete("tenant/t/a.jpg")

    assert client.deleted == ["tenant/t/a.jpg"]
    assert client.objects == {}
