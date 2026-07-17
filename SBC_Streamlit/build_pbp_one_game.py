from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import requests


ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
OFFICIAL_BOXSCORE_PATH = Path("nba_player_game_boxscores_2021_2026.parquet")

STAT_COLUMNS = [
    "game_id",
    "game_date",
    "stat",
    "player_id",
    "player",
    "wallclock",
    "value",
    "scored",
    "description",
]


def fetch_json(url: str, **params: Any) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def first_game_id_for_date(date: str) -> str:
    scoreboard = fetch_json(ESPN_SCOREBOARD_URL, dates=date)
    events = scoreboard.get("events") or []
    if not events:
        raise ValueError(f"No NBA games found for {date}.")
    return str(events[0]["id"])


def game_ids_for_date(date: str) -> list[str]:
    scoreboard = fetch_json(ESPN_SCOREBOARD_URL, dates=date)
    return [str(event["id"]) for event in scoreboard.get("events") or []]


def date_span(start_date: str, end_date: str) -> list[str]:
    start = datetime.strptime(start_date, "%Y%m%d").date()
    end = datetime.strptime(end_date, "%Y%m%d").date()
    if end < start:
        raise ValueError("--end-date must be on or after --start-date.")
    dates: list[str] = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return dates


def game_team_maps(summary: dict[str, Any]) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    competitors = summary["header"]["competitions"][0]["competitors"]
    teams: dict[str, dict[str, str]] = {}
    sides: dict[str, str] = {}
    for competitor in competitors:
        team = competitor["team"]
        team_id = str(team["id"])
        teams[team_id] = {
            "team_id": team_id,
            "team_abbr": team.get("abbreviation", ""),
            "team_name": team.get("displayName", ""),
        }
        sides[competitor["homeAway"]] = team_id
    return teams, sides


def athlete_maps(summary: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    player_names: dict[str, str] = {}
    player_teams: dict[str, str] = {}
    for team_block in summary.get("boxscore", {}).get("players", []):
        team_id = str(team_block["team"]["id"])
        for stat_group in team_block.get("statistics", []):
            for athlete_row in stat_group.get("athletes", []):
                athlete = athlete_row.get("athlete") or {}
                athlete_id = athlete.get("id")
                if athlete_id is None:
                    continue
                athlete_id = str(athlete_id)
                player_names[athlete_id] = athlete.get("displayName", "")
                player_teams[athlete_id] = team_id
    return player_names, player_teams


def starter_ids_by_team(summary: dict[str, Any]) -> dict[str, set[str]]:
    starters: dict[str, set[str]] = {}
    for team_block in summary.get("boxscore", {}).get("players", []):
        team_id = str(team_block["team"]["id"])
        starters.setdefault(team_id, set())
        for stat_group in team_block.get("statistics", []):
            for athlete_row in stat_group.get("athletes", []):
                athlete = athlete_row.get("athlete") or {}
                athlete_id = athlete.get("id")
                if athlete_id is not None and athlete_row.get("starter"):
                    starters[team_id].add(str(athlete_id))
    return starters


def participant_id(play: dict[str, Any], index: int) -> str | None:
    participants = play.get("participants") or []
    if len(participants) <= index:
        return None
    athlete = participants[index].get("athlete") or {}
    athlete_id = athlete.get("id")
    return str(athlete_id) if athlete_id is not None else None


def event_row(
    play: dict[str, Any],
    stat: str,
    player_id: str | None,
    player_names: dict[str, str],
    player_teams: dict[str, str],
    value: int,
    scored: bool | None,
) -> dict[str, Any] | None:
    if player_id is None:
        return None

    period = play.get("period") or {}
    clock = play.get("clock") or {}
    period_display = period.get("displayValue", "")
    clock_display = clock.get("displayValue", "")
    description = play.get("text", "")
    if period_display or clock_display:
        description = f"{description} ({period_display}, {clock_display})"

    return {
        "stat": stat,
        "player_id": player_id,
        "player": player_names.get(player_id, ""),
        "wallclock": play.get("wallclock"),
        "value": value,
        "scored": scored,
        "description": description,
        "_sequence_number": int(play.get("sequenceNumber") or 0),
    }


def adjustment_row(
    end_play: dict[str, Any],
    stat: str,
    player_id: str,
    player: str,
    value: float,
    sequence_suffix: float,
) -> dict[str, Any]:
    signed = f"+{value:g}" if value > 0 else f"{value:g}"
    return {
        "stat": stat,
        "player_id": str(player_id),
        "player": player,
        "wallclock": end_play.get("wallclock"),
        "value": value,
        "scored": None,
        "description": f"{player} {stat} adjustment {signed}",
        "_sequence_number": int(end_play.get("sequenceNumber") or 999999) + sequence_suffix,
    }


def period_length_seconds(period_number: int) -> int:
    return 720 if period_number <= 4 else 300


def period_start_seconds(period_number: int) -> int:
    if period_number <= 4:
        return (period_number - 1) * 720
    return 2880 + (period_number - 5) * 300


def clock_remaining_seconds(clock_display: str) -> float:
    if not clock_display:
        return 0.0
    if ":" in clock_display:
        minutes, seconds = clock_display.split(":", 1)
        return int(minutes) * 60 + float(seconds)
    return float(clock_display)


def play_absolute_seconds(play: dict[str, Any]) -> float:
    period = int((play.get("period") or {}).get("number") or 1)
    clock = (play.get("clock") or {}).get("displayValue", "")
    remaining = clock_remaining_seconds(clock)
    return period_start_seconds(period) + period_length_seconds(period) - remaining


def format_shift_time(seconds: float) -> str:
    rounded = int(round(seconds))
    minutes, seconds = divmod(max(0, rounded), 60)
    return f"{minutes}:{seconds:02d}"


def signed_shift(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


def shift_event_rows(
    player_id: str,
    exit_play: dict[str, Any],
    start_seconds: float,
    plus_minus: int,
    player_names: dict[str, str],
    sequence_suffix: float,
) -> list[dict[str, Any]]:
    played_seconds = play_absolute_seconds(exit_play) - start_seconds
    player = player_names.get(player_id, "")
    sequence_number = int(exit_play.get("sequenceNumber") or 0) + sequence_suffix
    return [
        {
            "stat": "minutes played",
            "player_id": player_id,
            "player": player,
            "wallclock": exit_play.get("wallclock"),
            "value": round(played_seconds / 60, 4),
            "scored": None,
            "description": f"{player} checked out after playing {format_shift_time(played_seconds)}",
            "_sequence_number": sequence_number,
        },
        {
            "stat": "+/-",
            "player_id": player_id,
            "player": player,
            "wallclock": exit_play.get("wallclock"),
            "value": plus_minus,
            "scored": None,
            "description": f"{player} checked out after a {signed_shift(plus_minus)} shift",
            "_sequence_number": sequence_number + 0.001,
        },
    ]


def build_shift_events(
    plays: list[dict[str, Any]],
    summary: dict[str, Any],
    player_names: dict[str, str],
    player_teams: dict[str, str],
) -> list[dict[str, Any]]:
    teams, sides = game_team_maps(summary)
    home_team_id = sides.get("home")
    away_team_id = sides.get("away")
    starters = starter_ids_by_team(summary)
    active_by_team: dict[str, set[str]] = {team_id: set(ids) for team_id, ids in starters.items()}
    shifts: dict[str, dict[str, float | int]] = {}
    rows: list[dict[str, Any]] = []

    for player_ids in active_by_team.values():
        for player_id in player_ids:
            shifts[player_id] = {"start": 0.0, "plus_minus": 0}

    last_home_score = 0
    last_away_score = 0
    current_period = 1

    def close_player(player_id: str, play: dict[str, Any], suffix: float) -> None:
        shift = shifts.pop(player_id, None)
        if not shift:
            return
        rows.extend(
            shift_event_rows(
                player_id,
                play,
                float(shift["start"]),
                int(shift["plus_minus"]),
                player_names,
                suffix,
            )
        )

    def open_player(player_id: str, play: dict[str, Any], start_seconds: float | None = None) -> None:
        if player_id in shifts:
            return
        shifts[player_id] = {
            "start": play_absolute_seconds(play) if start_seconds is None else start_seconds,
            "plus_minus": 0,
        }
        team_id = player_teams.get(player_id)
        if team_id:
            active_by_team.setdefault(team_id, set()).add(player_id)

    last_period_end_play: dict[str, Any] | None = None
    for play in plays:
        period_number = int((play.get("period") or {}).get("number") or current_period)
        if period_number != current_period:
            current_period = period_number
            if period_number == 3:
                close_play = last_period_end_play or play
                for idx, player_id in enumerate(list(shifts.keys())):
                    close_player(player_id, close_play, 0.01 + idx / 1000)
                active_by_team = {team_id: set(ids) for team_id, ids in starters.items()}
                shifts = {}
                start_seconds = period_start_seconds(period_number)
                for player_ids in active_by_team.values():
                    for player_id in player_ids:
                        shifts[player_id] = {"start": start_seconds, "plus_minus": 0}

        home_score = int(play.get("homeScore") or last_home_score)
        away_score = int(play.get("awayScore") or last_away_score)
        home_delta = home_score - last_home_score
        away_delta = away_score - last_away_score

        if home_delta or away_delta:
            for player_id, shift in shifts.items():
                team_id = player_teams.get(player_id)
                if team_id == home_team_id:
                    shift["plus_minus"] = int(shift["plus_minus"]) + home_delta - away_delta
                elif team_id == away_team_id:
                    shift["plus_minus"] = int(shift["plus_minus"]) + away_delta - home_delta
            last_home_score = home_score
            last_away_score = away_score

        type_text = ((play.get("type") or {}).get("text") or "").lower()
        if type_text == "end period":
            last_period_end_play = play

        if "substitution" in type_text:
            entering_id = participant_id(play, 0)
            leaving_id = participant_id(play, 1)
            if leaving_id:
                close_player(leaving_id, play, 0.01)
                team_id = player_teams.get(leaving_id)
                if team_id:
                    active_by_team.setdefault(team_id, set()).discard(leaving_id)
            if entering_id:
                open_player(entering_id, play)

        if type_text == "end period" and period_number >= 4:
            for idx, player_id in enumerate(list(shifts.keys())):
                close_player(player_id, play, 0.01 + idx / 1000)
            shifts = {}
            for player_ids in active_by_team.values():
                player_ids.clear()

    return rows


def missed_shot_stat(play: dict[str, Any]) -> str | None:
    play_text = (play.get("text") or "").lower()
    type_text = ((play.get("type") or {}).get("text") or "").lower()
    if "blocks" in play_text:
        if "three point" in play_text or "three pointer" in play_text:
            return "three-point miss"
        return "two-point miss"
    if "misses" not in play_text:
        return None
    if "free throw" in type_text:
        return "free-throw miss"
    if "three point" in play_text or "three pointer" in play_text:
        return "three-point miss"
    return "two-point miss"


def made_shot_stat(play: dict[str, Any], score_value: int) -> str | None:
    play_text = (play.get("text") or "").lower()
    type_text = ((play.get("type") or {}).get("text") or "").lower()
    if score_value == 3:
        return "three-point make"
    if score_value == 2:
        return "two-point make"
    if score_value == 1 and ("free throw" in play_text or "free throw" in type_text):
        return "free-throw make"
    return None


def is_turnover_play(play: dict[str, Any]) -> bool:
    type_text = ((play.get("type") or {}).get("text") or "").lower()
    play_text = (play.get("text") or "").lower()
    if "turnover" in type_text:
        return True
    turnover_types = [
        "traveling",
        "offensive charge",
        "offensive goaltending",
        "lane violation",
        "palming",
        "discontinue dribble",
        "double dribble",
        "illegal assist",
        "illegal screen",
        "backcourt violation",
        "jump ball violation",
        "5-second violation",
    ]
    if any(token in type_text for token in turnover_types):
        return True
    return "traveling" in play_text


def read_official_boxscore_game(game_id: str) -> pd.DataFrame:
    if not OFFICIAL_BOXSCORE_PATH.exists():
        return pd.DataFrame()
    box = pd.read_parquet(OFFICIAL_BOXSCORE_PATH)
    if "nba_game_id" not in box.columns:
        return pd.DataFrame()
    return box[box["nba_game_id"].astype(str) == str(game_id)].copy()


def row_stat_sum(rows: list[dict[str, Any]], player_id: str, stat: str) -> float:
    return sum(float(row.get("value", 0) or 0) for row in rows if str(row.get("player_id")) == str(player_id) and row.get("stat") == stat)


def add_official_adjustments(
    rows: list[dict[str, Any]],
    game_id: str,
    end_play: dict[str, Any],
) -> None:
    box = read_official_boxscore_game(game_id)
    if box.empty:
        return

    stat_pairs = [
        ("PTS", "points"),
        ("OREB", "offensive_rebound"),
        ("DREB", "defensive_rebound"),
        ("AST", "assist"),
        ("ST", "steal"),
        ("BLK", "block"),
        ("TO", "turnover"),
        ("+/-", "+/-"),
        ("MP", "minutes played"),
        ("2PTM", "two-point make"),
        ("3PTM", "three-point make"),
        ("FTM", "free-throw make"),
    ]
    suffix = 1000.0
    for _, official in box.iterrows():
        player_id = str(official.get("nba_player_id", ""))
        player = str(official.get("player_name", ""))
        if not player_id or player_id == "nan":
            continue
        for official_col, stat in stat_pairs:
            if official_col not in official:
                continue
            official_value = float(pd.to_numeric(pd.Series([official.get(official_col)]), errors="coerce").fillna(0).iloc[0])
            current_value = row_stat_sum(rows, player_id, stat)
            diff = official_value - current_value
            if abs(diff) >= 0.0001:
                rows.append(adjustment_row(end_play, stat, player_id, player, round(diff, 4), suffix))
                suffix += 0.001

        shot_specs = [
            ("2PTA", "two-point make", "two-point miss"),
            ("3PTA", "three-point make", "three-point miss"),
            ("FTA", "free-throw make", "free-throw miss"),
        ]
        for attempt_col, make_stat, miss_stat in shot_specs:
            if attempt_col not in official:
                continue
            official_attempts = float(pd.to_numeric(pd.Series([official.get(attempt_col)]), errors="coerce").fillna(0).iloc[0])
            current_attempts = row_stat_sum(rows, player_id, make_stat) + row_stat_sum(rows, player_id, miss_stat)
            diff = official_attempts - current_attempts
            if abs(diff) >= 0.0001:
                rows.append(adjustment_row(end_play, miss_stat, player_id, player, round(diff, 4), suffix))
                suffix += 0.001


def build_stat_events(game_id: str, game_date: str | None = None) -> pd.DataFrame:
    summary = fetch_json(ESPN_SUMMARY_URL, event=game_id)
    player_names, player_teams = athlete_maps(summary)
    plays = summary.get("plays", [])

    rows: list[dict[str, Any]] = []
    for play in plays:
        play_text = (play.get("text") or "").lower()
        type_text = ((play.get("type") or {}).get("text") or "").lower()
        score_value = int(play.get("scoreValue") or 0)

        if play.get("scoringPlay") and score_value > 0:
            row = event_row(
                play,
                "points",
                participant_id(play, 0),
                player_names,
                player_teams,
                score_value,
                True,
            )
            if row:
                rows.append(row)
            make_stat = made_shot_stat(play, score_value)
            if make_stat:
                row = event_row(
                    play,
                    make_stat,
                    participant_id(play, 0),
                    player_names,
                    player_teams,
                    1,
                    True,
                )
                if row:
                    rows.append(row)

        miss_stat = missed_shot_stat(play)
        if miss_stat:
            row = event_row(
                play,
                miss_stat,
                participant_id(play, 0),
                player_names,
                player_teams,
                1,
                False,
            )
            if row:
                rows.append(row)

        if "assists" in play_text:
            row = event_row(
                play,
                "assist",
                participant_id(play, 1),
                player_names,
                player_teams,
                1,
                None,
            )
            if row:
                rows.append(row)

        if "offensive rebound" in type_text:
            row = event_row(
                play,
                "offensive_rebound",
                participant_id(play, 0),
                player_names,
                player_teams,
                1,
                None,
            )
            if row:
                rows.append(row)

        if "defensive rebound" in type_text:
            row = event_row(
                play,
                "defensive_rebound",
                participant_id(play, 0),
                player_names,
                player_teams,
                1,
                None,
            )
            if row:
                rows.append(row)

        if "steals" in play_text:
            row = event_row(
                play,
                "steal",
                participant_id(play, 1),
                player_names,
                player_teams,
                1,
                None,
            )
            if row:
                rows.append(row)

        if "blocks" in play_text:
            row = event_row(
                play,
                "block",
                participant_id(play, 1),
                player_names,
                player_teams,
                1,
                None,
            )
            if row:
                rows.append(row)

        if is_turnover_play(play):
            row = event_row(
                play,
                "turnover",
                participant_id(play, 0),
                player_names,
                player_teams,
                1,
                None,
            )
            if row:
                rows.append(row)

    rows.extend(build_shift_events(plays, summary, player_names, player_teams))
    end_play = next((play for play in reversed(plays) if ((play.get("type") or {}).get("text") or "").lower() in ["end game", "end period"]), plays[-1] if plays else {})
    add_official_adjustments(rows, game_id, end_play)

    events = pd.DataFrame(rows)
    if not events.empty:
        events = events.sort_values(["_sequence_number", "stat"]).reset_index(drop=True)
        events = events.drop(columns=["_sequence_number"])
        events.insert(0, "game_date", game_date or "")
        events.insert(0, "game_id", game_id)
    return events.reindex(columns=STAT_COLUMNS)


def build_games_for_dates(start_date: str, end_date: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for game_date in date_span(start_date, end_date):
        game_ids = game_ids_for_date(game_date)
        print(f"{game_date}: {len(game_ids)} games")
        for game_id in game_ids:
            print(f"  building {game_id}")
            frame = build_stat_events(game_id, game_date=game_date)
            if not frame.empty:
                frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=STAT_COLUMNS)
    combined = pd.concat(frames, ignore_index=True)
    return combined.sort_values(["game_date", "game_id", "wallclock", "stat"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build NBA PBP stat event files.")
    parser.add_argument("--game-id", default=None, help="ESPN game/event id. Defaults to first game on --date.")
    parser.add_argument("--date", default="20241022", help="YYYYMMDD scoreboard date used when --game-id is omitted.")
    parser.add_argument("--start-date", default=None, help="YYYYMMDD first scoreboard date for multi-game output.")
    parser.add_argument("--end-date", default=None, help="YYYYMMDD last scoreboard date for multi-game output.")
    parser.add_argument("--out-dir", default="data_snapshots/pbp", help="Output directory for parquet files.")
    args = parser.parse_args()

    if args.start_date or args.end_date:
        start_date = args.start_date or args.date
        end_date = args.end_date or start_date
        events = build_games_for_dates(start_date, end_date)
        output_stem = f"pbp_stat_events_{start_date}_{end_date}"
        label = f"{start_date}-{end_date}"
    else:
        game_id = args.game_id or first_game_id_for_date(args.date)
        events = build_stat_events(game_id, game_date=args.date)
        output_stem = f"pbp_stat_events_{game_id}"
        label = game_id

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    events_path = out_dir / f"{output_stem}.parquet"
    csv_path = out_dir / f"{output_stem}.csv"
    events.to_parquet(events_path, index=False)
    events.to_csv(csv_path, index=False)

    print(f"built={label}")
    print(f"wrote {len(events):,} stat events to {events_path}")
    print(f"wrote CSV preview to {csv_path}")
    print(events["stat"].value_counts().sort_index().to_string())
    print()
    print("preview")
    print(events.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
