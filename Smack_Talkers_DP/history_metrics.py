"""Analysis layer for the Smack Talkers league-history Streamlit app."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILES = {
    "lineups": "yahoo/all_leagues_weekly_lineups_scraped.parquet",
    "lineup_scores": "yahoo/all_leagues_weekly_scores_scraped.parquet",
    "team_map": "yahoo/all_leagues_team_owner_map.parquet",
    "standings": "yahoo/all_leagues_standings.parquet",
    "scores": "yahoo/all_leagues_regular_season_scores.parquet",
    "matchups": "yahoo/all_leagues_regular_season_matchups.parquet",
    "drafts": "smack_talkers_draft_history.parquet",
    "drafts_enriched": "draft_history_with_espn.parquet",
}

PARQUET_COLUMNS = {
    "lineups": [
        "season", "league_id", "team_id", "week", "roster_slot", "roster_group",
        "player_name", "player_key", "fan_points", "actual_position_scraped",
        "is_starter", "owner", "draft_type",
    ],
    "lineup_scores": ["season", "league_id", "team_id", "week", "team_score", "owner", "draft_type"],
    "team_map": [
        "season", "league_id", "draft_type", "yahoo_team_id", "yahoo_team_name",
        "draft_team_name", "owner", "owner_source",
    ],
    "standings": [
        "season", "league_id", "team_id", "rank", "wins", "losses", "ties",
        "points_for", "points_against", "record", "team_name", "made_playoffs",
        "owner", "draft_type", "record_games",
    ],
    "scores": [
        "season", "league_id", "team_id", "week", "team_score", "opponent_id",
        "opponent_score", "result", "owner", "draft_type",
    ],
    "matchups": ["season", "league_id", "week", "team_a_id", "team_b_id", "draft_type"],
    "drafts": ["season", "draft_type", "team_name", "player_name", "position"],
    "drafts_enriched": [
        "season", "draft_type", "team_count", "round", "round_pick", "selection_number",
        "team_name", "amount", "player_name", "position", "espn_overall_rank", "espn_auction_value",
    ],
}

POSITION_ORDER = ["QB", "RB", "WR", "TE", "K", "DST", "Unknown"]
STARTER_SLOTS = {"QB": 1, "RB": 2, "FLEX": 3, "TE": 1, "K": 1, "DST": 1}
STARTER_SLOT_ORDER = [
    "QB1", "RB1", "RB2", "RB TOTAL", "WR1", "WR2", "WR3", "WR TOTAL",
    "TE1", "K1", "DST1", "TOTAL",
]


def fantasy_weeks(season: int) -> int:
    """Yahoo fantasy scoring weeks: 17 through 2020, 18 beginning in 2021."""
    return 17 if int(season) <= 2020 else 18


def starter_slot_rankings(lineups: pd.DataFrame) -> pd.DataFrame:
    """Rank team-season scoring from each actual starting lineup slot.

    RB and W/T starters are ordered by their weekly fantasy points to create
    RB1/RB2 and WR1/WR2/WR3. A tight end used in W/T therefore contributes to
    a WR slot; only the dedicated TE starter contributes to TE1.
    """
    columns = [
        "season", "league_id", "draft_type", "team_id", "owner", "starter_slot",
        "starter_points", "observed_weeks", "slot_rank", "ten_team_rank", "league_teams",
    ]
    required = {
        "season", "league_id", "draft_type", "team_id", "owner", "week",
        "roster_slot", "is_starter", "fan_points",
    }
    if lineups.empty or not required.issubset(lineups.columns):
        return pd.DataFrame(columns=columns)

    keys = ["season", "league_id", "draft_type", "team_id", "owner", "week"]
    work = lineups.loc[lineups["is_starter"]].copy()
    work["fan_points"] = pd.to_numeric(work["fan_points"], errors="coerce").fillna(0.0)
    work["slot_family"] = work["roster_slot"].map(
        {"QB": "QB", "RB": "RB", "W/T": "WR", "TE": "TE", "K": "K", "DEF": "DST"}
    )
    work = work.loc[work["slot_family"].notna()].copy()
    if work.empty:
        return pd.DataFrame(columns=columns)

    work = work.sort_values(
        [*keys, "slot_family", "fan_points"],
        ascending=[True] * (len(keys) + 1) + [False],
        kind="stable",
    )
    work["slot_depth"] = work.groupby([*keys, "slot_family"], sort=False, dropna=False).cumcount().add(1)
    slot_limits = {"QB": 1, "RB": 2, "WR": 3, "TE": 1, "K": 1, "DST": 1}
    work = work.loc[work["slot_depth"].le(work["slot_family"].map(slot_limits))].copy()
    work["starter_slot"] = work["slot_family"] + work["slot_depth"].astype(str)

    season_keys = ["season", "league_id", "draft_type", "team_id", "owner", "starter_slot"]
    result = work.groupby(season_keys, as_index=False, sort=False, dropna=False).agg(
        starter_points=("fan_points", "sum"),
        observed_weeks=("week", "nunique"),
    )
    total_keys = ["season", "league_id", "draft_type", "team_id", "owner"]
    position_totals = (
        work.loc[work["slot_family"].isin(["RB", "WR"])]
        .groupby([*total_keys, "slot_family"], as_index=False, sort=False, dropna=False)
        .agg(starter_points=("fan_points", "sum"), observed_weeks=("week", "nunique"))
        .rename(columns={"slot_family": "starter_slot"})
    )
    position_totals["starter_slot"] = position_totals["starter_slot"] + " TOTAL"
    totals = work.groupby(total_keys, as_index=False, sort=False, dropna=False).agg(
        starter_points=("fan_points", "sum"),
        observed_weeks=("week", "nunique"),
    )
    totals["starter_slot"] = "TOTAL"
    result = pd.concat(
        [result, position_totals[result.columns], totals[result.columns]], ignore_index=True
    )
    league_keys = ["season", "league_id", "starter_slot"]
    result["slot_rank"] = result.groupby(league_keys, sort=False, dropna=False)["starter_points"].rank(
        method="min", ascending=False
    )
    league_sizes = (
        lineups[["season", "league_id", "team_id"]]
        .drop_duplicates()
        .groupby(["season", "league_id"], as_index=False)
        .agg(league_teams=("team_id", "nunique"))
    )
    result = result.merge(league_sizes, on=["season", "league_id"], how="left", validate="many_to_one")
    result["ten_team_rank"] = np.where(
        result["league_teams"].gt(1),
        1.0 + (result["slot_rank"] - 1.0) * 9.0 / (result["league_teams"] - 1.0),
        1.0,
    )
    return result[columns]


def normalize_name(value: object) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = decomposed.encode("ascii", "ignore").decode("ascii")
    tokens = re.findall(r"[a-z0-9]+", ascii_value.casefold())
    if tokens and tokens[-1] in {"jr", "sr", "ii", "iii", "iv", "v"}:
        tokens.pop()
    aliases = {"gabrieldavis": "gabedavis", "jefferywilson": "jeffwilson", "kenwalker": "kennethwalker"}
    key = "".join(tokens)
    return aliases.get(key, key)


def normalize_defense_name(value: object) -> str:
    """Collapse Yahoo nicknames and full draft labels to one NFL defense key."""
    key = normalize_name(value)
    nicknames = {
        "cardinals": "ari", "falcons": "atl", "ravens": "bal", "bills": "buf",
        "panthers": "car", "bears": "chi", "bengals": "cin", "browns": "cle",
        "cowboys": "dal", "broncos": "den", "lions": "det", "packers": "gb",
        "texans": "hou", "colts": "ind", "jaguars": "jax", "chiefs": "kc",
        "raiders": "lv", "chargers": "lac", "rams": "lar", "dolphins": "mia",
        "vikings": "min", "patriots": "ne", "saints": "no", "giants": "nyg",
        "jets": "nyj", "eagles": "phi", "steelers": "pit", "fortyniners": "sf",
        "49ers": "sf", "seahawks": "sea", "buccaneers": "tb", "titans": "ten",
        "commanders": "was", "washingtonfootballteam": "was",
    }
    for nickname, abbreviation in nicknames.items():
        if key == nickname or key.endswith(nickname):
            return f"dst{abbreviation}"
    return f"dst{key}"


def load_history_data(processed_dir: Path) -> dict[str, pd.DataFrame]:
    data = {
        name: pd.read_parquet(processed_dir / relative, columns=PARQUET_COLUMNS[name], engine="pyarrow")
        for name, relative in DATA_FILES.items()
    }
    # Yahoo's API and browser archives serialize identifiers differently. Keep
    # every join key numeric after consolidation so mixed archive eras merge
    # consistently in the app.
    integer_keys = {
        "season", "league_id", "team_id", "week", "yahoo_team_id",
        "team_a_id", "team_b_id", "opponent_id",
    }
    for frame in data.values():
        for column in integer_keys.intersection(frame.columns):
            frame[column] = pd.to_numeric(frame[column], errors="raise").astype("int64")
    numeric_metrics = {
        "fan_points", "team_score", "opponent_score", "points_for",
        "points_against", "wins", "losses", "ties", "rank",
    }
    for frame in data.values():
        for column in numeric_metrics.intersection(frame.columns):
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    inventory_path = processed_dir / "yahoo" / "league_inventory.csv"
    data["inventory"] = pd.read_csv(inventory_path, keep_default_na=False)
    data["owners"] = pd.read_csv(processed_dir.parent / "context" / "Team owners.csv", keep_default_na=False)
    data["lineups"] = annotate_lineups(data["lineups"], data["drafts"], data["team_map"])
    return data


def season_h2h_records(scores: pd.DataFrame, standings: pd.DataFrame) -> pd.DataFrame:
    """Return complete regular-season H2H records by team-season.

    Matchup rows are authoritative when the archive is complete. Some 2024
    schedule pages are missing, so modern seasons fall back to Yahoo's complete
    standings record. The 2020 standings record includes postseason games;
    archived regular-season matchup rows remain authoritative for that era.
    """
    keys = ["season", "league_id", "team_id"]
    standing_columns = [
        *keys, "draft_type", "owner", "record", "record_games",
        "points_for", "points_against",
    ]
    base = standings[standing_columns].drop_duplicates(keys).copy()
    record_parts = base["record"].astype("string").str.extract(
        r"^\s*(\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?\s*$"
    )
    base["standing_wins"] = pd.to_numeric(record_parts[0], errors="coerce")
    base["standing_losses"] = pd.to_numeric(record_parts[1], errors="coerce")
    base["standing_ties"] = pd.to_numeric(record_parts[2], errors="coerce").fillna(0)
    base["standing_games"] = base[["standing_wins", "standing_losses", "standing_ties"]].sum(
        axis=1, min_count=2
    )
    base["standing_games"] = base["standing_games"].fillna(
        pd.to_numeric(base["record_games"], errors="coerce")
    )

    if scores.empty:
        games = pd.DataFrame(columns=[*keys, "score_games", "score_wins", "score_losses", "score_ties", "score_pf", "score_pa"])
    else:
        work = scores.copy()
        result = work["result"].astype("string").str.casefold()
        work["score_win"] = result.eq("win").astype(int)
        work["score_loss"] = result.eq("loss").astype(int)
        work["score_tie"] = result.eq("tie").astype(int)
        games = work.groupby(keys, as_index=False).agg(
            score_games=("week", "size"),
            score_wins=("score_win", "sum"),
            score_losses=("score_loss", "sum"),
            score_ties=("score_tie", "sum"),
            score_pf=("team_score", "sum"),
            score_pa=("opponent_score", "sum"),
        )

    result = base.merge(games, on=keys, how="left", validate="one_to_one")
    use_scores = result["score_games"].notna() & (
        result["season"].le(2020)
        | result["standing_games"].isna()
        | result["score_games"].ge(result["standing_games"])
    )
    for target, score_column, standing_column in [
        ("h2h_games", "score_games", "standing_games"),
        ("h2h_wins", "score_wins", "standing_wins"),
        ("h2h_losses", "score_losses", "standing_losses"),
        ("h2h_ties", "score_ties", "standing_ties"),
        ("h2h_points_for", "score_pf", "points_for"),
        ("h2h_points_against", "score_pa", "points_against"),
    ]:
        result[target] = result[score_column].where(use_scores, result[standing_column])
    result["h2h_win_pct"] = (
        result["h2h_wins"] + 0.5 * result["h2h_ties"]
    ) / result["h2h_games"].replace(0, np.nan)
    result["h2h_record"] = result.apply(
        lambda row: (
            "—" if pd.isna(row.h2h_games)
            else f"{int(row.h2h_wins)}-{int(row.h2h_losses)}-{int(row.h2h_ties)}"
        ),
        axis=1,
    )
    result["h2h_source"] = np.where(use_scores, "matchups", "standings fallback")
    return result[
        [
            *keys, "draft_type", "owner", "h2h_games", "h2h_wins", "h2h_losses",
            "h2h_ties", "h2h_win_pct", "h2h_record", "h2h_points_for",
            "h2h_points_against", "h2h_source",
        ]
    ]


def _mode_or_first(series: pd.Series):
    values = series.dropna().astype(str)
    if values.empty:
        return pd.NA
    mode = values.mode()
    return mode.iloc[0] if not mode.empty else values.iloc[0]


def annotate_lineups(
    lineups: pd.DataFrame,
    drafts: pd.DataFrame,
    team_map: pd.DataFrame,
) -> pd.DataFrame:
    """Infer player position and original-draft provenance for each lineup row."""
    result = lineups.copy()
    draft = drafts.copy()
    draft["player_key"] = draft["player_name"].map(normalize_name)
    draft.loc[draft["position"].isin(["DST", "DEF"]), "player_key"] = draft.loc[
        draft["position"].isin(["DST", "DEF"]), "player_name"
    ].map(normalize_defense_name)
    draft = draft.loc[draft["player_key"].ne("")]

    defense_rows = result["roster_group"].eq("defense")
    result.loc[defense_rows, "player_key"] = result.loc[defense_rows, "player_name"].map(normalize_defense_name)

    team_identity = team_map[["season", "draft_type", "yahoo_team_id", "draft_team_name"]].drop_duplicates().rename(
        columns={"yahoo_team_id": "team_id"}
    )
    result = result.merge(team_identity, on=["season", "draft_type", "team_id"], how="left", validate="many_to_one")
    # Week 1 is the temporary draft-origin baseline for every historical league.
    # This intentionally carries no selection-order information.
    week_one = result.loc[result["week"].eq(1) & result["player_key"].ne("")]
    drafted_any = pd.MultiIndex.from_frame(week_one[["season", "league_id", "player_key"]].drop_duplicates())
    drafted_home = pd.MultiIndex.from_frame(
        week_one[["season", "league_id", "team_id", "player_key"]].drop_duplicates()
    )
    current_any = pd.MultiIndex.from_frame(result[["season", "league_id", "player_key"]])
    current_home = pd.MultiIndex.from_frame(result[["season", "league_id", "team_id", "player_key"]])
    result["drafted_in_league"] = current_any.isin(drafted_any)
    result["drafted_by_owner"] = current_home.isin(drafted_home)

    draft_positions = (
        draft.groupby(["season", "player_key"], as_index=False)["position"]
        .agg(_mode_or_first)
        .rename(columns={"position": "draft_position"})
    )
    observed = result.loc[result["roster_slot"].isin(["QB", "RB", "TE", "K", "DEF"]), ["season", "player_key", "roster_slot"]].copy()
    observed["observed_position"] = observed["roster_slot"].replace({"DEF": "DST"})
    observed = observed.groupby(["season", "player_key"], as_index=False)["observed_position"].agg(_mode_or_first)
    result = result.merge(draft_positions, on=["season", "player_key"], how="left")
    result = result.merge(observed, on=["season", "player_key"], how="left")

    scraped_position = (
        result["actual_position_scraped"]
        if "actual_position_scraped" in result.columns
        else pd.Series(pd.NA, index=result.index, dtype="object")
    )
    result["actual_position"] = result["draft_position"].fillna(result["observed_position"]).fillna(scraped_position)
    result.loc[result["roster_group"].eq("kicker"), "actual_position"] = "K"
    result.loc[result["roster_group"].eq("defense"), "actual_position"] = "DST"
    result.loc[result["actual_position"].isna() & result["roster_slot"].eq("QB"), "actual_position"] = "QB"
    result.loc[result["actual_position"].isna() & result["roster_slot"].eq("RB"), "actual_position"] = "RB"
    result.loc[result["actual_position"].isna() & result["roster_slot"].eq("TE"), "actual_position"] = "TE"
    # W/T is a lineup slot, never a player position. Players observed in the
    # dedicated TE slot or draft data are already TE; unresolved W/T players
    # default to WR rather than leaking a hybrid label into app analytics.
    result.loc[result["actual_position"].isna() & result["roster_slot"].eq("W/T"), "actual_position"] = "WR"
    result["actual_position"] = result["actual_position"].replace({"WR/TE": "WR", "W/T": "WR"})
    result["actual_position"] = result["actual_position"].fillna("Unknown")
    result["position_group"] = result["actual_position"].replace({"DEF": "DST"})
    result.loc[~result["position_group"].isin(POSITION_ORDER), "position_group"] = "Unknown"
    result["lineup_role"] = np.where(result["is_starter"], "Starter", np.where(result["roster_slot"].eq("IR"), "IR", "Bench"))
    result["player_origin"] = np.select(
        [result["drafted_by_owner"], result["drafted_in_league"]],
        ["Drafted by current owner", "Drafted by another owner"],
        default="Undrafted / unmatched",
    )
    return result


def _take_top(frame: pd.DataFrame, count: int) -> tuple[float, list[int]]:
    if count <= 0 or frame.empty:
        return 0.0, []
    chosen = frame.nlargest(count, "fan_points")
    return float(chosen["fan_points"].fillna(0).sum()), chosen.index.tolist()


def optimal_lineup_score(roster: pd.DataFrame) -> float:
    """Return the best legal 1QB/2RB/1TE/3W-T/1K/1DST score, excluding IR."""
    eligible = roster.loc[~roster["roster_slot"].eq("IR")].copy()
    eligible["fan_points"] = pd.to_numeric(eligible["fan_points"], errors="coerce").fillna(0.0)
    total = 0.0
    used: list[int] = []
    for position, count in (("QB", 1), ("RB", 2), ("K", 1), ("DST", 1)):
        score, indices = _take_top(eligible.loc[eligible["actual_position"].eq(position)], count)
        total += score
        used.extend(indices)

    receivers = eligible.loc[eligible["actual_position"].isin(["WR", "TE"])]
    tight_ends = receivers.loc[receivers["actual_position"].eq("TE")]
    if tight_ends.empty:
        # A rare unresolved waiver player can still be recognized from the dedicated TE slot.
        tight_ends = receivers.loc[receivers["roster_slot"].eq("TE")]
    best_receiver_total = -np.inf
    for te_index in tight_ends.index:
        flex = receivers.drop(index=te_index)
        candidate = float(eligible.at[te_index, "fan_points"]) + float(flex.nlargest(3, "fan_points")["fan_points"].sum())
        best_receiver_total = max(best_receiver_total, candidate)
    if not np.isfinite(best_receiver_total):
        best_receiver_total = float(receivers.nlargest(4, "fan_points")["fan_points"].sum())
    total += best_receiver_total
    return round(total, 2)


def lineup_week_metrics(lineups: pd.DataFrame) -> pd.DataFrame:
    """Compute start/sit results for every team-week with grouped vector operations."""
    if lineups.empty:
        return pd.DataFrame()
    keys = ["season", "league_id", "draft_type", "team_id", "owner", "week"]
    work = lineups.copy()
    work["fan_points"] = pd.to_numeric(work["fan_points"], errors="coerce").fillna(0.0)
    work["actual_component"] = work["fan_points"].where(work["is_starter"], 0.0)
    work["bench_component"] = work["fan_points"].where(work["lineup_role"].eq("Bench"), 0.0)
    work["ir_component"] = work["fan_points"].where(work["lineup_role"].eq("IR"), 0.0)
    work["league_drafted_starter"] = work["drafted_in_league"].astype(float).where(work["is_starter"])
    work["homegrown_starter"] = work["drafted_by_owner"].astype(float).where(work["is_starter"])
    metrics = work.groupby(keys, as_index=False, dropna=False, sort=False).agg(
        actual_points=("actual_component", "sum"),
        bench_points=("bench_component", "sum"),
        ir_points=("ir_component", "sum"),
        league_drafted_starter_share=("league_drafted_starter", "mean"),
        homegrown_starter_share=("homegrown_starter", "mean"),
    )

    eligible = work.loc[~work["roster_slot"].eq("IR")].copy()
    base_choices = []
    for position, count in (("QB", 1), ("RB", 2), ("K", 1), ("DST", 1)):
        candidates = eligible.loc[eligible["actual_position"].eq(position)].sort_values(
            [*keys, "fan_points"], ascending=[True] * len(keys) + [False], kind="stable"
        )
        rank = candidates.groupby(keys, dropna=False, sort=False).cumcount()
        base_choices.append(candidates.loc[rank.lt(count), [*keys, "fan_points"]])
    base_selected = pd.concat(base_choices, ignore_index=True) if base_choices else pd.DataFrame(columns=[*keys, "fan_points"])
    base_scores = base_selected.groupby(keys, as_index=False, dropna=False, sort=False)["fan_points"].sum().rename(
        columns={"fan_points": "base_optimal_points"}
    )

    receivers = eligible.loc[eligible["actual_position"].isin(["WR", "TE"])].copy()
    if receivers.empty:
        receiver_scores = metrics[keys].assign(receiver_optimal_points=0.0)
    else:
        actual_te = receivers["actual_position"].eq("TE")
        group_has_actual_te = actual_te.groupby(
            [receivers[key] for key in keys], dropna=False, sort=False
        ).transform("any")
        receivers["te_eligible"] = actual_te | (~group_has_actual_te & receivers["roster_slot"].eq("TE"))
        receivers = receivers.sort_values(
            [*keys, "fan_points"], ascending=[True] * len(keys) + [False], kind="stable"
        )
        receivers["receiver_rank"] = receivers.groupby(keys, dropna=False, sort=False).cumcount()

        top_four = receivers.loc[receivers["receiver_rank"].lt(4)]
        top_three = receivers.loc[receivers["receiver_rank"].lt(3)]
        receiver_scores = metrics[keys].copy()
        receiver_scores = receiver_scores.merge(
            top_four.groupby(keys, as_index=False, dropna=False)["fan_points"].sum().rename(columns={"fan_points": "top4"}),
            on=keys,
            how="left",
        )
        receiver_scores = receiver_scores.merge(
            top_three.groupby(keys, as_index=False, dropna=False)["fan_points"].sum().rename(columns={"fan_points": "top3"}),
            on=keys,
            how="left",
        )
        receiver_scores = receiver_scores.merge(
            receivers.groupby(keys, as_index=False, dropna=False)["te_eligible"].any().rename(columns={"te_eligible": "has_te"}),
            on=keys,
            how="left",
        )
        receiver_scores = receiver_scores.merge(
            top_four.groupby(keys, as_index=False, dropna=False)["te_eligible"].any().rename(columns={"te_eligible": "top4_has_te"}),
            on=keys,
            how="left",
        )
        best_te = receivers.loc[receivers["te_eligible"]].drop_duplicates(keys, keep="first")
        receiver_scores = receiver_scores.merge(
            best_te[[*keys, "fan_points"]].rename(columns={"fan_points": "best_te"}),
            on=keys,
            how="left",
        )
        receiver_scores[["top4", "top3", "best_te"]] = receiver_scores[["top4", "top3", "best_te"]].fillna(0.0)
        receiver_scores[["has_te", "top4_has_te"]] = receiver_scores[["has_te", "top4_has_te"]].fillna(False)
        receiver_scores["receiver_optimal_points"] = np.where(
            ~receiver_scores["has_te"] | receiver_scores["top4_has_te"],
            receiver_scores["top4"],
            receiver_scores["top3"] + receiver_scores["best_te"],
        )
        receiver_scores = receiver_scores[[*keys, "receiver_optimal_points"]]

    metrics = metrics.merge(base_scores, on=keys, how="left").merge(receiver_scores, on=keys, how="left")
    metrics[["base_optimal_points", "receiver_optimal_points"]] = metrics[
        ["base_optimal_points", "receiver_optimal_points"]
    ].fillna(0.0)
    calculated_optimal = metrics["base_optimal_points"] + metrics["receiver_optimal_points"]
    metrics["optimal_points"] = np.maximum(metrics["actual_points"], calculated_optimal).round(2)
    metrics["actual_points"] = metrics["actual_points"].round(2)
    metrics["bench_points"] = metrics["bench_points"].round(2)
    metrics["ir_points"] = metrics["ir_points"].round(2)
    metrics["points_left"] = (metrics["optimal_points"] - metrics["actual_points"]).round(2)
    metrics["lineup_efficiency"] = metrics["actual_points"].div(metrics["optimal_points"].where(metrics["optimal_points"].gt(0)))
    return metrics.drop(columns=["base_optimal_points", "receiver_optimal_points"])


def owner_lineup_summary(week_metrics: pd.DataFrame) -> pd.DataFrame:
    if week_metrics.empty:
        return pd.DataFrame()
    summary = week_metrics.groupby("owner", as_index=False).agg(
        weeks_observed=("week", "size"),
        actual_points=("actual_points", "sum"),
        optimal_points=("optimal_points", "sum"),
        bench_points=("bench_points", "sum"),
        points_left=("points_left", "sum"),
        median_weekly_regret=("points_left", "median"),
        homegrown_starter_share=("homegrown_starter_share", "mean"),
        league_drafted_starter_share=("league_drafted_starter_share", "mean"),
    )
    summary["lineup_efficiency"] = summary["actual_points"] / summary["optimal_points"]
    return summary.sort_values(["lineup_efficiency", "actual_points"], ascending=[False, False])


def roster_decay(lineups: pd.DataFrame, include_draft_baseline: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Measure how many originally drafted players remain anywhere on each weekly roster."""
    if lineups.empty:
        return pd.DataFrame(), pd.DataFrame()
    keys = ["season", "league_id", "draft_type", "team_id", "owner", "week"]
    roster = lineups.copy()
    roster["roster_identity"] = roster["player_key"].where(roster["player_key"].ne(""), roster["player_name"])
    roster = roster.drop_duplicates([*keys, "roster_identity"])
    weekly = roster.groupby(keys, as_index=False).agg(
        rostered_players=("roster_identity", "size"),
        homegrown_rostered=("drafted_by_owner", "sum"),
        league_drafted_rostered=("drafted_in_league", "sum"),
    )
    weekly["homegrown_share"] = weekly["homegrown_rostered"] / weekly["rostered_players"]
    weekly["league_drafted_share"] = weekly["league_drafted_rostered"] / weekly["rostered_players"]

    if include_draft_baseline:
        baseline_keys = ["season", "league_id", "draft_type", "team_id", "owner"]
        baseline = weekly.loc[weekly["week"].eq(1), [*baseline_keys, "rostered_players"]].copy()
        baseline["week"] = 0
        baseline["homegrown_rostered"] = baseline["rostered_players"]
        baseline["league_drafted_rostered"] = baseline["rostered_players"]
        baseline["homegrown_share"] = 1.0
        baseline["league_drafted_share"] = 1.0
        weekly = pd.concat([baseline, weekly], ignore_index=True).sort_values([*baseline_keys, "week"])

    rows = []
    group_keys = ["season", "league_id", "draft_type", "team_id", "owner"]
    for key, owner_weeks in weekly.groupby(group_keys, dropna=False):
        owner_weeks = owner_weeks.sort_values("week")
        first, last = owner_weeks.iloc[0], owner_weeks.iloc[-1]
        captured_weeks = int(owner_weeks["week"].gt(0).sum())
        rows.append(
            {
                **dict(zip(group_keys, key)),
                "weeks_observed": captured_weeks,
                "first_week": "Draft" if int(first["week"]) == 0 else int(first["week"]),
                "latest_week": int(last["week"]),
                "homegrown_first": int(first["homegrown_rostered"]),
                "homegrown_latest": int(last["homegrown_rostered"]),
                "players_replaced": int(first["homegrown_rostered"] - last["homegrown_rostered"]),
                "latest_homegrown_share": float(last["homegrown_share"]),
                "latest_league_drafted": int(last["league_drafted_rostered"]),
                "coverage_note": (
                    f"Complete · {fantasy_weeks(key[0])} weeks"
                    if captured_weeks == fantasy_weeks(key[0])
                    else f"Partial · {captured_weeks}/{fantasy_weeks(key[0])} weeks"
                ),
            }
        )
    summary = pd.DataFrame(rows).sort_values(["players_replaced", "owner"], ascending=[False, True])
    return weekly, summary


def prepare_draft_board(drafts: pd.DataFrame, owners: pd.DataFrame) -> pd.DataFrame:
    """Attach owners, positional draft roles, and season-specific league benchmarks."""
    board = drafts.copy()
    owner_map = owners.rename(columns={"Year": "season", "Draft Type": "draft_type", "Team": "team_name"}).copy()
    owner_map["draft_type"] = owner_map["draft_type"].astype(str).str.strip().str.casefold()
    owner_map["team_name"] = owner_map["team_name"].astype(str).str.strip()
    owner_map["Owner"] = owner_map["Owner"].astype(str).str.strip()
    board["draft_type"] = board["draft_type"].astype(str).str.strip().str.casefold()
    board["team_name"] = board["team_name"].astype(str).str.strip()
    board = board.merge(
        owner_map[["season", "draft_type", "team_name", "Owner"]].rename(columns={"Owner": "owner"}),
        on=["season", "draft_type", "team_name"],
        how="left",
        validate="many_to_one",
    )
    board["player_key"] = board["player_name"].map(normalize_name)
    board["position"] = board["position"].replace({"PK": "K", "DEF": "DST"})
    board.loc[board["position"].eq("DST"), "player_key"] = board.loc[
        board["position"].eq("DST"), "player_name"
    ].map(normalize_defense_name)
    board["position_group"] = board["position"].where(board["position"].isin(POSITION_ORDER), "Unknown")

    board = board.reset_index(drop=True)
    group_keys = ["season", "draft_type", "team_name"]
    board["_priority"] = np.where(board["draft_type"].eq("auction"), -board["amount"], board["selection_number"])
    priority = board.sort_values([*group_keys, "_priority", "selection_number"], kind="stable")
    board["role"] = pd.NA
    board["position_slot"] = pd.NA
    receivers = priority.loc[priority["position"].isin(["WR", "TE"])].copy()
    receivers["_te_number"] = receivers["position"].eq("TE").groupby(
        [receivers[key] for key in group_keys], dropna=False, sort=False
    ).cumsum()
    dedicated_te = receivers["position"].eq("TE") & receivers["_te_number"].eq(1)
    board.loc[receivers.index[dedicated_te], "role"] = "TE1"
    board.loc[receivers.index[dedicated_te], "position_slot"] = 1
    flex_receivers = receivers.loc[~dedicated_te].copy()
    flex_slots = flex_receivers.groupby(group_keys, dropna=False, sort=False).cumcount().add(1)
    board.loc[flex_receivers.index, "role"] = "WR" + flex_slots.astype(str)
    board.loc[flex_receivers.index, "position_slot"] = flex_slots.to_numpy()

    for position in ["QB", "RB", "K", "DST"]:
        position_rows = priority.loc[priority["position"].eq(position)]
        slots = position_rows.groupby(group_keys, dropna=False, sort=False).cumcount().add(1)
        board.loc[position_rows.index, "role"] = position + slots.astype(str)
        board.loc[position_rows.index, "position_slot"] = slots.to_numpy()

    board["position_slot"] = pd.to_numeric(board["position_slot"], errors="coerce").astype("Int64")
    league_priority = board.sort_values(
        ["season", "draft_type", "_priority", "selection_number"], kind="stable"
    )
    capital_rank = league_priority.groupby(["season", "draft_type"], dropna=False, sort=False).cumcount().add(1)
    board["capital_rank"] = pd.NA
    board.loc[league_priority.index, "capital_rank"] = capital_rank.to_numpy()
    board["capital_rank"] = pd.to_numeric(board["capital_rank"], errors="coerce")
    board["round_equivalent"] = (board["capital_rank"] - 1) / board["team_count"] + 1
    board["league_round_equivalent"] = board.groupby(["season", "draft_type", "role"])["round_equivalent"].transform("mean")
    board["combined_aggression"] = board["league_round_equivalent"] - board["round_equivalent"]
    board["role_value"] = np.where(board["draft_type"].eq("snake"), board["round"], board["amount"])
    board["league_role_value"] = board.groupby(["season", "draft_type", "role"])["role_value"].transform("mean")
    board["aggression_vs_league"] = np.where(
        board["draft_type"].eq("snake"),
        board["league_role_value"] - board["role_value"],
        board["role_value"] - board["league_role_value"],
    )
    board["espn_market_gap"] = np.where(
        board["draft_type"].eq("snake"),
        board["espn_overall_rank"] - board["selection_number"],
        board["amount"] - board["espn_auction_value"],
    )
    if board["owner"].isna().any():
        missing = board.loc[board["owner"].isna(), ["season", "draft_type", "team_name"]].drop_duplicates()
        raise ValueError(f"Draft teams missing owner mapping:\n{missing}")
    return board.drop(columns="_priority").sort_values(["season", "draft_type", "selection_number"]).reset_index(drop=True)


def draft_role_summary(board: pd.DataFrame, draft_type: str) -> pd.DataFrame:
    selected = board.loc[board["draft_type"].eq(draft_type)].copy()
    if selected.empty:
        return pd.DataFrame()
    summary = selected.groupby(["owner", "role"], as_index=False).agg(
        drafts_observed=("season", "nunique"),
        owner_average=("role_value", "mean"),
        league_average=("league_role_value", "mean"),
        aggression_vs_league=("aggression_vs_league", "mean"),
    )
    return summary


def combined_draft_role_summary(board: pd.DataFrame) -> pd.DataFrame:
    """Compare snake and auction roster roles on one fractional-round scale."""
    if board.empty:
        return pd.DataFrame()
    return board.groupby(["owner", "role"], as_index=False).agg(
        drafts_observed=("season", "size"),
        owner_average=("round_equivalent", "mean"),
        league_average=("league_round_equivalent", "mean"),
        aggression_vs_league=("combined_aggression", "mean"),
    )


def draft_strategy_team_seasons(board: pd.DataFrame) -> pd.DataFrame:
    """Create one interpretable strategy record for every owner and draft."""
    rows = []
    keys = ["season", "draft_type", "team_name", "owner", "team_count"]
    for key, draft in board.groupby(keys, dropna=False):
        draft = draft.sort_values("selection_number")
        position_spend = draft.groupby("position")["amount"].sum()
        total_spend = float(draft["amount"].sum())
        top_three = float(draft.nlargest(3, "amount")["amount"].sum()) if total_spend else 0.0

        def first_round(position: str):
            values = draft.loc[draft["position"].eq(position), "round"]
            return float(values.min()) if len(values) else np.nan

        def nth_capital_round(positions: list[str], number: int):
            values = draft.loc[draft["position"].isin(positions)].sort_values("round_equivalent")["round_equivalent"]
            return float(values.iloc[number - 1]) if len(values) >= number else np.nan

        def position_amount(position: str) -> float:
            return float(position_spend.get(position, 0.0))

        row = {
            **dict(zip(keys, key)),
            "total_spend": total_spend,
            "max_bid": float(draft["amount"].max()),
            "top3_spend_share": top_three / total_spend if total_spend else np.nan,
            "first_qb_round": first_round("QB"),
            "first_rb_round": first_round("RB"),
            "first_wr_round": first_round("WR"),
            "first_te_round": first_round("TE"),
            "first_qb_capital": nth_capital_round(["QB"], 1),
            "first_rb_capital": nth_capital_round(["RB"], 1),
            "second_rb_capital": nth_capital_round(["RB"], 2),
            "first_wrte_capital": nth_capital_round(["WR", "TE"], 1),
            "third_wrte_capital": nth_capital_round(["WR", "TE"], 3),
            "first_te_capital": nth_capital_round(["TE"], 1),
            "second_te_capital": nth_capital_round(["TE"], 2),
            "first_k_capital": nth_capital_round(["K"], 1),
            "first_dst_capital": nth_capital_round(["DST"], 1),
            "early_qb_count": int(draft.loc[draft["round"].le(5), "position"].eq("QB").sum()),
            "early_rb_count": int(draft.loc[draft["round"].le(5), "position"].eq("RB").sum()),
            "early_wr_count": int(draft.loc[draft["round"].le(5), "position"].eq("WR").sum()),
            "qb_spend": position_amount("QB"),
            "rb_spend": position_amount("RB"),
            "wr_spend": position_amount("WR"),
            "te_spend": position_amount("TE"),
            "k_spend": position_amount("K"),
            "dst_spend": position_amount("DST"),
            "average_espn_market_gap": float(draft["espn_market_gap"].mean()),
        }
        for position in ["QB", "RB", "WR", "TE", "K", "DST"]:
            spend = row[f"{position.casefold()}_spend"]
            row[f"{position.casefold()}_spend_share"] = spend / total_spend if total_spend else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def attach_draft_outcomes(
    strategy: pd.DataFrame,
    standings: pd.DataFrame,
    scores: pd.DataFrame,
    lineup_weeks: pd.DataFrame,
    lineups: pd.DataFrame,
    team_map: pd.DataFrame,
) -> pd.DataFrame:
    """Join draft construction to season results without inventing missing seasons."""
    result = strategy.copy()
    identity = team_map[["season", "draft_type", "draft_team_name", "yahoo_team_id"]].drop_duplicates().rename(
        columns={"draft_team_name": "team_name", "yahoo_team_id": "team_id"}
    )
    result = result.merge(identity, on=["season", "draft_type", "team_name"], how="left", validate="one_to_one")
    outcome = standings.copy()
    outcome["finish_rank"] = pd.to_numeric(outcome["rank"], errors="coerce")
    outcome["points_per_game"] = outcome["points_for"] / outcome["record_games"].replace(0, np.nan)
    outcome["win_pct"] = outcome["record"].map(
        lambda value: (int(str(value).split("-")[0]) + 0.5 * int(str(value).split("-")[2]))
        / max(sum(map(int, str(value).split("-"))), 1)
    )
    outcome = outcome[["season", "draft_type", "team_id", "points_for", "points_per_game", "finish_rank", "win_pct"]]
    # Future drafts can exist before Yahoo team IDs are available. Their missing
    # IDs intentionally repeat, while every populated outcome key remains unique.
    result = result.merge(outcome, on=["season", "draft_type", "team_id"], how="left", validate="many_to_one")

    if not scores.empty:
        all_play_weekly, _ = all_play_summary(scores)
        all_play = all_play_weekly.groupby(["season", "draft_type", "team_id"], as_index=False).agg(
            all_play_win_pct=("all_play_win_value", "mean"),
            average_net_points=("net_points_vs_weekly_median", "mean"),
            median_net_points=("net_points_vs_weekly_median", "median"),
            combined_win_pct=("combined_win_value", "mean"),
        )
        result = result.merge(all_play, on=["season", "draft_type", "team_id"], how="left")
        result["schedule_luck"] = result["win_pct"] - result["all_play_win_pct"]

    if not lineup_weeks.empty:
        execution = lineup_weeks.groupby(["season", "draft_type", "team_id"], as_index=False).agg(
            observed_lineup_weeks=("week", "size"), actual_points=("actual_points", "sum"), optimal_points=("optimal_points", "sum")
        )
        execution["lineup_efficiency"] = execution["actual_points"] / execution["optimal_points"]
        result = result.merge(execution, on=["season", "draft_type", "team_id"], how="left")

    if not lineups.empty:
        _, decay = roster_decay(lineups, include_draft_baseline=True)
        decay = decay[["season", "draft_type", "team_id", "weeks_observed", "homegrown_latest", "players_replaced", "latest_homegrown_share"]]
        result = result.merge(decay, on=["season", "draft_type", "team_id"], how="left")
    result["outcome_available"] = result["points_for"].notna()
    return result


def drafted_player_outcomes(board: pd.DataFrame, lineups: pd.DataFrame, team_map: pd.DataFrame) -> pd.DataFrame:
    """Attach observed roster use and starter contribution to each drafted player."""
    if lineups.empty:
        result = board.copy()
        result["observed_team_weeks"] = np.nan
        return result
    identity = team_map[["season", "draft_type", "draft_team_name", "yahoo_team_id"]].drop_duplicates().rename(
        columns={"draft_team_name": "team_name", "yahoo_team_id": "team_id"}
    )
    result = board.merge(identity, on=["season", "draft_type", "team_name"], how="left", validate="many_to_one")
    usage = lineups.copy()
    usage["starter_points"] = np.where(usage["is_starter"], usage["fan_points"].fillna(0), 0.0)
    usage["started"] = usage["is_starter"].astype(int)
    player_usage = usage.groupby(["season", "draft_type", "team_id", "player_key"], as_index=False).agg(
        roster_weeks=("week", "nunique"),
        latest_roster_week=("week", "max"),
        starts=("started", "sum"),
        starter_points=("starter_points", "sum"),
    )
    team_weeks = usage.groupby(["season", "draft_type", "team_id"], as_index=False)["week"].nunique().rename(
        columns={"week": "observed_team_weeks"}
    )
    result = result.merge(player_usage, on=["season", "draft_type", "team_id", "player_key"], how="left")
    result = result.merge(team_weeks, on=["season", "draft_type", "team_id"], how="left")
    result["starter_points_per_observed_week"] = result["starter_points"].fillna(0) / result["observed_team_weeks"]
    result["start_rate_when_rostered"] = result["starts"] / result["roster_weeks"]
    return result


def all_play_summary(scores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for _, week in scores.groupby(["season", "league_id", "week"]):
        values = week["team_score"].to_numpy(dtype=float)
        weekly_median = float(np.median(values))
        for row in week.itertuples(index=False):
            wins = float(np.sum(values < row.team_score))
            ties = float(np.sum(values == row.team_score) - 1)
            denominator = max(len(values) - 1, 1)
            result_value = getattr(row, "result", None)
            if pd.isna(result_value):
                actual_win_value = np.nan
            elif result_value == "win":
                actual_win_value = 1.0
            elif result_value == "tie":
                actual_win_value = 0.5
            elif result_value == "loss":
                actual_win_value = 0.0
            else:
                actual_win_value = np.nan
            above_median_value = 1.0 if row.team_score > weekly_median else 0.5 if row.team_score == weekly_median else 0.0
            rows.append(
                {
                    "season": row.season,
                    "league_id": row.league_id,
                    "draft_type": row.draft_type,
                    "team_id": row.team_id,
                    "owner": row.owner,
                    "week": row.week,
                    "team_score": row.team_score,
                    "weekly_median": weekly_median,
                    "net_points_vs_weekly_median": row.team_score - weekly_median,
                    "above_median_value": above_median_value,
                    "actual_win_value": actual_win_value,
                    "all_play_win_value": (wins + 0.5 * ties) / denominator,
                    "combined_win_value": (actual_win_value + above_median_value) / 2 if not pd.isna(actual_win_value) else np.nan,
                }
            )
    weekly = pd.DataFrame(rows)
    summary = weekly.groupby("owner", as_index=False).agg(
        weeks=("week", "size"),
        points=("team_score", "sum"),
        average_points=("team_score", "mean"),
        median_points=("team_score", "median"),
        average_net_points=("net_points_vs_weekly_median", "mean"),
        median_net_points=("net_points_vs_weekly_median", "median"),
        score_std=("team_score", "std"),
        matchups=("actual_win_value", "count"),
        actual_win_pct=("actual_win_value", "mean"),
        all_play_win_pct=("all_play_win_value", "mean"),
        combined_win_pct=("combined_win_value", "mean"),
    )
    summary["schedule_luck"] = summary["actual_win_pct"] - summary["all_play_win_pct"]
    return weekly, summary


def perfect_start_counterfactual(week_metrics: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    if week_metrics.empty:
        return pd.DataFrame()
    joined = week_metrics.merge(
        scores[["season", "league_id", "team_id", "week", "opponent_score", "result"]],
        on=["season", "league_id", "team_id", "week"],
        how="inner",
    )
    joined["actual_win_value"] = np.select(
        [joined["result"].eq("win"), joined["result"].eq("tie")], [1.0, 0.5], default=0.0
    )
    joined["perfect_win_value"] = np.select(
        [joined["optimal_points"].gt(joined["opponent_score"]), joined["optimal_points"].eq(joined["opponent_score"])],
        [1.0, 0.5],
        default=0.0,
    )
    summary = joined.groupby("owner", as_index=False).agg(
        comparable_weeks=("week", "size"),
        actual_wins=("actual_win_value", "sum"),
        perfect_start_wins=("perfect_win_value", "sum"),
        points_left=("points_left", "sum"),
    )
    summary["wins_added"] = summary["perfect_start_wins"] - summary["actual_wins"]
    return summary.sort_values(["wins_added", "points_left"], ascending=False)


def coverage_summary(lineups: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    score_pages = scores.groupby(["season", "league_id", "draft_type"], as_index=False).agg(
        score_team_weeks=("week", "size"), teams=("team_id", "nunique"), score_weeks=("week", "nunique")
    )
    lineup_pages = lineups.groupby(["season", "league_id", "draft_type"], as_index=False).agg(
        lineup_team_weeks=("week", lambda x: x.groupby([lineups.loc[x.index, "team_id"], x]).ngroups),
        lineup_teams=("team_id", "nunique"),
        lineup_weeks=("week", "nunique"),
    )
    # Detailed-lineup coverage must be based on teams represented in the lineup
    # archive, not the independently collected H2H schedule. Legacy leagues can
    # have complete rosters with partial or no matchup rows.
    result = lineup_pages.merge(score_pages, on=["season", "league_id", "draft_type"], how="left")
    result["score_team_weeks"] = result["score_team_weeks"].fillna(0).astype(int)
    result["teams"] = result["teams"].fillna(0).astype(int)
    result["score_weeks"] = result["score_weeks"].fillna(0).astype(int)
    result["expected_lineup_pages"] = result["lineup_teams"] * result["season"].map(fantasy_weeks)
    result["lineup_coverage"] = result["lineup_team_weeks"] / result["expected_lineup_pages"]
    return result
