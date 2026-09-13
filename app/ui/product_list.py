"""Scrollable product list with grid/list views, pagination and
whole-word search + category filtering.

Only one page of products (default 50) is materialized at a time, fully and
synchronously, so the grid and list always show exactly the same product
count. Selection and quantity state live here as plain Python dicts, decoupled
from the temporary cards, so paging/switching never loses user input.
"""

from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models.product import Product
from app.pdf.image_extractor import thumbnail_for
from app.ui.flow_layout import FlowLayout
from app.ui.product_card import GRID, LIST, ProductCard
from app.ui.widgets import EmptyLabel

PAGE_SIZE = 50
CATEGORY_ALL = "Sve"


class ProductList(QScrollArea):
    selectionToggled = Signal(str, bool)
    quantityEdited = Signal(str, str)
    totalSelectedChanged = Signal(int)
    viewModeChanged = Signal(str)
    pageChanged = Signal(int, int)  # (page, total_pages)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)

        self._products: list[Product] = []
        self._filtered: list[Product] = []
        self._cards: dict[str, ProductCard] = {}
        self._mode = GRID
        self._page = 1
        self._page_size = PAGE_SIZE

        self._selected: dict[str, bool] = {}
        self._quantities: dict[str, str] = {}

        self._container = QWidget()
        self._box = QVBoxLayout(self._container)
        self._box.setContentsMargins(0, 0, 0, 0)
        self._box.setSpacing(0)

        self._grid_host = QWidget()
        self._flow = FlowLayout(self._grid_host, margin=8)
        self._list_host = QWidget()
        self._rows = QVBoxLayout(self._list_host)
        self._rows.setContentsMargins(8, 8, 8, 8)
        self._rows.setSpacing(10)
        self._rows.addStretch(1)

        self._box.addWidget(self._grid_host)
        self._box.addWidget(self._list_host)
        self._list_host.hide()

        self._empty_label: EmptyLabel | None = None
        self._empty_layout: QLayout | None = None

        self.setWidget(self._container)

    # ------------------------------------------------------------------ data

    def set_products(self, products: list[Product]) -> None:
        self._products = list(products)
        self._selected = {p.code: False for p in products}
        self._quantities = {}
        self.refresh()
        self.totalSelectedChanged.emit(0)

    def refresh(self, search: str = "", category: str = CATEGORY_ALL) -> None:
        """Re-filter (whole words, case-insensitive) and reset to page 1."""
        tokens = [t for t in search.split() if t]
        self._filtered = [
            p for p in self._products
            if self._matches(p, tokens, category)
        ]
        self._page = 1
        self._rebuild_page()
        self.pageChanged.emit(self._page, self.total_pages)

    @staticmethod
    def _matches(product: Product, tokens: list[str], category: str) -> bool:
        if category != CATEGORY_ALL and product.category != category:
            return False
        if not tokens:
            return True
        haystack = " ".join(filter(None, [
            product.name, product.code, product.category,
        ]))
        for token in tokens:
            # whole-word, case-insensitive; "dove" must not match "SUDOVE"
            if not re.search(
                rf"\b{re.escape(token)}\b", haystack, re.IGNORECASE
            ):
                return False
        return True

    # ---------------------------------------------------------------- views

    @property
    def view_mode(self) -> str:
        return self._mode

    def set_view_mode(self, mode: str) -> None:
        if mode not in (GRID, LIST) or mode == self._mode:
            return
        self._mode = mode
        self._grid_host.setVisible(mode == GRID)
        self._list_host.setVisible(mode == LIST)
        self._rebuild_page()
        self.viewModeChanged.emit(mode)
        self.pageChanged.emit(self._page, self.total_pages)

    def _active_surface(self) -> FlowLayout | QVBoxLayout:
        return self._flow if self._mode == GRID else self._rows

    # ------------------------------------------------------------- pagination

    @property
    def page_size(self) -> int:
        return 96 if self._mode == GRID else PAGE_SIZE

    @property
    def total_pages(self) -> int:
        if not self._filtered:
            return 1
        return (len(self._filtered) + self.page_size - 1) // self.page_size

    @property
    def page(self) -> int:
        return self._page

    def set_page(self, page: int) -> None:
        page = max(1, min(page, self.total_pages))
        if page == self._page:
            return
        self._page = page
        self._rebuild_page()
        self.pageChanged.emit(self._page, self.total_pages)

    def _page_products(self) -> list[Product]:
        start = (self._page - 1) * self.page_size
        return self._filtered[start:start + self.page_size]

    # -------------------------------------------------------------- render

    def _clear_cards(self) -> None:
        for card in self._cards.values():
            if card.parentWidget() is not None:
                layout = card.parentWidget().layout()
                if layout is not None:
                    layout.removeWidget(card)
            card.deleteLater()
        self._cards = {}

    def _rebuild_page(self) -> None:
        self._clear_cards()
        self.verticalScrollBar().setValue(0)
        host = self._grid_host if self._mode == GRID else self._list_host
        surface = self._active_surface()
        for product in self._page_products():
            card = self._make_card(product, parent=host)
            if self._mode == GRID:
                surface.addWidget(card)
            else:
                surface.insertWidget(surface.count() - 1, card)
            self._cards[product.code] = card
            card.selectionChanged.connect(self._card_selection)
            card.quantityEdited.connect(self._card_quantity)
            card.show()
        self._sync_empty()

    def _make_card(self, product: Product, parent: QWidget) -> ProductCard:
        return ProductCard(
            product,
            pixmap=self._load_pixmap(product),
            selected=self._selected.get(product.code, False),
            quantity=self._quantities.get(product.code, ""),
            mode=self._mode,
            parent=parent,
        )

    @staticmethod
    def _load_pixmap(product: Product) -> QPixmap | None:
        if not product.image_path:
            return None
        pixmap = QPixmap(thumbnail_for(product.image_path))
        if pixmap.isNull():
            return None
        return pixmap

    # --------------------------------------------------------------- state

    def _card_selection(self, code: str, checked: bool) -> None:
        self._selected[code] = checked
        self.selectionToggled.emit(code, checked)
        self.totalSelectedChanged.emit(self.selected_count())

    def _card_quantity(self, code: str, text: str) -> None:
        self._quantities[code] = text
        self.quantityEdited.emit(code, text)

    def set_selected(self, code: str, checked: bool) -> None:
        self._selected[code] = checked
        card = self._cards.get(code)
        if card is not None:
            card.set_selected(checked)
        self.totalSelectedChanged.emit(self.selected_count())

    def clear_selection(self) -> None:
        for code in self._selected:
            self._selected[code] = False
        self._quantities.clear()
        for card in self._cards.values():
            card.set_selected(False)
            card.set_quantity("")
        self.totalSelectedChanged.emit(0)

    def selected_products(self) -> list[Product]:
        return [p for p in self._products if self._selected.get(p.code, False)]

    def selected_count(self) -> int:
        return sum(1 for v in self._selected.values() if v)

    def quantity_of(self, code: str) -> str:
        return self._quantities.get(code, "")

    # -------------------------------------------------------------- empty

    def _sync_empty(self) -> None:
        surface = self._active_surface()
        if self._page_products():
            if self._empty_label is not None:
                if self._empty_layout is not None:
                    self._empty_layout.removeWidget(self._empty_label)
                self._empty_label.deleteLater()
                self._empty_label = None
                self._empty_layout = None
            return
        if self._empty_label is None:
            self._empty_label = EmptyLabel(
                "Nema rezultata. Probaj drugačiju pretragu ili kategoriju."
            )
        host = self._grid_host if self._mode == GRID else self._list_host
        if self._empty_label.parentWidget() is not host:
            self._empty_label.setParent(host)
        if self._empty_layout is not surface:
            if surface.indexOf(self._empty_label) == -1:
                if self._mode == GRID:
                    surface.addWidget(self._empty_label)
                else:
                    surface.insertWidget(0, self._empty_label)
            self._empty_layout = surface
        self._empty_label.show()