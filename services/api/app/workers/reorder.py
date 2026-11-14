"""Worker ARQ rule-based (sin LLM): detecta variantes con poco stock
y crea propuestas de reorden para aprobación humana. Nunca ejecuta acciones.
"""

from __future__ import annotations

import json

from app.core.db import Database
from app.core.observability import get_logger

logger = get_logger("growup.worker.reorder")


async def suggest_reorders(ctx: dict[str, object]) -> None:
    database = ctx.get("database")
    if not isinstance(database, Database):
        logger.error("suggest_reorders_missing_database")
        return

    async with database.worker_transaction() as connection:
        tenants = await connection.fetch(
            """
            select distinct t.id
            from app.tenants t
            where t.status in ('active', 'trialing')
            """
        )
        inserted = 0
        for row in tenants:
            tenant_id = row["id"]
            candidates = await connection.fetch(
                "select * from app.detect_reorder_candidates($1, 5)", tenant_id
            )
            for c in candidates:
                result = await connection.execute(
                    """
                    insert into app.ai_suggestions (tenant_id, type, payload)
                    values ($1, 'reorder', $2::jsonb)
                    on conflict do nothing
                    """,
                    tenant_id,
                    json.dumps(
                        {
                            "variant_id": str(c["variant_id"]),
                            "sku": str(c["sku"]),
                            "name": str(c["product_name"]),
                            "stock": c["stock_available"],
                            "threshold": c["threshold"],
                        }
                    ),
                )
                if result == "INSERT 0 1":
                    inserted += 1
        logger.info("suggest_reorders_done", inserted=inserted)
