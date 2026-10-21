from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO

import blurhash  # type: ignore[import-untyped]
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import AppError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_DIMENSION = 6000
MAX_PIXELS = 100_000_000
VARIANT_WIDTHS = (320, 640, 960, 1280, 1600)

# Evita que Pillow intente decodificar imágenes por encima del límite duro.
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

_FORMATS: dict[str, tuple[str, str]] = {
    "JPEG": ("image/jpeg", "jpg"),
    "MPO": ("image/jpeg", "jpg"),
    "PNG": ("image/png", "png"),
    "WEBP": ("image/webp", "webp"),
}
_MIME_ALIASES = {"image/jpg": "image/jpeg"}
_ALLOWED_MIMES = {mime for mime, _ in _FORMATS.values()}


@dataclass(frozen=True, slots=True)
class VariantImage:
    format: str
    width: int
    height: int
    data: bytes

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.data).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class ProcessedImage:
    mime: str
    extension: str
    data: bytes
    width: int
    height: int
    blurhash: str
    variants: tuple[VariantImage, ...]


def normalize_mime(content_type: str) -> str:
    normalized = content_type.split(";", 1)[0].strip().lower()
    return _MIME_ALIASES.get(normalized, normalized)


def ensure_allowed_mime(content_type: str) -> str:
    mime = normalize_mime(content_type)
    if mime not in _ALLOWED_MIMES:
        raise AppError(
            "MEDIA_UNSUPPORTED_TYPE",
            "Solo se aceptan imágenes JPEG, PNG o WebP",
            415,
        )
    return mime


def extension_for_mime(content_type: str) -> str:
    mime = ensure_allowed_mime(content_type)
    for actual_mime, extension in _FORMATS.values():
        if actual_mime == mime:
            return extension
    raise AppError("MEDIA_UNSUPPORTED_TYPE", "Formato no soportado", 415)


def process_image(data: bytes, declared_mime: str) -> ProcessedImage:
    """Valida el MIME real, quita EXIF y genera original saneado + variantes AVIF/WebP."""
    if not data:
        raise AppError("MEDIA_EMPTY", "La imagen está vacía", 400)
    if len(data) > MAX_IMAGE_BYTES:
        raise AppError("MEDIA_TOO_LARGE", "La imagen supera 10 MB", 413)

    expected_mime = ensure_allowed_mime(declared_mime)

    try:
        with Image.open(BytesIO(data)) as probe:
            image_format = probe.format
            width, height = probe.size
            probe.verify()
    except Image.DecompressionBombError as exc:
        raise AppError(
            "MEDIA_DIMENSIONS_EXCEEDED",
            "La imagen supera 6000 px por lado o 100 MP",
            400,
        ) from exc
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise AppError("MEDIA_INVALID", "El archivo no es una imagen válida", 400) from exc

    if image_format not in _FORMATS:
        raise AppError(
            "MEDIA_UNSUPPORTED_TYPE",
            "Solo se aceptan imágenes JPEG, PNG o WebP",
            415,
        )
    actual_mime, extension = _FORMATS[image_format]
    if actual_mime != expected_mime:
        raise AppError(
            "MEDIA_MIME_MISMATCH",
            "El tipo declarado no coincide con el contenido real",
            415,
        )
    if (
        width <= 0
        or height <= 0
        or width > MAX_DIMENSION
        or height > MAX_DIMENSION
        or width * height > MAX_PIXELS
    ):
        raise AppError(
            "MEDIA_DIMENSIONS_EXCEEDED",
            "La imagen supera 6000 px por lado o 100 MP",
            400,
        )

    try:
        with Image.open(BytesIO(data)) as image:
            image.load()
            oriented = ImageOps.exif_transpose(image)
            normalized = _normalize_mode(oriented)
            sanitized = _encode(normalized, image_format)
            variants = _variants(normalized)
            blur_hash = _blurhash(normalized)
    except Image.DecompressionBombError as exc:
        raise AppError(
            "MEDIA_DIMENSIONS_EXCEEDED",
            "La imagen supera 6000 px por lado o 100 MP",
            400,
        ) from exc
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise AppError("MEDIA_INVALID", "No se pudo procesar la imagen", 400) from exc

    return ProcessedImage(
        mime=actual_mime,
        extension=extension,
        data=sanitized,
        width=normalized.width,
        height=normalized.height,
        blurhash=blur_hash,
        variants=variants,
    )


def _normalize_mode(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        return image.convert("RGBA")
    return image.convert("RGB")


def _encode(image: Image.Image, image_format: str) -> bytes:
    buffer = BytesIO()
    if image_format == "JPEG":
        image.convert("RGB").save(
            buffer,
            format="JPEG",
            quality=90,
            optimize=True,
            progressive=True,
        )
    elif image_format == "PNG":
        image.save(buffer, format="PNG", optimize=True)
    else:
        image.save(buffer, format="WEBP", quality=90, method=4)
    return buffer.getvalue()


def _variants(image: Image.Image) -> tuple[VariantImage, ...]:
    targets = {width for width in VARIANT_WIDTHS if width <= image.width}
    if not targets:
        targets = {image.width}
    variants: list[VariantImage] = []
    for target_width in sorted(targets):
        target_height = max(1, round(image.height * target_width / image.width))
        resized = image.resize(
            (target_width, target_height),
            Image.Resampling.LANCZOS,
        )
        for variant_format, image_format in (("avif", "AVIF"), ("webp", "WEBP")):
            buffer = BytesIO()
            save_kwargs: dict[str, object] = {"quality": 80}
            if image_format == "WEBP":
                save_kwargs["method"] = 4
            resized.save(buffer, format=image_format, **save_kwargs)
            variants.append(
                VariantImage(
                    format=variant_format,
                    width=target_width,
                    height=target_height,
                    data=buffer.getvalue(),
                )
            )
    return tuple(variants)


def _blurhash(image: Image.Image) -> str:
    thumb = image.convert("RGB")
    thumb.thumbnail((32, 32))
    width, height = thumb.size
    raw = thumb.tobytes()
    matrix = [
        [
            tuple(raw[index : index + 3])
            for index in range(row * width * 3, (row + 1) * width * 3, 3)
        ]
        for row in range(height)
    ]
    return str(blurhash.encode(matrix, 4, 3))
