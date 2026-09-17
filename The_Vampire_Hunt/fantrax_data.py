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


def _fetch_player_stats(week: int, status_filter: str) -> dict[str, Any]:
    """Fetch one weekly Fantrax player table using this league's scoring."""
    params = {
        "view": "STATS",
        "positionOrGroup": "ALL",
        "seasonOrProjection": "SEASON_23l_BY_PERIOD",
        "timeframeTypeCode": "BY_PERIOD",
        "transactionPeriod": str(int(week)),
        "statusOrTeamFilter": status_filter,
        "sortType": "SCORE",
        "sortReversed": False,
        "maxResultsPerPage": "500",
        "pageNumber": "1",
    }
    response = requests.post(
        PRIVATE_API_URL,
        params={"leagueId": LEAGUE_ID},
        json={"msgs": [{"method": "getPlayerStats", "data": params}]},
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    page_error = payload.get("pageError")
    if page_error:
        code = page_error.get("code", page_error) if isinstance(page_error, dict) else page_error
        raise FantraxUnavailable(f"Fantrax player scores unavailable: {code}")
    try:
        return payload["responses"][0]["data"]
    except (KeyError, IndexError, TypeError) as exc:
        raise FantraxUnavailable("Fantrax returned an unexpected player-score response.") from exc


def _stat_column(data: dict[str, Any], key: str, sort_key: str = "") -> int | None:
    for index, header in enumerate(data.get("tableHeader", {}).get("cells", [])):
        if str(header.get("key", "")).lower() == key.lower():
            return index
        if sort_key and str(header.get("sortKey", "")).upper() == sort_key.upper():
            return index
    return None


def fetch_player_scores(week: int, auth_cookie: str = "") -> dict[str, float]:
    """Fetch Fantrax's official weekly FPts for rostered and sheet-selected players."""
    cookie_header = str(auth_cookie).strip()
    if cookie_header and "=" not in cookie_header:
        cookie_header = f"JSESSIONID={cookie_header}"
    # The Vampire roster is maintained in the public sheet and can contain a
    # player who Fantrax currently labels a free agent. ALL_TAKEN alone omits
    # those selections (notably DST units), so merge the complete player table.
    data_sources = [_fetch_player_stats(week, "ALL_TAKEN")]
    try:
        data_sources.append(_fetch_player_stats(week, "ALL"))
    except (requests.RequestException, FantraxUnavailable, ValueError, KeyError):
        # Keep the normal rostered-player scores if the supplemental free-agent
        # table is briefly unavailable.
        pass

    scores: dict[str, float] = {}
    for data in data_sources:
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


def fetch_available_players(week: int) -> list[dict[str, Any]]:
    """Return the top weekly scorers across Fantrax's complete NFL player pool."""
    data = _fetch_player_stats(week, "ALL")
    score_index = _stat_column(data, "fpts", "SCORE")
    status_index = _stat_column(data, "status", "STATUS")
    if score_index is None:
        raise FantraxUnavailable("Fantrax's FPts column was not found.")

    players = []
    for row in data.get("statsTable", []):
        scorer = row.get("scorer") or {}
        cells = row.get("cells") or []
        player_id = str(scorer.get("scorerId", "")).strip()
        if not player_id or score_index >= len(cells):
            continue
        score = _score_from_cell(cells[score_index])
        if score is None:
            continue
        name = str(scorer.get("name") or scorer.get("shortName") or player_id).strip()
        position = str(scorer.get("posShortNames") or "").split(",", 1)[0].strip()
        position = LEAGUE_POSITION_OVERRIDES.get(name.lower(), position)
        if position not in {"QB", "RB", "WR", "TE", "K", "DST"}:
            continue
        roster_status = ""
        if status_index is not None and status_index < len(cells):
            status_cell = cells[status_index]
            if isinstance(status_cell, dict):
                roster_status = str(status_cell.get("toolTip") or status_cell.get("content") or "")
        players.append(
            {
                "player_id": player_id,
                "player": name,
                "position": position,
                "nfl_team": str(scorer.get("teamShortName") or "FA"),
                "score": score,
                "roster_status": roster_status,
            }
        )
    return players


def fetch_fantasypros_weekly_rankings(week: int) -> list[dict[str, Any]]:
    """Fetch FantasyPros expert-consensus weekly ranking projections, not actuals."""
    # The league awards one point per reception, so use FantasyPros' PPR
    # weekly projection pages (not the post-game leaders/actuals pages).
    position_pages = {
        position: f"https://www.fantasypros.com/nfl/rankings/{'ppr-' if position in {'RB', 'WR', 'TE'} else ''}{position.lower()}.php"
        for position in ("QB", "RB", "WR", "TE", "K", "DST")
    }
    players: list[dict[str, Any]] = []
    for position, url in position_pages.items():
        try:
            response = requests.get(
                url,
                params={"week": int(week)},
                headers={"User-Agent": "Mozilla/5.0 (compatible; VampireHunt/1.0)"},
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException:
            # Keep other positions available if FantasyPros briefly blocks or
            # times out on one ranking page.
            continue
        # FantasyPros renders the ranking table from an embedded ecrData JSON
        # object.  Reading that object keeps this on ranking projections (not
        # post-game actuals) and gives us the full player pool for each spot.
        marker = response.text.find("var ecrData =")
        if marker < 0:
            continue
        json_start = response.text.find("{", marker)
        json_end = response.text.find("};", json_start)
        if json_start < 0 or json_end < 0:
            continue
        try:
            payload = json.loads(response.text[json_start : json_end + 1])
        except json.JSONDecodeError:
            continue
        for item in payload.get("players", []):
            source_position = str(item.get("player_position_id") or "").upper().replace("D/", "")
            requested_position = position.upper().replace("D/", "")
            if source_position and source_position != requested_position:
                continue
            try:
                rank = int(item.get("rank_ecr"))
            except (TypeError, ValueError):
                continue
            player_id = item.get("player_id")
            name = str(item.get("player_name") or "").strip()
            if not player_id or not name:
                continue
            projection = item.get("r2p_pts")
            try:
                projection = float(projection)
            except (TypeError, ValueError):
                projection = None
            players.append(
                {
                    "player_id": f"fantasypros-{player_id}",
                    "player": name,
                    "position": position,
                    "nfl_team": str(item.get("player_team_id") or "FA"),
                    "rank": rank,
                    "projection": projection,
                    "score": None,
                }
            )
    return players


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
