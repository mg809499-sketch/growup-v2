from __future__ import annotations

from datetime import datetime
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


class AISuggestionResponse(BaseModel):
    id: UUID
    type: str
    status: str
    payload: dict[str, object]
    proposed_at: datetime


class AISuggestionListResponse(BaseModel):
    items: list[AISuggestionResponse]
    total: int
    limit: int
    offset: int


class AISuggestionResolveRequest(BaseModel):
    action: str
