from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .counting_models import STANDARD_NBA_GAMES, _sigmoid, fit_logistic, standardize_total


SHOOTING_CATEGORIES = ["TS%", "2PT%", "3PT%", "FT%"]
SHOOTING_FIELDS = {
    "TS%": ("TS%", "TS_ATTEMPTS"),
    "2PT%": ("2PT%", "2PTA"),
    "3PT%": ("3PT%", "3PTA"),
    "FT%": ("FT%", "FTA"),
}


def add_true_shot_attempts(team_stats: pd.DataFrame) -> pd.DataFrame:
    result = team_stats.copy()
    two_a = pd.to_numeric(result["2PTA"], errors="coerce").fillna(0)
    three_a = pd.to_numeric(result["3PTA"], errors="coerce").fillna(0)
    ft_a = pd.to_numeric(result["FTA"], errors="coerce").fillna(0)
    # TS% = PTS / [2 * (FGA + 0.44 * FTA)], so this is its natural
    # attempt denominator and turns percentage lift into points above average.
    result["TS_ATTEMPTS"] = 2 * (two_a + three_a + 0.44 * ft_a)
    return result


def season_league_averages(team_stats: pd.DataFrame) -> pd.DataFrame:
    stats = add_true_shot_attempts(team_stats)
    rows: list[dict] = []
    for year, season in stats.groupby("Year"):
        row: dict[str, float | int] = {"Year": int(year)}
        for category, (percentage_column, attempt_column) in SHOOTING_FIELDS.items():
            attempts = pd.to_numeric(season[attempt_column], errors="coerce")
            percentages = pd.to_numeric(season[percentage_column], errors="coerce")
            valid = attempts.gt(0) & percentages.notna()
            row[category] = (
                float(np.average(percentages[valid], weights=attempts[valid]))
                if valid.any() and attempts[valid].sum() > 0 else np.nan
            )
        rows.append(row)
    return pd.DataFrame(rows).dropna(subset=SHOOTING_CATEGORIES, how="all")


def shooting_team_periods(team_stats: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    stats = add_true_shot_attempts(team_stats)
    averages = season_league_averages(stats)
    average_columns = {category: f"league_{category}" for category in SHOOTING_CATEGORIES}
    stats = stats.merge(
        averages.rename(columns=average_columns), on="Year", how="left", validate="many_to_one"
    )
    for category, (percentage_column, attempt_column) in SHOOTING_FIELDS.items():
        percentage = pd.to_numeric(stats[percentage_column], errors="coerce")
        attempts = pd.to_numeric(stats[attempt_column], errors="coerce")
        stats[f"{category}_points_gained"] = (
            percentage - pd.to_numeric(stats[f"league_{category}"], errors="coerce")
        ) * attempts
    return stats, averages


def shooting_observations(
    matchups: pd.DataFrame, team_periods: pd.DataFrame, category: str
) -> pd.DataFrame:
    winner = matchups[f"{category}_winner"]
    source = matchups.loc[winner.isin(["A", "B"])]
    rows = []
    value_column = f"{category}_points_gained"
    for side in ["A", "B"]:
        side_rows = source[[
            "Game_ID", "Year", "Period", f"Team{side}", "nba_games_in_period", f"{category}_winner"
        ]].rename(columns={f"Team{side}": "Team"})
        side_rows = side_rows.merge(
            team_periods[["Year", "Period", "Team", value_column]],
            on=["Year", "Period", "Team"], how="left", validate="many_to_one",
        )
        rows.append(pd.DataFrame({
            "Game_ID": side_rows["Game_ID"].astype(str),
            "Year": side_rows["Year"],
            "Period": side_rows["Period"],
            "category": category,
            "adjusted_total": standardize_total(
                side_rows[value_column], side_rows["nba_games_in_period"]
            ),
            "won_category": side_rows[f"{category}_winner"].eq(side).astype(int),
        }))
    observations = pd.concat(rows, ignore_index=True)
    return observations.replace([np.inf, -np.inf], np.nan).dropna(subset=["adjusted_total"])


def fit_shooting_models(
    matchups: pd.DataFrame, team_stats: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    team_periods, averages = shooting_team_periods(team_stats)
    model_rows = []
    curve_rows = []
    bin_rows = []
    for category in SHOOTING_CATEGORIES:
        observations = shooting_observations(matchups, team_periods, category)
        result = fit_logistic(observations)
        model_rows.append({
            "category": category,
            "metric": "points gained",
            "standard_nba_games": STANDARD_NBA_GAMES,
            **result,
        })

        lower, upper = observations["adjusted_total"].quantile([0.01, 0.99])
        grid = np.linspace(lower, upper, 121)
        probability = _sigmoid(result["intercept"] + result["slope"] * grid)
        curve_rows.extend({
            "category": category,
            "adjusted_total": float(value),
            "win_probability": float(chance),
        } for value, chance in zip(grid, probability))

        binned = observations.copy()
        binned["bin"] = pd.qcut(binned["adjusted_total"], q=12, duplicates="drop")
        calibration = binned.groupby("bin", observed=True).agg(
            adjusted_total=("adjusted_total", "mean"),
            observed_win_rate=("won_category", "mean"),
            observations=("won_category", "size"),
        ).reset_index(drop=True)
        calibration.insert(0, "category", category)
        bin_rows.extend(calibration.to_dict("records"))

    return pd.DataFrame(model_rows), pd.DataFrame(curve_rows), pd.DataFrame(bin_rows), averages


def projected_player_points_gained(projections: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    players = projections.copy()
    players["ts_attempts"] = 2 * (
        pd.to_numeric(players["fg_a"], errors="coerce").fillna(0)
        + 0.44 * pd.to_numeric(players["ft_a"], errors="coerce").fillna(0)
    )
    fields = {
        "TS%": ("ts_pct", "ts_attempts"),
        "2PT%": ("two_pct", "two_a"),
        "3PT%": ("three_pct", "three_a"),
        "FT%": ("ft_pct", "ft_a"),
    }
    league_averages: dict[str, float] = {}
    output = players[["fantrax_player_id", "player_name", "nba_team"]].copy()
    for category, (percentage_column, attempt_column) in fields.items():
        percentages = pd.to_numeric(players[percentage_column], errors="coerce")
        attempts = pd.to_numeric(players[attempt_column], errors="coerce").fillna(0)
        valid = attempts.gt(0) & percentages.notna()
        league_average = float(np.average(percentages[valid], weights=attempts[valid]))
        league_averages[category] = league_average
        output[f"{category}_league_average"] = league_average
        output[f"{category}_attempts"] = attempts
        output[f"{category}_points_gained"] = (percentages - league_average) * attempts
    return output, league_averages


def write_shooting_models(processed_dir: Path, raw_dir: Path) -> dict[str, int]:
    matchups = pd.read_parquet(processed_dir / "historical_matchups.parquet")
    team_stats = pd.read_parquet(raw_dir / "sbc_streamlit" / "all_team_stats_history.parquet")
    models, curves, bins, averages = fit_shooting_models(matchups, team_stats)
    models.to_csv(processed_dir / "shooting_logistic_models.csv", index=False)
    curves.to_csv(processed_dir / "shooting_logistic_curves.csv", index=False)
    bins.to_csv(processed_dir / "shooting_logistic_bins.csv", index=False)
    averages.to_csv(processed_dir / "shooting_league_averages.csv", index=False)

    projections = pd.read_csv(processed_dir / "canonical_player_projections.csv", dtype={"fantrax_player_id": str})
    player_metrics, _ = projected_player_points_gained(projections)
    player_metrics.to_csv(processed_dir / "player_shooting_points_gained.csv", index=False)
    return {
        "models": len(models), "curves": len(curves), "bins": len(bins),
        "seasons": len(averages), "players": len(player_metrics),
    }
