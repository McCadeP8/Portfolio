from __future__ import annotations

import unittest

import pandas as pd

from sbc_backend.matchup_preview import project_player_rows


class MatchupPreviewProjectionTests(unittest.TestCase):
    def test_projects_prior_rates_across_current_team_schedule(self):
        roster = pd.DataFrame([{"fantraxId": "ft1", "sbc_team": "El Paso"}])
        bridge = pd.DataFrame([{"fantraxId": "ft1", "espn_player_id": "nba1", "fantrax_name": "Example Player"}])
        players = pd.DataFrame([{"fantraxId": "ft1", "nba_team": "GS"}])
        prior = pd.DataFrame([
            {"nba_player_id": "nba1", "nba_game_id": "g1", "MP": 30, "2PTM": 5, "2PTA": 10, "3PTM": 2, "3PTA": 5, "FTM": 4, "FTA": 5, "PTS": 20, "OREB": 1, "DREB": 5, "AST": 6, "ST": 1, "BLK": 1, "TO": 2, "+/-": 3},
            {"nba_player_id": "nba1", "nba_game_id": "g2", "MP": 34, "2PTM": 7, "2PTA": 12, "3PTM": 4, "3PTA": 9, "FTM": 2, "FTA": 3, "PTS": 28, "OREB": 1, "DREB": 7, "AST": 8, "ST": 2, "BLK": 1, "TO": 4, "+/-": 5},
        ])
        games = pd.DataFrame([
            {"home_abbreviation": "GSW", "away_abbreviation": "LAL"},
            {"home_abbreviation": "PHX", "away_abbreviation": "GSW"},
            {"home_abbreviation": "GSW", "away_abbreviation": "DEN"},
        ])

        projected = project_player_rows(roster, bridge, players, prior, games)

        self.assertEqual(projected.iloc[0]["GP"], 3)
        self.assertAlmostEqual(projected.iloc[0]["PTS"], 72)
        self.assertAlmostEqual(projected.iloc[0]["AST"], 21)
        self.assertEqual(projected.iloc[0]["sbc_team"], "El Paso")


if __name__ == "__main__":
    unittest.main()
