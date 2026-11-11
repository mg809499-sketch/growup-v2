from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class InventoryLevelResponse(BaseModel):
    variant_id: UUID
    location_id: UUID
    location_name: str
    sku: str | None
    available: int
    reserved: int
    sellable: int


class InventoryLevelListResponse(BaseModel):
    items: list[InventoryLevelResponse]
    limit: int
    offset: int
