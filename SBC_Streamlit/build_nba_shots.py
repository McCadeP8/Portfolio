r"""Build compact, resumable ESPN shot-location parquets.

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

from sbc_backend.config import BackendSettings
from sbc_backend.storage import atomic_write_parquet, atomic_write_text


SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
DEFAULT_OUTPUT = Path("data_snapshots/shots/nba_shots_20241022_20241025.parquet")
DEFAULT_GAME_INDEX = Path("nba_player_game_boxscores_2021_2026.parquet")
SHOT_COLUMNS = [
    "game_id", "game_date", "shot_id", "sequence_number", "player_id",
    "nba_team_id", "home_away", "x", "y", "made", "points_attempted",
    "period", "clock", "description",
]
BACKEND_SETTINGS = BackendSettings.from_env(Path(__file__).resolve().parent)


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


def save_checkpoint(rows: list[dict], output_path: Path) -> None:
    """Merge a fetched batch into its season parquet without losing prior work."""
    if not rows:
        return
    new = pd.DataFrame(rows, columns=SHOT_COLUMNS)
    if output_path.exists():
        new = pd.concat([pd.read_parquet(output_path), new], ignore_index=True)
    new = new.drop_duplicates(["game_id", "shot_id"]).sort_values(
        ["game_date", "game_id", "sequence_number"]
    )
    atomic_write_parquet(
        new,
        output_path,
        row_group_size=BACKEND_SETTINGS.parquet_row_group_size,
    )


def completed_path(output_path: Path) -> Path:
    return output_path.with_suffix(".completed_games.txt")


def load_completed(output_path: Path) -> set[str]:
    path = completed_path(output_path)
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def save_completed(output_path: Path, game_ids: set[str]) -> None:
    path = completed_path(output_path)
    atomic_write_text("\n".join(sorted(game_ids)) + "\n", path)


def build_from_game_index(game_index: Path, output_dir: Path, checkpoint_every: int) -> None:
    games = pd.read_parquet(game_index, columns=["sbc_year", "nba_season", "Date", "nba_game_id"])
    games = games.drop_duplicates("nba_game_id").copy()
    games["game_date"] = pd.to_datetime(games["Date"], errors="coerce").dt.strftime("%Y%m%d")
    games = games.dropna(subset=["game_date", "nba_game_id"]).sort_values(["sbc_year", "game_date", "nba_game_id"])

    for (_, nba_season), season_games in games.groupby(["sbc_year", "nba_season"], sort=True):
        season_tag = str(nba_season).replace("-", "")
        output_path = output_dir / f"nba_shots_{season_tag}.parquet"
        completed = load_completed(output_path)
        pending = season_games[~season_games["nba_game_id"].astype(str).isin(completed)]
        print(f"{nba_season}: {len(completed):,} complete, {len(pending):,} remaining", flush=True)
        batch_rows: list[dict] = []
        batch_games: list[str] = []
        for counter, row in enumerate(pending.itertuples(index=False), start=1):
            game_id = str(row.nba_game_id)
            summary = fetch_json(SUMMARY_URL, event=game_id)
            batch_rows.extend(shot_rows(game_id, row.game_date, summary))
            batch_games.append(game_id)
            if counter % checkpoint_every == 0 or counter == len(pending):
                save_checkpoint(batch_rows, output_path)
                completed.update(batch_games)
                save_completed(output_path, completed)
                print(
                    f"  {nba_season}: {len(completed):,}/{len(season_games):,} games; "
                    f"saved {len(batch_rows):,} new shots",
                    flush=True,
                )
                batch_rows.clear()
                batch_games.clear()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="20241022")
    parser.add_argument("--end-date", default="20241025")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--game-index", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data_snapshots/shots"))
    parser.add_argument("--checkpoint-every", type=int, default=25)
    args = parser.parse_args()

    if args.game_index:
        build_from_game_index(args.game_index, args.output_dir, max(1, args.checkpoint_every))
        return

    rows = []
    for game_date in date_span(args.start_date, args.end_date):
        scoreboard = fetch_json(SCOREBOARD_URL, dates=game_date)
        game_ids = [str(event.get("id")) for event in scoreboard.get("events", []) if event.get("id")]
        print(f"{game_date}: {len(game_ids)} games")
        for game_id in game_ids:
            summary = fetch_json(SUMMARY_URL, event=game_id)
            rows.extend(shot_rows(game_id, game_date, summary))

    output = pd.DataFrame(rows).drop_duplicates(["game_id", "shot_id"])
    atomic_write_parquet(
        output,
        args.output,
        row_group_size=BACKEND_SETTINGS.parquet_row_group_size,
    )
    print(f"Saved {len(output):,} shots from {output['game_id'].nunique():,} games to {args.output}")


if __name__ == "__main__":
    main()
