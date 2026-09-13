"""Product card, in two layouts:

- grid: a compact uniform box (thumbnail left, info right). The card has a
  FIXED size so grid columns and rows stay perfectly aligned regardless of how
  long a product name is.
- list: reads top-down as NAME → PICTURE → DETAILS, spanning the full width
  with no large unused white space.

Long names are wrapped/elided to a fixed number of lines; the full name is
always available as a tooltip.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QFontMetrics, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.product import Product
from app.ui.widgets import QuantityEdit, ThumbnailLabel

GRID_W, GRID_H = 240, 300
LIST_H = 260
NAME_LINES = 2
GRID = "grid"
LIST = "list"


class ProductCard(QFrame):
    selectionChanged = Signal(str, bool)   # (code, checked)
    quantityEdited = Signal(str, str)      # (code, text)

    def __init__(self, product: Product, pixmap: QPixmap | None = None,
                 selected: bool = False, quantity: str = "",
                 mode: str = GRID, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.product = product
        self._pixmap = pixmap
        self._mode = mode

        self.setObjectName("productCard")
        self.setCursor(Qt.PointingHandCursor)

        if mode == GRID:
            self.setFixedSize(GRID_W, GRID_H)
            self._build_grid()
        else:
            self.setFixedHeight(LIST_H)
            self.setMaximumWidth(16777215)
            self._build_list()

        self.set_selected(selected)
        self.set_quantity(quantity)

    # ----------------------------------------------------------------------
    # shared bits
    # ----------------------------------------------------------------------

    def sizeHint(self) -> QSize:
        """Deterministic hint so the flow layout works before polish."""
        if self._mode == GRID:
            return QSize(GRID_W, GRID_H)
        return QSize(800, LIST_H)

    def _apply_style(self) -> None:
        if self.checkbox.isChecked():
            background, border = "#e7f0fb", "2px solid #2f6fd6"
        else:
            background, border = "#ffffff", "1px solid #d0d0d0"
        self.setStyleSheet(
            f"#productCard {{ background: {background}; border: {border};"
            "border-radius: 6px; }"
            "#productCard QLabel { color: #111111; }"
        )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.set_selected(not self.checkbox.isChecked())
            self.selectionChanged.emit(self.product.code, self.checkbox.isChecked())
            event.accept()
            return
        super().mousePressEvent(event)

    def _make_name_label(self, text: str, width: int,
                         font_size: int, lines: int) -> QLabel:
        label = QLabel(text)
        label.setObjectName("nameLabel")
        label.setStyleSheet(
            f"#nameLabel {{ color: #111111; font-size: {font_size}px;"
            "font-weight: 700; }"
        )
        label.setWordWrap(False)
        label.setToolTip(text)
        metrics = label.fontMetrics()
        label.setText(self._elide(text, width, metrics, lines=lines))
        label.setFixedHeight(lines * metrics.lineSpacing())
        return label

    @staticmethod
    def _elide(text: str, width: int, metrics: QFontMetrics,
               lines: int = NAME_LINES) -> str:
        """Wrap text into at most ``lines`` lines, each elided to ``width``."""
        words = text.split()
        if not words:
            return ""
        current = ""
        parts: list[str] = []
        for word in words:
            candidate = f"{current} {word}".strip()
            if current == "" or metrics.horizontalAdvance(candidate) <= width:
                current = candidate
                continue
            if len(parts) < lines - 1:
                parts.append(current)
                current = word
            else:
                current = candidate
                break
        parts.append(metrics.elidedText(current, Qt.ElideRight, width))
        return "\n".join(parts[:lines])

    # ----------------------------------------------------------------------
    # grid layout
    # ----------------------------------------------------------------------

    def _build_grid(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(9, 7, 9, 7)

        self.checkbox = QCheckBox()
        self.checkbox.setToolTip("Izaberi proizvod")
        layout.addWidget(self.checkbox, alignment=Qt.AlignRight)

        thumb = ThumbnailLabel(self._pixmap, size=110)
        layout.addWidget(thumb, alignment=Qt.AlignHCenter)

        self.name_label = self._make_name_label(
            self.product.name, GRID_W - 18, 12, NAME_LINES
        )
        layout.addWidget(self.name_label)

        self.code_label = QLabel(f"Šifra: {self.product.code}")
        self._style_meta(self.code_label)
        layout.addWidget(self.code_label)

        if self.product.package:
            self.package_label = QLabel(f"Paket: {self.product.package}")
            self._style_meta(self.package_label)
            layout.addWidget(self.package_label)

        prices = self._prices_label()
        if prices:
            layout.addWidget(prices)

        layout.addStretch(1)
        self.quantity = QuantityEdit(self.product.code)
        layout.addWidget(self.quantity, alignment=Qt.AlignLeft)

        self._connect()

    # ----------------------------------------------------------------------
    # list layout: NAME -> PICTURE -> DETAILS
    # ----------------------------------------------------------------------

    def _build_list(self) -> None:
        outer = QVBoxLayout(self)
        outer.setSpacing(8)
        outer.setContentsMargins(14, 12, 14, 12)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        self.checkbox = QCheckBox()
        self.checkbox.setToolTip("Izaberi proizvod")
        top_row.addWidget(self.checkbox, alignment=Qt.AlignTop)

        self.name_label = self._make_name_label(
            self.product.name, 820, 16, NAME_LINES
        )
        top_row.addWidget(self.name_label, 1)
        outer.addLayout(top_row)

        prices = self._prices_label(joined=True)
        if prices:
            outer.addWidget(prices)

        body = QHBoxLayout()
        body.setSpacing(14)
        thumb = ThumbnailLabel(self._pixmap, size=150)
        body.addWidget(thumb, alignment=Qt.AlignTop)

        details = QVBoxLayout()
        details.setSpacing(4)
        self.code_label = QLabel(f"Šifra: {self.product.code}")
        self._style_meta(self.code_label)
        details.addWidget(self.code_label)

        if self.product.package:
            self.package_label = QLabel(f"Paket: {self.product.package}")
            self._style_meta(self.package_label)
            details.addWidget(self.package_label)
        if self.product.category:
            self.category_label = QLabel(self.product.category)
            self._style_meta(self.category_label, small=True)
            details.addWidget(self.category_label)

        self.quantity = QuantityEdit(self.product.code)
        details.addWidget(self.quantity)
        details.addStretch(1)
        body.addLayout(details, 1)
        outer.addLayout(body, 1)

        self._connect()

    # ----------------------------------------------------------------------

    @staticmethod
    def _style_meta(label: QLabel, small: bool = False) -> None:
        color = "#777777" if small else "#333333"
        size = "font-size: 12px;" if small else ""
        label.setStyleSheet(f"color: {color}; {size}")

    def _prices_label(self, joined: bool = False) -> QLabel:
        parts = [
            f"{label}: {price.strip().replace('.', ',')}"
            for label, price in self.product.tiers
        ]
        text = "   •   ".join(parts) if joined else "\n".join(parts)
        label = QLabel(text)
        label.setObjectName("pricesLabel")
        label.setStyleSheet(
            "#pricesLabel { color: #0a6638; font-size: 12px; font-weight: 600; }"
        )
        label.setWordWrap(joined)
        label.setToolTip(text)
        return label

    def _connect(self) -> None:
        self._silent = False
        self.checkbox.setChecked(False)
        self.checkbox.toggled.connect(self._on_check_toggled)
        self.quantity.quantityChanged.connect(self.quantityEdited.emit)

    def _on_check_toggled(self, checked: bool) -> None:
        if self._silent:
            return
        self._apply_style()
        self.selectionChanged.emit(self.product.code, checked)

    def set_selected(self, selected: bool) -> None:
        self._silent = True
        self.checkbox.setChecked(selected)
        self._silent = False
        self._apply_style()

    def set_quantity(self, text: str) -> None:
        self._silent = True
        self.quantity.setText(text)
        self._silent = False

    def quantity_text(self) -> str:
        return self.quantity.text().strip()