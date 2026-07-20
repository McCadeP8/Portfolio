r"""Build a compact ESPN shot-location parquet for an NBA date range.

Initial SBC sample:
    .\.venv\Scripts\python.exe build_nba_shots.py --start-date 20241022 --end-date 20241025
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import time

import pandas as pd
import requests


SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
DEFAULT_OUTPUT = Path("data_snapshots/shots/nba_shots_20241022_20241025.parquet")


def fetch_json(url: str, **params) -> dict:
    last_error = None
    for attempt in range(1, 5):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if attempt < 4:
                time.sleep(attempt * 1.5)
    raise RuntimeError(f"Unable to fetch {url} {params}") from last_error


def date_span(start_text: str, end_text: str) -> list[str]:
    start = datetime.strptime(start_text, "%Y%m%d").date()
    end = datetime.strptime(end_text, "%Y%m%d").date()
    values = []
    current = start
    while current <= end:
        values.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return values


def game_sides(summary: dict) -> dict[str, str]:
    competitors = summary.get("header", {}).get("competitions", [{}])[0].get("competitors", [])
    return {str(item.get("team", {}).get("id")): str(item.get("homeAway", "")) for item in competitors}


def shot_rows(game_id: str, game_date: str, summary: dict) -> list[dict]:
    sides = game_sides(summary)
    rows = []
    for play in summary.get("plays", []):
        coordinate = play.get("coordinate") or {}
        participants = play.get("participants") or []
        player_id = ((participants[0].get("athlete") or {}).get("id")) if participants else None
        play_text = str(play.get("text", ""))
        type_text = str((play.get("type") or {}).get("text", ""))
        is_free_throw = "free throw" in f"{type_text} {play_text}".lower()
        if is_free_throw or not play.get("shootingPlay") or player_id is None or coordinate.get("x") is None or coordinate.get("y") is None:
            continue
        team_id = str((play.get("team") or {}).get("id", ""))
        rows.append({
            "game_id": str(game_id),
            "game_date": str(game_date),
            "shot_id": str(play.get("id", play.get("sequenceNumber", ""))),
            "sequence_number": int(play.get("sequenceNumber") or 0),
            "player_id": str(player_id),
            "nba_team_id": team_id,
            "home_away": sides.get(team_id, ""),
            "x": float(coordinate["x"]),
            "y": float(coordinate["y"]),
            "made": bool(play.get("scoringPlay")),
            "points_attempted": int(play.get("pointsAttempted") or (play.get("scoreValue") or 0)),
            "period": int((play.get("period") or {}).get("number") or 0),
            "clock": str((play.get("clock") or {}).get("displayValue", "")),
            "description": play_text,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="20241022")
    parser.add_argument("--end-date", default="20241025")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows = []
    for game_date in date_span(args.start_date, args.end_date):
        scoreboard = fetch_json(SCOREBOARD_URL, dates=game_date)
        game_ids = [str(event.get("id")) for event in scoreboard.get("events", []) if event.get("id")]
        print(f"{game_date}: {len(game_ids)} games")
        for game_id in game_ids:
            summary = fetch_json(SUMMARY_URL, event=game_id)
            rows.extend(shot_rows(game_id, game_date, summary))

    output = pd.DataFrame(rows).drop_duplicates(["game_id", "shot_id"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(args.output, index=False)
    print(f"Saved {len(output):,} shots from {output['game_id'].nunique():,} games to {args.output}")


if __name__ == "__main__":
    main()
