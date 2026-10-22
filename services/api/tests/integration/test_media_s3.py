"""E2E de media contra un S3-compatible.

Por defecto levanta `moto` en un hilo (no requiere Docker ni red externa).
Si `GROWUP_TEST_S3_ENDPOINT` está definido, usa ese endpoint (MinIO/R2).

    $env:GROWUP_TEST_DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    uv run pytest tests/integration/test_media_s3.py
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from io import BytesIO
from uuid import UUID, uuid4

import boto3
import httpx
import pytest
from botocore.config import Config
from moto.server import ThreadedMotoServer
from PIL import Image

from app.core.db import Database
from app.domains.media.models import MediaStatus
from app.domains.media.repository import PostgresMediaRepository
from app.domains.media.service import MediaService
from app.domains.media.storage import R2Storage

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")
EXTERNAL_S3_ENDPOINT = os.getenv("GROWUP_TEST_S3_ENDPOINT")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


@pytest.fixture(scope="module")
def s3_endpoint() -> Iterator[str]:
    if EXTERNAL_S3_ENDPOINT:
        yield EXTERNAL_S3_ENDPOINT
        return

    server = ThreadedMotoServer(port=0, verbose=False)
    server.start()
    host, port = server.get_host_and_port()
    try:
        yield f"http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}"
    finally:
        server.stop()


def _jpeg(size: tuple[int, int] = (800, 600)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="JPEG")
    return buffer.getvalue()


def _ensure_bucket(
    *,
    endpoint: str,
    access_key_id: str,
    secret_access_key: str,
    bucket: str,
    region: str,
) -> None:
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region,
        config=Config(signature_version="s3v4"),
    )
    try:
        client.head_bucket(Bucket=bucket)
    except Exception:  # noqa: BLE001 - el bucket local puede no existir aún
        client.create_bucket(Bucket=bucket)


async def test_media_upload_and_processing_against_s3(s3_endpoint: str) -> None:
    assert TEST_DSN is not None

    bucket = os.getenv("GROWUP_TEST_S3_BUCKET", "growup-catalog-local")
    access_key_id = os.getenv("GROWUP_TEST_S3_ACCESS_KEY_ID", "growup")
    secret_access_key = os.getenv("GROWUP_TEST_S3_SECRET_ACCESS_KEY", "growup123")
    region = os.getenv(
        "GROWUP_TEST_S3_REGION",
        "auto" if EXTERNAL_S3_ENDPOINT else "us-east-1",
    )
    _ensure_bucket(
        endpoint=s3_endpoint,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        bucket=bucket,
        region=region,
    )
    storage = R2Storage(
        endpoint_url=s3_endpoint,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        bucket=bucket,
        public_base_url=f"{s3_endpoint.rstrip('/')}/{bucket}",
        region=region,
    )

    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]
    uploaded_keys: list[str] = []

    try:
        async with database.pool.acquire() as connection:
            tenant_id = await connection.fetchval(
                "select app.create_tenant($1, $2, $3)",
                f"it-media-s3-{suffix}",
                f"it-media-s3-{suffix}.growup.com",
                "Media S3 Test",
            )
        tenants.append(tenant_id)

        repository = PostgresMediaRepository(database)
        service = MediaService(repository, storage)
        image = _jpeg()

        ticket = await service.create_upload(
            tenant_id,
            filename="camisa.jpg",
            content_type="image/jpeg",
            size_bytes=len(image),
        )
        uploaded_keys.append(ticket.r2_key)

        async with httpx.AsyncClient() as client:
            upload = await client.put(
                ticket.upload_url,
                content=image,
                headers={"Content-Type": "image/jpeg"},
            )
        assert upload.status_code in (200, 201)

        await service.process_asset(tenant_id, ticket.asset_id)

        asset = await repository.get_asset(tenant_id, ticket.asset_id)
        assert asset is not None
        assert asset.status is MediaStatus.READY
        assert (asset.width, asset.height) == (800, 600)
        assert asset.blurhash

        variants = await repository.list_variants(tenant_id, ticket.asset_id)
        assert {variant.format for variant in variants} == {"avif", "webp"}
        assert {variant.width for variant in variants} == {320, 640}

        for variant in variants:
            uploaded_keys.append(variant.r2_key)
            data = await storage.download(variant.r2_key, max_bytes=1_000_000)
            assert data
            assert storage.public_url(variant.r2_key).endswith(variant.r2_key)
    finally:
        for key in uploaded_keys:
            with contextlib.suppress(Exception):
                await storage.delete(key)
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()
