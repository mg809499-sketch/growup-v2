from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from app.core.db import Database
from app.core.safe_json import safe_json_object
from app.domains.content.models import Page, PageStatus, PageVersion


class PostgresPageRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def list_pages(
        self,
        tenant_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Page], int]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            total = await connection.fetchval(
                "select count(*) from app.pages where tenant_id = $1", tenant_id
            )
            rows = await connection.fetch(
                """
                select id, tenant_id, slug, title, status, published_version_id,
                       created_at, updated_at
                from app.pages
                where tenant_id = $1
                order by updated_at desc
                limit $2 offset $3
                """,
                tenant_id,
                limit,
                offset,
            )
        return [_page(row) for row in rows], int(total or 0)

    async def get_primary_host(self, tenant_id: UUID) -> str | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select host from app.domains
                where tenant_id = $1
                order by is_primary desc, created_at asc
                limit 1
                """,
                tenant_id,
            )
        return row["host"] if row is not None else None

    async def get_page(self, tenant_id: UUID, page_id: UUID) -> Page | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select id, tenant_id, slug, title, status, published_version_id,
                       created_at, updated_at
                from app.pages where tenant_id = $1 and id = $2
                """,
                tenant_id,
                page_id,
            )
        return _page(row) if row is not None else None

    async def get_page_by_slug(self, tenant_id: UUID, slug: str) -> Page | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select id, tenant_id, slug, title, status, published_version_id,
                       created_at, updated_at
                from app.pages where tenant_id = $1 and slug = $2
                """,
                tenant_id,
                slug,
            )
        return _page(row) if row is not None else None

    async def create_page(self, tenant_id: UUID, *, slug: str, title: str) -> Page:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                insert into app.pages (tenant_id, slug, title)
                values ($1, $2, $3)
                returning id, tenant_id, slug, title, status, published_version_id,
                          created_at, updated_at
                """,
                tenant_id,
                slug,
                title,
            )
        return _page(row)

    async def update_page(
        self,
        tenant_id: UUID,
        page_id: UUID,
        *,
        title: str | None,
        slug: str | None,
    ) -> Page | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                update app.pages
                set title = coalesce($3, title),
                    slug = coalesce($4, slug),
                    updated_at = now()
                where tenant_id = $1 and id = $2
                returning id, tenant_id, slug, title, status, published_version_id,
                          created_at, updated_at
                """,
                tenant_id,
                page_id,
                title,
                slug,
            )
        return _page(row) if row is not None else None

    async def latest_version(self, tenant_id: UUID, page_id: UUID) -> PageVersion | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select id, tenant_id, page_id, version, layout, created_by, created_at
                from app.page_versions
                where tenant_id = $1 and page_id = $2
                order by version desc
                limit 1
                """,
                tenant_id,
                page_id,
            )
        return _version(row) if row is not None else None

    async def get_version(
        self,
        tenant_id: UUID,
        page_id: UUID,
        version_id: UUID,
    ) -> PageVersion | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select id, tenant_id, page_id, version, layout, created_by, created_at
                from app.page_versions
                where tenant_id = $1 and page_id = $2 and id = $3
                """,
                tenant_id,
                page_id,
                version_id,
            )
        return _version(row) if row is not None else None

    async def published_version(self, tenant_id: UUID, slug: str) -> PageVersion | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select v.id, v.tenant_id, v.page_id, v.version, v.layout, v.created_by, v.created_at
                from app.pages p
                join app.page_versions v
                  on v.tenant_id = p.tenant_id and v.id = p.published_version_id
                where p.tenant_id = $1 and p.slug = $2 and p.status = 'published'
                """,
                tenant_id,
                slug,
            )
        return _version(row) if row is not None else None

    async def create_version(
        self,
        tenant_id: UUID,
        *,
        page_id: UUID,
        layout: dict[str, Any],
        created_by: UUID | None,
    ) -> PageVersion:
        async with self._database.tenant_transaction(tenant_id) as connection:
            version_number = await connection.fetchval(
                """
                select coalesce(max(version), 0) + 1
                from app.page_versions
                where tenant_id = $1 and page_id = $2
                """,
                tenant_id,
                page_id,
            )
            # La versión almacenada manda: se deriva del máximo actual, nunca del cliente.
            layout_payload = {**layout, "version": version_number}
            row = await connection.fetchrow(
                """
                insert into app.page_versions
                    (tenant_id, page_id, version, layout, created_by)
                values ($1, $2, $3, $4::jsonb, $5)
                returning id, tenant_id, page_id, version, layout, created_by, created_at
                """,
                tenant_id,
                page_id,
                version_number,
                json.dumps(layout_payload),
                created_by,
            )
        return _version(row)

    async def publish(
        self,
        tenant_id: UUID,
        *,
        page_id: UUID,
        version_id: UUID,
        actor_id: UUID,
    ) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            await connection.execute(
                "select app.publish_page($1, $2, $3, $4)",
                tenant_id,
                page_id,
                version_id,
                actor_id,
            )

    async def unpublish(self, tenant_id: UUID, *, page_id: UUID, actor_id: UUID) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            await connection.execute(
                "select app.unpublish_page($1, $2, $3)",
                tenant_id,
                page_id,
                actor_id,
            )

    async def get_theme(self, tenant_id: UUID) -> dict[str, Any] | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                "select tokens from app.themes where tenant_id = $1", tenant_id
            )
        if row is None:
            return None
        theme = safe_json_object(row["tokens"], context="content.theme.get")
        return theme or None

    async def upsert_theme(self, tenant_id: UUID, *, tokens: dict[str, Any]) -> dict[str, Any]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                insert into app.themes (tenant_id, tokens, updated_at)
                values ($1, $2::jsonb, now())
                on conflict (tenant_id) do update set tokens = excluded.tokens, updated_at = now()
                returning tokens
                """,
                tenant_id,
                json.dumps(tokens),
            )
        return safe_json_object(row["tokens"], context="content.theme.upsert")


def _page(row: Any) -> Page:
    return Page(
        id=row["id"],
        tenant_id=row["tenant_id"],
        slug=row["slug"],
        title=row["title"],
        status=PageStatus(row["status"]),
        published_version_id=row["published_version_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _version(row: Any) -> PageVersion:
    layout = row["layout"]
    return PageVersion(
        id=row["id"],
        tenant_id=row["tenant_id"],
        page_id=row["page_id"],
        version=row["version"],
        layout=safe_json_object(layout, context="content.layout.read"),
        created_by=row["created_by"],
        created_at=row["created_at"],
    )
