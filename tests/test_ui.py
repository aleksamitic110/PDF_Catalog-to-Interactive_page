"""UI card tests: AKCIJA flag renders pill + yellow background (Phase 10)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from PySide6.QtWidgets import QApplication, QLabel

from app.models.product import Product
from app.ui.product_card import ProductCard, GRID, LIST

pytestmark = pytest.mark.usefixtures("_qapp")


@pytest.fixture(scope="session")
def _qapp():
    app = QApplication.instance() or QApplication([])
    return app


def _pro(akcija: bool) -> Product:
    return Product(
        id=0,
        code="11401",
        name="ARIEL KAPSULE 50/1 COLOR",
        tiers=[],
        akcija=akcija,
    )


def _pills(card: ProductCard) -> list[QLabel]:
    return [w for w in card.findChildren(QLabel) if w.objectName() == "akcijaPill"]


def test_akcija_grid_card_is_yellow_with_pill():
    card = ProductCard(_pro(True), mode=GRID)
    assert len(_pills(card)) == 1
    assert "fff3ce" in card.styleSheet()


def test_regular_grid_card_is_white_without_pill():
    card = ProductCard(_pro(False), mode=GRID)
    assert _pills(card) == []
    assert "ffffff" in card.styleSheet() and "fff3ce" not in card.styleSheet()


def test_selected_akcija_card_uses_selection_color():
    card = ProductCard(_pro(True), mode=GRID, selected=True)
    assert "e7f0fb" in card.styleSheet() and "fff3ce" not in card.styleSheet()


def test_akcija_list_card_has_pill():
    card = ProductCard(_pro(True), mode=LIST)
    assert len(_pills(card)) == 1