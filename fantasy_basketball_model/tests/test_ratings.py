import pandas as pd

from fantasy_basketball.ratings import _chemistry_10, aggregate_categories, player_profiles, projection_available


def test_aggregate_categories_rebuilds_shooting_percentages_and_totals():
    profile = {
        "minutes_total": 200,
        "points": 120,
        "fg_a": 100,
        "ft_m": 16,
        "ft_a": 20,
        "three_m": 20,
        "three_a": 50,
        "two_m": 30,
        "two_a": 50,
        "offensive_rebounds": 10,
        "defensive_rebounds": 25,
        "assists": 20,
        "steals": 8,
        "blocks": 5,
        "turnovers": 12,
    }
    categories = aggregate_categories(profile)

    assert categories["MP"] == 200
    assert categories["2PT%"] == 0.60
    assert categories["3PT%"] == 0.40
    assert categories["FT%"] == 0.80
    assert categories["TS%"] == 120 / (2 * (100 + 0.44 * 20))


def test_minutes_are_converted_from_per_game_to_projected_total():
    players = pd.DataFrame([{"minutes": 30, "games": 70}])
    profiles = player_profiles(players)
    assert profiles.loc[0, "minutes_total"] == 2100


def test_zero_chemistry_is_neutral_five():
    ratings = _chemistry_10(pd.Series([-1.0, 0.0, 1.0]))
    assert ratings.iloc[1] == 5.0
    assert ratings.between(0.0, 10.0).all()


def test_missing_projection_is_not_rating_eligible():
    players = pd.DataFrame([
        {"games": 72, "minutes": 35.1},
        {"games": 0, "minutes": 0},
        {"games": None, "minutes": None},
    ])
    assert projection_available(players).tolist() == [True, False, False]
