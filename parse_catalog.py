"""Command-line catalog parse test (Phase 4).

Usage:
    python parse_catalog.py catalog.pdf
    python parse_catalog.py catalog.pdf --no-images
    python parse_catalog.py catalog.pdf --limit 20

Output:
    Found N products.
    12391 | ARIEL TECNI DETERDZENT 1,8L ALPINE
    ...
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from app.pdf.parser import parse_catalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a catalog PDF.")
    parser.add_argument("pdf", help="Path to the catalog PDF.")
    parser.add_argument("--limit", type=int, default=0,
                        help="Only print first N products (0 = all).")
    parser.add_argument("--no-images", action="store_true",
                        help="Skip image extraction.")
    parser.add_argument("--images-dir", type=str, default=None,
                        help="Where to save product images (default: temp).")
    parser.add_argument("--debug", action="store_true",
                        help="Print per-page debug info.")
    args = parser.parse_args()

    images_dir = None
    if not args.no_images:
        images_dir = Path(args.images_dir) if args.images_dir else Path(
            tempfile.mkdtemp(prefix="catalog_images_")
        )

    print(f"Parsing: {args.pdf}")
    result = parse_catalog(args.pdf, images_dir=images_dir)

    print(f"Pages: {result.pages}")
    if result.scanned_pages:
        print(f"Image-only pages skipped: {result.scanned_pages}")
    print(f"Found {len(result.products)} products.")

    if args.debug:
        print("\nPer-page product counts:")
        for page, count in sorted(result.products_per_page.items()):
            print(f"  Page {page}: {count} products")

    limit = args.limit or len(result.products)
    for product in result.products[:limit]:
        img = product.image_path or "-"
        print(f"{product.code} | {product.name} | paket:{product.package} | {img}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  {warning}")

    if not result.products:
        sys.exit(1)


if __name__ == "__main__":
    main()