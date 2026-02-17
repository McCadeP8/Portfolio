import pandas as pd
import streamlit as st
import numpy as np

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

def get_logo(df: pd.DataFrame, SelectedTeam: str) -> str:
    team_row = df[df["Team"] == SelectedTeam]
    return team_row["Logo"].iloc[0]

def get_team_schedule(df: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame, SelectedTeam: str, Tournament: str) -> str:
    df = df[df["Team"] == SelectedTeam]
    df[["Week", "Type"]] = df["Matchup"].str.split("_", n=1, expand=True)
    df = df.merge(df2, how="left", on=["Team", "Week"]).rename(columns={"Score": "Team Score"})
    df = df.merge(df2, how="left", left_on=["Opponent", "Week"], right_on=["Team", "Week"]).rename(columns={"Score": "Opponent Score"})
    df["Result"] = np.select([df["Team Score"] > df["Opponent Score"], df["Team Score"] < df["Opponent Score"]], ["Win", "Loss"], default="Tie")
    df = df.merge(df3[["Team", "Logo"]], how="left", left_on="Opponent", right_on="Team")
    df = df[["Week", "Type", "Logo", "Team Score", "Opponent Score", "Result"]]
    df["Result"] = np.where(df["Opponent Score"].isna(), np.nan, df["Result"])
    df = df[df["Type"] == Tournament]
    df = df.drop("Type", axis=1)
    return df

def get_base_records(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    df = get_schedule()
    df2 = get_weekly_scores()
    df[["Week", "Type"]] = df["Matchup"].str.split("_", n=1, expand=True)
    df = df.merge(df2, how="left", on=["Team", "Week"]).rename(columns={"Score": "Team Score"})
    df = df.merge(df2, how="left", left_on=["Opponent", "Week"], right_on=["Team", "Week"]).rename(columns={"Score": "Opponent Score"})
    df["Result"] = np.select([df["Team Score"] > df["Opponent Score"], df["Team Score"] < df["Opponent Score"]], ["Win", "Loss"], default="Tie")
    df = df[~df["Opponent Score"].isna()]
    df = df.groupby("Team_x")["Result"].value_counts().unstack(fill_value=0).reset_index()
    df["Win %"] = (df["Win"] + 0.5 * df["Tie"]) / (df["Win"] + df["Loss"] + df["Tie"])
    df["Record"] = np.where(df["Tie"] > 0, df["Win"].astype(str) + "-" + df["Loss"].astype(str) + "-" + df["Tie"].astype(str), df["Win"].astype(str) + "-" + df["Loss"].astype(str))
    df = df.rename(columns={"Team_x": "Team"})
    df = df[["Team", "Record", "Win %"]]
    df["Rank_num"] = df["Win %"].rank(method="min", ascending=False)
    df["Rank_num"] = df["Rank_num"].astype(int)
    tie_counts = df.groupby("Win %")["Win %"].transform("count")
    df["Rank"] = np.where(tie_counts > 1, "T-" + df["Rank_num"].astype(str), df["Rank_num"].astype(str))
    df = df.drop(columns=["Rank_num"])
    return df

def get_team_record(df: pd.DataFrame, SelectedTeam: str) -> str:
    team_row = df[df["Team"] == SelectedTeam]
    return team_row["Record"].iloc[0]

def get_team_record_rank(df: pd.DataFrame, SelectedTeam: str) -> str:
    team_row = df[df["Team"] == SelectedTeam]
    return team_row["Rank"].iloc[0]

#def get_opponent_record(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
 #   df = get_schedule()
 #   df3 = get_base_records(df, df2)


