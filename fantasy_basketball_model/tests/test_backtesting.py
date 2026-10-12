import numpy as np
import pandas as pd

from fantasy_basketball.backtesting import _prediction_metrics, _standalone_backtest


def test_leave_one_season_out_predicts_every_observation_once():
    rows = []
    for year in [2021, 2022, 2023]:
        values = np.linspace(-2, 2, 40) + (year - 2022) * 0.05
        for index, value in enumerate(values):
            outcome = int(value > 0)
            if index % 7 == 0:
                outcome = 1 - outcome
            rows.append({
                "Game_ID": f"{year}-{index}",
                "Year": year,
                "Period": index,
                "category": "PTS",
                "adjusted_total": value,
                "won_category": outcome,
            })
    observations = pd.DataFrame(rows)
    predictions = pd.DataFrame(_standalone_backtest(observations, "PTS"))

    assert len(predictions) == len(observations)
    assert sorted(predictions["heldout_year"].unique().tolist()) == [2021, 2022, 2023]
    assert predictions["predicted_probability"].between(0, 1).all()


def test_backtest_metrics_include_probability_accuracy_and_calibration():
    predictions = pd.DataFrame({
        "heldout_year": [2021] * 4,
        "Game_ID": ["1", "2", "3", "4"],
        "outcome": [0, 0, 1, 1],
        "predicted_probability": [0.1, 0.3, 0.7, 0.9],
    })
    metrics = _prediction_metrics(predictions)

    assert metrics["auc"] == 1.0
    assert metrics["brier_score"] < 0.1
    assert metrics["log_loss"] > 0
    assert metrics["calibration_error"] >= 0
