"""PDF inspection tool (Phase 1).

Usage:
    python inspect_pdf.py <catalog.pdf>
    python inspect_pdf.py <catalog.pdf> --page 5

Dumps raw extracted text per page so the developer can see exactly
how PyMuPDF sees the PDF.
"""

from __future__ import annotations

import argparse
import sys

import pymupdf


def inspect(pdf_path: str, page_filter: int | None = None) -> None:
    document = pymupdf.open(pdf_path)
    total_pages = document.page_count
    print(f"File: {pdf_path}")
    print(f"Pages: {total_pages}")
    print()

    pages = [page_filter] if page_filter is not None else range(total_pages)

    for page_index in pages:
        page = document[page_index]
        text = page.get_text()
        print(f"PAGE {page_index + 1} of {total_pages}")
        print("-" * 60)
        print(text)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect raw PDF text.")
    parser.add_argument("pdf", help="Path to the PDF catalog.")
    parser.add_argument("--page", type=int, default=None,
                        help="Only inspect a single page (1-based).")
    args = parser.parse_args()

    page = args.page - 1 if args.page is not None else None
    try:
        inspect(args.pdf, page)
    except Exception as exc:
        print(f"ERROR: cannot open PDF: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()