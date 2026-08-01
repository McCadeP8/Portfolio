import unittest

import pandas as pd

from sbc_backend.awards import build_award_count_tables


class AwardCountTests(unittest.TestCase):
    def test_combines_multi_column_and_recurring_awards(self):
        players = pd.DataFrame(
            [
                {"Award": "All-SBC 1st Team", "Winner": "Player A"},
                {"Award": "All-SBC 2nd Team", "Winner": "Player A"},
                {"Award": "All-SBC 1st Team", "Winner": "Player B"},
                {"Award": "East January POM", "Winner": "Player A"},
                {"Award": "West February POM", "Winner": "Player A"},
                {"Award": "East March POM", "Winner": "Not Awarded"},
                {"Award": "ECF MVP", "Winner": "Player B"},
                {"Award": "Finals MVP", "Winner": "Player B"},
            ]
        )
        teams = pd.DataFrame(
            [
                {"Award": "EC Champion", "Winner": "Baltimore"},
                {"Award": "WC Champion", "Winner": "Vegas"},
                {"Award": "Champion", "Winner": "Vegas"},
                {"Award": "Champion", "Winner": "Not Awarded"},
            ]
        )

        player_tables, team_tables = build_award_count_tables(players, teams)
        by_title = {item["title"]: item["table"] for item in player_tables}
        all_sbc = by_title["All-SBC"]
        self.assertEqual(all_sbc.iloc[0]["Player"], "Player A")
        self.assertEqual(int(all_sbc.iloc[0]["Total"]), 2)
        self.assertEqual(int(by_title["POM"].iloc[0]["Awards"]), 2)
        series = by_title["Series MVP"]
        self.assertEqual(int(series.iloc[0]["East"]), 1)
        self.assertEqual(int(series.iloc[0]["Finals"]), 1)

        team_by_title = {item["title"]: item["table"] for item in team_tables}
        self.assertEqual(team_by_title["Finals Winner"].shape[0], 1)
        self.assertEqual(team_by_title["Conference Winner"].shape[0], 2)


if __name__ == "__main__":
    unittest.main()
