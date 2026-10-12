from __future__ import annotations

from typing import Any

import pandas as pd


def _issue(level: str, check: str, message: str, value: Any = None) -> dict[str, Any]:
    return {"level": level, "check": check, "message": message, "observed_value": value}


def validate_foundation(
    teams: pd.DataFrame,
    rosters: pd.DataFrame,
    schedule: pd.DataFrame,
    categories: pd.DataFrame,
    projections: pd.DataFrame | None,
    config: dict[str, Any],
) -> pd.DataFrame:
    issues: list[dict[str, Any]] = []
    team_count = teams["fantasy_team_id"].nunique() if "fantasy_team_id" in teams else 0
    expected_teams = int(config["expected_team_count"])
    if team_count != expected_teams:
        issues.append(_issue("error", "team_count", f"Expected {expected_teams} teams", team_count))
    if rosters.empty:
        issues.append(_issue("error", "rosters_present", "No roster rows were loaded", 0))
    elif rosters["fantrax_player_id"].duplicated().any():
        duplicates = int(rosters["fantrax_player_id"].duplicated(keep=False).sum())
        issues.append(_issue("error", "unique_ownership", "Players appear on multiple roster rows", duplicates))
    regular_periods = schedule.loc[
        pd.to_numeric(schedule.get("period"), errors="coerce").between(1, int(config["expected_regular_season_periods"]))
    ] if not schedule.empty else schedule
    if not regular_periods.empty:
        appearances = pd.concat(
            [regular_periods[["period", "away_team_id"]].rename(columns={"away_team_id": "team_id"}),
             regular_periods[["period", "home_team_id"]].rename(columns={"home_team_id": "team_id"})]
        ).groupby(["period", "team_id"]).size()
        expected_opponents = int(config["expected_opponents_per_regular_period"])
        bad = appearances[appearances.ne(expected_opponents)]
        if not bad.empty:
            issues.append(_issue("error", "opponents_per_period", f"Expected {expected_opponents} opponents per team-period", len(bad)))
    expected_categories = int(config["expected_category_count"])
    if len(categories) != expected_categories:
        issues.append(_issue("error", "category_count", f"Expected {expected_categories} scoring categories", len(categories)))
    weight_total = pd.to_numeric(categories.get("weight", pd.Series(dtype=float)), errors="coerce").sum()
    if weight_total != float(config["expected_weight_total"]):
        issues.append(_issue("error", "category_weight_total", f"Expected weights to total {config['expected_weight_total']}", weight_total))
    if projections is None or projections.empty:
        issues.append(_issue("warning", "projections_present", "No projection source has been imported", 0))
    else:
        duplicate_names = projections["player_name"].map(str.lower).duplicated(keep=False).sum()
        if duplicate_names:
            issues.append(_issue("warning", "duplicate_projections", "Duplicate projection player names require review", int(duplicate_names)))
        percentage_columns = [column for column in ("fg_pct", "ft_pct", "three_pct", "two_pct", "ts_pct") if column in projections]
        invalid_percentages = sum(
            int((pd.to_numeric(projections[column], errors="coerce").dropna().between(0, 1) == False).sum())
            for column in percentage_columns
        )
        if invalid_percentages:
            issues.append(_issue("error", "percentage_ranges", "Shooting percentages fall outside 0–1", invalid_percentages))
        invalid_shooting = 0
        for made, attempted in (("fg_m", "fg_a"), ("ft_m", "ft_a"), ("three_m", "three_a"), ("two_m", "two_a")):
            if made in projections and attempted in projections:
                made_values = pd.to_numeric(projections[made], errors="coerce")
                attempted_values = pd.to_numeric(projections[attempted], errors="coerce")
                invalid_shooting += int((made_values > attempted_values).sum())
                invalid_shooting += int((made_values < 0).sum() + (attempted_values < 0).sum())
        if invalid_shooting:
            issues.append(_issue("error", "shooting_volume", "Shooting makes/attempts are negative or makes exceed attempts", invalid_shooting))
    if not issues:
        issues.append(_issue("ok", "foundation", "All configured foundation checks passed"))
    return pd.DataFrame(issues)

