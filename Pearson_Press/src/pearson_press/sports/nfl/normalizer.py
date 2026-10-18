"""Turn an ESPN football game summary into the simple box-score model.

Used by both the NFL and college football sections.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from pearson_press.providers import espn_parse as e
from pearson_press.sports.nfl.components import NFLPlayerLine, NFLSimpleBoxScore, NFLTeamBox

# "T.Bass 49 yard field goal is GOOD" / "is No Good" / "is BLOCKED"
_FIELD_GOAL = re.compile(r"([A-Z][\w.' -]*?)\s+(\d+)\s+yard field goal is\s+(GOOD|No Good|BLOCKED)", re.IGNORECASE)
_RETURN_TD = ("Interception Return", "Fumble Return", "Kickoff Return", "Punt Return", "Blocked", "Fumble Recovery")


def _group(side: e.Side, name: str) -> tuple[list[str], list[dict[str, Any]]]:
    for group in e.stat_groups(side):
        if group.get("name") == name:
            return group["labels"], group["athletes"]
    return [], []


def _lines(side: e.Side, name: str, columns: tuple[str, ...]) -> tuple[NFLPlayerLine, ...]:
    labels, athletes = _group(side, name)
    lines = []
    for athlete in athletes:
        stats = e.row(labels, athlete["stats"])
        lines.append(NFLPlayerLine(
            athlete["athlete"]["displayName"],
            tuple(stats.get(column, "0") for column in columns),
        ))
    return tuple(lines)


def _notes(side: e.Side, name: str, render) -> tuple[str, ...]:
    labels, athletes = _group(side, name)
    notes = []
    for athlete in athletes:
        text = render(e.surname(athlete["athlete"]["displayName"]), e.row(labels, athlete["stats"]))
        if text:
            notes.append(text)
    return tuple(notes)


def _sack(name: str, stats: dict[str, str]) -> str:
    sacks = float(stats.get("SACKS", "0") or 0)
    if not sacks:
        return ""
    return name if sacks == 1 else f"{name} {sacks:g}"


def _returns(name: str, stats: dict[str, str]) -> str:
    return f"{name} {stats.get('NO', stats.get('INT', '0'))}-{stats.get('YDS', '0')}"


def _field_goals(summary: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    """Kicker distances per team abbreviation, split into made and missed."""

    kicks: dict[str, dict[str, list[str]]] = defaultdict(lambda: {"made": [], "missed": []})
    for drive in summary.get("drives", {}).get("previous", []):
        team = drive.get("team", {}).get("abbreviation", "")
        for play in drive.get("plays", []):
            match = _FIELD_GOAL.search(play.get("text", ""))
            if match:
                kicker = match.group(1).split(".")[-1].strip()
                outcome = "made" if match.group(3).upper() == "GOOD" else "missed"
                kicks[team][outcome].append((kicker, match.group(2)))
    return {
        team: {outcome: _by_kicker(entries) for outcome, entries in outcomes.items()}
        for team, outcomes in kicks.items()
    }


def _by_kicker(entries: list[tuple[str, str]]) -> list[str]:
    """[("Bass","49"),("Bass","23")] -> ["Bass 49, 23"] in kick order."""

    grouped: dict[str, list[str]] = {}
    for kicker, yards in entries:
        grouped.setdefault(kicker, []).append(yards)
    return [f"{kicker} {', '.join(yards)}" for kicker, yards in grouped.items()]


def _other_touchdowns(summary: dict[str, Any], team_id: str) -> tuple[str, ...]:
    touchdowns = []
    for play in summary.get("scoringPlays", []):
        kind = play.get("type", {}).get("text", "")
        if str(play.get("team", {}).get("id")) == team_id and any(tag in kind for tag in _RETURN_TD):
            touchdowns.append(play.get("text", "").split("(")[0].strip())
    return tuple(touchdowns)


def _slash(value: str) -> str:
    return value.replace("-", "/")


def _team(side: e.Side, summary: dict[str, Any], kicks: dict[str, dict[str, list[str]]], *, ranked: bool) -> NFLTeamBox:
    team_kicks = kicks.get(side.abbreviation, {"made": [], "missed": []})
    return NFLTeamBox(
        location=side.location,
        nickname=side.nickname,
        abbreviation=side.abbreviation,
        score=side.score,
        record=side.record,
        quarter_scores=tuple(side.linescores),
        passing=_lines(side, "passing", ("C/ATT", "YDS", "TD", "INT")),
        rushing=_lines(side, "rushing", ("CAR", "YDS", "TD", "LONG")),
        receiving=_lines(side, "receiving", ("REC", "YDS", "TD", "TGTS", "LONG")),
        kicking=_lines(side, "kicking", ("FG", "XP", "PTS")),
        sacks=_notes(side, "defensive", _sack),
        interceptions=_notes(side, "interceptions", _returns),
        kick_returns=_notes(side, "kickReturns", _returns),
        punt_returns=_notes(side, "puntReturns", _returns),
        other_touchdowns=_other_touchdowns(summary, side.team_id),
        team_stats={
            "first_downs": e.team_stat(side, "firstDowns"),
            "plays": e.team_stat(side, "totalOffensivePlays"),
            "drives": e.team_stat(side, "totalDrives"),
            "sacks": e.team_stat(side, "sacksYardsLost", default="0-0"),
            "red_zone": _slash(e.team_stat(side, "redZoneAttempts", default="0-0")),
            "third_down": _slash(e.team_stat(side, "thirdDownEff", default="0-0")),
            "fourth_down": _slash(e.team_stat(side, "fourthDownEff", default="0-0")),
            "penalties": e.team_stat(side, "totalPenaltiesYards", default="0-0"),
            "turnovers": e.team_stat(side, "turnovers"),
            "fumbles_lost": e.team_stat(side, "fumblesLost"),
            "possession": e.team_stat(side, "possessionTime", default="-"),
        },
        display_name=side.location if ranked else None,
        rank=side.rank if ranked else None,
        field_goals_made=tuple(team_kicks["made"]),
        field_goals_missed=tuple(team_kicks["missed"]),
    )


def normalize(summary: dict[str, Any], *, college: bool = False) -> NFLSimpleBoxScore:
    away, home = e.sides(summary)
    kicks = _field_goals(summary)
    venue, city, state = e.venue(summary)
    return NFLSimpleBoxScore(
        away=_team(away, summary, kicks, ranked=college),
        home=_team(home, summary, kicks, ranked=college),
        venue=venue,
        city=city,
        state=state,
        officials=e.officials(summary),
        attendance=e.attendance(summary),
    )
