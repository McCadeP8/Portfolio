import pandas as pd
import streamlit as st
import math as math
from data import current_salary_cap, current_luxury_tax, current_apron_1, current_apron_2, tax_bracket_increment, league_ratio, columns_order, current_year, year_offset, team_info

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

def active_player_n(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Active Players']
    return df.shape[0]

def inactive_player_n(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
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
        "Cap Space": [current_salary_cap-get_cap_total(df, exceptions_df, team) for team in team_info.keys()],
        "Tax Space": [current_luxury_tax-get_tax_total(df, team) for team in team_info.keys()],
        "Hard Cap": [team_hard_cap(base_cap, team) for team in team_info.keys()],
        "Apron 1 Space": [current_apron_1-get_tax_total(df, team) for team in team_info.keys()],
        "Apron 2 Space": [current_apron_2-get_tax_total(df, team) for team in team_info.keys()],
        "Base Fee": [base_fee(df, team, base_cap) for team in team_info.keys()],
        "Luxury Fee": [luxury_fee(df, team, base_cap) for team in team_info.keys()],
        "Balance": [net_fee(df, team, base_cap) for team in team_info.keys()],
        "Amount Paid": [amount_paid(base_cap, team) for team in team_info.keys()],
    })
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
                styles[i] = "background-color: yellow;"
            elif value <= 11 or value >= 18 or value == 0:
                styles[i] = "background-color: red;"
            elif 12 <= value <= 14:
                styles[i] = "background-color: green;"
        elif col in ["Cap Space", "Tax Space"]:
            color = "green" if value > 0 else "red"
            styles[i] = f"color: {color};"
            styles[i] += "text-align: right;"
        elif col == "Hard Cap":
            if value in ["Second Apron", "First Apron"]:
                styles[i] = "background-color: yellow;"
        elif col == "Apron 1 Space":
            if value < 0:
                styles[i] = "background-color: red;"
            elif row.get("Hard Cap") == "First Apron":
                styles[i] = "background-color: yellow;"
            styles[i] += "text-align: right;"
        elif col == "Apron 2 Space":
            if value < 0:
                styles[i] = "background-color: red;"
            elif row.get("Hard Cap") == "Second Apron":
                styles[i] = "background-color: yellow;"
            styles[i] += "text-align: right;"
        elif col in ["Base Fee", "Luxury Fee", "Amount Paid"]:
            styles[i] = "text-align: right;"
        elif col == "Net Fee":
            color = "red" if value > 0 else "green"
            styles[i] = f"color: {color}; text-align: right;"
    return styles