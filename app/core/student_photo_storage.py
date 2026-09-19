from pathlib import Path

from app.core.config import settings

from io import BytesIO

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

def student_photo_directory() -> Path:
    """Return the configured private directory for student photos."""
    return (
        Path(settings.private_upload_dir).resolve()
        / "student_photos"
    )

MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_PHOTO_PIXELS = 16_000_000

ALLOWED_IMAGE_FORMATS = {
    "JPEG": "JPEG",
    "PNG": "PNG",
    "WEBP": "WEBP",
}


def validate_student_photo(content: bytes) -> bytes:
    """Validate and normalize an uploaded student photograph."""

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo file is empty",
        )

    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Photo must not exceed 5 MB",
        )

    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise ValueError("Unsupported image format")

            image.verify()

            with Image.open(BytesIO(content)) as image:
                if image.width * image.height > MAX_PHOTO_PIXELS:
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
                quality=85,
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
