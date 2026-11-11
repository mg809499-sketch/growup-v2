from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from app import runtime
from app.core.errors import AppError
from app.domains.commerce.service import CommerceService

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


def get_commerce_service() -> CommerceService:
    if runtime.commerce_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El servicio de comercio no está configurado",
            503,
        )
    return runtime.commerce_service


@router.post("/wompi")
async def wompi_webhook(
    request: Request,
    service: Annotated[CommerceService, Depends(get_commerce_service)],
) -> dict[str, str]:
    try:
        event: dict[str, Any] = await request.json()
    except Exception as exc:
        raise AppError("WOMPI_EVENT_INVALID", "Cuerpo JSON inválido", 400) from exc
    if not isinstance(event, dict):
        raise AppError("WOMPI_EVENT_INVALID", "Cuerpo JSON inválido", 400)
    return await service.process_wompi_event(event)
