"""Persist deterministic jersey matchups for a schedule season."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from jersey_engine import JerseyConfig
from jersey_rotation import select_game_uniforms


ROOT = Path(__file__).resolve().parent


def main(year: int = 2027) -> None:
    schedule_path = ROOT / "all_time_scores.parquet"
    config_path = ROOT / "jersey_team_configs.csv"
    schedule = pd.read_parquet(schedule_path)
    configs = pd.read_csv(config_path).fillna("")

    def config_loader(team: str, edition: str) -> JerseyConfig:
        match = configs[(configs["team"].astype(str) == team) & (configs["edition"].astype(str) == edition)]
        return JerseyConfig.from_mapping(match.iloc[0].to_dict()) if not match.empty else JerseyConfig(team=team, edition=edition)

    for column in ["RoadJersey", "HomeJersey"]:
        if column not in schedule:
            schedule[column] = ""
    if "JerseyClashAdjusted" not in schedule:
        schedule["JerseyClashAdjusted"] = False
    schedule["JerseyClashAdjusted"] = schedule["JerseyClashAdjusted"].fillna(False).astype(bool)

    season_mask = pd.to_numeric(schedule["Year"], errors="coerce").eq(year)
    for index, row in schedule[season_mask].iterrows():
        road_team = str(row.get("TeamA", ""))
        home_team = str(row.get("TeamB", ""))
        if not road_team or not home_team or road_team.startswith("#") or home_team.startswith("#") or road_team == "TBD" or home_team == "TBD":
            continue
        road, home, adjusted = select_game_uniforms(row.to_dict(), road_team, home_team, config_loader)
        schedule.at[index, "RoadJersey"] = road
        schedule.at[index, "HomeJersey"] = home
        schedule.at[index, "JerseyClashAdjusted"] = bool(adjusted)

    schedule.to_parquet(schedule_path, index=False)
    assigned = schedule.loc[season_mask, ["RoadJersey", "HomeJersey"]].astype(str).ne("").all(axis=1).sum()
    print(f"Assigned {assigned} jersey matchups for {year}.")


if __name__ == "__main__":
    main()
