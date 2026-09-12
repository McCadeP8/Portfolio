from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

import requests


LEAGUE_ID = "et040dehmtxkchmx"
BASE_URL = "https://www.fantrax.com/fxea/general"
PRIVATE_API_URL = "https://www.fantrax.com/fxpa/req"
SNAPSHOT_PATH = Path(__file__).parent / "data" / "fantrax_snapshot.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VampireHunt/1.0)"}

DEFENSE_TEAMS = {
    "20010": ("Buffalo", "BUF"),
    "20020": ("Miami", "MIA"),
    "20030": ("New England", "NE"),
    "20040": ("NY Jets", "NYJ"),
    "20050": ("Baltimore", "BAL"),
    "20060": ("Cincinnati", "CIN"),
    "20070": ("Cleveland", "CLE"),
    "20080": ("Pittsburgh", "PIT"),
    "20090": ("Houston", "HOU"),
    "20100": ("Indianapolis", "IND"),
    "20110": ("Jacksonville", "JAX"),
    "20120": ("Tennessee", "TEN"),
    "20130": ("Denver", "DEN"),
    "20140": ("Kansas City", "KC"),
    "20151": ("Las Vegas", "LV"),
    "20161": ("LA Chargers", "LAC"),
    "20170": ("Dallas", "DAL"),
    "20180": ("NY Giants", "NYG"),
    "20190": ("Philadelphia", "PHI"),
    "20200": ("Washington", "WAS"),
    "20210": ("Chicago", "CHI"),
    "20220": ("Detroit", "DET"),
    "20230": ("Green Bay", "GB"),
    "20240": ("Minnesota", "MIN"),
    "20250": ("Atlanta", "ATL"),
    "20260": ("Carolina", "CAR"),
    "20270": ("New Orleans", "NO"),
    "20280": ("Tampa Bay", "TB"),
    "20290": ("Arizona", "ARI"),
    "20295": ("LA Rams", "LAR"),
    "20310": ("San Francisco", "SF"),
    "20320": ("Seattle", "SEA"),
}

# Fantrax lists Connor Heyward as a hybrid RB/TE; this league treats him as RB only.
LEAGUE_POSITION_OVERRIDES = {"connor heyward": "RB"}


class FantraxUnavailable(RuntimeError):
    pass


def _get_json(path: str, **params: Any) -> Any:
    response = requests.get(
        f"{BASE_URL}/{path}",
        params=params,
        headers=HEADERS,
        timeout=8,
    )
    response.raise_for_status()
    return response.json()


def normalize_team_name(value: str) -> str:
    return re.sub(r"\s*\(\d+\s+of\s+\d+\s+lives?\)\s*$", "", str(value), flags=re.I).strip()


def parse_lives(value: str) -> int | None:
    match = re.search(r"\((\d+)\s+of\s+\d+\s+lives?\)", str(value), flags=re.I)
    return int(match.group(1)) if match else None


def display_player_name(value: str) -> str:
    parts = [part.strip() for part in str(value).split(",", 1)]
    return f"{parts[1]} {parts[0]}" if len(parts) == 2 else str(value).strip()


def enrich_roster_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for original in rows:
        row = dict(original)
        player_name = str(row.get("player", "")).strip().lower()
        if player_name in LEAGUE_POSITION_OVERRIDES:
            row["position"] = LEAGUE_POSITION_OVERRIDES[player_name]
        defense = DEFENSE_TEAMS.get(str(row.get("player_id", "")))
        if str(row.get("position", "")) == "DST" and defense:
            row["player"], row["nfl_team"] = defense
        enriched.append(row)
    return enriched


def fetch_league_info() -> dict[str, Any]:
    return _get_json("getLeagueInfo", leagueId=LEAGUE_ID)


def fetch_player_directory() -> dict[str, Any]:
    return _get_json("getPlayerIds", sport="NFL")


def fetch_roster_week(week: int, player_directory: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    players = player_directory if player_directory is not None else fetch_player_directory()
    payload = _get_json("getTeamRosters", leagueId=LEAGUE_ID, period=int(week))
    rows: list[dict[str, Any]] = []
    for team_id, roster in payload.get("rosters", {}).items():
        team_label = str(roster.get("teamName", ""))
        team_name = normalize_team_name(team_label)
        lives_remaining = parse_lives(team_label)
        for item in roster.get("rosterItems") or []:
            player_id = str(item.get("id", ""))
            player = players.get(player_id, {})
            rows.append(
                {
                    "week": int(week),
                    "team_id": str(team_id),
                    "team": team_name,
                    "lives_remaining": lives_remaining,
                    "player_id": player_id,
                    "player": display_player_name(player.get("name", player_id)),
                    "position": str(item.get("position") or player.get("position") or "—"),
                    "nfl_team": str(player.get("team") or "FA"),
                    "status": str(item.get("status") or "ROSTERED"),
                    "score": None,
                }
            )
    return enrich_roster_rows(rows)


def fetch_standings() -> list[dict[str, Any]]:
    payload = _get_json("getStandings", leagueId=LEAGUE_ID)
    rows = []
    for item in payload if isinstance(payload, list) else []:
        raw_score = item.get("points")
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = None
        rows.append(
            {
                "team": normalize_team_name(item.get("teamName", "")),
                "team_id": str(item.get("teamId", "")),
                "score": score,
                "rank": item.get("rank"),
                "lives_remaining": parse_lives(item.get("teamName", "")),
            }
        )
    return rows


def _score_from_cell(cell: Any) -> float | None:
    if isinstance(cell, (int, float)) and not isinstance(cell, bool):
        return float(cell)
    if isinstance(cell, str):
        value = cell.strip().replace(",", "")
        if re.fullmatch(r"-?\d+(?:\.\d+)?", value):
            return float(value)
        return None
    if isinstance(cell, dict):
        for key in ("value", "rawValue", "content", "text", "displayValue", "score"):
            if key in cell:
                value = _score_from_cell(cell[key])
                if value is not None:
                    return value
    return None


def fetch_player_scores(week: int, auth_cookie: str = "") -> dict[str, float]:
    """Fetch Fantrax's official weekly FPts for every rostered player."""
    cookie_header = str(auth_cookie).strip()
    if cookie_header and "=" not in cookie_header:
        cookie_header = f"JSESSIONID={cookie_header}"
    params = {
        "view": "STATS",
        "positionOrGroup": "ALL",
        "seasonOrProjection": "SEASON_23l_BY_PERIOD",
        "timeframeTypeCode": "BY_PERIOD",
        "transactionPeriod": str(int(week)),
        "statusOrTeamFilter": "ALL_TAKEN",
        "sortType": "SCORE",
        "sortReversed": False,
        "maxResultsPerPage": "500",
        "pageNumber": "1",
    }
    request_headers = dict(HEADERS)
    if cookie_header:
        request_headers["Cookie"] = cookie_header
    response = requests.post(
        PRIVATE_API_URL,
        params={"leagueId": LEAGUE_ID},
        json={"msgs": [{"method": "getPlayerStats", "data": params}]},
        headers=request_headers,
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    page_error = payload.get("pageError")
    if page_error:
        code = page_error.get("code", page_error) if isinstance(page_error, dict) else page_error
        raise FantraxUnavailable(f"Fantrax player scores unavailable: {code}")
    try:
        data = payload["responses"][0]["data"]
    except (KeyError, IndexError, TypeError) as exc:
        raise FantraxUnavailable("Fantrax returned an unexpected player-score response.") from exc

    header_cells = data.get("tableHeader", {}).get("cells", [])
    score_index = None
    for index, header in enumerate(header_cells):
        if str(header.get("key", "")).lower() == "fpts" or str(header.get("sortKey", "")).upper() == "SCORE":
            score_index = index
            break
    if score_index is None:
        for index, header in enumerate(header_cells):
            if str(header.get("shortName", "")).lower() == "fpts":
                score_index = index
                break
    if score_index is None:
        for index, header in enumerate(header_cells):
            searchable = " ".join(
                str(header.get(key, "")) for key in ("key", "name", "shortName", "sortKey")
            ).lower()
            if "fantasy point" in searchable:
                score_index = index
                break
    if score_index is None:
        raise FantraxUnavailable("Fantrax's FPts column was not found.")

    scores: dict[str, float] = {}
    for row in data.get("statsTable", []):
        scorer = row.get("scorer") or {}
        scorer_id = str(scorer.get("scorerId", "")).strip()
        cells = row.get("cells") or []
        if not scorer_id or score_index >= len(cells):
            continue
        score = _score_from_cell(cells[score_index])
        if score is not None:
            scores[scorer_id] = score
            # Roster payloads identify DST units by NFL team ID, while the
            # Players table gives them a separate scorer ID.
            if scorer.get("team") and scorer.get("teamId") is not None:
                scores[str(scorer["teamId"])] = score
    return scores


def current_week(info: dict[str, Any] | None = None, now: datetime | None = None) -> int:
    periods = (info or {}).get("rosterPeriods", [])
    current = now or datetime.now().astimezone()
    for period in periods:
        try:
            start = datetime.fromisoformat(period["startDate"])
            end = datetime.fromisoformat(period["endDate"])
        except (KeyError, TypeError, ValueError):
            continue
        if start <= current <= end:
            return int(period["number"])
    started = []
    for period in periods:
        try:
            if datetime.fromisoformat(period["startDate"]) <= current:
                started.append(int(period["number"]))
        except (KeyError, TypeError, ValueError):
            continue
    return max(started, default=1)


def build_snapshot() -> dict[str, Any]:
    info = fetch_league_info()
    players = fetch_player_directory()
    rosters = {str(week): fetch_roster_week(week, players) for week in range(1, 19)}
    return {
        "league_id": LEAGUE_ID,
        "league_name": info.get("leagueName", "The Vampire Hunt"),
        "season": info.get("seasonYear"),
        "generated_at": datetime.now().astimezone().isoformat(),
        "current_week": current_week(info),
        "rosters": rosters,
        "standings": fetch_standings(),
    }


def save_snapshot(snapshot: dict[str, Any], path: Path = SNAPSHOT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"rosters": {}, "standings": [], "current_week": 1}
    return json.loads(path.read_text(encoding="utf-8"))


def league_data(week: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    try:
        players = fetch_player_directory()
        return fetch_roster_week(week, players), fetch_standings(), True
    except (requests.RequestException, ValueError, KeyError):
        snapshot = load_snapshot()
        return snapshot.get("rosters", {}).get(str(week), []), snapshot.get("standings", []), False
