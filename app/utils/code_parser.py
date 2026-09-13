"""Product code normalization utilities."""

from __future__ import annotations

import re

_CODE_RE = re.compile(r"^[A-Za-z]?(\d{3,})$")


def normalize_product_code(code: str) -> str | None:
    """Normalize a product code, stripping a leading alpha character.

    M12391 -> 12391, A12345 -> 12345, P98765 -> 98765.
    Values that are not a valid code return None.
    """
    if not code:
        return None
    match = _CODE_RE.match(code.strip())
    if match is None:
        return None
    return match.group(1)