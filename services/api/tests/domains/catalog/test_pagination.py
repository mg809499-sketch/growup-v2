from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.errors import AppError
from app.domains.catalog.pagination import decode_cursor, encode_cursor


def test_cursor_roundtrip() -> None:
    created_at = datetime.now(UTC)
    product_id = uuid4()

    cursor = encode_cursor(created_at, product_id)
    decoded_at, decoded_id = decode_cursor(cursor)

    assert decoded_at == created_at
    assert decoded_id == product_id


def test_invalid_cursor_is_rejected() -> None:
    with pytest.raises(AppError) as exc_info:
        decode_cursor("not-a-valid-cursor")

    assert exc_info.value.code == "INVALID_CURSOR"
    assert exc_info.value.status_code == 400
