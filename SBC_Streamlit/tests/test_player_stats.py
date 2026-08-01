from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from sbc_backend.player_stats import prepare_matchup_archive_rows


ROOT = Path(__file__).resolve().parents[1]


class PlayerStatAggregationTests(unittest.TestCase):
    def test_game_type_filter_runs_before_duplicate_collapse(self):
        rows = pd.DataFrame([
            {"fantrax_id": "p1", "sbc_year": 2024, "sbc_period": 6, "sbc_team_key": "Manchester", "sbc_matchup_type": "In-Season Tournament", "Game_ID": "cup", "sbc_opponent": "Vegas", "nba_game_ids": "nba-1", "PTS": 46},
            {"fantrax_id": "p1", "sbc_year": 2024, "sbc_period": 6, "sbc_team_key": "Manchester", "sbc_matchup_type": "Regular Season", "Game_ID": "regular-a", "sbc_opponent": "Columbus", "nba_game_ids": "nba-1", "PTS": 46},
            {"fantrax_id": "p1", "sbc_year": 2024, "sbc_period": 6, "sbc_team_key": "Manchester", "sbc_matchup_type": "Regular Season", "Game_ID": "regular-b", "sbc_opponent": "Columbus", "nba_game_ids": "nba-1", "PTS": 46},
        ])

        regular = prepare_matchup_archive_rows(rows, matchup_type="Regular Season")
        cup = prepare_matchup_archive_rows(rows, matchup_type="In-Season Tournament")

        self.assertEqual(len(regular), 1)
        self.assertEqual(int(regular.iloc[0]["PTS"]), 46)
        self.assertEqual(len(cup), 1)
        self.assertEqual(int(cup.iloc[0]["PTS"]), 46)

    def test_manchester_record_totals_match_player_pages(self):
        archive = pd.read_parquet(ROOT / "sbc_player_matchup_stats.parquet")
        regular = prepare_matchup_archive_rows(archive, matchup_type="Regular Season")
        manchester = regular[regular["sbc_team_key"].astype(str) == "Manchester"]
        totals = manchester.groupby("fantrax_name")["PTS"].sum()

        self.assertEqual(int(totals["Bam Adebayo"]), 1857)
        self.assertEqual(int(totals["Jalen Brunson"]), 1820)


if __name__ == "__main__":
    unittest.main()
