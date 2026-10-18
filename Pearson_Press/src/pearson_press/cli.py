"""Command-line interface for collecting, building, checking, and printing editions."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date


def main(argv: list[str] | None = None) -> None:
    """Run the Pearson Press command-line interface."""

    parser = argparse.ArgumentParser(prog="pearson-press")
    commands = parser.add_subparsers(dest="command", required=True)

    test = commands.add_parser("test", help="Build the whole newspaper start to finish.")
    test.add_argument("--date", type=date.fromisoformat, help="Edition date (YYYY-MM-DD).")
    test.add_argument("--print", dest="send_to_printer", action="store_true",
                      help="Print the finished edition (two-sided, black and white).")
    test.add_argument("--pages", default="",
                      help="With --print, only these pages (e.g. 1 or 1-2) - handy for test prints.")
    test.add_argument("--email", action="store_true", help="Email the finished PDF (set up in .env).")
    test.add_argument("--no-open", action="store_true", help="Do not open the finished PDF.")
    test.add_argument("--refresh", action="store_true", help="Re-download ESPN data instead of using the cache.")

    commands.add_parser("specimen", help="Build the June 31 specimen: one labeled example of everything.")

    build = commands.add_parser("build", help="Build an edition (currently same as test).")
    build.add_argument("--edition", default="daily")
    build.add_argument("--date", type=date.fromisoformat)

    args = parser.parse_args(argv)

    if args.command == "specimen":
        from pearson_press.edition.specimen import build_specimen

        print("PEARSON PRESS - June 31 specimen (never printed)\n")
        output = build_specimen()
        print(f"\nSPECIMEN -> {output}")
        if os.name == "nt":
            os.startfile(output)
        return

    from pearson_press.orchestration.pipeline import run

    print("PEARSON PRESS - full build\n")
    report = run(
        edition_date=args.date,
        refresh=getattr(args, "refresh", False),
        send_to_printer=getattr(args, "send_to_printer", False),
        print_pages=getattr(args, "pages", ""),
        send_email=getattr(args, "email", False),
    )

    if not report.ok:
        print("\nBUILD FAILED - see the stage marked FAIL above.")
        sys.exit(1)
    print(f"\nBUILD PASSED -> {report.output}")
    if args.command == "test" and not args.no_open and report.output and os.name == "nt":
        os.startfile(report.output)
