"""Build a two-page Pearson Press masthead and running-header styleboard."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs" / "pearson-press-masthead-styleboard-v1.pdf"
FONT_DIR = Path(r"C:\Windows\Fonts")
PAGE_W, PAGE_H = letter
MARGIN = 38


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("PP-Engravers", str(FONT_DIR / "ENGR.TTF")))
    pdfmetrics.registerFont(TTFont("PP-BodoniPoster", str(FONT_DIR / "BOD_PSTC.TTF")))
    pdfmetrics.registerFont(TTFont("PP-RockwellExtra", str(FONT_DIR / "ROCKEB.TTF")))
    pdfmetrics.registerFont(TTFont("PP-PerpetuaTitling", str(FONT_DIR / "PERTIBD.TTF")))


def fit_size(text: str, font: str, target: float, maximum: float) -> float:
    size = maximum
    while size > 10 and pdfmetrics.stringWidth(text, font, size) > target:
        size -= 0.25
    return size


def rule(c: canvas.Canvas, x1: float, y: float, x2: float, width: float = 0.5) -> None:
    c.setStrokeGray(0)
    c.setLineWidth(width)
    c.line(x1, y, x2, y)


def study_header(c: canvas.Canvas, page: int) -> None:
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(MARGIN, PAGE_H - 34, "PEARSON PRESS / MASTHEAD STUDY")
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 34, f"SHEET {page} OF 2")
    rule(c, MARGIN, PAGE_H - 43, PAGE_W - MARGIN, 0.35)


def option_label(c: canvas.Canvas, letter: str, name: str, y: float, descriptor: str) -> None:
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(MARGIN, y, f"OPTION {letter}  /  {name.upper()}")
    c.setFont("Helvetica", 6.5)
    c.setFillGray(0.45)
    c.drawRightString(PAGE_W - MARGIN, y, descriptor.upper())


def common_date_row(c: canvas.Canvas, y: float, *, issue_style: str = "plain") -> None:
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 6.4)
    c.drawString(MARGIN, y, "TUESDAY, OCTOBER 13, 2026")
    c.drawCentredString(PAGE_W / 2, y, "THE PERSONAL MORNING EDITION")
    if issue_style == "boxed":
        c.rect(PAGE_W - MARGIN - 58, y - 4, 58, 13, fill=0, stroke=1)
        c.drawCentredString(PAGE_W - MARGIN - 29, y, "NO. 001")
    else:
        c.drawRightString(PAGE_W - MARGIN, y, "NO. 001")


def running_head(c: canvas.Canvas, y: float, brand_font: str, section: str,
                 page_number: str, *, inverted: bool = False) -> None:
    if inverted:
        c.setFillGray(0)
        c.rect(MARGIN, y - 6, PAGE_W - 2 * MARGIN, 25, fill=1, stroke=0)
        c.setFillGray(1)
    else:
        c.setFillGray(0)
        rule(c, MARGIN, y + 19, PAGE_W - MARGIN, 0.8)
    c.setFont(brand_font, 9)
    c.drawString(MARGIN + (8 if inverted else 0), y + 2, "PEARSON PRESS")
    c.setFont("Helvetica-Bold", 7)
    c.drawRightString(PAGE_W - MARGIN - (8 if inverted else 0), y + 3, f"{section}   /   {page_number}")
    c.setFillGray(0)


def tracked_center(c: canvas.Canvas, text: str, y: float, font: str, size: float,
                   tracking: float) -> None:
    widths = [pdfmetrics.stringWidth(char, font, size) for char in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (PAGE_W - total) / 2
    c.setFont(font, size)
    for char, width in zip(text, widths):
        c.drawString(x, y, char)
        x += width + tracking


def option_a(c: canvas.Canvas, top: float) -> None:
    option_label(c, "A", "The Engraved Standard", top, "Formal / premium / archival")
    y = top - 84
    c.setFillGray(0)
    size = fit_size("PEARSON PRESS", "PP-Engravers", PAGE_W - 2 * MARGIN, 42)
    c.setFont("PP-Engravers", size)
    c.drawCentredString(PAGE_W / 2, y, "PEARSON PRESS")
    c.setFont("Helvetica", 6.3)
    c.drawCentredString(PAGE_W / 2, y - 18, "ESTABLISHED FOR THE FIRST EDITION  /  READ SLOWLY")
    rule(c, MARGIN, y - 29, PAGE_W - MARGIN, 1.15)
    common_date_row(c, y - 43)
    rule(c, MARGIN, y - 51, PAGE_W - MARGIN, 0.35)
    running_head(c, y - 91, "PP-Engravers", "THE SCOREBOARD", "02")


def option_b(c: canvas.Canvas, top: float) -> None:
    option_label(c, "B", "The Editorial Tower", top, "Dramatic / compact / traditional")
    y = top - 88
    c.setFillGray(0)
    size = fit_size("PEARSON PRESS", "PP-BodoniPoster", PAGE_W - 2 * MARGIN, 58)
    c.setFont("PP-BodoniPoster", size)
    c.drawCentredString(PAGE_W / 2, y, "PEARSON PRESS")
    rule(c, MARGIN, y + 52, PAGE_W - MARGIN, 0.35)
    rule(c, MARGIN, y - 12, PAGE_W - MARGIN, 2.0)
    common_date_row(c, y - 29, issue_style="boxed")
    running_head(c, y - 78, "PP-BodoniPoster", "STANDINGS & TRENDS", "04", inverted=True)


def option_c(c: canvas.Canvas, top: float) -> None:
    option_label(c, "C", "The American Block", top, "Direct / confident / sports-forward")
    y = top - 97
    c.setFillGray(0)
    c.rect(MARGIN, y - 12, PAGE_W - 2 * MARGIN, 66, fill=1, stroke=0)
    c.setFillGray(1)
    size = fit_size("PEARSON PRESS", "PP-RockwellExtra", PAGE_W - 2 * MARGIN - 34, 40)
    c.setFont("PP-RockwellExtra", size)
    c.drawCentredString(PAGE_W / 2, y + 6, "PEARSON PRESS")
    c.setFillGray(0)
    common_date_row(c, y - 31)
    rule(c, MARGIN, y - 42, PAGE_W - MARGIN, 2.4)
    running_head(c, y - 83, "PP-RockwellExtra", "FEATURED BOX SCORE", "03")


def option_d(c: canvas.Canvas, top: float) -> None:
    option_label(c, "D", "The Pearson Signature", top, "Distinctive / restrained / ownable")
    y = top - 87
    c.setFillGray(0)
    c.circle(MARGIN + 30, y + 12, 26, fill=0, stroke=1)
    c.setFont("PP-PerpetuaTitling", 19)
    c.drawCentredString(MARGIN + 30, y + 6, "PP")
    tracked_center(c, "PEARSON PRESS", y, "PP-PerpetuaTitling", 26, 1.8)
    c.setFont("Helvetica", 6.2)
    c.drawCentredString(PAGE_W / 2 + 18, y - 17, "A NEWSPAPER BUILT AROUND ONE READER")
    rule(c, MARGIN, y - 29, PAGE_W - MARGIN, 0.4)
    common_date_row(c, y - 44)
    rule(c, MARGIN, y - 53, PAGE_W - MARGIN, 1.1)
    running_head(c, y - 94, "PP-PerpetuaTitling", "THE NEWS DESK", "05")


def footer(c: canvas.Canvas, page: int) -> None:
    c.setFillGray(0.5)
    c.setFont("Helvetica", 6)
    c.drawString(MARGIN, 25, "TYPE DIRECTIONS FOR DISCUSSION - NOT FINAL LICENSED BRAND FONTS")
    c.setFillGray(0)
    c.setFont("Helvetica-Bold", 7)
    c.drawRightString(PAGE_W - MARGIN, 25, f"0{page}")


def build() -> Path:
    register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(OUTPUT), pagesize=letter, pageCompression=1)
    pdf.setTitle("Pearson Press Masthead Styleboard V1")
    pdf.setAuthor("Pearson Press")
    pdf.setSubject("Four black-and-white masthead and running-header directions")

    study_header(pdf, 1)
    option_a(pdf, 704)
    option_b(pdf, 371)
    footer(pdf, 1)
    pdf.showPage()

    study_header(pdf, 2)
    option_c(pdf, 704)
    option_d(pdf, 371)
    footer(pdf, 2)
    pdf.showPage()

    pdf.save()
    return OUTPUT


if __name__ == "__main__":
    print(build())
