from __future__ import annotations

import json
from uuid import UUID

import httpx

from app.core.crypto import decrypt_secret, encrypt_secret
from app.core.errors import AppError
from app.domains.webhooks.crypto import sign_payload
from app.domains.webhooks.repository import PostgresWebhookRepository
from app.domains.webhooks.schemas import (
    WebhookEndpointCreateRequest,
    WebhookEndpointCreateResponse,
    WebhookEndpointOut,
)

MAX_FAILS = 5


class WebhookService:
    def __init__(self, repository: PostgresWebhookRepository) -> None:
        self._repository = repository

    async def create_endpoint(
        self, tenant_id: UUID, payload: WebhookEndpointCreateRequest
    ) -> WebhookEndpointCreateResponse:
        secret_plain = require_secret()
        secret_encrypted = encrypt_secret(secret_plain)
        endpoint_id = await self._repository.create_endpoint(
            tenant_id,
            event=payload.event,
            target_url=str(payload.target_url),
            secret_encrypted=secret_encrypted,
        )
        endpoints = await self._repository.list_endpoints(tenant_id)
        created = next(item for item in endpoints if item.id == endpoint_id)
        return WebhookEndpointCreateResponse(
            id=created.id,
            event=created.event,
            target_url=created.target_url,
            active=created.active,
            fail_count=created.fail_count,
            created_at=created.created_at,
            updated_at=created.updated_at,
            secret=secret_plain,
        )

    async def list_endpoints(self, tenant_id: UUID) -> list[WebhookEndpointOut]:
        endpoints = await self._repository.list_endpoints(tenant_id)
        return [
            WebhookEndpointOut(
                id=item.id,
                event=item.event,
                target_url=item.target_url,
                active=item.active,
                fail_count=item.fail_count,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in endpoints
        ]

    async def delete_endpoint(self, tenant_id: UUID, endpoint_id: UUID) -> None:
        await self._repository.delete_endpoint(tenant_id, endpoint_id)

    async def deliver_pending_paid_events(self) -> None:
        events = await self._repository.fetch_paid_events(limit=25)
        if not events:
            return

        async with httpx.AsyncClient(timeout=10.0) as client:
            for event in events:
                event_id = str(event["id"])
                tenant_id = event["tenant_id"]
                payload = event["payload"] if isinstance(event.get("payload"), dict) else {}
                body = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
                endpoints = await self._repository.load_active_endpoints(tenant_id, "orders.paid")
                if not endpoints:
                    await self._repository.mark_event_processed(event_id)
                    continue
                delivered = False
                for endpoint in endpoints:
                    try:
                        secret_plain = decrypt_secret(endpoint.secret)
                    except AppError:
                        await self._repository.mark_endpoint_failure(
                            tenant_id, endpoint.id, MAX_FAILS
                        )
                        continue
                    signature = sign_payload(secret_plain, body)
                    try:
                        response = await client.post(
                            endpoint.target_url,
                            content=body,
                            headers={
                                "Content-Type": "application/json",
                                "X-Growup-Tenant": str(tenant_id),
                                "X-Growup-Event": "orders.paid",
                                "X-Growup-Hmac-Sha256": signature,
                                "X-Growup-Delivery": event_id,
                            },
                        )
                        status_code = response.status_code
                    except Exception:
                        await self._repository.mark_endpoint_failure(
                            tenant_id, endpoint.id, MAX_FAILS
                        )
                        continue
                    if 200 <= status_code < 300:
                        delivered = True
                        await self._repository.mark_endpoint_success(tenant_id, endpoint.id)
                    else:
                        await self._repository.mark_endpoint_failure(
                            tenant_id, endpoint.id, MAX_FAILS
                        )
                if delivered or all(not endpoint.active for endpoint in endpoints):
                    await self._repository.mark_event_processed(event_id)


def require_secret() -> str:
    import secrets

    return secrets.token_urlsafe(32)
