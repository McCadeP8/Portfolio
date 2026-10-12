from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .counting_models import _sigmoid, fit_logistic
from .overall_model import ALL_CATEGORIES, overall_observations
from .player_value import player_period_contributions


def category_probabilities(values, counting_models, shooting_models):
    models = pd.concat([counting_models, shooting_models], ignore_index=True).set_index("category")
    probabilities = pd.DataFrame(index=values.index)
    for category in ALL_CATEGORIES:
        model = models.loc[category]
        total = pd.to_numeric(values[category], errors="coerce")
        probabilities[category] = _sigmoid(
            float(model["intercept"]) + float(model["slope"]) * total.to_numpy(dtype=float)
        )
    return probabilities


def fit_independent_score_model(
    observations, counting_models, shooting_models, category_weights
):
    probabilities = category_probabilities(
        observations[ALL_CATEGORIES], counting_models, shooting_models
    )
    expected_score = probabilities.mul(category_weights.reindex(ALL_CATEGORIES), axis=1).sum(axis=1)
    calibration = pd.DataFrame({
        "Game_ID": observations["Game_ID"].astype(str),
        "adjusted_total": expected_score,
        "won_category": observations["won_matchup"].astype(int),
    })
    return fit_logistic(calibration)


def chemistry_reference_residuals(
    observations,
    counting_models,
    shooting_models,
    overall_model,
    overall_coefficients,
    category_weights,
    independent_model,
):
    category_chances = category_probabilities(
        observations[ALL_CATEGORIES], counting_models, shooting_models
    )
    expected_score = category_chances.mul(
        category_weights.reindex(ALL_CATEGORIES), axis=1
    ).sum(axis=1)
    independent_probability = _sigmoid(
        float(independent_model["intercept"])
        + float(independent_model["slope"]) * expected_score.to_numpy(dtype=float)
    )
    coefficients = overall_coefficients.set_index("category")
    linear = np.full(len(observations), float(overall_model["intercept_standardized"]))
    for category in ALL_CATEGORIES:
        coefficient = coefficients.loc[category]
        standardized = (
            pd.to_numeric(observations[category], errors="coerce").to_numpy(dtype=float)
            - float(coefficient["mean"])
        ) / float(coefficient["standard_deviation"])
        linear += float(coefficient["coefficient_per_sd"]) * standardized
    overall_probability = _sigmoid(linear)
    return pd.Series(
        100 * (overall_probability - independent_probability),
        index=observations.index,
        name="chemistry_probability_points",
    )


def reference_percentile(values, reference):
    reference_values = np.sort(pd.to_numeric(reference, errors="coerce").dropna().to_numpy())
    if len(reference_values) == 0:
        return pd.Series(np.nan, index=values.index)
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.map(
        lambda value: 10 * np.searchsorted(reference_values, value, side="right") / len(reference_values)
        if pd.notna(value)
        else np.nan
    ).clip(0, 100)


def _profile_metrics(
    profile,
    league_means,
    standalone_models,
    overall_model,
    overall_coefficients,
    category_weights,
    independent_model,
):
    category_chances = {}
    for category in ALL_CATEGORIES:
        model = standalone_models.loc[category]
        adjusted_value = (
            float(profile[category])
            - float(league_means[category])
            + float(model["threshold_50"])
        )
        category_chances[category] = float(_sigmoid(np.array([
            float(model["intercept"]) + float(model["slope"]) * adjusted_value
        ]))[0])
    expected_score = sum(
        category_chances[category] * float(category_weights[category])
        for category in ALL_CATEGORIES
    )
    independent_probability = float(_sigmoid(np.array([
        float(independent_model["intercept"])
        + float(independent_model["slope"]) * expected_score
    ]))[0])
    linear = float(overall_model["intercept_standardized"])
    for category in ALL_CATEGORIES:
        coefficient = overall_coefficients.loc[category]
        linear += float(coefficient["coefficient_per_sd"]) * (
            float(profile[category]) - float(league_means[category])
        ) / float(coefficient["standard_deviation"])
    skill_probability = float(_sigmoid(np.array([linear]))[0])
    return {
        "expected_score": expected_score,
        "skill_probability": skill_probability,
        "chemistry_residual_pp": 100 * (skill_probability - independent_probability),
    }


def projected_player_team_chemistry(
    players,
    shooting,
    team_outlook,
    counting_models,
    shooting_models,
    overall_model,
    overall_coefficients,
    category_weights,
    independent_model,
):
    contributions = player_period_contributions(players, shooting)
    contributions[ALL_CATEGORIES] = contributions[ALL_CATEGORIES].fillna(0) * 0.5
    contributions["fantrax_player_id"] = contributions["fantrax_player_id"].astype(str)
    contribution_by_id = contributions.set_index("fantrax_player_id")
    player_lookup = players.copy()
    player_lookup["fantrax_player_id"] = player_lookup["fantrax_player_id"].astype(str)
    player_lookup["fantasy_team_id"] = player_lookup["fantasy_team_id"].astype(str)
    player_lookup = player_lookup.set_index("fantrax_player_id")
    eligible = (
        pd.to_numeric(player_lookup["games"], errors="coerce").fillna(0).gt(0)
        & pd.to_numeric(player_lookup["minutes"], errors="coerce").fillna(0).gt(0)
    )

    profiles = team_outlook.copy()
    profiles["fantasy_team_id"] = profiles["fantasy_team_id"].astype(str)
    profiles = profiles.set_index("fantasy_team_id")
    league_means = profiles[ALL_CATEGORIES].mean()
    standalone_models = pd.concat(
        [counting_models, shooting_models], ignore_index=True
    ).set_index("category")
    coefficients = overall_coefficients.set_index("category")
    weights = category_weights.reindex(ALL_CATEGORIES).astype(float)
    rows = []
    for target_team_id, team in profiles.iterrows():
        base_profile = team[ALL_CATEGORIES].astype(float)
        for player_id, player in player_lookup.iterrows():
            if not bool(eligible.loc[player_id]):
                continue
            contribution = contribution_by_id.loc[player_id, ALL_CATEGORIES].astype(float)
            current_nonminor = (
                str(player["fantasy_team_id"]) == str(target_team_id)
                and str(player["roster_status"]) != "MINORS"
            )
            if current_nonminor:
                before_profile = base_profile - contribution
                after_profile = base_profile
                context = "Current Roster"
            else:
                before_profile = base_profile
                after_profile = base_profile + contribution
                context = "Potential Addition"
            before = _profile_metrics(
                before_profile,
                league_means,
                standalone_models,
                overall_model,
                coefficients,
                weights,
                independent_model,
            )
            after = _profile_metrics(
                after_profile,
                league_means,
                standalone_models,
                overall_model,
                coefficients,
                weights,
                independent_model,
            )
            rows.append({
                "fantrax_player_id": player_id,
                "player_name": player["player_name"],
                "current_team_id": str(player["fantasy_team_id"]),
                "current_team_name": player["fantasy_team_name"],
                "target_team_id": str(target_team_id),
                "target_team_name": team["fantasy_team_name"],
                "context": context,
                "skill_impact_pp": 100 * (
                    after["skill_probability"] - before["skill_probability"]
                ),
                "expected_score_impact": after["expected_score"] - before["expected_score"],
                "chemistry_impact_pp": (
                    after["chemistry_residual_pp"] - before["chemistry_residual_pp"]
                ),
            })
    result = pd.DataFrame(rows)
    result["player_chemistry"] = result["chemistry_impact_pp"].rank(
        method="average", pct=True
    ) * 10
    # Recommendation fit asks where this specific player fits unusually well or
    # poorly compared with the other 29 destinations. Ranking within player—not
    # within team—prevents general player quality from reproducing the same board
    # for every franchise.
    result["chemistry_fit_percentile"] = result.groupby("fantrax_player_id")[
        "chemistry_impact_pp"
    ].rank(method="average", pct=True) * 10
    result["skill_fit_percentile"] = result.groupby("fantrax_player_id")[
        "skill_impact_pp"
    ].rank(method="average", pct=True) * 10
    result["team_fit_score"] = (
        0.65 * result["chemistry_fit_percentile"]
        + 0.35 * result["skill_fit_percentile"]
    )
    return result


def projected_teammate_chemistry(
    players,
    shooting,
    team_outlook,
    counting_models,
    shooting_models,
    overall_model,
    overall_coefficients,
    category_weights,
    independent_model,
):
    """Measure pairwise chemistry as a second difference on the team residual.

    For focal player A and teammate B, the interaction is
    chemistry(A+B) - chemistry(A) - chemistry(B) + chemistry(neither).
    It is positive when the pair's category shapes work better together than the
    sum of their standalone effects. Minors are evaluated as potential call-ups;
    candidate teammates are current projected non-minor players.
    """
    contributions = player_period_contributions(players, shooting)
    contributions[ALL_CATEGORIES] = contributions[ALL_CATEGORIES].fillna(0) * 0.5
    contributions["fantrax_player_id"] = contributions["fantrax_player_id"].astype(str)
    contributions["fantasy_team_id"] = contributions["fantasy_team_id"].astype(str)
    eligible = (
        pd.to_numeric(players["games"], errors="coerce").fillna(0).gt(0)
        & pd.to_numeric(players["minutes"], errors="coerce").fillna(0).gt(0)
    ).to_numpy()
    contributions = contributions.loc[eligible].copy()
    profiles = team_outlook.copy()
    profiles["fantasy_team_id"] = profiles["fantasy_team_id"].astype(str)
    profiles = profiles.set_index("fantasy_team_id")
    league_means = profiles[ALL_CATEGORIES].mean()
    standalone_models = pd.concat([counting_models, shooting_models], ignore_index=True).set_index("category")
    coefficients = overall_coefficients.set_index("category")
    weights = category_weights.reindex(ALL_CATEGORIES).astype(float)

    def residual(profile):
        return _profile_metrics(
            profile, league_means, standalone_models, overall_model,
            coefficients, weights, independent_model,
        )["chemistry_residual_pp"]

    rows = []
    for team_id, team_players in contributions.groupby("fantasy_team_id"):
        if team_id not in profiles.index:
            continue
        base = profiles.loc[team_id, ALL_CATEGORIES].astype(float)
        teammates = team_players[team_players["roster_status"].ne("MINORS")]
        for _, focal in team_players.iterrows():
            focal_value = focal[ALL_CATEGORIES].astype(float)
            focal_in_base = str(focal["roster_status"]) != "MINORS"
            for _, teammate in teammates.iterrows():
                if str(teammate["fantrax_player_id"]) == str(focal["fantrax_player_id"]):
                    continue
                teammate_value = teammate[ALL_CATEGORIES].astype(float)
                background = base - teammate_value - (focal_value if focal_in_base else 0)
                interaction = (
                    residual(background + focal_value + teammate_value)
                    - residual(background + focal_value)
                    - residual(background + teammate_value)
                    + residual(background)
                )
                rows.append({
                    "fantrax_player_id": str(focal["fantrax_player_id"]),
                    "player_name": focal["player_name"],
                    "fantasy_team_id": team_id,
                    "fantasy_team_name": focal["fantasy_team_name"],
                    "teammate_player_id": str(teammate["fantrax_player_id"]),
                    "teammate_name": teammate["player_name"],
                    "pair_chemistry_impact_pp": interaction,
                })
    result = pd.DataFrame(rows)
    if len(result):
        result["pair_chemistry_rating"] = result.groupby("fantrax_player_id")[
            "pair_chemistry_impact_pp"
        ].rank(method="average", pct=True) * 10
    return result


def projected_team_outlook(
    players,
    shooting,
    counting_models,
    shooting_models,
    overall_model,
    overall_coefficients,
    category_weights,
    independent_model,
    chemistry_reference,
):
    contributions = player_period_contributions(players, shooting)
    # Player ratings intentionally ask what one player contributes over 24.93 / 15
    # games. A full projected roster instead receives the schedule exposure of one
    # NBA team in a 24.93-game league-wide period: 24.93 / 30. Rescale the portable
    # player contribution by 15 / 30 before aggregating the roster.
    contributions[ALL_CATEGORIES] = contributions[ALL_CATEGORIES] * 0.5
    scoring = contributions[contributions["roster_status"].ne("MINORS")].copy()
    values = scoring.groupby(["fantasy_team_id", "fantasy_team_name"], as_index=False)[
        ALL_CATEGORIES
    ].sum()
    values["fantasy_team_id"] = values["fantasy_team_id"].astype(str)
    indexed = values.set_index("fantasy_team_id")

    standalone_models = pd.concat(
        [counting_models, shooting_models], ignore_index=True
    ).set_index("category")
    # "Average opponent" means the average current projected SBCFBL team. Center
    # the 30-team projection pool on each historical model's 50% benchmark while
    # retaining the full between-team spread from the projections.
    category_inputs = indexed[ALL_CATEGORIES].copy()
    for category in ALL_CATEGORIES:
        category_inputs[category] = (
            category_inputs[category]
            - category_inputs[category].mean()
            + float(standalone_models.loc[category, "threshold_50"])
        )
    probabilities = category_probabilities(
        category_inputs, counting_models, shooting_models
    )
    for category in ALL_CATEGORIES:
        indexed[f"probability_{category}"] = probabilities[category]
    weights = category_weights.reindex(ALL_CATEGORIES).astype(float)
    indexed["expected_score"] = probabilities.mul(weights, axis=1).sum(axis=1)
    indexed["categories_favored"] = probabilities.gt(0.5).sum(axis=1)
    indexed["independent_win_probability"] = _sigmoid(
        float(independent_model["intercept"])
        + float(independent_model["slope"]) * indexed["expected_score"].to_numpy(dtype=float)
    )

    coefficients = overall_coefficients.set_index("category")
    linear = np.full(len(indexed), float(overall_model["intercept_standardized"]))
    for category in ALL_CATEGORIES:
        coefficient = coefficients.loc[category]
        standardized = (
            indexed[category].to_numpy(dtype=float) - float(indexed[category].mean())
        ) / float(coefficient["standard_deviation"])
        linear += float(coefficient["coefficient_per_sd"]) * standardized
    indexed["skill_probability"] = _sigmoid(linear)
    indexed["chemistry_probability_points"] = 100 * (
        indexed["skill_probability"] - indexed["independent_win_probability"]
    )
    indexed["chemistry_score_points"] = 413 * (
        indexed["skill_probability"] - indexed["independent_win_probability"]
    )
    indexed["chemistry_level"] = reference_percentile(
        indexed["chemistry_probability_points"], chemistry_reference
    )
    indexed["league_rank"] = indexed["skill_probability"].rank(
        method="min", ascending=False
    ).astype(int)
    return indexed.reset_index()


def write_team_outlook(processed_dir: Path, raw_dir: Path, categories_path: Path):
    players = pd.read_csv(
        processed_dir / "canonical_player_projections.csv", dtype={"fantrax_player_id": str}
    )
    shooting = pd.read_csv(
        processed_dir / "player_shooting_points_gained.csv", dtype={"fantrax_player_id": str}
    )
    counting_models = pd.read_csv(processed_dir / "counting_logistic_models.csv")
    shooting_models = pd.read_csv(processed_dir / "shooting_logistic_models.csv")
    overall_model = pd.read_csv(processed_dir / "overall_logistic_model.csv").iloc[0]
    overall_coefficients = pd.read_csv(processed_dir / "overall_logistic_coefficients.csv")
    category_weights = pd.read_csv(categories_path).set_index("category")["weight"]

    matchups = pd.read_parquet(processed_dir / "historical_matchups.parquet")
    team_stats = pd.read_parquet(raw_dir / "sbc_streamlit" / "all_team_stats_history.parquet")
    observations = overall_observations(matchups, team_stats)
    independent_model = fit_independent_score_model(
        observations, counting_models, shooting_models, category_weights
    )
    pd.DataFrame([independent_model]).to_csv(
        processed_dir / "independent_score_logistic_model.csv", index=False
    )
    chemistry_reference = chemistry_reference_residuals(
        observations,
        counting_models,
        shooting_models,
        overall_model,
        overall_coefficients,
        category_weights,
        independent_model,
    )
    pd.DataFrame({
        "Game_ID": observations["Game_ID"].astype(str),
        "chemistry_probability_points": chemistry_reference,
    }).to_csv(processed_dir / "historical_chemistry_reference.csv", index=False)

    outlook = projected_team_outlook(
        players,
        shooting,
        counting_models,
        shooting_models,
        overall_model,
        overall_coefficients,
        category_weights,
        independent_model,
        chemistry_reference,
    )
    outlook.to_csv(processed_dir / "team_outlook.csv", index=False)
    player_chemistry = projected_player_team_chemistry(
        players,
        shooting,
        outlook,
        counting_models,
        shooting_models,
        overall_model,
        overall_coefficients,
        category_weights,
        independent_model,
    )
    player_chemistry.to_csv(processed_dir / "player_team_chemistry.csv", index=False)
    teammate_chemistry = projected_teammate_chemistry(
        players,
        shooting,
        outlook,
        counting_models,
        shooting_models,
        overall_model,
        overall_coefficients,
        category_weights,
        independent_model,
    )
    teammate_chemistry.to_csv(processed_dir / "player_teammate_chemistry.csv", index=False)
    return {
        "teams": len(outlook),
        "categories": len(ALL_CATEGORIES),
        "player_team_fits": len(player_chemistry),
        "player_teammate_pairs": len(teammate_chemistry),
    }
