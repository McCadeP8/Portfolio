import numpy as np
import pandas as pd

from fantasy_basketball.counting_models import fit_logistic, standardize_total


def test_standardize_total_uses_24_93_game_period():
    result = standardize_total(pd.Series([200.0]), pd.Series([25.0]))
    assert result.iloc[0] == 200.0 / 25.0 * 24.93


def test_logistic_fit_recovers_positive_relationship():
    x = np.linspace(-3, 3, 400)
    probability = 1 / (1 + np.exp(-1.5 * x))
    y = (np.arange(400) / 399 < probability).astype(int)
    observations = pd.DataFrame({
        "Game_ID": [f"g{index // 2}" for index in range(400)],
        "adjusted_total": x,
        "won_category": y,
    })
    result = fit_logistic(observations)
    assert result["slope"] > 0
    assert 0 <= result["auc"] <= 1
    assert result["observations"] == 400
