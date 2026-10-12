from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .matching import match_players
from .validation import validate_foundation


NBA_TEAM_SEASON_MINUTES = 19_680.0


def allocate_team_plus_minus(
    players: pd.DataFrame,
    team_totals: pd.DataFrame,
    team_minutes: float = NBA_TEAM_SEASON_MINUTES,
) -> pd.DataFrame:
    """Allocate an NBA team's projected +/- by each player's projected minute share."""
    result = players.copy()
    totals = team_totals.set_index("nba_team")["projected_season_plus_minus"]
    team = result["nba_team"].fillna("").astype(str).str.strip().str.upper()
    games = pd.to_numeric(result["games"], errors="coerce").fillna(0.0)
    minutes = pd.to_numeric(result["minutes"], errors="coerce").fillna(0.0)
    team_plus_minus = team.map(totals)
    result["plus_minus"] = (games * minutes / team_minutes * team_plus_minus).fillna(0.0)
    return result


def read_categories(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=["category", "weight", "direction"])
    return pd.read_csv(path)


def zero_teamless_projection_values(
    canonical: pd.DataFrame, projection_numeric_columns: list[str]
) -> pd.DataFrame:
    """Zero modeling inputs for players who are not assigned to an NBA team."""
    result = canonical.copy()
    nba_team = result["nba_team"].fillna("").astype(str).str.strip().str.upper()
    teamless = nba_team.isin({"", "(N/A)", "N/A"})
    columns = [column for column in projection_numeric_columns if column in result.columns]
    result.loc[teamless, columns] = 0
    return result


def build_canonical(
    processed_dir: Path, config_path: Path, categories_path: Path, aliases_path: Path
) -> pd.DataFrame:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    teams = pd.read_csv(processed_dir / "teams.csv")
    rosters = pd.read_csv(processed_dir / "rosters.csv", dtype={"fantrax_player_id": str})
    schedule = pd.read_csv(processed_dir / "schedule.csv")
    players = pd.read_csv(processed_dir / "fantrax_players.csv", dtype={"fantrax_player_id": str})
    categories = read_categories(categories_path)
    projection_path = processed_dir / "projections.csv"
    projections = pd.read_csv(projection_path) if projection_path.exists() else None
    canonical = rosters.merge(players, on="fantrax_player_id", how="left", validate="many_to_one")
    matched = None
    exceptions = pd.DataFrame()
    if projections is not None:
        aliases = pd.read_csv(aliases_path) if aliases_path.exists() else None
        matched, exceptions = match_players(players, projections, aliases)
        exceptions.to_csv(processed_dir / "player_match_exceptions.csv", index=False)
        matched_for_join = matched[matched["fantrax_player_id"].notna()].copy()
        projection_columns = [c for c in matched.columns if c not in {"player_name", "nba_team", "eligible_positions"}]
        canonical = canonical.merge(matched_for_join[projection_columns], on="fantrax_player_id", how="left", validate="many_to_one")
        projection_numeric_columns = matched.select_dtypes(include="number").columns.tolist()
        canonical = zero_teamless_projection_values(canonical, projection_numeric_columns)
        plus_minus_path = config_path.parent / "nba_team_plus_minus.csv"
        if plus_minus_path.exists():
            canonical = allocate_team_plus_minus(canonical, pd.read_csv(plus_minus_path))
    canonical.to_csv(processed_dir / "canonical_player_projections.csv", index=False)
    issues = validate_foundation(teams, rosters, schedule, categories, projections, config)
    if matched is not None:
        rostered_ids = set(rosters["fantrax_player_id"].dropna().astype(str))
        projected_ids = set(matched["fantrax_player_id"].dropna().astype(str))
        missing_rostered = rostered_ids - projected_ids
        if missing_rostered:
            issues = pd.concat([issues, pd.DataFrame([{
                "level": "warning",
                "check": "rostered_projection_coverage",
                "message": "Rostered players without a matched projection",
                "observed_value": len(missing_rostered),
            }])], ignore_index=True)
        if not exceptions.empty:
            issues = pd.concat([issues, pd.DataFrame([{
                "level": "warning",
                "check": "unmatched_projection_players",
                "message": "Projection players require identity review",
                "observed_value": len(exceptions),
            }])], ignore_index=True)
    if issues["level"].ne("ok").any():
        issues = issues[issues["level"].ne("ok")].reset_index(drop=True)
    issues.to_csv(processed_dir / "data_quality_issues.csv", index=False)
    return issues

