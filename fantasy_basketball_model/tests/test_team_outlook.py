import pandas as pd

from fantasy_basketball.overall_model import ALL_CATEGORIES
from fantasy_basketball.team_outlook import category_probabilities, reference_percentile


def test_zero_category_inputs_map_to_even_odds():
    counting_categories = ["MP", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "+/-"]
    shooting_categories = ["TS%", "2PT%", "3PT%", "FT%"]
    counting = pd.DataFrame({
        "category": counting_categories,
        "intercept": 0.0,
        "slope": 1.0,
    })
    shooting = pd.DataFrame({
        "category": shooting_categories,
        "intercept": 0.0,
        "slope": 1.0,
    })
    values = pd.DataFrame([[0.0] * len(ALL_CATEGORIES)], columns=ALL_CATEGORIES)
    probabilities = category_probabilities(values, counting, shooting)
    assert probabilities.loc[0].eq(0.5).all()


def test_chemistry_percentile_uses_fixed_historical_reference():
    reference = pd.Series([-10.0, -5.0, 0.0, 5.0, 10.0])
    scores = reference_percentile(pd.Series([-11.0, 0.0, 6.0, 11.0]), reference)
    assert scores.tolist() == [0.0, 6.0, 8.0, 10.0]
