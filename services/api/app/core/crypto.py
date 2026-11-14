"""Cifrado reversible para secretos de terceros en reposo (Fernet / AES-128-CBC+HMAC).

La clave maestra es GROWUP_PAYMENT_KEY (32 bytes en base64 urlsafe). En local/CI se
usa una clave de desarrollo fija y evidente; en producción es obligatorio configurarla
y rotarla. Nunca se loggea ni se expone por la API.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.errors import AppError

# Clave de desarrollo fija (SOLO local/test). 32 bytes base64.
_DEV_KEY = base64.urlsafe_b64encode(b"growup-dev-payment-key-32bytes!!")


def _fernet() -> Fernet:
    key = settings.payment_key.encode() if settings.payment_key else _DEV_KEY
    # Aceptar claves arbitrarias razonables derivándolas si no vienen en formato Fernet.
    try:
        return Fernet(key)
    except (ValueError, TypeError):
        digest = hashlib.sha256(key).digest()
        return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except UnicodeEncodeError as exc:
        raise AppError("SECRET_INVALID", "No se pudo descifrar el secreto", 500) from exc
    except InvalidToken as exc:
        raise AppError("SECRET_INVALID", "No se pudo descifrar el secreto", 500) from exc
