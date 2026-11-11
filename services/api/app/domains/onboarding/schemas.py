from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

_SLUG_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
_PHONE_PATTERN = r"^\+?[0-9][0-9 ()-]{6,19}$"
_DOC_NUMBER_PATTERN = r"^[0-9A-Za-z.-]{4,20}$"
_DOMAIN_PATTERN = (
    r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?"
    r"(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$"
)

DocType = Literal["CC", "CE", "NIT", "PP"]
StoreType = Literal["ropa", "joyeria", "otro"]
DomainChoice = Literal["subdomain", "custom"]


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=2, max_length=200)
    phone: str = Field(min_length=7, max_length=20, pattern=_PHONE_PATTERN)
    doc_type: DocType
    doc_number: str = Field(min_length=4, max_length=20, pattern=_DOC_NUMBER_PATTERN)
    store_name: str = Field(min_length=2, max_length=200)
    store_type: StoreType
    plan_code: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9_-]+$")
    slug: str = Field(min_length=2, max_length=63, pattern=_SLUG_PATTERN)
    domain_choice: DomainChoice
    custom_domain: str | None = Field(default=None, min_length=4, max_length=253, pattern=_DOMAIN_PATTERN)
    wants_subdomain: bool = False

    @model_validator(mode="after")
    def _validate_domain(self) -> SignupRequest:
        if self.domain_choice == "custom" and not self.custom_domain:
            raise ValueError("custom_domain es obligatorio con domain_choice=custom")
        return self


class SignupResponse(BaseModel):
    tenant_id: UUID
    slug: str
    host: str
    store_name: str
