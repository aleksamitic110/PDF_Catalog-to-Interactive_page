"""Image helpers: thumbnails and load-safe wrappers."""

from __future__ import annotations

from pathlib import Path

THUMBNAIL_SIZE = 300


def make_thumbnail(image_path: str | Path, target_size: int = THUMBNAIL_SIZE,
                   output_path: str | Path | None = None) -> str | None:
    """Create a square-ish thumbnail, returning the path or None on failure."""
    from PIL import Image, ImageOps

    try:
        image = Image.open(image_path)
        image.thumbnail((target_size, target_size), Image.LANCZOS)
        thumb_path = (
            Path(output_path)
            if output_path
            else Path(str(image_path) + f"_{target_size}.jpg")
        )
        image.convert("RGB").save(thumb_path, "JPEG", quality=85)
        return str(thumb_path)
    except Exception:
        return None


def load_thumbnail_qpixmap(image_path: str | Path, target_size: int = THUMBNAIL_SIZE):
    """Load an image scaled to ``target_size`` as a QPixmap (best-effort)."""
    from PySide6.QtGui import QPixmap

    pixmap = QPixmap(str(image_path))
    if pixmap.isNull() or max(pixmap.width(), pixmap.height()) <= target_size:
        return pixmap
    return pixmap.scaled(
        target_size, target_size,
        keepAspectRatio=True,
        transformMode=1,  # SmoothTransformation
    )