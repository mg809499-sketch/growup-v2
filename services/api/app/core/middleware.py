from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings

_JSON_HEADERS = [(b"content-type", b"application/json")]

_BASE_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
)

_CSP_HEADER = (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'")
_HSTS_HEADER = (b"strict-transport-security", b"max-age=31536000; includeSubDomains")


class SecurityMiddleware:
    """Headers de seguridad y límite de tamaño del cuerpo JSON.

    El límite se apoya en `Content-Length`; los proxies del borde deben cortar
    los cuerpos chunked que no lo declaren.
    """

    def __init__(self, app: ASGIApp, *, max_request_bytes: int | None = None) -> None:
        self.app = app
        self._max_request_bytes = max_request_bytes or settings.max_request_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = _header(scope, b"content-length")
        transfer_encoding = _header(scope, b"transfer-encoding")
        is_body_method = scope.get("method", "").upper() in ("POST", "PUT", "PATCH")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                length = 0
            if length > self._max_request_bytes:
                await self._send_too_large(send)
                return
        elif is_body_method and transfer_encoding and "chunked" in transfer_encoding.lower():
            # Sin Content-Length no se puede acotar el cuerpo aquí; en producción se rechaza
            # y el borde debe cortar igualmente.
            if settings.environment == "production":
                await self._send_length_required(send)
                return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(_BASE_HEADERS)
                path = scope.get("path", "")
                if path.startswith("/v1/"):
                    headers.append(_CSP_HEADER)
                if settings.environment not in ("local", "test"):
                    headers.append(_HSTS_HEADER)
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)

    async def _send_length_required(self, send: Send) -> None:
        body = (
            b'{"error":{"code":"LENGTH_REQUIRED",'
            b'"message":"Se requiere Content-Length",'
            b'"details":{},"request_id":null}}'
        )
        await send(
            {
                "type": "http.response.start",
                "status": 411,
                "headers": [
                    *_JSON_HEADERS,
                    *_BASE_HEADERS,
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    async def _send_too_large(self, send: Send) -> None:
        body = (
            b'{"error":{"code":"REQUEST_TOO_LARGE",'
            b'"message":"El cuerpo de la petici\xc3\xb3n supera el l\xc3\xadmite permitido",'
            b'"details":{},"request_id":null}}'
        )
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    *_JSON_HEADERS,
                    *_BASE_HEADERS,
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key.lower() == name:
            return str(value.decode())
    return None
