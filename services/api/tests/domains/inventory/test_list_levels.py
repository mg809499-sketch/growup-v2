from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.domains.inventory.models import InventoryLevel
from app.domains.inventory.service import InventoryService


class FakeInventoryRepository:
    def __init__(self) -> None:
        self.levels: list[InventoryLevel] = []
        self.calls: list[dict[str, object]] = []

    async def list_levels(
        self,
        tenant_id: UUID,
        *,
        variant_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InventoryLevel]:
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "variant_id": variant_id,
                "limit": limit,
                "offset": offset,
            }
        )
        return self.levels


@pytest.mark.asyncio
async def test_list_levels_passes_filters_and_returns_levels() -> None:
    repository = FakeInventoryRepository()
    level = InventoryLevel(
        variant_id=uuid4(),
        location_id=uuid4(),
        location_name="Principal",
        sku="SKU-1",
        available=10,
        reserved=3,
        sellable=7,
    )
    repository.levels.append(level)
    service = InventoryService(repository)  # type: ignore[arg-type]
    tenant_id = uuid4()

    result = await service.list_levels(tenant_id, variant_id=level.variant_id, limit=25, offset=5)

    assert result == [level]
    assert repository.calls == [
        {
            "tenant_id": tenant_id,
            "variant_id": level.variant_id,
            "limit": 25,
            "offset": 5,
        }
    ]
