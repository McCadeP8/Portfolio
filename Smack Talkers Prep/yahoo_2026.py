"""Yahoo Fantasy Football refresh and cache helpers for the 2026 leagues."""

from __future__ import annotations

import csv
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


YAHOO_API_ROOT = "https://pub-api-ro.fantasysports.yahoo.com/fantasy/v2"
DEFAULT_CONFIG = Path("data/yahoo_2026/leagues.csv")
DEFAULT_RAW_DIR = Path("data/yahoo_2026/raw")
DEFAULT_PROCESSED_DIR = Path("data/yahoo_2026/processed")

STATUS_COLUMNS = [
    "league_label", "draft_type", "league_url", "league_id", "game_key",
    "league_key", "yahoo_league_name", "season", "current_week",
    "start_week", "end_week", "start_date", "end_date", "team_count",
    "success", "error", "fetched_at_utc", "raw_cache_path",
]
TEAM_COLUMNS = [
    "league_label", "draft_type", "league_key", "league_id", "team_key",
    "team_id", "team_name", "team_url", "logo_url", "manager_nickname",
    "manager_guid", "is_commissioner", "previous_season_team_rank",
    "number_of_moves", "number_of_trades", "draft_grade", "fetched_at_utc",
]
MATCHUP_COLUMNS = [
    "league_label", "draft_type", "league_key", "league_id", "week",
    "matchup_index", "week_start", "week_end", "status", "is_playoffs",
    "is_consolation", "is_matchup_of_the_week", "winner_team_key",
    "team_1_key", "team_1_name", "team_1_points", "team_1_projected_points",
    "team_1_win_probability", "team_2_key", "team_2_name", "team_2_points",
    "team_2_projected_points", "team_2_win_probability", "fetched_at_utc",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def extract_league_id(value: str) -> str:
    """Extract a Yahoo league ID from a league URL or a bare numeric ID."""
    value = str(value).strip()
    if value.isdigit():
        return value
    match = re.search(r"football\.fantasysports\.yahoo\.com/f1/(\d+)(?:/|$)", value)
    if not match:
        raise ValueError(f"Could not extract a Yahoo football league ID from {value!r}")
    return match.group(1)


def load_league_config(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Yahoo league config not found: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    enabled = []
    for row in rows:
        if str(row.get("enabled", "1")).strip().lower() in {"0", "false", "no", "off"}:
            continue
        league_url = str(row.get("league_url", "")).strip()
        configured_id = str(row.get("league_id", "")).strip()
        parsed_id = extract_league_id(league_url or configured_id)
        if configured_id and parsed_id != configured_id:
            raise ValueError(
                f"Configured league ID {configured_id} does not match URL ID {parsed_id}"
            )
        enabled.append({
            "league_label": str(row.get("league_label", parsed_id)).strip(),
            "draft_type": str(row.get("draft_type", "")).strip(),
            "league_url": league_url,
            "league_id": parsed_id,
        })
    if not enabled:
        raise ValueError(f"No enabled Yahoo leagues found in {path}")
    return enabled


def fetch_json(url: str, timeout: int = 30) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Smack-Talkers-Prep/2026 Yahoo updater"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def derive_current_nfl_game_key(fetcher=fetch_json) -> tuple[str, dict[str, Any]]:
    payload = fetcher(f"{YAHOO_API_ROOT}/game/nfl?format=json")
    game = payload.get("fantasy_content", {}).get("game", [])
    for item in game if isinstance(game, list) else [game]:
        if isinstance(item, dict) and item.get("game_key"):
            return str(item["game_key"]), payload
    raise ValueError("Yahoo game response did not include an NFL game_key")


def _league_parts(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    league = payload.get("fantasy_content", {}).get("league", [])
    if not isinstance(league, list) or not league or not isinstance(league[0], dict):
        raise ValueError("Yahoo response did not contain the expected league structure")
    metadata = league[0]
    resources = next((item for item in league[1:] if isinstance(item, dict)), {})
    return metadata, resources


def _indexed_values(mapping: Any) -> list[Any]:
    if not isinstance(mapping, dict):
        return []
    keys = sorted((key for key in mapping if str(key).isdigit()), key=lambda key: int(key))
    return [mapping[key] for key in keys]


def _find_first(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for nested in value.values():
            found = _find_first(nested, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_first(nested, key)
            if found is not None:
                return found
    return None


def _team_record(team_node: Any) -> dict[str, Any]:
    team = team_node.get("team", team_node) if isinstance(team_node, dict) else team_node
    record: dict[str, Any] = {}
    metadata = team[0] if isinstance(team, list) and team and isinstance(team[0], list) else team
    if isinstance(metadata, list):
        for item in metadata:
            if not isinstance(item, dict):
                continue
            for key, value in item.items():
                if not isinstance(value, (dict, list)):
                    record[key] = value
    manager = _find_first(metadata, "manager") or {}
    logo = _find_first(metadata, "team_logo") or {}
    record.update({
        "manager_nickname": manager.get("nickname") if isinstance(manager, dict) else None,
        "manager_guid": manager.get("guid") if isinstance(manager, dict) else None,
        "is_commissioner": manager.get("is_commissioner") if isinstance(manager, dict) else None,
        "logo_url": logo.get("url") if isinstance(logo, dict) else None,
        "team_points": _find_first(team, "team_points"),
        "team_projected_points": _find_first(team, "team_projected_points"),
        "win_probability": _find_first(team, "win_probability"),
    })
    return record


def _number(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("total", value.get("value"))
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_teams(
    payload: dict[str, Any], config: dict[str, str], fetched_at: str
) -> list[dict[str, Any]]:
    metadata, resources = _league_parts(payload)
    league_key = str(metadata.get("league_key", ""))
    collection = resources.get("teams", {})
    rows = []
    for node in _indexed_values(collection):
        team = _team_record(node)
        rows.append({
            "league_label": config["league_label"],
            "draft_type": config["draft_type"],
            "league_key": league_key,
            "league_id": config["league_id"],
            "team_key": team.get("team_key"),
            "team_id": team.get("team_id"),
            "team_name": team.get("name"),
            "team_url": team.get("url"),
            "logo_url": team.get("logo_url"),
            "manager_nickname": team.get("manager_nickname"),
            "manager_guid": team.get("manager_guid"),
            "is_commissioner": team.get("is_commissioner"),
            "previous_season_team_rank": team.get("previous_season_team_rank"),
            "number_of_moves": team.get("number_of_moves"),
            "number_of_trades": team.get("number_of_trades"),
            "draft_grade": team.get("draft_grade"),
            "fetched_at_utc": fetched_at,
        })
    return rows


def normalize_matchups(
    payload: dict[str, Any], config: dict[str, str], fetched_at: str
) -> list[dict[str, Any]]:
    metadata, resources = _league_parts(payload)
    league_key = str(metadata.get("league_key", ""))
    scoreboard = resources.get("scoreboard", {})
    week = scoreboard.get("week")
    scoreboard_body = next(
        (item for item in _indexed_values(scoreboard) if isinstance(item, dict) and "matchups" in item),
        {},
    )
    rows = []
    for index, node in enumerate(_indexed_values(scoreboard_body.get("matchups", {})), start=1):
        matchup = node.get("matchup", node) if isinstance(node, dict) else {}
        teams_body = next(
            (item for item in _indexed_values(matchup) if isinstance(item, dict) and "teams" in item),
            {},
        )
        team_records = [_team_record(item) for item in _indexed_values(teams_body.get("teams", {}))]
        team_records += [{}] * (2 - len(team_records))
        left, right = team_records[:2]
        rows.append({
            "league_label": config["league_label"],
            "draft_type": config["draft_type"],
            "league_key": league_key,
            "league_id": config["league_id"],
            "week": int(week or matchup.get("week") or 0),
            "matchup_index": index,
            "week_start": matchup.get("week_start"),
            "week_end": matchup.get("week_end"),
            "status": matchup.get("status"),
            "is_playoffs": matchup.get("is_playoffs"),
            "is_consolation": matchup.get("is_consolation"),
            "is_matchup_of_the_week": matchup.get("is_matchup_of_the_week"),
            "winner_team_key": matchup.get("winner_team_key"),
            "team_1_key": left.get("team_key"),
            "team_1_name": left.get("name"),
            "team_1_points": _number(left.get("team_points")),
            "team_1_projected_points": _number(left.get("team_projected_points")),
            "team_1_win_probability": _number(left.get("win_probability")),
            "team_2_key": right.get("team_key"),
            "team_2_name": right.get("name"),
            "team_2_points": _number(right.get("team_points")),
            "team_2_projected_points": _number(right.get("team_projected_points")),
            "team_2_win_probability": _number(right.get("win_probability")),
            "fetched_at_utc": fetched_at,
        })
    return rows


def status_row(
    payload: dict[str, Any], config: dict[str, str], game_key: str,
    fetched_at: str, raw_cache_path: Path,
) -> dict[str, Any]:
    metadata, _ = _league_parts(payload)
    return {
        "league_label": config["league_label"],
        "draft_type": config["draft_type"],
        "league_url": config["league_url"],
        "league_id": config["league_id"],
        "game_key": game_key,
        "league_key": f"{game_key}.l.{config['league_id']}",
        "yahoo_league_name": metadata.get("name"),
        "season": metadata.get("season"),
        "current_week": metadata.get("current_week"),
        "start_week": metadata.get("start_week"),
        "end_week": metadata.get("end_week"),
        "start_date": metadata.get("start_date"),
        "end_date": metadata.get("end_date"),
        "team_count": metadata.get("num_teams"),
        "success": True,
        "error": "",
        "fetched_at_utc": fetched_at,
        "raw_cache_path": str(raw_cache_path),
    }


def failure_status_row(
    config: dict[str, str], game_key: str, fetched_at: str, error: Exception
) -> dict[str, Any]:
    return {
        "league_label": config["league_label"], "draft_type": config["draft_type"],
        "league_url": config["league_url"], "league_id": config["league_id"],
        "game_key": game_key, "league_key": f"{game_key}.l.{config['league_id']}",
        "yahoo_league_name": None, "season": None, "current_week": None,
        "start_week": None, "end_week": None, "start_date": None, "end_date": None,
        "team_count": None, "success": False, "error": f"{type(error).__name__}: {error}",
        "fetched_at_utc": fetched_at, "raw_cache_path": None,
    }


def atomic_json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(path)


def _merge_and_write(
    path: Path, rows: list[dict[str, Any]], columns: list[str], replace_keys: Iterable[str]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    incoming = pd.DataFrame(rows, columns=columns)
    if path.exists():
        existing = pd.read_parquet(path)
        if "league_key" in existing.columns:
            existing = existing.loc[~existing["league_key"].astype(str).isin(set(replace_keys))]
        incoming = pd.concat([existing, incoming], ignore_index=True)
    temporary = path.with_suffix(".tmp.parquet")
    incoming.to_parquet(temporary, index=False)
    temporary.replace(path)


def refresh_yahoo_2026(
    root: Path, config_path: Path | None = None, fetcher=fetch_json
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    config_path = config_path or root / DEFAULT_CONFIG
    leagues = load_league_config(config_path)
    game_key, game_payload = derive_current_nfl_game_key(fetcher)
    fetched_at = utc_now()
    statuses: list[dict[str, Any]] = []
    teams: list[dict[str, Any]] = []
    matchups: list[dict[str, Any]] = []
    successful_keys: list[str] = []

    for config in leagues:
        league_key = f"{game_key}.l.{config['league_id']}"
        slug = re.sub(r"[^a-z0-9]+", "_", config["league_label"].lower()).strip("_")
        raw_path = root / DEFAULT_RAW_DIR / slug / "latest.json"
        try:
            teams_payload = fetcher(f"{YAHOO_API_ROOT}/league/{league_key}/teams?format=json")
            scoreboard_payload = fetcher(f"{YAHOO_API_ROOT}/league/{league_key}/scoreboard?format=json")
            atomic_json_write(raw_path, {
                "fetched_at_utc": fetched_at,
                "game_key": game_key,
                "league_key": league_key,
                "source_league_url": config["league_url"],
                "game": game_payload,
                "teams": teams_payload,
                "scoreboard": scoreboard_payload,
            })
            statuses.append(status_row(teams_payload, config, game_key, fetched_at, raw_path))
            teams.extend(normalize_teams(teams_payload, config, fetched_at))
            matchups.extend(normalize_matchups(scoreboard_payload, config, fetched_at))
            successful_keys.append(league_key)
        except Exception as error:  # Keep the other league and last good cache usable.
            statuses.append(failure_status_row(config, game_key, fetched_at, error))

    processed = root / DEFAULT_PROCESSED_DIR
    configured_keys = [f"{game_key}.l.{row['league_id']}" for row in leagues]
    _merge_and_write(processed / "league_status.parquet", statuses, STATUS_COLUMNS, configured_keys)
    _merge_and_write(processed / "teams.parquet", teams, TEAM_COLUMNS, successful_keys)
    _merge_and_write(processed / "matchups.parquet", matchups, MATCHUP_COLUMNS, successful_keys)
    return statuses, teams, matchups


def load_cached_yahoo_2026(root: Path) -> dict[str, pd.DataFrame]:
    processed = root / DEFAULT_PROCESSED_DIR
    result = {}
    for name, columns in {
        "status": STATUS_COLUMNS, "teams": TEAM_COLUMNS, "matchups": MATCHUP_COLUMNS,
    }.items():
        path = processed / ("league_status.parquet" if name == "status" else f"{name}.parquet")
        result[name] = pd.read_parquet(path) if path.exists() else pd.DataFrame(columns=columns)
    return result
