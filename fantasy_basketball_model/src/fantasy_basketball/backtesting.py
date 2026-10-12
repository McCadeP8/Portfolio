from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .counting_models import COUNTING_CATEGORIES, _auc, _sigmoid, category_observations, fit_logistic
from .overall_model import ALL_CATEGORIES, fit_overall_logistic, overall_observations
from .shooting_models import SHOOTING_CATEGORIES, shooting_observations, shooting_team_periods


def _prediction_metrics(predictions: pd.DataFrame) -> dict[str, float | int]:
    y = predictions["outcome"].to_numpy(dtype=int)
    probability = np.clip(predictions["predicted_probability"].to_numpy(dtype=float), 1e-9, 1 - 1e-9)
    calibration = predictions.copy()
    calibration["bin"] = pd.qcut(calibration["predicted_probability"], q=10, duplicates="drop")
    grouped = calibration.groupby("bin", observed=True).agg(
        predicted=("predicted_probability", "mean"),
        observed=("outcome", "mean"),
        observations=("outcome", "size"),
    )
    calibration_error = float(
        np.average(np.abs(grouped["predicted"] - grouped["observed"]), weights=grouped["observations"])
    )
    return {
        "observations": len(predictions),
        "matchups": predictions[["heldout_year", "Game_ID"]].drop_duplicates().shape[0],
        "auc": _auc(y, probability),
        "brier_score": float(np.mean((probability - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(probability) + (1 - y) * np.log(1 - probability))),
        "calibration_error": calibration_error,
    }


def _standalone_backtest(observations: pd.DataFrame, category: str) -> list[dict]:
    predictions: list[dict] = []
    for heldout_year in sorted(pd.to_numeric(observations["Year"], errors="coerce").dropna().unique()):
        training = observations[observations["Year"].ne(heldout_year)]
        testing = observations[observations["Year"].eq(heldout_year)]
        result = fit_logistic(training)
        probability = _sigmoid(
            float(result["intercept"])
            + float(result["slope"]) * testing["adjusted_total"].to_numpy(dtype=float)
        )
        predictions.extend({
            "model": "Category",
            "category": category,
            "heldout_year": int(heldout_year),
            "Game_ID": str(row.Game_ID),
            "outcome": int(row.won_category),
            "predicted_probability": float(chance),
        } for row, chance in zip(testing.itertuples(index=False), probability))
    return predictions


def _overall_backtest(observations: pd.DataFrame) -> list[dict]:
    predictions: list[dict] = []
    for heldout_year in sorted(pd.to_numeric(observations["Year"], errors="coerce").dropna().unique()):
        training = observations[observations["Year"].ne(heldout_year)]
        testing = observations[observations["Year"].eq(heldout_year)]
        summary, coefficients, _ = fit_overall_logistic(training)
        coefficients = coefficients.set_index("category")
        linear = np.full(len(testing), float(summary["intercept_standardized"]))
        for category in ALL_CATEGORIES:
            coefficient = coefficients.loc[category]
            standardized = (
                testing[category].to_numpy(dtype=float) - float(coefficient["mean"])
            ) / float(coefficient["standard_deviation"])
            linear += float(coefficient["coefficient_per_sd"]) * standardized
        probability = _sigmoid(linear)
        predictions.extend({
            "model": "Overall",
            "category": "Overall",
            "heldout_year": int(heldout_year),
            "Game_ID": str(row.Game_ID),
            "outcome": int(row.won_matchup),
            "predicted_probability": float(chance),
        } for row, chance in zip(testing.itertuples(index=False), probability))
    return predictions


def season_backtests(
    matchups: pd.DataFrame, team_stats: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prediction_rows: list[dict] = []
    for category in COUNTING_CATEGORIES:
        prediction_rows.extend(_standalone_backtest(category_observations(matchups, category), category))

    shooting_periods, _ = shooting_team_periods(team_stats)
    for category in SHOOTING_CATEGORIES:
        observations = shooting_observations(matchups, shooting_periods, category)
        prediction_rows.extend(_standalone_backtest(observations, category))

    overall = overall_observations(matchups, team_stats)
    prediction_rows.extend(_overall_backtest(overall))
    predictions = pd.DataFrame(prediction_rows)

    fold_rows = []
    for (model, category, heldout_year), fold in predictions.groupby(
        ["model", "category", "heldout_year"], sort=False
    ):
        fold_rows.append({
            "model": model,
            "category": category,
            "heldout_year": int(heldout_year),
            **_prediction_metrics(fold),
        })
    folds = pd.DataFrame(fold_rows)

    summary_rows = []
    calibration_rows = []
    for (model, category), group in predictions.groupby(["model", "category"], sort=False):
        category_folds = folds[(folds["model"].eq(model)) & (folds["category"].eq(category))]
        summary_rows.append({
            "model": model,
            "category": category,
            "seasons": group["heldout_year"].nunique(),
            **_prediction_metrics(group),
            "auc_fold_min": category_folds["auc"].min(),
            "auc_fold_max": category_folds["auc"].max(),
            "brier_fold_min": category_folds["brier_score"].min(),
            "brier_fold_max": category_folds["brier_score"].max(),
        })
        calibrated = group.copy()
        calibrated["bin"] = pd.qcut(calibrated["predicted_probability"], q=10, duplicates="drop")
        bins = calibrated.groupby("bin", observed=True).agg(
            predicted_probability=("predicted_probability", "mean"),
            observed_win_rate=("outcome", "mean"),
            observations=("outcome", "size"),
        ).reset_index(drop=True)
        bins.insert(0, "category", category)
        bins.insert(0, "model", model)
        bins.insert(2, "bin", np.arange(1, len(bins) + 1))
        calibration_rows.extend(bins.to_dict("records"))

    summary = pd.DataFrame(summary_rows)
    calibration = pd.DataFrame(calibration_rows)
    return summary, folds, calibration, predictions


def write_season_backtests(processed_dir: Path, raw_dir: Path) -> dict[str, int]:
    matchups = pd.read_parquet(processed_dir / "historical_matchups.parquet")
    team_stats = pd.read_parquet(raw_dir / "sbc_streamlit" / "all_team_stats_history.parquet")
    summary, folds, calibration, predictions = season_backtests(matchups, team_stats)
    summary.to_csv(processed_dir / "season_backtest_summary.csv", index=False)
    folds.to_csv(processed_dir / "season_backtest_folds.csv", index=False)
    calibration.to_csv(processed_dir / "season_backtest_calibration.csv", index=False)
    predictions.to_csv(processed_dir / "season_backtest_predictions.csv", index=False)
    return {
        "models": len(summary),
        "folds": len(folds),
        "predictions": len(predictions),
        "seasons": predictions["heldout_year"].nunique(),
    }
