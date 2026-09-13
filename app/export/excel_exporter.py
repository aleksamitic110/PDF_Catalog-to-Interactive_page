"""Excel export (Phase 6): CODE + QUANTITY only, no prices, names or images.

When per-item unit prices are supplied a bold "UKUPNO (približno)" row is
appended so the shopkeeper can tell the customer roughly how much the whole
order costs.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Iterable

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from app.models.product import format_price

HEADERS = ("Šifra", "Količina")
TOTAL_LABEL = "UKUPNO (približno), RSD"


def default_filename() -> str:
    return f"porudzbina_{datetime.date.today().isoformat()}.xlsx"


def export_excel(
    items: Iterable[tuple[str, int] | tuple[str, int, float | None]],
    path: str | Path | None = None,
) -> Path:
    """Export (code, quantity[, unit_price]) rows to an .xlsx file.

    Returns the path that was written.
    """
    target = Path(path) if path else Path(default_filename())
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Porudžbina"

    sheet.cell(row=1, column=1, value=HEADERS[0]).font = Font(bold=True)
    sheet.cell(row=1, column=2, value=HEADERS[1]).font = Font(bold=True)

    total = 0.0
    total_known = False
    next_row = 2
    for row in items:
        code, quantity = row[0], row[1]
        unit_price = row[2] if len(row) > 2 else None
        sheet.cell(row=next_row, column=1, value=str(code))
        sheet.cell(row=next_row, column=2, value=int(quantity))
        if unit_price is not None:
            total += float(unit_price) * int(quantity)
            total_known = True
        next_row += 1

    if total_known:
        label = sheet.cell(row=next_row, column=1, value=TOTAL_LABEL)
        label.font = Font(bold=True)
        total_cell = sheet.cell(row=next_row, column=2, value=round(total, 2))
        total_cell.font = Font(bold=True)
        total_cell.number_format = "#,##0.00"
        sheet.cell(row=next_row, column=2).fill = PatternFill(
            "solid", fgColor="FFE9C7"
        )

    sheet.column_dimensions["A"].width = 22
    sheet.column_dimensions["B"].width = 14
    workbook.save(str(target))
    return target