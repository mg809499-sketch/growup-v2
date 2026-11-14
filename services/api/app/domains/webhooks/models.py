from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class WebhookEndpoint:
    id: UUID
    tenant_id: UUID
    event: str
    target_url: str
    secret: str
    active: bool
    fail_count: int
    created_at: datetime
    updated_at: datetime
