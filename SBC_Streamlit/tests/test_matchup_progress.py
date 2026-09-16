from __future__ import annotations

import unittest

import pandas as pd

from sbc_backend.matchup_progress import starter_game_progress


class StarterGameProgressTests(unittest.TestCase):
    def test_counts_completed_games_for_active_starters_not_elapsed_days(self):
        calendar = pd.DataFrame({
            "Year": [2027, 2027],
            "Period": [1, 1],
            "Day": [1, 2],
            "Date": ["2026-10-20", "2026-10-21"],
        })
        rosters = pd.DataFrame([
            {"Year": 2027, "period": day, "id": player, "status": "ACTIVE", "team_name": "El Paso Vipers"}
            for day in (1, 2)
            for player in ("one", "two")
        ])
        players = pd.DataFrame([
            {"fantraxId": "one", "nba_team": "GS"},
            {"fantraxId": "two", "nba_team": "LAL"},
        ])
        games = pd.DataFrame([
            {"game_date": "2026-10-20", "home_abbreviation": "GSW", "away_abbreviation": "LAL", "completed": True},
            {"game_date": "2026-10-21", "home_abbreviation": "GSW", "away_abbreviation": "DEN", "completed": False},
        ])

        progress = starter_game_progress(
            calendar, rosters, players, games, 2027, 1,
            as_of="2026-10-21", teams=["El Paso"],
        )

        self.assertEqual(progress, 66.7)


if __name__ == "__main__":
    unittest.main()
