from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol
from uuid import UUID

from app.core.db import Database
from app.domains.media.models import MediaAsset, MediaStatus, MediaVariant

_ASSET_COLUMNS = (
    "id, tenant_id, r2_key, mime, size_bytes, original_filename, "
    "width, height, alt, blurhash, status"
)


class MediaRepository(Protocol):
    async def create_asset(
        self,
        tenant_id: UUID,
        *,
        asset_id: UUID | None = None,
        r2_key: str,
        mime: str,
        size_bytes: int,
        original_filename: str | None,
    ) -> UUID: ...

    async def get_asset(self, tenant_id: UUID, asset_id: UUID) -> MediaAsset | None: ...

    async def list_assets(
        self,
        tenant_id: UUID,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[tuple[MediaAsset, ...], int]: ...

    async def list_variants(
        self,
        tenant_id: UUID,
        asset_id: UUID,
    ) -> tuple[MediaVariant, ...]: ...

    async def delete_asset(self, tenant_id: UUID, asset_id: UUID) -> bool: ...

    async def set_alt(self, tenant_id: UUID, asset_id: UUID, alt: str) -> None: ...

    async def mark_ready(
        self,
        tenant_id: UUID,
        asset_id: UUID,
        *,
        r2_key: str,
        mime: str,
        size_bytes: int,
        width: int,
        height: int,
        blurhash: str,
    ) -> None: ...

    async def replace_variants(
        self,
        tenant_id: UUID,
        asset_id: UUID,
        variants: Sequence[MediaVariant],
    ) -> None: ...

    async def mark_failed(self, tenant_id: UUID, asset_id: UUID) -> None: ...


class PostgresMediaRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def create_asset(
        self,
        tenant_id: UUID,
        *,
        asset_id: UUID | None = None,
        r2_key: str,
        mime: str,
        size_bytes: int,
        original_filename: str | None,
    ) -> UUID:
        async with self._database.tenant_transaction(tenant_id) as connection:
            if asset_id is None:
                created_id = await connection.fetchval(
                    """
                    insert into app.media_assets
                        (tenant_id, r2_key, mime, size_bytes, original_filename)
                    values ($1, $2, $3, $4, $5)
                    returning id
                    """,
                    tenant_id,
                    r2_key,
                    mime,
                    size_bytes,
                    original_filename,
                )
            else:
                created_id = await connection.fetchval(
                    """
                    insert into app.media_assets
                        (id, tenant_id, r2_key, mime, size_bytes, original_filename)
                    values ($1, $2, $3, $4, $5, $6)
                    returning id
                    """,
                    asset_id,
                    tenant_id,
                    r2_key,
                    mime,
                    size_bytes,
                    original_filename,
                )
        if created_id is None:
            raise RuntimeError("No se creó el media asset")
        return UUID(str(created_id))

    async def get_asset(self, tenant_id: UUID, asset_id: UUID) -> MediaAsset | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                f"""
                select {_ASSET_COLUMNS}
                from app.media_assets
                where tenant_id = $1 and id = $2
                """,
                tenant_id,
                asset_id,
            )
        return _asset(row) if row is not None else None

    async def list_assets(
        self,
        tenant_id: UUID,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[tuple[MediaAsset, ...], int]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            total = await connection.fetchval(
                """
                select count(*)
                from app.media_assets
                where tenant_id = $1
                  and ($2::text is null or status = $2)
                """,
                tenant_id,
                status,
            )
            rows = await connection.fetch(
                f"""
                select {_ASSET_COLUMNS}
                from app.media_assets
                where tenant_id = $1
                  and ($2::text is null or status = $2)
                order by created_at desc, id desc
                limit $3::int
                offset $4::int
                """,
                tenant_id,
                status,
                limit,
                offset,
            )
        return tuple(_asset(row) for row in rows), int(total or 0)

    async def list_variants(
        self,
        tenant_id: UUID,
        asset_id: UUID,
    ) -> tuple[MediaVariant, ...]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            rows = await connection.fetch(
                """
                select format, width, height, r2_key, size_bytes
                from app.media_variants
                where tenant_id = $1 and media_asset_id = $2
                order by width, format
                """,
                tenant_id,
                asset_id,
            )
        return tuple(
            MediaVariant(
                format=row["format"],
                width=row["width"],
                height=row["height"],
                r2_key=row["r2_key"],
                size_bytes=row["size_bytes"],
            )
            for row in rows
        )

    async def delete_asset(self, tenant_id: UUID, asset_id: UUID) -> bool:
        async with self._database.tenant_transaction(tenant_id) as connection:
            deleted = await connection.fetchval(
                """
                delete from app.media_assets
                where tenant_id = $1 and id = $2
                returning id
                """,
                tenant_id,
                asset_id,
            )
        return deleted is not None

    async def set_alt(self, tenant_id: UUID, asset_id: UUID, alt: str) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            await connection.execute(
                """
                update app.media_assets
                set alt = $3, updated_at = now()
                where tenant_id = $1 and id = $2
                """,
                tenant_id,
                asset_id,
                alt,
            )

    async def mark_ready(
        self,
        tenant_id: UUID,
        asset_id: UUID,
        *,
        r2_key: str,
        mime: str,
        size_bytes: int,
        width: int,
        height: int,
        blurhash: str,
    ) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            await connection.execute(
                """
                update app.media_assets
                set r2_key = $3,
                    mime = $4,
                    size_bytes = $5,
                    width = $6,
                    height = $7,
                    blurhash = $8,
                    status = 'ready',
                    updated_at = now()
                where tenant_id = $1 and id = $2
                """,
                tenant_id,
                asset_id,
                r2_key,
                mime,
                size_bytes,
                width,
                height,
                blurhash,
            )

    async def replace_variants(
        self,
        tenant_id: UUID,
        asset_id: UUID,
        variants: Sequence[MediaVariant],
    ) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            await connection.execute(
                "delete from app.media_variants where tenant_id = $1 and media_asset_id = $2",
                tenant_id,
                asset_id,
            )
            for variant in variants:
                await connection.execute(
                    """
                    insert into app.media_variants
                        (tenant_id, media_asset_id, format, width, height, r2_key, size_bytes)
                    values ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    tenant_id,
                    asset_id,
                    variant.format,
                    variant.width,
                    variant.height,
                    variant.r2_key,
                    variant.size_bytes,
                )

    async def mark_failed(self, tenant_id: UUID, asset_id: UUID) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            await connection.execute(
                """
                update app.media_assets
                set status = 'failed', updated_at = now()
                where tenant_id = $1 and id = $2
                """,
                tenant_id,
                asset_id,
            )


def _asset(row: Any) -> MediaAsset:
    return MediaAsset(
        id=row["id"],
        tenant_id=row["tenant_id"],
        r2_key=row["r2_key"],
        mime=row["mime"],
        size_bytes=row["size_bytes"],
        original_filename=row["original_filename"],
        width=row["width"],
        height=row["height"],
        alt=row["alt"],
        blurhash=row["blurhash"],
        status=MediaStatus(row["status"]),
    )
