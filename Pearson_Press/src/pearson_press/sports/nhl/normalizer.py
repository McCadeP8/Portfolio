"""Turn an ESPN NHL game summary into the simple box-score model."""

from __future__ import annotations

from typing import Any

from pearson_press.providers import espn_parse as e
from pearson_press.sports.nhl.components import GoalEvent, GoalieLine, NHLSimpleBoxScore, NHLTeamBox

STRENGTH = {"power-play": "PP", "short-handed": "SH"}


def _seconds(clock: str) -> int:
    minutes, _, seconds = clock.partition(":")
    return e.to_int(minutes) * 60 + e.to_int(seconds)


def _goalie(side: e.Side) -> GoalieLine:
    for group in e.stat_groups(side):
        if group.get("name") != "goalies" or not group["athletes"]:
            continue
        labels = group["labels"]
        # The goalie of record is the one who played the most.
        athlete = max(group["athletes"], key=lambda a: _seconds(e.row(labels, a["stats"]).get("TOI", "0:00")))
        stats = e.row(labels, athlete["stats"])
        return GoalieLine(
            name=e.surname(athlete["athlete"]["displayName"]),
            even_strength_saves=e.to_int(stats.get("ESSV")),
            power_play_saves=e.to_int(stats.get("PPSV")),
            short_handed_saves=e.to_int(stats.get("SHSV")),
            shots_against=e.to_int(stats.get("SA")),
            save_pct=stats.get("SV%", ".000"),
            time_on_ice=stats.get("TOI", "0:00"),
        )
    return GoalieLine("-", 0, 0, 0, 0, "-", "-")


def _penalty_minutes(side: e.Side) -> tuple[tuple[str, int], ...]:
    minutes: list[tuple[str, int]] = []
    for group in e.stat_groups(side):
        labels = group["labels"]
        for athlete in group["athletes"]:
            pim = e.to_int(e.row(labels, athlete["stats"]).get("PIM"))
            if pim:
                minutes.append((e.surname(athlete["athlete"]["displayName"]), pim))
    bench = e.to_int(e.team_stat(side, "penaltyMinutes")) - sum(value for _, value in minutes)
    minutes.sort(key=lambda item: -item[1])
    if bench > 0:
        minutes.append(("Team", bench))
    return tuple(minutes)


def _team(side: e.Side, regulation_and_ot: int) -> NHLTeamBox:
    return NHLTeamBox(
        location=side.location,
        nickname=side.nickname,
        abbreviation=side.abbreviation,
        score=side.score,
        goalie=_goalie(side),
        penalty_minutes=_penalty_minutes(side),
        team_stats={
            "shots": e.team_stat(side, "shotsTotal"),
            "hits": e.team_stat(side, "hits"),
            "faceoffs_won": e.team_stat(side, "faceoffsWon"),
            "power_play": f"{e.team_stat(side, 'powerPlayGoals')}/{e.team_stat(side, 'powerPlayOpportunities')}",
            "blocked_shots": e.team_stat(side, "blockedShots"),
            "takeaways": e.team_stat(side, "takeaways"),
            "giveaways": e.team_stat(side, "giveaways"),
        },
        period_scores=tuple(side.linescores[:regulation_and_ot]),
    )


def _goals(summary: dict[str, Any], last_period: int) -> tuple[GoalEvent, ...]:
    goals = []
    for play in summary.get("plays", []):
        if not play.get("scoringPlay") or play["period"]["number"] > last_period:
            continue
        people = play.get("participants", [])
        scorer = next((p for p in people if p.get("type") == "scorer"), None)
        if scorer is None:
            continue
        strength = STRENGTH.get(play.get("strength", {}).get("abbreviation", ""), "")
        if "empty net" in play.get("text", "").lower():
            strength = f"{strength}, EN" if strength else "EN"
        goals.append(GoalEvent(
            period=play["period"]["number"],
            time=play.get("clock", {}).get("displayValue", ""),
            scorer=scorer["athlete"]["displayName"],
            goal_number=e.to_int(scorer.get("ytdGoals")),
            assists=tuple(
                f"{p['athlete']['displayName']} ({e.to_int(p.get('ytdAssists'))})"
                for p in people if p.get("type") == "assister"
            ),
            away_score=e.to_int(play.get("awayScore")),
            home_score=e.to_int(play.get("homeScore")),
            strength=strength,
        ))
    return tuple(goals)


def normalize(summary: dict[str, Any]) -> NHLSimpleBoxScore:
    away, home = e.sides(summary)
    detail = e.status(summary).get("detail", "")
    shootout = "SO" in detail
    periods = max(len(away.linescores), len(home.linescores), 3)
    # ESPN lists a shootout as its own "period"; it is not part of play time.
    played = periods - 1 if shootout else periods
    venue, city, state = e.venue(summary)
    return NHLSimpleBoxScore(
        away=_team(away, played),
        home=_team(home, played),
        goals=_goals(summary, played),
        venue=venue,
        city=city,
        state=state,
        officials=e.officials(summary),
        attendance=e.attendance(summary),
        overtime_periods=max(0, played - 3),
        shootout=shootout,
    )
