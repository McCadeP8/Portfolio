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
get_player_conf2(df, "Anthony Edwards", 2022)


players = [
    "Harrison Barnes",
    "Julius Randle",
    "Ja Morant",
    "Karl-Anthony Towns",
    "Dejounte Murray",
    "Montrezl Harrell",
    "LeBron James",
    "Nikola Jokic",
    "Al Horford",
    "Nikola Jokic",
    "Giannis Antetokounmpo",
    "Kevin Durant",
    "Stephen Curry",
    "Tyrese Maxey",
    "Anthony Davis",
    "Nikola Jokic",
    "Karl-Anthony Towns",
    "Nikola Jokic",
    "DeMar DeRozan",
    "Jayson Tatum",
    "Anthony Edwards",
    "Trae Young",
    "LeBron James",
    "Stephen Curry",
    "Jae'Sean Tate",
    "LaMelo Ball",
    "Bobby Portis",
    "Dejounte Murray",
    "John Collins",
    "Trae Young",
    "Jarrett Allen",
    "Nikola Jokic",
    "Kevin Durant",
    "Kristaps Porzingis",
    "Damian Lillard",
    "Saddiq Bey",
    "Devin Booker",
    "Shai Gilgeous-Alexander",
    "James Harden",
    "LeBron James",
    "Ja Morant",
    "LeBron James",
    "Fred VanVleet",
    "Giannis Antetokounmpo",
    "Jayson Tatum",
    "Nikola Jokic",
    "Jaren Jackson Jr.",
    "Jaylen Brown",
    "James Harden",
    "Shai Gilgeous-Alexander",
    "Joel Embiid",
    "Nikola Jokic",
    "Chris Duarte",
    "Luka Doncic",
    "Jayson Tatum",
    "Nikola Jokic",
    "Joel Embiid",
    "Nikola Jokic",
    "Jimmy Butler",
    "Karl-Anthony Towns",
    "Bam Adebayo",
    "Pascal Siakam",
    "Giannis Antetokounmpo",
    "Nikola Jokic",
    "Giannis Antetokounmpo",
    "Julius Randle",
    "Joel Embiid",
    "Nikola Jokic",
    "Giannis Antetokounmpo",
    "Luka Doncic",
    "Devin Booker",
    "Jayson Tatum",
    "Pascal Siakam",
    "Scottie Barnes",
    "Karl-Anthony Towns",
    "Nikola Jokic"
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
results = get_multiple_player_conf(df, players, 2022)

df_results = pd.DataFrame([
    {"player": player, "conf": conf}
    for player, confs in results.items()
    for conf in confs
])