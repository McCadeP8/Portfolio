from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from ..config import BackendSettings, LiveMode
from ..storage import atomic_write_json, atomic_write_parquet
from .espn import EspnNBAClient, LiveSnapshot


class LiveScoreService:
    """Runs ESPN in off, shadow, or live mode without coupling it to the UI."""

    def __init__(self, settings: BackendSettings, client: EspnNBAClient | None = None):
        self.settings = settings
        self.client = client or EspnNBAClient(
            cache_root=settings.runtime_root / "espn",
            timeout_seconds=settings.http_timeout_seconds,
            live_ttl_seconds=settings.live_cache_seconds,
        )

    def collect(self, game_date: date | None = None) -> LiveSnapshot | None:
        if self.settings.live_mode is LiveMode.OFF:
            return None
        target_date = game_date or date.today()
        snapshot = self.client.snapshot(target_date, include_player_stats=True)
        self._persist_shadow_snapshot(snapshot)
        return snapshot

    def published_games(self, game_date: date | None = None) -> pd.DataFrame:
        """Return live rows only after the explicit live-mode gate is enabled."""

        snapshot = self.collect(game_date)
        if snapshot is None or self.settings.live_mode is not LiveMode.LIVE:
            return pd.DataFrame()
        return snapshot.game_frame()

    def _persist_shadow_snapshot(self, snapshot: LiveSnapshot) -> None:
        destination = self.settings.runtime_root / "live" / snapshot.game_date
        atomic_write_json(
            {
                "game_date": snapshot.game_date,
                "fetched_at": snapshot.fetched_at,
                "games": [game.as_dict() for game in snapshot.games],
            },
            destination / "games.json",
        )
        if not snapshot.player_stats.empty:
            atomic_write_parquet(
                snapshot.player_stats,
                destination / "player_stats.parquet",
                row_group_size=self.settings.parquet_row_group_size,
            )
