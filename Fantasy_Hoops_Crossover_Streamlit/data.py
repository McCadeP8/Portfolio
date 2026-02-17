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

def get_conf_records(df: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame) -> pd.DataFrame:
    df = get_schedule()
    df2 = get_weekly_scores()
    df3 = get_teams()
    df[["Week", "Type"]] = df["Matchup"].str.split("_", n=1, expand=True)
    df = df[df["Type"] == "Conf"]
    df = df.merge(df2, how="left", on=["Team", "Week"]).rename(columns={"Score": "Team Score"})
    df = df.merge(df2, how="left", left_on=["Opponent", "Week"], right_on=["Team", "Week"]).rename(columns={"Score": "Opponent Score"})
    df["Result"] = np.select([df["Team Score"] > df["Opponent Score"], df["Team Score"] < df["Opponent Score"]], ["Win", "Loss"], default="Tie")
    df = df[~df["Opponent Score"].isna()]
    df = df.groupby("Team_x")["Result"].value_counts().unstack(fill_value=0).reset_index()
    df["Win %"] = (df["Win"] + 0.5 * df["Tie"]) / (df["Win"] + df["Loss"] + df["Tie"])
    df["Record"] = np.where(df["Tie"] > 0, df["Win"].astype(str) + "-" + df["Loss"].astype(str) + "-" + df["Tie"].astype(str), df["Win"].astype(str) + "-" + df["Loss"].astype(str))
    df = df.rename(columns={"Team_x": "Team"})
    df = df[["Team", "Record", "Win %"]]
    df = df.merge(df3[["Team", "Conf"]], how="left", on="Team")
    df["Rank_num"] = df.groupby("Conf")["Win %"] \
                            .rank(method="min", ascending=False)
    df["Rank_num"] = df["Rank_num"].astype(int)
    tie_counts = df.groupby(["Conf", "Win %"])["Win %"] \
                .transform("count")
    df["Rank"] = np.where(tie_counts > 1, "T-" + df["Rank_num"].astype(str), df["Rank_num"].astype(str))
    df = df.drop(columns=["Rank_num"])
    return df

def get_RPI(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    df2 = df2[~df2["Opponent"].isin(["ELIMINATED", "BYE"])]
    base_3 = df2.merge(df2[["Team", "Opponent"]].rename(columns={"Team": "Opp_Opp"}), how="left", on="Opponent")
    base_3 = base_3.drop(["Matchup","Opponent"], axis=1)
    base_3 = base_3[base_3["Team"] != base_3["Opp_Opp"]]
    base_2 = df2.drop(["Matchup"], axis=1)
    base_1 = df[["Team", "Win %"]]
    df[["W", "L", "T"]] = df["Record"].str.split("-", expand=True)
    df[["W", "L", "T"]] = df[["W", "L", "T"]].fillna("0")
    df[["W", "L", "T"]] = df[["W", "L", "T"]].astype(int)
    df = df[["Team", "W", "L", "T"]]
    base_3 = base_3.merge(df, how="left", left_on="Opp_Opp", right_on="Team")
    base_3 = base_3.drop(columns=["Team_y"])
    base_3 = base_3.rename(columns={"Team_x": "Team"})
    base_3 = base_3.groupby("Team", as_index=False)[["W", "L", "T"]].sum()
    base_3["OOWin %"] = (base_3["W"] + 0.5 * base_3["T"]) / (base_3["W"] + base_3["L"] + base_3["T"])
    base_3 = base_3[["Team", "OOWin %"]]
    base_2 = base_2.merge(df, how="left", left_on="Opponent", right_on="Team")
    base_2 = base_2.drop(columns=["Team_y"])
    base_2 = base_2.rename(columns={"Team_x": "Team"})
    base_2 = base_2.groupby("Team", as_index=False)[["W", "L", "T"]].sum()
    base_2["OWin %"] = (base_2["W"] + 0.5 * base_2["T"]) / (base_2["W"] + base_2["L"] + base_2["T"])
    base_2 = base_2[["Team", "OWin %"]]
    base_1 = base_1.merge(base_2, how="left", left_on="Team", right_on="Team")
    base_1 = base_1.merge(base_3, how="left", left_on="Team", right_on="Team")
    base_1["RPI"] = (0.25 * base_1["Win %"] +0.50 * base_1["OWin %"] + 0.25 * base_1["OOWin %"])
    base_1["SOS"] = (2/3 * base_1["OWin %"] + 1/3 * base_1["OOWin %"])
    base_1 = base_1[["Team", "RPI", "SOS"]]
    base_1["RPI_Rk"] = base_1["RPI"].rank(method="min", ascending=False).astype(int)
    base_1["SOS_Rk"] = base_1["SOS"].rank(method="min", ascending=False).astype(int)
    base_1["RPI_Quad"] = pd.cut(base_1["RPI_Rk"], bins=[0, 42, 84, 126, 168], labels=["Quad 1", "Quad 2", "Quad 3", "Quad 4"])
    return base_1

def get_team_stat(df, team_name, column_name):
    team_row = df[df["Team"] == team_name]
    if team_row.empty:
        return None 
    return team_row.iloc[0][column_name]

