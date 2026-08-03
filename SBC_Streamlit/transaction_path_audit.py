"""Read-only audit for unexplained SBCFBL player roster transitions."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

from functions import (
    _draft_pick_team_key,
    get_all_time_rosters,
    get_draft_history,
    get_fantrax_players,
    get_fantrax_transactions,
    get_offseason_signing_history,
    normalize_player_key,
)
from sbc_backend import get_repository


CALENDAR_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/"
    "export?format=csv&gid=444367429"
)
CURRENT_WINDOW = pd.DataFrame({
    "Year": 2027,
    "games": range(1, 175),
    "Date": pd.date_range("2026-10-20", "2027-04-11", freq="D"),
})


def load_inputs():
    rosters = get_all_time_rosters().copy()
    rosters["Year"] = pd.to_numeric(rosters["Year"], errors="coerce").astype("Int64")
    rosters["period"] = pd.to_numeric(rosters["period"], errors="coerce").astype("Int64")
    rosters["id"] = rosters["id"].astype(str)
    rosters = rosters.dropna(subset=["Year", "period", "id", "team_name"])
    rosters = rosters.drop_duplicates(["Year", "period", "id"], keep="last")

    calendar = pd.read_csv(CALENDAR_URL)
    calendar = calendar.rename(columns={"games": "period"})[["Year", "period", "Date"]]
    current = CURRENT_WINDOW.rename(columns={"games": "period"})
    calendar = pd.concat([calendar, current], ignore_index=True)
    calendar["Date"] = pd.to_datetime(calendar["Date"], errors="coerce")
    calendar["Year"] = pd.to_numeric(calendar["Year"], errors="coerce").astype("Int64")
    calendar["period"] = pd.to_numeric(calendar["period"], errors="coerce").astype("Int64")
    rosters = rosters.merge(calendar, on=["Year", "period"], how="left")

    transaction_frames = []
    for year in range(2021, 2028):
        frame = get_fantrax_transactions(year).copy()
        frame["Season Year"] = year
        transaction_frames.append(frame)
    transactions = pd.concat(transaction_frames, ignore_index=True)
    transactions["Date Sort"] = pd.to_datetime(transactions["Date Sort"], errors="coerce")
    transactions["Player Key"] = transactions["Player"].map(normalize_player_key)
    transactions["From Key"] = transactions["From"].map(_draft_pick_team_key)
    transactions["To Key"] = transactions["To"].map(_draft_pick_team_key)
    transactions["Team Key"] = transactions["Team"].map(_draft_pick_team_key)

    player_map = get_fantrax_players().dropna(subset=["fantraxId", "name"]).copy()
    id_to_names = {}
    for _, row in player_map.iterrows():
        id_to_names.setdefault(str(row["fantraxId"]), []).append(str(row["name"]))
    historic = transactions[
        transactions["Player ID"].astype(str).str.match(r"^[A-Za-z0-9]+$")
        & ~transactions["Player ID"].astype(str).str.startswith("offseason-")
    ]
    for player_id, group in historic.groupby("Player ID"):
        id_to_names.setdefault(str(player_id), []).extend(group["Player"].dropna().astype(str).tolist())
    matchup_stats = get_repository(Path(__file__).resolve().parent).read("matchup_stats")
    if not matchup_stats.empty and {"fantrax_id", "fantrax_name"}.issubset(matchup_stats.columns):
        for player_id, group in matchup_stats.dropna(subset=["fantrax_id", "fantrax_name"]).groupby("fantrax_id"):
            id_to_names.setdefault(str(player_id), []).extend(group["fantrax_name"].astype(str).tolist())
    # This retired player predates the archive's matchup-stat coverage.
    id_to_names.setdefault("027q4", []).append("E'Twaun Moore")
    id_to_name = {
        player_id: Counter(names).most_common(1)[0][0]
        for player_id, names in id_to_names.items() if names
    }
    rosters["Player"] = rosters["id"].map(id_to_name)
    rosters["Player Key"] = rosters["Player"].map(normalize_player_key)
    rosters["Team Key"] = rosters["team_name"].map(_draft_pick_team_key)
    return rosters, transactions, get_offseason_signing_history(), get_draft_history()


def _player_transactions(
    player: str,
    transactions: pd.DataFrame,
    after: pd.Timestamp,
    before: pd.Timestamp,
) -> pd.DataFrame:
    player_key = normalize_player_key(player)
    return transactions[
        transactions["Player Key"].eq(player_key)
        & transactions["Date Sort"].between(after - pd.Timedelta(days=2), before + pd.Timedelta(days=2))
    ].copy()


def offseason_boundaries(
    rosters: pd.DataFrame,
    transactions: pd.DataFrame,
    offseason: pd.DataFrame,
    draft: pd.DataFrame,
) -> pd.DataFrame:
    """Classify every end-of-season roster state against the player's next state."""
    ordered = rosters.sort_values(["id", "Year", "period"]).copy()
    max_period = ordered.groupby("Year")["period"].transform("max")
    season_ends = ordered[ordered["period"].eq(max_period)].copy()
    season_firsts = ordered.groupby(["id", "Year"], as_index=False).first()
    first_by_player = {
        player_id: group.sort_values("Year")
        for player_id, group in season_firsts.groupby("id", sort=False)
    }
    offseason = offseason.copy()
    offseason["Player Key"] = offseason["Player"].map(normalize_player_key)
    offseason["Team Key"] = offseason["Team"].map(_draft_pick_team_key)
    draft = draft.copy()
    draft["Player Key"] = draft["Player"].map(normalize_player_key)
    draft["Team Key"] = draft["Team"].map(_draft_pick_team_key)

    rows = []
    for end in season_ends.itertuples(index=False):
        later = first_by_player[end.id]
        later = later[later["Year"] > int(end.Year)]
        next_row = later.iloc[0] if not later.empty else None
        next_year = int(next_row["Year"]) if next_row is not None else int(end.Year) + 1
        boundary_end = (
            pd.Timestamp(next_row["Date"])
            if next_row is not None
            else pd.Timestamp(year=int(end.Year), month=7, day=1)
        )
        relevant = _player_transactions(end.Player, transactions, pd.Timestamp(end.Date), boundary_end)
        from_key = _draft_pick_team_key(end.team_name)
        to_key = _draft_pick_team_key(next_row["team_name"]) if next_row is not None else ""
        continuation = (
            next_row is not None
            and int(next_row["Year"]) == int(end.Year) + 1
            and int(next_row["period"]) == 1
            and from_key == to_key
        )
        traded = False
        dropped = False
        acquired = False
        if not relevant.empty:
            traded = bool((relevant["From Key"].eq(from_key) & relevant["To Key"].eq(to_key)).any())
            dropped = bool(
                relevant["Type"].astype(str).str.lower().eq("drop").any()
                and (relevant["Team Key"].eq(from_key) | relevant["From Key"].eq(from_key)).any()
            )
            acquired = bool(
                relevant["Type"].astype(str).str.lower().isin(["claim", "signing", "original signing"]).any()
                and (relevant["Team Key"].eq(to_key) | relevant["To Key"].eq(to_key)).any()
            )
        signed = offseason[
            offseason["Season Year"].eq(next_year)
            & offseason["Player Key"].eq(normalize_player_key(end.Player))
            & offseason["Team Key"].eq(to_key)
        ]
        acquired = acquired or not signed.empty
        if continuation:
            classification = "Continued"
        elif traded:
            classification = "Documented trade"
        elif dropped and (next_row is None or acquired):
            classification = "Documented release/signing"
        elif acquired:
            classification = "Missing expiration"
        elif next_row is None:
            classification = "Missing expiration"
        else:
            classification = "Missing expiration + move"
        rows.append({
            "Prior Season": int(end.Year),
            "Player ID": end.id,
            "Player": end.Player,
            "From": from_key,
            "Last Date": end.Date,
            "Next Season": int(next_row["Year"]) if next_row is not None else pd.NA,
            "Next Period": int(next_row["period"]) if next_row is not None else pd.NA,
            "Next Date": next_row["Date"] if next_row is not None else pd.NaT,
            "To": to_key,
            "Classification": classification,
        })
    return pd.DataFrame(rows)


def first_appearances(
    rosters: pd.DataFrame,
    transactions: pd.DataFrame,
    offseason: pd.DataFrame,
    draft: pd.DataFrame,
) -> pd.DataFrame:
    """Find players whose first roster state has no original, draft, signing, or claim source."""
    first = rosters.sort_values(["Date", "period"]).groupby("id", as_index=False).first()
    offseason = offseason.copy()
    offseason["Player Key"] = offseason["Player"].map(normalize_player_key)
    offseason["Team Key"] = offseason["Team"].map(_draft_pick_team_key)
    draft = draft.copy()
    draft["Player Key"] = draft["Player"].map(normalize_player_key)
    draft["Team Key"] = draft["Team"].map(_draft_pick_team_key)
    rows = []
    for row in first.itertuples(index=False):
        player_key = normalize_player_key(row.Player)
        team_key = _draft_pick_team_key(row.team_name)
        source = ""
        original = offseason[
            offseason["Original Team"].eq(True)
            & offseason["Player Key"].eq(player_key)
            & offseason["Team Key"].eq(team_key)
        ]
        drafted = draft[
            draft["Year"].eq(int(row.Year) - 1)
            & draft["Player Key"].eq(player_key)
            & draft["Team Key"].eq(team_key)
        ]
        signed = offseason[
            offseason["Season Year"].eq(int(row.Year))
            & offseason["Player Key"].eq(player_key)
            & offseason["Team Key"].eq(team_key)
        ]
        relevant = transactions[
            transactions["Player Key"].eq(player_key)
            & transactions["Date Sort"].le(pd.Timestamp(row.Date) + pd.Timedelta(days=2))
            & (transactions["Team Key"].eq(team_key) | transactions["To Key"].eq(team_key))
        ]
        if not original.empty:
            source = "Original signing"
        elif not drafted.empty:
            source = "Draft"
        elif not signed.empty:
            source = "Offseason signing"
        elif not relevant.empty:
            source = "Fantrax transaction"
        rows.append({
            "Season": int(row.Year), "Date": row.Date, "Period": int(row.period),
            "Player ID": row.id, "Player": row.Player, "Team": team_key,
            "Source": source or "Missing source",
        })
    return pd.DataFrame(rows)


def roster_events(rosters: pd.DataFrame) -> pd.DataFrame:
    ordered = rosters.sort_values(["id", "Year", "period"]).copy()
    groups = ordered.groupby(["id", "Year"], sort=False)
    ordered["Prev Period"] = groups["period"].shift()
    ordered["Prev Team"] = groups["Team Key"].shift()
    ordered["Prev Date"] = groups["Date"].shift()
    ordered["Max Period"] = ordered.groupby("Year")["period"].transform("max")
    base_columns = {
        "id": "Player ID", "period": "Period", "Team Key": "To",
    }

    starts = ordered[ordered["Prev Period"].isna()].rename(columns=base_columns)
    starts = starts[["Player ID", "Player", "Player Key", "Year", "Period", "Date", "To"]].copy()
    starts["Event"] = "Season Entry"
    starts["From"] = ""

    changed = ordered[
        ordered["Prev Period"].notna()
        & ordered["period"].eq(ordered["Prev Period"] + 1)
        & ordered["Team Key"].ne(ordered["Prev Team"])
    ].rename(columns=base_columns)
    changed = changed[["Player ID", "Player", "Player Key", "Year", "Period", "Date", "To", "Prev Team"]].copy()
    changed["Event"] = "Team Change"
    changed["From"] = changed.pop("Prev Team")

    gaps = ordered[ordered["Prev Period"].notna() & ordered["period"].gt(ordered["Prev Period"] + 1)]
    gap_entries = gaps.rename(columns=base_columns)
    gap_entries = gap_entries[["Player ID", "Player", "Player Key", "Year", "Period", "Date", "To"]].copy()
    gap_entries["Event"] = "Roster Entry"
    gap_entries["From"] = ""
    gap_exits = pd.DataFrame({
        "Player ID": gaps["id"], "Player": gaps["Player"], "Player Key": gaps["Player Key"],
        "Year": gaps["Year"], "Period": gaps["Prev Period"] + 1,
        "Date": gaps["Prev Date"] + pd.Timedelta(days=1), "From": gaps["Prev Team"],
        "Event": "Roster Exit", "To": "",
    })

    ends = ordered.groupby(["id", "Year"], as_index=False).last()
    ends = ends[ends["period"].lt(ends["Max Period"])].rename(
        columns={"id": "Player ID", "period": "Period", "Team Key": "From"}
    )
    ends = ends[["Player ID", "Player", "Player Key", "Year", "Period", "Date", "From"]].copy()
    ends["Period"] = ends["Period"] + 1
    ends["Date"] = ends["Date"] + pd.Timedelta(days=1)
    ends["Event"] = "Roster Exit"
    ends["To"] = ""
    return pd.concat([starts, changed, gap_entries, gap_exits, ends], ignore_index=True)


def event_is_covered(event: pd.Series, transactions: pd.DataFrame, offseason: pd.DataFrame) -> bool:
    player_key = normalize_player_key(event.get("Player", ""))
    if not player_key:
        return False
    year = int(event["Year"])
    candidates = transactions[
        transactions["Season Year"].eq(year) & transactions["Player Key"].eq(player_key)
    ].copy()
    event_date = pd.to_datetime(event["Date"], errors="coerce")
    if event["Event"] == "Season Entry" and int(event["Period"]) == 1:
        source = offseason[
            offseason["Season Year"].eq(year)
            & offseason["Player"].map(normalize_player_key).eq(player_key)
            & offseason["Team"].map(_draft_pick_team_key).eq(event["To"])
        ]
        if not source.empty:
            return True
    if candidates.empty or pd.isna(event_date):
        return False
    date_gap = (candidates["Date Sort"].dt.normalize() - event_date.normalize()).dt.days.abs()
    nearby = candidates[date_gap <= 2]
    if nearby.empty:
        return False
    if event["Event"] == "Roster Exit":
        return nearby["Type"].astype(str).str.lower().eq("drop").any()
    if event["Event"] in {"Roster Entry", "Season Entry"}:
        return (
            nearby["Team Key"].eq(event["To"])
            | nearby["To Key"].eq(event["To"])
        ).any()
    if event["Event"] == "Team Change":
        return (
            nearby["From Key"].eq(event["From"])
            & nearby["To Key"].eq(event["To"])
        ).any() or (
            nearby["Team Key"].eq(event["To"])
            & nearby["Type"].astype(str).str.lower().isin(["claim", "signing", "original signing"])
        ).any()
    return False


def main():
    rosters, transactions, offseason, draft = load_inputs()
    events = roster_events(rosters)
    events["Covered"] = events.apply(event_is_covered, axis=1, transactions=transactions, offseason=offseason)
    print("Roster rows:", len(rosters))
    print("Roster player IDs:", rosters["id"].nunique())
    print("Named roster IDs:", rosters.dropna(subset=["Player"])["id"].nunique())
    print("Roster dates missing:", int(rosters["Date"].isna().sum()))
    print("\nEvents by type and coverage:")
    print(events.groupby(["Event", "Covered"]).size().unstack(fill_value=0).to_string())
    unexplained = events[~events["Covered"]].copy()
    print("\nUnexplained named events by year/type:")
    print(
        unexplained[unexplained["Player"].notna()]
        .groupby(["Year", "Event"]).size().unstack(fill_value=0).to_string()
    )
    print("\nUnmapped roster IDs:")
    print(rosters[rosters["Player"].isna()]["id"].value_counts().head(60).to_string())
    print("\nSample unexplained team changes:")
    print(
        unexplained[(unexplained["Event"] == "Team Change") & unexplained["Player"].notna()]
        [["Year", "Date", "Player ID", "Player", "From", "To"]]
        .head(80).to_string(index=False)
    )
    print("\nSample unexplained exits:")
    print(
        unexplained[(unexplained["Event"] == "Roster Exit") & unexplained["Player"].notna()]
        [["Year", "Date", "Player ID", "Player", "From"]]
        .head(80).to_string(index=False)
    )
    boundaries = offseason_boundaries(rosters, transactions, offseason, draft)
    print("\nOffseason boundary classifications:")
    print(boundaries["Classification"].value_counts().to_string())
    print("\nMissing offseason moves:")
    print(
        boundaries[boundaries["Classification"].eq("Missing expiration + move")]
        [["Prior Season", "Player", "From", "Next Season", "Next Date", "To"]]
        .to_string(index=False)
    )
    starts = first_appearances(rosters, transactions, offseason, draft)
    print("\nFirst appearance sources:")
    print(starts["Source"].value_counts().to_string())
    print("\nMissing first sources:")
    print(starts[starts["Source"].eq("Missing source")].to_string(index=False))
    boundaries.to_csv("transaction_boundary_audit.csv", index=False)
    starts.to_csv("transaction_first_appearance_audit.csv", index=False)


if __name__ == "__main__":
    main()
