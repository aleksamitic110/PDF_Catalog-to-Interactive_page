"""Shared GUI widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

THUMB_SIZE = 240


class ThumbnailLabel(QLabel):
    """A label that shows an image scaled to a fixed thumbnail size."""

    def __init__(self, pixmap: QPixmap | None = None,
                 size: int = THUMB_SIZE, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedWidth(size)
        self.setMinimumHeight(size)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.set_placeholder()
        self.set_pixmap(pixmap)

    def set_placeholder(self) -> None:
        self.setText("No image")
        self.setStyleSheet("color: #888; font-style: italic;")

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        pixmap = self._placeholder_pixmap() if pixmap is None else pixmap
        scaled = pixmap.scaled(
            self._size,
            self._size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        ) if not (pixmap.isNull() or pixmap.width() <= self._size) else pixmap
        if scaled.isNull() or scaled.width() <= 16:
            scaled = self._placeholder_pixmap()
        self.setPixmap(scaled)

    @staticmethod
    def _placeholder_pixmap() -> QPixmap:
        pixmap = QPixmap(1, 1)
        pixmap.fill(Qt.transparent)
        return pixmap


class QuantityEdit(QLineEdit):
    """Text field for quantity; allows only empty or a positive integer."""

    quantityChanged = Signal(str, str)  # (code, text)

    def __init__(self, code: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._code = code
        self.setPlaceholderText("Količina")
        self.setFixedWidth(110)
        self.setMaxLength(6)
        self.setStyleSheet(
            "QLineEdit { background: #ffffff; color: #111111;"
            "border: 1px solid #b0b0b0; border-radius: 4px; padding: 2px 6px; }"
            "QLineEdit:focus { border: 1px solid #2f6fd6; }"
        )
        self.textChanged.connect(self._on_change)

    def _on_change(self, text: str) -> None:
        self.quantityChanged.emit(self._code, text)


class EmptyLabel(QLabel):
    """Centered hint shown when there are no products to display."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("color: #888; font-size: 16px; padding: 48px;")
        self.setWordWrap(True)