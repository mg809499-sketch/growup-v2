from __future__ import annotations

from uuid import uuid4

from app.workers.media import process_media


class FakeMediaService:
    def __init__(self) -> None:
        self.calls: list[tuple[object, object]] = []

    async def process_asset(self, tenant_id: object, asset_id: object) -> None:
        self.calls.append((tenant_id, asset_id))


async def test_process_media_delegates_to_service() -> None:
    service = FakeMediaService()
    tenant_id = uuid4()
    asset_id = uuid4()

    await process_media(
        {"media_service": service},
        str(tenant_id),
        str(asset_id),
    )

    assert service.calls == [(tenant_id, asset_id)]
