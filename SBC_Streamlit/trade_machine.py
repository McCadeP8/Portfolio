import pandas as pd
import streamlit as st
import math as math
from data import current_salary_cap, current_luxury_tax, current_apron_1, current_apron_2, tax_bracket_increment, league_ratio, columns_order, current_year, year_offset, team_info

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
    df = df[df['OGTeam'] == SelectedTeam]
    df = df[df['Year'].between(current_year, current_year + 6)]
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df.sort_values('Pick', ascending=True)
    df_list = df['Pick'].tolist()
    return df_list

def tradeable_picks_in(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df[df['OGTeam'] != SelectedTeam]
    df = df[df['Year'].between(current_year, current_year + 6)]
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df.sort_values('Pick', ascending=True)
    df_list = df['Pick'].tolist()
    return df_list

def players_out_table(df: pd.DataFrame, pics: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df = df[df['Player'].isin(selected_players)]
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df.rename(columns={f"Y{current_year}": f"{current_year}"})
    df = df.rename(columns={'Picture_Online': ' '})
    df = df[[' ', 'Player', f"{current_year}"]]
    return df

def players_in_table(df: pd.DataFrame, pics: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df = df[df['Player'].isin(selected_players)]
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={f"Y{current_year}": f"{current_year}"})
    df = df.rename(columns={'Picture_Online': ' '})
    df = df[['Team_logo', ' ', 'Player', f"{current_year}"]]
    return df
