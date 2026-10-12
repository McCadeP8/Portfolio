from __future__ import annotations

from statistics import NormalDist
from pathlib import Path

import numpy as np
import pandas as pd


MODELED_CATEGORIES = [
    "MP", "TS%", "2PT%", "3PT%", "FT%", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TOV"
]
PERCENTAGE_CATEGORIES = {"TS%", "2PT%", "3PT%", "FT%"}
LOWER_IS_BETTER = {"TOV"}
PROFILE_COLUMNS = [
    "minutes_total", "points", "fg_a", "ft_m", "ft_a", "three_m", "three_a", "two_m", "two_a",
    "offensive_rebounds", "defensive_rebounds", "assists", "steals", "blocks", "turnovers",
]


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(0.0, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)


def player_profiles(players: pd.DataFrame) -> pd.DataFrame:
    profiles = pd.DataFrame(index=players.index)
    profiles["minutes_total"] = _numeric(players, "minutes") * _numeric(players, "games")
    for column in PROFILE_COLUMNS[1:]:
        profiles[column] = _numeric(players, column)
    return profiles


def projection_available(players: pd.DataFrame) -> pd.Series:
    """A chemistry score requires an actual playing-time projection."""
    return _numeric(players, "games").gt(0) & _numeric(players, "minutes").gt(0)


def aggregate_categories(profile: pd.Series | dict) -> dict[str, float]:
    value = pd.Series(profile, dtype=float).reindex(PROFILE_COLUMNS, fill_value=0.0)

    def ratio(numerator: str, denominator: str) -> float:
        denominator_value = float(value[denominator])
        return float(value[numerator] / denominator_value) if denominator_value > 0 else np.nan

    ts_denominator = 2.0 * (float(value["fg_a"]) + 0.44 * float(value["ft_a"]))
    return {
        "MP": float(value["minutes_total"]),
        "TS%": float(value["points"] / ts_denominator) if ts_denominator > 0 else np.nan,
        "2PT%": ratio("two_m", "two_a"),
        "3PT%": ratio("three_m", "three_a"),
        "FT%": ratio("ft_m", "ft_a"),
        "PTS": float(value["points"]),
        "OREB": float(value["offensive_rebounds"]),
        "DREB": float(value["defensive_rebounds"]),
        "AST": float(value["assists"]),
        "STL": float(value["steals"]),
        "BLK": float(value["blocks"]),
        "TOV": float(value["turnovers"]),
    }


def _category_rating(value: float, opponents: pd.Series, category: str) -> float:
    valid = pd.to_numeric(opponents, errors="coerce").dropna()
    if not np.isfinite(value) or valid.empty:
        return 5.0
    wins = valid.gt(value) if category in LOWER_IS_BETTER else valid.lt(value)
    ties = valid.eq(value)
    return float(10.0 * (wins.sum() + 0.5 * ties.sum()) / len(valid))


def _ratings_for_profile(profile: pd.Series, opponents: pd.DataFrame) -> dict[str, float]:
    categories = aggregate_categories(profile)
    return {
        category: _category_rating(categories[category], opponents[category], category)
        for category in MODELED_CATEGORIES
    }


def _fast_category_values(profile: np.ndarray) -> np.ndarray:
    values = np.full(len(MODELED_CATEGORIES), np.nan, dtype=float)
    values[0] = profile[0]
    ts_denominator = 2.0 * (profile[2] + 0.44 * profile[4])
    values[1] = profile[1] / ts_denominator if ts_denominator > 0 else np.nan
    values[2] = profile[7] / profile[8] if profile[8] > 0 else np.nan
    values[3] = profile[5] / profile[6] if profile[6] > 0 else np.nan
    values[4] = profile[3] / profile[4] if profile[4] > 0 else np.nan
    values[5:] = profile[[1, 9, 10, 11, 12, 13, 14]]
    return values


def _fast_ratings(profile: np.ndarray, opponents: np.ndarray) -> np.ndarray:
    values = _fast_category_values(profile)
    ratings = np.full(len(MODELED_CATEGORIES), 5.0, dtype=float)
    for index, value in enumerate(values):
        valid = opponents[:, index]
        valid = valid[np.isfinite(valid)]
        if not np.isfinite(value) or len(valid) == 0:
            continue
        wins = valid > value if MODELED_CATEGORIES[index] in LOWER_IS_BETTER else valid < value
        ties = valid == value
        ratings[index] = 10.0 * (wins.sum() + 0.5 * ties.sum()) / len(valid)
    return ratings


def _percentile_10(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().sum() <= 1:
        return pd.Series(5.0, index=values.index)
    return (numeric.rank(method="average", pct=True) * 10.0).clip(0.0, 10.0)


def _chemistry_10(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").fillna(0.0)
    scale = float(numeric.std(ddof=0))
    if not np.isfinite(scale) or scale <= 1e-12:
        return pd.Series(5.0, index=values.index)
    normal = NormalDist()
    return numeric.map(lambda value: 10.0 * normal.cdf(float(value) / scale)).clip(0.0, 10.0)


def _linear_residual(x: pd.Series, y: pd.Series) -> tuple[pd.Series, pd.Series]:
    x_num = pd.to_numeric(x, errors="coerce").fillna(0.0)
    y_num = pd.to_numeric(y, errors="coerce").fillna(0.0)
    if float(x_num.var(ddof=0)) <= 1e-12:
        predicted = pd.Series(float(y_num.mean()), index=y.index)
    else:
        slope, intercept = np.polyfit(x_num.to_numpy(), y_num.to_numpy(), 1)
        predicted = intercept + slope * x_num
    return predicted, y_num - predicted


def _team_profile(players: pd.DataFrame, profiles: pd.DataFrame, team_id: str) -> pd.Series:
    scoring_roster = players["roster_status"].ne("MINORS") & players["fantasy_team_id"].astype(str).eq(str(team_id))
    return profiles.loc[scoring_roster, PROFILE_COLUMNS].sum()


def _weights(categories: pd.DataFrame) -> dict[str, float]:
    configured = categories.set_index("category")["weight"].to_dict()
    return {category: float(configured[category]) for category in MODELED_CATEGORIES}


def build_ratings(players: pd.DataFrame, categories: pd.DataFrame) -> dict[str, pd.DataFrame]:
    players = players.copy().reset_index(drop=True)
    players["fantasy_team_id"] = players["fantasy_team_id"].astype(str)
    players["fantrax_player_id"] = players["fantrax_player_id"].astype(str)
    profiles = player_profiles(players)
    has_projection = projection_available(players)
    weights = _weights(categories)
    modeled_weight = sum(weights.values())
    teams = players[["fantasy_team_id", "fantasy_team_name"]].drop_duplicates().sort_values("fantasy_team_name")

    team_profiles = {
        row.fantasy_team_id: _team_profile(players, profiles, row.fantasy_team_id)
        for row in teams.itertuples(index=False)
    }
    team_values = pd.DataFrame(
        {team_id: aggregate_categories(profile) for team_id, profile in team_profiles.items()}
    ).T.reindex(columns=MODELED_CATEGORIES)

    team_category_rows: list[dict] = []
    for team in teams.itertuples(index=False):
        opponent_ids = team_values.index.difference([team.fantasy_team_id])
        for category in MODELED_CATEGORIES:
            team_category_rows.append({
                "fantasy_team_id": team.fantasy_team_id,
                "fantasy_team_name": team.fantasy_team_name,
                "category": category,
                "projected_value": team_values.loc[team.fantasy_team_id, category],
                "team_category_rating": _category_rating(
                    team_values.loc[team.fantasy_team_id, category],
                    team_values.loc[opponent_ids, category],
                    category,
                ),
            })
    team_category = pd.DataFrame(team_category_rows)

    scoring_roster = players["roster_status"].ne("MINORS")
    neutral_profile = pd.DataFrame(team_profiles).T[PROFILE_COLUMNS].mean().fillna(0.0)
    neutral_ratings = _ratings_for_profile(neutral_profile, team_values)

    player_category_rows: list[dict] = []
    neutral_deltas: dict[int, dict[str, float]] = {}
    neutral_points: dict[int, float] = {}
    for index, player in players.iterrows():
        candidate_profile = neutral_profile + profiles.loc[index, PROFILE_COLUMNS]
        candidate_ratings = _ratings_for_profile(candidate_profile, team_values)
        neutral_deltas[index] = {
            category: candidate_ratings[category] - neutral_ratings[category]
            for category in MODELED_CATEGORIES
        }
        neutral_points[index] = sum(
            neutral_deltas[index][category] * weights[category] / 10.0 for category in MODELED_CATEGORIES
        ) if has_projection.loc[index] else np.nan
        for category in MODELED_CATEGORIES:
            player_category_rows.append({
                "fantrax_player_id": player["fantrax_player_id"],
                "player_name": player["player_name"],
                "fantasy_team_id": player["fantasy_team_id"],
                "fantasy_team_name": player["fantasy_team_name"],
                "roster_status": player["roster_status"],
                "category": category,
                "neutral_category_rating_delta": neutral_deltas[index][category] if has_projection.loc[index] else np.nan,
                "neutral_expected_points_added": neutral_deltas[index][category] * weights[category] / 10.0 if has_projection.loc[index] else np.nan,
            })
    player_category = pd.DataFrame(player_category_rows)
    player_category["player_category_talent_rating"] = player_category.groupby("category")[
        "neutral_expected_points_added"
    ].transform(_percentile_10)

    player_ratings = players[[
        "fantrax_player_id", "player_name", "fantasy_team_id", "fantasy_team_name", "roster_status",
        "roster_position", "eligible_positions",
    ]].copy()
    player_ratings["neutral_expected_points_added"] = pd.Series(neutral_points)
    player_ratings["player_talent_rating"] = _percentile_10(player_ratings["neutral_expected_points_added"])

    neutral_by_player = player_category.pivot(
        index="fantrax_player_id", columns="category", values="neutral_category_rating_delta"
    )
    scoring_ids = set(players.loc[scoring_roster, "fantrax_player_id"])
    team_talent_category_rows: list[dict] = []
    for team in teams.itertuples(index=False):
        ids = players.loc[
            scoring_roster & players["fantasy_team_id"].eq(team.fantasy_team_id), "fantrax_player_id"
        ]
        for category in MODELED_CATEGORIES:
            team_talent_category_rows.append({
                "fantasy_team_id": team.fantasy_team_id,
                "category": category,
                "portable_category_talent": neutral_by_player.reindex(ids)[category].sum(),
            })
    portable_team_category = pd.DataFrame(team_talent_category_rows)
    team_category = team_category.merge(portable_team_category, on=["fantasy_team_id", "category"], how="left")
    team_category["talent_implied_category_rating"] = np.nan
    team_category["category_chemistry_delta"] = np.nan
    team_category["team_category_chemistry_rating"] = np.nan
    for category in MODELED_CATEGORIES:
        mask = team_category["category"].eq(category)
        predicted, residual = _linear_residual(
            team_category.loc[mask, "portable_category_talent"],
            team_category.loc[mask, "team_category_rating"],
        )
        team_category.loc[mask, "talent_implied_category_rating"] = predicted
        team_category.loc[mask, "category_chemistry_delta"] = residual
        team_category.loc[mask, "team_category_chemistry_rating"] = _chemistry_10(residual)

    team_ratings = teams.copy().set_index("fantasy_team_id")
    scoring_player_values = player_ratings[player_ratings["fantrax_player_id"].isin(scoring_ids)].copy()
    team_ratings["portable_talent_points"] = scoring_player_values.groupby("fantasy_team_id")[
        "neutral_expected_points_added"
    ].sum()
    scoring_counts = players.loc[scoring_roster].groupby("fantasy_team_id").size()
    projected_scoring_counts = players.loc[scoring_roster & has_projection].groupby("fantasy_team_id").size()
    team_ratings["scoring_roster_players"] = scoring_counts
    team_ratings["projected_scoring_roster_players"] = projected_scoring_counts.reindex(team_ratings.index, fill_value=0)
    team_ratings["projection_coverage"] = team_ratings["projected_scoring_roster_players"] / team_ratings["scoring_roster_players"]
    team_ratings["team_talent_rating"] = _percentile_10(team_ratings["portable_talent_points"])
    weighted_team = team_category.assign(
        weighted=lambda frame: frame["team_category_rating"] * frame["category"].map(weights)
    ).groupby("fantasy_team_id")["weighted"].sum() / modeled_weight
    team_ratings["team_rating"] = weighted_team
    predicted, residual = _linear_residual(team_ratings["portable_talent_points"], team_ratings["team_rating"])
    team_ratings["talent_implied_team_rating"] = predicted
    team_ratings["team_chemistry_delta"] = residual
    team_ratings["team_chemistry_rating"] = _chemistry_10(residual)
    team_ratings["modeled_weight"] = modeled_weight
    team_ratings = team_ratings.reset_index()

    team_name = teams.set_index("fantasy_team_id")["fantasy_team_name"].to_dict()
    profile_matrix = profiles[PROFILE_COLUMNS].to_numpy(dtype=float)
    team_profile_arrays = {
        team_id: profile.reindex(PROFILE_COLUMNS).to_numpy(dtype=float)
        for team_id, profile in team_profiles.items()
    }
    team_value_matrix = team_values[MODELED_CATEGORIES].to_numpy(dtype=float)
    team_value_index = list(team_values.index)
    opponent_arrays = {
        team_id: np.delete(team_value_matrix, team_value_index.index(team_id), axis=0)
        for team_id in team_value_index
    }
    neutral_delta_arrays = {
        index: np.array([neutral_deltas[index][category] for category in MODELED_CATEGORIES], dtype=float)
        for index in players.index
    }
    weight_array = np.array([weights[category] for category in MODELED_CATEGORIES], dtype=float)
    fit_rows: list[dict] = []
    fit_category_rows: list[dict] = []
    for player_index, player in players.iterrows():
        if not has_projection.loc[player_index]:
            continue
        candidate_id = player["fantrax_player_id"]
        candidate_profile = profile_matrix[player_index]
        for target_team_id, base_profile in team_profile_arrays.items():
            target_scoring_roster = players.index[
                scoring_roster & players["fantasy_team_id"].eq(target_team_id)
            ].tolist()
            own_scoring = [idx for idx in target_scoring_roster if players.loc[idx, "fantrax_player_id"] == candidate_id]
            if own_scoring:
                incumbent_index = own_scoring[0]
                comparison_profile = base_profile - profile_matrix[incumbent_index]
                new_profile = base_profile
                roster_context = "Current roster contribution"
            else:
                comparison_profile = base_profile
                new_profile = base_profile + candidate_profile
                roster_context = "Added to non-minor roster"

            opponents = opponent_arrays[target_team_id]
            comparison_ratings = _fast_ratings(comparison_profile, opponents)
            new_ratings = _fast_ratings(new_profile, opponents)
            contextual_deltas = new_ratings - comparison_ratings
            category_chemistry_values = contextual_deltas - neutral_delta_arrays[player_index]
            contextual_points = float(np.dot(contextual_deltas, weight_array) / 10.0)
            chemistry_bonus = float(np.dot(category_chemistry_values, weight_array) / 10.0)
            for category_index, category in enumerate(MODELED_CATEGORIES):
                contextual_delta = contextual_deltas[category_index]
                category_chemistry = category_chemistry_values[category_index]
                fit_category_rows.append({
                    "fantrax_player_id": candidate_id,
                    "player_name": player["player_name"],
                    "target_team_id": target_team_id,
                    "target_team_name": team_name[target_team_id],
                    "category": category,
                    "contextual_category_rating_delta": contextual_delta,
                    "neutral_category_rating_delta": neutral_deltas[player_index][category],
                    "category_chemistry_delta": category_chemistry,
                })
            projected_team_rating = float(np.dot(new_ratings, weight_array) / modeled_weight)
            fit_rows.append({
                "fantrax_player_id": candidate_id,
                "player_name": player["player_name"],
                "current_team_id": player["fantasy_team_id"],
                "current_team_name": player["fantasy_team_name"],
                "target_team_id": target_team_id,
                "target_team_name": team_name[target_team_id],
                "roster_context": roster_context,
                "contextual_expected_points_added": contextual_points,
                "chemistry_bonus_points": chemistry_bonus,
                "projected_team_rating_after": projected_team_rating,
            })

    player_team_fit = pd.DataFrame(fit_rows)
    player_team_fit["player_team_chemistry_rating"] = _chemistry_10(player_team_fit["chemistry_bonus_points"])
    player_team_category_fit = pd.DataFrame(fit_category_rows)
    player_team_category_fit["player_team_category_chemistry_rating"] = player_team_category_fit.groupby(
        "category"
    )["category_chemistry_delta"].transform(_chemistry_10)

    current_fit = player_team_fit[
        player_team_fit["current_team_id"].eq(player_team_fit["target_team_id"])
    ][["fantrax_player_id", "player_team_chemistry_rating", "chemistry_bonus_points"]]
    player_ratings = player_ratings.merge(current_fit, on="fantrax_player_id", how="left", validate="one_to_one")

    for frame in [team_ratings, team_category, player_ratings, player_category, player_team_fit, player_team_category_fit]:
        rating_columns = [column for column in frame.columns if column.endswith("_rating")]
        frame[rating_columns] = frame[rating_columns].clip(0.0, 10.0).round(2)
        numeric_columns = frame.select_dtypes(include="number").columns.difference(rating_columns)
        frame[numeric_columns] = frame[numeric_columns].round(6)

    return {
        "team_ratings": team_ratings,
        "team_category_ratings": team_category,
        "player_ratings": player_ratings,
        "player_category_ratings": player_category,
        "player_team_fit": player_team_fit,
        "player_team_category_fit": player_team_category_fit,
    }


def write_ratings(processed_dir: Path, categories_path: Path) -> dict[str, int]:
    players = pd.read_csv(processed_dir / "canonical_player_projections.csv", dtype={"fantrax_player_id": str})
    categories = pd.read_csv(categories_path)
    outputs = build_ratings(players, categories)
    for name, frame in outputs.items():
        frame.to_csv(processed_dir / f"{name}.csv", index=False)
    return {name: len(frame) for name, frame in outputs.items()}
