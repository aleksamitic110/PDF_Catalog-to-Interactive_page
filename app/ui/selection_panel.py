"""Sidebar panel that keeps showing the running order while paging."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class SelectionPanel(QWidget):
    """Pinned list of every product selected so far, page-independent."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.title = QLabel("Izabrani proizvodi")
        self.title.setStyleSheet(
            "font-size: 14px; font-weight: 700; color: #111111;"
        )

        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("color: #555555; font-size: 12px;")

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setStyleSheet(
            "QListWidget { background: #ffffff; color: #111111;"
            "border: 1px solid #d0d0d0; border-radius: 6px; font-size: 12px;}"
        )

        layout.addWidget(self.title)
        layout.addWidget(self.count_label)
        layout.addWidget(self.list_widget, 1)

    def refresh(self, items: list[tuple[str, str, str]]) -> None:
        """items: (code, name, quantity_text) of the currently selected products."""
        self.count_label.setText(str(len(items)))
        self.list_widget.clear()
        for code, name, quantity in items:
            line = f"{name}  –  {code}"
            if quantity:
                line += f"  (x{quantity})"
            self.list_widget.addItem(QListWidgetItem(line))
        if not items:
            empty = QListWidgetItem("Nijedan proizvod nije selektovan.")
            empty.setForeground(Qt.gray)
            self.list_widget.addItem(empty)