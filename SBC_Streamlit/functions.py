#import os
#os.chdir("SBC_Streamlit")

import pandas as pd
import streamlit as st
import math as math
import numpy as np
import folium as folium
import streamlit.components.v1 as components
import base64
from pathlib import Path
from itertools import combinations
import requests
import json
import altair as alt
import unicodedata
from data import current_salary_cap, current_luxury_tax, current_apron_1, current_apron_2, tax_bracket_increment, league_ratio, columns_order, current_year, year_offset, team_info, cap_sheets_to_fantrax_name_fix, minimum_sal, max_minimum, league_ids, team_id_history, stat_to_scipId, today

def safe_team_info(team, field, default=""):
    return team_info.get(str(team), {}).get(field, default)

def normalize_player_key(value):
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.lower().replace(".", "").replace("'", "").split())

@st.cache_data(ttl=86400)
def get_data() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1906653859"
    df = pd.read_csv(csv_url)
    return df

@st.cache_data()
def get_pictures() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1180190150"
    df = pd.read_csv(csv_url)
    df = df.drop(columns=["Picture"])
    return df

@st.cache_data()
def get_exceptions(ttl=86400) -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1620818587"
    df = pd.read_csv(csv_url)
    df = df[["Team", "Player", "Y" + str(current_year), "BirdRights"]]
    return df

@st.cache_data(ttl=86400)
def get_base_cap() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=760630769"
    df = pd.read_csv(csv_url)
    return df

@st.cache_data(ttl=86400)
def get_draft_picks() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1612129799"
    df = pd.read_csv(csv_url)
    df = df[df['Year'].between(current_year, current_year + 6)]
    return df

@st.cache_data(ttl=86400)
def get_all_time_team_stats() -> pd.DataFrame:
    df = pd.read_parquet("SBC_Streamlit/all_team_stats_history.parquet")
    return df

@st.cache_data(ttl=86400)
def get_all_time_rosters() -> pd.DataFrame:
    df = pd.read_parquet("SBC_Streamlit/all_time_rosters_history.parquet")
    return df

@st.cache_data(ttl=86400)
def get_fantrax_roster(year, period) -> pd.DataFrame:
    all_rosters_list = []    
    roster_url = f"https://www.fantrax.com/fxea/general/getTeamRosters?leagueId={league_ids.get(year)}&period={period}"
    headers = {'Cookie': 'JSESSIONID='}
    response = requests.get(roster_url, headers=headers)
    if response.status_code == 200:
        roster_json = response.text
        roster_data = json.loads(roster_json)
        rosters = roster_data.get('rosters', {})
        for team_id, roster in rosters.items():
            team_name = roster.get('teamName')
            roster_items = roster.get('rosterItems')
            if roster_items is not None and len(roster_items) > 0:
                roster_df = pd.DataFrame(roster_items)
                roster_df['team_name'] = team_name
                roster_df['period'] = period
                roster_df['team_id'] = team_id
                all_rosters_list.append(roster_df)    
    if all_rosters_list:
        all_rosters_data = pd.concat(all_rosters_list, ignore_index=True)
    else:
        all_rosters_data = pd.DataFrame()
    return all_rosters_data

@st.cache_data()
def get_fantrax_players() -> pd.DataFrame:
    roster_url = "https://www.fantrax.com/fxea/general/getPlayerIds?sport=NBA"
    headers = {'Cookie': 'JSESSIONID='}
    response = requests.get(roster_url, headers=headers)
    if response.status_code == 200:
        data = json.loads(response.text)
        players_list = []
        for player_id, player_info in data.items():
            player_record = player_info.copy()
            players_list.append(player_record)
        players_df = pd.DataFrame(players_list)
        players_df = players_df[['name', 'fantraxId']]
        new_row = pd.DataFrame([{"name": "Bogdanovic, Bojan", "fantraxId": "027pg"}])
        players_df = pd.concat([players_df, new_row], ignore_index=True)
        players_df['name'] = players_df['name'].str.split(', ').str[1] + ' ' + players_df['name'].str.split(', ').str[0]
        players_df.loc[players_df['name'] == 'Amari Bailey', 'fantraxId'] = '06cbt'
        players_df.loc[players_df['name'] == 'Tarik Biberovic', 'fantraxId'] = '06ccr'
        players_df = players_df[players_df['fantraxId'] != "067x0"]
        players_df = players_df[players_df['fantraxId'] != "06ps6"]
    else:
        print(f"Failed to fetch data - Status code: {response.status_code}")
    return players_df

@st.cache_data(ttl=86400)
def get_standings() -> pd.DataFrame:
    df = pd.read_parquet("SBC_Streamlit/all_time_standings.parquet")
    return df

@st.cache_data()
def get_fantrax_matchups(year) -> pd.DataFrame:
    roster_url = f"https://www.fantrax.com/fxea/general/getLeagueInfo?leagueId={league_ids.get(year)}"
    headers = {'Cookie': 'JSESSIONID='}
    response = requests.get(roster_url, headers=headers)
    if response.status_code == 200:
        Matchups = json.loads(response.text)
        df = pd.DataFrame(Matchups)
    else:
        print(f"Failed to fetch data - Status code: {response.status_code}")
    return df

@st.cache_data()
def get_draft_history() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1546613902"
    df = pd.read_csv(csv_url)
    return df

@st.cache_data()
def get_award_history() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/export?format=csv&gid=1698988928"
    df = pd.read_csv(csv_url)
    df = df.melt(id_vars=["Award"], var_name="Year", value_name="Winner")
    df = df[df["Year"].str.isnumeric()] 
    df["Year"] = df["Year"].astype(int)    
    return df

@st.cache_data()
def get_team_award_history() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/export?format=csv&gid=451021615"
    df = pd.read_csv(csv_url)
    df = df.melt(id_vars=["Award"], var_name="Year", value_name="Winner")  
    df = df[df["Year"].str.isnumeric()] 
    df["Year"] = df["Year"].astype(int)    
    return df

@st.cache_data()
def get_all_time_schedule() -> pd.DataFrame:
    df = pd.read_parquet("SBC_Streamlit/all_time_scores.parquet")
    return df

def current_matchup_period() -> float:
    csv_url = "https://docs.google.com/spreadsheets/d/1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/export?format=csv&gid=444367429"
    df = pd.read_csv(csv_url)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df2 = df[(df["Date"] == today) & (df["Year"] == current_year)]
    if len(df2) == 0:
        return int(df["Period"].iloc[-1])
    if len(df2) == 1:
        return int(df2["Period"].iloc[0])
    return int(df2["Period"].iloc[-1])

def get_matchup_stats(year: int, period: int) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json", "Cookie": "JSESSIONID=YOUR_REAL_SESSION_ID"})
    payload = {"msgs": [{"method": "getLiveScoringStats","data": {"sppId": "-1", "teamId": "ALL", "period": period, "date": "2026-01-30", "viewType": "2", "playerViewType": "1", "newView": False}}, {"method": "getScoresSummaryData", "data": {}}]}
    response = session.post("https://www.fantrax.com/fxpa/req", params={"leagueId": league_ids.get(year)}, json=payload)
    if response.status_code == 200:
        data = response.json()
        scoring_categories = ['Team', 'GP', 'MP', 'TS%', '2PTM', '2PTA', '2PT%', '3PTM', '3PTA', '3PT%', 'FTM', 'FTA', 'FT%', 'PTS', 'OREB', 'DREB', 'AST', 'ST', 'BLK', 'TO', '+/-']
        team_id_to_name = {}
        for team_name, years in team_id_history.items():
            for _, team_id in years.items():
                team_id_to_name[team_id] = team_name
        year_key = f"{year}_id"
        team_ids = [ids.get(year_key) for ids in team_id_history.values() if ids.get(year_key)]        
        rows = []
        for team_id in team_ids:
            row = {'Team': team_id}
            team_stats = (
                data['responses'][0]["data"]
                .get('statsPerTeam', {})
                .get('allTeamsStats', {})
                .get(team_id, {})
                .get('ACTIVE', {})
                .get('statsMap', {}))
            stats_list = (
                team_stats
                .get('_3010', {})
                .get('object2', []))
            stats_dict = {
                stat.get('scipId'): stat.get('av')
                for stat in stats_list
                if stat.get('scipId') is not None}
            if year <= 2025:
                for stat_name in scoring_categories[2:]:
                    scipId = stat_to_scipId.get(stat_name)
                    row[stat_name] = stats_dict.get(scipId, 0)
            else:
                for stat_name in scoring_categories[1:]:
                    scipId = stat_to_scipId.get(stat_name)
                    row[stat_name] = stats_dict.get(scipId, 0)
            rows.append(row)
        df = pd.DataFrame(rows, columns=scoring_categories)
        df["Team"] = df["Team"].map(team_id_to_name)
        df.loc[(df["2PTA"] < 10) | (df["3PTA"] < 10) | (df["FTA"] < 5), ['TS%', '2PT%', '3PT%', 'FT%']] = 0
        return df
    else:
        print(f"Error: Request failed for URL with status code {response.status_code}")
        return None

def style_salaries(row, type_colors):
    styles = [""] * len(row)
    for i, col in enumerate(row.index):
        if col.isdigit():
            type_col = f"Type{col}"
            if type_col in row.index:
                contract_type = row[type_col]
                color = type_colors.get(contract_type, None)
                if color:
                    styles[i] = f"background-color: {color}; color: black;"
    return styles

def active_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Active Players']
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def overseas_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Non-Active Players']
    df = df[df["Type" + str(current_year)].isin(['Guaranteed', 'Unguaranteed'])]
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def dead_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Non-Active Players']
    df = df[df["Type" + str(current_year)] == "Dead"]
    df = df[df["Trade.Restriction"] != "Retired"]
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def free_agent_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df["Type" + str(current_year + year_offset)].isin(['Unrestricted', 'Restricted'])]
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year + year_offset), ascending=False)
    return df

def draft_retired_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[(df["Type" + str(current_year)] == 'Draft Rights') | (df['Trade.Restriction'] == 'Retired')]
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def exception_table(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['Team'] == SelectedTeam]
    df = df[df["Y" + str(current_year)] > 0]
    df = df.drop(columns=["Team"])
    df = df.rename(columns={'Player': 'Exception'})
    df = df.rename(columns={"Y" + str(current_year): 'Amount'})
    df = df.rename(columns={'BirdRights': 'Expiration Date'})
    df = df.sort_values('Amount', ascending=False)
    return df

def active_player_n(df: pd.DataFrame, SelectedTeam: str) -> float:
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Active Players']
    return df.shape[0]

def inactive_player_n(df: pd.DataFrame, SelectedTeam: str) -> float:
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Non-Active Players']
    df = df[df["Type" + str(current_year)].isin(['Guaranteed', 'Unguaranteed'])]
    return df.shape[0]

def get_cap_total(df: pd.DataFrame, exceptions_df: pd.DataFrame, SelectedTeam: str) -> float:
    df = df[df['Team'] == SelectedTeam]
    player_total = df["Y" + str(current_year)].sum()
    exceptions_df = exceptions_df[exceptions_df['Team'] == SelectedTeam]
    exceptions_df = exceptions_df[exceptions_df['Player'] != 'Minimum']
    exceptions_total = exceptions_df["Y" + str(current_year)].sum()
    total_cap = player_total + exceptions_total
    ap = 12-active_player_n(df, SelectedTeam)
    if ap > 0:
        min_penalty = minimum_sal * ap
        total_cap = min_penalty + total_cap
    return total_cap

def get_tax_total(df: pd.DataFrame, SelectedTeam: str) -> float:
    df = df[df['Team'] == SelectedTeam]
    player_total = df["Y" + str(current_year)].sum()
    return player_total

def team_hard_cap(df: pd.DataFrame, SelectedTeam: str) -> str:
    df = df[df['Team'] == SelectedTeam]
    hard_cap = df['HardCap'].values[0]
    return hard_cap

def team_hard_cap_n(df: pd.DataFrame, SelectedTeam: str, base_cap: pd.DataFrame) -> str:
    tax_number = get_tax_total(df, SelectedTeam)
    hard_cap_type = team_hard_cap(base_cap, SelectedTeam)
    if hard_cap_type == "None":
        return None
    elif hard_cap_type == "First Apron":
        return tax_number-current_apron_1
    elif hard_cap_type == "Second Apron":
        return tax_number-current_apron_2

def base_fee(df: pd.DataFrame, SelectedTeam: str, base_cap: pd.DataFrame) -> float:
    payment = get_tax_total(df, SelectedTeam)
    payment = current_salary_cap * 0.9 if payment < current_salary_cap * 0.9 else payment
    payment = payment/league_ratio
    base_cap = base_cap[base_cap['Team'] == SelectedTeam]
    rate = base_cap["Rate"].iloc[0]
    payment = payment*rate
    payment = payment+3
    return payment

def luxury_fee(df: pd.DataFrame, SelectedTeam: str, base_cap: pd.DataFrame) -> float:
    df = df[df['Team'] == SelectedTeam]
    tax_number = get_tax_total(df, SelectedTeam)
    tax_number = tax_number-current_luxury_tax
    repeater_penalty = base_cap["Tax2022"].iloc[0] + base_cap["Tax2023"].iloc[0] + base_cap["Tax2024"].iloc[0] + base_cap["Tax2025"].iloc[0]
    repeater_penalty = True if repeater_penalty >= 3 else False
    tax_amount = tax_amount_calc(tax_number, repeater_penalty)
    tax_amount = tax_amount/league_ratio
    base_cap = base_cap[base_cap['Team'] == SelectedTeam]
    rate = base_cap["Rate"].iloc[0]
    tax_amount = tax_amount*rate
    return tax_amount

def tax_amount_calc(fee: float, repeater: bool) -> float:
    penalty_false = [1.0, 0.25, 2.25, 1.25]
    penalty_true = [3.0, 0.25, 2.25, 1.25]
    if fee <= 0:
        return 0
    elif repeater:
        tax = fee * penalty_true[0]
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_true[1])
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_true[2])
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_true[3])
        fee = fee - tax_bracket_increment
        while fee > 0:
            tax = tax + (fee * 0.5)
            fee = fee - tax_bracket_increment
        return tax
    elif not repeater:
        tax = fee * penalty_false[0]
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_false[1])
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_false[2])
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_false[3])
        fee = fee - tax_bracket_increment
        while fee > 0:
            tax = tax + (fee * 0.5)
            fee = fee - tax_bracket_increment
        return tax

def amount_paid(df: pd.DataFrame, SelectedTeam: str) -> float:
    df = df[df['Team'] == SelectedTeam]
    df = df["MoneyPaid"].iloc[0]
    return df

def net_fee(df: pd.DataFrame, SelectedTeam: str, base_cap: pd.DataFrame) -> float:
    fee = base_fee(df, SelectedTeam, base_cap)
    tax = luxury_fee(df, SelectedTeam, base_cap)
    paid = amount_paid(base_cap, SelectedTeam)
    net_fee = tax + fee - paid
    net_fee = -net_fee
    return math.ceil(net_fee * 100) / 100

def trade_restrictions(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Trade.Restriction'].notna()]
    df = df[df['Player'] != "Minimum Salary Penalty"]
    df = df[['Picture_Online','Player','Trade.Restriction']]
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'Trade.Restriction': 'Trade Restriction'})
    df = df.sort_values('Player', ascending=True)
    return df

def active_players_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Type'] == 'Active Players']
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def inactive_players_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Type'] == 'Non-Active Players']
    df = df[df["Type" + str(current_year)].isin(['Guaranteed', 'Unguaranteed'])]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def dead_players_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Type'] == 'Non-Active Players']
    df = df[df["Type" + str(current_year)] == "Dead"]
    df = df[df["Trade.Restriction"] != "Retired"]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def draft_rights_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[(df["Type" + str(current_year)] == 'Draft Rights')]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values('Player', ascending=True)
    return df

def retired_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[(df['Trade.Restriction'] == 'Retired')]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values('Player', ascending=True)
    return df

def all_free_agents(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df["Type" + str(current_year + year_offset)].isin(['Unrestricted', 'Restricted'])]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year + year_offset), ascending=False)
    return df

def trade_restrictions_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Trade.Restriction'].notna()]
    df = df[df['Player'] != "Minimum Salary Penalty"]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df[['Team_logo', 'Picture_Online','Player','Trade.Restriction']]
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'Trade.Restriction': 'Trade Restriction'})
    df = df.sort_values('Player', ascending=True)
    return df

def overall_cap_table(df: pd.DataFrame, exceptions_df: pd.DataFrame, base_cap: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "Logo": [info["logo"] for info in team_info.values()],
        "Team": list(team_info.keys()),
        "Active Players": [active_player_n(df, team) for team in team_info.keys()],
        "Cap Space": [current_salary_cap - get_cap_total(df, exceptions_df, team) for team in team_info.keys()],
        "Tax Space": [current_luxury_tax - get_tax_total(df, team) for team in team_info.keys()],
        "Hard Cap": [team_hard_cap(base_cap, team) for team in team_info.keys()],
        "Apron 1 Space": [current_apron_1 - get_tax_total(df, team) for team in team_info.keys()],
        "Apron 2 Space": [current_apron_2 - get_tax_total(df, team) for team in team_info.keys()],
        "Base Fee": [base_fee(df, team, base_cap) for team in team_info.keys()],
        "Luxury Fee": [luxury_fee(df, team, base_cap) for team in team_info.keys()],
        "Balance": [net_fee(df, team, base_cap) for team in team_info.keys()],
        "Amount Paid": [amount_paid(base_cap, team) for team in team_info.keys()]})
    return df

def unit_payout(df: pd.DataFrame, exceptions_df: pd.DataFrame, base_cap: pd.DataFrame) -> pd.DataFrame:
    df = overall_cap_table(df, exceptions_df, base_cap)
    total_fee = df["Base Fee"].sum()
    total_fee = total_fee-130-100-90
    total_fee = total_fee/24
    return total_fee

def tax_payout_champ(df: pd.DataFrame, exceptions_df: pd.DataFrame, base_cap: pd.DataFrame) -> pd.DataFrame:
    df = overall_cap_table(df, exceptions_df, base_cap)
    total_fee = df["Base Fee"].sum()
    total_fee = total_fee/2
    return total_fee

def tax_payout_split(df: pd.DataFrame, exceptions_df: pd.DataFrame, base_cap: pd.DataFrame) -> pd.DataFrame:
    df = overall_cap_table(df, exceptions_df, base_cap)
    total_fee = df["Base Fee"].sum()
    total_fee = total_fee/2
    total_fee = total_fee / (df["Luxury Fee"] == 0).sum()
    return total_fee

def style_overall_cap(row):
    styles = [""] * len(row)
    for i, col in enumerate(row.index):
        value = row[col]
        if col == "Active Players":
            if 15 <= value <= 17:
                styles[i] = "color: #F9A01B;"
            elif value <= 11 or value >= 18 or value == 0:
                styles[i] = "color: red;"
        elif col in ["Cap Space", "Tax Space"]:
            color = "green" if value > 0 else "red"
            styles[i] = f"color: {color};"
        elif col == "Hard Cap":
            if value in ["Second Apron", "First Apron"]:
                styles[i] = "color: #F9A01B;"
        elif col == "Apron 1 Space":
            if value < 0:
                styles[i] = "color: red;"
            elif row.get("Hard Cap") == "First Apron":
                styles[i] = "color: #F9A01B;"
        elif col == "Apron 2 Space":
            if value < 0:
                styles[i] = "color: red;"
            elif row.get("Hard Cap") == "Second Apron":
                styles[i] = "color: #F9A01B;"
        elif col == "Balance":
            color = "green" if value > -0.005 else "red"
            styles[i] = f"color: {color};"
    return styles

def full_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['FullyOwned']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df[df['PickSwap'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def swap_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['PickSwap']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def split_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['FullyOwned'] == False]  # noqa: E712
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def locked_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['Locked']]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def original_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['OGTeam'] == SelectedTeam) & (df['CurrentTeam'].str.contains(SelectedTeam) == False)]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def touched_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['TeamTouched'].str.contains(SelectedTeam, na=False))]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def all_full_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['FullyOwned']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df[df['PickSwap'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def all_swap_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['PickSwap']]
    df = df[df['FullyOwned']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def all_split_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['FullyOwned'] == False]  # noqa: E712
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.rename(columns={'CurrentTeam': 'Potential Owners'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def all_locked_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['Locked']]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def data_picture_check(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Picture_Online'].isna()]
    df = df[['Player', 'Picture_Online']]
    df = df.rename(columns={'Picture_Online': 'Picture'})
    return df

def data_roster_check(df: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "Team": list(team_info.keys()),
        "Active Players": [active_player_n(df, team) for team in team_info.keys()]})
    df = df[(df['Active Players'] > 17) | (df['Active Players'] < 12)]
    return df

def data_missing_salary_check(df: pd.DataFrame) -> pd.DataFrame:
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team', 'Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    year_cols = [f"Y{year}" for year in columns_order]
    type_cols = [f"Type{year}" for year in columns_order]
    salary_long = df.melt(id_vars = ["Team", "Player"], value_vars = year_cols, var_name = "Year", value_name = "Salary")
    salary_long["Year"] = salary_long["Year"].str.replace("Y", "", regex=False)
    type_long = df.melt(id_vars = ["Team", "Player"], value_vars = type_cols, var_name = "Year",  value_name = "Type")
    type_long["Year"] = type_long["Year"].str.replace("Type", "", regex=False)
    long_df = salary_long.merge(type_long,on=["Team", "Player", "Year"], how="left")
    df = long_df[long_df["Type"].notna() & long_df["Salary"].isna()]
    return df

def hard_cap_check(df: pd.DataFrame, base_cap: pd.DataFrame) -> str:
    df = pd.DataFrame({
        "Team": team_info.keys(),
        "HardCapResult": [team_hard_cap_n(df, team, base_cap) for team in team_info.keys()]})
    df = df[df['HardCapResult'] > 0]
    df["HardCapResult"] = df["HardCapResult"].apply(lambda x: f"${x:,.0f}")
    df = df.rename(columns={'HardCapResult': 'Over Amount'})
    return df

def stepien_data_check(df: pd.DataFrame) -> pd.DataFrame:
    df = get_draft_picks()


    df2 = pd.DataFrame({
        "Year": [current_year-1] * 30,
        "Round": ["1st Round"] * 30,
        "CurrentTeam": list(team_info.keys())
    })
    df = df[(df['FullyOwned']) | (df['Locked']) | (df['TwoYearLimit'])]
    df['Year'] = np.where(df['TwoYearLimit'], df['Year'] + 0.5, df['Year'])
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes','OGTeam','TeamTouched','Explanation', 'TwoYearLimit'])
    df = df[df['Round'] == "1st Round"]
    df = df.assign(CurrentTeam=df['CurrentTeam'].str.split(', ')) \
       .explode('CurrentTeam') \
       .reset_index(drop=True)
    df = pd.concat([df2, df], ignore_index=True)
    df = df.sort_values(["CurrentTeam", "Year"])
    df["next_year"] = df.groupby("CurrentTeam")["Year"].shift(-1)
    df["next_year"] = df["next_year"].fillna(current_year + 7)
    df["gap"] = df["next_year"] - df["Year"]
    mask = ((df["Year"] % 1 == 0.5) & (df["next_year"] % 1 == 0.5) & (df["gap"] == 2))
    df.loc[mask, "gap"] = 3
    df = df[df["gap"] > 2]
    df = df[['CurrentTeam', 'Year','next_year']]
    df = df.rename(columns={'CurrentTeam': 'Team'})
    df = df.rename(columns={'year': 'Gap Open'})
    df = df.rename(columns={'next_year': 'Gap Closed'})
    return df

def tradeable_players_out(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Trade.Restriction'].isna()]
    df = df[['Player']]
    df = df.sort_values('Player', ascending=True)
    df_list = df['Player'].tolist()
    return df_list

def tradeable_players_in(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df[df['Team'] != SelectedTeam]
    df = df[df['Trade.Restriction'].isna()]
    df = df[['Player']]
    df = df.sort_values('Player', ascending=True)
    df_list = df['Player'].tolist()
    return df_list

def tradeable_picks_out(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['CurrentTeam'].str.contains(SelectedTeam)]
    df = df[df['Locked'] == False] #noqa: E712
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df.sort_values('Pick', ascending=True)
    df_list = df['Pick'].tolist()
    return df_list

def tradeable_picks_in(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam)) == False]  # noqa: E712
    df = df[df['Locked'] == False]  # noqa: E712
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df.sort_values('Pick', ascending=True)
    df_list = df['Pick'].tolist()
    return df_list

def tradeable_exceptions_in(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df[df["Y" + str(current_year)] > 0]
    df = df[df["Player"] != "Minimum"]
    df = df[df["Team"] != SelectedTeam]
    df["Exception"] = (df["Team"].astype(str) + " " + df["Player"].astype(str))
    df = df.sort_values('Exception', ascending=True)
    df_list = df['Exception'].tolist()
    df_list.append("Minimum")
    return df_list

def tradeable_exceptions_out(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df[df["Y" + str(current_year)] > 0]
    df = df[df["Player"] != "Minimum"]
    df = df[df["Team"] == SelectedTeam]
    df["Exception"] = (df["Team"].astype(str) + " " + df["Player"].astype(str))
    df = df.sort_values('Exception', ascending=True)
    df_list = df['Exception'].tolist()
    df_list.append("Minimum")
    return df_list

def players_out_table(df: pd.DataFrame, pics: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Player'].isin(selected_players)]
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def players_in_table(df: pd.DataFrame, pics: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Player'].isin(selected_players)]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def picks_out_table(df: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df = df.drop(columns=["TwoYearLimit"])
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df[df['Pick'].isin(selected_players)]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes', 'TeamTouched','Pick'])
    df["CurrentTeam"] = df["CurrentTeam"].apply(lambda x: team_info.get(x.split(",")[0].strip(), {}).get("logo", ""))
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def picks_in_table(df: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df = df.drop(columns=["TwoYearLimit"])
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df[df['Pick'].isin(selected_players)]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes', 'TeamTouched','Pick'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def exceptions_in_table(df: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df["Exception"] = (df["Team"].astype(str) + " " + df["Player"].astype(str))
    df = df[df['Exception'].isin(selected_players)]
    df["Team"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.drop(columns=['Exception'])
    df = df.rename(columns={'Player': 'Exception'})
    df = df.rename(columns={"Y" + str(current_year): str(current_year)})
    df[str(current_year)] = df[str(current_year)].apply(lambda x: f"${x:,.0f}")
    df = df.rename(columns={'BirdRights': 'Expiration Date'})
    df = df.sort_values('Team', ascending=True)
    df = df.sort_values('Exception', ascending=True)
    return df

def exceptions_out_table(df: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df["Exception"] = (df["Team"].astype(str) + " " + df["Player"].astype(str))
    df = df[df['Exception'].isin(selected_players)]
    df = df.drop(columns=['Exception'])
    df = df.rename(columns={'Player': 'Exception'})
    df = df.rename(columns={"Y" + str(current_year): str(current_year)})
    df[str(current_year)] = df[str(current_year)].apply(lambda x: f"${x:,.0f}")
    df = df.rename(columns={'BirdRights': 'Expiration Date'})
    df = df.drop(columns=['Team'])
    df = df.sort_values('Exception', ascending=True)
    return df

def net_players_check(df: pd.DataFrame, SelectedTeam: str, selected_players_in: list[str], selected_players_out: list[str]) -> float:
    n_in = df[df['Player'].isin(selected_players_in)]
    n_in = n_in[df['Type'] == "Active Players"]
    n_in = len(n_in)
    n_out = df[df['Player'].isin(selected_players_out)]
    n_out = n_out[df['Type'] == "Active Players"]
    n_out = len(n_out)
    current_players = active_player_n(df, SelectedTeam)
    current_players = current_players-n_out+n_in
    if current_players > 17:
        excess_players = current_players - 17
        st.error(f"Roster exceeds the maximum limit of 17 players. You would need to cut at least {excess_players} player(s) to comply with roster rules.", icon = "❌")
    elif 15 <= current_players <= 17:
        st.warning("Roster is within 15-17 players. Ensure you have sufficient IR-eligible players to maintain compliance and flexibility.", icon = "✅")
    elif 12 <= current_players <= 14:
        st.success(f"Roster size of {current_players} players is within the standard limits. No immediate action required.", icon = "✅")
    elif current_players < 12:
        players_needed = 12 - current_players
        st.warning(f"Roster is below the minimum limit of 12 players. You need to sign at least {players_needed} player(s) to comply with roster requirements.", icon = "✅")
    return current_players

def check_cash_after(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str) -> str:
    team_total = get_tax_total(df, SelectedTeam)
    df1 = df[df['Player'].isin(PlayersIn)]
    df1 = df1["Y" + str(current_year)].sum()
    df2 = df[df['Player'].isin(PlayersOut)]
    df2 = df2["Y" + str(current_year)].sum()
    team_total = team_total - df2 + df1
    if team_total < current_salary_cap:
        return "Cap"
    elif current_salary_cap <= team_total < current_luxury_tax:
        return "Standard"
    elif current_luxury_tax <= team_total < current_apron_1:
        return "Tax"
    elif current_apron_1 <= team_total < current_apron_2:
        return "First"
    else:
        return "Second" #ABC

def no_cash(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame, CashOut: float):
    try:
        CashOut = float(CashOut) 
    except (TypeError, ValueError):
        CashOut = 0.0
    if np.isnan(CashOut):
        CashOut = 0.0
    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
    HardCap = team_hard_cap(base_cap, SelectedTeam)
    if CapType == "Second" and CashOut > 0:
        st.error("This transaction is not permitted. Teams above the Second Apron are prohibited from sending out cash in a trade.", icon="❌")
    elif HardCap in ["First Apron", "No Cap"] and CashOut > 0:
        st.warning("Sending out cash in this trade will hard cap your team at the Second Apron for the remainder of the season. Please proceed with caution.", icon="✅")
    elif CashOut > 0:
        st.success("There are no cap-related restrictions preventing you from sending out cash in this trade.",icon="✅")
    else:
        st.success("No outgoing cash was included in this transaction.",icon="✅")

def tpe_st_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame, SelectedExceptionOut: list[str]):
    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
    HardCap = team_hard_cap(base_cap, SelectedTeam)
    flagged = any("S&T" in exc for exc in SelectedExceptionOut)
    if CapType == "Second" and flagged == 1:
        st.error("This transaction is not permitted. Teams operating above the Second Apron are prohibited from acquiring players via a Traded-Player Exception created from a Sign-And-Trade.", icon="❌")
    elif HardCap in ["First Apron", "No Cap"] and flagged == 1:
        st.warning("This transaction utilizes an outgoing Traded-Player Exception created via a Sign-And-Trade. As a result, your team will be hard-capped at the Second Apron for the remainder of the season.", icon="✅")
    elif flagged == 1:
        st.success("There are no cap-related restrictions preventing your team from using a Traded-Player Exception created from a Sign-And-Trade", icon="✅")
    else: 
        st.success("This transaction does not utilize a Traded-Player Exception created from a Sign-And-Trade to acquire a player.", icon="✅")

#def no_aggregation_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: no_aggregation_check", icon = "⚠️")
#    return "A"

def under_100_percent_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame, SelectedExceptionOut: list[str]):
    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
    HardCap = team_hard_cap(base_cap, SelectedTeam)
    df1 = df[df['Player'].isin(PlayersIn)]
    df1 = df1["Y" + str(current_year)].sum()
    df2 = df[df['Player'].isin(PlayersOut)]
    df2 = df2["Y" + str(current_year)].sum()
    Diff = df1 / df2 if df2 != 0 else 1000
    if len(PlayersIn) == 1 and len(PlayersOut) == 0 and len(SelectedExceptionOut) == 1:
        if "Minimum" in SelectedExceptionOut[0]:
            if df1 < max_minimum:
                Diff = 1.0
    if CapType in ["First", "Second"] and Diff > 1:
        st.error("This transaction is not permitted. Teams above the First Apron are not allowed to take back more than 100% of outgoing salary, unless the incoming player is on a minimum contract.", icon="❌")
    elif HardCap in ["No Cap"] and Diff > 1:
        st.warning("This transaction is allowed, but taking back more than 100% of outgoing salary will hard-cap your team at the First Apron for the remainder of the season.", icon="✅")
    elif Diff > 1:
        st.success("There are no cap-related restrictions preventing your team from taking back more than 100% of outgoing salary.", icon="✅")
    else: 
        st.success("Your team is taking back less than or equal to 100% of outgoing salary. No further action is required.", icon="✅")

def no_bae_mle_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame, SelectedExceptionOuts: list[str]):
    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
    HardCap = team_hard_cap(base_cap, SelectedTeam)
    flagged = any("Bi-Annual" in exc or "Mid-Level" in exc for exc in SelectedExceptionOuts)
    if CapType in ["First", "Second"] and flagged == 1:
        st.error("This transaction is not permitted. Teams operating above the First Apron are prohibited from trading for players via the Bi-Annual Exception (BAE) or Mid-Level Exception (MLE).", icon="❌")
    elif HardCap in ["No Cap"] and flagged == 1:
        st.warning("This transaction utilizes an outgoing Bi-Annual Exception (BAE) or Mid-Level Exception (MLE). As a result, your team will be hard-capped at the First Apron for the remainder of the season.", icon="✅")
    elif flagged == 1:
        st.success("There are no cap-related restrictions preventing your team from using the Bi-Annual Exception (BAE) or Mid-Level Exception (MLE) to acquire a player.",icon="✅")
    else: 
        st.success("This transaction does not utilize the Bi-Annual Exception (BAE) or Mid-Level Exception (MLE) to acquire a player.",icon="✅")

#def salary_trade_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: salary_trade_check", icon = "⚠️")
#    return "A"

#def tpe_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: tpe_check", icon = "⚠️")
#    return "A"

#def bae_mle_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: bae_mle_check", icon = "⚠️")
#    return "A"

#def player_agg_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: player_agg_check", icon = "⚠️")
#    return "A"

#def create_tpe_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: create_tpe_check", icon = "⚠️")
#    return "A"

#def new_trade_rest_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: new_trade_rest_check", icon = "⚠️")
#    return "A"

#def old_team_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: old_team_check", icon = "⚠️")
#    return "A"

def stepien_check(dp: pd.DataFrame, DraftPicksIn: list[str], DraftPicksOut: list[str], SelectedTeam: str):
    return "A"

def fantrax_players_check(df: pd.DataFrame, ft_players: pd.DataFrame, ft_roster: pd.DataFrame) -> pd.DataFrame:
    df['Player'] = df['Player'].replace(cap_sheets_to_fantrax_name_fix)
    df = df[df['Player'] != "Minimum Salary Penalty"]
    df = df[df['Trade.Restriction'] != "Dead"]
    df = df[df['Trade.Restriction'] != "Banned"]
    df = df.merge(ft_players, how='left', left_on='Player', right_on='name')
    df = df.merge(ft_roster, how='outer', left_on='fantraxId', right_on='id')
    df = df[df['Player'].isna() | df['team_name'].isna()]
    df = df.rename(columns={'Player': 'Cap Sheet Name'})
    df = df.rename(columns={'name': 'Fantrax Name'})
    df = df[['Cap Sheet Name', 'Fantrax Name', 'id', 'team_name']]
    return df

def fantrax_roster_check(df: pd.DataFrame, ft_players: pd.DataFrame, ft_roster: pd.DataFrame) -> pd.DataFrame:
    df['Player'] = df['Player'].replace(cap_sheets_to_fantrax_name_fix)
    df = df[df['Player'] != "Minimum Salary Penalty"]
    df = df[df['Trade.Restriction'] != "Dead"]
    df = df[df['Trade.Restriction'] != "Banned"]
    df = df.merge(ft_players, how='left', left_on='Player', right_on='name')
    df = df.merge(ft_roster, how='outer', left_on='fantraxId', right_on='id')
    df['status2'] = df['status'].apply(lambda x: "Non-Active Players" if x == "MINORS" else "Active Players")
    df = df[df['Type'] != df["status2"]]
    df = df[['Player', 'team_name', 'Type', 'status']]
    df = df.rename(columns={'Type': 'Cap Sheet Location'})
    df = df.rename(columns={'status': 'Fantrax Locatoin'})
    return df

def fantrax_positional_check(df: pd.DataFrame, ft_players: pd.DataFrame, ft_rosters: pd.DataFrame) -> pd.DataFrame:
    df = get_data()
    df_players = pd.DataFrame({
        "Team": list(team_info.keys()),
        "Active Players": [active_player_n(df, team) for team in team_info.keys()],})
    df['Player'] = df['Player'].replace(cap_sheets_to_fantrax_name_fix)
    df = df[df['Type'] == "Active Players"]
    df = df.merge(ft_players, how='left', left_on='Player', right_on='name')
    df = df.merge(ft_rosters, how='outer', left_on='fantraxId', right_on='id')

    df_ir = df[df['status'] == "INJURED_RESERVE"]
    df_ir = df_ir.groupby(['Team']).size().reset_index(name='Total')
    df_ir = df_ir.merge(df_players, how='left', left_on='Team', right_on='Team')
    df_ir['Count'] = df_ir['Active Players'] - df_ir['Total']
    df_ir = df_ir[df_ir['Count'] > 14]
    df_ir['Type'] = "IR"
    df_ir = df_ir[['Team', 'Type']]

    df_starters = df[df['status'] == "ACTIVE"]
    df_starters = df_starters[df_starters['position'].isin(['PG', 'SG', 'SF', 'PF', 'C'])]
    df_starters = df_starters.groupby(['Team','position']).size().reset_index(name='Total')
    df_starters = df_starters[df_starters['Total'] > 1]
    df_starters['Type'] = "Starters"
    df_starters = df_starters[['Team', 'Type']]

    df_flex = df[df['status'] == "ACTIVE"]
    df_flex = df_flex[df_flex['position'] == "Flx"]
    df_flex = df_flex.groupby(['Team']).size().reset_index(name='Total')
    df_flex = df_flex[df_flex['Total'] > 3]
    df_flex['Type'] = "Flex"
    df_flex = df_flex[['Team', 'Type']]

    df_reserve = df[df['status'] == "RESERVE"]
    df_reserve = df_reserve.groupby(['Team']).size().reset_index(name='Total')
    df_reserve = df_reserve[df_reserve['Total'] > 6]
    df_reserve['Type'] = "Reserve"
    df_reserve = df_reserve[['Team', 'Type']]

    df = pd.concat([df_ir, df_starters, df_flex, df_reserve], ignore_index=True)
    return df

def current_draft(df: pd.DataFrame, dp: pd.DataFrame, round: str) -> pd.DataFrame:
    required_standings = {"Year", "Period", "Record", "Team"}
    required_picks = {"Year", "Round", "OGTeam", "CurrentTeam", "Explanation"}
    if not required_standings.issubset(df.columns) or not required_picks.issubset(dp.columns):
        return pd.DataFrame(columns=["Pick", "Slot", "Team", "Explanation", "Time Due (ET)"])
    df = df[(df['Year'] == current_year) & (df['Period'] == 99)]
    if df.empty:
        return pd.DataFrame(columns=["Pick", "Slot", "Team", "Explanation", "Time Due (ET)"])
    df[['Wins', 'Losses']] = df['Record'].str.split('-', expand=True).astype(int)
    df['winPercentage'] = df['Wins'] / (df['Wins'] + df['Losses'])    
    df = df[['Team', 'winPercentage']]
    dp = dp[dp['Year'] == current_year].copy()
    dp = dp[dp['Round'] == round].copy()
    order_col = "CurrentTeam"
    dp["_DraftOrderTeam"] = dp[order_col].astype(str).str.split(",").str[0].str.strip()
    dp = dp.merge(df, how = 'left', left_on = '_DraftOrderTeam', right_on = 'Team')
    dp = dp.sort_values('winPercentage', ascending=True)
    pick_start = 1 if round == "1st Round" else 31
    dp['Pick'] = range(pick_start, pick_start + dp.shape[0])
    draft_times = ["10:30 AM", "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM","1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM", "5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM", "8:00 PM", "8:30 PM", "9:00 PM", "9:30 PM", "10:00 PM", "10:30 PM", "11:00 PM", "11:30 PM", "12:00 AM", "12:30 AM", "1:00 AM"]
    dp["Time Due (ET)"] = [draft_times[i % len(draft_times)] for i in range(dp.shape[0])]
    dp = dp[['Pick', '_DraftOrderTeam', 'CurrentTeam', 'Explanation', 'Time Due (ET)']]
    dp = dp.rename(columns={'_DraftOrderTeam': 'OGTeam'})
    dp = dp.rename(columns={'OGTeam': 'Slot'})
    dp = dp.rename(columns={'CurrentTeam': 'Team'})
    return dp

def past_draft(df: pd.DataFrame, pics: pd.DataFrame, dh: pd.DataFrame, year: float, round: float) -> pd.DataFrame:
    dh = dh[dh['Year'] == year]
    dh = dh[dh['Round'] == round]
    df = df[df["Type" + str(current_year)] != "Dead"]
    dh = dh.merge(df[['Player', 'Team']], on='Player', how='left')
    dh = dh.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    dh = dh.drop(columns=["Year",'Round'])
    dh["Drafted Team Name"] = dh["Team_x"]
    dh["Current Team Name"] = dh["Team_y"]
    dh["Drafted Team"] = dh["Team_x"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    dh["Current Team"] = dh["Team_y"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    dh = dh[['Pick', 'Drafted Team Name', 'Drafted Team', 'Player', 'Picture_Online', 'Current Team Name', 'Current Team']]
    return dh

def lottery_table(standings: pd.DataFrame) -> pd.DataFrame:
    for city, info in team_info.items():
        standings.loc[standings["Team"].str.startswith(city), "conference"] = info["conf"]
    standings = standings[(standings['Year'] == current_year) & (standings['Period'] == 99)]
    standings[['Wins', 'Losses']] = standings['Record'].str.split('-', expand=True).astype(int)
    standings['winPercentage'] = standings['Wins'] / (standings['Wins'] + standings['Losses'])    
    standings = standings[['Team', 'winPercentage','conference']]
    standings["Conf_Rank"] = (standings.groupby("conference")["winPercentage"].rank(method="first", ascending=False).astype(int))
    standings = standings[standings['Conf_Rank'] >= 9]
    standings = standings.sort_values("winPercentage", ascending=True)
    items = list(range(1, 15)) 
    combos = list(combinations(items, 4))
    df = pd.DataFrame(combos, columns=["Lowest Ball", "Lower Ball", "Higher Ball", "Highest Ball"])
    df["Ownership"] = np.concatenate([
        #np.repeat(standings["Team"].iloc[0], 140),
        np.repeat("El Paso", 140),
        np.repeat("Little Rock", 140),
        np.repeat("Tulsa (Top 3), Else El Paso", 140),
        np.repeat("Tulsa 2", 115),
        np.repeat("Austin", 115),
        np.repeat("Nashville", 83),
        np.repeat("Manchester", 82),
        np.repeat("San Jose", 60),
        np.repeat("Jacksonville", 45),
        np.repeat("Vegas", 30),
        np.repeat("Birmingham", 20),
        np.repeat("Buffalo", 15),
        np.repeat("Albuquerque", 10),
        np.repeat("Des Moines", 5),
        np.repeat("Redraw", 1)])
    return df

def format_live_stats_df(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if col == 'Team':
            continue
        if col in ['TS%', '2PT%', '3PT%', 'FT%']:
            df.iloc[0, df.columns.get_loc(col)] = f"{float(df.iloc[0][col]) * 100:.2f}"
        elif col == 'MP':
            minutes = float(df.iloc[0][col])
            mins = int(minutes)
            secs = int((minutes - mins) * 60)
            df.iloc[0, df.columns.get_loc(col)] = f"{mins}:{secs:02d}"
        elif col == '+/-':
            val = float(df.iloc[0][col])
            df.iloc[0, df.columns.get_loc(col)] = f"{val:+.1f}"
        else: 
            df.iloc[0, df.columns.get_loc(col)] = f"{float(df.iloc[0][col]):.0f}"
    return df

def team_with_ranks(df: pd.DataFrame, SelectedTeam: str, SelectedYear: int, SelectedPeriod: int) -> pd.DataFrame:
    # --- Select numeric stat columns ---
    stat_cols = df.select_dtypes("number").columns.tolist()
    if SelectedYear <= 2025 and 'GP' in stat_cols:
        stat_cols.remove('GP')

    # --- Get team row safely ---
    team_row = df[df["Team"] == SelectedTeam]
    if team_row.empty:
        raise ValueError(f"Team '{SelectedTeam}' not found in dataframe.")

    team_idx = team_row.index[0]

    # --- Compute ranks (numeric) ---
    ranks = df[stat_cols].rank(ascending=False, method="min")

    # Keep numeric ranks for logic
    team_ranks = ranks.loc[team_idx].copy()

    # Create separate display version (strings)
    team_ranks_display = pd.Series(index=team_ranks.index, dtype="object")

    # --- Build rank strings ---
    for col in team_ranks.index:
        rank_val = int(team_ranks[col])
        is_tied = (ranks[col] == rank_val).sum() > 1

        # ordinal suffix
        if 11 <= rank_val % 100 <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(rank_val % 10, 'th')

        rank_str = f"{rank_val}{suffix}"
        team_ranks_display[col] = f"T-{rank_str}" if is_tied else rank_str

    # --- Combine stats + ranks ---
    out = pd.concat(
        [team_row[stat_cols].reset_index(drop=True),
         team_ranks_display.to_frame().T],
        ignore_index=True
    )

    # --- Add team column (logos) ---
    out.insert(0, "Team", [SelectedTeam, None])
    out["Team"] = out["Team"].map(lambda t: team_info.get(t, {}).get("logo", "") if t else "")

    return out

def team_stats_line_chart(df: pd.DataFrame, SelectedTeam: str, SelectedCategory: str, SelectedYear: int, SelectedMatchup: int) -> alt.Chart:
    df_year = df[df["Year"] == SelectedYear]
    df_year = df_year[df_year["MP"] != 0]
    league_median = (df_year
        .groupby("Period", as_index=False)[SelectedCategory]
        .median()
        .assign(Series="League Median"))
    team_series = (df_year[df_year["Team"] == SelectedTeam]
        .loc[:, ["Period", SelectedCategory]]
        .assign(Series=SelectedTeam))    
    plot_df = pd.concat([league_median, team_series], ignore_index=True)
    chart = (alt.Chart(plot_df)
        .mark_line(strokeWidth=2.5, interpolate='monotone')
        .encode(x=alt.X("Period:O", title="Period", axis=alt.Axis(labelAngle=0, labelFontSize=11, titleFontSize=12, titlePadding=10, grid=False)),
                y=alt.Y(f"{SelectedCategory}:Q", title=SelectedCategory, scale=alt.Scale(zero=False),
                axis=alt.Axis(labelFontSize=11, titleFontSize=12, titlePadding=10, gridOpacity=0.3)),
                color=alt.Color("Series:N", scale=alt.Scale(domain=["League Median", SelectedTeam], range=["#8B8B8B", "#3B82F6"]),
                legend=alt.Legend(title=None, orient="top", labelFontSize=11, symbolSize=100, symbolStrokeWidth=2.5)),
                tooltip=[alt.Tooltip("Series:N", title=""), alt.Tooltip("Period:O", title="Period"), alt.Tooltip(f"{SelectedCategory}:Q", title=SelectedCategory, format=".1f")])
        .properties(height=450))
    team_points = (alt.Chart(team_series)
        .mark_circle(size=80, opacity=1)
        .encode(x="Period:O", y=f"{SelectedCategory}:Q", color=alt.value("#3B82F6"), tooltip=[alt.Tooltip("Period:O", title="Period"), alt.Tooltip(f"{SelectedCategory}:Q", title=SelectedCategory, format=".1f")]))
    return (chart + team_points).configure_view(strokeWidth=0).configure_axis(domainColor="#E5E7EB", tickColor="#E5E7EB")

def matchup_scoreboard(df: pd.DataFrame, SelectedTeam: str, SelectedYear: int, SelectedPeriod: int, Opponent: str) -> pd.DataFrame:
    team1 = team_with_ranks(df, SelectedTeam, SelectedYear, SelectedPeriod)
    team2 = team_with_ranks(df, Opponent, SelectedYear, SelectedPeriod)
    for col in team1.columns:
        if col == 'Team':
            continue
        if col in ['TS%', '2PT%', '3PT%', 'FT%']:
            # Multiply by 100 and format
            team1.iloc[0, team1.columns.get_loc(col)] = f"{float(team1.iloc[0][col]) * 100:.2f}"
            team2.iloc[0, team2.columns.get_loc(col)] = f"{float(team2.iloc[0][col]) * 100:.2f}"
        elif col == 'MP':
            minutes1 = float(team1.iloc[0][col])
            mins1 = int(minutes1)
            secs1 = int((minutes1 - mins1) * 60)
            team1.iloc[0, team1.columns.get_loc(col)] = f"{mins1}:{secs1:02d}"
            minutes2 = float(team2.iloc[0][col])
            mins2 = int(minutes2)
            secs2 = int((minutes2 - mins2) * 60)
            team2.iloc[0, team2.columns.get_loc(col)] = f"{mins2}:{secs2:02d}"
        elif col == '+/-':
            val1 = float(team1.iloc[0][col])
            val2 = float(team2.iloc[0][col])
            team1.iloc[0, team1.columns.get_loc(col)] = f"{val1:+.1f}"
            team2.iloc[0, team2.columns.get_loc(col)] = f"{val2:+.1f}"
        else: 
            team1.iloc[0, team1.columns.get_loc(col)] = f"{float(team1.iloc[0][col]):.0f}"
            team2.iloc[0, team2.columns.get_loc(col)] = f"{float(team2.iloc[0][col]):.0f}"
    team1_scores = team1.iloc[0]
    team2_scores = team2.iloc[0]
    scores = pd.concat([team1_scores, team2_scores], axis=1).T
    green = '#6B9B6B'
    yellow = '#D4B963'
    red = '#CC8888'
    def get_color(col, reverse=False):
        val1 = scores.iloc[0][col]
        val2 = scores.iloc[1][col]
        if col == 'MP':
            def mp_to_float(v):
                mins, secs = v.split(':')
                return int(mins) + int(secs) / 60
            n1, n2 = mp_to_float(val1), mp_to_float(val2)
        else:
            n1, n2 = float(val1), float(val2)
        if n1 > n2:
            return green if not reverse else red
        elif n1 == n2:
            return yellow
        else:
            return red if not reverse else green    
    Color1 = get_color('MP')
    Color2 = get_color('TS%')
    Color3 = get_color('2PT%')
    Color4 = get_color('3PT%')
    Color5 = get_color('FT%')
    Color6 = get_color('PTS')
    Color7 = get_color('OREB')
    Color8 = get_color('DREB')
    Color9 = get_color('AST')
    Color10 = get_color('ST')
    Color11 = get_color('BLK')
    Color12 = get_color('+/-')
    Color13 = get_color('TO', reverse=True)
    def style_matchup(row):
        styles = [""] * len(row)
        color_map = {'MP': Color1, 'TS%': Color2, '2PT%': Color3, '3PT%': Color4, 'FT%': Color5, 'PTS': Color6, 'OREB': Color7, 'DREB': Color8, 'AST': Color9, 'ST': Color10, 'BLK': Color11, '+/-': Color12, 'TO': Color13}
        for i, col in enumerate(row.index):
            if col in color_map:
                styles[i] = f"background-color: {color_map[col]};"
        return styles
    styled_team2 = team2.style.apply(style_matchup, axis=1)
    return styled_team2

def get_opponents(df: pd.DataFrame, SelectedTeam: str, SelectedYear: int, SelectedPeriod: int, Type: str) -> list:    
    filtered = df[(df["Type"] == Type) & (df["Year"] == SelectedYear) & (df["Period"] == SelectedPeriod)].copy()
    filtered = filtered[(filtered["TeamA"].str.contains(SelectedTeam)) | (filtered["TeamB"].str.contains(SelectedTeam))]
    opponents = []
    for _, row in filtered.iterrows():
        if SelectedTeam in row["TeamA"]:
            opponents.append(row["TeamB"])
        else:
            opponents.append(row["TeamA"])
    return opponents

def get_transactions(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    team_df = df[df["team_name"].str.startswith(SelectedTeam, na=False)].copy()
    time_periods = df[['Year', 'period']].drop_duplicates().sort_values(['Year', 'period'])
    time_periods['time_seq'] = range(len(time_periods))
    team_df = team_df.merge(time_periods, on=['Year', 'period'], how='left')
    team_df = team_df.sort_values(['id', 'time_seq'])
    team_df['prev_time_seq'] = team_df.groupby('id')['time_seq'].shift(1)
    team_df['time_gap'] = team_df['time_seq'] - team_df['prev_time_seq']
    team_df['transaction_type'] = None
    team_df.loc[team_df['prev_time_seq'].isna(), 'transaction_type'] = 'joined' 
    team_df.loc[team_df['time_gap'] > 1, 'transaction_type'] = 'joined'
    team_df['next_time_seq'] = team_df.groupby('id')['time_seq'].shift(-1)
    team_df['next_gap'] = team_df['next_time_seq'] - team_df['time_seq']
    team_df.loc[team_df['next_time_seq'].isna(), 'transaction_type'] = 'left'
    team_df.loc[team_df['next_gap'] > 1, 'transaction_type'] = 'left'
    team_df = team_df[team_df['transaction_type'].notna()][['id', 'team_name', 'period', 'Year', 'transaction_type']]
    return team_df

def send_discord_message(DISCORD_WEBHOOK_URL: str, message: str):
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()

def get_single_award(df: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame, df4: pd.DataFrame, Year: int, Award: str) -> pd.DataFrame:
    df = df[df["Award"] == Award]
    df = df[df["Year"] == Year]
    df = df.copy()
    df2 = df2.copy()
    df4 = df4.copy()
    df["_player_key"] = df["Winner"].apply(normalize_player_key)
    df2["_player_key"] = df2["name"].apply(normalize_player_key)
    df4["_player_key"] = df4["Player"].apply(normalize_player_key)
    df = df.merge(df2, how="left", on="_player_key")
    df3 = df3[df3["Year"] == Year]
    df3 = df3[df3["period"] == df3["period"].max()]
    df = df.merge(df3, how="left", left_on="fantraxId", right_on="id")
    df = df.merge(df4, how="left", on="_player_key")
    def get_team_logo(team_name, team_info):
        for city, info in team_info.items():
            full_name = f"{city} {info['nickname']}"
            if team_name == full_name:
                return info["logo"]
        return None 
    df["logo"] = df["team_name"].apply(lambda x: get_team_logo(x, team_info))
    df = df[["logo", "Winner", "Picture_Online"]]
    df = df.sort_values("Winner")
    return df

def get_team_award(df: pd.DataFrame, Year: int, Award: str) -> str:
    df = df[df["Award"] == Award]
    df = df[df["Year"] == Year]
    winner = df.iloc[0]["Winner"]
    if winner == "Not Awarded":
        logo = "https://pbs.twimg.com/media/HCRpyEUaQAAPORi?format=png&name=medium"
    else:
        logo = team_info.get(winner, {}).get("wordmark", "")
    return logo

def get_all_stars_award(df: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame, df4: pd.DataFrame, Year: int, Award: str) -> pd.DataFrame:
    df = df[df["Award"] == Award]
    df = df[df["Year"] == Year]
    df = df.copy()
    df2 = df2.copy()
    df4 = df4.copy()
    df["_player_key"] = df["Winner"].apply(normalize_player_key)
    df2["_player_key"] = df2["name"].apply(normalize_player_key)
    df4["_player_key"] = df4["Player"].apply(normalize_player_key)
    df = df.merge(df2, how="left", on="_player_key")
    df3 = df3[df3["Year"] == Year]
    df3 = df3[df3["period"] == df3["period"].max()]
    df = df.merge(df3, how="left", left_on="fantraxId", right_on="id")
    df = df.merge(df4, how="left", on="_player_key")
    def get_team_logo(team_name, team_info):
        for city, info in team_info.items():
            full_name = f"{city} {info['nickname']}"
            if team_name == full_name:
                return info["logo"]
        return None
    def get_team_conf(team_name, team_info):
        for city, info in team_info.items():
            full_name = f"{city} {info['nickname']}"
            if team_name == full_name:
                return info["conf"]
        return None 
    df["logo"] = df["team_name"].apply(lambda x: get_team_logo(x, team_info))
    df["conf"] = df["team_name"].apply(lambda x: get_team_conf(x, team_info))
    df = df[["logo", "Winner", "Picture_Online"]]
    df = df.sort_values("Winner")
    return df

def get_short_term_awards(df: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame, df4: pd.DataFrame, Year: int, Award: str) -> pd.DataFrame:
    df["Week"] = df["Award"].str.extract(
    r'(Week \d+|January|February|March|April|May|June|July|August|September|October|November|December)')[0]
    df["Award_clean"] = df["Award"].apply(
    lambda x: " ".join([x.split()[0], x.split()[-1]]))
    df = df[df["Award_clean"] == Award]
    df = df[df["Year"] == Year]
    df = df.copy()
    df2 = df2.copy()
    df4 = df4.copy()
    df["_player_key"] = df["Winner"].apply(normalize_player_key)
    df2["_player_key"] = df2["name"].apply(normalize_player_key)
    df4["_player_key"] = df4["Player"].apply(normalize_player_key)
    df = df.merge(df2, how="left", on="_player_key")
    df3 = df3[df3["Year"] == Year]
    df3 = df3[df3["period"] == df3["period"].max()]
    df = df.merge(df3, how="left", left_on="fantraxId", right_on="id")
    df = df.merge(df4, how="left", on="_player_key")
    def get_team_logo(team_name, team_info):
        for city, info in team_info.items():
            full_name = f"{city} {info['nickname']}"
            if team_name == full_name:
                return info["logo"]
        return None
    def get_team_conf(team_name, team_info):
        for city, info in team_info.items():
            full_name = f"{city} {info['nickname']}"
            if team_name == full_name:
                return info["conf"]
        return None 
    df["logo"] = df["team_name"].apply(lambda x: get_team_logo(x, team_info))
    df["conf"] = df["team_name"].apply(lambda x: get_team_conf(x, team_info))
    df = df[["Week", "logo", "Winner", "Picture_Online"]]
    df["Week"] = pd.Categorical(df["Week"], categories=["November", "December", "January", "February", "March"] +[f"Week {i}" for i in range(1, 39)],ordered=True)
    df = df.sort_values("Week")
    return df

def img_to_base64(path: str) -> str:
    try:
        data = Path(path).read_bytes()
        ext = Path(path).suffix.lstrip(".").lower()
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "svg": "svg+xml", "webp": "webp"}.get(ext, "png")
        return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"
    except Exception:
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

def render_scorebug(row):
    team_a = row["TeamA_Nickname"]
    team_b = row["TeamB_Nickname"]
    logo_a = row["TeamA_logo"]
    logo_b = row["TeamB_logo"]
    record_a = row["TeamA_record"]
    record_b = row["TeamB_record"]
    score_a = row["TeamA_Score"]
    score_b = row["TeamB_Score"]
    color_a = row["TeamA_color"]
    color_b = row["TeamB_color"]
    logo_a_src = img_to_base64(logo_a) if not logo_a.startswith("http") else logo_a
    logo_b_src = img_to_base64(logo_b) if not logo_b.startswith("http") else logo_b


    html = f"""<!DOCTYPE html>
        <html>
        <head>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;800&family=Barlow:wght@400;500&display=swap" rel="stylesheet">
        <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            background: transparent;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 160px;
            font-family: 'Barlow Condensed', sans-serif;
        }}

        .scorebug {{
            position: relative;
            width: 420px;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 0 0 1px rgba(255,255,255,0.08), 0 24px 64px rgba(0,0,0,0.6);
            background: #0d0d0f;
        }}

        .team-row {{
            position: relative;
            display: flex;
            align-items: center;
            padding: 0 20px 0 24px;
            height: 72px;
            gap: 14px;
            overflow: hidden;
        }}

        .team-row::before {{
            content: '';
            position: absolute;
            inset: 0;
            opacity: 0.13;
            pointer-events: none;
        }}

        .row-a::before {{ background: radial-gradient(ellipse at 30% 50%, {color_a} 0%, transparent 70%); }}
        .row-b::before {{ background: radial-gradient(ellipse at 30% 50%, {color_b} 0%, transparent 70%); }}

        .row-a::after {{
            content: '';
            position: absolute;
            left: 0; right: 0; top: 0;
            height: 2px;
            background: linear-gradient(90deg, {color_a}, transparent 80%);
            box-shadow: 0 0 12px 2px {color_a};
            animation: glowPulse 2.4s ease-in-out infinite;
        }}

        .row-b::after {{
            content: '';
            position: absolute;
            left: 0; right: 0; bottom: 0;
            height: 2px;
            background: linear-gradient(90deg, {color_b}, transparent 80%);
            box-shadow: 0 0 12px 2px {color_b};
            animation: glowPulse 2.4s ease-in-out infinite 1.2s;
        }}

        @keyframes glowPulse {{
            0%, 100% {{ opacity: 1; }}
            50%       {{ opacity: 0.4; }}
        }}

        .divider {{
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 20%, rgba(255,255,255,0.15) 80%, transparent 100%);
        }}

        .accent-stripe {{
            position: absolute;
            left: 0; top: 0; bottom: 0;
            width: 4px;
        }}
        .row-a .accent-stripe {{ background: {color_a}; box-shadow: 2px 0 12px 0 {color_a}; }}
        .row-b .accent-stripe {{ background: {color_b}; box-shadow: 2px 0 12px 0 {color_b}; }}

        .team-logo {{
            width: 44px;
            height: 44px;
            object-fit: contain;
            flex-shrink: 0;
            filter: drop-shadow(0 2px 8px rgba(0,0,0,0.5));
        }}

        .team-info {{ flex: 1; min-width: 0; }}

        .team-name {{
            font-size: 15.8px;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: #ffffff;
            line-height: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .team-record {{
            font-family: 'Barlow', sans-serif;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.06em;
            color: rgba(255,255,255,0.45);
            margin-top: 3px;
            text-transform: uppercase;
        }}

        .team-score {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #ffffff;
            min-width: 52px;
            text-align: right;
            line-height: 1;
            text-shadow: 0 0 24px rgba(255,255,255,0.18);
        }}
        </style>
        </head>
        <body>
        <div class="scorebug">
            <div class="team-row row-a">
            <div class="accent-stripe"></div>
            <img class="team-logo" src="{logo_a_src}" alt="{team_a}" />
            <div class="team-info">
                <div class="team-name">{team_a}</div>
                <div class="team-record">{record_a}</div>
            </div>
            <div class="team-score">{score_a}</div>
            </div>
            <div class="divider"></div>
            <div class="team-row row-b">
            <div class="accent-stripe"></div>
            <img class="team-logo" src="{logo_b_src}" alt="{team_b}" />
            <div class="team-info">
                <div class="team-name">{team_b}</div>
                <div class="team-record">{record_b}</div>
            </div>
            <div class="team-score">{score_b}</div>
            </div>
        </div>
        </body>
        </html>"""
    components.html(html, height=180, scrolling=False)

def get_matchup_score(team_a: str, team_b: str, df: pd.DataFrame):
    matchup = df[df["Team"].isin([team_a, team_b])].copy()
    if matchup.shape[0] != 2:
        raise ValueError("Both teams must exist exactly once in dataframe.")
    matchup = matchup.set_index("Team").loc[[team_a, team_b]].reset_index()
    weights = {"PTS": 61, "AST": 41, "TS%": 41, "2PT%": 31, "+/-": 31, "3PT%": 31, "BLK": 31, "DREB": 31, "OREB": 31, "ST": 31, "FT%": 21, "MP": 11, "TO": 21}
    team_a_score = 0
    team_b_score = 0
    for stat, weight in weights.items():
        val_a = matchup.loc[0, stat]
        val_b = matchup.loc[1, stat]
        if stat == "TO":
            if val_a < val_b:
                team_a_score += weight
            elif val_b < val_a:
                team_b_score += weight
            else:
                team_a_score += weight / 2
                team_b_score += weight / 2
        else:
            if val_a > val_b:
                team_a_score += weight
            elif val_b > val_a:
                team_b_score += weight
            else:
                team_a_score += weight / 2
                team_b_score += weight / 2
    return team_a_score, team_b_score

def get_weekly_scores_df(SelectedYear, SelectedPeriod, df, df2, df3):
    df = df[(df["Year"] == SelectedYear) & (df["Period"] == SelectedPeriod)].copy()
    df["TeamA_Nickname"] = df["TeamA"].apply(lambda x: safe_team_info(x, "nickname", str(x)))
    df["TeamB_Nickname"] = df["TeamB"].apply(lambda x: safe_team_info(x, "nickname", str(x)))
    df["TeamA_logo"] = df["TeamA"].apply(lambda x: safe_team_info(x, "logo"))
    df["TeamB_logo"] = df["TeamB"].apply(lambda x: safe_team_info(x, "logo"))
    df["TeamA_color"] = df["TeamA"].apply(lambda x: safe_team_info(x, "bg", "#111827"))
    df["TeamB_color"] = df["TeamB"].apply(lambda x: safe_team_info(x, "bg", "#111827"))
    conditions = [df["Type"] == "Regular Season", df["Round"] == "Group Stage", (df["Type"] == "In-Season Tournament") & (df["Round"] != "Group Stage"), df["Type"].isin(["Play-In", "Playoffs"])]
    choices = ["Record", "GSRecord", "IST Seed", "Playoff Seed"]
    df["lookup_col"] = np.select(conditions, choices, default=None)
    if ((df3["Year"] == SelectedYear) & (df3["Period"] == SelectedPeriod)).any():
        df3 = df3[(df3["Year"] == SelectedYear) & (df3["Period"] == SelectedPeriod)].copy()
    else:
        df3 = df3[(df3["Year"] == SelectedYear) & (df3["Period"] == 99)].copy()
    df3_melted = df3.melt(id_vars="Team", value_vars=["Record", "GSRecord", "IST Seed", "Playoff Seed"], var_name="lookup_col", value_name="value")
    df = df.merge(df3_melted, left_on=["TeamA", "lookup_col"], right_on=["Team", "lookup_col"], how="left")
    df = df.rename(columns={"value": "TeamA_record"})
    df = df.drop(columns=["Team"])
    df = df.merge(df3_melted, left_on=["TeamB", "lookup_col"], right_on=["Team", "lookup_col"],how="left")
    df = df.rename(columns={"value": "TeamB_record"})
    df = df.drop(columns=["Team"])
    def compute_scores(row):
        team_a = row["TeamA"]
        team_b = row["TeamB"]
        score_a, score_b = get_matchup_score(team_a, team_b, df2)
        return pd.Series([score_a, score_b])
    df[["TeamA_Score", "TeamB_Score"]] = df.apply(compute_scores, axis=1)
    order = ["Regular Season", "In-Season Tournament", "Play-In", "Playoffs"]
    df["Type"] = pd.Categorical(df["Type"], categories=order, ordered=True)
    df = df.sort_values(["Type", "TeamB_Nickname"], ascending=[True, True])    
    return df

def get_standings_table(df, SelectedPeriod, SelectedYear, Conference):
    team_to_conf = {team: info["conf"] for team, info in team_info.items()}
    df["Conference"] = df["Team"].map(team_to_conf)
    mask = (df["Year"] == SelectedYear) & (df["Period"] == SelectedPeriod)
    if not mask.any():
        SelectedPeriod = 99
    df = df[(df["Year"] == SelectedYear) & (df["Period"] == SelectedPeriod) & (df["Conference"] == Conference)].copy()
    df[["wins", "losses"]] = df["Record"].str.split("-", expand=True).astype(int)
    df["Win %"] = df["wins"] / (df["wins"] + df["losses"])   
    max_wins = df["wins"].max()
    df["GB"] = (max_wins - df["wins"]).astype(float).round(1).astype(str)    
    df.loc[df["GB"] == "0.0", "GB"] = "—"
    team_to_logo = {team: info["logo"] for team, info in team_info.items()}
    df["Logo"] = df["Team"].map(team_to_logo)
    df = df[["Logo", "Record", "Win %", "GB", "ConfRecord", "DivRecord"]]    
    df = df.sort_values("Win %", ascending=False).reset_index(drop=True)
    df["Win %"] = (df["Win %"] * 100).round(2).astype(str) + "%"
    df = df.rename(columns={"ConfRecord": "Conf. Record", "DivRecord": "Div. Record"})
    green = '#6B9B6B'
    yellow = '#D4B963'
    red = '#CC8888'

    def tier_color(row):
        if row.name <= 5:
            color = green
        elif row.name <= 9:
            color = yellow
        else:
            color = red

        return [f'background-color: {color}'] * len(row)
    df = df.style.apply(tier_color, axis=1).hide(axis="index")
    return df

def get_team_schedule(df, SelectedTeam, SelectedYear):
    df = get_all_time_schedule()
    df = df[df["Year"] == SelectedYear].copy()
    df = df[(df["TeamA"].str.contains(SelectedTeam)) | (df["TeamB"].str.contains(SelectedTeam))]
    df["Team"] = SelectedTeam
    df["Opponent"] = np.where(df["TeamA"].str.contains(SelectedTeam, na=False), df["TeamB"], df["TeamA"])
    df["Location"] = np.where(df["TeamA"].str.contains(SelectedTeam, na=False), "", "@")
    df["TeamScore"] = np.where(df["TeamA"].str.contains(SelectedTeam, na=False), df["TeamAScore"], df["TeamBScore"])
    df["OpponentScore"] = np.where(df["TeamA"].str.contains(SelectedTeam, na=False), df["TeamBScore"], df["TeamAScore"])
    df["Result"] = np.where(df["TeamScore"] > df["OpponentScore"], "W", "L")
    df["Score"] = df["TeamScore"].astype(str) + "-" + df["OpponentScore"].astype(str)
    team_to_logo = {team: info["logo"] for team, info in team_info.items()}
    df["Logo"] = df["Opponent"].map(team_to_logo)
    green = '#6B9B6B'
    red = '#CC8888'
    def tier_color(row):
        color = green if row["Result"] == "W" else red
        return [f'background-color: {color}'] * len(row)
    df = df[["Period", "Location", "Logo", "Score", "Result"]]
    df = df.style.apply(tier_color, axis=1).hide(axis="index")
    return df

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def get_team_mileage(SelectedTeam, Year, df):
    team_df = df[(df["Year"] == Year) & (df["Type"].isin(["Regular Season", "In-Season Tournament"])) & ((df["TeamA"] == SelectedTeam) | (df["TeamB"] == SelectedTeam))].copy()
    type_order = {"Regular Season": 0, "In-Season Tournament": 1}
    team_df["TypeOrder"] = team_df["Type"].map(type_order)
    team_df = team_df.sort_values(["Period", "TypeOrder"]).reset_index(drop=True)
    team_df.drop(columns="TypeOrder", inplace=True)
    selected_info = team_info.get(SelectedTeam)
    if not selected_info:
        return 0, 0
    current_lat = selected_info["lat"]
    current_lon = selected_info["lon"]
    miles_per_game = []
    for _, row in team_df.iterrows():
        dest = row["TeamB"] if row["TeamA"] == SelectedTeam else SelectedTeam
        dest_info = team_info.get(dest)
        if not dest_info:
            continue
        dest_lat = dest_info["lat"]
        dest_lon = dest_info["lon"]
        miles = haversine(current_lat, current_lon, dest_lat, dest_lon)
        miles_per_game.append(miles)
        current_lat, current_lon = dest_lat, dest_lon
    team_df["MilesThisGame"] = miles_per_game
    team_df = team_df[["TeamA", "TeamB", "MilesThisGame"]]
    total_miles = team_df["MilesThisGame"].sum()
    num_flights = (team_df["MilesThisGame"] > 0).sum()
    return total_miles, num_flights

def arc_points(lat1, lon1, lat2, lon2, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        lat = lat1 + t * (lat2 - lat1)
        lon = lon1 + t * (lon2 - lon1)
        bow = math.sin(math.pi * t) * 3
        pts.append([lon, lat + bow])
    return pts

def plot_team_flights(SelectedTeam, Year, df):
    team_df = df[(df["Year"] == Year) & (df["Type"].isin(["Regular Season", "In-Season Tournament"])) & ((df["TeamA"] == SelectedTeam) | (df["TeamB"] == SelectedTeam))].copy()
    type_order = {"Regular Season": 0, "In-Season Tournament": 1}
    team_df["TypeOrder"] = team_df["Type"].map(type_order)
    team_df = team_df.sort_values(["Period", "TypeOrder"]).reset_index(drop=True)
    home = team_info.get(SelectedTeam)
    if not home:
        return folium.Map(location=[39.5, -98.35], zoom_start=4, tiles="CartoDB Positron", zoom_control=False)
    team_color = home["bg"]
    team_color2 = home["bg2"]
    current_lat = home["lat"]
    current_lon = home["lon"]
    m = folium.Map(location=[current_lat, current_lon], zoom_start=4, tiles="CartoDB Positron", zoom_control=False)
    visited = set()
    for _, row in team_df.iterrows():
        dest = row["TeamB"] if row["TeamA"] == SelectedTeam else SelectedTeam
        dest_info = team_info.get(dest)
        if not dest_info:
            continue
        dest_lat = dest_info["lat"]
        dest_lon = dest_info["lon"]
        if dest_lat != current_lat or dest_lon != current_lon:
            folium.PolyLine(locations=[[current_lat, current_lon], [dest_lat, dest_lon]], color=team_color, weight=3, opacity=0.8).add_to(m)
        if dest not in visited:
            folium.CircleMarker(location=[dest_lat, dest_lon], radius=5, color=team_color2, fill=True, fill_color=team_color, fill_opacity=0.9, tooltip=dest).add_to(m)
            visited.add(dest)
        current_lat, current_lon = dest_lat, dest_lon
    return m
