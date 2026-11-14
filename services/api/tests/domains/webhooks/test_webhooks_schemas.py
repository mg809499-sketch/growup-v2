import pytest
from pydantic import ValidationError

from app.domains.webhooks.schemas import WebhookEndpointCreateRequest


def test_sign_payload_deterministic() -> None:
    from app.domains.webhooks.crypto import sign_payload

    assert sign_payload("abc123", b"x") == sign_payload("abc123", b"x")
    assert len(sign_payload("abc123", b"x")) == 64


def test_create_request_valid() -> None:
    body = WebhookEndpointCreateRequest(event="orders.paid", target_url="https://example.com/hook")
    assert body.event == "orders.paid"
    assert body.target_url == "https://example.com/hook"


def test_create_request_rejects_unsupported_event() -> None:
    with pytest.raises(ValidationError):
        WebhookEndpointCreateRequest(event="not.supported", target_url="https://example.com")


def test_create_request_rejects_non_http_url() -> None:
    with pytest.raises(ValidationError):
        WebhookEndpointCreateRequest(event="orders.paid", target_url="ftp://example.com")
