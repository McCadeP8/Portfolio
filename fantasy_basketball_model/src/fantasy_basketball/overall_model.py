from __future__ import annotations

from math import erfc, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from .counting_models import COUNTING_CATEGORIES, STANDARD_NBA_GAMES, _auc, _sigmoid, standardize_total
from .shooting_models import SHOOTING_CATEGORIES, shooting_team_periods


ALL_CATEGORIES = ["MP", "TS%", "2PT%", "3PT%", "FT%", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "+/-"]


def overall_observations(matchups: pd.DataFrame, team_stats: pd.DataFrame) -> pd.DataFrame:
    decided = matchups["matchup_winner"].isin(["A", "B"])
    source = matchups.loc[decided]
    shooting_periods, _ = shooting_team_periods(team_stats)
    shooting_columns = [f"{category}_points_gained" for category in SHOOTING_CATEGORIES]
    rows = []
    for side in ["A", "B"]:
        frame = source[["Game_ID", "Year", "Period", f"Team{side}", "nba_games_in_period", "matchup_winner"]].copy()
        frame = frame.rename(columns={f"Team{side}": "Team"})
        for category in COUNTING_CATEGORIES:
            frame[category] = standardize_total(
                source[f"{category}_{side}"].reset_index(drop=True),
                source["nba_games_in_period"].reset_index(drop=True),
            ).to_numpy()
        frame = frame.merge(
            shooting_periods[["Year", "Period", "Team", *shooting_columns]],
            on=["Year", "Period", "Team"], how="left", validate="many_to_one",
        )
        for category in SHOOTING_CATEGORIES:
            frame[category] = standardize_total(
                frame[f"{category}_points_gained"], frame["nba_games_in_period"]
            )
        frame["won_matchup"] = frame["matchup_winner"].eq(side).astype(int)
        rows.append(frame[["Game_ID", "Year", "Period", "Team", "won_matchup", *ALL_CATEGORIES]])
    return pd.concat(rows, ignore_index=True).replace([np.inf, -np.inf], np.nan).dropna(subset=ALL_CATEGORIES)


def fit_overall_logistic(observations: pd.DataFrame, max_iterations: int = 100) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    x_raw = observations[ALL_CATEGORIES].to_numpy(dtype=float)
    y = observations["won_matchup"].to_numpy(dtype=float)
    centers = x_raw.mean(axis=0)
    scales = x_raw.std(axis=0)
    scales = np.where(scales > 1e-12, scales, 1.0)
    x_standard = (x_raw - centers) / scales
    design = np.column_stack([np.ones(len(x_standard)), x_standard])
    beta = np.zeros(design.shape[1], dtype=float)

    for _ in range(max_iterations):
        probability = np.clip(_sigmoid(design @ beta), 1e-9, 1 - 1e-9)
        weights = probability * (1 - probability)
        information = design.T @ (design * weights[:, None])
        score = design.T @ (y - probability)
        step = np.linalg.solve(information + np.eye(design.shape[1]) * 1e-9, score)
        beta += step
        if np.max(np.abs(step)) < 1e-9:
            break

    probability = np.clip(_sigmoid(design @ beta), 1e-9, 1 - 1e-9)
    weights = probability * (1 - probability)
    bread = np.linalg.inv(design.T @ (design * weights[:, None]) + np.eye(design.shape[1]) * 1e-9)
    scores = design * (y - probability)[:, None]
    score_frame = pd.DataFrame(scores)
    score_frame["cluster"] = observations["Game_ID"].astype(str).to_numpy()
    cluster_scores = score_frame.groupby("cluster").sum().to_numpy()
    meat = cluster_scores.T @ cluster_scores
    clusters = len(cluster_scores)
    correction = clusters / (clusters - 1) * (len(y) - 1) / (len(y) - design.shape[1])
    covariance = bread @ meat @ bread * correction
    standard_errors = np.sqrt(np.maximum(np.diag(covariance), 0))

    log_likelihood = float(np.sum(y * np.log(probability) + (1 - y) * np.log(1 - probability)))
    null_probability = float(y.mean())
    null_log_likelihood = float(np.sum(y * np.log(null_probability) + (1 - y) * np.log(1 - null_probability)))
    summary = {
        "intercept_standardized": float(beta[0]),
        "intercept_se": float(standard_errors[0]),
        "auc": _auc(y.astype(int), probability),
        "brier_score": float(np.mean((probability - y) ** 2)),
        "mcfadden_r2": float(1 - log_likelihood / null_log_likelihood),
        "observations": len(y),
        "matchups": observations["Game_ID"].nunique(),
        "standard_nba_games": STANDARD_NBA_GAMES,
    }

    coefficient_rows = []
    for index, category in enumerate(ALL_CATEGORIES, start=1):
        estimate = float(beta[index])
        se = float(standard_errors[index])
        z_value = estimate / se if se > 0 else np.nan
        p_value = erfc(abs(z_value) / sqrt(2)) if np.isfinite(z_value) else np.nan
        coefficient_rows.append({
            "category": category,
            "coefficient_per_sd": estimate,
            "clustered_se": se,
            "odds_ratio_per_sd": float(np.exp(np.clip(estimate, -50, 50))),
            "ci_95_low": float(np.exp(np.clip(estimate - 1.96 * se, -50, 50))),
            "ci_95_high": float(np.exp(np.clip(estimate + 1.96 * se, -50, 50))),
            "z_value": z_value,
            "p_value": p_value,
            "mean": float(centers[index - 1]),
            "standard_deviation": float(scales[index - 1]),
        })

    calibration_source = pd.DataFrame({"predicted_probability": probability, "won_matchup": y})
    calibration_source["bin"] = pd.qcut(calibration_source["predicted_probability"], q=12, duplicates="drop")
    calibration = calibration_source.groupby("bin", observed=True).agg(
        predicted_probability=("predicted_probability", "mean"),
        observed_win_rate=("won_matchup", "mean"),
        observations=("won_matchup", "size"),
    ).reset_index(drop=True)
    return summary, pd.DataFrame(coefficient_rows), calibration


def write_overall_model(processed_dir: Path, raw_dir: Path) -> dict[str, int]:
    matchups = pd.read_parquet(processed_dir / "historical_matchups.parquet")
    team_stats = pd.read_parquet(raw_dir / "sbc_streamlit" / "all_team_stats_history.parquet")
    observations = overall_observations(matchups, team_stats)
    summary, coefficients, calibration = fit_overall_logistic(observations)
    pd.DataFrame([summary]).to_csv(processed_dir / "overall_logistic_model.csv", index=False)
    coefficients.to_csv(processed_dir / "overall_logistic_coefficients.csv", index=False)
    calibration.to_csv(processed_dir / "overall_logistic_calibration.csv", index=False)
    return {"models": 1, "coefficients": len(coefficients), "bins": len(calibration), "matchups": summary["matchups"]}
