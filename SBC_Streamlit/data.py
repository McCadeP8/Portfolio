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
league_id = "ka3frpayly11teos"

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
    "Albuquerque": {"bg": "#D72C2C", "bg2": "#281B0D", "text": "white", "logo": "https://pbs.twimg.com/media/Fxamop_aMAIM8OV?format=png&name=small", "nickname": "Armadillos"},
    "Anaheim": {"bg": "#DA0F10", "bg2": "#FFB1B1", "text": "white", "logo": "https://pbs.twimg.com/media/FxamoqBaQAAQSwY?format=png&name=small", "nickname": "Mice"},
    "Anchorage": {"bg": "#454B55", "bg2": "#B8C4C4", "text": "white", "logo": "https://pbs.twimg.com/media/FxamoqAaYAEpifP?format=png&name=small", "nickname": "Killer Whales"},
    "Austin": {"bg": "#040404", "bg2": "#BB8549", "text": "white", "logo": "https://pbs.twimg.com/media/FxvLuE8acAAUiBQ?format=png&name=small", "nickname": "Bats"},
    "Baltimore": {"bg": "#00CED1", "bg2": "#FBF5E1", "text": "black", "logo": "https://pbs.twimg.com/media/Fxamr7daQAAhwSx?format=png&name=small", "nickname": "Blue Crabs"},
    "Birmingham": {"bg": "#853500", "bg2": "#EA2507", "text": "white", "logo": "https://pbs.twimg.com/media/Fxamr8GaMAE5xbG?format=png&name=small", "nickname": "Bandits"},
    "Boise": {"bg": "#744529", "bg2": "#EAD676", "text": "white", "logo": "https://pbs.twimg.com/media/Fxamr80aEAAWgO1?format=png&name=small", "nickname": "Spuds"},
    "Buffalo": {"bg": "#152238", "bg2": "#FFDE3A", "text": "white", "logo": "https://pbs.twimg.com/media/Fxamr7JaYAADNSj?format=png&name=small", "nickname": "Daredevils"},
    "Cincinnati": {"bg": "#FFEA61", "bg2": "#D2691E", "text": "black", "logo": "https://pbs.twimg.com/media/FxamtxqaMAAoWvU?format=png&name=small", "nickname": "Chili"},
    "Columbus": {"bg": "#CD7F32", "bg2": "#666666", "text": "white", "logo": "https://pbs.twimg.com/media/FxamtzbaUAEvyXi?format=png&name=small", "nickname": "Arches"},
    "Des Moines": {"bg": "#1B1E23", "bg2": "#F7F7EE", "text": "white", "logo": "https://pbs.twimg.com/media/FxamtzcaMAAPdlW?format=png&name=small", "nickname": "Racoons"},
    "El Paso": {"bg": "#F8EFAE", "bg2": "#2A623D", "text": "black", "logo": "https://pbs.twimg.com/media/FxamtxraQAANsYd?format=png&name=small", "nickname": "Vipers"},
    "Honolulu": {"bg": "#CDC0C0", "bg2": "#FAFBF5", "text": "black", "logo": "https://pbs.twimg.com/media/FxamvzcaUAAnl_g?format=png&name=small", "nickname": "Diamonds"},
    "Jacksonville": {"bg": "#36454F", "bg2": "#B0E0E6", "text": "white", "logo": "https://pbs.twimg.com/media/FxamvzoaIAAd9nF?format=png&name=small", "nickname": "Manatees"},
    "Kentucky": {"bg": "#663399", "bg2": "#FFFF00", "text": "white", "logo": "https://pbs.twimg.com/media/Fxamv04aQAQl4UB?format=png&name=small", "nickname": "Thoroughbreds"},
    "Lansing": {"bg": "#B9EFE1", "bg2": "#197419", "text": "black", "logo": "https://pbs.twimg.com/media/Fxamv1ZacAAfxMM?format=png&name=small", "nickname": "Lagoon"},
    "Lincoln": {"bg": "#FC6A03", "bg2": "#1520A6", "text": "black", "logo": "https://pbs.twimg.com/media/Fxamx14aEAAyD29?format=png&name=small", "nickname": "Bully"},
    "Little Rock": {"bg": "#710193", "bg2": "#E39FF6", "text": "white", "logo": "https://pbs.twimg.com/media/Fxamx2xaYAAqupS?format=png&name=small", "nickname": "Big Foot"},
    "Manchester": {"bg": "#D7F2FA", "bg2": "#C20700", "text": "black", "logo": "https://pbs.twimg.com/media/Fxamx3nagAAZXCI?format=png&name=small", "nickname": "Trout"},
    "Nashville": {"bg": "#450012", "bg2": "#93A9AE", "text": "white", "logo": "https://pbs.twimg.com/media/Fxamx01aMAAD8na?format=png&name=small", "nickname": "Strings"},
    "Pittsburgh": {"bg": "#F1F137", "bg2": "#32322C", "text": "black", "logo": "https://pbs.twimg.com/media/Fxam0E7agAAc1zF?format=png&name=small", "nickname": "Bridge"},
    "Providence": {"bg": "#BF0A30", "bg2": "#1C2E4A", "text": "white", "logo": "https://pbs.twimg.com/media/Fxam0GKaQAAlzwx?format=png&name=small", "nickname": "Pilgrims"},
    "San Diego": {"bg": "#31439B", "bg2": "#0BB5FF", "text": "white", "logo": "https://pbs.twimg.com/media/Fxam0INacAIC29O?format=png&name=small", "nickname": "Seals"},
    "San Jose": {"bg": "#97EBF4", "bg2": "#EDFF21", "text": "black", "logo": "https://pbs.twimg.com/media/Fxam0EvaIAAcI_3?format=png&name=small", "nickname": "Seagulls"},
    "Seattle": {"bg": "#006241", "bg2": "#FFFFFF", "text": "white", "logo": "https://pbs.twimg.com/media/Fxam1s5aAAIanao?format=png&name=small", "nickname": "Brew"},
    "St. Louis": {"bg": "#B7B1AE", "bg2": "#B90E0A", "text": "black", "logo": "https://pbs.twimg.com/media/Fxam1ugaEAUkbUi?format=png&name=small", "nickname": "66ers"},
    "Tampa Bay": {"bg": "#FC8EAC", "bg2": "#313639", "text": "black", "logo": "https://pbs.twimg.com/media/G_eTqPpacAIV82Y?format=png&name=small", "nickname": "Flamingos"},
    "Tulsa": {"bg": "#333333", "bg2": "#656565", "text": "white", "logo": "https://pbs.twimg.com/media/Fxam1s7aQAAiSsW?format=png&name=small", "nickname": "Tornado"},
    "Vancouver": {"bg": "#17780D", "bg2": "#CACE00", "text": "black", "logo": "https://pbs.twimg.com/media/Fxam4eaaMAAW6Pz?format=png&name=small", "nickname": "Forest"},
    "Vegas": {"bg": "#35654D", "bg2": "#B8000A", "text": "white", "logo": "https://pbs.twimg.com/media/Fxam4dlaIAIKnBb?format=png&name=small", "nickname": "Blackjack"},
}

cap_sheets_to_fantrax_name_fix = {
    "Eugeny Omoruyi": "Eugeny Omoruyi",
    "Kenneth Lofton Jr.": "Kenneth Lofton Jr.",
    "Lonnie Walker IV": "Lonnie Walker IV",
    "N'Faly Dante": "N'Faly Dante",
    "Vasilije Micić": "Vasilije Micić",
    "Bogdan Bogdanović": "Bogdan Bogdanović",
    "D'Angelo Russell": "D'Angelo Russell",
    "Gary Trent Jr.": "Gary Trent Jr.",
    "Jonas Valančiūnas": "Jonas Valančiūnas",
    "Kevin Porter Jr.": "Kevin Porter Jr.",
    "Larry Nance Jr.": "Larry Nance Jr.",
    "Nae'Qwan Tomlin": "Nae'Qwan Tomlin",
    "Tim Hardaway Jr.": "Tim Hardaway Jr.",
    "Alperen Şengün": "Alperen Şengün",
    "Cam Thomas": "Cam Thomas",
    "Dennis Schröder": "Dennis Schröder",
    "Trey Murphy III": "Trey Murphy III",
    "Ron Harper Jr.": "Ron Harper Jr.",
    "A.J. Green": "A.J. Green",
    "Alexandre Sarr": "Alexandre Sarr",
    "Bub Carrington": "Bub Carrington",
    "Jae'Sean Tate": "Jae'Sean Tate",
    "Dario Šarić": "Dario Šarić",
    "Dariq Miller-Whitehead": "Dariq Miller-Whitehead",
    "DaRon Holmes II": "DaRon Holmes II",
    "Day'Ron Sharpe": "Day'Ron Sharpe",
    "De'Aaron Fox": "De'Aaron Fox",
    "De'Andre Hunter": "De'Andre Hunter",
    "De'Anthony Melton": "De'Anthony Melton",
    "Derrick Jones Jr.": "Derrick Jones Jr.",
    "Ja'Kobe Walter": "Ja'Kobe Walter",
    "Jabari Smith Jr.": "Jabari Smith Jr.",
    "Jaren Jackson Jr.": "Jaren Jackson Jr.",
    "Jusuf Nurkić": "Jusuf Nurkic",
    "Kel El Ware": "Kel El Ware",
    "Kenyon Martin Jr.": "Kenyon Martin Jr.",
    "Kristaps Porziņģis": "Kristaps Porziņģis",
    "Luka Dončić": "Luka Dončić",
    "Marvin Bagley III": "Marvin Bagley III",
    "Michael Porter Jr.": "Michael Porter Jr.",
    "Nic Claxton": "Nic Claxton",
    "Nikola Jokić": "Nikola Jokić",
    "Nikola Jović": "Nikola Jović",
    "Nikola Vučević": "Nikola Vučević",
    "Patrick Baldwin Jr.": "Patrick Baldwin Jr.",
    "Ricky Council IV": "Ricky Council IV",
    "Rob Dillingham": "Rob Dillingham",
    "Royce O'Neale": "Royce O'Neale",
    "Scotty Pippen Jr.": "Scotty Pippen Jr.",
    "Terrence Shannon Jr.": "Terrence Shannon Jr.",
    "TyTy Washington Jr.": "TyTy Washington Jr.",
    "Vince Williams Jr.": "Vince Williams Jr.",
    "VJ Edgecomb": "VJ Edgecomb",
    "Vlad Goldin": "Vlad Goldin",
    "Vrenz Bjleijenbergh": "Vrenz Bjleijenbergh",
    "Walter Clayton Jr.": "Walter Clayton Jr.",
    "Wendell Carter Jr.": "Wendell Carter Jr.",
    "Xavier Tillman Sr.": "Xavier Tillman Sr.",
    "Zaccharie Risacher": "Zaccharie Risacher",
    "Bojan Bogdanović": "Bojan Bogdanović",
    "Dāvis Bertāns": "Dāvis Bertāns",
    "Devonte' Graham": "Devonte' Graham",
}
