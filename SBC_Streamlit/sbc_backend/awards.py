"""Pure award-history aggregation for all-time leaderboard views."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd


PLAYER_AWARD_SPECS = [
    ("Rings", "Championship roster appearances.", {"Rings": {"Champion"}}),
    ("MVP", "Most Valuable Player awards.", {"Awards": {"MVP"}}),
    (
        "Series MVP",
        "Conference finals and SBCFBL Finals MVP awards.",
        {"East": {"ECF MVP"}, "West": {"WCF MVP"}, "Finals": {"Finals MVP"}},
    ),
    ("Cup Winner", "SBC Cup-winning roster appearances.", {"Wins": {"Cup Winner"}}),
    ("Cup MVP", "SBC Cup Most Valuable Player awards.", {"Awards": {"Cup MVP"}}),
    ("DPOY", "Defensive Player of the Year awards.", {"Awards": {"DPOY"}}),
    (
        "All-SBC",
        "All-SBC selections by team.",
        {
            "1st": {"All-SBC 1st Team"},
            "2nd": {"All-SBC 2nd Team"},
            "3rd": {"All-SBC 3rd Team"},
        },
    ),
    (
        "All-Defense",
        "All-Defense selections by team.",
        {"1st": {"All-Defense 1st Team"}, "2nd": {"All-Defense 2nd Team"}},
    ),
    (
        "All-Rookie",
        "All-Rookie selections by team.",
        {"1st": {"All-Rookie 1st Team"}, "2nd": {"All-Rookie 2nd Team"}},
    ),
    ("All-Star", "East and West All-Star selections combined.", {"Selections": {"East All-Star", "West All-Star"}}),
    ("ASG MVP", "All-Star Game MVP awards.", {"Awards": {"ASG MVP"}}),
    ("Clutch", "Clutch Player of the Year awards.", {"Awards": {"Clutch"}}),
    ("ROY", "Rookie of the Year awards.", {"Awards": {"ROY"}}),
    ("MIP", "Most Improved Player awards.", {"Awards": {"MIP"}}),
    ("Sixth Man of the Year", "Sixth Man of the Year awards.", {"Awards": {"6MOY"}}),
    ("POM", "East and West Player of the Month awards combined.", {"Awards": "POM"}),
    ("POW", "East and West Player of the Week awards combined.", {"Awards": "POW"}),
    ("ROM", "East and West Rookie of the Month awards combined.", {"Awards": "ROM"}),
]


TEAM_AWARD_SPECS = [
    (
        "Finals Winner",
        "SBCFBL championships.",
        {"Wins": {"Champion"}},
    ),
    (
        "Conference Winner",
        "East and West conference championships combined.",
        {"Wins": {"EC Champion", "WC Champion"}},
    ),
    (
        "Division Winner",
        "All six division championships combined.",
        {
            "Wins": {
                "Atlantic Champion",
                "Central Champion",
                "Northwest Champion",
                "Pacific Champion",
                "Southeast Champion",
                "Southwest Champion",
            }
        },
    ),
    (
        "Cup Winner",
        "SBC Cup championships.",
        {"Wins": {"Cup Winner"}},
    ),
]


def _winner_key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


def _valid_award_rows(table: pd.DataFrame) -> pd.DataFrame:
    required = {"Award", "Winner"}
    if table is None or table.empty or not required.issubset(table.columns):
        return pd.DataFrame(columns=["Award", "Winner", "_winner_key"])
    work = table.copy()
    work["Award"] = work["Award"].fillna("").astype(str).str.strip()
    work["Winner"] = work["Winner"].fillna("").astype(str).str.strip()
    invalid = {"", "-", "not awarded", "none", "nan", "n/a"}
    work = work[~work["Winner"].str.casefold().isin(invalid)].copy()
    work["_winner_key"] = work["Winner"].map(_winner_key)
    work = work[work["_winner_key"] != ""].copy()
    # One player can appear twice in a source column, but a player can only
    # earn the same award once in a season. Cup MVP remains a separate award.
    dedupe_columns = ["Award", "_winner_key"]
    if "Year" in work.columns:
        dedupe_columns.append("Year")
    return work.drop_duplicates(dedupe_columns).copy()


def _award_names_for_rule(all_awards: set[str], rule: set[str] | str) -> set[str]:
    if isinstance(rule, set):
        return rule
    token = str(rule).upper()
    return {award for award in all_awards if re.search(rf"(?:^|\s){re.escape(token)}$", award.upper())}


def _leaderboard(table: pd.DataFrame, columns: dict[str, set[str] | str], entity_label: str) -> pd.DataFrame:
    if table.empty:
        return pd.DataFrame(columns=["Rank", entity_label, *columns])
    all_awards = set(table["Award"].unique())
    display_names = (
        table.groupby("_winner_key")["Winner"]
        .agg(lambda values: values.value_counts().index[0])
        .rename(entity_label)
    )
    pieces = []
    leaderboard_awards = set()
    for column, rule in columns.items():
        award_names = _award_names_for_rule(all_awards, rule)
        leaderboard_awards.update(award_names)
        counts = table[table["Award"].isin(award_names)].groupby("_winner_key").size().rename(column)
        pieces.append(counts)
    result = pd.concat([display_names, *pieces], axis=1).fillna(0)
    count_columns = list(columns)
    for column in count_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0).astype(int)
    if len(count_columns) > 1:
        result["Total"] = result[count_columns].sum(axis=1)
        primary_count = "Total"
    else:
        primary_count = count_columns[0]
    if "Year" in table.columns:
        relevant_rows = table[table["Award"].isin(leaderboard_awards)].copy()
        relevant_rows["_award_year"] = pd.to_numeric(relevant_rows["Year"], errors="coerce")
        latest_wins = relevant_rows.groupby("_winner_key")["_award_year"].max()
        result["_latest_win"] = result.index.to_series().map(latest_wins)
    else:
        result["_latest_win"] = float("-inf")
    result["_latest_win"] = pd.to_numeric(result["_latest_win"], errors="coerce").fillna(float("-inf"))
    result = (
        result[result[count_columns].sum(axis=1) > 0]
        .sort_values([primary_count, "_latest_win", entity_label], ascending=[False, False, True])
        .drop(columns=["_latest_win"])
        .reset_index(drop=True)
    )
    result.insert(0, "Rank", range(1, len(result) + 1))
    return result


def _all_rookie_table(table: pd.DataFrame) -> pd.DataFrame:
    """List selections, with the reigning first team occupying the five-card preview."""
    awards = {
        "All-Rookie 1st Team": "1st",
        "All-Rookie 2nd Team": "2nd",
    }
    work = table[table["Award"].isin(awards)].copy()
    if work.empty:
        return pd.DataFrame(columns=["Rank", "Player", "Team"])
    work["Team"] = work["Award"].map(awards)
    work["_year"] = pd.to_numeric(work.get("Year"), errors="coerce").fillna(0).astype(int)
    work["_team_order"] = work["Team"].map({"1st": 0, "2nd": 1})
    work = work.sort_values(["_year", "_team_order", "Winner"], ascending=[False, True, True])
    work = work.drop_duplicates("_winner_key", keep="first").reset_index(drop=True)
    result = work[["Winner", "Team"]].rename(columns={"Winner": "Player"})
    result.insert(0, "Rank", range(1, len(result) + 1))
    return result


def build_award_count_tables(player_awards: pd.DataFrame, team_awards: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    """Return ordered player and franchise award leaderboard definitions."""
    player_rows = _valid_award_rows(player_awards)
    team_rows = _valid_award_rows(team_awards)
    player_tables = [
        {
            "title": title,
            "subtitle": subtitle,
            "table": _all_rookie_table(player_rows) if title == "All-Rookie" else _leaderboard(player_rows, columns, "Player"),
        }
        for title, subtitle, columns in PLAYER_AWARD_SPECS
    ]
    team_tables = [
        {"title": title, "subtitle": subtitle, "table": _leaderboard(team_rows, columns, "Team")}
        for title, subtitle, columns in TEAM_AWARD_SPECS
    ]
    return player_tables, team_tables
