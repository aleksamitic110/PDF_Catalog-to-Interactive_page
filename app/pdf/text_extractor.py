"""Low-level text extraction from a PDF with PyMuPDF.

Provides two views of a page:

- extract_lines(): lines in the PDF's natural reading order (the order
  returned by ``get_text``), which groups each product's price/code/name
  block contiguously.
- extract_code_positions(): maps a normalized product code to its position
  on the page so images can be linked to the correct grid cell.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pymupdf


def extract_lines(page: "pymupdf.Page") -> list[str]:
    """Return stripped text lines in reading order (``get_text`` order)."""
    return [line.strip() for line in page.get_text().split("\n") if line.strip()]


def extract_code_positions(
    page: "pymupdf.Page", text_data: dict | None = None
) -> dict[str, tuple[float, float]]:
    """Map normalized product code -> (x, y) of its first occurrence."""
    from app.utils.code_parser import normalize_product_code

    positions: dict[str, tuple[float, float]] = {}
    data = text_data if text_data is not None else page.get_text("dict")
    for block in data["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            span = line["spans"][0]
            text = span["text"].strip()
            code = normalize_product_code(text)
            if code is not None and code not in positions:
                positions[code] = (span["bbox"][0], span["bbox"][1])
    return positions