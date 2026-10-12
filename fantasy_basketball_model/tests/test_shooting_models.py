import pandas as pd
import pytest

from fantasy_basketball.shooting_models import (
    projected_player_points_gained,
    season_league_averages,
    shooting_team_periods,
)


def test_points_gained_is_percentage_lift_times_attempts():
    stats = pd.DataFrame({
        "Year": [2026, 2026], "Period": [1, 1], "Team": ["A", "B"],
        "TS%": [.60, .50], "2PT%": [.60, .40], "3PT%": [.40, .30], "FT%": [.80, .70],
        "2PTA": [100, 100], "3PTA": [50, 50], "FTA": [25, 25],
    })
    periods, averages = shooting_team_periods(stats)
    assert averages.loc[0, "2PT%"] == .50
    assert periods.loc[0, "2PT%_points_gained"] == pytest.approx(10)
    assert periods.loc[1, "2PT%_points_gained"] == pytest.approx(-10)


def test_season_averages_are_attempt_weighted():
    stats = pd.DataFrame({
        "Year": [2026, 2026], "TS%": [.50, .70], "2PT%": [.50, .70],
        "3PT%": [.30, .50], "FT%": [.70, .90], "2PTA": [10, 30],
        "3PTA": [10, 30], "FTA": [10, 30],
    })
    averages = season_league_averages(stats)
    assert averages.loc[0, "2PT%"] == .65


def test_projected_player_metric_centers_weighted_league_at_zero():
    projections = pd.DataFrame({
        "fantrax_player_id": ["1", "2"], "player_name": ["A", "B"], "nba_team": ["DEN", "BOS"],
        "fg_a": [100, 100], "ft_a": [20, 20], "two_a": [60, 60], "three_a": [40, 40],
        "ts_pct": [.60, .50], "two_pct": [.60, .40], "three_pct": [.40, .30], "ft_pct": [.80, .70],
    })
    metrics, _ = projected_player_points_gained(projections)
    for category in ["TS%", "2PT%", "3PT%", "FT%"]:
        assert abs(metrics[f"{category}_points_gained"].sum()) < 1e-9
