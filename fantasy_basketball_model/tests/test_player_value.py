import numpy as np
import pytest

import pandas as pd

from fantasy_basketball.player_value import PLAYER_GAMES_PER_PERIOD, minmax_rating, probability_rating


def test_average_replacement_player_is_five_on_category_curve():
    intercept = -2.0
    slope = 0.1
    threshold = 20.0
    average_core = threshold * 14 / 15
    average_player_period_value = threshold / 15
    assert PLAYER_GAMES_PER_PERIOD == pytest.approx(1.662)
    assert probability_rating(intercept, slope, average_core + average_player_period_value) == pytest.approx(5.0)


def test_lower_turnover_replacement_rates_above_average():
    intercept = 2.0
    slope = -0.1
    threshold = 20.0
    average_core = threshold * 14 / 15
    lower_turnover_player = threshold / 15 - 1
    assert probability_rating(intercept, slope, average_core + lower_turnover_player) > 5.0


def test_minmax_rating_spans_zero_to_ten_and_preserves_missing():
    result = minmax_rating(pd.Series([2.0, 4.0, 7.0, np.nan]))
    assert result.iloc[0] == 0.0
    assert result.iloc[2] == 10.0
    assert pd.isna(result.iloc[3])
