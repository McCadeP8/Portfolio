#import os
#os.chdir("SBC_Streamlit")

import pandas as pd
import os
import numpy as np  # noqa: F401
from datetime import datetime
from data import current_year, team_info
from functions import get_matchup_stats, get_fantrax_roster, send_discord_message, get_matchup_score

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
    today = datetime.now().date()
    april_15 = datetime(today.year, 4, 15).date()
    if today > april_15:
        send_discord_message(DISCORD_WEBHOOK_URL, "Turn back on Roster Count")

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

def get_all_time_standings() -> pd.DataFrame:
    df2 = pd.read_parquet("all_time_standings.parquet")
    df = pd.read_parquet("all_time_scores.parquet")
    df = df[df["Year"] == current_year]
    df_old = df2[df2["Year"] != current_year]
    df2 = df2[df2["Year"] == current_year]
    df["Winner"] = df["TeamA"].where(df["TeamAScore"] > df["TeamBScore"], df["TeamB"])
    df["Loser"] = df["TeamA"].where(df["TeamBScore"] >= df["TeamAScore"], df["TeamB"])
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
    df3 = pd.read_csv(csv_url)
    df = df.drop(columns=["Playoff Seed", "IST Seed"])
    df = df.merge(df3, on=["Year", "Team"], how="left")
    df.to_parquet("all_time_standings.parquet", index=False)
    send_discord_message(DISCORD_WEBHOOK_URL, "Completed run of get_all_time_standings")

def add_game_to_schedule(game_dict):
    df = pd.read_parquet("all_time_scores.parquet")
    new_row = pd.DataFrame([game_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_parquet("all_time_scores.parquet", index=False)
    return df

# add_game_to_schedule({
#     "Round": "Play-In Round 2",
#     "Type": "Play-In",
#     "Year": 2026,
#     "Period": 38,
#     "TeamA": "Baltimore",
#     "TeamB": "Des Moines",
#     "TeamAScore": np.nan,
#     "TeamBScore": np.nan,
#     "DivisionGame": np.nan,
#     "ConferenceGame": np.nan
# })

get_all_team_stats_history()
get_all_time_rosters_history()
get_all_time_scores()
get_all_time_standings()
