import pandas as pd
import streamlit as st
import requests
import json
from data import current_year, league_ids
from functions import get_matchup_stats, get_matchup_period_dates

def get_all_team_stats_history() -> pd.DataFrame:
    df_old = pd.read_parquet("./SBC_Streamlit/all_team_stats_history.parquet")
    df_old = df_old[df_old["Year"] != current_year]
    all_dates = get_matchup_period_dates()
    all_dates = all_dates[all_dates["Year"] == current_year]
    all_dates = all_dates[all_dates["Season"] == "Regular"]
    all_dates = (all_dates[["Year", "Period"]].drop_duplicates().reset_index(drop=True))
    dfs = []
    for i, row in enumerate(all_dates.itertuples(index=False), start=1):
        year = int(row.Year)
        period = int(row.Period)
        df = get_matchup_stats(year, period)
        df["Year"] = year
        df["Period"] = period
        dfs.append(df)
        print(f"row {i} done for {year} season, period {period}")
    final_df = pd.concat(dfs, ignore_index=True)
    final_df = pd.concat([df_old, final_df], ignore_index=True)
    final_df.to_parquet("SBC_Streamlit/all_team_stats_history.parquet", index=False)
    print("Complete")

@st.cache_data(ttl=86400)
def get_all_fantrax_standings(year) -> pd.DataFrame:
    roster_url = f"https://www.fantrax.com/fxea/general/getStandings?leagueId={league_ids.get(year)}"
    headers = {'Cookie': 'JSESSIONID='}
    response = requests.get(roster_url, headers=headers)
    if response.status_code == 200:
        standings = json.loads(response.text)
        df = pd.DataFrame(standings)
    else:
        print(f"Failed to fetch data - Status code: {response.status_code}")
    return df

