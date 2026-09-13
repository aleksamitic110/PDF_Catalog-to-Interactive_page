"""Qt FlowLayout — left-to-right, top-to-bottom wrapping layout.

Adapted from the Qt Corporation example at doc.qt.io/qtforpython/examples/
example_widgets_flowlayout.html.
"""

from __future__ import annotations

from PySide6.QtCore import QMargins, QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QLayoutItem, QSizePolicy, QWidget

CARD_SPACING = 12


class FlowLayout(QLayout):
    """A layout that places widgets left-to-right, wrapping at the width."""

    def __init__(
        self, parent: QWidget | None = None,
        margin: int = 0,
        spacing: int = CARD_SPACING,
    ) -> None:
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self._items: list[QLayoutItem] = []
        self._spacing = spacing

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)
        self.invalidate()

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self.invalidate()
            return item
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientations(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize(0, 0)
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(),
                      margins.top() + margins.bottom())
        return size

    # --------------------------------------------------------------- internal

    @staticmethod
    def _item_size(item: QLayoutItem) -> QSize:
        """Effective size honoring a widget's min/max constraints.

        QLayoutItem returns invalid sizes before the widget is polished, but
        the widget's explicit constraints (setFixedSize etc.) are trustworthy,
        so those win. Fixed-size widgets therefore always resolve correctly.
        """
        widget = item.widget()
        if widget is None:
            return QSize(0, 0)
        mn = widget.minimumSize()
        mx = widget.maximumSize()
        hint = widget.sizeHint()
        width = hint.width() if hint.width() > 0 else mn.width()
        height = hint.height() if hint.height() > 0 else mn.height()
        width = max(mn.width(), min(width, mx.width()))
        height = max(mn.height(), min(height, mx.height()))
        if width <= 0:
            width = mx.width()
        if height <= 0:
            height = mx.height()
        return QSize(max(width, 1), max(height, 1))

    def _do_layout(self, rect: QRect, *, test_only: bool) -> int:
        left, top, right, _ = (
            self.contentsMargins().left(),
            self.contentsMargins().top(),
            self.contentsMargins().right(),
            self.contentsMargins().bottom(),
        )
        effective_x = rect.x() + left
        effective_right = rect.right() - right
        x = effective_x
        y = rect.y() + top
        line_height = 0

        for item in self._items:
            widget = item.widget()
            if widget is None:
                continue
            space_x = self._spacing
            space_y = self._spacing
            size = self._item_size(item)
            next_x = x + size.width() + space_x

            if next_x - space_x > effective_right + 1 and line_height > 0:
                x = effective_x
                y += line_height + space_y
                next_x = x + size.width() + space_x
                line_height = 0

            if not test_only and widget is not None:
                widget.setGeometry(QRect(QPoint(x, y), size))

            x = next_x
            line_height = max(line_height, size.height())

        return y + line_height - rect.y() - top

    # --------------------------------------------------------- public helpers

    def addWidget(self, widget: QWidget) -> None:
        from PySide6.QtWidgets import QWidgetItem as _WI  # noqa: local import to avoid cycles
        self.addItem(_WI(widget))

    def removeWidget(self, widget: QWidget) -> None:
        for i in range(len(self._items) - 1, -1, -1):
            if self._items[i].widget() is widget:
                self.takeAt(i)
                return

    def indexOf(self, widget: QWidget) -> int:
        for i, item in enumerate(self._items):
            if item.widget() is widget:
                return i
        return -1