"""PDF catalog parser (Phase 3).

Reads a product catalog PDF and returns a list of Product objects plus
diagnostics. The parser is pure (no GUI): input is a PDF file, output is
``List[Product]`` unless image extraction is requested.

Heuristics (tuned against the real catalog):

- A product cell is: 3 price tiers (tier label / price / "sa PDV-om" /
  code variant / "sifra"), then the product NAME, then ``PAKET:<n>``.
- Codes appear as M12391 / N12391 / P12391 (one per price tier); all three
  normalize to the same digit string. Only one Product is created per code.
- Product name lines always contain at least one ALL-CAPS word (brand);
  category banners (e.g. "Tečni deterdženti Ariel") contain none, so they
  are treated as the running category instead of part of the name.
- Image-only pages (cover) are skipped with a warning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from app.models.product import Product
from app.pdf import image_extractor
from app.pdf.text_extractor import extract_code_positions, extract_lines
from app.utils.code_parser import normalize_product_code

CODE_RE = re.compile(r"^[A-Za-z](\d{3,})$")
PAKET_RE = re.compile(r"^PAKET\s*[:]?\s*(\d*)$")
TIER_RE = re.compile(r"^\d+(?:-\d+|\+)?\s*(kom|pak)$")
PRICE_RE = re.compile(r"^[\d.,]+$")
NOISE = {
    "sa PDV-om",
    "sifra",
    "SIFRA",
    "NAJBOLJA CENA",
    "PDV",
    "cena",
    "CENA",
    "*",
    "-",
    "PRINT",
    "YEAR",
    "2026",
    "a",
}


@dataclass
class ParseResult:
    products: list[Product] = field(default_factory=list)
    pages: int = 0
    scanned_pages: int = 0
    products_per_page: dict[int, int] = field(default_factory=dict)
    duplicate_codes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    category_counts: dict[str, int] = field(default_factory=dict)

    def any_products(self) -> bool:
        return bool(self.products)


def _is_name_line(line: str) -> bool:
    return any(word.isalpha() and word.isupper() for word in line.split())


def _is_banner_line(line: str) -> bool:
    if TIER_RE.match(line) or PRICE_RE.match(line) or line in NOISE:
        return False
    if PAKET_RE.match(line) or CODE_RE.match(line):
        return False
    return not _is_name_line(line)


def _collect_banners(text_data) -> list[tuple[float, str]]:
    """Return (y, banner_text) for every category banner on the page."""
    banners: list[tuple[float, str]] = []
    for block in text_data["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            span = line["spans"][0]
            text = span["text"].strip()
            if _is_banner_line(text):
                banners.append((span["bbox"][1], text))
    return banners


def _category_for_y(banners: list[tuple[float, str]], y: float) -> str | None:
    best: tuple[float, str] | None = None
    for banner_y, text in banners:
        if banner_y < y and (best is None or banner_y > best[0]):
            best = (banner_y, text)
    return best[1] if best else None


def parse_catalog(
    pdf_path: str | Path,
    images_dir: str | Path | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
) -> ParseResult:
    """Parse the PDF into products, optionally extracting product images."""
    import pymupdf

    result = ParseResult()
    images_dir_path = Path(images_dir) if images_dir else None
    code_to_xref: dict[str, int] = {}
    carry_category: str | None = None

    try:
        document = pymupdf.open(str(pdf_path))
    except Exception as exc:
        result.warnings.append(f"PDF ne moze da se otvori: {exc}")
        return result

    result.pages = document.page_count
    total_pages = document.page_count

    try:
        for page_index in range(total_pages):
            if progress_cb is not None:
                progress_cb(page_index + 1, total_pages)

            page = document[page_index]
            lines = extract_lines(page)
            raw_length = sum(len(line) for line in lines)

            if raw_length < 20:
                result.scanned_pages += 1
                result.warnings.append(
                    f"Stranica {page_index + 1} je verovatno slika (bez teksta), preskocena."
                )
                continue

            page_text = page.get_text()
            text_data = page.get_text("dict")
            positions = extract_code_positions(page, text_data=text_data)
            banners = _collect_banners(text_data)
            akcija_codes = image_extractor.link_badges_to_codes(page, positions)
            linked = (
                image_extractor.link_images_to_codes(page, positions)
                if images_dir_path
                else {}
            )

            current_code: str | None = None
            name_lines: list[str] = []
            page_count = 0
            current_tier_label: str | None = None
            pending_price: str | None = None
            tiers: list[tuple[str, str]] = []

            for line in lines:
                code_match = CODE_RE.match(line)
                if code_match:
                    if current_tier_label is not None and pending_price is not None:
                        tiers.append((current_tier_label, pending_price))
                    current_tier_label = None
                    pending_price = None
                    current_code = code_match.group(1)
                    name_lines = []
                    continue

                package_match = PAKET_RE.match(line)
                if package_match:
                    if current_code is not None and name_lines:
                        page_count += 1
                        name = " ".join(name_lines)
                        code_y = positions.get(current_code, (0.0, 0.0))[1]
                        product = Product(
                            id=0,
                            code=current_code,
                            name=name,
                            package=package_match.group(1) or None,
                            image_path=None,
                            category=_category_for_y(banners, code_y) or carry_category,
                            page_number=page_index + 1,
                            raw_text=page_text,
                            tiers=list(tiers),
                            akcija=current_code in akcija_codes,
                        )
                        result.products.append(product)
                        code_to_xref.setdefault(current_code, linked.get(current_code))
                        current_code = None
                    name_lines = []
                    current_tier_label = None
                    pending_price = None
                    tiers = []
                    continue

                tier_match = TIER_RE.match(line)
                if tier_match:
                    current_tier_label = line
                    pending_price = None
                    continue

                if PRICE_RE.match(line):
                    if current_tier_label is not None:
                        pending_price = line
                    continue

                if line in NOISE:
                    continue

                if _is_name_line(line):
                    name_lines.append(line)

            result.products_per_page[page_index + 1] = page_count

            if banners:
                carry_category = max(banners, key=lambda item: item[0])[1]

        if images_dir_path:
            paths = image_extractor.extract_product_images(
                document, code_to_xref, images_dir_path
            )
            for product in result.products:
                product.image_path = paths.get(product.code)

    finally:
        document.close()

    _post_process(result)
    return result


def _post_process(result: ParseResult) -> None:
    """Assign ids, detect duplicates, compute category counts."""
    seen: dict[str, Product] = {}
    for index, product in enumerate(result.products, start=1):
        product.id = index
        if product.code in seen:
            result.duplicate_codes.append(product.code)
            prior = seen[product.code]
            if prior.name != product.name:
                result.warnings.append(
                    f"DUPLIKAT: sifra {product.code} sa razlicitim nazivima "
                    f"({prior.name} / {product.name})."
                )
        else:
            seen[product.code] = product

    for product in result.products:
        if product.category:
            result.category_counts[product.category] = (
                result.category_counts.get(product.category, 0) + 1
            )

    if not result.products:
        result.warnings.append("Nije pronadjen nijedan prepoznatljiv proizvod u PDF-u.")