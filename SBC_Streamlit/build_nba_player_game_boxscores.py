import argparse
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import requests


STATS_URL = "https://stats.nba.com/stats/leaguegamelog"
SCHEDULE_URL = (
    "https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/{season_start}/"
    "league/00_full_schedule.json"
)
LIVE_BOXSCORE_URL = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

NBA_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Host": "stats.nba.com",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}

GENERIC_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
}

SBC_STAT_COLUMNS = [
    "GP",
    "MP",
    "TS%",
    "2PTM",
    "2PTA",
    "2PT%",
    "3PTM",
    "3PTA",
    "3PT%",
    "FTM",
    "FTA",
    "FT%",
    "PTS",
    "OREB",
    "DREB",
    "AST",
    "ST",
    "BLK",
    "TO",
    "+/-",
]

COMPLETED_SBC_YEARS = [2021, 2022, 2023, 2024, 2025, 2026]

NBA_TEAM_ABBREVIATIONS = {
    "ATL",
    "BKN",
    "BOS",
    "CHA",
    "CHI",
    "CLE",
    "DAL",
    "DEN",
    "DET",
    "GS",
    "HOU",
    "IND",
    "LAC",
    "LAL",
    "MEM",
    "MIA",
    "MIL",
    "MIN",
    "NO",
    "NY",
    "OKC",
    "ORL",
    "PHI",
    "PHX",
    "POR",
    "SAC",
    "SA",
    "TOR",
    "UTA",
    "UTAH",
    "WAS",
    "WSH",
}

NBA_CUP_FINAL_GAME_IDS = {
    "401607495",  # 2023-24: Pacers-Lakers
    "401734908",  # 2024-25: Bucks-Thunder
    "401809839",  # 2025-26: Knicks-Spurs
}

REGULAR_SEASON_DATES = {
    2021: (date(2020, 12, 22), date(2021, 5, 16)),
    2022: (date(2021, 10, 19), date(2022, 4, 10)),
    2023: (date(2022, 10, 18), date(2023, 4, 9)),
    2024: (date(2023, 10, 24), date(2024, 4, 14)),
    2025: (date(2024, 10, 22), date(2025, 4, 13)),
    2026: (date(2025, 10, 21), date(2026, 4, 12)),
}


def season_from_sbc_year(year: int) -> str:
    return f"{year - 1}-{str(year)[-2:]}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build player-game NBA regular-season box scores with SBC stat columns."
    )
    parser.add_argument(
        "--sbc-year",
        type=int,
        default=2021,
        help="SBC league year. 2021 maps to NBA season 2020-21.",
    )
    parser.add_argument(
        "--sbc-years",
        nargs="+",
        type=int,
        default=None,
        help="One or more SBC league years, such as --sbc-years 2021 2022 2023.",
    )
    parser.add_argument(
        "--all-completed-years",
        action="store_true",
        help="Build all completed SBC years, currently 2021-2026.",
    )
    parser.add_argument(
        "--nba-season",
        default=None,
        help='NBA season string, such as "2020-21". Overrides --sbc-year mapping.',
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output parquet path. Defaults to nba_player_game_boxscores_<sbc-year>.parquet.",
    )
    parser.add_argument("--sleep", type=float, default=0.6, help="Delay after NBA Stats request.")
    parser.add_argument("--retries", type=int, default=5, help="NBA Stats retry count.")
    parser.add_argument("--timeout", type=int, default=90, help="Per-request timeout in seconds.")
    parser.add_argument("--chunk-days", type=int, default=14, help="Days per NBA Stats request.")
    parser.add_argument("--date-from", default=None, help='Optional start date, such as "2020-12-22".')
    parser.add_argument("--date-to", default=None, help='Optional end date, such as "2021-05-16".')
    parser.add_argument("--csv", default=None, help="Optional CSV copy of the parquet output.")
    parser.add_argument(
        "--cache-dir",
        default="data_snapshots/nba_boxscore_cache",
        help="Directory for ESPN scoreboard/summary JSON cache.",
    )
    parser.add_argument(
        "--warmup",
        action="store_true",
        help="Optionally visit nba.com/stats before the stats API request.",
    )
    parser.add_argument(
        "--source",
        choices=["espn", "cdn", "stats"],
        default="espn",
        help="Use ESPN JSON, NBA static/live-data JSON by game, or stats.nba.com.",
    )
    args, unknown_args = parser.parse_known_args()
    if unknown_args:
        print(f"Ignoring extra runtime arguments: {' '.join(unknown_args)}")
    return args


def nba_stats_result_to_frame(payload: dict[str, Any]) -> pd.DataFrame:
    result_sets = payload.get("resultSets") or payload.get("resultSet")
    if isinstance(result_sets, dict):
        headers = result_sets["headers"]
        rows = result_sets["rowSet"]
    else:
        first = result_sets[0]
        headers = first["headers"]
        rows = first["rowSet"]
    return pd.DataFrame(rows, columns=headers)


def default_regular_season_dates(sbc_year: int) -> tuple[date, date]:
    if sbc_year in REGULAR_SEASON_DATES:
        return REGULAR_SEASON_DATES[sbc_year]
    return date(sbc_year - 1, 10, 1), date(sbc_year, 6, 30)


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def iter_date_windows(start_date: date, end_date: date, chunk_days: int):
    current = start_date
    while current <= end_date:
        window_end = min(current + timedelta(days=chunk_days - 1), end_date)
        yield current, window_end
        current = window_end + timedelta(days=1)


def nba_date(value: date) -> str:
    return value.strftime("%m/%d/%Y")


def fetch_player_game_log(
    nba_season: str,
    sleep_seconds: float,
    retries: int,
    timeout: int,
    warmup: bool = False,
    date_from: date | None = None,
    date_to: date | None = None,
) -> pd.DataFrame:
    params = {
        "Counter": "0",
        "DateFrom": nba_date(date_from) if date_from else "",
        "DateTo": nba_date(date_to) if date_to else "",
        "Direction": "ASC",
        "LeagueID": "00",
        "PlayerOrTeam": "P",
        "Season": nba_season,
        "SeasonType": "Regular Season",
        "Sorter": "DATE",
    }
    session = requests.Session()
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            if warmup:
                session.get("https://www.nba.com/stats", headers=NBA_HEADERS, timeout=15)
            label = ""
            if date_from and date_to:
                label = f" for {date_from} to {date_to}"
            print(f"Fetching NBA player game logs{label}...")
            response = session.get(STATS_URL, params=params, headers=NBA_HEADERS, timeout=timeout)
            response.raise_for_status()
            time.sleep(sleep_seconds)
            return nba_stats_result_to_frame(response.json())
        except requests.RequestException as exc:
            last_error = exc
            wait = min(45, attempt * 5)
            print(f"NBA Stats request failed on attempt {attempt}/{retries}: {exc}")
            if attempt < retries:
                print(f"Retrying in {wait} seconds...")
                time.sleep(wait)
    raise RuntimeError(f"NBA Stats request failed after {retries} attempts") from last_error


def request_json(
    session: requests.Session,
    url: str,
    retries: int,
    timeout: int,
    sleep_seconds: float,
    cache_path: Path | None = None,
) -> dict[str, Any]:
    if cache_path and cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, headers=GENERIC_HEADERS, timeout=timeout)
            response.raise_for_status()
            time.sleep(sleep_seconds)
            payload = response.json()
            if cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                with cache_path.open("w", encoding="utf-8") as handle:
                    json.dump(payload, handle)
            return payload
        except requests.RequestException as exc:
            last_error = exc
            wait = min(45, attempt * 5)
            print(f"Request failed on attempt {attempt}/{retries}: {exc}")
            if attempt < retries:
                print(f"Retrying in {wait} seconds...")
                time.sleep(wait)
    raise RuntimeError(f"Request failed after {retries} attempts: {url}") from last_error


def fetch_regular_season_games(
    sbc_year: int,
    start_date: date,
    end_date: date,
    retries: int,
    timeout: int,
    sleep_seconds: float,
) -> list[dict[str, Any]]:
    season_start = sbc_year - 1
    url = SCHEDULE_URL.format(season_start=season_start)
    session = requests.Session()
    print(f"Fetching NBA schedule for {season_start}-{str(sbc_year)[-2:]}...")
    payload = request_json(session, url, retries, timeout, sleep_seconds)

    games = []
    for month in payload.get("lscd", []):
        for game in month.get("mscd", {}).get("g", []):
            game_date = datetime.strptime(game.get("gdte", ""), "%Y-%m-%d").date()
            game_id = str(game.get("gid", ""))
            if not game_id.startswith("002"):
                continue
            if not (start_date <= game_date <= end_date):
                continue
            games.append(game)
    games.sort(key=lambda item: (item.get("gdte", ""), item.get("gid", "")))
    return games


def player_rows_from_live_boxscore(
    boxscore: dict[str, Any],
    game_date: date,
    game_id: str,
) -> list[dict[str, Any]]:
    game = boxscore.get("game", {})
    rows = []
    teams = [
        (game.get("homeTeam", {}), game.get("awayTeam", {}), True),
        (game.get("awayTeam", {}), game.get("homeTeam", {}), False),
    ]
    for team, opponent, is_home in teams:
        team_tricode = team.get("teamTricode")
        opponent_tricode = opponent.get("teamTricode")
        matchup = f"{team_tricode} {'vs.' if is_home else '@'} {opponent_tricode}"
        wl = ""
        try:
            team_score = int(team.get("score", 0))
            opponent_score = int(opponent.get("score", 0))
            wl = "W" if team_score > opponent_score else "L" if team_score < opponent_score else ""
        except (TypeError, ValueError):
            pass

        for player in team.get("players", []):
            stats = player.get("statistics") or {}
            minutes = stats.get("minutes") or "PT00M"
            rows.append(
                {
                    "SEASON_ID": "",
                    "PLAYER_ID": player.get("personId"),
                    "PLAYER_NAME": player.get("name"),
                    "TEAM_ID": team.get("teamId"),
                    "TEAM_ABBREVIATION": team_tricode,
                    "TEAM_NAME": team.get("teamName"),
                    "GAME_ID": game_id,
                    "GAME_DATE": game_date.isoformat(),
                    "MATCHUP": matchup,
                    "WL": wl,
                    "MIN": nba_duration_to_minutes(minutes),
                    "FGM": stats.get("fieldGoalsMade", 0),
                    "FGA": stats.get("fieldGoalsAttempted", 0),
                    "FG3M": stats.get("threePointersMade", 0),
                    "FG3A": stats.get("threePointersAttempted", 0),
                    "FTM": stats.get("freeThrowsMade", 0),
                    "FTA": stats.get("freeThrowsAttempted", 0),
                    "PTS": stats.get("points", 0),
                    "OREB": stats.get("reboundsOffensive", 0),
                    "DREB": stats.get("reboundsDefensive", 0),
                    "AST": stats.get("assists", 0),
                    "STL": stats.get("steals", 0),
                    "BLK": stats.get("blocks", 0),
                    "TOV": stats.get("turnovers", 0),
                    "PLUS_MINUS": stats.get("plusMinusPoints", 0),
                }
            )
    return rows


def nba_duration_to_minutes(value: Any) -> float:
    if value is None:
        return 0.0
    value = str(value)
    if ":" in value:
        minutes, seconds = value.split(":", 1)
        return float(minutes or 0) + float(seconds or 0) / 60
    if value.startswith("PT"):
        trimmed = value.removeprefix("PT")
        minutes = 0.0
        seconds = 0.0
        if "M" in trimmed:
            before_m, trimmed = trimmed.split("M", 1)
            minutes = float(before_m or 0)
        if "S" in trimmed:
            before_s = trimmed.split("S", 1)[0]
            seconds = float(before_s or 0)
        return minutes + seconds / 60
    try:
        return float(value)
    except ValueError:
        return 0.0


def parse_made_attempted(value: Any) -> tuple[int, int]:
    if value is None:
        return 0, 0
    parts = str(value).split("-")
    if len(parts) != 2:
        return 0, 0
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return 0, 0


def parse_number(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value).replace("+", ""))
    except ValueError:
        return 0.0


def espn_scoreboard_url(day: date) -> str:
    return (
        "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/"
        f"scoreboard?dates={day:%Y%m%d}&limit=100"
    )


def espn_summary_urls(event_id: str) -> list[str]:
    return [
        f"https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}",
        f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}",
    ]


def fetch_espn_summary(
    session: requests.Session,
    event_id: str,
    retries: int,
    timeout: int,
    sleep_seconds: float,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    cache_path = cache_dir / "summaries" / f"{event_id}.json" if cache_dir else None
    if cache_path and cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    last_error = None
    for url in espn_summary_urls(event_id):
        try:
            return request_json(session, url, retries, timeout, sleep_seconds, cache_path=cache_path)
        except RuntimeError as exc:
            last_error = exc
    raise RuntimeError(f"ESPN summary failed for event {event_id}") from last_error


def fetch_espn_events(
    sbc_year: int,
    start_date: date,
    end_date: date,
    retries: int,
    timeout: int,
    sleep_seconds: float,
    cache_dir: Path | None = None,
) -> list[dict[str, Any]]:
    session = requests.Session()
    events_by_id = {}
    current = start_date
    while current <= end_date:
        print(f"Fetching ESPN scoreboard for {current}...")
        cache_path = None
        if cache_dir:
            cache_path = cache_dir / "scoreboards" / str(sbc_year) / f"{current:%Y%m%d}.json"
        payload = request_json(
            session,
            espn_scoreboard_url(current),
            retries,
            timeout,
            sleep_seconds,
            cache_path=cache_path,
        )
        for event in payload.get("events", []):
            event_id = str(event.get("id", ""))
            if not event_id:
                continue
            season_type = event.get("season", {}).get("type")
            if season_type not in (None, 2):
                continue
            event["sbc_game_date"] = current.isoformat()
            events_by_id[event_id] = event
        current += timedelta(days=1)
    events = list(events_by_id.values())
    events.sort(key=lambda item: item.get("date", ""))
    return events


def rows_from_espn_summary(summary: dict[str, Any], event: dict[str, Any]) -> list[dict[str, Any]]:
    event_id = str(event.get("id", ""))
    game_date = pd.to_datetime(event.get("sbc_game_date") or event.get("date")).date()
    competitors = event.get("competitions", [{}])[0].get("competitors", [])
    team_context = {}
    for competitor in competitors:
        team = competitor.get("team", {})
        team_id = str(team.get("id", ""))
        team_context[team_id] = {
            "team_id": team_id,
            "abbreviation": team.get("abbreviation", ""),
            "display_name": team.get("displayName", ""),
            "home_away": competitor.get("homeAway", ""),
            "score": parse_number(competitor.get("score")),
            "winner": competitor.get("winner"),
        }

    rows = []
    for team_box in summary.get("boxscore", {}).get("players", []):
        team = team_box.get("team", {})
        team_id = str(team.get("id", ""))
        context = team_context.get(team_id, {})
        opponent_context = next((ctx for tid, ctx in team_context.items() if tid != team_id), {})
        is_home = context.get("home_away") == "home"
        matchup = (
            f"{context.get('abbreviation', team.get('abbreviation', ''))} "
            f"{'vs.' if is_home else '@'} "
            f"{opponent_context.get('abbreviation', '')}"
        )
        wl = ""
        if context.get("winner") is True:
            wl = "W"
        elif context.get("winner") is False:
            wl = "L"

        for category in team_box.get("statistics", []):
            labels = category.get("labels", [])
            for athlete_row in category.get("athletes", []):
                athlete = athlete_row.get("athlete", {})
                stats = dict(zip(labels, athlete_row.get("stats", [])))
                if not stats:
                    continue
                fgm, fga = parse_made_attempted(stats.get("FG"))
                fg3m, fg3a = parse_made_attempted(stats.get("3PT"))
                ftm, fta = parse_made_attempted(stats.get("FT"))
                rows.append(
                    {
                        "SEASON_ID": "",
                        "PLAYER_ID": athlete.get("id"),
                        "PLAYER_NAME": athlete.get("displayName") or athlete.get("shortName"),
                        "TEAM_ID": team_id or team.get("id"),
                        "TEAM_ABBREVIATION": context.get("abbreviation") or team.get("abbreviation"),
                        "TEAM_NAME": context.get("display_name") or team.get("displayName"),
                        "GAME_ID": event_id,
                        "GAME_DATE": game_date.isoformat(),
                        "MATCHUP": matchup,
                        "WL": wl,
                        "MIN": nba_duration_to_minutes(stats.get("MIN")),
                        "FGM": fgm,
                        "FGA": fga,
                        "FG3M": fg3m,
                        "FG3A": fg3a,
                        "FTM": ftm,
                        "FTA": fta,
                        "PTS": parse_number(stats.get("PTS")),
                        "OREB": parse_number(stats.get("OREB")),
                        "DREB": parse_number(stats.get("DREB")),
                        "AST": parse_number(stats.get("AST")),
                        "STL": parse_number(stats.get("STL")),
                        "BLK": parse_number(stats.get("BLK")),
                        "TOV": parse_number(stats.get("TO")),
                        "PLUS_MINUS": parse_number(stats.get("+/-")),
                    }
                )
    return rows


def fetch_espn_player_game_log(
    sbc_year: int,
    start_date: date,
    end_date: date,
    retries: int,
    timeout: int,
    sleep_seconds: float,
    cache_dir: Path | None,
) -> pd.DataFrame:
    events = fetch_espn_events(sbc_year, start_date, end_date, retries, timeout, sleep_seconds, cache_dir)
    print(f"Found {len(events):,} ESPN regular-season events.")
    session = requests.Session()
    rows = []
    for index, event in enumerate(events, start=1):
        event_id = str(event["id"])
        print(f"Fetching ESPN box score {index:,}/{len(events):,}: {event.get('date', '')[:10]} {event_id}")
        summary = fetch_espn_summary(session, event_id, retries, timeout, sleep_seconds, cache_dir)
        rows.extend(rows_from_espn_summary(summary, event))
    return pd.DataFrame(rows)


def fetch_cdn_player_game_log(
    sbc_year: int,
    start_date: date,
    end_date: date,
    retries: int,
    timeout: int,
    sleep_seconds: float,
) -> pd.DataFrame:
    games = fetch_regular_season_games(
        sbc_year=sbc_year,
        start_date=start_date,
        end_date=end_date,
        retries=retries,
        timeout=timeout,
        sleep_seconds=sleep_seconds,
    )
    print(f"Found {len(games):,} regular-season games.")
    session = requests.Session()
    rows = []
    for index, game in enumerate(games, start=1):
        game_id = str(game["gid"])
        game_date = datetime.strptime(game["gdte"], "%Y-%m-%d").date()
        url = LIVE_BOXSCORE_URL.format(game_id=game_id)
        print(f"Fetching box score {index:,}/{len(games):,}: {game_date} {game_id}")
        boxscore = request_json(session, url, retries, timeout, sleep_seconds)
        rows.extend(player_rows_from_live_boxscore(boxscore, game_date, game_id))
    return pd.DataFrame(rows)


def normalize_boxscores(raw: pd.DataFrame, sbc_year: int, nba_season: str) -> pd.DataFrame:
    df = raw.copy()
    df["Date"] = pd.to_datetime(df["GAME_DATE"]).dt.date
    df["GP"] = 1

    numeric_cols = [
        "MIN",
        "FGM",
        "FGA",
        "FG3M",
        "FG3A",
        "FTM",
        "FTA",
        "PTS",
        "OREB",
        "DREB",
        "AST",
        "STL",
        "BLK",
        "TOV",
        "PLUS_MINUS",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["MP"] = df["MIN"]
    df["2PTM"] = df["FGM"] - df["FG3M"]
    df["2PTA"] = df["FGA"] - df["FG3A"]
    df["2PT%"] = (df["2PTM"] / df["2PTA"]).where(df["2PTA"] > 0, 0)
    df["3PTM"] = df["FG3M"]
    df["3PTA"] = df["FG3A"]
    df["3PT%"] = (df["3PTM"] / df["3PTA"]).where(df["3PTA"] > 0, 0)
    df["FT%"] = (df["FTM"] / df["FTA"]).where(df["FTA"] > 0, 0)
    df["TS%"] = (df["PTS"] / (2 * (df["FGA"] + 0.44 * df["FTA"]))).where(
        (df["FGA"] + 0.44 * df["FTA"]) > 0, 0
    )
    df["ST"] = df["STL"]
    df["TO"] = df["TOV"]
    df["+/-"] = df["PLUS_MINUS"]

    df["home_away"] = df["MATCHUP"].astype(str).str.extract(r"(vs\.|@)", expand=False)
    df["is_home"] = df["home_away"].eq("vs.")
    df["opponent"] = df["MATCHUP"].astype(str).str.extract(r"(?:vs\.|@)\s+([A-Z]{2,3})", expand=False)

    rename_cols = {
        "SEASON_ID": "season_id",
        "PLAYER_ID": "nba_player_id",
        "PLAYER_NAME": "player_name",
        "TEAM_ID": "nba_team_id",
        "TEAM_ABBREVIATION": "nba_team",
        "TEAM_NAME": "nba_team_name",
        "GAME_ID": "nba_game_id",
        "MATCHUP": "matchup",
        "WL": "wl",
    }
    df = df.rename(columns=rename_cols)
    df["season_id"] = df["season_id"].replace("", f"2{nba_season[:4]}")
    df["sbc_year"] = sbc_year
    df["nba_season"] = nba_season

    background_cols = [
        "sbc_year",
        "nba_season",
        "season_id",
        "Date",
        "nba_game_id",
        "nba_player_id",
        "player_name",
        "nba_team_id",
        "nba_team",
        "nba_team_name",
        "opponent",
        "matchup",
        "is_home",
        "wl",
    ]
    output_cols = background_cols + SBC_STAT_COLUMNS
    return df[output_cols].sort_values(["Date", "nba_game_id", "nba_team", "player_name"]).reset_index(drop=True)


def clean_regular_season_boxscores(boxscores: pd.DataFrame) -> pd.DataFrame:
    df = boxscores.copy()
    df["nba_game_id"] = df["nba_game_id"].astype(str)
    df = df[
        df["nba_team"].isin(NBA_TEAM_ABBREVIATIONS)
        & df["opponent"].isin(NBA_TEAM_ABBREVIATIONS)
        & ~df["nba_game_id"].isin(NBA_CUP_FINAL_GAME_IDS)
    ].copy()

    game_totals = (
        df.groupby(["sbc_year", "nba_game_id"], as_index=False)
        .agg(total_pts=("PTS", "sum"), total_mp=("MP", "sum"))
    )
    live_game_ids = game_totals[(game_totals["total_pts"] > 0) & (game_totals["total_mp"] > 0)][
        ["sbc_year", "nba_game_id"]
    ]
    df = df.merge(live_game_ids, on=["sbc_year", "nba_game_id"], how="inner")
    return df.sort_values(["Date", "nba_game_id", "nba_team", "player_name"]).reset_index(drop=True)


def build_year_boxscores(args: argparse.Namespace, sbc_year: int) -> pd.DataFrame:
    nba_season = args.nba_season or season_from_sbc_year(sbc_year)
    start_date, end_date = default_regular_season_dates(sbc_year)
    if len(get_sbc_years(args)) == 1:
        start_date = parse_iso_date(args.date_from) or start_date
        end_date = parse_iso_date(args.date_to) or end_date
    elif args.date_from or args.date_to:
        print("Ignoring --date-from/--date-to for multi-year builds.")

    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    if args.source == "espn":
        raw = fetch_espn_player_game_log(
            sbc_year=sbc_year,
            start_date=start_date,
            end_date=end_date,
            retries=args.retries,
            timeout=args.timeout,
            sleep_seconds=args.sleep,
            cache_dir=cache_dir,
        )
    elif args.source == "cdn":
        raw = fetch_cdn_player_game_log(
            sbc_year=sbc_year,
            start_date=start_date,
            end_date=end_date,
            retries=args.retries,
            timeout=args.timeout,
            sleep_seconds=args.sleep,
        )
    else:
        chunks = []
        for window_start, window_end in iter_date_windows(start_date, end_date, args.chunk_days):
            chunk = fetch_player_game_log(
                nba_season=nba_season,
                sleep_seconds=args.sleep,
                retries=args.retries,
                timeout=args.timeout,
                warmup=args.warmup,
                date_from=window_start,
                date_to=window_end,
            )
            if not chunk.empty:
                chunks.append(chunk)

        if not chunks:
            raise RuntimeError("No NBA player-game rows were returned.")

        raw = pd.concat(chunks, ignore_index=True).drop_duplicates()

    if raw.empty:
        raise RuntimeError("No NBA player-game rows were returned.")
    return normalize_boxscores(raw, sbc_year, nba_season)


def get_sbc_years(args: argparse.Namespace) -> list[int]:
    if args.all_completed_years:
        return COMPLETED_SBC_YEARS
    if args.sbc_years:
        return args.sbc_years
    return [args.sbc_year]


def main() -> None:
    args = parse_args()
    years = get_sbc_years(args)
    if args.nba_season and len(years) > 1:
        raise ValueError("--nba-season can only be used with a single SBC year.")

    if args.output:
        output = Path(args.output)
    elif len(years) > 1:
        output = Path(f"nba_player_game_boxscores_{min(years)}_{max(years)}.parquet")
    else:
        output = Path(f"nba_player_game_boxscores_{years[0]}.parquet")

    frames = []
    for sbc_year in years:
        print(f"\n=== Building SBC year {sbc_year} ({season_from_sbc_year(sbc_year)}) ===")
        frames.append(build_year_boxscores(args, sbc_year))

    boxscores = pd.concat(frames, ignore_index=True).drop_duplicates()
    boxscores = clean_regular_season_boxscores(boxscores)
    boxscores = boxscores.sort_values(["Date", "nba_game_id", "nba_team", "player_name"]).reset_index(drop=True)
    boxscores.to_parquet(output, index=False)
    if args.csv:
        boxscores.to_csv(args.csv, index=False)

    print(f"Wrote {len(boxscores):,} player-game rows to {output}")
    print(f"Games: {boxscores['nba_game_id'].nunique():,}")
    print(f"SBC years: {', '.join(str(year) for year in sorted(boxscores['sbc_year'].unique()))}")
    print(f"Date range: {boxscores['Date'].min()} to {boxscores['Date'].max()}")


if __name__ == "__main__":
    main()
