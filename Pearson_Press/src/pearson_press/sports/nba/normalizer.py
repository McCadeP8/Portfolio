"""Turn an ESPN basketball game summary into the simple box-score model.

Used by both the NBA and men's college basketball sections.
"""

from __future__ import annotations

from typing import Any

from pearson_press.providers import espn_parse as e
from pearson_press.sports.nba.components import PlayerLine, SimpleBoxScore, TeamBox


def _player_lines(side: e.Side) -> tuple[tuple[PlayerLine, ...], PlayerLine]:
    group = e.stat_groups(side)[0]
    labels = group["labels"]
    players = []
    for athlete in group["athletes"]:
        if athlete.get("didNotPlay") or not athlete.get("stats"):
            continue
        players.append(_line(athlete["athlete"]["displayName"], e.row(labels, athlete["stats"])))
    return tuple(players), _line("TOTAL", e.row(labels, group.get("totals", [])))


def _line(name: str, stats: dict[str, str]) -> PlayerLine:
    return PlayerLine(
        name=name,
        fg=stats.get("FG", "0-0"),
        three_pt=stats.get("3PT", "0-0"),
        points=e.to_int(stats.get("PTS")),
        rebounds=e.to_int(stats.get("REB")),
        assists=e.to_int(stats.get("AST")),
        steals=e.to_int(stats.get("STL")),
        blocks=e.to_int(stats.get("BLK")),
        free_throws=stats.get("FT", "0-0"),
        turnovers=e.to_int(stats.get("TO")),
    )


def _team(side: e.Side, *, ranked: bool) -> TeamBox:
    players, totals = _player_lines(side)
    return TeamBox(
        location=side.location,
        nickname=side.nickname,
        abbreviation=side.abbreviation,
        score=side.score,
        record=side.record,
        players=players,
        totals=totals,
        quarter_scores=tuple(side.linescores),
        team_stats={
            "offensive_rebounds": e.to_int(e.team_stat(side, "offensiveRebounds")),
            "defensive_rebounds": e.to_int(e.team_stat(side, "defensiveRebounds")),
            "turnover_points": e.to_int(e.team_stat(side, "turnoverPoints")),
            "fast_break_points": e.to_int(e.team_stat(side, "fastBreakPoints")),
            "points_in_paint": e.to_int(e.team_stat(side, "pointsInPaint")),
            "fouls": e.to_int(e.team_stat(side, "fouls", "totalFouls")),
        },
        display_name=side.location if ranked else None,
        rank=side.rank if ranked else None,
    )


def normalize(summary: dict[str, Any], *, college: bool = False) -> SimpleBoxScore:
    away, home = e.sides(summary)
    venue, city, state = e.venue(summary)
    return SimpleBoxScore(
        away=_team(away, ranked=college),
        home=_team(home, ranked=college),
        venue=venue,
        city=city,
        state=state,
        officials=e.officials(summary),
        attendance=e.attendance(summary),
        regulation_periods=2 if college else 4,
    )
