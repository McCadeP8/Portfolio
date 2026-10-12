from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


COUNTING_CATEGORIES = ["MP", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "+/-"]
STANDARD_NBA_GAMES = 24.93


def standardize_total(value: pd.Series, nba_games: pd.Series, standard_games: float = STANDARD_NBA_GAMES) -> pd.Series:
    games = pd.to_numeric(nba_games, errors="coerce").replace(0, np.nan)
    return pd.to_numeric(value, errors="coerce").div(games).mul(standard_games)


def category_observations(matchups: pd.DataFrame, category: str) -> pd.DataFrame:
    winner = matchups[f"{category}_winner"]
    decided = winner.isin(["A", "B"])
    source = matchups.loc[decided]
    rows = []
    for side in ["A", "B"]:
        rows.append(pd.DataFrame({
            "Game_ID": source["Game_ID"].astype(str),
            "Year": source["Year"],
            "Period": source["Period"],
            "category": category,
            "adjusted_total": standardize_total(
                source[f"{category}_{side}"], source["nba_games_in_period"]
            ),
            "won_category": source[f"{category}_winner"].eq(side).astype(int),
        }))
    observations = pd.concat(rows, ignore_index=True)
    return observations.replace([np.inf, -np.inf], np.nan).dropna(subset=["adjusted_total"])


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return np.where(
        value >= 0,
        1.0 / (1.0 + np.exp(-value)),
        np.exp(value) / (1.0 + np.exp(value)),
    )


def _auc(y: np.ndarray, probability: np.ndarray) -> float:
    ranks = pd.Series(probability).rank(method="average").to_numpy()
    positives = y == 1
    n_positive = int(positives.sum())
    n_negative = int((~positives).sum())
    if n_positive == 0 or n_negative == 0:
        return np.nan
    return float((ranks[positives].sum() - n_positive * (n_positive + 1) / 2) / (n_positive * n_negative))


def fit_logistic(observations: pd.DataFrame, max_iterations: int = 100) -> dict:
    x_raw = observations["adjusted_total"].to_numpy(dtype=float)
    y = observations["won_category"].to_numpy(dtype=float)
    center = float(x_raw.mean())
    scale = float(x_raw.std()) or 1.0
    x_standard = (x_raw - center) / scale
    design = np.column_stack([np.ones(len(x_standard)), x_standard])
    beta = np.zeros(2, dtype=float)

    for _ in range(max_iterations):
        probability = np.clip(_sigmoid(design @ beta), 1e-9, 1 - 1e-9)
        weights = probability * (1 - probability)
        information = design.T @ (design * weights[:, None])
        score = design.T @ (y - probability)
        step = np.linalg.solve(information + np.eye(2) * 1e-10, score)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-10:
            break

    probability = np.clip(_sigmoid(design @ beta), 1e-9, 1 - 1e-9)
    weights = probability * (1 - probability)
    bread = np.linalg.inv(design.T @ (design * weights[:, None]) + np.eye(2) * 1e-10)
    scores = design * (y - probability)[:, None]
    cluster_scores = pd.DataFrame(scores).assign(cluster=observations["Game_ID"].to_numpy()).groupby("cluster")[[0, 1]].sum().to_numpy()
    meat = cluster_scores.T @ cluster_scores
    clusters = len(cluster_scores)
    correction = clusters / (clusters - 1) * (len(y) - 1) / (len(y) - design.shape[1])
    covariance_standard = bread @ meat @ bread * correction

    intercept = float(beta[0] - beta[1] * center / scale)
    slope = float(beta[1] / scale)
    transform = np.array([[1.0, -center / scale], [0.0, 1.0 / scale]])
    covariance_raw = transform @ covariance_standard @ transform.T
    intercept_se = float(np.sqrt(max(covariance_raw[0, 0], 0)))
    slope_se = float(np.sqrt(max(covariance_raw[1, 1], 0)))
    threshold = float(-intercept / slope) if abs(slope) > 1e-12 else np.nan
    log_likelihood = float(np.sum(y * np.log(probability) + (1 - y) * np.log(1 - probability)))
    null_probability = float(y.mean())
    null_log_likelihood = float(np.sum(y * np.log(null_probability) + (1 - y) * np.log(1 - null_probability)))

    return {
        "intercept": intercept,
        "intercept_se": intercept_se,
        "slope": slope,
        "slope_se": slope_se,
        "odds_ratio_per_unit": float(np.exp(np.clip(slope, -50, 50))),
        "threshold_50": threshold,
        "auc": _auc(y.astype(int), probability),
        "brier_score": float(np.mean((probability - y) ** 2)),
        "mcfadden_r2": float(1 - log_likelihood / null_log_likelihood),
        "observations": len(y),
        "matchups": observations["Game_ID"].nunique(),
    }


def fit_counting_models(matchups: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    model_rows = []
    curve_rows = []
    bin_rows = []
    for category in COUNTING_CATEGORIES:
        observations = category_observations(matchups, category)
        result = fit_logistic(observations)
        model_rows.append({"category": category, "standard_nba_games": STANDARD_NBA_GAMES, **result})

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

    return pd.DataFrame(model_rows), pd.DataFrame(curve_rows), pd.DataFrame(bin_rows)


def write_counting_models(processed_dir: Path) -> dict[str, int]:
    matchups = pd.read_parquet(processed_dir / "historical_matchups.parquet")
    models, curves, bins = fit_counting_models(matchups)
    models.to_csv(processed_dir / "counting_logistic_models.csv", index=False)
    curves.to_csv(processed_dir / "counting_logistic_curves.csv", index=False)
    bins.to_csv(processed_dir / "counting_logistic_bins.csv", index=False)
    return {"models": len(models), "curves": len(curves), "bins": len(bins)}
