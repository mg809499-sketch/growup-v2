from __future__ import annotations

import asyncio
from typing import Any, Protocol

import boto3  # type: ignore[import-untyped]
from botocore.config import Config  # type: ignore[import-untyped]

from app.core.errors import AppError

_IMMUTABLE_CACHE = "public, max-age=31536000, immutable"


class MediaStorage(Protocol):
    def presigned_put(
        self,
        key: str,
        *,
        content_type: str,
        expires_in: int = 900,
    ) -> str: ...

    async def download(self, key: str, *, max_bytes: int) -> bytes: ...

    async def upload(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        cache_control: str = _IMMUTABLE_CACHE,
    ) -> None: ...

    async def delete(self, key: str) -> None: ...

    def public_url(self, key: str) -> str: ...


class R2Storage:
    """Adaptador S3-compatible para Cloudflare R2.

    El navegador solo recibe la URL prefirmada; las credenciales viven en el
    servidor. La validación real de MIME/tamaño ocurre en el worker.
    """

    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
        public_base_url: str,
        region: str = "auto",
        client: Any | None = None,
    ) -> None:
        if client is None:
            if not endpoint_url or not access_key_id or not secret_access_key:
                raise ValueError("R2 requiere endpoint y credenciales")
            client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region,
                config=Config(signature_version="s3v4"),
            )
        self._client = client
        self._bucket = bucket
        self._public_base_url = public_base_url.rstrip("/")

    def presigned_put(
        self,
        key: str,
        *,
        content_type: str,
        expires_in: int = 900,
    ) -> str:
        url = self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
        return str(url)

    async def download(self, key: str, *, max_bytes: int) -> bytes:
        response = await asyncio.to_thread(
            self._client.get_object,
            Bucket=self._bucket,
            Key=key,
        )
        length = int(response.get("ContentLength", 0))
        if length > max_bytes:
            raise AppError("MEDIA_TOO_LARGE", "La imagen supera 10 MB", 413)
        body = response["Body"]
        data = await asyncio.to_thread(body.read)
        if len(data) > max_bytes:
            raise AppError("MEDIA_TOO_LARGE", "La imagen supera 10 MB", 413)
        return bytes(data)

    async def upload(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        cache_control: str = _IMMUTABLE_CACHE,
    ) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            CacheControl=cache_control,
        )

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(
            self._client.delete_object,
            Bucket=self._bucket,
            Key=key,
        )

    def public_url(self, key: str) -> str:
        return f"{self._public_base_url}/{key}"
