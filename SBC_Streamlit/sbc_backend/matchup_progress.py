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
    scheduled = pd.concat(
        [
            games[["game_date", "home_abbreviation", "completed"]].rename(columns={"home_abbreviation": "nba_team"}),
            games[["game_date", "away_abbreviation", "completed"]].rename(columns={"away_abbreviation": "nba_team"}),
        ],
        ignore_index=True,
    )
    scheduled["nba_team"] = scheduled["nba_team"].map(normalize_nba_team)
    scheduled = scheduled.dropna(subset=["game_date", "nba_team"])

    assignments = starters.merge(scheduled, on=["game_date", "nba_team"], how="inner")
    if assignments.empty:
        return 0.0
    cutoff = pd.Timestamp(as_of if as_of is not None else date.today()).normalize()
    completed = assignments["completed"].fillna(False).astype(bool) & (assignments["game_date"] <= cutoff)
    return round(float(completed.sum()) / float(len(assignments)) * 100.0, 1)
