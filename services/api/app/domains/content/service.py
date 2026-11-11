from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.core.errors import AppError
from app.domains.content.blocks import PageLayout
from app.domains.content.models import Page, PageVersion
from app.domains.content.repository import PostgresPageRepository

_MAX_LAYOUT_BYTES = 65536


class PageService:
    def __init__(self, repository: PostgresPageRepository) -> None:
        self._repository = repository

    async def list_pages(
        self, tenant_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[Page], int]:
        return await self._repository.list_pages(tenant_id, limit=limit, offset=offset)

    async def get_page(self, tenant_id: UUID, page_id: UUID) -> Page:
        page = await self._repository.get_page(tenant_id, page_id)
        if page is None:
            raise AppError("PAGE_NOT_FOUND", "Página no encontrada", 404)
        return page

    async def create_page(self, tenant_id: UUID, *, slug: str, title: str) -> Page:
        existing = await self._repository.get_page_by_slug(tenant_id, slug)
        if existing is not None:
            raise AppError("PAGE_SLUG_TAKEN", "Ya existe una página con ese slug", 409)
        return await self._repository.create_page(tenant_id, slug=slug, title=title)

    async def update_page(
        self,
        tenant_id: UUID,
        page_id: UUID,
        *,
        title: str | None,
        slug: str | None,
    ) -> Page:
        if slug is not None:
            existing = await self._repository.get_page_by_slug(tenant_id, slug)
            if existing is not None and existing.id != page_id:
                raise AppError("PAGE_SLUG_TAKEN", "Ya existe una página con ese slug", 409)
        page = await self._repository.update_page(tenant_id, page_id, title=title, slug=slug)
        if page is None:
            raise AppError("PAGE_NOT_FOUND", "Página no encontrada", 404)
        return page

    async def latest_version(self, tenant_id: UUID, page_id: UUID) -> PageVersion | None:
        return await self._repository.latest_version(tenant_id, page_id)

    async def get_published_page(self, tenant_id: UUID, slug: str) -> PageVersion:
        version = await self._repository.published_version(tenant_id, slug)
        if version is None:
            raise AppError("PAGE_NOT_FOUND", "Página no publicada", 404)
        return version

    async def get_version(
        self, tenant_id: UUID, page_id: UUID, version_id: UUID
    ) -> PageVersion:
        version = await self._repository.get_version(tenant_id, page_id, version_id)
        if version is None:
            raise AppError("VERSION_NOT_FOUND", "Versión no encontrada", 404)
        return version

    async def create_draft(
        self,
        tenant_id: UUID,
        page_id: UUID,
        *,
        layout: PageLayout,
        actor_id: UUID | None,
    ) -> PageVersion:
        await self.get_page(tenant_id, page_id)
        payload = layout.model_dump(mode="json")
        if len(json_dumps(payload)) > _MAX_LAYOUT_BYTES:
            raise AppError("LAYOUT_TOO_LARGE", "El layout supera el tamaño permitido", 413)
        return await self._repository.create_version(
            tenant_id,
            page_id=page_id,
            layout=payload,
            created_by=actor_id,
        )

    async def publish(
        self,
        tenant_id: UUID,
        page_id: UUID,
        *,
        version_id: UUID,
        expected_version: int,
        actor_id: UUID,
    ) -> PageVersion:
        await self.get_page(tenant_id, page_id)
        version = await self.get_version(tenant_id, page_id, version_id)
        if version.version != expected_version:
            raise AppError(
                "VERSION_CONFLICT",
                "La página cambió desde que se guardó el borrador",
                409,
                {"expected": expected_version, "latest": version.version},
            )
        await self._repository.publish(
            tenant_id, page_id=page_id, version_id=version_id, actor_id=actor_id
        )
        return version

    async def unpublish(self, tenant_id: UUID, page_id: UUID, *, actor_id: UUID) -> None:
        await self.get_page(tenant_id, page_id)
        await self._repository.unpublish(tenant_id, page_id=page_id, actor_id=actor_id)

    async def get_theme(self, tenant_id: UUID) -> dict[str, Any] | None:
        return await self._repository.get_theme(tenant_id)

    async def upsert_theme(self, tenant_id: UUID, *, tokens: dict[str, Any]) -> dict[str, Any]:
        if len(json_dumps(tokens)) > 16384:
            raise AppError(
                "THEME_TOO_LARGE",
                "Los tokens del tema superan el tamaño permitido",
                413,
            )
        return await self._repository.upsert_theme(tenant_id, tokens=tokens)

    # Preview con token firmado HMAC (TTL corto)
    @staticmethod
    def sign_preview_token(
        tenant_id: UUID,
        page_id: UUID,
        version_id: UUID,
        *,
        ttl_seconds: int = 900,
    ) -> str:
        expires = int(time.time()) + ttl_seconds
        payload = f"{tenant_id}.{page_id}.{version_id}.{expires}"
        signature = hmac.new(
            settings.preview_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return f"{payload}.{signature}"

    @staticmethod
    def verify_preview_token(token: str) -> tuple[UUID, UUID, UUID]:
        parts = token.split(".")
        if len(parts) != 5:
            raise AppError("PREVIEW_INVALID", "Token de previsualización inválido", 403)
        tenant_id, page_id, version_id, expires, signature = parts
        payload = f"{tenant_id}.{page_id}.{version_id}.{expires}"
        expected = hmac.new(
            settings.preview_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise AppError("PREVIEW_INVALID", "Token de previsualización inválido", 403)
        try:
            expiry = int(expires)
        except ValueError as exc:
            raise AppError("PREVIEW_INVALID", "Token de previsualización inválido", 403) from exc
        if time.time() > expiry:
            raise AppError("PREVIEW_EXPIRED", "El token de previsualización expiró", 403)
        try:
            return UUID(tenant_id), UUID(page_id), UUID(version_id)
        except ValueError as exc:
            raise AppError("PREVIEW_INVALID", "Token de previsualización inválido", 403) from exc


def json_dumps(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, default=str)
