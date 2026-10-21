from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
import jwt
from jwt import PyJWK

from app.core.errors import AppError

_ALLOWED_ALGORITHMS = frozenset({"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"})


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    tenant_id: UUID | None
    role: str | None
    email: str | None
    audience: str | tuple[str, ...]
    expires_at: datetime
    raw: dict[str, Any]


class JWKSCache:
    """Caché de claves públicas de Supabase, con refresco por TTL o kid desconocido."""

    def __init__(
        self,
        url: str,
        *,
        ttl_seconds: int = 300,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._url = url
        self._ttl_seconds = ttl_seconds
        self._client = client
        self._keys: dict[str, PyJWK] = {}
        self._expires_at = 0.0

    async def get(self, kid: str) -> PyJWK:
        now = time.monotonic()
        if now >= self._expires_at or kid not in self._keys:
            await self._refresh()

        key = self._keys.get(kid)
        if key is None:
            raise AppError("TOKEN_INVALID", "kid desconocido", 401)
        return key

    async def _refresh(self) -> None:
        client = self._client or httpx.AsyncClient(timeout=5.0)
        owns_client = self._client is None
        try:
            response = await client.get(self._url)
            response.raise_for_status()
            payload = response.json()
            raw_keys = payload.get("keys")
            if not isinstance(raw_keys, list):
                raise ValueError("JWKS sin keys")

            parsed: dict[str, PyJWK] = {}
            for item in raw_keys:
                if not isinstance(item, dict):
                    continue
                kid = item.get("kid")
                if not isinstance(kid, str) or not kid:
                    continue
                parsed[kid] = PyJWK(item)

            if not parsed:
                raise ValueError("JWKS vacío")

            self._keys = parsed
            self._expires_at = time.monotonic() + self._ttl_seconds
        except (httpx.HTTPError, ValueError, jwt.PyJWTError) as exc:
            raise AppError("TOKEN_INVALID", "No se pudo cargar JWKS", 401) from exc
        finally:
            if owns_client:
                await client.aclose()


class JWTVerifier:
    """Verifica firma, issuer, audience y claims de un JWT de Supabase."""

    def __init__(
        self,
        *,
        jwks_url: str,
        issuer: str,
        audience: str,
        leeway_seconds: int = 30,
        jwks: JWKSCache | None = None,
    ) -> None:
        self._issuer = issuer.rstrip("/")
        self._audience = audience
        self._leeway_seconds = leeway_seconds
        self._jwks = jwks or JWKSCache(jwks_url)

    async def verify(self, token: str) -> TokenClaims:
        if not token or token.count(".") != 2:
            raise AppError("TOKEN_INVALID", "Token malformado", 401)

        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not isinstance(kid, str) or not kid:
                raise AppError("TOKEN_INVALID", "Token sin kid", 401)

            jwk = await self._jwks.get(kid)
            if jwk.algorithm_name not in _ALLOWED_ALGORITHMS:
                raise AppError("TOKEN_INVALID", "Algoritmo no permitido", 401)
            payload = jwt.decode(
                token,
                jwk.key,
                algorithms=[jwk.algorithm_name],
                audience=self._audience,
                issuer=self._issuer,
                leeway=self._leeway_seconds,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AppError("TOKEN_EXPIRED", "Token expirado", 401) from exc
        except AppError:
            raise
        except jwt.PyJWTError as exc:
            raise AppError("TOKEN_INVALID", "Token inválido", 401) from exc

        return _claims_from_payload(payload)


def _claims_from_payload(payload: dict[str, Any]) -> TokenClaims:
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AppError("TOKEN_INVALID", "sub inválido", 401)

    app_metadata = payload.get("app_metadata", {})
    if not isinstance(app_metadata, dict):
        raise AppError("TOKEN_INVALID", "app_metadata inválido", 401)

    tenant_id: UUID | None = None
    tenant_raw = app_metadata.get("tenant_id")
    if tenant_raw is not None:
        try:
            tenant_id = UUID(str(tenant_raw))
        except (TypeError, ValueError) as exc:
            raise AppError("TOKEN_INVALID", "tenant_id inválido", 401) from exc

    role_raw = app_metadata.get("role")
    role = role_raw if isinstance(role_raw, str) and role_raw else None

    email_raw = payload.get("email")
    email = email_raw if isinstance(email_raw, str) and email_raw else None

    exp_raw = payload.get("exp")
    if not isinstance(exp_raw, (int, float)):
        raise AppError("TOKEN_INVALID", "exp inválido", 401)
    expires_at = datetime.fromtimestamp(float(exp_raw), tz=UTC)

    aud_raw = payload.get("aud")
    if isinstance(aud_raw, str):
        audience: str | tuple[str, ...] = aud_raw
    elif isinstance(aud_raw, list) and all(isinstance(item, str) for item in aud_raw):
        audience = tuple(aud_raw)
    else:
        raise AppError("TOKEN_INVALID", "aud inválido", 401)

    return TokenClaims(
        subject=subject,
        tenant_id=tenant_id,
        role=role,
        email=email,
        audience=audience,
        expires_at=expires_at,
        raw=payload,
    )
