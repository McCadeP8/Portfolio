from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd


SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}
EXCEPTION_COLUMNS = [
    "projection_player_name", "normalized_name", "suggested_player_name",
    "suggested_fantrax_player_id", "similarity", "ambiguous", "review_recommended",
]


def normalize_name(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.replace("'", "").replace("’", "")
    parts = re.findall(r"[a-z0-9]+", text.lower())
    return " ".join(part for part in parts if part not in SUFFIXES)


def match_players(
    fantrax_players: pd.DataFrame,
    projections: pd.DataFrame,
    aliases: pd.DataFrame | None = None,
    suggestion_threshold: float = 0.82,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ft = fantrax_players.copy()
    pr = projections.copy()
    alias_map: dict[str, str] = {}
    if aliases is not None and {"source_name", "canonical_name"}.issubset(aliases.columns):
        alias_map = {
            normalize_name(row.source_name): normalize_name(row.canonical_name)
            for row in aliases.itertuples(index=False)
            if normalize_name(row.source_name) and normalize_name(row.canonical_name)
        }
    ft["name_key"] = ft["player_name"].map(normalize_name)
    pr["name_key"] = pr["player_name"].map(normalize_name).replace(alias_map)
    counts = ft["name_key"].value_counts()
    unique_lookup = ft[ft["name_key"].map(counts).eq(1)].set_index("name_key")["fantrax_player_id"]
    pr["fantrax_player_id"] = pr["name_key"].map(unique_lookup).astype("object")
    pr["match_method"] = pr["fantrax_player_id"].notna().map({True: "exact_name", False: "unmatched"})

    # A few retired/inactive catalog records share a name with a current player.
    # Resolve only when the normalized name and NBA team together identify one row.
    if "nba_team" in ft and "nba_team" in pr:
        ft["nba_team_key"] = ft["nba_team"].fillna("").astype(str).str.upper().str.strip()
        pr["nba_team_key"] = pr["nba_team"].fillna("").astype(str).str.upper().str.strip()
        pair_counts = ft.groupby(["name_key", "nba_team_key"]).size()
        unique_pairs = set(pair_counts[pair_counts.eq(1)].index)
        pair_lookup = {
            (row.name_key, row.nba_team_key): row.fantrax_player_id
            for row in ft.itertuples(index=False)
            if (row.name_key, row.nba_team_key) in unique_pairs
        }
        unresolved = pr["fantrax_player_id"].isna()
        for index, row in pr.loc[unresolved, ["name_key", "nba_team_key"]].iterrows():
            pair = (row["name_key"], row["nba_team_key"])
            if pair in unique_pairs:
                pr.at[index, "fantrax_player_id"] = pair_lookup[pair]
                pr.at[index, "match_method"] = "exact_name_team"

    candidates = ft[["fantrax_player_id", "player_name", "name_key"]].drop_duplicates()
    exception_rows: list[dict[str, object]] = []
    for row in pr[pr["fantrax_player_id"].isna()].itertuples(index=False):
        scored = [
            (SequenceMatcher(None, row.name_key, candidate.name_key).ratio(), candidate)
            for candidate in candidates.itertuples(index=False)
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        best = scored[:2]
        exception_rows.append(
            {
                "projection_player_name": row.player_name,
                "normalized_name": row.name_key,
                "suggested_player_name": best[0][1].player_name if best else pd.NA,
                "suggested_fantrax_player_id": best[0][1].fantrax_player_id if best else pd.NA,
                "similarity": round(best[0][0], 4) if best else pd.NA,
                "ambiguous": bool(len(best) > 1 and best[0][0] - best[1][0] < 0.03),
                "review_recommended": bool(best and best[0][0] >= suggestion_threshold),
            }
        )
    return (
        pr.drop(columns=["name_key", "nba_team_key"], errors="ignore"),
        pd.DataFrame(exception_rows, columns=EXCEPTION_COLUMNS),
    )

