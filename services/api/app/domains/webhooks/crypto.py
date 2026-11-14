from __future__ import annotations

import hmac
from hashlib import sha256


def sign_payload(secret_plain: str, body: bytes) -> str:
    return hmac.new(secret_plain.encode("utf-8"), body, sha256).hexdigest()
