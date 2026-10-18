"""Plain factual game briefs built straight from box scores.

Used when Claude-written stories are unavailable, so the paper always has
text. Every sentence is a fact from the box score; nothing is embellished.
"""

from __future__ import annotations

from typing import Any

from pearson_press.edition import text
from pearson_press.edition.blocks import Story
from pearson_press.edition.model import GameLine, SportContent


def _winner_loser(game: Any) -> tuple[Any, Any]:
    return (game.away, game.home) if game.away.score > game.home.score else (game.home, game.away)


def _name(team: Any) -> str:
    return f"{team.location} {team.nickname}".strip()


def _innings(value: str) -> str:
    """ESPN's '1.1' means one and one-third innings."""

    whole, _, outs = value.partition(".")
    fraction = {"1": " 1/3", "2": " 2/3"}.get(outs, "")
    if whole == "0" and fraction:
        return fraction.strip()
    return f"{whole}{fraction}"


def _count(value: str | int, noun: str) -> str:
    number = int(value or 0)
    return f"{number} {noun}{'' if number == 1 else 's'}"


def brief(sport: SportContent, event_id: str, game: Any) -> Story:
    winner, loser = _winner_loser(game)
    note = sport.box_notes.get(event_id, "")
    where = f"at {game.venue}" if game.venue else ""
    opener = (f"The {_name(winner)} beat the {_name(loser)} {winner.score}-{loser.score}"
              f"{' in ' + note.replace(' - ', ' ') if note else ''} {where}.").replace("  ", " ").replace(" .", ".")
    paragraphs = [opener]
    series = next((s for s in sport.series if any(g.game.event_id == event_id for g in s.games)), None)
    if series:
        paragraphs.append(f"{series.summary}.")

    if sport.key in {"nba", "ncaam"}:
        for team in (winner, loser):
            top = sorted(team.players, key=lambda p: -p.points)[:2]
            if top:
                lead = top[0]
                line = f"{lead.name} led {team.location} with {lead.points} points, {lead.rebounds} rebounds and {lead.assists} assists"
                if len(top) > 1:
                    line += f", and {top[1].name} added {top[1].points}"
                paragraphs.append(line + ".")
    elif sport.key == "nhl":
        # The deciding goal is the first one that put the winner one past the loser's final total.
        winning_goal = next((g for g in game.goals
                             if (g.away_score if winner is game.away else g.home_score) == loser.score + 1), None)
        if winning_goal and not game.shootout:
            paragraphs.append(f"{winning_goal.scorer} scored the deciding goal at {winning_goal.time} of period "
                              f"{winning_goal.period}.")
        goalie = winner.goalie
        paragraphs.append(f"{goalie.name} made {goalie.shots_against - loser.score} saves for {winner.location}.")
    elif sport.key == "mlb":
        decisions = [p for team in (winner, loser) for p in team.pitchers
                     if p.decision[:1] in {"W", "L", "S"}]
        for pitcher in decisions:
            innings = _innings(pitcher.innings)
            paragraphs.append(f"{pitcher.name} ({pitcher.decision}) pitched {innings} "
                              f"{'inning' if innings == '1' else 'innings'}, "
                              f"allowing {_count(pitcher.earned_runs, 'earned run')} with "
                              f"{_count(pitcher.strikeouts, 'strikeout')}.")
        if winner.home_runs:
            paragraphs.append(f"Home runs: {', '.join(winner.home_runs)}.")
    elif sport.key in {"nfl", "ncaaf"}:
        for team in (winner, loser):
            if team.passing:
                qb = team.passing[0]
                paragraphs.append(f"{qb.name} went {qb.values[0]} for {qb.values[1]} yards and "
                                  f"{qb.values[2]} touchdowns for {team.location}.")
    return Story(
        headline=game.headline,
        body=tuple(paragraphs),
        kicker=note or sport.label,
        credit="Pearson Press | Compiled from ESPN box score",
        event_id=event_id,
    )


def preview_brief(sport: SportContent, game: GameLine) -> Story:
    """A factual preview: who, when, where to watch, and where things stand."""

    when = f"{text.weekday_date(game.start.date())} at {text.clock(game.start)} {text.ZONE_LABEL}"
    paragraphs = [f"{game.away.label} at {game.home.label}, {when}."]
    tv = text.first_network(game)
    if tv:
        paragraphs.append(f"The game airs on {tv}.")
    records = [f"{team.label} is {team.record}" for team in (game.away, game.home) if team.record]
    if records:
        paragraphs.append(" and ".join(records) + ".")
    if game.series_summary:
        paragraphs.append(f"{game.series_summary}.")
    kicker = game.note.split(" - ")[0] if game.note else sport.label
    return Story(
        headline=game.matchup_text(),
        body=tuple(paragraphs),
        kicker=f"{kicker} preview",
        credit="Pearson Press | Compiled from ESPN data",
        event_id=game.event_id,
    )
