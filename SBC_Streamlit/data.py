from datetime import date, timedelta
from math import ceil

league_start_date = date(2025, 10, 21)
today = date.today() + timedelta(days=0)
period = max(1, min(163, (today - league_start_date).days + 1))

if today.month in [8, 9] or (today.month == 7 and today.day >= 2):
    year_offset = 0
else:
    year_offset = 1

if today.month > 7 or (today.month == 7 and today.day >= 2):
    current_year = today.year + 1
else:
    current_year = today.year

columns_order = [str(current_year + i) for i in range(7)]

current_salary_cap = 154647000
current_luxury_tax = 187895000
current_apron_1 = 195945000
current_apron_2 = 207824000
tax_bracket_increment = 5685000
league_ratio = ceil(current_salary_cap/60000000)*1000000
max_cash = 7964000
league_id = "u9f8f7o9mavp4dt1"

type_colors = {
    "Guaranteed": "#FCE5CD",   
    "Non-Guaranteed": "#F4CCCC",
    "Team": "#CFE2F3",         
    "Dead": "#D9D9D9",         
    "Unrestricted": "#D9D2E9", 
    "Restricted": "#CFFFFF", 
    "Draft Rights": "#D9D9D9",
}

team_info = {
    "Albuquerque": {"conf": "West", "bg": "#D72C2C", "bg2": "#281B0D", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxamop_aMAIM8OV?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMOfTbUAA0QzS?format=jpg&name=medium",
        "nickname": "Armadillos"},

    "Anaheim": {"conf": "West", "bg": "#DA0F10", "bg2": "#FFB1B1", "text": "white",
        "logo": "https://pbs.twimg.com/media/FxamoqBaQAAQSwY?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMRu7bAAArhA9?format=jpg&name=medium",
        "nickname": "Mice"},

    "Anchorage": {"conf": "West", "bg": "#454B55", "bg2": "#B8C4C4", "text": "white",
        "logo": "https://pbs.twimg.com/media/FxamoqAaYAEpifP?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANiSzSb0AAFwtG?format=jpg&name=medium",
        "nickname": "Killer Whales"},

    "Austin": {"conf": "West", "bg": "#040404", "bg2": "#BB8549", "text": "white",
        "logo": "https://pbs.twimg.com/media/FxvLuE8acAAUiBQ?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMKhgbkAEDRaf?format=jpg&name=medium",
        "nickname": "Bats"},

    "Baltimore": {"conf": "East", "bg": "#00CED1", "bg2": "#FBF5E1", "text": "black",
        "logo": "https://pbs.twimg.com/media/Fxamr7daQAAhwSx?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANiSzTawAEYp_j?format=jpg&name=medium",
        "nickname": "Blue Crabs"},

    "Birmingham": {"conf": "East", "bg": "#853500", "bg2": "#EA2507", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxamr8GaMAE5xbG?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANL-RLakAA902R?format=png&name=medium",
        "nickname": "Bandits"},

    "Boise": {"conf": "West", "bg": "#744529", "bg2": "#EAD676", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxamr80aEAAWgO1?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANiVTnasAAfKtH?format=jpg&name=medium",
        "nickname": "Spuds"},

    "Buffalo": {"conf": "East", "bg": "#152238", "bg2": "#FFDE3A", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxamr7JaYAADNSj?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMEUxaYAALcTw?format=png&name=medium",
        "nickname": "Daredevils"},

    "Cincinnati": {"conf": "East", "bg": "#FFEA61", "bg2": "#D2691E", "text": "black",
        "logo": "https://pbs.twimg.com/media/FxamtxqaMAAoWvU?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMBfgbAAA-uur?format=jpg&name=medium",
        "nickname": "Chili"},

    "Columbus": {"conf": "East", "bg": "#CD7F32", "bg2": "#666666", "text": "white",
        "logo": "https://pbs.twimg.com/media/FxamtzbaUAEvyXi?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMBfcbgAAJNoC?format=jpg&name=medium",
        "nickname": "Arches"},

    "Des Moines": {"conf": "East", "bg": "#1B1E23", "bg2": "#F7F7EE", "text": "white",
        "logo": "https://pbs.twimg.com/media/FxamtzcaMAAPdlW?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANL-RRawAA-Nkf?format=jpg&name=medium",
        "nickname": "Racoons"},

    "El Paso": {"conf": "West", "bg": "#F8EFAE", "bg2": "#2A623D", "text": "black",
        "logo": "https://pbs.twimg.com/media/FxamtxraQAANsYd?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANjbVMbwAA7DTW?format=png&name=medium",
        "nickname": "Vipers"},

    "Honolulu": {"conf": "West", "bg": "#CDC0C0", "bg2": "#FAFBF5", "text": "black",
        "logo": "https://pbs.twimg.com/media/FxamvzcaUAAnl_g?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANiSzRbIAE7i0d?format=jpg&name=medium",
        "nickname": "Diamonds"},

    "Jacksonville": {"conf": "East", "bg": "#36454F", "bg2": "#B0E0E6", "text": "white",
        "logo": "https://pbs.twimg.com/media/FxamvzoaIAAd9nF?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANL6y-aAAAghlA?format=jpg&name=medium",
        "nickname": "Manatees"},

    "Kentucky": {"conf": "East", "bg": "#663399", "bg2": "#FFFF00", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxamv04aQAQl4UB?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANL-RNbEAA_Dg_?format=jpg&name=medium",
        "nickname": "Thoroughbreds"},

    "Lansing": {"conf": "East", "bg": "#B9EFE1", "bg2": "#197419", "text": "black",
        "logo": "https://pbs.twimg.com/media/Fxamv1ZacAAfxMM?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANL-RJboAEqm60?format=jpg&name=medium",
        "nickname": "Lagoon"},

    "Lincoln": {"conf": "West", "bg": "#FC6A03", "bg2": "#1520A6", "text": "black",
        "logo": "https://pbs.twimg.com/media/Fxamx14aEAAyD29?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMOj2agAA139A?format=jpg&name=medium",
        "nickname": "Bully"},

    "Little Rock": {"conf": "East", "bg": "#710193", "bg2": "#E39FF6", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxamx2xaYAAqupS?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANL6zAbAAIrPa_?format=jpg&name=medium",
        "nickname": "Big Foot"},

    "Manchester": {"conf": "East", "bg": "#D7F2FA", "bg2": "#C20700", "text": "black",
        "logo": "https://pbs.twimg.com/media/Fxamx3nagAAZXCI?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANiQhVaUAEw78l?format=jpg&name=medium",
        "nickname": "Trout"},

    "Nashville": {"conf": "East", "bg": "#450012", "bg2": "#93A9AE", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxamx01aMAAD8na?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANL6y-bQAAWomv?format=jpg&name=medium",
        "nickname": "Strings"},

    "Pittsburgh": {"conf": "East", "bg": "#F1F137", "bg2": "#32322C", "text": "black",
        "logo": "https://pbs.twimg.com/media/Fxam0E7agAAc1zF?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMBfqaoAA1noJ?format=png&name=medium",
        "nickname": "Bridge"},

    "Providence": {"conf": "East", "bg": "#BF0A30", "bg2": "#1C2E4A", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxam0GKaQAAlzwx?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMBfkbwAApvJb?format=jpg&name=medium",
        "nickname": "Pilgrims"},

    "San Diego": {"conf": "West", "bg": "#31439B", "bg2": "#0BB5FF", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxam0INacAIC29O?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANiQgIawAAEZC9?format=jpg&name=medium",
        "nickname": "Seals"},

    "San Jose": {"conf": "West", "bg": "#97EBF4", "bg2": "#EDFF21", "text": "black",
        "logo": "https://pbs.twimg.com/media/Fxam0EvaIAAcI_3?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANiQhVbAAApSML?format=jpg&name=medium",
        "nickname": "Seagulls"},

    "Seattle": {"conf": "West", "bg": "#006241", "bg2": "#FFFFFF", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxam1s5aAAIanao?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMOfYaIAAUPiY?format=jpg&name=medium",
        "nickname": "Brew"},

    "St. Louis": {"conf": "West", "bg": "#B7B1AE", "bg2": "#B90E0A", "text": "black",
        "logo": "https://pbs.twimg.com/media/Fxam1ugaEAUkbUi?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMLQobQAAdeDO?format=jpg&name=medium",
        "nickname": "66ers"},

    "Tampa Bay": {"conf": "East", "bg": "#FC8EAC", "bg2": "#313639", "text": "black",
        "logo": "https://pbs.twimg.com/media/G_eTqPpacAIV82Y?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANiQhMboAAO1cd?format=jpg&name=medium",
        "nickname": "Flamingos"},

    "Tulsa": {"conf": "West", "bg": "#333333", "bg2": "#656565", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxam1s7aQAAiSsW?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMEU0bwAA95nZ?format=png&name=medium",
        "nickname": "Tornado"},

    "Vancouver": {"conf": "West", "bg": "#17780D", "bg2": "#CACE00", "text": "black",
        "logo": "https://pbs.twimg.com/media/Fxam4eaaMAAW6Pz?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMKg-bAAEpRBD?format=jpg&name=medium",
        "nickname": "Forest"},

    "Vegas": {"conf": "West", "bg": "#35654D", "bg2": "#B8000A", "text": "white",
        "logo": "https://pbs.twimg.com/media/Fxam4dlaIAIKnBb?format=png&name=small",
        "wordmark": "https://pbs.twimg.com/media/HANMVMPb0AAwdh2?format=jpg&name=medium",
        "nickname": "Blackjack"},
}

cap_sheets_to_fantrax_name_fix = {
    "Eugeny Omoruyi": "Eugene Omoruyi",
    "Kenneth Lofton Jr.": "Kenneth Lofton",
    "Lonnie Walker IV": "Lonnie Walker",
    "N'Faly Dante": "NFaly Dante",
    "Vasilije Micić": "Vasilije Micic",
    "Bogdan Bogdanović": "Bogdan Bogdanovic",
    "D'Angelo Russell": "DAngelo Russell",
    "Gary Trent Jr.": "Gary Trent",
    "Jonas Valančiūnas": "Jonas Valanciunas",
    "Kevin Porter Jr.": "Kevin Porter",
    "Larry Nance Jr.": "Larry Nance",
    "Nae'Qwan Tomlin": "NaeQwan Tomlin",
    "Tim Hardaway Jr.": "Tim Hardaway",
    "Alperen Şengün": "Alperen Sengun",
    "Cam Thomas": "Cameron Thomas",
    "Dennis Schröder": "Dennis Schroder",
    "Trey Murphy III": "Trey Murphy",
    "Ron Harper Jr.": "Ron Harper",
    "A.J. Green": "AJ Green",
    "Alexandre Sarr": "Alex Sarr",
    "Bub Carrington": "Carlton Carrington",
    "Jae'Sean Tate": "JaeSean Tate",
    "Dario Šarić": "Dario Saric",
    "Dariq Miller-Whitehead": "Dariq Whitehead",
    "DaRon Holmes II": "DaRon Holmes",
    "Day'Ron Sharpe": "DayRon Sharpe",
    "De'Aaron Fox": "DeAaron Fox",
    "De'Andre Hunter": "DeAndre Hunter",
    "De'Anthony Melton": "DeAnthony Melton",
    "Derrick Jones Jr.": "Derrick Jones",
    "Ja'Kobe Walter": "JaKobe Walter",
    "Jabari Smith Jr.": "Jabari Smith",
    "Jaren Jackson Jr.": "Jaren Jackson",
    "Jusuf Nurkić": "Jusuf Nurkic",
    "Kel El Ware": "Kelel Ware",
    "Kenyon Martin Jr.": "Kenyon Martin",
    "Kristaps Porziņģis": "Kristaps Porzingis",
    "Luka Dončić": "Luka Doncic",
    "Marvin Bagley III": "Marvin Bagley",
    "Michael Porter Jr.": "Michael Porter",
    "Nic Claxton": "Nicolas Claxton",
    "Nikola Jokić": "Nikola Jokic",
    "Nikola Jović": "Nikola Jovic",
    "Nikola Vučević": "Nikola Vucevic",
    "Patrick Baldwin Jr.": "Patrick Baldwin",
    "Ricky Council IV": "Ricky Council",
    "Rob Dillingham": "Robert Dillingham",
    "Royce O'Neale": "Royce ONeale",
    "Scotty Pippen Jr.": "Scotty Pippen",
    "Terrence Shannon Jr.": "Terrence Shannon",
    "TyTy Washington Jr.": "TyTy Washington",
    "Vince Williams Jr.": "Vince Williams",
    "Vlad Goldin": "Vladislav Goldin",
    "Vrenz Bjleijenbergh": "Vander Blue",
    "Walter Clayton Jr.": "Walter Clayton",
    "Wendell Carter Jr.": "Wendell Carter",
    "Xavier Tillman Sr.": "Xavier Tillman",
    "Bojan Bogdanović": "Bojan Bogdanovic",
    "Dāvis Bertāns": "Davis Bertans",
    "Devonte' Graham": "Devonte Graham",
}
