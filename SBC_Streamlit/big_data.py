#import os
#os.chdir("SBC_Streamlit")

import pandas as pd
import os
import numpy as np  # noqa: F401
from datetime import date, datetime, timedelta
from pathlib import Path
from data import league_ids, team_info
from functions import (
    current_matchup_period,
    get_award_history,
    get_base_cap,
    get_data,
    get_draft_history,
    get_draft_picks,
    get_exceptions,
    get_fantrax_roster,
    get_matchup_score,
    get_matchup_stats,
    get_period_calendar,
    get_pictures,
    get_team_award_history,
    future_matchup_periods,
    read_csv_snapshot,
    send_discord_message,
    zero_future_matchup_scores,
)
from sbc_backend import BackendSettings
from sbc_backend.storage import atomic_write_parquet

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
APP_DIR = Path(__file__).resolve().parent
BACKEND_SETTINGS = BackendSettings.from_env(APP_DIR)
current_year = BACKEND_SETTINGS.current_sbc_year

ROSTER_SEASON_WINDOWS = {
    2027: (date(2026, 10, 20), date(2027, 4, 11)),
}


def dataset_path(filename: str) -> Path:
    return BACKEND_SETTINGS.data_root / filename

def notify(message: str):
    print(message)
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        send_discord_message(DISCORD_WEBHOOK_URL, message)
    except Exception as exc:
        print(f"Discord notification failed: {exc}")


def refresh_sheet_snapshots():
    loaders = [
        ("cap sheet", get_data),
        ("pictures", get_pictures),
        ("exceptions", get_exceptions),
        ("base cap", get_base_cap),
        ("draft picks", get_draft_picks),
        ("period calendar", get_period_calendar),
        ("draft history", get_draft_history),
        ("award history", get_award_history),
        ("team award history", get_team_award_history),
        ("current matchup period", current_matchup_period),
    ]
    for label, loader in loaders:
        try:
            loader()
            notify(f"Refreshed snapshot: {label}")
        except Exception as exc:
            notify(f"Skipped snapshot refresh for {label}: {type(exc).__name__}: {exc}")


def get_all_team_stats_history() -> pd.DataFrame:
    history = pd.read_parquet(dataset_path("all_team_stats_history.parquet"))
    all_dates = pd.read_parquet(dataset_path("all_time_scores.parquet"))
    all_dates = all_dates[all_dates["Year"] == current_year]
    all_dates = (all_dates[["Year", "Period"]].drop_duplicates().reset_index(drop=True))
    if all_dates.empty:
        notify(f"Skipped get_all_team_stats_history: no {current_year} periods found in all_time_scores.parquet")
        return history

    dfs = []
    for i, row in enumerate(all_dates.itertuples(index=False), start=1):
        year = int(row.Year)
        period = int(row.Period)
        df = get_matchup_stats(year, period)
        if df is None or df.empty:
            notify(f"Skipped team stats for {year} period {period}: Fantrax returned no data")
            continue
        df["Year"] = year
        df["Period"] = period
        dfs.append(df)
    if not dfs:
        notify(f"Skipped get_all_team_stats_history: no Fantrax team stats were available for {current_year}")
        return history

    df_old = history[history["Year"] != current_year]
    final_df = pd.concat(dfs, ignore_index=True)
    final_df = pd.concat([df_old, final_df], ignore_index=True)
    final_df["Created"] = pd.Timestamp.now()
    atomic_write_parquet(final_df, dataset_path("all_team_stats_history.parquet"), row_group_size=BACKEND_SETTINGS.parquet_row_group_size)
    notify("Completed run of get_all_team_stats_history")
    today = datetime.now().date()
    april_15 = datetime(today.year, 4, 15).date()
    if today > april_15:
        notify("Turn back on Roster Count")

def _merge_roster_snapshots(history: pd.DataFrame, fresh: pd.DataFrame, year: int, refreshed_periods: set[int]) -> pd.DataFrame:
    """Replace only successfully refreshed periods, preserving every other snapshot."""
    existing = history.copy()
    existing_year = pd.to_numeric(existing.get("Year"), errors="coerce")
    existing_period = pd.to_numeric(existing.get("period"), errors="coerce")
    replace_mask = existing_year.eq(year) & existing_period.isin(refreshed_periods)
    combined = pd.concat([existing.loc[~replace_mask], fresh], ignore_index=True, sort=False)
    dedupe_key = [column for column in ("Year", "period", "team_name", "id") if column in combined.columns]
    if dedupe_key:
        combined = combined.drop_duplicates(dedupe_key, keep="last")
    sort_key = [column for column in ("Year", "period", "team_name", "id") if column in combined.columns]
    if sort_key:
        combined = combined.sort_values(sort_key, kind="stable", na_position="last").reset_index(drop=True)
    return combined


def _configured_roster_periods(year: int) -> pd.DataFrame:
    """Build Fantrax's one-based daily periods for seasons configured before the schedule exists."""
    window = ROSTER_SEASON_WINDOWS.get(year)
    if window is None:
        return pd.DataFrame(columns=["games", "Year", "Date"])
    start, end = window
    if end < start:
        raise ValueError(f"Roster season window ends before it starts for {year}")
    dates = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
    return pd.DataFrame({"games": range(1, len(dates) + 1), "Year": year, "Date": dates})


def get_all_time_rosters_history() -> pd.DataFrame:
    history = pd.read_parquet(dataset_path("all_time_rosters_history.parquet"))
    roster_year = BACKEND_SETTINGS.current_sbc_year
    if roster_year not in league_ids:
        notify(f"Skipped get_all_time_rosters_history: no Fantrax league ID configured for {roster_year}")
        return history
    df = _configured_roster_periods(roster_year)
    if not df.empty:
        start, end = ROSTER_SEASON_WINDOWS[roster_year]
        notify(f"Using configured {roster_year} roster window: {start} through {end} ({len(df)} daily periods)")
    else:
        csv_url = ("https://docs.google.com/spreadsheets/d/1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/export?format=csv&gid=444367429")
        df = read_csv_snapshot("schedule_calendar", csv_url, ttl_seconds=0)
        df["Year"] = pd.to_numeric(df.get("Year"), errors="coerce")
        df["games"] = pd.to_numeric(df.get("games"), errors="coerce")
        df = df[df["Year"].eq(roster_year) & df["games"].notna()].copy()
        df["games"] = df["games"].astype(int)
        df = df[["games", "Year"]].drop_duplicates().sort_values("games").reset_index(drop=True)
    if df.empty:
        notify(f"Skipped get_all_time_rosters_history: no {roster_year} roster periods found in the schedule sheet")
        return history

    all_rosters = []
    refreshed_periods: set[int] = set()
    for row in df.itertuples(index=False):
        year = int(row.Year)
        games = int(row.games)
        df2 = get_fantrax_roster(year, games)
        if df2 is None or df2.empty:
            notify(f"Skipped roster snapshot for {year} period {games}: Fantrax returned no roster data")
            continue
        df2["Year"] = year
        df2["period"] = games
        df2["Created"] = pd.Timestamp.now(tz="UTC").tz_localize(None)
        cols = ["id", "position", "status", "team_name", "period", "Year"]
        df2 = df2[[c for c in [*cols, "Created"] if c in df2.columns]]
        all_rosters.append(df2)
        refreshed_periods.add(games)
    if not all_rosters:
        notify(f"Skipped get_all_time_rosters_history: no Fantrax roster data was available for {roster_year}")
        return history

    fresh = pd.concat(all_rosters, ignore_index=True)
    final_df = _merge_roster_snapshots(history, fresh, roster_year, refreshed_periods)
    atomic_write_parquet(final_df, dataset_path("all_time_rosters_history.parquet"), row_group_size=BACKEND_SETTINGS.parquet_row_group_size)
    notify(
        f"Completed get_all_time_rosters_history for {roster_year}: "
        f"{len(refreshed_periods)}/{len(df)} periods refreshed, {len(fresh)} current rows fetched"
    )
    return final_df

def get_all_time_scores() -> pd.DataFrame:
    df = pd.read_parquet(dataset_path("all_time_scores.parquet"))
    df_old = df[df["Year"] != current_year]
    df = df[df["Year"] == current_year]
    if df.empty:
        notify(f"Skipped get_all_time_scores: no {current_year} games found in all_time_scores.parquet")
        return pd.concat([df_old, df], ignore_index=True)

    try:
        period_calendar = get_period_calendar()
    except Exception as exc:
        notify(f"Could not apply future score guard: {type(exc).__name__}: {exc}")
        period_calendar = pd.DataFrame()
    future_periods = future_matchup_periods(period_calendar)
    df = zero_future_matchup_scores(df, period_calendar)

    for (year, period), group in df.groupby(["Year", "Period"]):
        year = int(year)
        period = int(period)
        if (year, period) in future_periods:
            notify(f"Kept future scores at 0-0 for {year} period {period}")
            continue
        stats_df = get_matchup_stats(year, period)
        if stats_df is None or stats_df.empty:
            notify(f"Skipped score update for {year} period {period}: Fantrax returned no team stats")
            continue
        for idx in group.index:
            team_a = df.at[idx, "TeamA"]
            team_b = df.at[idx, "TeamB"]
            try:
                team_a_score, team_b_score = get_matchup_score(team_a, team_b, stats_df)
            except ValueError as exc:
                notify(f"Skipped score update for {team_a} vs {team_b}, {year} period {period}: {exc}")
                continue
            if team_a_score is None or team_b_score is None:
                notify(f"Skipped score update for {team_a} vs {team_b}, {year} period {period}: incomplete team stats")
                continue
            df.at[idx, "TeamAScore"] = team_a_score
            df.at[idx, "TeamBScore"] = team_b_score
    def get_conference(team_name):
        if team_name in team_info:
            return team_info[team_name]['conf']
        return None
    df['ConferenceGame'] = df.apply(lambda row: get_conference(row['TeamA']) == get_conference(row['TeamB']), axis=1)
    df.loc[df['Type'] != 'Regular Season', 'ConferenceGame'] = False
    def get_division(team_name):
        if team_name in team_info:
            return team_info[team_name]['div']
        return None
    df['DivisionGame'] = df.apply(lambda row: get_division(row['TeamA']) == get_division(row['TeamB']), axis=1)
    df.loc[df['Type'] != 'Regular Season', 'DivisionGame'] = False
    df = pd.concat([df_old, df], ignore_index=True)        
    atomic_write_parquet(df, dataset_path("all_time_scores.parquet"), row_group_size=BACKEND_SETTINGS.parquet_row_group_size)
    notify("Completed run of get_all_time_scores")

def get_all_time_standings() -> pd.DataFrame:
    df2 = pd.read_parquet(dataset_path("all_time_standings.parquet"))
    df = pd.read_parquet(dataset_path("all_time_scores.parquet"))
    df = df[df["Year"] == current_year]
    df_old = df2[df2["Year"] != current_year]
    df2 = df2[df2["Year"] == current_year]
    if df.empty or df2.empty:
        notify(f"Skipped get_all_time_standings: missing {current_year} scores or standings seed rows")
        return pd.concat([df_old, df2], ignore_index=True)

    # A 0-0 row is an unplayed schedule placeholder, not a TeamB win.
    played = (pd.to_numeric(df["TeamAScore"], errors="coerce") > 0) | (pd.to_numeric(df["TeamBScore"], errors="coerce") > 0)
    df["Winner"] = None
    df["Loser"] = None
    df.loc[played, "Winner"] = df.loc[played, "TeamA"].where(
        df.loc[played, "TeamAScore"] > df.loc[played, "TeamBScore"], df.loc[played, "TeamB"]
    )
    df.loc[played, "Loser"] = df.loc[played, "TeamA"].where(
        df.loc[played, "TeamBScore"] >= df.loc[played, "TeamAScore"], df.loc[played, "TeamB"]
    )
    total_wins = df[df['Type'] == 'Regular Season'].groupby(['Year', 'Period', 'Winner']).size().reset_index(name='Total')
    total_losses = df[df['Type'] == 'Regular Season'].groupby(['Year', 'Period', 'Loser']).size().reset_index(name='Total')
    total_wins['CumWins'] = total_wins.groupby(['Year', 'Winner'])['Total'].cumsum()
    total_losses['CumLosses'] = total_losses.groupby(['Year', 'Loser'])['Total'].cumsum()
    df2 = df2.merge(total_wins[['Year', 'Period', 'Winner', 'CumWins']], left_on=['Year', 'Period', 'Team'], right_on=['Year', 'Period', 'Winner'], how='left').drop(columns='Winner')
    df2['CumWins'] = df2.groupby(['Year', 'Team'])['CumWins'].ffill().fillna(0)
    df2 = df2.merge(total_losses[['Year', 'Period', 'Loser', 'CumLosses']], left_on=['Year', 'Period', 'Team'], right_on=['Year', 'Period', 'Loser'], how='left').drop(columns='Loser')
    df2['CumLosses'] = df2.groupby(['Year', 'Team'])['CumLosses'].ffill().fillna(0)
    df2['CumWins'] = df2.groupby(['Year', 'Team'])['CumWins'].shift(1).fillna(0)
    df2['CumLosses'] = df2.groupby(['Year', 'Team'])['CumLosses'].shift(1).fillna(0)
    df2['Record'] = df2['CumWins'].astype(int).astype(str) + '-' + df2['CumLosses'].astype(int).astype(str)
    df2 = df2.drop(columns=['CumWins', 'CumLosses'])
    conf_wins = df[(df['Type'] == 'Regular Season') & (df['ConferenceGame'])].groupby(['Year', 'Period', 'Winner']).size().reset_index(name='Total')
    conf_losses = df[(df['Type'] == 'Regular Season') & (df['ConferenceGame'])].groupby(['Year', 'Period', 'Loser']).size().reset_index(name='Total')
    conf_wins['CumConfWins'] = conf_wins.groupby(['Year', 'Winner'])['Total'].cumsum()
    conf_losses['CumConfLosses'] = conf_losses.groupby(['Year', 'Loser'])['Total'].cumsum()
    df2 = df2.merge(conf_wins[['Year', 'Period', 'Winner', 'CumConfWins']], left_on=['Year', 'Period', 'Team'], right_on=['Year', 'Period', 'Winner'], how='left').drop(columns='Winner')
    df2['CumConfWins'] = df2.groupby(['Year', 'Team'])['CumConfWins'].ffill().fillna(0)
    df2 = df2.merge(conf_losses[['Year', 'Period', 'Loser', 'CumConfLosses']], left_on=['Year', 'Period', 'Team'], right_on=['Year', 'Period', 'Loser'], how='left').drop(columns='Loser')
    df2['CumConfLosses'] = df2.groupby(['Year', 'Team'])['CumConfLosses'].ffill().fillna(0)
    df2['CumConfWins'] = df2.groupby(['Year', 'Team'])['CumConfWins'].shift(1).fillna(0)
    df2['CumConfLosses'] = df2.groupby(['Year', 'Team'])['CumConfLosses'].shift(1).fillna(0)
    df2['ConfRecord'] = df2['CumConfWins'].astype(int).astype(str) + '-' + df2['CumConfLosses'].astype(int).astype(str)
    df2 = df2.drop(columns=['CumConfWins', 'CumConfLosses'])
    div_wins = df[(df['Type'] == 'Regular Season') & (df['DivisionGame'])].groupby(['Year', 'Period', 'Winner']).size().reset_index(name='Total')
    div_losses = df[(df['Type'] == 'Regular Season') & (df['DivisionGame'])].groupby(['Year', 'Period', 'Loser']).size().reset_index(name='Total')
    div_wins['CumDivWins'] = div_wins.groupby(['Year', 'Winner'])['Total'].cumsum()
    div_losses['CumDivLosses'] = div_losses.groupby(['Year', 'Loser'])['Total'].cumsum()
    df2 = df2.merge(div_wins[['Year', 'Period', 'Winner', 'CumDivWins']], left_on=['Year', 'Period', 'Team'], right_on=['Year', 'Period', 'Winner'], how='left').drop(columns='Winner')
    df2['CumDivWins'] = df2.groupby(['Year', 'Team'])['CumDivWins'].ffill().fillna(0)
    df2 = df2.merge(div_losses[['Year', 'Period', 'Loser', 'CumDivLosses']], left_on=['Year', 'Period', 'Team'], right_on=['Year', 'Period', 'Loser'], how='left').drop(columns='Loser')
    df2['CumDivLosses'] = df2.groupby(['Year', 'Team'])['CumDivLosses'].ffill().fillna(0)
    df2['CumDivWins'] = df2.groupby(['Year', 'Team'])['CumDivWins'].shift(1).fillna(0)
    df2['CumDivLosses'] = df2.groupby(['Year', 'Team'])['CumDivLosses'].shift(1).fillna(0)
    df2['DivRecord'] = df2['CumDivWins'].astype(int).astype(str) + '-' + df2['CumDivLosses'].astype(int).astype(str)
    df2 = df2.drop(columns=['CumDivWins', 'CumDivLosses'])
    gs_wins = df[df['Round'] == 'Group Stage'].groupby(['Year', 'Period', 'Winner']).size().reset_index(name='Total')
    gs_losses = df[df['Round'] == 'Group Stage'].groupby(['Year', 'Period', 'Loser']).size().reset_index(name='Total')
    gs_wins['CumGSWins'] = gs_wins.groupby(['Year', 'Winner'])['Total'].cumsum()
    gs_losses['CumGSLosses'] = gs_losses.groupby(['Year', 'Loser'])['Total'].cumsum()
    df2 = df2.merge(gs_wins[['Year', 'Period', 'Winner', 'CumGSWins']], left_on=['Year', 'Period', 'Team'], right_on=['Year', 'Period', 'Winner'], how='left').drop(columns='Winner')
    df2['CumGSWins'] = df2.groupby(['Year', 'Team'])['CumGSWins'].ffill().fillna(0)
    df2 = df2.merge(gs_losses[['Year', 'Period', 'Loser', 'CumGSLosses']], left_on=['Year', 'Period', 'Team'], right_on=['Year', 'Period', 'Loser'], how='left').drop(columns='Loser')
    df2['CumGSLosses'] = df2.groupby(['Year', 'Team'])['CumGSLosses'].ffill().fillna(0)
    df2['CumGSWins'] = df2.groupby(['Year', 'Team'])['CumGSWins'].shift(1).fillna(0)
    df2['CumGSLosses'] = df2.groupby(['Year', 'Team'])['CumGSLosses'].shift(1).fillna(0)
    df2['GSRecord'] = df2['CumGSWins'].astype(int).astype(str) + '-' + df2['CumGSLosses'].astype(int).astype(str)
    df2 = df2.drop(columns=['CumGSWins', 'CumGSLosses'])
    df = pd.concat([df_old, df2], ignore_index=True)        
    csv_url = "https://docs.google.com/spreadsheets/d/1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/export?format=csv&gid=243607559"
    df3 = read_csv_snapshot("playoff_ist_seeds", csv_url, ttl_seconds=0)
    df = df.drop(columns=["Playoff Seed", "IST Seed"], errors="ignore")
    df = df.merge(df3, on=["Year", "Team"], how="left")
    atomic_write_parquet(df, dataset_path("all_time_standings.parquet"), row_group_size=BACKEND_SETTINGS.parquet_row_group_size)
    notify("Completed run of get_all_time_standings")

def add_game_to_schedule(game_dict):
    schedule_path = dataset_path("all_time_scores.parquet")
    df = pd.read_parquet(schedule_path)
    year = game_dict["Year"]
    df_year = df[df["Game_ID"].str.startswith(str(year)) & df["Game_ID"].notna()]
    if len(df_year) == 0:
        next_num = 1
    else:
        nums = df_year["Game_ID"].str.split("_").str[1].astype(int)
        next_num = nums.max() + 1
    game_dict["Game_ID"] = f"{year}_{str(next_num).zfill(3)}"
    df = pd.concat([df, pd.DataFrame([game_dict])], ignore_index=True)
    atomic_write_parquet(df, schedule_path, row_group_size=BACKEND_SETTINGS.parquet_row_group_size)
    return df

# add_game_to_schedule({
#     "Round": "SBCFBL Finals",
#     "Type": "Playoffs",
#     "Year": 2026,
#     "Period": 42,
#     "TeamA": "Honolulu",
#     "TeamB": "Pittsburgh",
#     "TeamAScore": np.nan,
#     "TeamBScore": np.nan,
#     "DivisionGame": np.nan,
#     "ConferenceGame": np.nan,
# })

if __name__ == "__main__":
    refresh_sheet_snapshots()
    get_all_team_stats_history()
    get_all_time_rosters_history()
    get_all_time_scores()
    get_all_time_standings()

