import pandas as pd

from fantasy_basketball.validation import validate_foundation
from fantasy_basketball.pipeline import zero_teamless_projection_values


def test_category_weight_error_is_visible():
    config = {"expected_team_count": 1, "expected_category_count": 2, "expected_weight_total": 3, "expected_regular_season_periods": 1, "expected_opponents_per_regular_period": 1}
    teams = pd.DataFrame([{"fantasy_team_id": "a"}])
    rosters = pd.DataFrame([{"fantrax_player_id": "p"}])
    schedule = pd.DataFrame([{"period": 1, "away_team_id": "a", "home_team_id": "b"}])
    categories = pd.DataFrame([{"category": "PTS", "weight": 1}])
    issues = validate_foundation(teams, rosters, schedule, categories, None, config)
    assert {"category_count", "category_weight_total", "projections_present"}.issubset(set(issues["check"]))


def test_teamless_players_have_zero_projection_values():
    canonical = pd.DataFrame([
        {"player_name": "Free Agent", "nba_team": "(N/A)", "games": 72.0, "points": 1000.0},
        {"player_name": "Rostered Player", "nba_team": "DEN", "games": 70.0, "points": 900.0},
    ])

    result = zero_teamless_projection_values(canonical, ["games", "points"])

    assert result.loc[0, ["games", "points"]].tolist() == [0.0, 0.0]
    assert result.loc[1, ["games", "points"]].tolist() == [70.0, 900.0]

