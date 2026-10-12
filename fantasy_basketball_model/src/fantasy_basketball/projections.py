from __future__ import annotations

import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests


COLUMN_ALIASES = {
    "projection_player_id": {"player_id", "id", "playerid"},
    "player_name": {"player", "name", "player_name"},
    "nba_team": {"team", "nba_team", "tm"},
    "eligible_positions": {"position", "positions", "pos", "eligible_positions"},
    "games": {"games", "gp", "g"},
    "minutes": {"minutes", "min", "mpg", "mins"},
    "fg_pct": {"fg%", "fg_pct", "field_goal_percentage"},
    "fg_m": {"fgm", "fg_m", "field_goals_made"},
    "fg_a": {"fga", "fg_a", "field_goals_attempted"},
    "ft_pct": {"ft%", "ft_pct", "free_throw_percentage"},
    "ft_m": {"ftm", "ft_m", "free_throws_made"},
    "ft_a": {"fta", "ft_a", "free_throws_attempted"},
    "three_pct": {"3p%", "3pt%", "three_pct", "three_point_percentage"},
    "three_m": {"3pm", "3ptm", "three_m", "threes"},
    "three_a": {"3pa", "3pta", "three_a"},
    "two_pct": {"2p%", "2pt%", "two_pct"},
    "two_m": {"2pm", "2ptm", "two_m"},
    "two_a": {"2pa", "2pta", "two_a"},
    "ts_pct": {"ts%", "ts_pct", "true_shooting_percentage"},
    "points": {"pts", "points"},
    "rebounds": {"reb", "trb", "treb", "rebounds"},
    "offensive_rebounds": {"oreb", "orb", "offensive_rebounds"},
    "defensive_rebounds": {"dreb", "drb", "defensive_rebounds"},
    "assists": {"ast", "assists"},
    "steals": {"stl", "steals"},
    "blocks": {"blk", "blocks"},
    "turnovers": {"to", "tov", "turnovers"},
    "plus_minus": {"plus_minus", "+/-", "plusminus"},
}

SHOT_CELL = re.compile(
    r"^\s*(?P<pct>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*"
    r"\(\s*(?P<made>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*/\s*"
    r"(?P<attempted>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\)\s*$"
)


def _column_key(value: object) -> str:
    text = str(value).strip().lower().replace("%", " pct ")
    return re.sub(r"[^a-z0-9+/-]+", "_", text).strip("_")


def _read_source(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt", ".tsv"}:
        return pd.read_csv(path, sep=None, engine="python")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix in {".html", ".htm"}:
        tables = pd.read_html(path)
        if not tables:
            raise ValueError(f"No HTML tables found in {path}")
        return max(tables, key=lambda table: table.shape[0] * table.shape[1])
    raise ValueError(f"Unsupported projection format: {suffix}")


def _parse_shooting_cell(value: object) -> tuple[float, float, float]:
    if pd.isna(value):
        return np.nan, np.nan, np.nan
    match = SHOT_CELL.match(str(value))
    if not match:
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        return float(numeric) if pd.notna(numeric) else np.nan, np.nan, np.nan
    return tuple(float(match.group(name)) for name in ("pct", "made", "attempted"))


def _normalize_projection_frame(
    frame: pd.DataFrame,
    provider: str,
    snapshot_date: str,
    stat_basis: str = "unknown",
    minutes_basis: str = "unknown",
) -> tuple[pd.DataFrame, list[str]]:
    keyed = {_column_key(column): column for column in frame.columns}
    rename: dict[object, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases | {_column_key(canonical)}:
            if _column_key(alias) in keyed:
                rename[keyed[_column_key(alias)]] = canonical
                break
    normalized = frame.rename(columns=rename).copy()
    if "player_name" not in normalized:
        raise ValueError("Projection input needs a recognizable player/name column")
    normalized["player_name"] = normalized["player_name"].astype(str).str.strip()
    normalized = normalized[
        normalized["player_name"].ne("")
        & normalized["player_name"].str.lower().ne("player")
        & normalized["player_name"].str.lower().ne("nan")
    ].copy()

    for pct_col, made_col, attempted_col in (
        ("fg_pct", "fg_m", "fg_a"),
        ("ft_pct", "ft_m", "ft_a"),
        ("three_pct", "three_m", "three_a"),
    ):
        if pct_col not in normalized:
            continue
        parsed = normalized[pct_col].map(_parse_shooting_cell)
        parsed_frame = pd.DataFrame(parsed.tolist(), index=normalized.index, columns=[pct_col, made_col, attempted_col])
        for column in parsed_frame:
            if column not in normalized or normalized[column].isna().all():
                normalized[column] = parsed_frame[column]
            else:
                normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(parsed_frame[column])

    canonical_columns = list(COLUMN_ALIASES)
    initially_missing = [column for column in canonical_columns if column not in normalized]
    for column in initially_missing:
        normalized[column] = pd.NA
    numeric = [c for c in canonical_columns if c not in {"projection_player_id", "player_name", "nba_team", "eligible_positions"}]
    for column in numeric:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    normalized["two_m"] = normalized["two_m"].fillna(normalized["fg_m"] - normalized["three_m"])
    normalized["two_a"] = normalized["two_a"].fillna(normalized["fg_a"] - normalized["three_a"])
    normalized["two_pct"] = normalized["two_pct"].fillna(
        normalized["two_m"].div(normalized["two_a"].replace(0, np.nan))
    )
    ts_denominator = 2 * (normalized["fg_a"] + 0.44 * normalized["ft_a"])
    normalized["ts_pct"] = normalized["ts_pct"].fillna(
        normalized["points"].div(ts_denominator.replace(0, np.nan))
    )
    normalized["projection_source"] = provider
    normalized["projection_snapshot_date"] = snapshot_date
    normalized["stat_basis"] = stat_basis
    normalized["minutes_basis"] = minutes_basis
    missing = [column for column in canonical_columns if normalized[column].isna().all()]
    output_columns = canonical_columns + [
        "projection_source", "projection_snapshot_date", "stat_basis", "minutes_basis"
    ]
    return normalized[output_columns].reset_index(drop=True), missing


def import_projections(
    source: Path,
    raw_dir: Path,
    provider: str = "Hashtag Basketball",
    snapshot_date: str | None = None,
    stat_basis: str = "unknown",
    minutes_basis: str = "unknown",
) -> tuple[pd.DataFrame, list[str], Path]:
    """Copy a user-supplied source unchanged and normalize recognized columns."""
    if not source.exists():
        raise FileNotFoundError(source)
    snapshot_date = snapshot_date or date.today().isoformat()
    raw_dir.mkdir(parents=True, exist_ok=True)
    preserved = raw_dir / f"{snapshot_date}_{source.name}"
    if source.resolve() != preserved.resolve():
        shutil.copy2(source, preserved)
    frame = _read_source(preserved)
    normalized, missing = _normalize_projection_frame(
        frame, provider, snapshot_date, stat_basis, minutes_basis
    )
    return normalized, missing, preserved


def import_google_sheet_projections(
    spreadsheet_id: str,
    gid: int,
    raw_dir: Path,
    provider: str = "Hashtag Basketball",
    snapshot_date: str | None = None,
    stat_basis: str = "season_total",
    minutes_basis: str = "per_game",
    timeout_seconds: float = 30.0,
) -> tuple[pd.DataFrame, list[str], Path]:
    """Export one public Google Sheet tab as CSV, preserve it, and normalize it."""
    snapshot_date = snapshot_date or date.today().isoformat()
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export"
    response = requests.get(
        url, params={"format": "csv", "gid": int(gid)}, timeout=timeout_seconds,
        headers={"User-Agent": "fantasy-basketball-model/0.1"},
    )
    response.raise_for_status()
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    preserved = raw_dir / f"google_sheet_{spreadsheet_id}_{gid}_{stamp}.csv"
    preserved.write_bytes(response.content)
    frame = pd.read_csv(preserved)
    normalized, missing = _normalize_projection_frame(
        frame, provider, snapshot_date, stat_basis, minutes_basis
    )
    return normalized, missing, preserved

