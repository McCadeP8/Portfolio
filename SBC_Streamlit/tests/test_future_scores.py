from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import big_data
from functions import get_matchup_score, zero_future_matchup_scores


SCORE_COLUMNS = ["PTS", "AST", "TS%", "2PT%", "+/-", "3PT%", "BLK", "DREB", "OREB", "ST", "FT%", "MP", "TO"]


class FutureScoreTests(unittest.TestCase):
    def test_all_zero_team_stats_are_an_unstarted_zero_zero_game(self):
        stats = pd.DataFrame([
            {"Team": "Albuquerque", **{column: 0 for column in SCORE_COLUMNS}},
            {"Team": "Anaheim", **{column: 0 for column in SCORE_COLUMNS}},
        ])
        self.assertEqual(get_matchup_score("Albuquerque", "Anaheim", stats), (0, 0))

    def test_real_category_tie_is_not_erased(self):
        stats = pd.DataFrame([
            {"Team": "Albuquerque", **{column: 1 for column in SCORE_COLUMNS}},
            {"Team": "Anaheim", **{column: 1 for column in SCORE_COLUMNS}},
        ])
        self.assertEqual(get_matchup_score("Albuquerque", "Anaheim", stats), (206.5, 206.5))

    def test_future_rows_are_zeroed_without_touching_started_rows(self):
        schedule = pd.DataFrame([
            {"Year": 2027, "Period": 1, "TeamAScore": 230.0, "TeamBScore": 183.0},
            {"Year": 2027, "Period": 2, "TeamAScore": 206.5, "TeamBScore": 206.5},
        ])
        calendar = pd.DataFrame([
            {"Year": 2027, "Period": 1, "Date": "2026-10-20"},
            {"Year": 2027, "Period": 2, "Date": "2026-10-24"},
        ])
        result = zero_future_matchup_scores(schedule, calendar, as_of="2026-10-22")
        self.assertEqual(result.loc[0, ["TeamAScore", "TeamBScore"]].tolist(), [230.0, 183.0])
        self.assertEqual(result.loc[1, ["TeamAScore", "TeamBScore"]].tolist(), [0.0, 0.0])

    def test_overnight_refresh_resets_and_skips_future_periods(self):
        today = pd.Timestamp.now(tz="America/New_York").normalize().tz_localize(None)
        schedule = pd.DataFrame([
            {"Year": 2027, "Period": 1, "Type": "Regular Season", "Round": "", "TeamA": "Albuquerque", "TeamB": "Anaheim", "TeamAScore": 230.0, "TeamBScore": 183.0},
            {"Year": 2027, "Period": 2, "Type": "Regular Season", "Round": "", "TeamA": "Albuquerque", "TeamB": "Anaheim", "TeamAScore": 206.5, "TeamBScore": 206.5},
        ])
        calendar = pd.DataFrame([
            {"Year": 2027, "Period": 1, "Date": today - pd.Timedelta(days=1)},
            {"Year": 2027, "Period": 2, "Date": today + pd.Timedelta(days=1)},
        ])
        with tempfile.TemporaryDirectory() as temp_dir:
            score_path = Path(temp_dir) / "all_time_scores.parquet"
            schedule.to_parquet(score_path, index=False)
            with (
                patch.object(big_data, "current_year", 2027),
                patch.object(big_data, "dataset_path", side_effect=lambda filename: Path(temp_dir) / filename),
                patch.object(big_data, "get_period_calendar", return_value=calendar),
                patch.object(big_data, "get_matchup_stats", return_value=pd.DataFrame()) as get_stats,
                patch.object(big_data, "notify"),
            ):
                big_data.get_all_time_scores()
            refreshed = pd.read_parquet(score_path)
        future = refreshed[refreshed["Period"].eq(2)].iloc[0]
        self.assertEqual((future["TeamAScore"], future["TeamBScore"]), (0.0, 0.0))
        self.assertEqual(get_stats.call_args_list[0].args, (2027, 1))
        self.assertEqual(len(get_stats.call_args_list), 1)


if __name__ == "__main__":
    unittest.main()
