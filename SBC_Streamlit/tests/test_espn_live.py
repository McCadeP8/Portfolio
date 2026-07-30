from __future__ import annotations

import unittest

from sbc_backend.live.espn import as_legacy_player_rows, parse_live_game, parse_player_boxscore


class EspnLiveTests(unittest.TestCase):
    def setUp(self):
        self.event = {
            "id": "401000001",
            "date": "2026-10-20T01:00Z",
            "status": {"period": 4, "displayClock": "0.0", "type": {"state": "post", "completed": True, "shortDetail": "Final"}},
            "competitions": [{"competitors": [
                {"homeAway": "home", "score": "111", "winner": True, "team": {"id": "1", "abbreviation": "DEN", "displayName": "Denver Nuggets"}},
                {"homeAway": "away", "score": "99", "winner": False, "team": {"id": "2", "abbreviation": "UTA", "displayName": "Utah Jazz"}},
            ]}],
        }

    def test_score_and_player_boxscore_normalization(self):
        game = parse_live_game(self.event, fetched_at="now")
        self.assertTrue(game.completed)
        self.assertEqual((game.home_score, game.away_score), (111.0, 99.0))
        summary = {"boxscore": {"players": [{
            "team": {"id": "1", "abbreviation": "DEN"},
            "statistics": [{"labels": ["MIN", "FG", "3PT", "FT", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TO", "+/-"],
                            "athletes": [{"athlete": {"id": "15", "displayName": "Nikola Jokic"}, "stats": ["35:30", "10-17", "2-4", "5-6", "27", "3", "9", "11", "2", "1", "4", "+14"]}]}]
        }]}}
        frame = parse_player_boxscore(summary, self.event)
        self.assertEqual(frame.loc[0, "3PTM"], 2)
        self.assertAlmostEqual(frame.loc[0, "MP"], 35.5)
        legacy = as_legacy_player_rows(frame)[0]
        self.assertEqual((legacy["PLAYER_ID"], legacy["PTS"], legacy["MATCHUP"]), ("15", 27.0, "DEN vs. UTA"))


if __name__ == "__main__":
    unittest.main()
