"""Sidebar panel that keeps showing the running order while paging."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SelectionPanel(QWidget):
    """Pinned, scrollable list of every product selected so far.

    Each entry wraps to the panel width; entries are separated by a dashed
    line so the reading order stays clear when many products are picked.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(300)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        self.title = QLabel("Izabrani proizvodi")
        self.title.setStyleSheet(
            "font-size: 14px; font-weight: 700; color: #111111;"
        )

        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("color: #555555; font-size: 12px;")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("selectionScroll")
        self.scroll.setStyleSheet(
            "#selectionScroll { background: #ffffff; border: 1px solid #d0d0d0;"
            "border-radius: 6px; }"
        )

        self._container = QWidget()
        self._container.setObjectName("selectionContainer")
        self._container.setStyleSheet("#selectionContainer { background: #ffffff; }")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(4)
        self.scroll.setWidget(self._container)

        outer.addWidget(self.title)
        outer.addWidget(self.count_label)
        outer.addWidget(self.scroll, 1)

    # ------------------------------------------------------------------ rows

    def refresh(self, items: list[tuple[str, str, str]]) -> None:
        """items: (code, name, quantity_text) of the currently selected products."""
        self.count_label.setText(str(len(items)))

        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not items:
            hint = QLabel("Nijedan proizvod nije selektovan.")
            hint.setWordWrap(True)
            hint.setStyleSheet("color: #888888; font-size: 12px;")
            self._layout.addWidget(hint)
            return

        for index, (code, name, quantity) in enumerate(items):
            if index:
                self._layout.addWidget(self._make_separator())
            self._layout.addWidget(self._make_row(name, code, quantity))
        self._layout.addStretch(1)
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    @staticmethod
    def _make_row(name: str, code: str, quantity: str) -> QLabel:
        line = f"{name}  –  {code}"
        if quantity:
            line += f"  (x{quantity})"
        label = QLabel(line)
        label.setWordWrap(True)
        label.setStyleSheet("color: #111111; font-size: 12px;")
        return label

    @staticmethod
    def _make_separator() -> QFrame:
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        separator.setStyleSheet(
            "QFrame#separator { border: none; border-top: 1px dashed #b0b0b0; }"
        )
        return separator