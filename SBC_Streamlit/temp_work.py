#import os
import pandas as pd
#os.chdir("SBC_Streamlit")

from data import team_info
from functions import get_fantrax_players

ft_players = get_fantrax_players()
csv_url = "https://docs.google.com/spreadsheets/d/1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/export?format=csv&gid=444367429"
df2 = pd.read_csv(csv_url)


df = pd.read_parquet("all_time_rosters_history.parquet")
df = df.merge(ft_players, how="left", left_on="id", right_on="fantraxId")
df = df.merge(
    df2,
    how="left",
    left_on=["period", "Year"],
    right_on=["games", "Year"]
)
full_to_conf = {
    f"{city} {info['nickname']}": info["conf"]
    for city, info in team_info.items()
}
df["team_name"] = df["team_name"].map(full_to_conf)
df = df.loc[
    df.groupby(["Year", "Period", "name"])["games"].idxmax()
].reset_index(drop=True)

def get_player_conf(df, player_name, year):
    result = df.loc[
        (df["name"] == player_name) & (df["Year"] == year),
        "team_name"
    ].dropna().unique()
    print(result)

def get_player_conf2(df, player_name, year):
    result = df.loc[
        (df["name"] == player_name) & (df["Year"] == year),
        "team_name"
    ]
    print(result)
    return result


get_player_conf(df, "Aleksej Pokusevski", 2021)
get_player_conf2(df, "Shai Gilgeous-Alexander", 2026)


players = [
    "Scottie Barnes",
    "Kawhi Leonard",
    "Tyrese Maxey",
    "Victor Wembanyama",
    "Not Awarded",
    "Nikola Jokic",
    "Nikola Jokic",
    "Amen Thompson",
    "Nikola Jokic",
    "Not Awarded",
    "Luka Doncic",
    "LaMelo Ball",
    "Shai Gilgeous-Alexander",
    "Tyrese Maxey",
    "Shai Gilgeous-Alexander",
    "Giannis Antetokounmpo",
    "Victor Wembanyama",
    "Jalen Johnson",
    "Shai Gilgeous-Alexander",
    "Jalen Johnson",
    "Keegan Murray",
    "Jalen Johnson",
    "Kawhi Leonard",
    "Jalen Johnson",
    "Luka Doncic",
    "Lauri Markkanen",
    "Shai Gilgeous-Alexander",
    "Kevin Porter",
    "Keyonte George",
    "Scottie Barnes",
    "Tyrese Maxey",
    "Cade Cunningham",
    "Luka Doncic",
    "Tyrese Maxey",
    "Trey Murphy",
    "Victor Wembanyama",
    "Luka Doncic",
    "Jaylen Brown",
    "Alex Sarr",
    "Luka Doncic",
    "Jamal Murray",
    "Kawhi Leonard",
    "Cade Cunningham",
    "Jalen Johnson",
    "Victor Wembanyama",
    "Tyrese Maxey",
    "Not Awarded",
    "Not Awarded",
    "Stephen Curry",
    "Austin Reaves",
    "Paolo Banchero",
    "Devin Booker",
    "Nikola Jokic",
    "Nikola Jokic",
    "Nikola Jokic",
    "Alperen Sengun",
    "Nikola Jokic",
    "Nikola Jokic",
    "Karl-Anthony Towns",
    "Evan Mobley",
    "Nikola Jokic",
    "Derrick White",
    "Nikola Jokic",
    "Nikola Jokic",
    "Kevin Durant",
    "Nikola Jokic",
    "Nikola Jokic",
    "Kawhi Leonard",
    "Deni Avdija",
    "LeBron James",
    "Stephen Curry",
    "James Harden",
    "Kevin Durant",
    "Chet Holmgren",
    "Anthony Edwards",
    "Evan Mobley",
    "Michael Porter",
    "Nikola Jokic",
    "Nikola Jokic",
    "Stephon Castle",
    "Julius Randle",
    "Nikola Jokic",
    "Karl-Anthony Towns",
    "Alperen Sengun",
    "Not Awarded",
    "Not Awarded",
    "Cedric Coward",
    "Kon Knueppel",
    "Kon Knueppel",
    "Kon Knueppel",
    "Not Awarded",
    "Cooper Flagg",
    "Cooper Flagg",
    "Cooper Flagg",
    "Maxime Raynaud",
    "Scottie Barnes",
    "Shai Gilgeous-Alexander",
    "Tyrese Maxey",
    "Cade Cunningham",
    "Donovan Mitchell",
    "Jalen Johnson",
    "Jaylen Brown",
    "Victor Wembanyama",
    "Luka Doncic",
    "Bam Adebayo",
    "Jamal Murray",
    "Deni Avdija",
    "Nikola Jokic",
    "Julius Randle",
    "Derrick White",
    "Karl-Anthony Towns",
    "Evan Mobley",
    "Amen Thompson",
    "Mikal Bridges",
    "Kevin Durant",
    "Chet Holmgren",
    "Alperun Sengun",
    "Anthony Edwards",
    "Naz Reid"
]

def get_multiple_player_conf(df, player_list, year):
    output = {}
    
    for player in player_list:
        confs = df.loc[
            (df["name"] == player) & (df["Year"] == year),
            "team_name"
        ].dropna().unique().tolist()
        
        output[player] = confs
    
    return output

# Run function
results = get_multiple_player_conf(df, players, 2026)

df_results = pd.DataFrame([
    {"player": player, "conf": conf}
    for player, confs in results.items()
    for conf in confs
])