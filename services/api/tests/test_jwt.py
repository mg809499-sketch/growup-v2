import time
from typing import Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, generate_private_key
from jwt.algorithms import RSAAlgorithm

from app.core.errors import AppError
from app.core.security.jwt import JWKSCache, JWTVerifier, TokenClaims

ISSUER = "https://example.supabase.co/auth/v1"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"
AUDIENCE = "authenticated"


@pytest.fixture(scope="module")
def rsa_keypair() -> tuple[RSAPrivateKey, dict[str, Any]]:
    private_key = generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    assert isinstance(public_jwk, dict)
    public_jwk.update({"kid": "test-key", "alg": "RS256", "use": "sig"})
    return private_key, public_jwk


def _payload(**overrides: Any) -> dict[str, Any]:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": "user-1",
        "aud": AUDIENCE,
        "iss": ISSUER,
        "exp": now + 3600,
        "iat": now,
        "email": "owner@example.com",
        "app_metadata": {
            "tenant_id": "6f0f3a1e-3a47-4f1f-9a2b-2f8f1c5d7e10",
            "role": "owner",
        },
    }
    payload.update(overrides)
    return payload


def _token(private_key: RSAPrivateKey, **overrides: Any) -> str:
    return jwt.encode(
        _payload(**overrides),
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


async def _verify(
    token: str,
    public_jwk: dict[str, Any],
    *,
    leeway_seconds: int = 0,
    jwks_status: int = 200,
) -> TokenClaims:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == JWKS_URL
        if jwks_status != 200:
            return httpx.Response(jwks_status, json={"error": "unavailable"})
        return httpx.Response(200, json={"keys": [public_jwk]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        verifier = JWTVerifier(
            jwks_url=JWKS_URL,
            issuer=ISSUER,
            audience=AUDIENCE,
            leeway_seconds=leeway_seconds,
            jwks=JWKSCache(JWKS_URL, client=client),
        )
        return await verifier.verify(token)


async def test_verify_valid_token(rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]]) -> None:
    private_key, public_jwk = rsa_keypair

    claims = await _verify(_token(private_key), public_jwk)

    assert claims.subject == "user-1"
    assert claims.tenant_id is not None
    assert str(claims.tenant_id) == "6f0f3a1e-3a47-4f1f-9a2b-2f8f1c5d7e10"
    assert claims.role == "owner"
    assert claims.email == "owner@example.com"
    assert claims.audience == AUDIENCE


async def test_expired_token_is_rejected(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    private_key, public_jwk = rsa_keypair
    now = int(time.time())
    token = _token(private_key, exp=now - 60, iat=now - 3600)

    with pytest.raises(AppError) as exc_info:
        await _verify(token, public_jwk)

    assert exc_info.value.code == "TOKEN_EXPIRED"


async def test_leeway_allows_recently_expired_token(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    private_key, public_jwk = rsa_keypair
    now = int(time.time())
    token = _token(private_key, exp=now - 10, iat=now - 3600)

    claims = await _verify(token, public_jwk, leeway_seconds=30)

    assert claims.subject == "user-1"


async def test_wrong_audience_is_rejected(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    private_key, public_jwk = rsa_keypair

    with pytest.raises(AppError) as exc_info:
        await _verify(_token(private_key, aud="other"), public_jwk)

    assert exc_info.value.code == "TOKEN_INVALID"


async def test_wrong_issuer_is_rejected(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    private_key, public_jwk = rsa_keypair

    with pytest.raises(AppError) as exc_info:
        await _verify(_token(private_key, iss="https://evil.example.com/auth/v1"), public_jwk)

    assert exc_info.value.code == "TOKEN_INVALID"


async def test_tampered_signature_is_rejected(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    private_key, public_jwk = rsa_keypair
    token = _token(private_key)
    tampered = f"{token.rsplit('.', 1)[0]}.AAAA"

    with pytest.raises(AppError) as exc_info:
        await _verify(tampered, public_jwk)

    assert exc_info.value.code == "TOKEN_INVALID"


async def test_token_without_kid_is_rejected(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    private_key, public_jwk = rsa_keypair
    token = jwt.encode(_payload(), private_key, algorithm="RS256")

    with pytest.raises(AppError) as exc_info:
        await _verify(token, public_jwk)

    assert exc_info.value.code == "TOKEN_INVALID"


async def test_alg_none_is_rejected(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    _, public_jwk = rsa_keypair
    token = jwt.encode(_payload(), key="", algorithm="none")

    with pytest.raises(AppError) as exc_info:
        await _verify(token, public_jwk)

    assert exc_info.value.code == "TOKEN_INVALID"


async def test_tenant_id_is_optional(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    private_key, public_jwk = rsa_keypair

    claims = await _verify(
        _token(private_key, app_metadata={"role": "platform_admin"}),
        public_jwk,
    )

    assert claims.tenant_id is None
    assert claims.role == "platform_admin"


async def test_invalid_tenant_id_is_rejected(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    private_key, public_jwk = rsa_keypair

    with pytest.raises(AppError) as exc_info:
        await _verify(
            _token(private_key, app_metadata={"tenant_id": "not-a-uuid", "role": "owner"}),
            public_jwk,
        )

    assert exc_info.value.code == "TOKEN_INVALID"


async def test_invalid_app_metadata_is_rejected(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    private_key, public_jwk = rsa_keypair

    with pytest.raises(AppError) as exc_info:
        await _verify(_token(private_key, app_metadata="nope"), public_jwk)

    assert exc_info.value.code == "TOKEN_INVALID"


async def test_malformed_token_is_rejected(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    _, public_jwk = rsa_keypair

    with pytest.raises(AppError) as exc_info:
        await _verify("not-a-token", public_jwk)

    assert exc_info.value.code == "TOKEN_INVALID"


async def test_jwks_unavailable_is_rejected(
    rsa_keypair: tuple[RSAPrivateKey, dict[str, Any]],
) -> None:
    private_key, public_jwk = rsa_keypair

    with pytest.raises(AppError) as exc_info:
        await _verify(_token(private_key), public_jwk, jwks_status=503)

    assert exc_info.value.code == "TOKEN_INVALID"
