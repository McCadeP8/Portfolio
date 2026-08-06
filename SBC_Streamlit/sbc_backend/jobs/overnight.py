from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import time
from typing import Any, Callable

import pandas as pd
import requests
import functions as fantrax

from ..config import BackendSettings, LiveMode
from ..datasets import DATASETS, DatasetRepository
from ..live import EspnNBAClient, LiveScoreService, as_legacy_player_rows, parse_live_game
from ..storage import FileLock, LockUnavailable, atomic_write_json, atomic_write_parquet
from ..validation import build_repository_manifest, validate_repository
from ..fantrax_rotation import FantraxRotation, planned_post_kinds, simulated_today


PROJECT_ROOT = Path(__file__).resolve().parents[2]
JobFunction = Callable[["JobContext"], dict[str, Any]]


@dataclass(frozen=True)
class JobContext:
    settings: BackendSettings
    repository: DatasetRepository
    target_date: date
    lookback_days: int
    fantrax_slot: str = "all"

    @property
    def season_start(self) -> date:
        return date(self.settings.current_sbc_year - 1, 10, 1)

    @property
    def season_end(self) -> date:
        return date(self.settings.current_sbc_year, 6, 30)

    @property
    def nba_season(self) -> str:
        return f"{self.settings.current_sbc_year - 1}-{str(self.settings.current_sbc_year)[-2:]}"

    @property
    def in_nba_window(self) -> bool:
        return self.season_start <= self.target_date <= self.season_end


@dataclass(frozen=True)
class JobResult:
    name: str
    status: str
    started_at: str
    finished_at: str
    duration_seconds: float
    details: dict[str, Any]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _run_job(name: str, function: JobFunction, context: JobContext) -> JobResult:
    started = _utc_now()
    monotonic_start = time.monotonic()
    try:
        details = function(context)
        status = str(details.pop("status", "ok"))
    except Exception as exc:
        status = "failed"
        details = {"error": f"{type(exc).__name__}: {exc}"}
    finished = _utc_now()
    return JobResult(
        name=name,
        status=status,
        started_at=started.isoformat(),
        finished_at=finished.isoformat(),
        duration_seconds=round(time.monotonic() - monotonic_start, 3),
        details=details,
    )


def refresh_sheets(context: JobContext) -> dict[str, Any]:
    import big_data

    big_data.refresh_sheet_snapshots()
    return {"message": "Google Sheet snapshots refreshed with stale-cache fallback"}


def refresh_league(context: JobContext) -> dict[str, Any]:
    import big_data

    operations = (
        big_data.get_all_team_stats_history,
        big_data.get_all_time_rosters_history,
        big_data.get_all_time_scores,
        big_data.get_all_time_standings,
    )
    completed: list[str] = []
    for operation in operations:
        operation()
        completed.append(operation.__name__)
    return {"operations": completed}


def refresh_espn_boxscores(context: JobContext) -> dict[str, Any]:
    if not context.in_nba_window:
        return {"status": "skipped", "message": "outside the NBA regular-season refresh window"}

    from build_nba_player_game_boxscores import clean_regular_season_boxscores, normalize_boxscores

    start = max(context.season_start, context.target_date - timedelta(days=context.lookback_days))
    client = EspnNBAClient(
        cache_root=context.settings.runtime_root / "espn",
        timeout_seconds=context.settings.http_timeout_seconds,
        live_ttl_seconds=context.settings.live_cache_seconds,
    )
    events = client.regular_season_events(start, context.target_date)
    completed_events = [event for event in events if parse_live_game(event).completed]
    if not completed_events:
        return {"status": "skipped", "message": "no completed ESPN games in lookback", "events_seen": len(events)}

    raw_rows = pd.DataFrame(as_legacy_player_rows(client.player_game_rows(completed_events)))
    if raw_rows.empty:
        return {"status": "skipped", "message": "ESPN returned no player rows"}
    fresh = normalize_boxscores(raw_rows, context.settings.current_sbc_year, context.nba_season)
    fresh = clean_regular_season_boxscores(fresh)
    if fresh.empty:
        return {"status": "skipped", "message": "no valid regular-season player rows"}

    existing_source = context.repository.resolve("nba_boxscores", required=True)
    output = context.settings.data_root / DATASETS["nba_boxscores"].relative_path
    existing = pd.read_parquet(existing_source)
    combined = pd.concat([existing, fresh], ignore_index=True)
    key = ["sbc_year", "nba_game_id", "nba_player_id"]
    combined = combined.drop_duplicates(key, keep="last")
    combined = clean_regular_season_boxscores(combined)
    combined = combined.sort_values(["Date", "nba_game_id", "nba_team", "player_name"]).reset_index(drop=True)
    atomic_write_parquet(combined, output, row_group_size=context.settings.parquet_row_group_size)
    return {
        "path": str(output),
        "games": int(fresh["nba_game_id"].nunique()),
        "new_or_updated_rows": int(len(fresh)),
        "total_rows": int(len(combined)),
    }


def refresh_shots(context: JobContext) -> dict[str, Any]:
    if not context.in_nba_window:
        return {"status": "skipped", "message": "outside the NBA regular-season refresh window"}
    from build_nba_shots import build_from_game_index

    local_index = context.settings.data_root / DATASETS["nba_boxscores"].relative_path
    game_index = local_index if local_index.exists() else context.repository.resolve("nba_boxscores", required=True)
    output_dir = context.settings.snapshot_root / "shots"
    before = context.repository.archive_mtime("data_snapshots/shots/nba_shots_20????.parquet")
    build_from_game_index(game_index, output_dir, checkpoint_every=10)
    after = context.repository.archive_mtime("data_snapshots/shots/nba_shots_20????.parquet")
    return {"path": str(output_dir), "archives_changed": after > before}


def refresh_pbp(context: JobContext) -> dict[str, Any]:
    if not context.in_nba_window:
        return {"status": "skipped", "message": "outside the NBA regular-season refresh window"}
    from build_pbp_one_game import build_games_from_index

    start = max(context.season_start, context.target_date - timedelta(days=context.lookback_days))
    local_index = context.settings.data_root / DATASETS["nba_boxscores"].relative_path
    game_index = local_index if local_index.exists() else context.repository.resolve("nba_boxscores", required=True)
    checkpoint_dir = context.settings.runtime_root / "pbp" / context.nba_season.replace("-", "")
    fresh = build_games_from_index(
        seasons=[context.nba_season],
        start_date=start.strftime("%Y%m%d"),
        end_date=context.target_date.strftime("%Y%m%d"),
        checkpoint_dir=checkpoint_dir,
        boxscore_path=game_index,
    )
    if fresh.empty:
        return {"status": "skipped", "message": "no indexed games in lookback"}
    season_tag = context.nba_season.replace("-", "")
    output = context.settings.snapshot_root / "pbp" / f"pbp_stat_events_{season_tag}.parquet"
    existing = pd.read_parquet(output) if output.exists() else pd.DataFrame(columns=fresh.columns)
    combined = pd.concat([existing, fresh], ignore_index=True)
    key = [column for column in ("game_id", "wallclock", "stat", "player_id", "description") if column in combined.columns]
    if key:
        combined = combined.drop_duplicates(key, keep="last")
    sort_columns = [column for column in ("game_date", "game_id", "wallclock", "stat") if column in combined.columns]
    if sort_columns:
        combined = combined.sort_values(sort_columns).reset_index(drop=True)
    atomic_write_parquet(combined, output, row_group_size=context.settings.parquet_row_group_size)
    return {"path": str(output), "new_or_updated_rows": int(len(fresh)), "total_rows": int(len(combined))}


def refresh_matchups(context: JobContext) -> dict[str, Any]:
    from build_sbc_player_matchup_stats import build_matchup_stats

    table = build_matchup_stats()
    if table.empty:
        return {"status": "skipped", "message": "no matchup rows produced"}
    output = context.settings.data_root / "sbc_player_matchup_stats.parquet"
    atomic_write_parquet(table, output, row_group_size=context.settings.parquet_row_group_size)
    return {"path": str(output), "rows": int(len(table))}


def collect_live_shadow(context: JobContext) -> dict[str, Any]:
    if context.settings.live_mode is LiveMode.OFF:
        return {"status": "skipped", "message": "SBC_LIVE_MODE=off"}
    snapshot = LiveScoreService(context.settings).collect(context.target_date)
    if snapshot is None:
        return {"status": "skipped", "message": "live collection disabled"}
    return {
        "mode": context.settings.live_mode.value,
        "games": len(snapshot.games),
        "player_rows": int(len(snapshot.player_stats)),
        "published": context.settings.live_mode is LiveMode.LIVE,
    }


def validate_and_catalog(context: JobContext) -> dict[str, Any]:
    report = validate_repository(context.repository)
    manifest = build_repository_manifest(context.repository)
    atomic_write_json(report.as_dict(), context.settings.metadata_root / "validation.json")
    atomic_write_json(manifest, context.settings.metadata_root / "data_manifest.json")
    if not report.ok:
        messages = "; ".join(f"{item.dataset}: {item.message}" for item in report.errors)
        raise RuntimeError(messages)
    return {
        "datasets": manifest["totals"]["files"],
        "rows": manifest["totals"]["rows"],
        "bytes": manifest["totals"]["bytes"],
        "warnings": sum(item.status == "warning" for item in report.items),
    }


def publish_fantrax_rotation(context: JobContext) -> dict[str, Any]:
    """Render and publish the date-aware nightly Fantrax image rotation."""
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    offset_days = int(os.getenv("SBC_FANTRAX_DATE_OFFSET_DAYS", "168"))
    publishing_date = simulated_today(context.target_date, offset_days)
    rotation = FantraxRotation(context.repository, PROJECT_ROOT, publishing_date)
    kinds = planned_post_kinds(rotation.period, context.fantrax_slot)
    if rotation.period is None:
        return {
            "status": "skipped",
            "publishing_date": publishing_date.isoformat(),
            "message": "simulated date is outside the SBC matchup calendar",
        }
    if not webhook:
        return {
            "status": "skipped",
            "publishing_date": publishing_date.isoformat(),
            "year": rotation.period.year,
            "period": rotation.period.period,
            "slot": context.fantrax_slot,
            "planned": kinds,
            "message": "DISCORD_WEBHOOK_URL is not configured",
        }
    posts, skipped = rotation.build_posts(kinds)
    published = []
    for post in posts:
        fantrax.post_fantrax_webhook(
            webhook,
            message="",
            image_bytes=post.image_bytes,
            image_filename=post.filename,
        )
        published.append({"kind": post.kind, "filename": post.filename, "bytes": len(post.image_bytes)})
        # Six images can be published in the 2 a.m. slot. Leave breathing room
        # between webhook calls instead of relying on Discord's 429 retry path.
        time.sleep(0.6)
    return {
        "publishing_date": publishing_date.isoformat(),
        "year": rotation.period.year,
        "period": rotation.period.period,
        "slot": context.fantrax_slot,
        "period_start": rotation.period.start.isoformat(),
        "period_end": rotation.period.end.isoformat(),
        "planned": kinds,
        "published": published,
        "skipped": skipped,
    }


JOBS: dict[str, JobFunction] = {
    "sheets": refresh_sheets,
    "league": refresh_league,
    "espn_boxscores": refresh_espn_boxscores,
    "shots": refresh_shots,
    "pbp": refresh_pbp,
    "matchups": refresh_matchups,
    "live_shadow": collect_live_shadow,
    "validate": validate_and_catalog,
    "fantrax_rotation": publish_fantrax_rotation,
}


def _notify_summary(payload: dict[str, Any]) -> None:
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        return
    failures = [result["name"] for result in payload["results"] if result["status"] == "failed"]
    # Successful runs already publish the rotation images. Only send a text
    # health notification when something failed, avoiding a daily noise post.
    if not failures:
        return
    message = f"SBC overnight refresh failed for {payload['target_date']}. Failed: {', '.join(failures)}"
    try:
        requests.post(webhook, json={"content": message}, timeout=10).raise_for_status()
    except requests.RequestException as exc:
        print(f"Discord notification failed: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the resilient SBC overnight data refresh pipeline.")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="Target date (YYYY-MM-DD).")
    parser.add_argument("--lookback-days", type=int, default=3, help="Days to recheck for late ESPN corrections.")
    parser.add_argument("--jobs", nargs="+", choices=tuple(JOBS), default=list(JOBS), help="Ordered jobs to run.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved plan without writing or fetching.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any job fails.")
    parser.add_argument("--fantrax-slot", choices=("all", "overnight", "opening"), default="all", help="Select the 2 a.m. or 3 a.m. publishing rotation.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = BackendSettings.from_env(PROJECT_ROOT)
    repository = DatasetRepository(settings)
    context = JobContext(settings, repository, args.date, max(0, args.lookback_days), args.fantrax_slot)
    if args.dry_run:
        offset_days = int(os.getenv("SBC_FANTRAX_DATE_OFFSET_DAYS", "168"))
        publishing_date = simulated_today(args.date, offset_days)
        calendar = __import__("functions").get_period_calendar()
        from ..fantrax_rotation import period_for_date
        rotation_period = period_for_date(calendar, publishing_date)
        print(json.dumps({
            "target_date": args.date.isoformat(),
            "fantrax_date": publishing_date.isoformat(),
            "fantrax_offset_days": offset_days,
            "fantrax_period": None if rotation_period is None else {
                "year": rotation_period.year,
                "period": rotation_period.period,
                "start": rotation_period.start.isoformat(),
                "end": rotation_period.end.isoformat(),
                "planned": planned_post_kinds(rotation_period, args.fantrax_slot),
            },
            "current_sbc_year": settings.current_sbc_year,
            "nba_season": context.nba_season,
            "live_mode": settings.live_mode.value,
            "jobs": args.jobs,
        }, indent=2))
        return 0

    settings.ensure_runtime_directories()
    started = _utc_now()
    results: list[JobResult] = []
    try:
        with FileLock(settings.lock_root / "overnight.lock"):
            for name in args.jobs:
                print(f"\n=== {name} ===", flush=True)
                result = _run_job(name, JOBS[name], context)
                results.append(result)
                print(f"{result.status}: {json.dumps(result.details, default=str)}", flush=True)
    except LockUnavailable as exc:
        print(str(exc))
        return 2

    failed = [result for result in results if result.status == "failed"]
    payload = {
        "schema_version": 1,
        "status": "failed" if failed else "ok",
        "target_date": args.date.isoformat(),
        "started_at": started.isoformat(),
        "finished_at": _utc_now().isoformat(),
        "live_mode": settings.live_mode.value,
        "results": [asdict(result) for result in results],
    }
    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    atomic_write_json(payload, settings.run_root / f"{stamp}.json")
    atomic_write_json(payload, settings.run_root / "latest.json")
    _notify_summary(payload)
    print(json.dumps(payload, indent=2, default=str))
    return 1 if failed and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
