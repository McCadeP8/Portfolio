from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import fnmatch
from functools import lru_cache
import json
import os
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import quote

import pandas as pd
import requests

from .config import BackendSettings
from .storage import read_parquet_files


@dataclass(frozen=True)
class DatasetContract:
    name: str
    relative_path: str
    required_columns: tuple[str, ...] = ()
    unique_key: tuple[str, ...] = ()


DATASETS: dict[str, DatasetContract] = {
    "team_stats": DatasetContract("team_stats", "all_team_stats_history.parquet", ("Year", "Period", "Team")),
    "rosters": DatasetContract("rosters", "all_time_rosters_history.parquet", ("Year", "period", "team_name")),
    "schedule": DatasetContract("schedule", "all_time_scores.parquet", ("Year", "Period", "TeamA", "TeamB"), ("Game_ID",)),
    "standings": DatasetContract("standings", "all_time_standings.parquet", ("Year", "Period", "Team")),
    "nba_boxscores": DatasetContract(
        "nba_boxscores",
        "nba_player_game_boxscores_2021_2026.parquet",
        ("sbc_year", "nba_game_id", "nba_player_id", "Date"),
        ("sbc_year", "nba_game_id", "nba_player_id"),
    ),
    "matchup_stats": DatasetContract(
        "matchup_stats",
        "sbc_player_matchup_stats.parquet",
        ("sbc_year", "sbc_period", "fantrax_id", "sbc_team_key"),
    ),
    "fantrax_players": DatasetContract("fantrax_players", "fantrax_players_snapshot.parquet", ("name", "fantraxId")),
}


def season_tag_for_date(value: str | date | datetime) -> str:
    text = str(value).strip().replace("-", "")
    parsed = pd.to_datetime(text, format="%Y%m%d", errors="coerce") if len(text) == 8 and text.isdigit() else pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    year = int(parsed.year)
    start = year if int(parsed.month) >= 7 else year - 1
    return f"{start}{str(start + 1)[-2:]}"


class DatasetRepository:
    """Centralized, selective access to local or remotely hosted datasets."""

    def __init__(self, settings: BackendSettings):
        self.settings = settings
        self._remote_manifest_paths: tuple[str, ...] | None = None

    @property
    def search_roots(self) -> tuple[Path, ...]:
        roots = [self.settings.data_root, self.settings.project_root, self.settings.project_root.parent]
        unique: list[Path] = []
        for root in roots:
            resolved = root.resolve()
            if resolved not in unique:
                unique.append(resolved)
        return tuple(unique)

    def resolve(self, dataset: str | DatasetContract, *, required: bool = False) -> Path | None:
        contract = DATASETS[dataset] if isinstance(dataset, str) else dataset
        remote = self._fetch_remote(contract.relative_path)
        if remote is not None:
            return remote
        for root in self.search_roots:
            candidate = root / contract.relative_path
            if candidate.exists():
                return candidate
        if contract.name == "nba_boxscores":
            candidates = self.parquet_paths("nba_player_game_boxscores_*.parquet")
            if candidates:
                return max(candidates, key=lambda path: path.stat().st_mtime)
        if required:
            raise FileNotFoundError(f"Dataset {contract.name!r} was not found at {contract.relative_path}")
        return None

    def read(
        self,
        dataset: str,
        *,
        columns: Sequence[str] | None = None,
        filters: list[tuple[str, str, Any]] | None = None,
        required: bool = False,
    ) -> pd.DataFrame:
        contract = DATASETS[dataset]
        path = self.resolve(contract, required=required)
        if path is None:
            return pd.DataFrame(columns=list(columns or contract.required_columns))
        frame = pd.read_parquet(path, columns=list(columns) if columns else None, filters=filters, engine="pyarrow")
        self.validate_contract(frame, contract, projected=columns is not None)
        return frame

    def validate_contract(self, frame: pd.DataFrame, contract: DatasetContract, *, projected: bool = False) -> None:
        if projected:
            return
        missing = [column for column in contract.required_columns if column not in frame.columns]
        if missing:
            raise ValueError(f"Dataset {contract.name!r} is missing required columns: {', '.join(missing)}")

    def parquet_paths(self, pattern: str) -> list[Path]:
        by_relative_path: dict[str, Path] = {}
        for root in self.search_roots:
            for candidate in sorted(root.glob(pattern)):
                if candidate.is_file():
                    relative = str(candidate.relative_to(root)).replace("\\", "/")
                    by_relative_path.setdefault(relative, candidate)
        for relative in self._catalog_paths():
            if fnmatch.fnmatch(relative, pattern.replace("\\", "/")):
                remote = self._fetch_remote(relative)
                if remote is not None:
                    by_relative_path[relative] = remote
        return [by_relative_path[key] for key in sorted(by_relative_path)]

    def archive_mtime(self, pattern: str) -> float:
        mtimes = [path.stat().st_mtime for path in self.parquet_paths(pattern)]
        return max(mtimes, default=0.0)

    def read_shots(
        self,
        game_ids: Iterable[str],
        *,
        game_dates: Iterable[str] = (),
        columns: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        normalized_ids = sorted({str(value).strip() for value in game_ids if str(value).strip()})
        if not normalized_ids:
            return pd.DataFrame(columns=list(columns or []))
        paths = self._season_archive_paths("data_snapshots/shots/nba_shots_20????.parquet", normalized_ids, game_dates)
        if not paths:
            sample = self.settings.project_root / "data_snapshots" / "shots" / "nba_shots_20241022_20241025.parquet"
            paths = [sample] if sample.exists() else []
        return read_parquet_files(paths, columns=columns, filters=[("game_id", "in", normalized_ids)])

    def read_pbp(
        self,
        *,
        game_ids: Iterable[str] = (),
        game_dates: Iterable[str] = (),
        columns: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        normalized_ids = sorted({str(value).strip() for value in game_ids if str(value).strip()})
        normalized_dates = sorted({str(value).strip().replace("-", "") for value in game_dates if str(value).strip()})
        if not normalized_ids and not normalized_dates:
            return pd.DataFrame(columns=list(columns or []))
        paths = self._season_archive_paths(
            "data_snapshots/pbp/pbp_stat_events_20????.parquet",
            normalized_ids,
            normalized_dates,
        )
        if not paths:
            paths = self.parquet_paths("data_snapshots/pbp/pbp_stat_events_20????.parquet")
        filters: list[tuple[str, str, Any]] = []
        if normalized_ids:
            filters.append(("game_id", "in", normalized_ids))
        elif normalized_dates:
            filters.append(("game_date", "in", normalized_dates))
        return read_parquet_files(paths, columns=columns, filters=filters)

    def _season_archive_paths(self, pattern: str, game_ids: Sequence[str], game_dates: Iterable[str]) -> list[Path]:
        tags = {season_tag_for_date(value) for value in game_dates}
        tags.discard("")
        if not tags and game_ids:
            tags.update(self._season_tags_for_game_ids(game_ids))
        candidates = self.parquet_paths(pattern)
        if not tags:
            return candidates
        return [path for path in candidates if any(path.stem.endswith(tag) for tag in tags)]

    def _season_tags_for_game_ids(self, game_ids: Sequence[str]) -> set[str]:
        path = self.resolve("nba_boxscores")
        if path is None:
            return set()
        index = read_parquet_files(
            [path],
            columns=["nba_game_id", "Date"],
            filters=[("nba_game_id", "in", list(game_ids))],
        )
        return {season_tag_for_date(value) for value in index.get("Date", []) if season_tag_for_date(value)}

    def _fetch_remote(self, relative_path: str) -> Path | None:
        base_url = self.settings.remote_data_base_url
        if not base_url:
            return None
        safe_parts = [quote(part) for part in Path(relative_path).parts]
        url = f"{base_url}/{'/'.join(safe_parts)}"
        target = self.settings.remote_cache_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and datetime.now().timestamp() - target.stat().st_mtime < self.settings.remote_cache_seconds:
            return target
        temporary = target.with_name(f".{target.name}.download")
        try:
            with requests.get(url, timeout=self.settings.http_timeout_seconds, stream=True) as response:
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                with temporary.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            os.replace(temporary, target)
            return target
        except requests.RequestException:
            return target if target.exists() else None
        finally:
            if temporary.exists():
                temporary.unlink()

    def _catalog_paths(self) -> tuple[str, ...]:
        if not self.settings.remote_data_base_url:
            return ()
        if self._remote_manifest_paths is not None:
            return self._remote_manifest_paths
        manifest = self._fetch_remote("data_snapshots/_metadata/data_manifest.json")
        if manifest is None:
            self._remote_manifest_paths = ()
            return ()
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            datasets = payload.get("datasets", [])
            self._remote_manifest_paths = tuple(
                str(item.get("path", "")).replace("\\", "/")
                for item in datasets
                if isinstance(item, dict) and item.get("path")
            )
        except (ValueError, TypeError):
            self._remote_manifest_paths = ()
        return self._remote_manifest_paths


@lru_cache(maxsize=4)
def _cached_repository(project_root: str, data_root: str, runtime_root: str, remote_url: str) -> DatasetRepository:
    settings = BackendSettings.from_env(Path(project_root))
    settings = BackendSettings(
        project_root=Path(project_root),
        data_root=Path(data_root),
        runtime_root=Path(runtime_root),
        remote_data_base_url=remote_url,
        live_mode=settings.live_mode,
        current_sbc_year=settings.current_sbc_year,
        http_timeout_seconds=settings.http_timeout_seconds,
        live_cache_seconds=settings.live_cache_seconds,
        remote_cache_seconds=settings.remote_cache_seconds,
        parquet_row_group_size=settings.parquet_row_group_size,
    )
    return DatasetRepository(settings)


def get_repository(project_root: Path | None = None) -> DatasetRepository:
    settings = BackendSettings.from_env(project_root)
    return _cached_repository(
        str(settings.project_root),
        str(settings.data_root),
        str(settings.runtime_root),
        settings.remote_data_base_url,
    )
