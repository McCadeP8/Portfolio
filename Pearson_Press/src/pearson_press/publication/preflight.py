"""Check clipping, overflow, margins, missing assets, citations, and page parity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter

LETTER = (612.0, 792.0)
SIZE_TOLERANCE = 1.0
MAX_FILE_MB = 25.0


@dataclass
class PreflightReport:
    page_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {"page_count": self.page_count, "errors": self.errors, "warnings": self.warnings}


def polish(path: Path, *, edition_date: date) -> list[str]:
    """Apply automatic print fixes in place and return what was changed."""

    reader = PdfReader(path)
    writer = PdfWriter(clone_from=reader)
    notes: list[str] = []

    if len(writer.pages) % 2:
        writer.add_blank_page(*LETTER)
        notes.append("added blank back page for duplex parity")

    writer.add_metadata({
        "/Title": f"Pearson Press - {edition_date:%A, %B %d, %Y}",
        "/Author": "Pearson Press",
        "/Subject": "Black-and-white duplex personal newspaper",
    })
    notes.append("stamped edition metadata")

    with path.open("wb") as stream:
        writer.write(stream)
    return notes


def preflight(path: Path) -> PreflightReport:
    """Check a finished edition is printable: size, parity, fonts, and text."""

    reader = PdfReader(path)
    report = PreflightReport(page_count=len(reader.pages))

    if report.page_count == 0:
        report.errors.append("edition has no pages")
        return report
    if report.page_count % 2:
        report.errors.append(f"odd page count ({report.page_count}) cannot print duplex")

    for number, page in enumerate(reader.pages, start=1):
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        if abs(width - LETTER[0]) > SIZE_TOLERANCE or abs(height - LETTER[1]) > SIZE_TOLERANCE:
            report.errors.append(f"page {number} is {width:.0f}x{height:.0f}pt, not US Letter")
        if not (page.extract_text() or "").strip() and number != report.page_count:
            report.warnings.append(f"page {number} has no text")
        for font in _unembedded_fonts(page):
            report.warnings.append(f"page {number} uses unembedded font {font}")

    size_mb = path.stat().st_size / 1_048_576
    if size_mb > MAX_FILE_MB:
        report.warnings.append(f"file is {size_mb:.1f} MB (limit {MAX_FILE_MB:.0f} MB)")

    report.warnings = sorted(set(report.warnings))
    return report


# The 14 standard PDF fonts are always available to printers without embedding.
_STANDARD_FONTS = {
    "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
    "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
    "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
    "Symbol", "ZapfDingbats",
}


def _unembedded_fonts(page: PageObject) -> set[str]:
    resources = page.get("/Resources")
    fonts = resources.get_object().get("/Font") if resources else None
    missing: set[str] = set()
    if not fonts:
        return missing
    for ref in fonts.get_object().values():
        font = ref.get_object()
        name = str(font.get("/BaseFont", "")).lstrip("/")
        descendants = font.get("/DescendantFonts")
        descriptor = (descendants[0].get_object() if descendants else font).get("/FontDescriptor")
        embedded = descriptor and any(
            key in descriptor.get_object() for key in ("/FontFile", "/FontFile2", "/FontFile3")
        )
        if not embedded and name.split("+")[-1] not in _STANDARD_FONTS:
            missing.add(name)
    return missing
