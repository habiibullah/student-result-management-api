from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


MAX_LOGO_BYTES = 5 * 1024 * 1024
MAX_LOGO_PIXELS = 16_000_000

ALLOWED_IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}


def school_logo_directory() -> Path:
    """Return the configured private directory for school logos."""
    return Path(settings.private_upload_dir).resolve() / "school_logos"


def validate_school_logo(content: bytes) -> bytes:
    """Validate and normalize an uploaded school logo."""

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logo file is empty",
        )

    if len(content) > MAX_LOGO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Logo must not exceed 5 MB",
        )

    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise ValueError("Unsupported image format")

            image.verify()

        with Image.open(BytesIO(content)) as image:
            if image.width * image.height > MAX_LOGO_PIXELS:
                raise ValueError("Image pixel count is too large")

            if image.width > 4096 or image.height > 4096:
                raise ValueError("Image dimensions are too large")

            image.load()

            normalized = image.convert("RGB")
            normalized.thumbnail((1024, 1024))

            output = BytesIO()
            normalized.save(
                output,
                format="JPEG",
                quality=90,
            )

            return output.getvalue()

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unsupported image file",
        )
