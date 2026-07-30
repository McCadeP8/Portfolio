from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import re
from typing import Any, Iterable

import pandas as pd

from ..network import CachedHttpClient


SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
SUMMARY_URLS = (
    "https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/summary",
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary",
)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "--"):
            return default
        return float(str(value).replace(",", "").replace("+", ""))
    except (TypeError, ValueError):
        return default


def _made_attempted(value: Any) -> tuple[int, int]:
    match = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", str(value or ""))
    return (int(match.group(1)), int(match.group(2))) if match else (0, 0)


def _minutes(value: Any) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    if text.startswith("PT"):
        hours = re.search(r"(\d+(?:\.\d+)?)H", text)
        minutes = re.search(r"(\d+(?:\.\d+)?)M", text)
        seconds = re.search(r"(\d+(?:\.\d+)?)S", text)
        return (
            _number(hours.group(1) if hours else 0) * 60
            + _number(minutes.group(1) if minutes else 0)
            + _number(seconds.group(1) if seconds else 0) / 60
        )
    if ":" in text:
        minute_text, second_text = text.split(":", 1)
        return _number(minute_text) + _number(second_text) / 60
    return _number(text)


@dataclass(frozen=True)
class LiveGame:
    event_id: str
    game_date: str
    state: str
    status: str
    period: int
    clock: str
    completed: bool
    home_team_id: str
    home_abbreviation: str
    home_name: str
    home_score: float
    away_team_id: str
    away_abbreviation: str
    away_name: str
    away_score: float
    fetched_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LiveSnapshot:
    game_date: str
    fetched_at: str
    games: tuple[LiveGame, ...]
    player_stats: pd.DataFrame
    raw_scoreboard: dict[str, Any]

    def game_frame(self) -> pd.DataFrame:
        return pd.DataFrame([game.as_dict() for game in self.games])


def parse_live_game(event: dict[str, Any], *, fetched_at: str | None = None) -> LiveGame:
    competition = (event.get("competitions") or [{}])[0]
    competitors = competition.get("competitors") or []
    by_side = {str(item.get("homeAway", "")): item for item in competitors}
    home = by_side.get("home", {})
    away = by_side.get("away", {})
    status = event.get("status") or competition.get("status") or {}
    status_type = status.get("type") or {}
    state = str(status_type.get("state") or "pre")
    fetched = fetched_at or datetime.now(timezone.utc).isoformat()

    def team_values(competitor: dict[str, Any]) -> tuple[str, str, str, float]:
        team = competitor.get("team") or {}
        return (
            str(team.get("id") or ""),
            str(team.get("abbreviation") or ""),
            str(team.get("displayName") or team.get("name") or ""),
            _number(competitor.get("score")),
        )

    home_id, home_abbr, home_name, home_score = team_values(home)
    away_id, away_abbr, away_name, away_score = team_values(away)
    return LiveGame(
        event_id=str(event.get("id") or ""),
        game_date=str(event.get("date") or "")[:10],
        state=state,
        status=str(status_type.get("shortDetail") or status_type.get("detail") or status_type.get("description") or ""),
        period=int(_number(status.get("period"))),
        clock=str((status.get("displayClock") or (status.get("clock") or {}).get("displayValue") or "")),
        completed=bool(status_type.get("completed")),
        home_team_id=home_id,
        home_abbreviation=home_abbr,
        home_name=home_name,
        home_score=home_score,
        away_team_id=away_id,
        away_abbreviation=away_abbr,
        away_name=away_name,
        away_score=away_score,
        fetched_at=fetched,
    )


def parse_player_boxscore(summary: dict[str, Any], event: dict[str, Any]) -> pd.DataFrame:
    event_id = str(event.get("id") or "")
    game_date = pd.to_datetime(event.get("sbc_game_date") or event.get("date"), errors="coerce")
    game_date_text = "" if pd.isna(game_date) else game_date.date().isoformat()
    competitors = ((event.get("competitions") or [{}])[0].get("competitors") or [])
    context: dict[str, dict[str, Any]] = {}
    for competitor in competitors:
        team = competitor.get("team") or {}
        context[str(team.get("id") or "")] = {
            "abbreviation": team.get("abbreviation", ""),
            "display_name": team.get("displayName", ""),
            "home_away": competitor.get("homeAway", ""),
            "winner": competitor.get("winner"),
        }

    rows: list[dict[str, Any]] = []
    for team_box in (summary.get("boxscore") or {}).get("players", []):
        team = team_box.get("team") or {}
        team_id = str(team.get("id") or "")
        team_context = context.get(team_id, {})
        opponent = next((item for key, item in context.items() if key != team_id), {})
        is_home = team_context.get("home_away") == "home"
        matchup = f"{team_context.get('abbreviation') or team.get('abbreviation', '')} {'vs.' if is_home else '@'} {opponent.get('abbreviation', '')}".strip()
        result = "W" if team_context.get("winner") is True else "L" if team_context.get("winner") is False else ""
        for category in team_box.get("statistics", []):
            labels = category.get("labels") or []
            for athlete_row in category.get("athletes", []):
                athlete = athlete_row.get("athlete") or {}
                stats = dict(zip(labels, athlete_row.get("stats") or []))
                if not stats:
                    continue
                fgm, fga = _made_attempted(stats.get("FG"))
                fg3m, fg3a = _made_attempted(stats.get("3PT"))
                ftm, fta = _made_attempted(stats.get("FT"))
                rows.append(
                    {
                        "event_id": event_id,
                        "game_date": game_date_text,
                        "espn_player_id": str(athlete.get("id") or ""),
                        "player_name": athlete.get("displayName") or athlete.get("shortName") or "",
                        "nba_team_id": team_id,
                        "nba_team": team_context.get("abbreviation") or team.get("abbreviation", ""),
                        "nba_team_name": team_context.get("display_name") or team.get("displayName", ""),
                        "home_away": team_context.get("home_away", ""),
                        "matchup": matchup,
                        "result": result,
                        "MP": _minutes(stats.get("MIN")),
                        "FGM": fgm,
                        "FGA": fga,
                        "3PTM": fg3m,
                        "3PTA": fg3a,
                        "FTM": ftm,
                        "FTA": fta,
                        "PTS": _number(stats.get("PTS")),
                        "OREB": _number(stats.get("OREB")),
                        "DREB": _number(stats.get("DREB")),
                        "AST": _number(stats.get("AST")),
                        "ST": _number(stats.get("STL")),
                        "BLK": _number(stats.get("BLK")),
                        "TO": _number(stats.get("TO")),
                        "+/-": _number(stats.get("+/-")),
                    }
                )
    return pd.DataFrame(rows)


def as_legacy_player_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    renamed = frame.rename(
        columns={
            "espn_player_id": "PLAYER_ID",
            "player_name": "PLAYER_NAME",
            "nba_team_id": "TEAM_ID",
            "nba_team": "TEAM_ABBREVIATION",
            "nba_team_name": "TEAM_NAME",
            "event_id": "GAME_ID",
            "game_date": "GAME_DATE",
            "matchup": "MATCHUP",
            "result": "WL",
            "MP": "MIN",
            "3PTM": "FG3M",
            "3PTA": "FG3A",
            "ST": "STL",
            "TO": "TOV",
            "+/-": "PLUS_MINUS",
        }
    ).copy()
    renamed["SEASON_ID"] = ""
    columns = [
        "SEASON_ID", "PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION", "TEAM_NAME",
        "GAME_ID", "GAME_DATE", "MATCHUP", "WL", "MIN", "FGM", "FGA", "FG3M", "FG3A", "FTM",
        "FTA", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PLUS_MINUS",
    ]
    return renamed.reindex(columns=columns).to_dict("records")


class EspnNBAClient:
    """Resilient ESPN adapter with short live caches and long final caches."""

    def __init__(self, *, cache_root: Path, timeout_seconds: int = 30, live_ttl_seconds: int = 15):
        self.cache_root = Path(cache_root)
        self.timeout_seconds = timeout_seconds
        self.live_ttl_seconds = live_ttl_seconds
        self.http = CachedHttpClient(timeout_seconds=timeout_seconds)

    def scoreboard(self, game_date: date, *, allow_stale_on_error: bool = True) -> dict[str, Any]:
        cache_path = self.cache_root / "scoreboards" / f"{game_date:%Y%m%d}.json"
        ttl = 365 * 24 * 60 * 60 if game_date < date.today() else self.live_ttl_seconds
        return self.http.get_json(
            SCOREBOARD_URL,
            params={"dates": f"{game_date:%Y%m%d}", "limit": 100},
            cache_path=cache_path,
            ttl_seconds=ttl,
            allow_stale_on_error=allow_stale_on_error,
        )

    def summary(self, event_id: str, *, final: bool = False, allow_stale_on_error: bool = True) -> dict[str, Any]:
        cache_path = self.cache_root / "summaries" / f"{event_id}.json"
        # ESPN can apply postgame corrections. Final responses remain cheap to
        # reuse during one run, but expire before the next overnight lookback.
        ttl = 12 * 60 * 60 if final else self.live_ttl_seconds
        last_error: Exception | None = None
        for url in SUMMARY_URLS:
            try:
                return self.http.get_json(
                    url,
                    params={"event": event_id},
                    cache_path=cache_path,
                    ttl_seconds=ttl,
                    allow_stale_on_error=allow_stale_on_error,
                )
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"ESPN summary failed for event {event_id}") from last_error

    def snapshot(self, game_date: date, *, include_player_stats: bool = True) -> LiveSnapshot:
        fetched_at = datetime.now(timezone.utc).isoformat()
        scoreboard = self.scoreboard(game_date)
        raw_events = [event for event in (scoreboard.get("events") or []) if event.get("id")]
        games = tuple(parse_live_game(event, fetched_at=fetched_at) for event in raw_events)
        player_frames: list[pd.DataFrame] = []
        if include_player_stats:
            for game, event in zip(games, raw_events):
                if game.state == "pre":
                    continue
                summary = self.summary(game.event_id, final=game.completed)
                frame = parse_player_boxscore(summary, event)
                if not frame.empty:
                    frame["fetched_at"] = fetched_at
                    frame["game_state"] = game.state
                    player_frames.append(frame)
        players = pd.concat(player_frames, ignore_index=True) if player_frames else pd.DataFrame()
        return LiveSnapshot(
            game_date=game_date.isoformat(),
            fetched_at=fetched_at,
            games=games,
            player_stats=players,
            raw_scoreboard=scoreboard,
        )

    def regular_season_events(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        events: dict[str, dict[str, Any]] = {}
        current = start_date
        while current <= end_date:
            payload = self.scoreboard(current)
            for event in payload.get("events") or []:
                event_id = str(event.get("id") or "")
                if not event_id or (event.get("season") or {}).get("type") not in (None, 2):
                    continue
                copied = dict(event)
                copied["sbc_game_date"] = current.isoformat()
                events[event_id] = copied
            current += pd.Timedelta(days=1).to_pytimedelta()
        return sorted(events.values(), key=lambda item: item.get("date", ""))

    def player_game_rows(self, events: Iterable[dict[str, Any]]) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for event in events:
            event_id = str(event.get("id") or "")
            if not event_id:
                continue
            game = parse_live_game(event)
            summary = self.summary(event_id, final=game.completed)
            frame = parse_player_boxscore(summary, event)
            if not frame.empty:
                frames.append(frame)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
