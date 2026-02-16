import pandas as pd
import streamlit as st

@st.cache_data()
def get_teams() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/12YsTcnc19YhkLA1GNEhtLYYSvtG1Ze5fHPPBLADdVf0/export?format=csv&gid=1726698249"
    df = pd.read_csv(csv_url)
    return df

@st.cache_data()
def get_weekly_scores() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/12YsTcnc19YhkLA1GNEhtLYYSvtG1Ze5fHPPBLADdVf0/export?format=csv&gid=896954524"
    df = pd.read_csv(csv_url)
    df = df.melt(id_vars="Team", var_name="Week", value_name="Score")
    return df

@st.cache_data()
def get_schedule() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/12YsTcnc19YhkLA1GNEhtLYYSvtG1Ze5fHPPBLADdVf0/export?format=csv&gid=1113134782"
    df = pd.read_csv(csv_url)
    df = df.melt(id_vars="Team", var_name="Matchup", value_name="Opponent")
    return df

def get_logo(df: pd.DataFrame, selected_team: str) -> str:
    team_row = df[df["Team"] == selected_team]
    return team_row["Logo"].iloc[0]
