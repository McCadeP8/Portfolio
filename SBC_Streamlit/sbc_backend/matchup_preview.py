from __future__ import annotations

import pandas as pd


SUM_STATS = [
    "MP", "2PTM", "2PTA", "3PTM", "3PTA", "FTM", "FTA", "PTS",
    "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-",
]

NBA_TEAM_ALIASES = {
    "GS": "GSW",
    "NY": "NYK",
    "NO": "NOP",
    "SA": "SAS",
    "UTAH": "UTA",
    "WSH": "WAS",
}


def normalize_nba_team(value: object) -> str:
    team = str(value or "").strip().upper()
    return NBA_TEAM_ALIASES.get(team, team)


def project_player_rows(
    active_roster: pd.DataFrame,
    player_bridge: pd.DataFrame,
    player_catalog: pd.DataFrame,
    prior_boxscores: pd.DataFrame,
    nba_games: pd.DataFrame,
) -> pd.DataFrame:
    """Project a future fantasy matchup from current rosters and prior-year NBA rates."""
    if any(frame is None or frame.empty for frame in (active_roster, player_bridge, player_catalog, prior_boxscores, nba_games)):
        return pd.DataFrame()

    roster = active_roster.copy()
    roster["fantraxId"] = roster["fantraxId"].astype(str)
    bridge = player_bridge[["fantraxId", "espn_player_id", "fantrax_name"]].copy()
    bridge["fantraxId"] = bridge["fantraxId"].astype(str)
    bridge["espn_player_id"] = bridge["espn_player_id"].astype(str)

    catalog = player_catalog.copy()
    catalog["fantraxId"] = catalog["fantraxId"].astype(str)
    team_column = "nba_team" if "nba_team" in catalog.columns else "team"
    if team_column not in catalog.columns:
        return pd.DataFrame()
    catalog = catalog[["fantraxId", team_column]].drop_duplicates("fantraxId")
    catalog["nba_team"] = catalog[team_column].map(normalize_nba_team)

    roster = roster.merge(bridge, on="fantraxId", how="left").merge(
        catalog[["fantraxId", "nba_team"]], on="fantraxId", how="left"
    )
    roster = roster.dropna(subset=["espn_player_id"]).drop_duplicates("fantraxId")

    game_teams = pd.concat(
        [nba_games.get("home_abbreviation", pd.Series(dtype=str)), nba_games.get("away_abbreviation", pd.Series(dtype=str))],
        ignore_index=True,
    ).map(normalize_nba_team)
    games_remaining = game_teams.value_counts().to_dict()
    roster["projected_games"] = roster["nba_team"].map(games_remaining).fillna(0).astype(int)
    roster = roster[roster["projected_games"] > 0].copy()
    if roster.empty:
        return pd.DataFrame()

    box = prior_boxscores.copy()
    box["nba_player_id"] = box["nba_player_id"].astype(str)
    for stat in SUM_STATS:
        if stat not in box.columns:
            box[stat] = 0.0
        else:
            box[stat] = pd.to_numeric(box[stat], errors="coerce").fillna(0)
    games_played = box.groupby("nba_player_id")["nba_game_id"].nunique().rename("prior_games")
    rates = box.groupby("nba_player_id", as_index=False)[SUM_STATS].sum().merge(games_played, on="nba_player_id")
    for stat in SUM_STATS:
        rates[stat] = rates[stat] / rates["prior_games"].clip(lower=1)

    projected = roster.merge(rates, left_on="espn_player_id", right_on="nba_player_id", how="inner")
    for stat in SUM_STATS:
        projected[stat] = projected[stat] * projected["projected_games"]
    projected["GP"] = projected["projected_games"]
    attempts = projected["2PTA"] + projected["3PTA"] + 0.44 * projected["FTA"]
    projected["TS%"] = (projected["PTS"] / (2 * attempts)).where(attempts > 0, 0)
    projected["2PT%"] = (projected["2PTM"] / projected["2PTA"]).where(projected["2PTA"] > 0, 0)
    projected["3PT%"] = (projected["3PTM"] / projected["3PTA"]).where(projected["3PTA"] > 0, 0)
    projected["FT%"] = (projected["FTM"] / projected["FTA"]).where(projected["FTA"] > 0, 0)
    projected["display_player"] = projected["fantrax_name"]
    projected["projection"] = True
    return projected.reset_index(drop=True)
