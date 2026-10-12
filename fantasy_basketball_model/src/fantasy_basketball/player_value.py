from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .counting_models import COUNTING_CATEGORIES, STANDARD_NBA_GAMES, _sigmoid
from .overall_model import ALL_CATEGORIES
from .shooting_models import SHOOTING_CATEGORIES


ROSTER_SIZE = 15.0
PLAYER_GAMES_PER_PERIOD = STANDARD_NBA_GAMES / ROSTER_SIZE
COUNTING_PLAYER_COLUMNS = {
    "MP": "minutes",
    "PTS": "points",
    "OREB": "offensive_rebounds",
    "DREB": "defensive_rebounds",
    "AST": "assists",
    "STL": "steals",
    "BLK": "blocks",
    "TOV": "turnovers",
    "+/-": "plus_minus",
}


def probability_rating(intercept: float, slope: float, adjusted_total: float) -> float:
    return float(np.clip(10 * _sigmoid(np.array([intercept + slope * adjusted_total]))[0], 0, 10))


def minmax_rating(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    lower, upper = numeric.min(), numeric.max()
    if pd.isna(lower) or pd.isna(upper) or upper - lower <= 1e-12:
        return pd.Series(np.where(numeric.notna(), 5.0, np.nan), index=values.index)
    return ((numeric - lower) / (upper - lower) * 10).clip(0, 10)


def player_period_contributions(players: pd.DataFrame, shooting: pd.DataFrame) -> pd.DataFrame:
    frame = players.copy()
    shooting_columns = ["fantrax_player_id", *[f"{category}_points_gained" for category in SHOOTING_CATEGORIES]]
    frame["fantrax_player_id"] = frame["fantrax_player_id"].astype(str)
    shooting = shooting[shooting_columns].copy()
    shooting["fantrax_player_id"] = shooting["fantrax_player_id"].astype(str)
    frame = frame.merge(shooting, on="fantrax_player_id", how="left", validate="one_to_one")
    games = pd.to_numeric(frame["games"], errors="coerce").replace(0, np.nan)
    contributions = frame[["fantrax_player_id", "player_name", "fantasy_team_id", "fantasy_team_name", "roster_status"]].copy()
    for category, column in COUNTING_PLAYER_COLUMNS.items():
        value = pd.to_numeric(frame[column], errors="coerce")
        per_game = value if category == "MP" else value.div(games)
        contributions[category] = per_game * PLAYER_GAMES_PER_PERIOD
    for category in SHOOTING_CATEGORIES:
        contributions[category] = pd.to_numeric(
            frame[f"{category}_points_gained"], errors="coerce"
        ).div(games) * PLAYER_GAMES_PER_PERIOD
    return contributions


def build_player_value_ratings(
    players: pd.DataFrame,
    shooting: pd.DataFrame,
    counting_models: pd.DataFrame,
    shooting_models: pd.DataFrame,
    overall_model: pd.Series,
    overall_coefficients: pd.DataFrame,
) -> pd.DataFrame:
    contributions = player_period_contributions(players, shooting)
    counting = counting_models.set_index("category")
    shooting_fit = shooting_models.set_index("category")
    overall = overall_coefficients.set_index("category")
    eligible = pd.to_numeric(players["games"], errors="coerce").fillna(0).gt(0).to_numpy() & (
        pd.to_numeric(players["minutes"], errors="coerce").fillna(0).gt(0).to_numpy()
    )
    result = contributions[["fantrax_player_id", "player_name", "fantasy_team_id", "fantasy_team_name", "roster_status"]].copy()

    for category in ALL_CATEGORIES:
        model = shooting_fit.loc[category] if category in SHOOTING_CATEGORIES else counting.loc[category]
        average_fourteen_player_core = float(model["threshold_50"]) * (ROSTER_SIZE - 1) / ROSTER_SIZE
        adjusted = average_fourteen_player_core + pd.to_numeric(contributions[category], errors="coerce")
        rating = adjusted.map(lambda value: probability_rating(model["intercept"], model["slope"], value) if pd.notna(value) else np.nan)
        raw_rating = rating.where(eligible)
        result[f"probability_rating_{category}"] = raw_rating
        result[f"rating_{category}"] = minmax_rating(raw_rating)

    linear_predictor = np.full(len(contributions), float(overall_model["intercept_standardized"]))
    for category in ALL_CATEGORIES:
        mean = float(overall.loc[category, "mean"])
        scale = float(overall.loc[category, "standard_deviation"])
        after_replacement = mean * (ROSTER_SIZE - 1) / ROSTER_SIZE + pd.to_numeric(
            contributions[category], errors="coerce"
        ).to_numpy()
        standardized = (after_replacement - mean) / scale
        linear_predictor += float(overall.loc[category, "coefficient_per_sd"]) * standardized
    result["overall_probability_rating"] = pd.Series(10 * _sigmoid(linear_predictor)).where(eligible).clip(0, 10)
    result["overall_rating"] = minmax_rating(result["overall_probability_rating"])
    return result


def write_player_value_ratings(processed_dir: Path) -> dict[str, int]:
    players = pd.read_csv(processed_dir / "canonical_player_projections.csv", dtype={"fantrax_player_id": str})
    shooting = pd.read_csv(processed_dir / "player_shooting_points_gained.csv", dtype={"fantrax_player_id": str})
    counting_models = pd.read_csv(processed_dir / "counting_logistic_models.csv")
    shooting_models = pd.read_csv(processed_dir / "shooting_logistic_models.csv")
    overall_model = pd.read_csv(processed_dir / "overall_logistic_model.csv").iloc[0]
    overall_coefficients = pd.read_csv(processed_dir / "overall_logistic_coefficients.csv")
    ratings = build_player_value_ratings(
        players, shooting, counting_models, shooting_models, overall_model, overall_coefficients
    )
    ratings.to_csv(processed_dir / "player_value_ratings.csv", index=False)
    return {"players": len(ratings), "rated_players": int(ratings["overall_rating"].notna().sum()), "categories": len(ALL_CATEGORIES)}
