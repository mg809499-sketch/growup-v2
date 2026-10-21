from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from app.core.errors import AppError
from app.domains.media.imaging import MAX_IMAGE_BYTES, process_image


def _image_bytes(
    *,
    format: str = "JPEG",
    size: tuple[int, int] = (800, 600),
    mode: str = "RGB",
    exif: Image.Exif | None = None,
) -> bytes:
    buffer = BytesIO()
    image = Image.new(mode, size, "red" if mode == "RGB" else (255, 0, 0, 128))
    save_kwargs: dict[str, object] = {}
    if exif is not None:
        save_kwargs["exif"] = exif
    image.save(buffer, format=format, **save_kwargs)
    return buffer.getvalue()


def test_jpeg_variants_and_blurhash() -> None:
    processed = process_image(_image_bytes(), "image/jpeg")

    assert processed.mime == "image/jpeg"
    assert processed.extension == "jpg"
    assert (processed.width, processed.height) == (800, 600)
    assert processed.blurhash

    assert {variant.format for variant in processed.variants} == {"avif", "webp"}
    assert {variant.width for variant in processed.variants} == {320, 640}

    for variant in processed.variants:
        with Image.open(BytesIO(variant.data)) as image:
            assert image.size == (variant.width, variant.height)
            assert image.format.lower() == variant.format


def test_exif_is_stripped_and_orientation_is_applied() -> None:
    exif = Image.Exif()
    exif[0x010F] = "TestCamera"
    exif[0x0112] = 6  # Rotar 90 grados.
    data = _image_bytes(size=(800, 600), exif=exif)

    processed = process_image(data, "image/jpeg")

    assert (processed.width, processed.height) == (600, 800)
    with Image.open(BytesIO(processed.data)) as sanitized:
        assert sanitized.getexif().get(0x010F) is None
        assert sanitized.getexif().get(0x0112) is None


def test_png_with_alpha_is_preserved() -> None:
    data = _image_bytes(format="PNG", size=(400, 300), mode="RGBA")

    processed = process_image(data, "image/png")

    assert processed.mime == "image/png"
    with Image.open(BytesIO(processed.data)) as sanitized:
        assert sanitized.mode == "RGBA"


def test_mime_mismatch_is_rejected() -> None:
    data = _image_bytes(format="PNG")

    with pytest.raises(AppError) as exc_info:
        process_image(data, "image/jpeg")

    assert exc_info.value.code == "MEDIA_MIME_MISMATCH"
    assert exc_info.value.status_code == 415


def test_gif_is_rejected_even_if_declared_as_jpeg() -> None:
    data = _image_bytes(format="GIF", size=(10, 10))

    with pytest.raises(AppError) as exc_info:
        process_image(data, "image/jpeg")

    assert exc_info.value.code == "MEDIA_UNSUPPORTED_TYPE"


def test_unsupported_declared_type_is_rejected() -> None:
    with pytest.raises(AppError) as exc_info:
        process_image(_image_bytes(), "image/svg+xml")

    assert exc_info.value.code == "MEDIA_UNSUPPORTED_TYPE"


def test_invalid_bytes_are_rejected() -> None:
    with pytest.raises(AppError) as exc_info:
        process_image(b"no soy una imagen", "image/jpeg")

    assert exc_info.value.code == "MEDIA_INVALID"


def test_empty_and_oversized_files_are_rejected() -> None:
    with pytest.raises(AppError) as empty:
        process_image(b"", "image/jpeg")
    assert empty.value.code == "MEDIA_EMPTY"

    with pytest.raises(AppError) as oversized:
        process_image(b"x" * (MAX_IMAGE_BYTES + 1), "image/jpeg")
    assert oversized.value.code == "MEDIA_TOO_LARGE"


def test_dimension_limit_is_enforced() -> None:
    data = _image_bytes(size=(6001, 1))

    with pytest.raises(AppError) as exc_info:
        process_image(data, "image/jpeg")

    assert exc_info.value.code == "MEDIA_DIMENSIONS_EXCEEDED"
