from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, str]
