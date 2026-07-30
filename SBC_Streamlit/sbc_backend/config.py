from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import os
from pathlib import Path


class LiveMode(str, Enum):
    """Controls whether ESPN data is disabled, observed, or publishable."""

    OFF = "off"
    SHADOW = "shadow"
    LIVE = "live"

    @classmethod
    def parse(cls, value: str | None) -> "LiveMode":
        normalized = str(value or cls.OFF.value).strip().lower()
        try:
            return cls(normalized)
        except ValueError as exc:
            choices = ", ".join(mode.value for mode in cls)
            raise ValueError(f"SBC_LIVE_MODE must be one of: {choices}") from exc


def infer_sbc_year(day: date | None = None) -> int:
    """Return the SBC season-ending year used throughout the existing app."""

    value = day or date.today()
    return value.year + 1 if (value.month > 6 or (value.month == 6 and value.day >= 30)) else value.year


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    value = int(raw)
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


@dataclass(frozen=True)
class BackendSettings:
    project_root: Path
    data_root: Path
    runtime_root: Path
    remote_data_base_url: str = ""
    live_mode: LiveMode = LiveMode.OFF
    current_sbc_year: int = 0
    http_timeout_seconds: int = 30
    live_cache_seconds: int = 15
    remote_cache_seconds: int = 300
    parquet_row_group_size: int = 50_000

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> "BackendSettings":
        root = (project_root or Path(__file__).resolve().parents[1]).resolve()
        data_root = Path(os.getenv("SBC_DATA_ROOT", str(root))).expanduser().resolve()
        runtime_root = Path(os.getenv("SBC_RUNTIME_ROOT", str(root / ".runtime"))).expanduser().resolve()
        return cls(
            project_root=root,
            data_root=data_root,
            runtime_root=runtime_root,
            remote_data_base_url=os.getenv("SBC_DATA_BASE_URL", "").strip().rstrip("/"),
            live_mode=LiveMode.parse(os.getenv("SBC_LIVE_MODE", LiveMode.OFF.value)),
            current_sbc_year=_env_int("SBC_CURRENT_SBC_YEAR", infer_sbc_year(), minimum=2021),
            http_timeout_seconds=_env_int("SBC_HTTP_TIMEOUT_SECONDS", 30),
            live_cache_seconds=_env_int("SBC_LIVE_CACHE_SECONDS", 15),
            remote_cache_seconds=_env_int("SBC_REMOTE_CACHE_SECONDS", 300),
            parquet_row_group_size=_env_int("SBC_PARQUET_ROW_GROUP_SIZE", 50_000, minimum=1_000),
        )

    @property
    def snapshot_root(self) -> Path:
        return self.data_root / "data_snapshots"

    @property
    def metadata_root(self) -> Path:
        return self.snapshot_root / "_metadata"

    @property
    def run_root(self) -> Path:
        return self.snapshot_root / "_runs"

    @property
    def lock_root(self) -> Path:
        return self.runtime_root / "locks"

    @property
    def remote_cache_root(self) -> Path:
        return self.runtime_root / "remote_data"

    def ensure_runtime_directories(self) -> None:
        for path in (self.runtime_root, self.lock_root, self.remote_cache_root, self.metadata_root, self.run_root):
            path.mkdir(parents=True, exist_ok=True)
