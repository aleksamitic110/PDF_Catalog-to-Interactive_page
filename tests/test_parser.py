"""Parser tests run against the real catalog PDF.

The parser test requires the sample catalog PDF. If none is found, the
test is skipped (so CI/unit-only runs stay green).
"""

import glob
from pathlib import Path

import pytest

from app.pdf.parser import parse_catalog

_FIXTURE_GLOBS = [
    "samples_pdfs/*.pdf",
    "Sample_PDFs/*.pdf",
    "tests/fixtures/*.pdf",
]


def _find_catalog() -> Path | None:
    root = Path(__file__).resolve().parent.parent
    for pattern in _FIXTURE_GLOBS:
        matches = sorted(root.glob(pattern))
        if matches:
            return matches[0]
    return None


_CATALOG = _find_catalog()


@pytest.mark.skipif(_CATALOG is None, reason="sample catalog PDF not present")
def test_parser_finds_expected_number_of_products():
    result = parse_catalog(_CATALOG)
    assert len(result.products) > 300


@pytest.mark.skipif(_CATALOG is None, reason="sample catalog PDF not present")
def test_parser_flags_akcija_products():
    result = parse_catalog(_CATALOG)
    by_code = {p.code: p for p in result.products}
    flagged = [p for p in result.products if p.akcija]
    assert 20 <= len(flagged) <= 40
    # canonical promotions present in the sample catalog
    for code in ("10036", "11401", "10351"):
        assert by_code[code].akcija, code
    # random non-promotion product must NOT be flagged
    assert not by_code["11951"].akcija


@pytest.mark.skipif(_CATALOG is None, reason="sample catalog PDF not present")
def test_parser_finds_no_duplicate_codes():
    result = parse_catalog(_CATALOG)
    assert result.duplicate_codes == []


@pytest.mark.skipif(_CATALOG is None, reason="sample catalog PDF not present")
def test_parser_normalizes_codes():
    result = parse_catalog(_CATALOG)
    codes = {p.code for p in result.products}
    assert all(code.isdigit() for code in codes)
    assert "12391" in codes


@pytest.mark.skipif(_CATALOG is None, reason="sample catalog PDF not present")
def test_parser_extracts_packages():
    result = parse_catalog(_CATALOG)
    with_package = [p for p in result.products if p.package]
    assert len(with_package) == len(result.products)


@pytest.mark.skipif(_CATALOG is None, reason="sample catalog PDF not present")
def test_parser_extracts_price_tiers():
    result = parse_catalog(_CATALOG)
    with_tiers = [p for p in result.products if p.tiers]
    assert len(with_tiers) / len(result.products) > 0.9
    assert sum(1 for p in result.products if len(p.tiers) == 3) > 600
    sample = next((p for p in result.products if len(p.tiers) == 3), None)
    assert sample is not None
    assert all(
        len(t) == 2 and bool(t[0]) and t[1].replace(",", "").replace(".", "").isdigit()
        for t in sample.tiers
    )
    by_code = {p.code: p.tiers for p in result.products}
    if "11914" in by_code:
        assert by_code["11914"] == [
            ("1-3 kom", "652.68"),
            ("4-7 kom", "619.38"),
            ("8+ kom", "599.4"),
        ]


@pytest.mark.skipif(_CATALOG is None, reason="sample catalog PDF not present")
def test_parser_generates_at_least_some_categories():
    result = parse_catalog(_CATALOG)
    assert len(result.category_counts) >= 10


@pytest.mark.skipif(_CATALOG is None, reason="sample catalog PDF not present")
def test_image_linking_covers_most_products(tmp_path):
    result = parse_catalog(_CATALOG, images_dir=tmp_path)
    with_image = [p for p in result.products if p.image_path]
    assert len(with_image) / len(result.products) > 0.7