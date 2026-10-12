import numpy as np
import pandas as pd

from fantasy_basketball.overall_model import ALL_CATEGORIES, fit_overall_logistic


def test_overall_logistic_uses_all_thirteen_inputs():
    rng = np.random.default_rng(7)
    size = 600
    frame = pd.DataFrame(rng.normal(size=(size, len(ALL_CATEGORIES))), columns=ALL_CATEGORIES)
    probability = 1 / (1 + np.exp(-(1.4 * frame["PTS"] - 1.1 * frame["TOV"])))
    frame["won_matchup"] = rng.binomial(1, probability)
    frame["Game_ID"] = [f"g{index // 2}" for index in range(size)]
    summary, coefficients, calibration = fit_overall_logistic(frame)
    effects = coefficients.set_index("category")["coefficient_per_sd"]
    assert len(coefficients) == 13
    assert effects["PTS"] > 0
    assert effects["TOV"] < 0
    assert 0.5 < summary["auc"] <= 1
    assert len(calibration) == 12
