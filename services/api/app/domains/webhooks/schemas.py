from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_ALLOWED_EVENTS = frozenset({"orders.paid", "orders.created"})
_URL_PATTERN = r"^https?://"


class WebhookEndpointCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: str = Field(min_length=1, max_length=64)
    target_url: str = Field(min_length=9, max_length=2048, pattern=_URL_PATTERN)

    @field_validator("event")
    @classmethod
    def _allowed_event(cls, value: str) -> str:
        if value not in _ALLOWED_EVENTS:
            raise ValueError(f"Evento no soportado: {value}")
        return value


class WebhookEndpointOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    event: str
    target_url: str
    active: bool
    fail_count: int
    created_at: datetime
    updated_at: datetime


class WebhookEndpointCreateResponse(WebhookEndpointOut):
    secret: str  # solo en la creación, mostrar solo una vez
