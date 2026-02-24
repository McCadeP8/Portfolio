import pandas as pd
import os
from data import current_year, team_info
from functions import get_matchup_stats, get_all_time_schedule, get_fantrax_roster, send_discord_message, get_matchup_score

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

def get_all_team_stats_history() -> pd.DataFrame:
    df_old = pd.read_parquet("all_team_stats_history.parquet")
    df_old = df_old[df_old["Year"] != current_year]
    all_dates = pd.read_parquet("all_time_scores.parquet")
    all_dates = all_dates[all_dates["Year"] == current_year]
    all_dates = (all_dates[["Year", "Period"]].drop_duplicates().reset_index(drop=True))
    dfs = []
    for i, row in enumerate(all_dates.itertuples(index=False), start=1):
        year = int(row.Year)
        period = int(row.Period)
        df = get_matchup_stats(year, period)
        df["Year"] = year
        df["Period"] = period
        dfs.append(df)
    final_df = pd.concat(dfs, ignore_index=True)
    final_df = pd.concat([df_old, final_df], ignore_index=True)
    final_df["Created"] = pd.Timestamp.now()
    final_df.to_parquet("all_team_stats_history.parquet", index=False)
    send_discord_message(DISCORD_WEBHOOK_URL, "Completed run of get_all_team_stats_history")

def get_all_time_rosters_history() -> pd.DataFrame:
    df_old = pd.read_parquet("all_time_rosters_history.parquet")
    df_old = df_old[df_old["Year"] != current_year]
    csv_url = ("https://docs.google.com/spreadsheets/d/1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/export?format=csv&gid=444367429")
    df = pd.read_csv(csv_url)
    df = df[df["Year"] == current_year]
    df = (df[["games", "Year"]].drop_duplicates().reset_index(drop=True))
    all_rosters = []
    for i, row in df.iterrows():
        year = row["Year"]
        games = row["games"]
        df2 = get_fantrax_roster(year, games)
        df2["Year"] = year
        cols = ["id", "position", "status", "team_name", "period", "Year"]
        df2 = df2[[c for c in cols if c in df2.columns]]
        all_rosters.append(df2)
    final_df = pd.concat(all_rosters, ignore_index=True)
    final_df = pd.concat([df_old, final_df], ignore_index=True)
    final_df["Created"] = pd.Timestamp.now()
    final_df.to_parquet("all_time_rosters_history.parquet", index=False)
    send_discord_message(DISCORD_WEBHOOK_URL, "Completed run of get_all_time_rosters_history")

def get_all_time_scores() -> pd.DataFrame:
    df = pd.read_parquet("all_time_scores.parquet")
    df_old = df[df["Year"] != current_year]
    df = df[df["Year"] == current_year]
    def get_team_city(team_name):
        for city, info in team_info.items():
            if team_name == f"{city} {info['nickname']}":
                return city
        return None
    df["TeamA"] = df["TeamA"].apply(get_team_city)
    df["TeamB"] = df["TeamB"].apply(get_team_city)
    for (year, period), group in df.groupby(["Year", "Period"]):
        year = int(year)
        period = int(period)
        stats_df = get_matchup_stats(year, period)
        for idx in group.index:
            team_a = df.at[idx, "TeamA"]
            team_b = df.at[idx, "TeamB"]
            team_a_score, team_b_score = get_matchup_score(team_a, team_b, stats_df)
            team_a_score, team_b_score = get_matchup_score(team_a, team_b, stats_df)
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
    df.to_parquet("all_time_scores.parquet", index=False)
    send_discord_message(DISCORD_WEBHOOK_URL, "Completed run of get_all_time_scores")

get_all_team_stats_history()
get_all_time_rosters_history()
get_all_time_scores()