import pandas as pd
import streamlit as st

@st.cache_data(ttl=120)
def get_data() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1906653859"
    df = pd.read_csv(csv_url)
    return df

@st.cache_data(ttl=120)
def get_pictures() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1180190150"
    df = pd.read_csv(csv_url)
    df = df.drop(columns=["Picture"])
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
    year_cols = ['Y2026','Y2027','Y2028','Y2029','Y2030','Y2031','Y2032']
    type_cols_keep = ['Type2026','Type2027','Type2028','Type2029','Type2030','Type2031','Type2032']
    cols_to_keep = ['Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values('2026', ascending=False)
    return df

def overseas_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Non-Active Players']
    df = df[df['Type2026'].isin(['Guaranteed', 'Unguaranteed'])]
    year_cols = ['Y2026','Y2027','Y2028','Y2029','Y2030','Y2031','Y2032']
    type_cols_keep = ['Type2026','Type2027','Type2028','Type2029','Type2030','Type2031','Type2032']
    cols_to_keep = ['Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values('2026', ascending=False)
    return df

def dead_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Non-Active Players']
    df = df[df['Type2026'] == "Dead"]
    df = df[df["Trade.Restriction"] != "Retired"]
    year_cols = ['Y2026','Y2027','Y2028','Y2029','Y2030','Y2031','Y2032']
    type_cols_keep = ['Type2026','Type2027','Type2028','Type2029','Type2030','Type2031','Type2032']
    cols_to_keep = ['Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values('2026', ascending=False)
    return df

def free_agent_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type2026'].isin(['Unrestricted', 'Restricted'])]
    year_cols = ['Y2026','Y2027','Y2028','Y2029','Y2030','Y2031','Y2032']
    type_cols_keep = ['Type2026','Type2027','Type2028','Type2029','Type2030','Type2031','Type2032']
    cols_to_keep = ['Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values('2026', ascending=False)
    return df

def draft_retired_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:

    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[(df['Type2026'] == 'Draft Rights') | (df['Trade.Restriction'] == 'Retired')]
    year_cols = ['Y2026','Y2027','Y2028','Y2029','Y2030','Y2031','Y2032']
    type_cols_keep = ['Type2026','Type2027','Type2028','Type2029','Type2030','Type2031','Type2032']
    cols_to_keep = ['Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values('2026', ascending=False)
    return df

def active_player_n(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Active Players']
    return df.shape[0]

def inactive_player_n(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Non-Active Players']
    df = df[df['Type2026'].isin(['Guaranteed', 'Unguaranteed'])]
    return df.shape[0]