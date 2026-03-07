# import streamlit as st
# import pydeck as pdk
# import pandas as pd
# import math
# from datetime import date

# st.set_page_config(page_title="NBA Travel Tracker", layout="wide", page_icon="✈️")

# # ── Styles ────────────────────────────────────────────────────────────────────
# st.markdown("""
# <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
# <style>
#   [data-testid="stAppViewContainer"] { background: #080c14; }
#   [data-testid="stSidebar"]          { background: #0d1117; border-right: 1px solid #1e2d40; }
#   [data-testid="stSidebar"] * { color: #c9d8e8 !important; }
#   h1, h2, h3 { font-family: 'Orbitron', monospace !important; }
#   .block-container { padding-top: 1.5rem; }

#   .trip-card {
#     background: linear-gradient(135deg, #0d1f33 0%, #0a1520 100%);
#     border: 1px solid #1a3a5c;
#     border-left: 3px solid #00aaff;
#     border-radius: 10px;
#     padding: 14px 18px;
#     margin-bottom: 10px;
#     font-family: 'DM Mono', monospace;
#     font-size: 13px;
#     color: #a8c8e8;
#   }
#   .trip-card .leg-header { color: #00aaff; font-weight: 700; font-size: 14px; margin-bottom: 4px; }
#   .trip-card .miles      { color: #00ffcc; font-size: 11px; margin-top: 4px; }
#   .trip-card .past       { border-left-color: #334455; opacity: 0.6; }

#   .stat-box {
#     background: #0d1f33;
#     border: 1px solid #1a3a5c;
#     border-radius: 8px;
#     padding: 12px;
#     text-align: center;
#     font-family: 'DM Mono', monospace;
#   }
#   .stat-num { font-size: 26px; font-weight: 700; color: #00aaff; font-family: 'Orbitron', monospace; }
#   .stat-lbl { font-size: 11px; color: #557799; margin-top: 2px; letter-spacing: 0.08em; }

#   .page-title {
#     font-family: 'Orbitron', monospace;
#     font-size: 28px;
#     font-weight: 900;
#     color: #ffffff;
#     letter-spacing: 0.06em;
#     margin-bottom: 0;
#   }
#   .page-sub {
#     font-family: 'DM Mono', monospace;
#     font-size: 13px;
#     color: #446688;
#     margin-top: 2px;
#     margin-bottom: 18px;
#   }
# </style>
# """, unsafe_allow_html=True)

# # ── Team data ─────────────────────────────────────────────────────────────────
# TEAMS = {
#     "Boston Celtics":        {"city": "Boston",        "lat": 42.3601, "lon": -71.0589, "color": [0,  122, 51],  "abbr": "BOS"},
#     "Golden State Warriors": {"city": "San Francisco", "lat": 37.7749, "lon": -122.4194,"color": [29,  66,138],  "abbr": "GSW"},
#     "LA Lakers":             {"city": "Los Angeles",   "lat": 34.0430, "lon": -118.2673,"color": [85,  37,130],  "abbr": "LAL"},
#     "Miami Heat":            {"city": "Miami",         "lat": 25.7814, "lon": -80.1870, "color": [152, 0,  46],  "abbr": "MIA"},
#     "Chicago Bulls":         {"city": "Chicago",       "lat": 41.8807, "lon": -87.6742, "color": [206, 17, 65],  "abbr": "CHI"},
#     "Dallas Mavericks":      {"city": "Dallas",        "lat": 32.7767, "lon": -96.7970, "color": [0,   83,188],  "abbr": "DAL"},
#     "Denver Nuggets":        {"city": "Denver",        "lat": 39.7392, "lon": -104.9903,"color": [13, 34, 64],   "abbr": "DEN"},
#     "New York Knicks":       {"city": "New York",      "lat": 40.7128, "lon": -74.0060, "color": [0,  107,182],  "abbr": "NYK"},
#     "Phoenix Suns":          {"city": "Phoenix",       "lat": 33.4455, "lon": -112.0712,"color": [29,  17, 96],  "abbr": "PHX"},
#     "Toronto Raptors":       {"city": "Toronto",       "lat": 43.6435, "lon": -79.3791, "color": [206, 17, 65],  "abbr": "TOR"},
#     "London Testicles":       {"city": "London",       "lat": 51.5072, "lon": 0.1276, "color": [206, 17, 65],  "abbr": "LOND"},

# }

# # Sample road trip schedule — (opponent, date, home/away)
# SCHEDULES = {
#     "Boston Celtics": [
#         ("Miami Heat",        date(2025,  2,  5), "away"),
#         ("Chicago Bulls",     date(2025,  2,  7), "away"),
#         ("New York Knicks",   date(2025,  2,  9), "away"),
#         ("London Testicles",   date(2025,  2,  10), "away"),
#         ("Toronto Raptors",   date(2025,  2, 11), "away"),
#         ("Boston Celtics",    date(2025,  2, 14), "home"),
#         ("Dallas Mavericks",  date(2025,  2, 18), "away"),
#         ("Denver Nuggets",    date(2025,  2, 20), "away"),
#         ("Golden State Warriors", date(2025, 2, 22), "away"),
#         ("LA Lakers",         date(2025,  2, 24), "away"),
#         ("Boston Celtics",    date(2025,  2, 27), "home"),
#     ],
#     "Golden State Warriors": [
#         ("LA Lakers",         date(2025,  2,  4), "away"),
#         ("Phoenix Suns",      date(2025,  2,  6), "away"),
#         ("Denver Nuggets",    date(2025,  2,  8), "away"),
#         ("Dallas Mavericks",  date(2025,  2, 10), "away"),
#         ("Golden State Warriors", date(2025, 2, 13), "home"),
#         ("Chicago Bulls",     date(2025,  2, 17), "away"),
#         ("Miami Heat",        date(2025,  2, 19), "away"),
#         ("New York Knicks",   date(2025,  2, 21), "away"),
#         ("Boston Celtics",    date(2025,  2, 23), "away"),
#         ("Golden State Warriors", date(2025, 2, 26), "home"),
#     ],
# }
# # Fill remaining teams with a short generic trip
# for team in TEAMS:
#     if team not in SCHEDULES:
#         opponents = [t for t in list(TEAMS.keys()) if t != team][:5]
#         SCHEDULES[team] = [(opp, date(2025, 2, 4 + i*2), "away") for i, opp in enumerate(opponents)] + \
#                           [(team, date(2025, 2, 15), "home")]

# # ── Helpers ───────────────────────────────────────────────────────────────────
# def haversine(lat1, lon1, lat2, lon2):
#     R = 3958.8
#     φ1, φ2 = math.radians(lat1), math.radians(lat2)
#     dφ = math.radians(lat2 - lat1)
#     dλ = math.radians(lon2 - lon1)
#     a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
#     return R * 2 * math.asin(math.sqrt(a))

# def arc_points(lat1, lon1, lat2, lon2, n=40):
#     """Generate intermediate points along a great-circle arc."""
#     pts = []
#     for i in range(n + 1):
#         t = i / n
#         lat = lat1 + t * (lat2 - lat1)
#         lon = lon1 + t * (lon2 - lon1)
#         # add slight vertical bow
#         bow = math.sin(math.pi * t) * 3
#         pts.append([lon, lat + bow])
#     return pts

# def build_trip_legs(team_name, schedule):
#     """Turn a schedule into a list of travel legs."""
#     home = TEAMS[team_name]
#     legs = []
#     current_lat, current_lon, current_city = home["lat"], home["lon"], home["city"]

#     for opponent, game_date, ha in schedule:
#         dest = TEAMS[opponent]
#         if ha == "home":
#             dest_lat, dest_lon, dest_city = home["lat"], home["lon"], home["city"]
#         else:
#             dest_lat, dest_lon, dest_city = dest["lat"], dest["lon"], dest["city"]

#         if current_city == dest_city:
#             current_lat, current_lon, current_city = dest_lat, dest_lon, dest_city
#             continue

#         miles = haversine(current_lat, current_lon, dest_lat, dest_lon)
#         legs.append({
#             "from_city":  current_city,
#             "to_city":    dest_city,
#             "from_lat":   current_lat,
#             "from_lon":   current_lon,
#             "to_lat":     dest_lat,
#             "to_lon":     dest_lon,
#             "miles":      miles,
#             "date":       game_date,
#             "opponent":   opponent,
#             "home_away":  ha,
#             "path":       arc_points(current_lat, current_lon, dest_lat, dest_lon),
#         })
#         current_lat, current_lon, current_city = dest_lat, dest_lon, dest_city

#     return legs

# # ── Sidebar ───────────────────────────────────────────────────────────────────
# with st.sidebar:
#     st.markdown("### ✈️ TEAM TRAVEL TRACKER")
#     st.divider()
#     selected_team = st.selectbox("Select Team", list(TEAMS.keys()))
#     today = st.date_input("Today's Date", value=date(2025, 2, 14))
#     show_past = st.toggle("Show Past Legs", value=True)
#     st.divider()
#     st.caption("Arc lines show team travel routes.\nGlow = upcoming game.")

# team_info = TEAMS[selected_team]
# schedule  = SCHEDULES[selected_team]
# legs      = build_trip_legs(selected_team, schedule)

# past_legs     = [l for l in legs if l["date"] <  today]
# upcoming_legs = [l for l in legs if l["date"] >= today]
# visible_legs  = (past_legs if show_past else []) + upcoming_legs

# # ── Build pydeck layers ───────────────────────────────────────────────────────
# team_color   = team_info["color"]
# team_color_a = team_color + [220]

# # Arc paths
# path_data = []
# for leg in visible_legs:
#     is_past = leg["date"] < today
#     color = [255, 220, 0, 200]    
#     path_data.append({"path": leg["path"], "color": color, "width": 2 if is_past else 4})

# path_layer = pdk.Layer(
#     "PathLayer",
#     data=path_data,
#     get_path="path",
#     get_color="color",
#     get_width="width",
#     width_scale=1,
#     width_min_pixels=1,
#     pickable=False,
# )

# # City dots — all cities visited
# visited = {}
# for leg in visible_legs:
#     visited[leg["from_city"]] = (leg["from_lat"], leg["from_lon"])
#     visited[leg["to_city"]]   = (leg["to_lat"],   leg["to_lon"])

# dot_data = [{"city": c, "lat": v[0], "lon": v[1]} for c, v in visited.items()]

# dot_layer = pdk.Layer(
#     "ScatterplotLayer",
#     data=dot_data,
#     get_position="[lon, lat]",
#     get_radius=35000,
#     get_fill_color=team_color_a,
#     get_line_color=[255, 255, 255, 180],
#     stroked=True,
#     line_width_min_pixels=1,
#     pickable=True,
# )

# # Home base pulsing ring
# home_layer = pdk.Layer(
#     "ScatterplotLayer",
#     data=[{"lat": team_info["lat"], "lon": team_info["lon"]}],
#     get_position="[lon, lat]",
#     get_radius=60000,
#     get_fill_color=team_color + [40],
#     get_line_color=team_color + [255],
#     stroked=True,
#     line_width_min_pixels=2,
# )

# # Text labels
# text_layer = pdk.Layer(
#     "TextLayer",
#     data=dot_data,
#     get_position="[lon, lat]",
#     get_text="city",
#     get_size=13,
#     get_color=[200, 220, 255, 220],
#     get_anchor="'middle'",
#     get_alignment_baseline="'bottom'",
#     get_pixel_offset=[0, -18],
#     font_family="'DM Mono', monospace",
# )

# # View centred on home city
# view = pdk.ViewState(
#     latitude=team_info["lat"],
#     longitude=team_info["lon"],
#     zoom=3.5,
#     pitch=25,
#     bearing=-10,
# )

# deck = pdk.Deck(
#     layers=[path_layer, home_layer, dot_layer, text_layer],
#     initial_view_state=view,
#     map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",    
#     tooltip={"text": "{city}"},
# )

# # ── Page layout ───────────────────────────────────────────────────────────────
# st.markdown(f'<div class="page-title">✈ {team_info["abbr"]} ROAD MAP</div>', unsafe_allow_html=True)
# st.markdown(f'<div class="page-sub">{selected_team} · 2024–25 Season Travel</div>', unsafe_allow_html=True)

# # Stats row
# total_miles  = sum(l["miles"] for l in legs)
# road_games   = sum(1 for l in legs if l["home_away"] == "away")
# cities       = len(set([l["to_city"] for l in legs]))
# flights      = len(legs)

# c1, c2, c3, c4 = st.columns(4)
# for col, num, lbl in [
#     (c1, f"{int(total_miles):,}", "TOTAL MILES"),
#     (c2, road_games,              "ROAD GAMES"),
#     (c3, cities,                  "CITIES"),
#     (c4, flights,                 "FLIGHTS"),
# ]:
#     with col:
#         st.markdown(f"""
#         <div class="stat-box">
#           <div class="stat-num">{num}</div>
#           <div class="stat-lbl">{lbl}</div>
#         </div>""", unsafe_allow_html=True)

# st.markdown("<br>", unsafe_allow_html=True)

# # Map + trip log side by side
# map_col, log_col = st.columns([3, 1])

# with map_col:
#     st.pydeck_chart(deck, use_container_width=True, height=480)

# with log_col:
#     st.markdown("#### 🗓 TRIP LOG")
#     for leg in sorted(visible_legs, key=lambda l: l["date"]):
#         is_past = leg["date"] < today
#         card_class = "trip-card past" if is_past else "trip-card"
#         icon = "🏠" if leg["home_away"] == "home" else "✈️"
#         status = "COMPLETED" if is_past else "UPCOMING"
#         st.markdown(f"""
#         <div class="{card_class}">
#           <div class="leg-header">{icon} {leg['from_city']} → {leg['to_city']}</div>
#           {leg['date'].strftime('%b %d')} · vs {TEAMS[leg['opponent']]['abbr']} · {status}
#           <div class="miles">🛫 {int(leg['miles']):,} mi</div>
#         </div>""", unsafe_allow_html=True)


import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="SBCFBL Playoffs 2026",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    background-color: #080c14;
    font-family: 'DM Sans', sans-serif;
    color: #e8eaf0;
}

.bracket-page {
    position: relative;
    min-height: 100vh;
    padding: 2rem 1rem 4rem;
    background:
        radial-gradient(ellipse 120% 60% at 50% -10%, #1a2a4a 0%, transparent 60%),
        #080c14;
}

.nba-header {
    text-align: center;
    margin-bottom: 2.5rem;
    position: relative;
    z-index: 1;
}
.nba-header h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(2.8rem, 6vw, 5rem);
    letter-spacing: 0.12em;
    color: #fff;
    line-height: 1;
}
.nba-header h1 span {
    background: linear-gradient(90deg, #c8a84b, #f5d675, #c8a84b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.nba-header p {
    font-size: 0.8rem;
    letter-spacing: 0.25em;
    color: #556080;
    text-transform: uppercase;
    margin-top: 0.35rem;
}
.divider {
    width: 80px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #c8a84b, transparent);
    margin: 0.8rem auto;
}

.conf-labels {
    display: flex;
    justify-content: space-between;
    padding: 0 1rem;
    margin-bottom: 0.8rem;
    position: relative;
    z-index: 1;
}
.conf-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    letter-spacing: 0.15em;
    color: #c8a84b;
    opacity: 0.7;
}

.playin-section {
    display: flex;
    justify-content: space-between;
    gap: 1.5rem;
    margin-bottom: 2.5rem;
    position: relative;
    z-index: 1;
}
.playin-conference {
    flex: 1;
    background: linear-gradient(135deg, #0f1726 0%, #111928 100%);
    border: 1px solid #1e2d4a;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
}
.playin-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.9rem;
    letter-spacing: 0.2em;
    color: #e05c2a;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.playin-title::before {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #e05c2a;
    border-radius: 50%;
    animation: pulse 1.8s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
}
.playin-matches {
    display: flex;
    gap: 1.2rem;
    align-items: center;
}
.playin-match { flex: 1; }
.playin-match-label {
    font-size: 0.62rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #3a4a6a;
    margin-bottom: 0.4rem;
}
.playin-arrow {
    color: #1e2d4a;
    font-size: 1.5rem;
    flex-shrink: 0;
}

.team-card {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    background: #0d1520;
    border: 1px solid #1a2540;
    margin-bottom: 3px;
    cursor: default;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}
.team-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: var(--accent, #1a2540);
    border-radius: 3px 0 0 3px;
}
.team-card:hover {
    background: #111e30;
    border-color: #2a3d60;
    transform: translateX(2px);
}
.seed {
    font-size: 0.62rem;
    font-weight: 600;
    color: #556080;
    min-width: 14px;
    text-align: right;
}
.team-name {
    font-size: 0.78rem;
    font-weight: 500;
    color: #c8d0e0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
}

.tbd-card {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    background: #080e18;
    border: 1px dashed #1a2540;
    margin-bottom: 3px;
}
.tbd-card span {
    font-size: 0.72rem;
    color: #2a3a5a;
    letter-spacing: 0.08em;
}

.bracket-wrapper {
    display: flex;
    align-items: center;
    position: relative;
    z-index: 1;
    overflow-x: auto;
    padding-bottom: 1rem;
}
.bracket-side {
    flex: 1;
    display: flex;
    min-width: 0;
}
/* West left: R1 outermost left, R3 closest to center */
.bracket-side.west { flex-direction: row; }
/* East right: R1 outermost right, R3 closest to center */
.bracket-side.east { flex-direction: row-reverse; }

.round-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    padding: 0 4px;
    min-width: 130px;
}
.round-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #2a3a5a;
    text-align: center;
    margin-bottom: 0.6rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #151f30;
}
.matchup-group {
    display: flex;
    flex-direction: column;
    justify-content: center;
    flex: 1;
    position: relative;
}
/* West: connectors on right side */
.bracket-side.west .matchup-group.has-connector::after {
    content: '';
    position: absolute;
    right: -4px;
    top: 25%;
    height: 50%;
    width: 4px;
    border-top: 2px solid #1e2d4a;
    border-bottom: 2px solid #1e2d4a;
    border-right: 2px solid #1e2d4a;
}
/* East: connectors on left side */
.bracket-side.east .matchup-group.has-connector::after {
    content: '';
    position: absolute;
    left: -4px;
    top: 25%;
    height: 50%;
    width: 4px;
    border-top: 2px solid #1e2d4a;
    border-bottom: 2px solid #1e2d4a;
    border-left: 2px solid #1e2d4a;
}
.matchup {
    background: linear-gradient(135deg, #0d1625 0%, #0f1a2a 100%);
    border: 1px solid #161f30;
    border-radius: 8px;
    padding: 0.4rem;
    margin: 0.25rem 0;
}

.finals-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 160px;
    padding: 0 0.5rem;
}
.finals-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    letter-spacing: 0.2em;
    color: #c8a84b;
    text-align: center;
    margin-bottom: 0.8rem;
}
.finals-trophy {
    font-size: 2rem;
    text-align: center;
    margin-bottom: 0.6rem;
    filter: drop-shadow(0 0 12px #c8a84b88);
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-6px); }
}
.finals-matchup {
    background: linear-gradient(135deg, #12200a 0%, #0d1625 50%, #1a1208 100%);
    border: 1px solid #c8a84b33;
    border-radius: 10px;
    padding: 0.6rem;
    width: 100%;
    box-shadow: 0 0 30px #c8a84b18, inset 0 0 20px #c8a84b08;
}

.legend {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-top: 2.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid #111928;
    position: relative;
    z-index: 1;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.7rem;
    color: #3a4a6a;
    letter-spacing: 0.08em;
}
.legend-dot { width: 8px; height: 8px; border-radius: 50%; }
</style>
"""

TEAM_COLORS = {
    "Boise Spuds":   "#744529", "Lincoln Bully":      "#FC6A03", "Kentucky Thoroughbreds": "#663399",
    "St. Louis 66ers":     "#B7B1AE", "Vegas Blackjack":     "#35654D", "Providence Pilgrims":    "#BF0A30",
    "Vancouver Forest":    "#17780D", "Albuquerque Armadillos":     "#D72C2C", "Columbus Arches":   "#CD7F32",
    "Honolulu Diamonds":  "#CDC0C0", "Cincinnati Chilli":  "#FFEA61", "Des Moines Racoons": "#1B1E23",
    "Anaheim Mice":  "#DA0F10", "Pittsburgh Bridge":      "#F1F137", "Baltimore Blue Crabs":   "#00CED1",
    "Seattle Brew":    "#006241", "Tampa Bay Flamingos":     "#FC8EAC", "Buffalo Daredevils":     "#152238",
    "Anchorage Killer Whales":     "#454B55", "Lansing Lagoon":  "#B9EFE1",
}

WEST = {
    "playin": {
        "78_game":    ("No. 7 Anchorage Killer Whales",    "No. 8 Albuquerque Armadillos"),
        "910_game":   ("No. 9 Lincoln Bully",     "No. 10 Vegas Blackjack"),
        "loser_game": ("Loser 7/8",   "Winner 9/10"),
    },
    "r1": [
        [("No. 1", "Boise Spuds"),   ("PI. 2", "TBD")],
        [("No. 5", "Anaheim Mice"),   ("No. 4", "Honolulu Diamonds")],
        [("No. 3", "St. Louis 66ers"),  ("No. 6", "Seattle Brew")],
        [("PI. 1", "TBD"), ("No. 2", "Vancouver Forest")],
    ],
    "r2": [
        [("TBD", ""), ("TBD", "")],
        [("TBD", ""), ("TBD", "")],
    ],
    "r3": [
        [("TBD", ""), ("TBD", "")],
    ],
}

EAST = {
    "playin": {
        "78_game":    ("No. 7 Columbus Arches",      "No. 8 Des Moines Racoons"),
        "910_game":   ("No. 9 Baltimore Blue Crabs",     "No. 10 Buffalo Daredevils"),
        "loser_game": ("Loser 7/8",   "Winner 9/10"),
    },
    "r1": [
        [("No. 1", "Cincinnati Chilli"),   ("PI. 1", "TBD")],
        [("No. 5", "Kentucky Thoroughbreds"), ("No. 4", "Lansing Lagoon")],
        [("No. 3", "Tampa Bay Flamingos"),     ("No. 6", "Providence Pilgrims")],
        [("PI. 1", "TBD"),    ("No. 2", "Pittsburgh Bridge")],
    ],
    "r2": [
        [("TBD", ""), ("TBD", "")],
        [("TBD", ""), ("TBD", "")],
    ],
    "r3": [
        [("TBD", ""), ("TBD", "")],
    ],
}

def team_card(seed, name):
    if not name or name == "TBD":
        return '<div class="tbd-card"><span>TBD</span></div>'
    color = TEAM_COLORS.get(name, "#1e2d4a")
    return f'<div class="team-card" style="--accent:{color}"><span class="seed">{seed}</span><span class="team-name">{name}</span></div>'

def matchup_html(teams, connector=False):
    t1, t2 = teams
    conn = "has-connector" if connector else ""
    return f'<div class="matchup-group {conn}"><div class="matchup">{team_card(*t1)}{team_card(*t2)}</div></div>'

def round_col(label, matchups, connector=False):
    inner = "".join(matchup_html(m, connector=connector) for m in matchups)
    return f'<div class="round-col"><div class="round-label">{label}</div>{inner}</div>'

def playin_html(conf_data, conf_name):
    def pi_match(t1, t2, note=""):
        return f'''<div class="playin-match">
          <div class="playin-match-label">{note}</div>
          <div class="matchup">
            <div class="team-card"><span class="seed"></span><span class="team-name">{t1}</span></div>
            <div class="team-card"><span class="seed"></span><span class="team-name">{t2}</span></div>
          </div></div>'''
    return f'''<div class="playin-conference">
      <div class="playin-title">{conf_name} Play-In Tournament</div>
      <div class="playin-matches">
        {pi_match(*conf_data["78_game"],    note="Win → 7 Seed")}
        <div class="playin-arrow">→</div>
        {pi_match(*conf_data["910_game"],   note="Win advances")}
        <div class="playin-arrow">→</div>
        {pi_match(*conf_data["loser_game"], note="Win → 8 Seed")}
      </div></div>'''

def build_bracket():
    west_r1 = round_col("First Round",  WEST["r1"], connector=True)
    west_r2 = round_col("Conf. Semis",  WEST["r2"], connector=True)
    west_r3 = round_col("Conf. Finals", WEST["r3"], connector=True)
    east_r1 = round_col("First Round",  EAST["r1"], connector=True)
    east_r2 = round_col("Conf. Semis",  EAST["r2"], connector=True)
    east_r3 = round_col("Conf. Finals", EAST["r3"], connector=True)

    finals = '''<div class="finals-col">
      <div class="finals-label">SBCFBL Finals</div>
      <div class="finals-trophy">🏆</div>
      <div class="finals-matchup">
        <div class="tbd-card"><span>West Champion</span></div>
        <div class="tbd-card"><span>East Champion</span></div>
      </div></div>'''

    return f'''<div class="bracket-wrapper">
      <div class="bracket-side west">{west_r1}{west_r2}{west_r3}</div>
      {finals}
      <div class="bracket-side east">{east_r1}{east_r2}{east_r3}</div>
    </div>'''

header = '''<div class="nba-header">
  <h1>2026 SBCFBL <span>Playoffs</span></h1>
  <div class="divider"></div>
  <p>Western Conference &nbsp;·&nbsp; Play-In Tournament &nbsp;·&nbsp; Eastern Conference</p>
</div>'''

conf_labels = '''<div class="conf-labels">
  <span class="conf-label">⬡ Western Conference</span>
  <span class="conf-label">Eastern Conference ⬡</span>
</div>'''

playin = f'''<div class="playin-section">
  {playin_html(WEST["playin"], "WEST")}
  {playin_html(EAST["playin"], "EAST")}
</div>'''

legend = '''<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#e05c2a"></div> Play-In Tournament</div>
  <div class="legend-item"><div class="legend-dot" style="background:#c8a84b"></div> SBCFBL Finals</div>
  <div class="legend-item"><div class="legend-dot" style="background:#1e2d4a"></div> Awaiting Result</div>
</div>'''

body = f'<div class="bracket-page">{header}{conf_labels}{playin}{build_bracket()}{legend}</div>'

full_doc = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">{CSS}</head>
<body>{body}</body>
</html>"""

components.html(full_doc, height=1800, scrolling=True)

import streamlit as st
from datetime import date


def render_scoreboard(
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    home_logo_url: str,
    away_logo_url: str,
    game_date: str = None,
    league: str = None,
    venue: str = None,
    quarter_scores: list[dict] = None,  # e.g. [{"Q1": (7,3)}, {"Q2": (14,10)}, ...]
    game_status: str = "FINAL",
    home_record: str = None,
    away_record: str = None,
    home_color: str = "#1a1a2e",
    away_color: str = "#16213e",
):
    """
    Renders a beautiful 5:2 ratio scoreboard at the top of a Streamlit article.

    Parameters:
    -----------
    home_team       : Full team name (e.g. "Los Angeles Lakers")
    away_team       : Full team name
    home_score      : Final score for home team
    away_score      : Final score for away team
    home_logo_url   : Direct URL to home team logo image
    away_logo_url   : Direct URL to away team logo image
    game_date       : Display date string (e.g. "March 4, 2026"). Defaults to today.
    league          : League / competition name (e.g. "NBA", "NFL", "Premier League")
    venue           : Stadium / arena name
    quarter_scores  : List of period dicts, e.g. [{"label":"Q1","home":7,"away":3}, ...]
    game_status     : Status string shown above score (default "FINAL")
    home_record     : Win-loss record string (e.g. "42-18")
    away_record     : Win-loss record string
    home_color      : Accent hex color for home team side
    away_color      : Accent hex color for away team side
    """

    if game_date is None:
        game_date = date.today().strftime("%B %-d, %Y")

    winner = "home" if home_score > away_score else "away" if away_score > home_score else "tie"

    # Build quarter/period table HTML
    period_html = ""
    if quarter_scores:
        headers = "".join(f"<th>{p['label']}</th>" for p in quarter_scores)
        home_cells = "".join(f"<td>{p['home']}</td>" for p in quarter_scores)
        away_cells = "".join(f"<td>{p['away']}</td>" for p in quarter_scores)
        period_html = f"""
        <div class="period-table-wrap">
          <table class="period-table">
            <thead>
              <tr>
                <th class="team-col">TEAM</th>
                {headers}
                <th class="final-col">T</th>
              </tr>
            </thead>
            <tbody>
              <tr class="{'winner-row' if winner == 'away' else ''}">
                <td class="team-col">{away_team.split()[-1].upper()}</td>
                {away_cells}
                <td class="final-col total">{away_score}</td>
              </tr>
              <tr class="{'winner-row' if winner == 'home' else ''}">
                <td class="team-col">{home_team.split()[-1].upper()}</td>
                {home_cells}
                <td class="final-col total">{home_score}</td>
              </tr>
            </tbody>
          </table>
        </div>
        """

    meta_items = []
    if league:
        meta_items.append(f'<span class="meta-chip">{league}</span>')
    if venue:
        meta_items.append(f'<span class="meta-chip venue">📍 {venue}</span>')
    meta_bar = f'<div class="meta-bar">{"".join(meta_items)}</div>' if meta_items else ""

    record_home = f'<span class="record">{home_record}</span>' if home_record else ""
    record_away = f'<span class="record">{away_record}</span>' if away_record else ""

    winner_badge_home = '<span class="winner-badge">▲ W</span>' if winner == "home" else ""
    winner_badge_away = '<span class="winner-badge">▲ W</span>' if winner == "away" else ""

    scoreboard_html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;900&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
      .sb-root {{
        font-family: 'Barlow', sans-serif;
        background: #0a0a0f;
        border-radius: 16px;
        overflow: hidden;
        position: relative;
        box-shadow:
          0 0 0 1px rgba(255,255,255,0.06),
          0 32px 80px rgba(0,0,0,0.7),
          0 8px 24px rgba(0,0,0,0.5);
        margin-bottom: 8px;
        aspect-ratio: 5 / 2;
        display: flex;
        flex-direction: column;
      }}

      /* ── animated grain overlay ── */
      .sb-root::before {{
        content: '';
        position: absolute;
        inset: 0;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
        opacity: 0.35;
        pointer-events: none;
        z-index: 10;
        border-radius: 16px;
      }}

      /* ── split background glow ── */
      .sb-glow-left {{
        position: absolute;
        left: -10%;
        top: -30%;
        width: 55%;
        height: 160%;
        background: radial-gradient(ellipse at 30% 50%, {home_color}99 0%, transparent 65%);
        pointer-events: none;
        z-index: 0;
        filter: blur(2px);
      }}
      .sb-glow-right {{
        position: absolute;
        right: -10%;
        top: -30%;
        width: 55%;
        height: 160%;
        background: radial-gradient(ellipse at 70% 50%, {away_color}99 0%, transparent 65%);
        pointer-events: none;
        z-index: 0;
        filter: blur(2px);
      }}

      /* ── top bar ── */
      .sb-topbar {{
        position: relative;
        z-index: 5;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 20px 6px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
      }}
      .sb-topbar .date-label {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.4);
      }}
      .sb-topbar .status-pill {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #f0c040;
        background: rgba(240,192,64,0.12);
        border: 1px solid rgba(240,192,64,0.3);
        padding: 3px 12px;
        border-radius: 50px;
      }}

      /* ── main score area ── */
      .sb-main {{
        position: relative;
        z-index: 5;
        flex: 1;
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        padding: 0 24px;
        gap: 0;
      }}

      /* team block */
      .sb-team {{
        display: flex;
        align-items: center;
        gap: 18px;
      }}
      .sb-team.home {{ flex-direction: row; }}
      .sb-team.away {{ flex-direction: row-reverse; }}

      .team-logo-wrap {{
        position: relative;
        flex-shrink: 0;
      }}
      .team-logo-wrap img {{
        width: 88px;
        height: 88px;
        object-fit: contain;
        display: block;
        filter: drop-shadow(0 4px 20px rgba(0,0,0,0.6));
        transition: transform 0.3s ease;
      }}
      .team-logo-wrap img:hover {{
        transform: scale(1.05);
      }}

      .team-info {{ line-height: 1.2; }}
      .sb-team.away .team-info {{ text-align: right; }}

      .team-city {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.45);
        display: block;
      }}
      .team-name {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 28px;
        font-weight: 900;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        color: #ffffff;
        display: block;
        line-height: 1;
      }}
      .record {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1.5px;
        color: rgba(255,255,255,0.3);
        display: block;
        margin-top: 3px;
      }}
      .winner-badge {{
        display: inline-block;
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #f0c040;
        border: 1px solid rgba(240,192,64,0.4);
        padding: 1px 6px;
        border-radius: 4px;
        margin-top: 4px;
      }}

      /* ── center score ── */
      .sb-center {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        padding: 0 20px;
      }}
      .score-row {{
        display: flex;
        align-items: center;
        gap: 0;
      }}
      .score-num {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 90px;
        font-weight: 900;
        color: #ffffff;
        line-height: 1;
        letter-spacing: -2px;
        text-shadow: 0 0 60px rgba(255,255,255,0.1);
      }}
      .score-num.winner-score {{
        color: #f0c040;
        text-shadow: 0 0 40px rgba(240,192,64,0.3);
      }}
      .score-divider {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 50px;
        font-weight: 300;
        color: rgba(255,255,255,0.2);
        padding: 0 8px;
        line-height: 1;
        margin-top: -8px;
      }}
      .vs-line {{
        width: 60px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
      }}

      /* ── bottom bar ── */
      .sb-bottombar {{
        position: relative;
        z-index: 5;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 6px 20px 10px;
        border-top: 1px solid rgba(255,255,255,0.07);
        gap: 12px;
      }}

      /* meta bar */
      .meta-bar {{
        display: flex;
        align-items: center;
        gap: 8px;
      }}
      .meta-chip {{
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.4);
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 3px 10px;
        border-radius: 4px;
      }}
      .meta-chip.venue {{ letter-spacing: 1px; }}

      /* period table */
      .period-table-wrap {{
        overflow-x: auto;
        margin-top: 0;
      }}
      .period-table {{
        border-collapse: collapse;
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 12px;
        color: rgba(255,255,255,0.5);
        letter-spacing: 1px;
      }}
      .period-table th, .period-table td {{
        padding: 3px 10px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.07);
      }}
      .period-table th {{
        font-weight: 700;
        color: rgba(255,255,255,0.3);
        background: rgba(255,255,255,0.03);
        letter-spacing: 2px;
        font-size: 10px;
      }}
      .period-table .team-col {{
        text-align: left;
        padding-left: 12px;
        font-weight: 700;
        color: rgba(255,255,255,0.6);
      }}
      .period-table .final-col {{
        font-weight: 700;
        color: rgba(255,255,255,0.6);
      }}
      .period-table .total {{
        color: #ffffff;
        font-size: 14px;
        font-weight: 900;
      }}
      .period-table .winner-row td {{
        color: rgba(255,255,255,0.7);
      }}
      .period-table .winner-row .total {{
        color: #f0c040;
      }}
    </style>

    <div class="sb-root">
      <div class="sb-glow-left"></div>
      <div class="sb-glow-right"></div>

      <!-- Top bar -->
      <div class="sb-topbar">
        <span class="date-label">{game_date}</span>
        <span class="status-pill">{game_status}</span>
        <span class="date-label" style="opacity:0">{game_date}</span>
      </div>

      <!-- Main score area -->
      <div class="sb-main">

        <!-- Home team (left) -->
        <div class="sb-team home">
          <div class="team-logo-wrap">
            <img src="{home_logo_url}" alt="{home_team}" onerror="this.style.opacity='0.3'"/>
          </div>
          <div class="team-info">
            <span class="team-city">{" ".join(home_team.split()[:-1]) or home_team}</span>
            <span class="team-name">{home_team.split()[-1]}</span>
            {record_home}
            {winner_badge_home}
          </div>
        </div>

        <!-- Center score -->
        <div class="sb-center">
          <div class="score-row">
            <span class="score-num {'winner-score' if winner == 'home' else ''}">{home_score}</span>
            <span class="score-divider">—</span>
            <span class="score-num {'winner-score' if winner == 'away' else ''}">{away_score}</span>
          </div>
          <div class="vs-line"></div>
        </div>

        <!-- Away team (right) -->
        <div class="sb-team away">
          <div class="team-logo-wrap">
            <img src="{away_logo_url}" alt="{away_team}" onerror="this.style.opacity='0.3'"/>
          </div>
          <div class="team-info">
            <span class="team-city">{" ".join(away_team.split()[:-1]) or away_team}</span>
            <span class="team-name">{away_team.split()[-1]}</span>
            {record_away}
            {winner_badge_away}
          </div>
        </div>

      </div>

      <!-- Bottom bar -->
      <div class="sb-bottombar">
        {meta_bar}
        {period_html}
      </div>
    </div>
    """

    st.html(scoreboard_html)


# ─────────────────────────────────────────────
# Demo / dev preview  (streamlit run scoreboard.py)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Scoreboard Demo")

    st.markdown(
        """
        <style>
          .stApp { background: #111117; }
          section[data-testid="stAppViewContainer"] { padding: 2rem 3rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── NFL Example ──────────────────────────
    st.subheader("NFL Example", anchor=False)
    render_scoreboard(
        home_team="Utah Jazz",
        away_team="Washington Wizards",
        home_score=0,
        away_score=0,
        home_logo_url="https://a.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/utah.png&h=200&w=200",
        away_logo_url="https://a.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/was.png&h=200&w=200",
        game_date="March 5, 2026",
        league="NBA",
        venue="Capital One Arena, Washington D.C.",
        game_status="FINAL",
        home_record="18-44",
        away_record="16-45",
        home_color="#31006F",
        away_color="#E31837",
        quarter_scores=[
            {"label": "Q1", "home": 0, "away": 0},
            {"label": "Q2", "home": 0, "away": 0},
            {"label": "Q3", "home": 0, "away": 0},
            {"label": "Q4", "home": 0, "away": 0},
        ],
    )


    st.markdown("<br>", unsafe_allow_html=True)

    # ── NBA Example ──────────────────────────
    st.subheader("NBA Example", anchor=False)
    render_scoreboard(
        home_team="Utah Mammoth",
        away_team="Philadelphia Flyers",
        home_score=3,
        away_score=0,
        home_logo_url="https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/utah.png&h=200&w=200",
        away_logo_url="https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/phi.png&h=200&w=200",
        game_date="March 5, 2026",
        league="NHL",
        venue="Xfinity Arena, Philadelphia",
        game_status="FINAL",
        home_record="33-25-4",
        away_record="28-22-11",
        home_color="#6CACE3",
        away_color="#F74902",
        quarter_scores=[
            {"label": "P1", "home": 0, "away": 0},
            {"label": "P2", "home": 2, "away": 0},
            {"label": "P3", "home": 1, "away": 0},
        ],
    )

#A
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Soccer Example ──────────────────────────
    # st.subheader("Soccer Example (no period scores)", anchor=False)
    # render_scoreboard(
    #     home_team="Manchester City",
    #     away_team="Arsenal FC",
    #     home_score=2,
    #     away_score=2,
    #     home_logo_url="https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/1200px-Manchester_City_FC_badge.svg.png",
    #     away_logo_url="https://upload.wikimedia.org/wikipedia/en/thumb/5/53/Arsenal_FC.svg/1200px-Arsenal_FC.svg.png",
    #     game_date="March 31, 2024",
    #     league="Premier League · GW30",
    #     venue="Etihad Stadium, Manchester",
    #     game_status="FINAL",
    #     home_record="15W 5D 3L",
    #     away_record="16W 4D 3L",
    #     home_color="#6CABDD",
    #     away_color="#EF0107",
    # )