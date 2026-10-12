from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


BASE_URL = "https://www.fantrax.com/fxea/general"


class FantraxError(RuntimeError):
    """Raised when a Fantrax response cannot be safely consumed."""


@dataclass
class FantraxClient:
    league_id: str
    raw_dir: Path
    timeout_seconds: float = 30.0
    session: requests.Session | None = None

    def __post_init__(self) -> None:
        self.session = self.session or requests.Session()
        self.session.headers.update({"User-Agent": "fantasy-basketball-model/0.1"})
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _get(self, endpoint: str, params: dict[str, Any], snapshot_name: str) -> dict[str, Any]:
        assert self.session is not None
        response = self.session.get(
            f"{BASE_URL}/{endpoint}", params=params, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except requests.JSONDecodeError as exc:
            raise FantraxError(f"Fantrax returned non-JSON content for {endpoint}") from exc
        if not isinstance(payload, dict):
            raise FantraxError(f"Expected an object from {endpoint}, got {type(payload).__name__}")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snapshot = self.raw_dir / f"{snapshot_name}_{stamp}.json"
        snapshot.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return payload

    def fetch_rosters(self, period: int) -> tuple[pd.DataFrame, pd.DataFrame]:
        payload = self._get(
            "getTeamRosters",
            {"leagueId": self.league_id, "period": int(period)},
            f"rosters_period_{int(period):03d}",
        )
        rosters = payload.get("rosters")
        if not isinstance(rosters, dict):
            raise FantraxError("Roster response is missing the 'rosters' object")
        roster_rows: list[dict[str, Any]] = []
        team_rows: list[dict[str, Any]] = []
        for team_id, team_payload in rosters.items():
            if not isinstance(team_payload, dict):
                continue
            team_name = str(team_payload.get("teamName", "")).strip()
            team_rows.append({"fantasy_team_id": str(team_id), "fantasy_team_name": team_name})
            items = team_payload.get("rosterItems") or []
            for item in items:
                if not isinstance(item, dict):
                    continue
                roster_rows.append(
                    {
                        "fantasy_team_id": str(team_id),
                        "fantasy_team_name": team_name,
                        "fantrax_player_id": str(item.get("id", "")).strip(),
                        "roster_position": str(item.get("position", "")).strip(),
                        "roster_status": str(item.get("status", "")).strip(),
                        "period": int(payload.get("period", period)),
                    }
                )
        teams = pd.DataFrame(team_rows).drop_duplicates("fantasy_team_id")
        roster = pd.DataFrame(roster_rows)
        return roster, teams

    def fetch_player_catalog(self) -> pd.DataFrame:
        payload = self._get("getPlayerIds", {"sport": "NBA"}, "nba_player_catalog")
        rows: list[dict[str, Any]] = []
        for fallback_id, item in payload.items():
            if not isinstance(item, dict):
                continue
            raw_name = str(item.get("name", "")).strip()
            if "," in raw_name:
                last, first = [part.strip() for part in raw_name.split(",", 1)]
                display_name = f"{first} {last}".strip()
            else:
                display_name = raw_name
            rows.append(
                {
                    "fantrax_player_id": str(item.get("fantraxId") or fallback_id),
                    "player_name": display_name,
                    "nba_team": str(item.get("team", "")).strip(),
                    "eligible_positions": str(item.get("position", "")).strip(),
                }
            )
        return pd.DataFrame(rows).drop_duplicates("fantrax_player_id")

    def fetch_schedule(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        payload = self._get(
            "getLeagueInfo", {"leagueId": self.league_id}, "league_info"
        )
        schedule_rows: list[dict[str, Any]] = []
        team_rows: list[dict[str, Any]] = []
        for period_payload in payload.get("matchups", []):
            period = int(period_payload.get("period"))
            for matchup_number, matchup in enumerate(period_payload.get("matchupList", []), start=1):
                row: dict[str, Any] = {"period": period, "matchup_number": matchup_number}
                for side in ("away", "home"):
                    team = matchup.get(side) or {}
                    row[f"{side}_team_id"] = str(team.get("id", ""))
                    row[f"{side}_team_name"] = str(team.get("name", ""))
                    row[f"{side}_short_name"] = str(team.get("shortName", ""))
                    team_rows.append(
                        {
                            "fantasy_team_id": str(team.get("id", "")),
                            "fantasy_team_name": str(team.get("name", "")),
                            "short_name": str(team.get("shortName", "")),
                        }
                    )
                schedule_rows.append(row)
        teams = pd.DataFrame(team_rows)
        if not teams.empty:
            teams = teams[
                teams["fantasy_team_id"].astype(str).str.strip().ne("")
                & teams["fantasy_team_name"].astype(str).str.strip().ne("")
            ].drop_duplicates("fantasy_team_id")
        return pd.DataFrame(schedule_rows), teams

