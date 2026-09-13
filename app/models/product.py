"""Product model."""

from __future__ import annotations

from dataclasses import dataclass, field


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