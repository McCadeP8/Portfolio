"""Tuesday-runnable Yahoo refresh for the two 2026 Smack Talkers leagues."""

from pathlib import Path

from yahoo_2026 import DEFAULT_PROCESSED_DIR, refresh_yahoo_2026


def main() -> int:
    root = Path(__file__).resolve().parent
    try:
        statuses, teams, matchups = refresh_yahoo_2026(root)
    except Exception as error:
        print(f"[FATAL] Yahoo refresh could not start: {type(error).__name__}: {error}")
        return 1

    game_key = statuses[0]["game_key"] if statuses else "unknown"
    print(f"Current Yahoo NFL game key: {game_key}")
    for status in statuses:
        if status["success"]:
            team_count = sum(row["league_key"] == status["league_key"] for row in teams)
            matchup_count = sum(row["league_key"] == status["league_key"] for row in matchups)
            print(
                f"[OK] {status['league_label']}: {status['league_key']} | "
                f"week {status['current_week']} | {team_count} teams | {matchup_count} matchups"
            )
        else:
            print(f"[FAIL] {status['league_label']}: {status['league_key']} | {status['error']}")
    print(f"Normalized parquet files: {root / DEFAULT_PROCESSED_DIR}")
    return 0 if all(status["success"] for status in statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
