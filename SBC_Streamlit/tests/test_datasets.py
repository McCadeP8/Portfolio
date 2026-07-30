from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from sbc_backend.config import BackendSettings
from sbc_backend.datasets import DatasetRepository, season_tag_for_date
from sbc_backend.storage import atomic_write_parquet


class DatasetRepositoryTests(unittest.TestCase):
    def test_season_tag_accepts_archive_and_iso_dates(self):
        self.assertEqual(season_tag_for_date("20241022"), "202425")
        self.assertEqual(season_tag_for_date("2025-01-04"), "202425")

    def test_selective_season_and_game_reads(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            settings = BackendSettings(project_root=root, data_root=root, runtime_root=root / ".runtime")
            shots = root / "data_snapshots" / "shots" / "nba_shots_202425.parquet"
            pbp = root / "data_snapshots" / "pbp" / "pbp_stat_events_202425.parquet"
            atomic_write_parquet(pd.DataFrame({"game_id": ["one", "two"], "game_date": ["20241022", "20241022"], "x": [1, 2]}), shots)
            atomic_write_parquet(pd.DataFrame({"game_id": ["one", "two"], "game_date": ["20241022", "20241022"], "stat": ["PTS", "AST"]}), pbp)
            repository = DatasetRepository(settings)
            self.assertEqual(repository.read_shots(["two"], game_dates=["2024-10-22"])["game_id"].tolist(), ["two"])
            self.assertEqual(repository.read_pbp(game_ids=["one"], game_dates=["20241022"])["game_id"].tolist(), ["one"])


if __name__ == "__main__":
    unittest.main()
