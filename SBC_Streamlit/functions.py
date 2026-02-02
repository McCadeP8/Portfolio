import pandas as pd
import streamlit as st
import math as math
import numpy as np
import requests
import json
from data import current_salary_cap, current_luxury_tax, current_apron_1, current_apron_2, tax_bracket_increment, league_ratio, columns_order, current_year, year_offset, team_info, league_id, period, cap_sheets_to_fantrax_name_fix

@st.cache_data(ttl=21600)
def get_data() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1906653859"
    df = pd.read_csv(csv_url)
    return df

@st.cache_data(ttl=21600)
def get_pictures() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1180190150"
    df = pd.read_csv(csv_url)
    df = df.drop(columns=["Picture"])
    return df

@st.cache_data(ttl=21600)
def get_exceptions() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1620818587"
    df = pd.read_csv(csv_url)
    df = df[["Team", "Player", "Y" + str(current_year), "BirdRights"]]
    return df

@st.cache_data(ttl=21600)
def get_base_cap() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=760630769"
    df = pd.read_csv(csv_url)
    return df

@st.cache_data(ttl=21600)
def get_draft_picks() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1612129799"
    df = pd.read_csv(csv_url)
    df = df[df['Year'].between(current_year, current_year + 6)]
    return df

@st.cache_data(ttl=21600)
def get_fantrax_roster() -> pd.DataFrame:
    all_rosters_list = []    
    roster_url = f"https://www.fantrax.com/fxea/general/getTeamRosters?leagueId={league_id}&period={period}"
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

@st.cache_data(ttl=21600)
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

@st.cache_data(ttl=21600)
def get_fantrax_standings() -> pd.DataFrame:
    roster_url = f"https://www.fantrax.com/fxea/general/getStandings?leagueId={league_id}"
    headers = {'Cookie': 'JSESSIONID='}
    response = requests.get(roster_url, headers=headers)
    if response.status_code == 200:
        standings = json.loads(response.text)
        df = pd.DataFrame(standings)
    else:
        print(f"Failed to fetch data - Status code: {response.status_code}")
    return df

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

    tax_payout_champ

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
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def swap_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['PickSwap']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def split_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['FullyOwned'] == False]  # noqa: E712
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def locked_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['Locked']]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def original_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['OGTeam'] == SelectedTeam) & (df['CurrentTeam'].str.contains(SelectedTeam) == False)]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def touched_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['TeamTouched'].str.contains(SelectedTeam, na=False))]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def all_full_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['FullyOwned']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df[df['PickSwap'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def all_swap_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['PickSwap']]
    df = df[df['FullyOwned']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def all_split_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['FullyOwned'] == False]  # noqa: E712
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.rename(columns={'CurrentTEam': 'Potential Owners'})
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def all_locked_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['Locked']]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
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
    df2 = pd.DataFrame({
        "Year": [2025] * 30,
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
    df = df[df['gap'] > 2]
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
    df = df[df['CurrentTeam'].str.contains(SelectedTeam)]
    df = df[df['Locked'] == False] #noqa: E712
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df.sort_values('Pick', ascending=True)
    df_list = df['Pick'].tolist()
    return df_list

def tradeable_picks_in(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
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
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df[df['Pick'].isin(selected_players)]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes', 'TeamTouched','Pick'])
    df["CurrentTeam"] = df["CurrentTeam"].apply(lambda x: team_info.get(x.split(",")[0].strip(), {}).get("logo", ""))
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def picks_in_table(df: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
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
        st.warning("Roster is within 15-17 players. Ensure you have sufficient IR-eligible players to maintain compliance and flexibility.", icon = "⚠️")
    elif 12 <= current_players <= 14:
        st.success(f"Roster size of {current_players} players is within the standard limits. No immediate action required.", icon = "✅")
    elif current_players < 12:
        players_needed = 12 - current_players
        st.warning(f"Roster is below the minimum limit of 12 players. You need to sign at least {players_needed} player(s) to comply with roster requirements.", icon = "⚠️")
    return current_players


#SB 

def no_cash():
    st.warning("Under Construction: no_cash", icon = "⚠️")
    return "A"
def tpe_st_check():
    st.warning("Under Construction: tpe_st_check", icon = "⚠️")
    return "A"
def no_aggregation_check():
    st.warning("Under Construction: no_aggregation_check", icon = "⚠️")
    return "A"

def under_100_percent_check():
    st.warning("Under Construction: under_100_percent_check", icon = "⚠️")
    return "A"
def no_bae_mle_check():
    st.warning("Under Construction: no_bae_mle_check", icon = "⚠️")
    return "A"

def salary_trade_check():
    st.warning("Under Construction: salary_trade_check", icon = "⚠️")
    return "A"
def tpe_check():
    st.warning("Under Construction: tpe_check", icon = "⚠️")
    return "A"
def bae_mle_check():
    st.warning("Under Construction: bae_mle_check", icon = "⚠️")
    return "A"

def player_agg_check():
    st.warning("Under Construction: player_agg_check", icon = "⚠️")
    return "A"
def create_tpe_check():
    st.warning("Under Construction: create_tpe_check", icon = "⚠️")
    return "A"
def new_trade_rest_check():
    st.warning("Under Construction: new_trade_rest_check", icon = "⚠️")
    return "A"
def old_team_check():
    st.warning("Under Construction: old_team_check", icon = "⚠️")
    return "A"

def stepien_check():
    st.warning("Under Construction: stepien_check", icon = "⚠️")
    return "A"

def fantrax_players_check(df: pd.DataFrame, ft_players: pd.DataFrame, ft_rosters: pd.DataFrame) -> pd.DataFrame:
    df['Player'] = df['Player'].replace(cap_sheets_to_fantrax_name_fix)
    df = df[df['Player'] != "Minimum Salary Penalty"]
    df = df[df['Trade.Restriction'] != "Dead"]
    df = df[df['Trade.Restriction'] != "Banned"]
    df = df.merge(ft_players, how='left', left_on='Player', right_on='name')
    df = df.merge(ft_rosters, how='outer', left_on='fantraxId', right_on='id')
    df = df[df['Player'].isna() | df['team_name'].isna()]
    df = df.rename(columns={'Player': 'Cap Sheet Name'})
    df = df.rename(columns={'name': 'Fantrax Name'})
    df = df[['Cap Sheet Name', 'Fantrax Name']]
    return df

def fantrax_roster_check(df: pd.DataFrame, ft_players: pd.DataFrame, ft_rosters: pd.DataFrame) -> pd.DataFrame:
    df['Player'] = df['Player'].replace(cap_sheets_to_fantrax_name_fix)
    df = df[df['Player'] != "Minimum Salary Penalty"]
    df = df[df['Trade.Restriction'] != "Dead"]
    df = df[df['Trade.Restriction'] != "Banned"]
    df = df.merge(ft_players, how='left', left_on='Player', right_on='name')
    df = df.merge(ft_rosters, how='outer', left_on='fantraxId', right_on='id')
    df['status2'] = df['status'].apply(lambda x: "Non-Active Players" if x == "MINORS" else "Active Players")
    df = df[df['Type'] != df["status2"]]
    df = df[['Player', 'Team', 'Type', 'status']]
    df = df.rename(columns={'Type': 'Cap Sheet Location'})
    df = df.rename(columns={'status': 'Fantrax Locatoin'})
    return df

    #AABC

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
    df = get_fantrax_standings()
    df = df[['teamName', 'winPercentage']]
    dp = get_draft_picks()
    dp = dp[dp['Year'] == current_year]
    dp["OGTeam"] = dp["OGTeam"].map(lambda t: f"{t} {team_info.get(t, {}).get('nickname', '')}".strip())
    dp = dp.merge(df, how = 'left', left_on = 'OGTeam', right_on = 'teamName')
    dp = dp[dp['Round'] == round]
    dp = dp.sort_values('winPercentage', ascending=True)
    dp = dp[['OGTeam', 'CurrentTeam', 'Explanation']]
    dp["Selection"] = [None] * 30
    dp["Time Due (ET)"] = ["10:30 AM", "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM","1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM", "5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM", "8:00 PM", "8:30 PM", "9:00 PM", "9:30 PM", "10:00 PM", "10:30 PM", "11:00 PM", "11:30 PM", "12:00 AM", "12:30 AM", "1:00 AM"]
    dp = dp.rename(columns={'OGTeam': 'Slot'})
    dp = dp.rename(columns={'CurrentTeam': 'Player'})
    return dp