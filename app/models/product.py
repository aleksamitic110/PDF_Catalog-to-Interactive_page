"""Product model."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_BOUNDS_RE = re.compile(r"(\d+)\s*[-–—]\s*(\d+)|(\d+)\s*\+")


def parse_price(text: str | None) -> float | None:
    """Parse an English-style price string like '1,033.70' or '249.31'."""
    if not text:
        return None
    s = text.strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def format_price(value: float) -> str:
    """Render a number Serbian-style: 1033.7 -> '1.033,70'."""
    s = f"{value:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def tier_bounds(label: str) -> tuple[int | None, int | None]:
    """Quantity range encoded in a tier label, e.g. ('1-5 kom') -> (1, 5)."""
    m = _BOUNDS_RE.search(label)
    if not m:
        return None, None
    if m.group(1) is not None:
        return int(m.group(1)), int(m.group(2))
    return int(m.group(3)), None


@dataclass
class Product:
    id: int
    code: str
    name: str
    package: str | None = None
    image_path: str | None = None
    category: str | None = None
    page_number: int | None = None
    raw_text: str | None = None
    tiers: list[tuple[str, str]] = field(default_factory=list)
    akcija: bool = False

    def price_for(self, quantity: int) -> float | None:
        """Best matching tier price for a given quantity, else None.

        Tiers are ordered by ascending quantity; when the quantity does not
        fall inside any tier (e.g. bulk order beyond the last range) the last
        priced tier is used as an approximation.
        """
        priced: list[tuple[int | None, int | None, float]] = []
        for label, value in self.tiers:
            low, high = tier_bounds(label)
            price = parse_price(value)
            if price is None:
                continue
            priced.append((low, high, price))
        if not priced:
            return None
        for low, high, price in priced:
            if high is not None and low <= quantity <= high:
                return price
            if high is None and quantity >= low:
                return price
        return priced[-1][2]