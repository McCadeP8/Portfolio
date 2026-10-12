from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import requests


CATEGORY_SOURCE = {
    "MP": "MP",
    "TS%": "TS%",
    "2PT%": "2PT%",
    "3PT%": "3PT%",
    "FT%": "FT%",
    "PTS": "PTS",
    "OREB": "OREB",
    "DREB": "DREB",
    "AST": "AST",
    "STL": "ST",
    "BLK": "BLK",
    "TOV": "TO",
    "+/-": "+/-",
}
CATEGORIES = list(CATEGORY_SOURCE)
PERCENTAGE_CATEGORIES = {"TS%", "2PT%", "3PT%", "FT%"}
LOWER_IS_BETTER = {"TOV"}
SOURCE_FILES = (
    "all_team_stats_history.parquet",
    "all_time_scores.parquet",
    "sbc_player_matchup_stats.parquet",
    "nba_player_game_boxscores_2021_2026.parquet",
    "data_snapshots/period_calendar.parquet",
)


def _team_game_counts(player_stats: pd.DataFrame, valid_teams: set[str]) -> pd.DataFrame:
    players = player_stats[player_stats["sbc_team_key"].isin(valid_teams)].copy()
    players["player_key"] = (
        players["fantrax_id"].fillna("").astype(str).str.strip()
        .mask(lambda value: value.eq(""), players["espn_player_id"].fillna("").astype(str).str.strip())
        .mask(lambda value: value.eq(""), players["player_name"].fillna("").astype(str).str.strip())
    )
    players = players.sort_values("Game_ID").drop_duplicates(
        ["sbc_year", "sbc_period", "sbc_team_key", "player_key"]
    )
    return (
        players.groupby(["sbc_year", "sbc_period", "sbc_team_key"], as_index=False)["GP"]
        .sum()
        .rename(columns={"sbc_year": "Year", "sbc_period": "Period", "sbc_team_key": "Team"})
    )


def build_historical_matchups(
    scores: pd.DataFrame,
    team_stats: pd.DataFrame,
    player_stats: pd.DataFrame,
    period_calendar: pd.DataFrame,
) -> pd.DataFrame:
    completed = scores.loc[(scores["TeamAScore"].abs() + scores["TeamBScore"].abs()) > 0].copy()
    completed = completed[pd.to_numeric(completed["Year"], errors="coerce").le(2026)]

    stats = team_stats.copy()
    stats = stats.rename(columns={source: category for category, source in CATEGORY_SOURCE.items()})
    gp = _team_game_counts(player_stats, set(stats["Team"].dropna().astype(str)))
    stats = stats.drop(columns=["GP"], errors="ignore").merge(
        gp, on=["Year", "Period", "Team"], how="left", validate="one_to_one"
    )

    keep = ["Year", "Period", "Team", "GP", *CATEGORIES]
    left = stats[keep].rename(
        columns={"Team": "TeamA", **{column: f"{column}_A" for column in ["GP", *CATEGORIES]}}
    )
    right = stats[keep].rename(
        columns={"Team": "TeamB", **{column: f"{column}_B" for column in ["GP", *CATEGORIES]}}
    )
    matchups = completed.merge(left, on=["Year", "Period", "TeamA"], how="left", validate="many_to_one")
    matchups = matchups.merge(right, on=["Year", "Period", "TeamB"], how="left", validate="many_to_one")

    calendar = period_calendar.copy()
    calendar["Date"] = pd.to_datetime(calendar["Date"], errors="coerce")
    windows = (
        calendar.groupby(["Year", "Period"], as_index=False)
        .agg(period_start=("Date", "min"), period_end=("Date", "max"), period_stage=("Season", "first"))
    )
    matchups = matchups.merge(windows, on=["Year", "Period"], how="left", validate="many_to_one")
    matchups["matchup_winner"] = np.select(
        [matchups["TeamAScore"] > matchups["TeamBScore"], matchups["TeamBScore"] > matchups["TeamAScore"]],
        ["A", "B"],
        default="TIE",
    )
    for category in CATEGORIES:
        left_value = matchups[f"{category}_A"]
        right_value = matchups[f"{category}_B"]
        if category in LOWER_IS_BETTER:
            left_wins, right_wins = left_value < right_value, right_value < left_value
        else:
            left_wins, right_wins = left_value > right_value, right_value > left_value
        matchups[f"{category}_winner"] = np.select([left_wins, right_wins], ["A", "B"], default="TIE")
    return matchups.sort_values(["Year", "Period", "Game_ID"]).reset_index(drop=True)


def summarize_categories(matchups: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    decided_matchups = matchups[matchups["matchup_winner"].ne("TIE")]
    rows: list[dict] = []
    for category in CATEGORIES:
        winner_column = f"{category}_winner"
        category_decided = matchups[matchups[winner_column].ne("TIE")].copy()
        category_winner = category_decided[winner_column]
        winning_value = np.where(
            category_winner.eq("A"), category_decided[f"{category}_A"], category_decided[f"{category}_B"]
        )
        losing_value = np.where(
            category_winner.eq("A"), category_decided[f"{category}_B"], category_decided[f"{category}_A"]
        )
        if category in PERCENTAGE_CATEGORIES:
            threshold = pd.Series(winning_value).replace([np.inf, -np.inf], np.nan).dropna()
            losing_threshold = pd.Series(losing_value).replace([np.inf, -np.inf], np.nan).dropna()
            league_threshold = pd.concat([
                pd.to_numeric(matchups[f"{category}_A"], errors="coerce"),
                pd.to_numeric(matchups[f"{category}_B"], errors="coerce"),
            ]).replace([np.inf, -np.inf], np.nan).dropna()
            threshold_kind = "winning percentage"
        else:
            period_games = pd.to_numeric(category_decided["nba_games_in_period"], errors="coerce").reset_index(drop=True)
            threshold = pd.Series(winning_value).div(period_games.replace(0, np.nan)).replace(
                [np.inf, -np.inf], np.nan
            ).dropna()
            losing_threshold = pd.Series(losing_value).div(period_games.replace(0, np.nan)).replace(
                [np.inf, -np.inf], np.nan
            ).dropna()
            all_period_games = pd.to_numeric(matchups["nba_games_in_period"], errors="coerce").replace(0, np.nan)
            league_threshold = pd.concat([
                pd.to_numeric(matchups[f"{category}_A"], errors="coerce").div(all_period_games),
                pd.to_numeric(matchups[f"{category}_B"], errors="coerce").div(all_period_games),
            ]).replace([np.inf, -np.inf], np.nan).dropna()
            threshold_kind = "per NBA game"
        matchup_alignment = (
            decided_matchups[winner_column].eq(decided_matchups["matchup_winner"])
        )
        rows.append({
            "category": category,
            "matchup_winner_category_win_pct": matchup_alignment.mean(),
            "category_tie_pct": matchups[winner_column].eq("TIE").mean(),
            "average_winning_threshold": threshold.mean(),
            "average_league_threshold": league_threshold.mean(),
            "average_losing_threshold": losing_threshold.mean(),
            "median_winning_threshold": threshold.median(),
            "threshold_kind": threshold_kind,
            "matchups": len(decided_matchups),
            "decided_category_matchups": len(category_decided),
        })

    co_win = pd.DataFrame(index=CATEGORIES, columns=CATEGORIES, dtype=float)
    for row_category in CATEGORIES:
        for column_category in CATEGORIES:
            row_winner = matchups[f"{row_category}_winner"]
            column_winner = matchups[f"{column_category}_winner"]
            decided = row_winner.ne("TIE") & column_winner.ne("TIE")
            co_win.loc[row_category, column_category] = (
                row_winner[decided].eq(column_winner[decided]).mean() if decided.any() else np.nan
            )
    co_win.index.name = "category"
    return pd.DataFrame(rows), co_win


def historical_nba_schedule(boxscores: pd.DataFrame) -> pd.DataFrame:
    games = boxscores[[
        "sbc_year", "nba_season", "Date", "nba_game_id", "nba_team", "opponent", "is_home"
    ]].drop_duplicates(["nba_game_id", "nba_team", "is_home"])
    home = games[games["is_home"]].rename(columns={"nba_team": "home_team", "opponent": "away_team"})
    away = games[~games["is_home"]].rename(columns={"nba_team": "away_team_check", "opponent": "home_team_check"})
    schedule = home.merge(
        away[["nba_game_id", "away_team_check", "home_team_check"]], on="nba_game_id", how="left", validate="one_to_one"
    )
    schedule["away_team"] = schedule["away_team"].fillna(schedule["away_team_check"])
    schedule["home_team"] = schedule["home_team"].fillna(schedule["home_team_check"])
    schedule["date"] = pd.to_datetime(schedule["Date"], errors="coerce").dt.date.astype(str)
    schedule["source"] = "SBC Streamlit historical ESPN boxscores"
    return schedule[["sbc_year", "nba_season", "date", "nba_game_id", "away_team", "home_team", "source"]]


def _espn_day(day: date, timeout: int = 30) -> list[dict]:
    response = requests.get(
        "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        params={"dates": day.strftime("%Y%m%d"), "limit": 100},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json().get("events", [])


def fetch_espn_nba_schedule(start: date, end: date, raw_path: Path, workers: int = 8) -> pd.DataFrame:
    days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
    events: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_espn_day, day): day for day in days}
        for future in as_completed(futures):
            events.extend(future.result())
    unique_events = {str(event.get("id")): event for event in events if event.get("id")}
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(list(unique_events.values()), ensure_ascii=False), encoding="utf-8")

    return espn_events_to_schedule(list(unique_events.values()))


def espn_events_to_schedule(events: list[dict]) -> pd.DataFrame:

    rows = []
    for event in events:
        competitions = event.get("competitions") or []
        if not competitions:
            continue
        competitors = competitions[0].get("competitors") or []
        home = next((item for item in competitors if item.get("homeAway") == "home"), {})
        away = next((item for item in competitors if item.get("homeAway") == "away"), {})
        rows.append({
            "sbc_year": 2027,
            "nba_season": "2026-27",
            "date": pd.to_datetime(event.get("date"), errors="coerce").date().isoformat(),
            "nba_game_id": str(event.get("id")),
            "away_team": (away.get("team") or {}).get("abbreviation", ""),
            "home_team": (home.get("team") or {}).get("abbreviation", ""),
            "source": "ESPN public NBA scoreboard schedule",
        })
    return pd.DataFrame(rows).sort_values(["date", "nba_game_id"]).reset_index(drop=True)


def import_sbc_history(
    source_dir: Path,
    raw_dir: Path,
    processed_dir: Path,
    fetch_current_schedule: bool = False,
) -> dict[str, int]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    for relative in SOURCE_FILES:
        source = source_dir / relative
        destination = raw_dir / Path(relative).name
        shutil.copy2(source, destination)

    team_stats = pd.read_parquet(source_dir / "all_team_stats_history.parquet")
    scores = pd.read_parquet(source_dir / "all_time_scores.parquet")
    player_stats = pd.read_parquet(source_dir / "sbc_player_matchup_stats.parquet")
    boxscores = pd.read_parquet(source_dir / "nba_player_game_boxscores_2021_2026.parquet")
    calendar = pd.read_parquet(source_dir / "data_snapshots" / "period_calendar.parquet")

    calendar_out = calendar.copy()
    calendar_out["Date"] = pd.to_datetime(calendar_out["Date"], errors="coerce").dt.date.astype(str)
    calendar_join = calendar_out[["Year", "Date", "Period", "Season"]].rename(
        columns={"Year": "sbc_year", "Date": "date"}
    )

    matchups = build_historical_matchups(scores, team_stats, player_stats, calendar)
    nba_schedule = historical_nba_schedule(boxscores)
    nba_schedule = nba_schedule.merge(
        calendar_join, on=["sbc_year", "date"], how="left", validate="many_to_one"
    )
    period_games = (
        nba_schedule.dropna(subset=["Period"])
        .groupby(["sbc_year", "Period"], as_index=False)["nba_game_id"]
        .nunique()
        .rename(columns={"sbc_year": "Year", "nba_game_id": "nba_games_in_period"})
    )
    matchups = matchups.merge(period_games, on=["Year", "Period"], how="left", validate="many_to_one")
    summary, co_win = summarize_categories(matchups)

    schedule_snapshot = raw_dir / "espn_nba_schedule_2026_27.json"
    if fetch_current_schedule:
        current = fetch_espn_nba_schedule(
            date(2026, 10, 20), date(2027, 4, 11), schedule_snapshot
        )
        current = current.merge(calendar_join, on=["sbc_year", "date"], how="left", validate="many_to_one")
        nba_schedule = pd.concat([nba_schedule, current], ignore_index=True).drop_duplicates("nba_game_id", keep="last")
    elif schedule_snapshot.exists():
        current = espn_events_to_schedule(json.loads(schedule_snapshot.read_text(encoding="utf-8")))
        current = current.merge(calendar_join, on=["sbc_year", "date"], how="left", validate="many_to_one")
        nba_schedule = pd.concat([nba_schedule, current], ignore_index=True).drop_duplicates("nba_game_id", keep="last")

    matchups.to_parquet(processed_dir / "historical_matchups.parquet", index=False)
    summary.to_csv(processed_dir / "league_category_summary.csv", index=False)
    co_win.to_csv(processed_dir / "league_category_cowin.csv")
    calendar_out.to_csv(processed_dir / "sbc_period_calendar.csv", index=False)
    nba_schedule.sort_values(["date", "nba_game_id"]).to_csv(processed_dir / "nba_schedule.csv", index=False)
    return {
        "matchups": len(matchups),
        "seasons": matchups["Year"].nunique(),
        "period_days": len(calendar_out),
        "nba_games": len(nba_schedule),
    }
