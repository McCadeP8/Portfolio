from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import build_pbp_one_game as pbp
from sbc_backend.storage import atomic_write_parquet


def event_frame(game_id: str) -> pd.DataFrame:
    return pd.DataFrame([{
        "game_id": game_id,
        "game_date": "20261020",
        "stat": "PTS",
        "player_id": "15",
        "player": "Player",
        "wallclock": "2026-10-20T01:00:00Z",
        "value": 2,
        "scored": 2,
        "description": "made shot",
    }], columns=pbp.STAT_COLUMNS)


class PbpResumeTests(unittest.TestCase):
    def test_day_checkpoint_does_not_hide_a_late_game(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = root / "boxscores.parquet"
            checkpoints = root / "checkpoints"
            atomic_write_parquet(pd.DataFrame({
                "Date": ["2026-10-20", "2026-10-20"],
                "nba_game_id": ["game-one", "game-two"],
                "nba_season": ["2026-27", "2026-27"],
            }), index)
            atomic_write_parquet(event_frame("game-one"), checkpoints / "20261020.parquet")
            with patch.object(pbp, "OFFICIAL_BOXSCORE_PATH", index), patch.object(
                pbp, "build_stat_events", side_effect=lambda game_id, game_date, boxscore_path=None: event_frame(game_id)
            ) as fetch:
                combined = pbp.build_games_from_index(
                    seasons=["2026-27"],
                    start_date="20261020",
                    end_date="20261020",
                    checkpoint_dir=checkpoints,
                )
            self.assertEqual(set(combined["game_id"]), {"game-one", "game-two"})
            fetch.assert_called_once_with("game-two", game_date="20261020", boxscore_path=None)


if __name__ == "__main__":
    unittest.main()
