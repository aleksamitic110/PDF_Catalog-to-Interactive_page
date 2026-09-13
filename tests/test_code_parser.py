"""Tests for product code normalization."""

from app.utils.code_parser import normalize_product_code


def test_removes_leading_letter():
    assert normalize_product_code("M12391") == "12391"
    assert normalize_product_code("A12345") == "12345"
    assert normalize_product_code("P98765") == "98765"


def test_keeps_lowercase_prefix():
    assert normalize_product_code("m12391") == "12391"


def test_strips_whitespace():
    assert normalize_product_code("  12391  ") == "12391"


def test_rejects_non_code():
    assert normalize_product_code("12391A") is None
    assert normalize_product_code("abc") is None
    assert normalize_product_code("12") is None
    assert normalize_product_code("") is None
    assert normalize_product_code("12A34") is None
    assert normalize_product_code("KOM") is None


def test_rejects_short_digit_sequences():
    assert normalize_product_code("M12") is None