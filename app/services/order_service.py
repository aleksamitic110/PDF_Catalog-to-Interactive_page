"""Order building and validation.

An item only enters the order when:
- it is selected, and
- its quantity is a positive integer.

Before export, every selected product must have a valid quantity.
"""

from __future__ import annotations

from typing import Iterable

from app.models.order import Order, OrderItem
from app.models.product import Product

INVALID_MESSAGES = {
    "empty": "nema unetu količinu",
    "zero": "količina mora biti veća od 0",
    "negative": "količina mora biti pozitivna",
    "decimal": "količina mora biti ceo broj",
    "text": "količina mora biti ceo broj",
}


def parse_quantity(raw: str) -> tuple[int | None, str | None]:
    """Validate a raw quantity string.

    Returns (quantity, error_key). quantity is None when invalid.
    Allowed: "1", " 5 ", "10". Not allowed: "", "0", "-5", "3.5", "abc".
    """
    text = raw.strip()
    if text == "":
        return None, "empty"
    if text[0] == "-":
        if text[1:].isdigit():
            return None, "negative"
        return None, "text"
    if text.isdigit():
        value = int(text)
        if value == 0:
            return None, "zero"
        return value, None
    if any(ch.isalpha() for ch in text):
        return None, "text"
    if "." in text or "," in text:
        return None, "decimal"
    return None, "text"


def parse_quantity_message(raw: str) -> str | None:
    """Return a Serbian human-readable error message, or None if valid."""
    _, error_key = parse_quantity(raw)
    if error_key is None:
        return None
    return INVALID_MESSAGES[error_key]


def build_order(products: Iterable[Product],
                quantities: dict[str, str]) -> tuple[Order, list[str]]:
    """Build an order from selected products.

    Returns (order, errors). ``errors`` lists human-readable messages for
    selected products with missing or invalid quantities.
    """
    order = Order()
    errors: list[str] = []
    for product in products:
        raw = quantities.get(product.code, "").strip()
        value, error_key = parse_quantity(raw)
        if error_key is not None:
            errors.append(
                f"Proizvod {product.name} {INVALID_MESSAGES[error_key]}."
            )
        else:
            order.add_item(product, value)
    return order, errors