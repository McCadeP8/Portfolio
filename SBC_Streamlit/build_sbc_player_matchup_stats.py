import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd

from data import team_info


APP_DIR = Path(__file__).resolve().parent
SUM_STATS = ["GP", "MP", "2PTM", "2PTA", "3PTM", "3PTA", "FTM", "FTA", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]


def read_parquet(name):
    for path in [APP_DIR / name, APP_DIR / "data_snapshots" / name, Path(name)]:
        if path.exists():
            return pd.read_parquet(path)
    raise FileNotFoundError(name)


def read_csv(name):
    for path in [APP_DIR / name, Path(name)]:
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame()


def normalize_player_key(value):
    text = str(value or "")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\b(Jr|Sr|II|III|IV|V)\b\.?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[^A-Za-z0-9]+", "", text).lower()
    return text


def resolve_team_key(team):
    value = str(team or "").strip()
    if value in team_info:
        return value
    lowered = value.lower()
    for key, info in team_info.items():
        nickname = str(info.get("nickname", "")).strip()
        full_name = f"{key} {nickname}".strip()
        if lowered in {key.lower(), nickname.lower(), full_name.lower()} or lowered.startswith(f"{key.lower()} "):
            return key
    return value


def season_label_from_year(year):
    year = int(year)
    return f"{year - 1}-{str(year)[-2:]}"


def build_bridge(fantrax_players, boxscores):
    ft = fantrax_players.rename(columns={"name": "fantrax_name"}).dropna(subset=["fantrax_name", "fantraxId"]).copy()
    ft["fantraxId"] = ft["fantraxId"].astype(str)
    ft["_player_key"] = ft["fantrax_name"].apply(normalize_player_key)

    box_players = boxscores[["nba_player_id", "player_name"]].dropna().drop_duplicates().copy()
    box_players["nba_player_id"] = box_players["nba_player_id"].astype(str)
    box_players["_player_key"] = box_players["player_name"].apply(normalize_player_key)
    key_counts = box_players.groupby("_player_key")["nba_player_id"].nunique()
    unique_box_players = box_players[box_players["_player_key"].isin(key_counts[key_counts == 1].index)]

    bridge = ft.merge(unique_box_players, on="_player_key", how="inner")
    bridge = bridge.rename(columns={"nba_player_id": "espn_player_id", "player_name": "espn_name"})
    bridge["match_type"] = "name"
    bridge = bridge[["fantraxId", "fantrax_name", "espn_player_id", "espn_name", "match_type"]]

    overrides = read_csv("player_id_overrides.csv")
    if not overrides.empty:
        overrides = overrides[["fantraxId", "fantrax_name", "espn_player_id", "espn_name"]].dropna(subset=["fantraxId", "espn_player_id"]).copy()
        overrides["fantraxId"] = overrides["fantraxId"].astype(str)
        overrides["espn_player_id"] = overrides["espn_player_id"].astype(str)
        overrides["match_type"] = "override"
        bridge = bridge[~bridge["fantraxId"].isin(overrides["fantraxId"])]
        bridge = pd.concat([bridge, overrides], ignore_index=True)
    return bridge.drop_duplicates("fantraxId").reset_index(drop=True)


def recalc_percentages(frame):
    out = frame.copy()
    fga = out["2PTA"] + out["3PTA"]
    ts_denom = 2 * (fga + 0.44 * out["FTA"])
    out["TS%"] = (out["PTS"] / ts_denom).where(ts_denom > 0, 0)
    out["2PT%"] = (out["2PTM"] / out["2PTA"]).where(out["2PTA"] > 0, 0)
    out["3PT%"] = (out["3PTM"] / out["3PTA"]).where(out["3PTA"] > 0, 0)
    out["FT%"] = (out["FTM"] / out["FTA"]).where(out["FTA"] > 0, 0)
    return out


def build_matchup_stats(seasons=None):
    box = read_parquet("nba_player_game_boxscores_2021_2026.parquet")
    rosters = read_parquet("all_time_rosters_history.parquet")
    schedule = read_parquet("all_time_scores.parquet")
    calendar = read_parquet("period_calendar.parquet")
    fantrax = read_parquet("fantrax_players_snapshot.parquet")

    if seasons:
        seasons = {int(season) for season in seasons}
        box = box[pd.to_numeric(box["sbc_year"], errors="coerce").isin(seasons)].copy()
        rosters = rosters[pd.to_numeric(rosters["Year"], errors="coerce").isin(seasons)].copy()
        schedule = schedule[pd.to_numeric(schedule["Year"], errors="coerce").isin(seasons)].copy()
        calendar = calendar[pd.to_numeric(calendar["Year"], errors="coerce").isin(seasons)].copy()

    bridge = build_bridge(fantrax, box).rename(columns={"fantraxId": "fantrax_id"})
    if bridge.empty:
        return pd.DataFrame()

    active = rosters[rosters["status"].astype(str).str.upper() == "ACTIVE"].copy()
    active = active.rename(columns={"id": "fantrax_id", "period": "Day"})
    active["fantrax_id"] = active["fantrax_id"].astype(str)
    active["_year"] = pd.to_numeric(active["Year"], errors="coerce").astype("Int64")
    active["_day"] = pd.to_numeric(active["Day"], errors="coerce").astype("Int64")
    active["sbc_team"] = active["team_name"].astype(str)
    active["sbc_team_key"] = active["sbc_team"].apply(resolve_team_key)

    calendar = calendar.copy()
    calendar["_year"] = pd.to_numeric(calendar["Year"], errors="coerce").astype("Int64")
    calendar["_day"] = pd.to_numeric(calendar["Day"], errors="coerce").astype("Int64")
    calendar["_period"] = pd.to_numeric(calendar["Period"], errors="coerce").astype("Int64")
    calendar["Date"] = pd.to_datetime(calendar["Date"], errors="coerce").dt.normalize()
    active_dates = active.merge(calendar[["_year", "_day", "_period", "Date"]], on=["_year", "_day"], how="inner")
    active_dates = active_dates.merge(bridge, on="fantrax_id", how="inner")
    active_dates["espn_player_id"] = active_dates["espn_player_id"].astype(str)

    box = box.copy()
    box["Date"] = pd.to_datetime(box["Date"], errors="coerce").dt.normalize()
    box["nba_player_id"] = box["nba_player_id"].astype(str)
    for col in SUM_STATS:
        box[col] = pd.to_numeric(box.get(col, 0), errors="coerce").fillna(0)

    rows = box.merge(
        active_dates[["_year", "_day", "_period", "Date", "fantrax_id", "fantrax_name", "espn_player_id", "sbc_team", "sbc_team_key"]],
        left_on=["sbc_year", "Date", "nba_player_id"],
        right_on=["_year", "Date", "espn_player_id"],
        how="inner",
    )
    if rows.empty:
        return rows

    schedule = schedule.copy()
    schedule["_year"] = pd.to_numeric(schedule["Year"], errors="coerce").astype("Int64")
    schedule["_period"] = pd.to_numeric(schedule["Period"], errors="coerce").astype("Int64")
    sched_a = schedule[["_year", "_period", "Type", "Round", "Game_ID", "TeamA", "TeamB"]].rename(
        columns={"TeamA": "sbc_team_key", "TeamB": "sbc_opponent", "Type": "sbc_matchup_type", "Round": "sbc_round"}
    )
    sched_b = schedule[["_year", "_period", "Type", "Round", "Game_ID", "TeamA", "TeamB"]].rename(
        columns={"TeamB": "sbc_team_key", "TeamA": "sbc_opponent", "Type": "sbc_matchup_type", "Round": "sbc_round"}
    )
    sched_long = pd.concat([sched_a, sched_b], ignore_index=True)
    sched_long["sbc_team_key"] = sched_long["sbc_team_key"].apply(resolve_team_key)
    sched_long["sbc_opponent"] = sched_long["sbc_opponent"].apply(resolve_team_key)
    rows = rows.merge(sched_long, on=["_year", "_period", "sbc_team_key"], how="left")
    rows["sbc_matchup_type"] = rows["sbc_matchup_type"].fillna("Regular Season")
    rows["sbc_round"] = rows["sbc_round"].fillna("")
    rows["sbc_opponent"] = rows["sbc_opponent"].fillna("")

    group_cols = [
        "fantrax_id", "fantrax_name", "espn_player_id", "player_name", "sbc_year", "_period",
        "sbc_team", "sbc_team_key", "sbc_matchup_type", "sbc_round", "sbc_opponent", "Game_ID",
    ]
    agg = rows.groupby(group_cols, dropna=False, as_index=False).agg(
        **{col: (col, "sum") for col in SUM_STATS},
        start_date=("Date", "min"),
        end_date=("Date", "max"),
        nba_game_ids=("nba_game_id", lambda values: ",".join(sorted({str(value) for value in values if pd.notna(value)}))),
    )
    agg = recalc_percentages(agg)
    agg = agg.rename(columns={"_period": "sbc_period"})
    agg["sbc_year"] = pd.to_numeric(agg["sbc_year"], errors="coerce").astype("Int64")
    agg["sbc_period"] = pd.to_numeric(agg["sbc_period"], errors="coerce").astype("Int64")
    agg["season"] = agg["sbc_year"].apply(lambda value: season_label_from_year(value) if pd.notna(value) else "")
    agg["matchups"] = 1
    agg["matchup_label"] = agg.apply(lambda row: f"{row['season']} P{int(row['sbc_period'])}" if pd.notna(row["sbc_period"]) else str(row["season"]), axis=1)
    column_order = [
        "fantrax_id", "fantrax_name", "espn_player_id", "player_name", "sbc_year", "season", "sbc_period",
        "sbc_matchup_type", "sbc_round", "Game_ID", "sbc_team", "sbc_team_key", "sbc_opponent", "matchup_label",
        "start_date", "end_date", "nba_game_ids", "matchups",
        "GP", "MP", "TS%", "2PTM", "2PTA", "2PT%", "3PTM", "3PTA", "3PT%", "FTM", "FTA", "FT%", "PTS",
        "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-",
    ]
    return agg[[col for col in column_order if col in agg.columns]].sort_values(["sbc_year", "sbc_period", "sbc_team_key", "fantrax_name"])


def main():
    parser = argparse.ArgumentParser(description="Build one-row-per-player-per-SBCFBL-matchup stats archive.")
    parser.add_argument("--output", default="sbc_player_matchup_stats.parquet")
    parser.add_argument("--season", type=int, action="append", help="SBC season year to include; repeat for multiple seasons.")
    args = parser.parse_args()

    table = build_matchup_stats(args.season)
    output = APP_DIR / args.output
    table.to_parquet(output, index=False)
    print(f"Wrote {len(table):,} rows to {output}")
    if not table.empty:
        print(f"Seasons: {int(table['sbc_year'].min())}-{int(table['sbc_year'].max())}")


if __name__ == "__main__":
    main()
