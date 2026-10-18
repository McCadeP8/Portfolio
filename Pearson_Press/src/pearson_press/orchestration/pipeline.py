"""Collect, write, design, preflight, archive, and print one edition.

Every stage is reported on its own, so a failure says exactly where the paper
broke. Data and stories are cached per edition date: rebuilding the same date
replays the same facts and never pays for the writing twice.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pearson_press.edition.build import compose, edition_dir, gather, ledger, write
from pearson_press.edition.model import EditionContent
from pearson_press.publication.preflight import PreflightReport, polish, preflight


@dataclass
class StageResult:
    name: str
    ok: bool
    seconds: float
    detail: str = ""


@dataclass
class RunReport:
    edition_date: str
    stages: list[StageResult] = field(default_factory=list)
    output: Path | None = None
    preflight: PreflightReport | None = None
    warnings: list[str] = field(default_factory=list)
    cost_usd: float = 0.0

    @property
    def ok(self) -> bool:
        return all(stage.ok for stage in self.stages)


def _stage(report: RunReport, name: str, log: Callable[[str], None], action: Callable[[], str]) -> bool:
    log(f"[{len(report.stages) + 1}] {name} ...")
    started = time.perf_counter()
    try:
        detail = action()
        ok = True
    except Exception as exc:  # noqa: BLE001 - every failure is reported, not raised
        detail = f"{type(exc).__name__}: {exc}"
        ok = False
    result = StageResult(name, ok, time.perf_counter() - started, detail)
    report.stages.append(result)
    log(f"    {'OK  ' if ok else 'FAIL'} ({result.seconds:.1f}s) {detail}")
    return ok


def run(
    *,
    edition_date: date | None = None,
    refresh: bool = False,
    send_to_printer: bool = False,
    print_pages: str = "",
    send_email: bool = False,
    log: Callable[[str], None] = print,
) -> RunReport:
    """Run LOAD -> WRITE -> FORMAT -> POLISH -> SAVE (-> PRINT) and return a report."""

    edition_date = edition_date or date.today()
    report = RunReport(edition_date.isoformat())
    state: dict[str, object] = {}

    def load() -> str:
        content = gather(edition_date, refresh=refresh, log=lambda line: log(f"   {line}"))
        state["content"] = content
        report.warnings.extend(content.warnings)
        boxes = sum(len(sport.boxes) for sport in content.sports)
        return f"{len(content.sports)} sports in season, {boxes} box scores"

    def write_stage() -> str:
        content: EditionContent = state["content"]  # type: ignore[assignment]
        state["written"] = written = write(content, log=lambda line: log(f"   {line}"))
        report.cost_usd = ledger().edition_total(edition_date)
        if not (edition_dir(edition_date) / "stories.json").exists():
            return f"{len(written)} box-score briefs (Claude writing unavailable)"
        return f"{len(written)} stories, ${report.cost_usd:.2f} spent on this edition"

    def format_stage() -> str:
        output, pages = compose(state["content"], state["written"])  # type: ignore[arg-type]
        state["output"] = output
        report = getattr(state["content"], "fill_report", [])
        for column in report:
            if column.before > 12:
                log(f"   fill: {column.line()}")
        short = [c for c in report if c.after > 2.0]
        if short:
            report_warnings = [f"column short of the bottom line: {c.line()}" for c in short]
            report.__class__  # keep linters quiet
            for line in report_warnings:
                log(f"   warning: {line}")
        return f"{pages} pages laid out" + (f", {len(short)} columns short" if short else ", every column full")

    def polish_and_check() -> str:
        output: Path = state["output"]  # type: ignore[assignment]
        notes = polish(output, edition_date=edition_date)
        report.preflight = preflight(output)
        if not report.preflight.ok:
            raise RuntimeError("; ".join(report.preflight.errors))
        return f"{report.preflight.page_count} pages, {len(notes)} fixes, {len(report.preflight.warnings)} warnings"

    def save() -> str:
        report.output = state["output"]  # type: ignore[assignment]
        (edition_dir(edition_date) / "build-report.json").write_text(json.dumps(_as_dict(report), indent=2))
        return str(report.output)

    def tidy_stage() -> str:
        from pearson_press.publication.retention import tidy

        return tidy(edition_dir(edition_date).parents[2], date.today())

    def print_edition() -> str:
        from pearson_press.edition.build import load_profile
        from pearson_press.publication.printer import print_pdf

        return print_pdf(state["output"], load_profile().get("printer"), print_pages)  # type: ignore[arg-type]

    def email_edition() -> str:
        from pearson_press.edition import text
        from pearson_press.publication.mailer import email_configured, email_pdf

        if not email_configured():
            return "skipped: email not set up in .env yet"
        return email_pdf(state["output"], f"Pearson Press - {text.long_date(edition_date)}")  # type: ignore[arg-type]

    _stage(report, "LOAD live data", log, load) \
        and _stage(report, "WRITE stories", log, write_stage) \
        and _stage(report, "FORMAT newspaper", log, format_stage) \
        and _stage(report, "POLISH + preflight", log, polish_and_check) \
        and _stage(report, "SAVE edition", log, save)         and _stage(report, "TIDY old data", log, tidy_stage) \
        and (not send_to_printer or _stage(report, "PRINT", log, print_edition)) \
        and send_email and _stage(report, "EMAIL", log, email_edition)

    for warning in report.warnings + (report.preflight.warnings if report.preflight else []):
        log(f"    warning: {warning}")
    return report


def _as_dict(report: RunReport) -> dict:
    return {
        "edition_date": report.edition_date,
        "ok": report.ok,
        "output": str(report.output) if report.output else None,
        "stages": [vars(stage) for stage in report.stages],
        "preflight": report.preflight.as_dict() if report.preflight else None,
        "warnings": report.warnings,
        "writing_cost_usd": round(report.cost_usd, 4),
    }
