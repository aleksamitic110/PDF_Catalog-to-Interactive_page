"""Extract product images from the PDF and save them to a cache directory.

Images are matched to products by grid position:

- every product cell in the catalog is laid out as image (left) + price/code
  text column (right);
- the product code therefore sits below and to the right of its own image;
- we pick the image whose top edge is the smallest value greater than the
  code's y, preferring the rightmost such image in that row.
"""

from __future__ import annotations

from pathlib import Path

from app.utils.image_utils import make_thumbnail

DECORATIVE_XREFS = {188}
HEADER_STRIP_SIZE = (555, 83)
THUMB_SUFFIX = "_thumb.jpg"


def _product_images(page) -> list[dict]:
    return [
        info
        for info in page.get_image_info(xrefs=True)
        if info["xref"] not in DECORATIVE_XREFS
        and (info["width"], info["height"]) != HEADER_STRIP_SIZE
    ]


def link_images_to_codes(
    page, code_positions: dict[str, tuple[float, float]]
) -> dict[str, int]:
    """Map normalized code -> image xref for the given page."""
    infos = _product_images(page)
    if not infos:
        return {}
    linked: dict[str, int] = {}
    for code, (x, y) in code_positions.items():
        eligible = [
            info for info in infos if info["bbox"][1] > y and info["bbox"][2] < x
        ]
        if not eligible:
            continue
        best = min(eligible, key=lambda info: (info["bbox"][1], -info["bbox"][2]))
        linked[code] = best["xref"]
    return linked


def extract_product_images(
    document, code_to_xref: dict[str, int], images_dir: Path
) -> dict[str, str | None]:
    """Save unique product images as ``<code>.<ext>``.

    Returns a map of product code -> saved file path (None on failure).
    Images referenced by several products are saved only once.
    """
    images_dir.mkdir(parents=True, exist_ok=True)
    saved_xrefs: dict[int, str] = {}
    results: dict[str, str | None] = {}

    for code, xref in code_to_xref.items():
        if xref in saved_xrefs:
            results[code] = saved_xrefs[xref]
            continue
        try:
            info = document.extract_image(xref)
        except Exception:
            results[code] = None
            continue
        ext = info["ext"] or "jpg"
        target = images_dir / f"{code}.{ext}"
        target.write_bytes(info["image"])
        make_thumbnail(target, target_size=300, output_path=thumbnail_path(str(target)))
        saved_xrefs[xref] = str(target)
        results[code] = str(target)
    return results


def thumbnail_path(image_path: str) -> str:
    """Return the thumbnail path for a saved product image."""
    base = Path(image_path)
    return str(base.with_name(base.stem + THUMB_SUFFIX + base.suffix))


def thumbnail_for(image_path: str, size: int = 300) -> str:
    """Create (once) a cached thumbnail next to the image; return its path.

    Falls back to the original image path when thumbnail creation fails.
    """
    thumb = thumbnail_path(image_path)
    if Path(thumb).exists():
        return thumb
    made = make_thumbnail(image_path, target_size=size, output_path=thumb)
    return made or image_path