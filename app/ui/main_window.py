"""Main application window (Phase 5-8).

Flow:  Open PDF -> background parse (progress) -> product list with lazy
cards -> search/category -> select + quantity -> export Excel / PDF.
"""

from __future__ import annotations

import pathlib
import sys

from PySide6.QtCore import QStandardPaths, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.export.excel_exporter import export_excel
from app.export.pdf_exporter import export_pdf
from app.pdf.parser import ParseResult, parse_catalog
from app.services.order_service import build_order
from app.ui.product_list import CATEGORY_ALL, GRID, LIST, ProductList
from app.ui.selection_panel import SelectionPanel

WINDOW_TITLE = "PDF Catalog Order Manager"


class ParseWorker(QThread):
    """Parses the catalog in a background thread."""

    progress = Signal(int, int)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, pdf_path: str, images_dir: str, parent=None) -> None:
        super().__init__(parent)
        self._pdf_path = pdf_path
        self._images_dir = images_dir

    def run(self) -> None:
        try:
            result = parse_catalog(
                self._pdf_path,
                images_dir=self._images_dir,
                progress_cb=self.progress.emit,
            )
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            self.failed.emit(str(exc))
            return
        self.finished_ok.emit(result)


def cache_dir(*parts: str) -> pathlib.Path:
    base = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
    directory = pathlib.Path(base).joinpath(*parts)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1280, 860)

        self._worker: ParseWorker | None = None
        self._products = []

        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        top = QHBoxLayout()
        self.open_button = QPushButton("Open PDF")
        self.open_button.clicked.connect(self.open_pdf)
        top.addWidget(self.open_button)

        top.addSpacing(12)
        top.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Pretraži po nazivu, šifri ili kategoriji...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._apply_filter)
        top.addWidget(self.search_edit, 1)

        top.addSpacing(12)
        top.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem(CATEGORY_ALL)
        self.category_combo.currentTextChanged.connect(self._apply_filter)
        top.addWidget(self.category_combo)

        top.addSpacing(12)
        top.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.addItem("Grid")
        self.view_combo.addItem("List")
        self.view_combo.setToolTip("Promeni raspored proizvoda")
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        top.addWidget(self.view_combo)

        root.addLayout(top)

        middle = QHBoxLayout()
        middle.setSpacing(12)
        left = QVBoxLayout()
        left.setSpacing(8)

        self.product_list = ProductList()
        left.addWidget(self.product_list, 1)

        pager = QHBoxLayout()
        pager.addStretch(1)
        self.prev_button = QPushButton("‹ Prev")
        self.prev_button.clicked.connect(
            lambda: self.product_list.set_page(self.product_list.page - 1)
        )
        self.page_label = QLabel("Page 1 / 1")
        self.next_button = QPushButton("Next ›")
        self.next_button.clicked.connect(
            lambda: self.product_list.set_page(self.product_list.page + 1)
        )
        pager.addWidget(self.prev_button)
        pager.addWidget(self.page_label)
        pager.addWidget(self.next_button)
        pager.addStretch(1)
        self.product_list.pageChanged.connect(self._on_page_changed)
        left.addLayout(pager)
        self._on_page_changed(1, 1)
        middle.addLayout(left, 1)

        self.selection_panel = SelectionPanel()
        middle.addWidget(self.selection_panel)

        root.addLayout(middle)

        bottom = QHBoxLayout()
        self.selected_label = QLabel("Selected products: 0")
        bottom.addWidget(self.selected_label)
        bottom.addStretch(1)

        self.clear_button = QPushButton("Clear selection")
        self.clear_button.clicked.connect(self._clear_selection)
        bottom.addWidget(self.clear_button)

        self.export_excel_button = QPushButton("Export Excel")
        self.export_excel_button.clicked.connect(self.export_to_excel)
        bottom.addWidget(self.export_excel_button)

        self.export_pdf_button = QPushButton("Export PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        bottom.addWidget(self.export_pdf_button)

        root.addLayout(bottom)

        self.product_list.totalSelectedChanged.connect(
            lambda n: self.selected_label.setText(f"Selected products: {n}")
        )
        self.product_list.selectionToggled.connect(
            lambda *_: self._refresh_selection_panel()
        )
        self.product_list.quantityEdited.connect(
            lambda *_: self._refresh_selection_panel()
        )

        self.setCentralWidget(central)
        self.statusBar().showMessage("Otvori PDF katalog za početak.")

    def _clear_selection(self) -> None:
        self.product_list.clear_selection()
        self._refresh_selection_panel()

    def _refresh_selection_panel(self) -> None:
        items = [
            (p.code, p.name, self.product_list.quantity_of(p.code))
            for p in self.product_list.selected_products()
        ]
        self.selection_panel.refresh(items)

    # ------------------------------------------------------------- actions

    def open_pdf(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF catalog", "", "PDF files (*.pdf)"
        )
        if not file_path:
            return
        self._start_parse(file_path)

    def _start_parse(self, pdf_path: str) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        self.open_button.setEnabled(False)
        self.statusBar().showMessage("Parsiranje u toku...")

        images_dir = str(cache_dir("images"))
        self._worker = ParseWorker(pdf_path, images_dir, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_parse_done)
        self._worker.failed.connect(self._on_parse_failed)

        self._progress = QProgressDialog("Loading catalog...", "", 0, 100, self)
        self._progress.setWindowTitle("Učitavanje kataloga")
        self._progress.setWindowModality(Qt.WindowModal)
        self._progress.setAutoClose(False)
        self._progress.setCancelButton(None)
        self._progress.show()

        self._worker.start()

    def _on_progress(self, page: int, total: int) -> None:
        self._progress.setLabelText(f"Loading catalog...  Page {page} / {total}")
        self._progress.setValue(100 * page // max(total, 1))

    def _on_parse_done(self, result: ParseResult) -> None:
        self._progress.close()
        self.open_button.setEnabled(True)
        self._products = result.products

        if not result.products:
            QMessageBox.warning(
                self,
                "Nema proizvoda",
                "Nijedan proizvod nije pronađen u ovom PDF-u.",
            )
            self.statusBar().showMessage("Otvori PDF katalog za početak.")
            return

        self.product_list.set_products(result.products)
        self._populate_categories(result)
        message = f"Loaded {len(result.products)} products."
        if result.warnings:
            message += f"  ({len(result.warnings)} upozorenja)"
        self.statusBar().showMessage(message)

        if result.warnings and len(result.warnings) <= 8:
            QMessageBox.information(
                self, "Upozorenja pri parsiranju", "\n".join(result.warnings)
            )

    def _on_parse_failed(self, error: str) -> None:
        self._progress.close()
        self.open_button.setEnabled(True)
        QMessageBox.critical(self, "Greška", f"Greška pri parsiranju PDF-a:\n{error}")
        self.statusBar().showMessage("Otvori PDF katalog za početak.")

    def _populate_categories(self, result: ParseResult) -> None:
        categories = sorted(
            set(c for c in result.category_counts if c), key=str.lower
        )
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem(CATEGORY_ALL)
        self.category_combo.addItems(categories)
        self.category_combo.blockSignals(False)

    def _apply_filter(self) -> None:
        self.product_list.refresh(
            search=self.search_edit.text(),
            category=self.category_combo.currentText(),
        )

    def _on_view_changed(self, index: int) -> None:
        self.product_list.set_view_mode(GRID if index == 0 else LIST)

    def _on_page_changed(self, page: int, total: int) -> None:
        self.page_label.setText(f"Page {page} / {total}")
        self.prev_button.setEnabled(page > 1)
        self.next_button.setEnabled(page < total)

    # --------------------------------------------------------------- export

    def export_to_excel(self) -> None:
        self._export("excel")

    def export_to_pdf(self) -> None:
        self._export("pdf")

    def _export(self, kind: str) -> None:
        selected = self.product_list.selected_products()
        if not selected:
            QMessageBox.warning(self, "Porudžbina", "Nijedan proizvod nije selektovan.")
            return

        quantities = {
            code: self.product_list.quantity_of(code) for code in
            (p.code for p in selected)
        }
        order, errors = build_order(selected, quantities)
        if errors:
            QMessageBox.warning(
                self, "Neispravna količina", "\n".join(errors[:12])
            )
            return
        if order.is_empty():
            QMessageBox.warning(self, "Porudžbina", "Nijedan proizvod nije selektovan.")
            return

        if kind == "excel":
            from app.export.excel_exporter import default_filename as name
            filter_str = "Excel fajl (*.xlsx)"
        else:
            from app.export.pdf_exporter import default_filename as name
            filter_str = "PDF fajl (*.pdf)"

        target, _ = QFileDialog.getSaveFileName(
            self, "Sačuvaj porudžbinu", name(), filter_str
        )
        if not target:
            return

        items = [(item.product.code, item.quantity) for item in order.items]
        try:
            if kind == "excel":
                export_excel(items, path=target)
            else:
                export_pdf(items, path=target)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            QMessageBox.critical(
                self, "Greška", f"Export nije uspeo:\n{exc}"
            )
            return

        QMessageBox.information(
            self, "Gotovo", f"Porudžbina sačuvana u:\n{target}"
        )


def run_app() -> None:
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    app.setOrganizationName("CatalogOrderManager")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())