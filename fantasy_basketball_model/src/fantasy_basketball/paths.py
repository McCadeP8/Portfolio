from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
HISTORY_DIR = PROJECT_ROOT / "data" / "history"


def ensure_directories() -> None:
    for path in (RAW_DIR / "fantrax", RAW_DIR / "projections", RAW_DIR / "sbc_streamlit", PROCESSED_DIR, HISTORY_DIR):
        path.mkdir(parents=True, exist_ok=True)

