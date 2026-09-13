"""Whole-word, case-insensitive search matching tests."""

from __future__ import annotations

from app.models.product import Product
from app.ui.product_list import CATEGORY_ALL, ProductList


def _p(name: str, code: str, category: str = "Kategorija") -> Product:
    return Product(
        id=0, code=code, name=name, package="", image_path=None,
        category=category, page_number=1, raw_text="",
    )


def test_word_match_is_whole_word_case_insensitive() -> None:
    # "dove" is only a whole word in the first, not in "Sudove"
    assert ProductList._matches(_p("Dove tečni sapun", "1"), ["dove"], CATEGORY_ALL)
    assert ProductList._matches(_p("Dove tečni sapun", "1"), ["DOVE"], CATEGORY_ALL)
    assert not ProductList._matches(_p("Sudove mesa", "2"), ["dove"], CATEGORY_ALL)


def test_partial_word_does_not_match() -> None:
    assert not ProductList._matches(_p("Sapun", "1"), ["sap"], CATEGORY_ALL)
    assert not ProductList._matches(_p("123456", "2"), ["123"], CATEGORY_ALL)


def test_multiple_terms_must_all_match() -> None:
    product = _p("Dove tečni sapun 600ml", "1")
    assert ProductList._matches(product, ["dove", "sapun"], CATEGORY_ALL)
    assert not ProductList._matches(product, ["dove", "šampon"], CATEGORY_ALL)


def test_code_search_matches_whole_code() -> None:
    # parser stores normalized codes: "M12391" -> "12391"
    product = _p("Nesto", "12391")
    assert ProductList._matches(product, ["12391"], CATEGORY_ALL)
    # a prefixed code is not a whole word inside the normalized one
    assert not ProductList._matches(product, ["m12391"], CATEGORY_ALL)


def test_category_filter_combined_with_search() -> None:
    product = _p("Ariel kapsule", "1", category="Ariel")
    assert ProductList._matches(product, ["ariel"], CATEGORY_ALL)
    assert ProductList._matches(product, ["kapsule"], "Ariel")
    assert not ProductList._matches(product, ["kapsule"], "Ostalo")


def test_empty_tokens_matches_everything() -> None:
    product = _p("Bilo šta", "1")
    assert ProductList._matches(product, [], CATEGORY_ALL)