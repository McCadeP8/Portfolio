from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .fantrax import FantraxClient
from .history import import_sbc_history
from .paths import CONFIG_DIR, PROCESSED_DIR, RAW_DIR, ensure_directories
from .pipeline import build_canonical
from .projections import import_google_sheet_projections, import_projections
from .ratings import write_ratings
from .counting_models import write_counting_models
from .shooting_models import write_shooting_models
from .overall_model import write_overall_model
from .player_value import write_player_value_ratings
from .team_outlook import write_team_outlook
from .player_archetypes import write_player_archetypes
from .backtesting import write_season_backtests


def _config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_fantrax(config_path: Path, period: int | None = None) -> None:
    ensure_directories()
    config = _config(config_path)
    period = int(period or config["roster_period"])
    client = FantraxClient(config["fantrax_league_id"], RAW_DIR / "fantrax")
    rosters, roster_teams = client.fetch_rosters(period)
    players = client.fetch_player_catalog()
    schedule, schedule_teams = client.fetch_schedule()
    teams = schedule_teams.merge(roster_teams, on=["fantasy_team_id", "fantasy_team_name"], how="outer")
    teams = teams[
        teams["fantasy_team_id"].astype(str).str.strip().ne("")
        & teams["fantasy_team_name"].astype(str).str.strip().ne("")
    ].reset_index(drop=True)
    rosters.to_csv(PROCESSED_DIR / "rosters.csv", index=False)
    players.to_csv(PROCESSED_DIR / "fantrax_players.csv", index=False)
    schedule.to_csv(PROCESSED_DIR / "schedule.csv", index=False)
    teams.to_csv(PROCESSED_DIR / "teams.csv", index=False)
    print(f"Loaded {len(teams)} teams, {len(rosters)} roster slots, and {len(schedule)} matchups.")


def build_everything(config_path: Path) -> dict[str, int]:
    """Rebuild every derived output from the saved local source snapshots."""
    ensure_directories()
    print("[1/8] Building canonical player, roster, and validation data...")
    issues = build_canonical(
        PROCESSED_DIR,
        config_path,
        CONFIG_DIR / "categories.csv",
        CONFIG_DIR / "player_aliases.csv",
    )
    print("[2/8] Building legacy team, player, category, and fit ratings...")
    write_ratings(PROCESSED_DIR, CONFIG_DIR / "categories.csv")
    print("[3/8] Fitting nine counting-category win models...")
    write_counting_models(PROCESSED_DIR)
    print("[4/8] Fitting four shooting-category win models...")
    write_shooting_models(PROCESSED_DIR, RAW_DIR)
    print("[5/8] Fitting the 13-input overall matchup model...")
    write_overall_model(PROCESSED_DIR, RAW_DIR)
    print("[6/8] Running leave-one-season-out model backtests...")
    backtests = write_season_backtests(PROCESSED_DIR, RAW_DIR)
    print("[7/8] Building player value and team chemistry outputs...")
    write_player_value_ratings(PROCESSED_DIR)
    outlook = write_team_outlook(PROCESSED_DIR, RAW_DIR, CONFIG_DIR / "categories.csv")
    print("[8/8] Classifying player archetypes and similarity groups...")
    archetypes = write_player_archetypes(PROCESSED_DIR, CONFIG_DIR / "categories.csv")
    return {
        "validation_issues": len(issues),
        "backtest_models": backtests["models"],
        "backtest_folds": backtests["folds"],
        "teams": outlook["teams"],
        "rated_players": archetypes["rated_players"],
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Fantasy basketball Phase 1 data pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    fetch = subparsers.add_parser("fetch-fantrax", help="Snapshot and normalize Fantrax league data")
    fetch.add_argument("--config", type=Path, default=CONFIG_DIR / "league.json")
    fetch.add_argument("--period", type=int)
    projections = subparsers.add_parser("import-projections", help="Import a user-supplied projection file")
    projections.add_argument("source", type=Path)
    projections.add_argument("--provider", default="Hashtag Basketball")
    projections.add_argument("--snapshot-date")
    google = subparsers.add_parser("import-google-projections", help="Import the configured Google Sheet projection tab")
    google.add_argument("--config", type=Path, default=CONFIG_DIR / "projections.json")
    google.add_argument("--snapshot-date")
    build = subparsers.add_parser("build", help="Build canonical data and validation reports")
    build.add_argument("--config", type=Path, default=CONFIG_DIR / "league.json")
    history = subparsers.add_parser("import-history", help="Import SBCFBL history and build league-level analytics")
    history.add_argument("--sbc-project", type=Path, default=CONFIG_DIR.parent.parent / "SBC_Streamlit")
    history.add_argument("--fetch-current-nba-schedule", action="store_true")
    subparsers.add_parser("rate", help="Build team, player, category, and 30-team fit ratings")
    subparsers.add_parser("fit-counting-models", help="Fit nine historical category-win logistic regressions")
    subparsers.add_parser("fit-shooting-models", help="Fit four volume-weighted shooting category models")
    subparsers.add_parser("fit-overall-model", help="Fit the 13-input overall matchup-win model")
    subparsers.add_parser("backtest-models", help="Run leave-one-season-out backtests for all 14 win models")
    subparsers.add_parser("rate-player-value", help="Build replacement-player category and overall ratings")
    subparsers.add_parser("rate-team-outlook", help="Build projected team skill, score, chemistry, and rank")
    subparsers.add_parser("classify-player-archetypes", help="Score eight player archetypes and build hierarchical similarity groups")
    build_all = subparsers.add_parser("build-all", help="Rebuild every derived output from saved local snapshots")
    build_all.add_argument("--config", type=Path, default=CONFIG_DIR / "league.json")
    args = parser.parse_args(argv)
    if args.command == "fetch-fantrax":
        fetch_fantrax(args.config, args.period)
    elif args.command == "import-projections":
        ensure_directories()
        frame, missing, preserved = import_projections(
            args.source, RAW_DIR / "projections", args.provider, args.snapshot_date
        )
        frame.to_csv(PROCESSED_DIR / "projections.csv", index=False)
        print(f"Imported {len(frame)} projections; preserved source at {preserved}")
        print("Missing optional fields: " + ", ".join(missing))
    elif args.command == "import-google-projections":
        ensure_directories()
        source_config = _config(args.config)
        frame, missing, preserved = import_google_sheet_projections(
            source_config["spreadsheet_id"],
            source_config["sheet_gid"],
            RAW_DIR / "projections",
            source_config.get("provider", "Hashtag Basketball"),
            args.snapshot_date,
            source_config.get("stat_basis", "season_total"),
            source_config.get("minutes_basis", "per_game"),
        )
        frame.to_csv(PROCESSED_DIR / "projections.csv", index=False)
        print(f"Imported {len(frame)} projections; preserved source at {preserved}")
        print("Unavailable source fields: " + ", ".join(missing))
    elif args.command == "build":
        issues = build_canonical(
            PROCESSED_DIR,
            args.config,
            CONFIG_DIR / "categories.csv",
            CONFIG_DIR / "player_aliases.csv",
        )
        print(issues.to_string(index=False))
    elif args.command == "import-history":
        ensure_directories()
        counts = import_sbc_history(
            args.sbc_project,
            RAW_DIR / "sbc_streamlit",
            PROCESSED_DIR,
            fetch_current_schedule=args.fetch_current_nba_schedule,
        )
        print(
            f"Imported {counts['seasons']} completed seasons and {counts['matchups']} matchups; "
            f"mapped {counts['period_days']} SBCFBL calendar days and {counts['nba_games']} NBA games."
        )
    elif args.command == "rate":
        ensure_directories()
        counts = write_ratings(PROCESSED_DIR, CONFIG_DIR / "categories.csv")
        print(
            f"Built {counts['team_ratings']} team ratings, {counts['player_ratings']} player ratings, "
            f"and {counts['player_team_fit']} player-team fit evaluations."
        )
    elif args.command == "fit-counting-models":
        ensure_directories()
        counts = write_counting_models(PROCESSED_DIR)
        models = pd.read_csv(PROCESSED_DIR / "counting_logistic_models.csv")
        print(models[[
            "category", "threshold_50", "slope", "slope_se", "odds_ratio_per_unit",
            "auc", "brier_score", "mcfadden_r2", "matchups",
        ]].to_string(index=False))
        print(f"Built {counts['models']} models, {counts['curves']} curve points, and {counts['bins']} calibration points.")
    elif args.command == "fit-shooting-models":
        ensure_directories()
        counts = write_shooting_models(PROCESSED_DIR, RAW_DIR)
        models = pd.read_csv(PROCESSED_DIR / "shooting_logistic_models.csv")
        print(models[[
            "category", "threshold_50", "slope", "slope_se", "odds_ratio_per_unit",
            "auc", "brier_score", "mcfadden_r2", "matchups",
        ]].to_string(index=False))
        print(
            f"Built {counts['models']} shooting models and points-gained metrics for "
            f"{counts['players']} projected players."
        )
    elif args.command == "fit-overall-model":
        ensure_directories()
        counts = write_overall_model(PROCESSED_DIR, RAW_DIR)
        summary = pd.read_csv(PROCESSED_DIR / "overall_logistic_model.csv").iloc[0]
        print(
            f"Built the 13-input overall model on {int(summary['matchups']):,} matchups: "
            f"AUC={summary['auc']:.3f}, Brier={summary['brier_score']:.3f}, "
            f"McFadden R2={summary['mcfadden_r2']:.3f}."
        )
    elif args.command == "backtest-models":
        ensure_directories()
        counts = write_season_backtests(PROCESSED_DIR, RAW_DIR)
        summary = pd.read_csv(PROCESSED_DIR / "season_backtest_summary.csv")
        print(summary[[
            "category", "seasons", "auc", "brier_score", "log_loss", "calibration_error",
        ]].to_string(index=False))
        print(
            f"Backtested {counts['models']} models across {counts['seasons']} held-out seasons "
            f"and {counts['predictions']:,} out-of-sample team observations."
        )
    elif args.command == "rate-player-value":
        ensure_directories()
        counts = write_player_value_ratings(PROCESSED_DIR)
        print(
            f"Built {counts['categories']} category ratings and one overall rating for "
            f"{counts['rated_players']} players with projections."
        )
    elif args.command == "rate-team-outlook":
        ensure_directories()
        counts = write_team_outlook(PROCESSED_DIR, RAW_DIR, CONFIG_DIR / "categories.csv")
        print(
            f"Built projected skill, expected score, chemistry, and league rank for "
            f"{counts['teams']} teams across {counts['categories']} categories."
        )
    elif args.command == "classify-player-archetypes":
        ensure_directories()
        counts = write_player_archetypes(PROCESSED_DIR, CONFIG_DIR / "categories.csv")
        print(
            f"Scored {counts['rated_players']} projected players across eight archetypes; "
            f"observed {counts['archetypes_observed']} of 64 possible labels and built "
            f"{counts['hierarchical_clusters']} Ward similarity clusters."
        )
    elif args.command == "build-all":
        counts = build_everything(args.config)
        print(
            f"Build complete: {counts['teams']} teams, {counts['rated_players']} rated players, "
            f"{counts['backtest_models']} backtested models across {counts['backtest_folds']} season folds, "
            f"and {counts['validation_issues']} validation issue rows."
        )


if __name__ == "__main__":
    main()

