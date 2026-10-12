import pandas as pd
import pytest

from fantasy_basketball.pipeline import allocate_team_plus_minus


def test_team_plus_minus_is_allocated_by_projected_minute_share():
    players = pd.DataFrame({
        "nba_team": ["DEN", "DEN", ""],
        "games": [72, 0, 72],
        "minutes": [35.1, 20, 30],
    })
    totals = pd.DataFrame({
        "nba_team": ["DEN"],
        "projected_season_plus_minus": [1062.5],
    })
    result = allocate_team_plus_minus(players, totals)
    expected = 72 * 35.1 / 19_680 * 1062.5
    assert result.loc[0, "plus_minus"] == pytest.approx(expected)
    assert result.loc[0, "plus_minus"] / 72 == pytest.approx(1.895, abs=0.0001)
    assert result.loc[1, "plus_minus"] == 0
    assert result.loc[2, "plus_minus"] == 0
