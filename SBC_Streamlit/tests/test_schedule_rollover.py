from collections import Counter
from itertools import combinations
from pathlib import Path
import unittest

import pandas as pd

from data import team_info


ROOT = Path(__file__).resolve().parents[1]


class ScheduleRolloverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scores = pd.read_parquet(ROOT / "all_time_scores.parquet")
        cls.prior = scores[(scores["Year"] == 2026) & (scores["Type"] == "Regular Season")]
        cls.current = scores[(scores["Year"] == 2027) & (scores["Type"] == "Regular Season")]
        cls.current_all = scores[scores["Year"] == 2027]

    def rows_for_pair(self, frame, team_a, team_b):
        return frame[
            ((frame["TeamA"] == team_a) & (frame["TeamB"] == team_b))
            | ((frame["TeamA"] == team_b) & (frame["TeamB"] == team_a))
        ]

    def test_every_team_has_72_games_and_36_home_games(self):
        appearances = pd.concat([self.current["TeamA"], self.current["TeamB"]]).value_counts()
        self.assertEqual(set(appearances.index), set(team_info))
        self.assertTrue((appearances == 72).all())
        self.assertTrue((self.current["TeamB"].value_counts() == 36).all())

    def test_conference_rotation_and_cross_conference_home_and_home(self):
        for team_a, team_b in combinations(sorted(team_info), 2):
            current_pair = self.rows_for_pair(self.current, team_a, team_b)
            same_conference = team_info[team_a]["conf"] == team_info[team_b]["conf"]
            if same_conference:
                self.assertEqual(len(current_pair), 3, (team_a, team_b))
                prior_pair = self.rows_for_pair(self.prior, team_a, team_b)
                prior_double_home = {team for team, count in Counter(prior_pair["TeamB"]).items() if count == 2}
                current_double_home = {team for team, count in Counter(current_pair["TeamB"]).items() if count == 2}
                self.assertEqual(len(prior_double_home), 1, (team_a, team_b))
                self.assertEqual(len(current_double_home), 1, (team_a, team_b))
                self.assertNotEqual(prior_double_home, current_double_home, (team_a, team_b))
            else:
                self.assertEqual(len(current_pair), 2, (team_a, team_b))
                self.assertEqual(Counter(current_pair["TeamB"]), Counter({team_a: 1, team_b: 1}))

    def test_scores_and_game_flags_are_ready_for_the_new_season(self):
        self.assertTrue((self.current_all[["TeamAScore", "TeamBScore"]] == 0).all().all())
        expected_conference = self.current.apply(
            lambda row: int(team_info[row["TeamA"]]["conf"] == team_info[row["TeamB"]]["conf"]), axis=1
        )
        expected_division = self.current.apply(
            lambda row: int(team_info[row["TeamA"]]["div"] == team_info[row["TeamB"]]["div"]), axis=1
        )
        self.assertTrue((self.current["ConferenceGame"] == expected_conference).all())
        self.assertTrue((self.current["DivisionGame"] == expected_division).all())
        postseason = self.current_all[self.current_all["Type"] != "Regular Season"]
        self.assertTrue((postseason[["ConferenceGame", "DivisionGame"]] == 0).all().all())

    def test_new_season_standings_are_zeroed(self):
        standings = pd.read_parquet(ROOT / "all_time_standings.parquet")
        current = standings[standings["Year"] == 2027]
        self.assertEqual(set(current["Team"]), set(team_info))
        self.assertEqual(set(current["Period"]), set(range(1, 37)) | {99})
        self.assertTrue((current[["Record", "ConfRecord", "DivRecord", "GSRecord"]] == "0-0").all().all())


if __name__ == "__main__":
    unittest.main()
