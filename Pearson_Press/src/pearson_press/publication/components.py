"""Reusable masthead, article, brief, score, table, chart, and footer components."""

from __future__ import annotations

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas


def draw_inside_page_folio(
    pdf: Canvas,
    *,
    page_width: float,
    margin: float,
    date_label: str,
    page_number: int,
    publication_name: str = "PEARSON PRESS",
    edition_name: str = "THE PERSONAL MORNING EDITION",
    masthead_font: str = "PP-Engravers",
) -> float:
    """Draw permanent inside-page furniture and return the divider-rule y."""

    registered = pdfmetrics.getRegisteredFontNames()
    wordmark_font = masthead_font if masthead_font in registered else "Times-Bold"
    baseline = 774.0

    pdf.setFillGray(0)
    pdf.setFont(wordmark_font, 10.5)
    pdf.drawString(margin, baseline, publication_name)

    pdf.setFont("Helvetica-Bold", 5.6)
    pdf.drawCentredString(page_width / 2, baseline + 0.8, edition_name)
    pdf.drawRightString(
        page_width - margin,
        baseline + 0.8,
        f"{date_label}  /  PAGE {page_number}",
    )

    rule_y = 762.0
    pdf.setLineWidth(0.55)
    pdf.line(margin, rule_y, page_width - margin, rule_y)
    return rule_y
