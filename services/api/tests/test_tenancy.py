import pytest

from app.core.errors import AppError
from app.core.tenancy import (
    managed_subdomain_slug,
    normalize_host,
    tenant_slug_from_host,
    validate_slug,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ropa.growup.com", "ropa.growup.com"),
        ("  Ropa.Growup.COM:443  ", "ropa.growup.com"),
        ("ropa.growup.com.", "ropa.growup.com"),
        ("añejo.growup.com", "xn--aejo-gqa.growup.com"),
        ("[::1]:8000", "::1"),
        ("127.0.0.1:3000", "127.0.0.1"),
    ],
)
def test_normalize_host(raw: str, expected: str) -> None:
    assert normalize_host(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "["])
def test_normalize_host_rejects_invalid(raw: str | None) -> None:
    with pytest.raises(AppError) as exc_info:
        normalize_host(raw)

    assert exc_info.value.code == "TENANT_NOT_FOUND"
    assert exc_info.value.status_code == 404


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("ropa.growup.com", "ropa"),
        ("joyeria.growup.com", "joyeria"),
        ("growup.com", None),
        ("a.b.growup.com", None),
        ("ropa.example.com", None),
    ],
)
def test_managed_subdomain_slug(host: str, expected: str | None) -> None:
    assert managed_subdomain_slug(host) == expected


def test_tenant_slug_from_host() -> None:
    assert tenant_slug_from_host("ropa.growup.com") == "ropa"


@pytest.mark.parametrize(
    ("host", "code"),
    [
        ("growup.com", "TENANT_NOT_FOUND"),
        ("ropa.example.com", "TENANT_NOT_FOUND"),
        ("admin.growup.com", "SLUG_RESERVED"),
        ("-ropa.growup.com", "SLUG_INVALID"),
    ],
)
def test_tenant_slug_from_host_rejects(host: str, code: str) -> None:
    with pytest.raises(AppError) as exc_info:
        tenant_slug_from_host(host)

    assert exc_info.value.code == code


def test_validate_slug_accepts_valid_slug() -> None:
    assert validate_slug("ropa-2") == "ropa-2"
    assert validate_slug("a") == "a"


@pytest.mark.parametrize("slug", ["admin", "api", "www", "platform"])
def test_validate_slug_rejects_reserved(slug: str) -> None:
    with pytest.raises(AppError) as exc_info:
        validate_slug(slug)

    assert exc_info.value.code == "SLUG_RESERVED"


@pytest.mark.parametrize("slug", ["-ropa", "ropa-", "RoPa", "ropa_2", "a" * 64, ""])
def test_validate_slug_rejects_invalid(slug: str) -> None:
    with pytest.raises(AppError) as exc_info:
        validate_slug(slug)

    assert exc_info.value.code == "SLUG_INVALID"
