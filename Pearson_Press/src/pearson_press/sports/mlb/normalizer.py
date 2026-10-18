"""Turn an ESPN MLB game summary into the simple box-score model."""

from __future__ import annotations

import re
from typing import Any

from pearson_press.providers import espn_parse as e
from pearson_press.sports.mlb.components import (
    MLBBatterLine,
    MLBPitcherLine,
    MLBSimpleBoxScore,
    MLBTeamBox,
)

# "Ramírez (2, 2nd base off Peralta/Hicks)" -> "Ramírez (2)"
_PAREN_DETAIL = re.compile(r"\((\d+)[^)]*\)")
# "Ramírez, Jo (1, fielding)" -> ESPN adds a first-name hint before the paren.
_NAME_HINT = re.compile(r",\s*[A-Z][a-z]{0,3}\s*\(")


def _details(side: e.Side) -> dict[str, str]:
    found: dict[str, str] = {}
    for group in side.team_box.get("details", []):
        for stat in group.get("stats", []):
            found.setdefault(stat.get("abbreviation", ""), stat.get("displayValue", ""))
    return found


def _listed(value: str) -> tuple[str, ...]:
    """Split ESPN's '; '-separated detail text into tidy 'Name (n)' entries."""

    if not value:
        return ()
    cleaned = _NAME_HINT.sub(" (", value)
    cleaned = _PAREN_DETAIL.sub(r"(\1)", cleaned).rstrip(".")
    return tuple(part.strip().rstrip(".") for part in cleaned.split(";") if part.strip())


def _batting(side: e.Side) -> tuple[tuple[MLBBatterLine, ...], tuple[str, ...]]:
    group = next(g for g in e.stat_groups(side) if g.get("type") == "batting")
    labels = group["labels"]
    batters = []
    for athlete in group["athletes"]:
        if not athlete.get("stats"):
            continue
        stats = e.row(labels, athlete["stats"])
        batters.append(MLBBatterLine(
            name=athlete["athlete"]["displayName"],
            ab=stats.get("AB", "0"),
            runs=stats.get("R", "0"),
            hits=stats.get("H", "0"),
            rbi=stats.get("RBI", "0"),
            walks=stats.get("BB", "0"),
            strikeouts=stats.get("K", "0"),
            substitute=not athlete.get("starter", False),
        ))
    totals = e.row(labels, group.get("totals", []))
    return tuple(batters), tuple(totals.get(key, "0") for key in ("AB", "R", "H", "RBI", "BB", "K"))


def _pitching(side: e.Side) -> tuple[MLBPitcherLine, ...]:
    group = next(g for g in e.stat_groups(side) if g.get("type") == "pitching")
    labels = group["labels"]
    pitchers = []
    for athlete in group["athletes"]:
        stats = e.row(labels, athlete["stats"])
        decision = next(
            (note["text"] for note in athlete.get("notes", []) if note.get("type") == "pitchingDecision"),
            "",
        )
        pitchers.append(MLBPitcherLine(
            name=athlete["athlete"]["displayName"],
            innings=stats.get("IP", "0.0"),
            hits=stats.get("H", "0"),
            runs=stats.get("R", "0"),
            earned_runs=stats.get("ER", "0"),
            walks=stats.get("BB", "0"),
            strikeouts=stats.get("K", "0"),
            pitches_strikes=stats.get("PC-ST", ""),
            decision=decision,
        ))
    return tuple(pitchers)


def _team(side: e.Side) -> MLBTeamBox:
    batters, totals = _batting(side)
    details = _details(side)
    innings = tuple(item.get("displayValue", "0") for item in side.header.get("linescores", []))
    double_plays = e.to_int((details.get("DP") or "0").split(" ")[0])
    return MLBTeamBox(
        location=side.location,
        nickname=side.nickname,
        abbreviation=side.abbreviation,
        score=side.score,
        record=side.record,
        innings=innings,
        hits=e.to_int(side.header.get("hits")),
        errors=e.to_int(side.header.get("errors")),
        batters=batters,
        batting_totals=totals,  # type: ignore[arg-type]
        doubles=_listed(details.get("2B", "")),
        triples=_listed(details.get("3B", "")),
        home_runs=_listed(details.get("HR", "")),
        stolen_bases=_listed(details.get("SB", "")),
        error_players=_listed(details.get("E", "")),
        pitchers=_pitching(side),
        lob=e.to_int(details.get("Team LOB") or e.team_stat(side, "LOB")),
        double_plays=double_plays,
    )


def normalize(summary: dict[str, Any]) -> MLBSimpleBoxScore:
    away, home = e.sides(summary)
    venue, city, state = e.venue(summary)
    return MLBSimpleBoxScore(
        away=_team(away),
        home=_team(home),
        venue=venue,
        city=city,
        state=state,
        umpires=e.officials(summary),
        attendance=e.attendance(summary),
    )


def game_note(summary: dict[str, Any]) -> str:
    """ESPN's postseason label, e.g. 'ALCS - Game 2'."""

    note = summary.get("header", {}).get("gameNote")
    if note:
        return note
    notes = summary.get("notes") or []
    return notes[0].get("headline", "") if notes and isinstance(notes[0], dict) else ""
