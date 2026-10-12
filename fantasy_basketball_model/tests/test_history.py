import pandas as pd

from fantasy_basketball.history import CATEGORIES, summarize_categories


def test_category_summary_tracks_matchup_winner_and_per_game_threshold():
    row = {
        "matchup_winner": "A",
        "GP_A": 10,
        "GP_B": 10,
        "nba_games_in_period": 5,
    }
    for category in CATEGORIES:
        row[f"{category}_winner"] = "A"
        row[f"{category}_A"] = 0.60 if "%" in category else 100.0
        row[f"{category}_B"] = 0.50 if "%" in category else 90.0
    row["TOV_A"], row["TOV_B"] = 80.0, 90.0

    summary, co_win = summarize_categories(pd.DataFrame([row]))

    points = summary.set_index("category").loc["PTS"]
    true_shooting = summary.set_index("category").loc["TS%"]
    assert points["matchup_winner_category_win_pct"] == 1.0
    assert points["average_winning_threshold"] == 20.0
    assert points["average_league_threshold"] == 19.0
    assert points["average_losing_threshold"] == 18.0
    assert true_shooting["average_winning_threshold"] == 0.60
    assert true_shooting["average_league_threshold"] == 0.55
    assert true_shooting["average_losing_threshold"] == 0.50
    assert co_win.loc["PTS", "TS%"] == 1.0
