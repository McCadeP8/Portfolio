import pandas as pd
import streamlit as st
import re
from data import type_colors

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

def style_salaries(row):
    styles = [""] * len(row)
    for i, col in enumerate(row.index):
        match = re.match(r"\d{4}", col)
        if match:
            year = match.group(1)
            type_col = f"Type{year}"
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
    cols_to_keep = ['Picture_Online'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ''})
    df = df.rename(columns={col: col[1:] for col in year_cols})    
    df = (df.style
        .apply(style_salaries, axis=1, type_colors=type_colors)
        .format({c: "${:,.0f}" for c in df.columns if re.match(r"\d{4}", c)}))
    return df

