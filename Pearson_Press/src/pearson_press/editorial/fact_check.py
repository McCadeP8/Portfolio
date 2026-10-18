"""Every number printed must appear in the data the story was written from.

Stories are written in self-contained paragraphs, most important first, so a
paragraph with an unverifiable number is dropped rather than repaired. A
dropped number costs a sentence; a wrong number costs the paper's credibility.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def numbers_in(value: Any) -> set[str]:
    """All digit runs in a fact sheet (JSON-encoded), with leading zeros normalized."""

    found = set()
    for token in _NUMBER.findall(json.dumps(value)):
        found.add(token)
        found.add(token.lstrip("0") or "0")
        if "." in token:  # ".821" in the data allows "821"; "4.5" allows "4" and "5"
            found.update(part.lstrip("0") or "0" for part in token.split("."))
    return found


@dataclass
class CheckResult:
    paragraphs: tuple[str, ...]
    dropped: list[str]


def check_story(paragraphs: tuple[str, ...], allowed: set[str] | None, edition_date: date) -> CheckResult:
    if allowed is None:  # web-researched stories: numbers come from cited reporting, not only our data
        return CheckResult(tuple(paragraphs), [])
    allowed = allowed | {str(edition_date.day), str(edition_date.year), str(edition_date.month)}
    kept, dropped = [], []
    for paragraph in paragraphs:
        unknown = [n for n in _NUMBER.findall(paragraph) if (n.lstrip("0") or "0") not in allowed and n not in allowed]
        (dropped if unknown else kept).append(paragraph)
    return CheckResult(tuple(kept), dropped)
