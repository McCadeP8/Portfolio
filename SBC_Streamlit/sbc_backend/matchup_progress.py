from __future__ import annotations

from datetime import date

import pandas as pd

from .matchup_preview import normalize_nba_team


def starter_game_progress(
    period_calendar: pd.DataFrame,
    rosters: pd.DataFrame,
    player_catalog: pd.DataFrame,
    nba_games: pd.DataFrame,
    year: int,
    period: int,
    *,
    as_of: date | str | pd.Timestamp | None = None,
    teams: tuple[str, ...] | list[str] = (),
) -> float:
    """Return completed scheduled NBA games divided by games for active fantasy starters."""
    required_calendar = {"Year", "Period", "Day", "Date"}
    required_roster = {"Year", "period", "id", "status", "team_name"}
    if (
        period_calendar is None
        or rosters is None
        or player_catalog is None
        or nba_games is None
        or period_calendar.empty
        or rosters.empty
        or player_catalog.empty
        or nba_games.empty
        or not required_calendar.issubset(period_calendar.columns)
        or not required_roster.issubset(rosters.columns)
    ):
        return 0.0

    days = period_calendar[
        (pd.to_numeric(period_calendar["Year"], errors="coerce") == int(year))
        & (pd.to_numeric(period_calendar["Period"], errors="coerce") == int(period))
    ][["Day", "Date"]].copy()
    days["Day"] = pd.to_numeric(days["Day"], errors="coerce")
    days["game_date"] = pd.to_datetime(days["Date"], errors="coerce").dt.normalize()
    days = days.dropna(subset=["Day", "game_date"])
    if days.empty:
        return 0.0
    days["Day"] = days["Day"].astype(int)

    starters = rosters[
        (pd.to_numeric(rosters["Year"], errors="coerce") == int(year))
        & (pd.to_numeric(rosters["period"], errors="coerce").isin(days["Day"]))
        & (rosters["status"].astype(str).str.upper() == "ACTIVE")
    ].copy()
    if teams:
        wanted = tuple(str(team) for team in teams)
        roster_names = starters["team_name"].astype(str)
        team_mask = pd.Series(False, index=starters.index)
        for team in wanted:
            team_mask |= roster_names.eq(team) | roster_names.str.startswith(f"{team} ")
        starters = starters[team_mask]
    if starters.empty:
        return 0.0

    starters["fantraxId"] = starters["id"].astype(str)
    starters["Day"] = pd.to_numeric(starters["period"], errors="coerce").astype(int)
    starters = starters.merge(days[["Day", "game_date"]], on="Day", how="inner")

    catalog = player_catalog.copy()
    catalog["fantraxId"] = catalog["fantraxId"].astype(str)
    team_column = "nba_team" if "nba_team" in catalog.columns else "team"
    if team_column not in catalog.columns:
        return 0.0
    catalog["nba_team"] = catalog[team_column].map(normalize_nba_team)
    catalog = catalog[["fantraxId", "nba_team"]].drop_duplicates("fantraxId")
    starters = starters.merge(catalog, on="fantraxId", how="left").dropna(subset=["nba_team"])

    games = nba_games.copy()
    games["game_date"] = pd.to_datetime(games["game_date"], errors="coerce").dt.normalize()
    if "completed" not in games.columns:
        state = games["state"] if "state" in games.columns else pd.Series("", index=games.index)
        games["completed"] = state.astype(str).str.lower().eq("post")
    games["fraction"] = [
        game_fraction(row.get("state"), row.get("period"), row.get("clock"), row.get("completed"))
        for row in games.to_dict("records")
    ]
    scheduled = pd.concat(
        [
            games[["game_date", "home_abbreviation", "fraction"]].rename(columns={"home_abbreviation": "nba_team"}),
            games[["game_date", "away_abbreviation", "fraction"]].rename(columns={"away_abbreviation": "nba_team"}),
        ],
        ignore_index=True,
    )
    scheduled["nba_team"] = scheduled["nba_team"].map(normalize_nba_team)
    scheduled = scheduled.dropna(subset=["game_date", "nba_team"])

    assignments = starters.merge(scheduled, on=["game_date", "nba_team"], how="inner")
    if assignments.empty:
        return 0.0
    cutoff = pd.Timestamp(as_of if as_of is not None else date.today()).normalize()
    played = assignments["fraction"].fillna(0.0).where(assignments["game_date"] <= cutoff, 0.0)
    return round(float(played.sum()) / float(len(assignments)) * 100.0, 1)


def game_fraction(state, period, clock, completed) -> float:
    """Share of one NBA game played: 0 before tip, 1 when final, and minutes
    elapsed / 48 in between (8:33 left in the 3rd = 57%). Overtime, and the
    end of regulation before ESPN marks it final, hold at 99.9% so a matchup
    never reads Final before its last game ends."""
    if bool(completed) or str(state).lower() == "post":
        return 1.0
    if str(state).lower() != "in":
        return 0.0
    try:
        quarter = int(float(period))
    except (TypeError, ValueError):
        return 0.0
    if quarter > 4:
        return 0.999
    text = str(clock or "").strip()
    try:
        if ":" in text:
            minutes, seconds = text.split(":", 1)
            remaining = int(minutes) + float(seconds) / 60
        else:
            remaining = float(text) / 60  # under a minute, ESPN sends seconds
    except ValueError:
        remaining = 12.0
    elapsed = (quarter - 1) * 12 + (12 - min(max(remaining, 0.0), 12.0))
    return round(min(max(elapsed / 48, 0.0), 0.999), 4)
