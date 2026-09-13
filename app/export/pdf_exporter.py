"""PDF export (Phase 7): a simple PORUDŽBINA sheet, code + quantity only."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FONT_REGULAR = "CatalogSans"
FONT_BOLD = "CatalogSansBold"

_FONT_FAMILIES = [
    (
        "CatalogSans",
        "CatalogSansBold",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ),
    (
        "CatalogArial",
        "CatalogArialBold",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ),
]

_FALLBACK = ("Helvetica", "Helvetica-Bold")


def _register_font() -> None:
    """Register a regular+bold unicode TTF pair so Serbian diacritics render.

    A font is only usable when BOTH the regular and bold files exist, so the
    first complete pair on this machine wins; otherwise reportlab's built-in
    Helvetica names are used (no diacritics, but the export never crashes).
    """
    global FONT_REGULAR, FONT_BOLD
    if FONT_REGULAR in pdfmetrics.getRegisteredFontNames():
        return
    for name_r, name_b, regular_path, bold_path in _FONT_FAMILIES:
        if Path(regular_path).exists() and Path(bold_path).exists():
            pdfmetrics.registerFont(TTFont(name_r, regular_path))
            pdfmetrics.registerFont(TTFont(name_b, bold_path))
            FONT_REGULAR, FONT_BOLD = name_r, name_b
            return
    FONT_REGULAR, FONT_BOLD = _FALLBACK


def default_filename() -> str:
    return f"porudzbina_{datetime.date.today().isoformat()}.pdf"


def _serbian_date() -> str:
    return datetime.date.today().strftime("%d.%m.%Y.")


def export_pdf(items: Iterable[tuple[str, int]], path: str | Path | None = None) -> Path:
    """Export (code, quantity) pairs to a PDF file. Returns the written path."""
    _register_font()

    target = Path(path) if path else Path(default_filename())

    title_style = ParagraphStyle(
        "Title",
        fontName=FONT_BOLD,
        fontSize=20,
        leading=24,
        alignment=1,  # center
        spaceAfter=6,
    )
    date_style = ParagraphStyle(
        "Date",
        fontName=FONT_REGULAR,
        fontSize=11,
        leading=14,
        alignment=1,
        spaceAfter=12,
    )

    doc = SimpleDocTemplate(
        str(target),
        pagesize=A4,
        leftMargin=25 * mm,
        rightMargin=25 * mm,
        topMargin=25 * mm,
        bottomMargin=25 * mm,
    )

    story = [
        Paragraph("PORUDŽBINA", title_style),
        Paragraph(f"Datum: {_serbian_date()}", date_style),
        Spacer(1, 6 * mm),
    ]

    rows: list[list[str]] = [["Šifra", "Količina"]]
    for code, quantity in items:
        rows.append([str(code), str(quantity)])

    header_style = ParagraphStyle(
        "H", fontName=FONT_BOLD, fontSize=11, leading=13, alignment=1
    )
    cell_style = ParagraphStyle(
        "C", fontName=FONT_REGULAR, fontSize=11, leading=13, alignment=1
    )

    data = [
        [Paragraph("Šifra", header_style), Paragraph("Količina", header_style)],
    ]
    for code, quantity in rows[1:]:
        data.append([Paragraph(code, cell_style), Paragraph(quantity, cell_style)])

    table = Table(data, colWidths=[70 * mm, 50 * mm], hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.6, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return target