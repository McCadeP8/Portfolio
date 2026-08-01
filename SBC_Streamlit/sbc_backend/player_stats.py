"""Pure helpers for filtering and deduplicating SBC player matchup totals."""

from __future__ import annotations

import pandas as pd


def _is_blank(value: object) -> bool:
    if value is None or pd.isna(value):
        return True
    return str(value).strip().casefold() in {"", "nan", "none", "null"}


def prepare_matchup_archive_rows(rows: pd.DataFrame, matchup_type: str | None = None) -> pd.DataFrame:
    """Filter to one game type before collapsing duplicate schedule representations."""
    if rows is None or rows.empty:
        return rows.copy() if isinstance(rows, pd.DataFrame) else pd.DataFrame()
    work = rows.copy()
    if "sbc_opponent" in work.columns:
        work = work[~work["sbc_opponent"].apply(_is_blank)].copy()
    if "Game_ID" in work.columns:
        work = work[~work["Game_ID"].apply(_is_blank)].copy()
    if matchup_type is not None:
        if "sbc_matchup_type" not in work.columns:
            return work.iloc[0:0].copy()
        work = work[work["sbc_matchup_type"].astype(str) == str(matchup_type)].copy()
    if work.empty or "nba_game_ids" not in work.columns:
        return work

    period_col = "sbc_period" if "sbc_period" in work.columns else "_period"
    team_col = "sbc_team_key" if "sbc_team_key" in work.columns else "sbc_team"
    key_cols = [col for col in ["fantrax_id", "sbc_year", period_col, team_col] if col in work.columns]
    if len(key_cols) < 3:
        return work
    sort_cols = key_cols + [col for col in ["sbc_matchup_type", "Game_ID"] if col in work.columns]
    work = work.sort_values(sort_cols)
    first_rows = work.drop_duplicates(key_cols, keep="first").copy()
    if "sbc_opponent" in work.columns:
        opponents = (
            work.groupby(key_cols)["sbc_opponent"]
            .apply(lambda values: " / ".join(pd.Series(values).dropna().astype(str).drop_duplicates()))
            .reset_index()
        )
        first_rows = first_rows.drop(columns=["sbc_opponent"], errors="ignore").merge(opponents, on=key_cols, how="left")
    if "Game_ID" in work.columns:
        game_ids = (
            work.groupby(key_cols)["Game_ID"]
            .apply(lambda values: " / ".join(pd.Series(values).dropna().astype(str).drop_duplicates()))
            .reset_index()
        )
        first_rows = first_rows.drop(columns=["Game_ID"], errors="ignore").merge(game_ids, on=key_cols, how="left")
    return first_rows
