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
    return work[work["_winner_key"] != ""].copy()


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
    for column, rule in columns.items():
        award_names = _award_names_for_rule(all_awards, rule)
        counts = table[table["Award"].isin(award_names)].groupby("_winner_key").size().rename(column)
        pieces.append(counts)
    result = pd.concat([display_names, *pieces], axis=1).fillna(0).reset_index(drop=True)
    count_columns = list(columns)
    for column in count_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0).astype(int)
    if len(count_columns) > 1:
        result["Total"] = result[count_columns].sum(axis=1)
        sort_columns = ["Total", *count_columns, entity_label]
        ascending = [False] * (len(count_columns) + 1) + [True]
    else:
        sort_columns = [count_columns[0], entity_label]
        ascending = [False, True]
    result = result[result[count_columns].sum(axis=1) > 0].sort_values(sort_columns, ascending=ascending).reset_index(drop=True)
    result.insert(0, "Rank", range(1, len(result) + 1))
    return result


def build_award_count_tables(player_awards: pd.DataFrame, team_awards: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    """Return ordered player and franchise award leaderboard definitions."""
    player_rows = _valid_award_rows(player_awards)
    team_rows = _valid_award_rows(team_awards)
    player_tables = [
        {"title": title, "subtitle": subtitle, "table": _leaderboard(player_rows, columns, "Player")}
        for title, subtitle, columns in PLAYER_AWARD_SPECS
    ]
    team_tables = [
        {"title": title, "subtitle": subtitle, "table": _leaderboard(team_rows, columns, "Team")}
        for title, subtitle, columns in TEAM_AWARD_SPECS
    ]
    return player_tables, team_tables
