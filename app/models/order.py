"""Order model."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.product import Product


@dataclass
class OrderItem:
    product: Product
    quantity: int


@dataclass
class Order:
    items: list[OrderItem] = field(default_factory=list)

    def add_item(self, product: Product, quantity: int) -> None:
        self.items.append(OrderItem(product=product, quantity=quantity))

    def clear(self) -> None:
        self.items.clear()

    def is_empty(self) -> bool:
        return len(self.items) == 0