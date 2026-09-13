"""Read game status, but never fantasy scoring, from the official NFL scoreboard."""

from datetime import datetime
from html.parser import HTMLParser
import json
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests


NFL_TEAM_CODES = {"AZ": "ARI", "JAC": "JAX", "LA": "LAR", "WSH": "WAS"}


class NFLGamesUnavailable(RuntimeError):
    pass


def team_code(value: str) -> str:
    code = str(value or "").strip().upper()
    return NFL_TEAM_CODES.get(code, code)


class _ScoreboardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.card: dict | None = None
        self.card_links = 0
        self.games: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "li":
            if self.card is None:
                self.card = {"teams": [], "text_parts": []}
                self.depth = 1
            else:
                self.depth += 1
            return
        if self.card is None:
            return
        attributes = dict(attrs)
        if tag == "time" and attributes.get("datetime"):
            self.card["kickoff"] = str(attributes["datetime"])
        if tag == "a" and attributes.get("data-analytics"):
            try:
                analytics = json.loads(attributes["data-analytics"] or "{}")
            except json.JSONDecodeError:
                return
            if analytics.get("linkModule") == "Game Card":
                self.card_links += 1
                self.card["state"] = str(analytics.get("gameState") or "SCHEDULED").upper()
                self.card["id"] = str(analytics.get("gameId") or "")
                self.card["url"] = "https://www.nfl.com" + str(attributes.get("href") or "")
        elif tag == "img" and str(attributes.get("alt") or "").endswith("Team Logo"):
            match = re.search(r"/clubs/logos/([A-Z]{2,3})(?:$|[/?])", str(attributes.get("src") or ""))
            if match:
                code = team_code(match.group(1))
                if code not in self.card["teams"]:
                    self.card["teams"].append(code)

    def handle_data(self, data: str) -> None:
        if self.card is not None and data.strip():
            self.card["text_parts"].append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag != "li" or self.card is None:
            return
        self.depth -= 1
        if self.depth == 0:
            if self.card.get("state") and len(self.card["teams"]) == 2:
                self.games.append(self.card)
            self.card = None


def fetch_week_games(season: int, week: int) -> list[dict]:
    """Return all regular-season games for a week, failing closed on incomplete markup."""
    response = requests.get(
        f"https://www.nfl.com/scores/{int(season)}/week-{int(week)}",
        headers={"User-Agent": "Mozilla/5.0 (compatible; VampireHunt/1.0)"},
        timeout=20,
    )
    response.raise_for_status()
    parser = _ScoreboardParser()
    parser.feed(response.text)
    if parser.card_links < 12 or len(parser.games) != parser.card_links:
        raise NFLGamesUnavailable("The NFL week could not be verified completely.")
    teams = [team for game in parser.games for team in game["teams"]]
    if len(set(teams)) != len(teams):
        raise NFLGamesUnavailable("The NFL scoreboard returned duplicate team games.")
    return parser.games


def games_are_final(games: list[dict]) -> bool:
    return bool(games) and all(str(game.get("state", "")).startswith("FINAL") for game in games)


def followers_left(roster: list[dict], games: list[dict]) -> int:
    """Count rostered followers whose NFL team still has an unresolved game."""
    pending_teams = {
        team for game in games if not str(game.get("state", "")).startswith("FINAL")
        for team in game["teams"]
    }
    return sum(not row.get("stolen") and team_code(row.get("nfl_team", "")) in pending_teams for row in roster)


def game_marker(game: dict | None) -> tuple[str, str]:
    """Return a short, human-readable status and styling key for an NFL game."""
    if not game:
        return "Bye", "bye"
    state = str(game.get("state") or "").upper()
    if state.startswith("FINAL"):
        return "Final", "final"
    if state in {"SCHEDULED", "PREGAME", "PRE"}:
        kickoff = game.get("kickoff")
        if kickoff:
            try:
                eastern = datetime.fromisoformat(str(kickoff).replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))
                hour = eastern.hour % 12 or 12
                time_text = f"{hour}:{eastern.minute:02d}" if eastern.minute else str(hour)
                meridiem = "AM" if eastern.hour < 12 else "PM"
                return f"{eastern:%a} {time_text} {meridiem} ET", "scheduled"
            except (ValueError, TypeError, KeyError, ZoneInfoNotFoundError):
                pass
        return "Scheduled", "scheduled"
    if "HALF" in state:
        return "Halftime", "live"
    parts = [str(part).upper() for part in game.get("text_parts", [])]
    for index, part in enumerate(parts):
        if re.fullmatch(r"Q[1-4]|OT", part):
            clock = next((piece for piece in parts[index + 1:index + 5] if re.fullmatch(r"\d{1,2}:\d{2}", piece)), None)
            return (f"{part} {clock}" if clock else part), "live"
    return "Live", "live"
