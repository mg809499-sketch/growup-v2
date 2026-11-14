from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.content.blocks import PageLayout
from app.domains.content.models import Page, PageStatus, PageVersion

_SLUG_PATTERN = r"^[a-z0-9](?:[a-z0-9/-]{0,126}[a-z0-9])?$"

_THEME_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
_THEME_MAX_DEPTH = 3
_THEME_MAX_KEYS = 200
_THEME_MAX_STRING = 2048
_THEME_MAX_LIST = 50


def validate_theme_tokens(tokens: dict[str, Any]) -> dict[str, Any]:
    """Cierra el esquema del JSON de tokens de tema (análogo a un metacampo tipado).

    Reglas: claves acotadas, profundidad <= 3, <= 200 claves en total, valores
    planos (str acotada | int | float | bool | None | list acotada). Cualquier
    violación rechaza la escritura con 422 en lugar de persistir basura.
    """
    budget = [_THEME_MAX_KEYS]
    _validate_theme_value(tokens, depth=0, path="tokens", budget=budget)
    return tokens


def _validate_theme_value(value: Any, *, depth: int, path: str, budget: list[int]) -> None:
    if depth > _THEME_MAX_DEPTH:
        raise ValueError(f"{path}: profundidad máxima {_THEME_MAX_DEPTH} excedida")
    if value is None or isinstance(value, bool | int | float):
        return
    if isinstance(value, str):
        if len(value) > _THEME_MAX_STRING:
            raise ValueError(f"{path}: cadena supera {_THEME_MAX_STRING} caracteres")
        return
    if isinstance(value, list):
        if len(value) > _THEME_MAX_LIST:
            raise ValueError(f"{path}: lista supera {_THEME_MAX_LIST} elementos")
        for index, item in enumerate(value):
            _validate_theme_value(item, depth=depth + 1, path=f"{path}[{index}]", budget=budget)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not _THEME_KEY_PATTERN.match(key):
                raise ValueError(f"{path}: clave inválida {key!r}")
            budget[0] -= 1
            if budget[0] < 0:
                raise ValueError(f"{path}: supera {_THEME_MAX_KEYS} claves en total")
            _validate_theme_value(item, depth=depth + 1, path=f"{path}.{key}", budget=budget)
        return
    raise ValueError(f"{path}: tipo de valor no permitido ({type(value).__name__})")


class PageSummary(BaseModel):
    id: UUID
    slug: str
    title: str
    status: PageStatus
    published_version_id: UUID | None
    updated_at: datetime


class PageDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    status: PageStatus
    published_version_id: UUID | None
    updated_at: datetime
    latest_version: int | None


class PageListResponse(BaseModel):
    items: list[PageSummary]
    total: int
    limit: int
    offset: int


class PageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=128, pattern=_SLUG_PATTERN)
    title: str = Field(min_length=1, max_length=200)


class PageUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=128, pattern=_SLUG_PATTERN)


class PageDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layout: PageLayout


class PublishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_id: UUID
    expected_version: int = Field(ge=1)


class StorefrontPageResponse(BaseModel):
    slug: str
    title: str
    version: int
    layout: dict[str, Any]


class ThemeResponse(BaseModel):
    tokens: dict[str, Any] | None


class ThemeUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tokens: dict[str, Any] = Field(min_length=1, max_length=200)

    @field_validator("tokens")
    @classmethod
    def _tokens_valid(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_theme_tokens(value)


def page_summary(page: Page) -> PageSummary:
    return PageSummary(
        id=page.id,
        slug=page.slug,
        title=page.title,
        status=page.status,
        published_version_id=page.published_version_id,
        updated_at=page.updated_at,
    )


def page_detail(page: Page, latest_version: int | None) -> PageDetail:
    return PageDetail(
        id=page.id,
        slug=page.slug,
        title=page.title,
        status=page.status,
        published_version_id=page.published_version_id,
        updated_at=page.updated_at,
        latest_version=latest_version,
    )


def version_response(version: PageVersion) -> dict[str, Any]:
    return {
        "id": version.id,
        "page_id": version.page_id,
        "version": version.version,
        "layout": version.layout,
        "created_by": version.created_by,
        "created_at": version.created_at,
    }
