from __future__ import annotations

import ipaddress
import re

from app.core.errors import AppError

ROOT_DOMAIN = "growup.com"

RESERVED_SLUGS = frozenset(
    {
        "admin",
        "api",
        "app",
        "assets",
        "billing",
        "cdn",
        "checkout",
        "docs",
        "mail",
        "pay",
        "platform",
        "static",
        "status",
        "store",
        "support",
        "www",
    }
)

_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def normalize_host(raw_host: str | None) -> str:
    """Normaliza un Host: minúsculas, sin puerto, sin punto final, IDN a punycode."""
    if raw_host is None:
        raise AppError("TENANT_NOT_FOUND", "Host requerido", 404)

    host = raw_host.strip().lower()
    if not host:
        raise AppError("TENANT_NOT_FOUND", "Host vacío", 404)

    if host.startswith("["):
        end = host.find("]")
        if end == -1:
            raise AppError("TENANT_NOT_FOUND", "Host IPv6 inválido", 404)
        host = host[1:end]
    elif host.count(":") == 1:
        host = host.split(":", 1)[0]

    host = host.rstrip(".")
    if not host:
        raise AppError("TENANT_NOT_FOUND", "Host vacío", 404)

    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise AppError("TENANT_NOT_FOUND", "Host inválido", 404) from exc

    if len(host) > 253:
        raise AppError("TENANT_NOT_FOUND", "Host demasiado largo", 404)

    return host


def managed_subdomain_slug(host: str, root_domain: str = ROOT_DOMAIN) -> str | None:
    """Devuelve el slug si el host es `{slug}.{root_domain}`; None si no aplica."""
    root = normalize_host(root_domain)
    if host == root:
        return None

    suffix = f".{root}"
    if not host.endswith(suffix):
        return None

    slug = host[: -len(suffix)]
    if not slug or "." in slug:
        return None

    return slug


def validate_slug(slug: str) -> str:
    if slug in RESERVED_SLUGS:
        raise AppError("SLUG_RESERVED", "Slug reservado", 400)
    if not _SLUG_RE.fullmatch(slug):
        raise AppError("SLUG_INVALID", "Slug inválido", 400)
    return slug


def tenant_slug_from_host(raw_host: str, root_domain: str = ROOT_DOMAIN) -> str:
    """Resuelve el slug de un subdominio gestionado o falla con TENANT_NOT_FOUND."""
    host = normalize_host(raw_host)
    slug = managed_subdomain_slug(host, root_domain)
    if slug is None:
        raise AppError("TENANT_NOT_FOUND", "Host sin tenant", 404)
    return validate_slug(slug)
