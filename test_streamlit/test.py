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
    page_title="NBA Playoffs 2024",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CSS ────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body, .stApp {
    background-color: #080c14;
    font-family: 'DM Sans', sans-serif;
    color: #e8eaf0;
}

.stApp { background: #080c14; }

/* ── Grain overlay ── */
.bracket-page {
    position: relative;
    min-height: 100vh;
    padding: 2rem 1rem 4rem;
    background:
        radial-gradient(ellipse 120% 60% at 50% -10%, #1a2a4a 0%, transparent 60%),
        #080c14;
}
.bracket-page::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
    opacity: 0.03;
    pointer-events: none;
    z-index: 0;
}

/* ── Header ── */
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

/* ── Conference labels ── */
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

/* ── Play-in wrapper ── */
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
.playin-match {
    flex: 1;
}
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

/* ── Team card ── */
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
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: var(--accent, #1a2540);
    border-radius: 3px 0 0 3px;
}
.team-card:hover {
    background: #111e30;
    border-color: #2a3d60;
    transform: translateX(2px);
}
.team-card.winner {
    border-color: #c8a84b44;
    background: #14200e;
}
.team-card.winner::before { background: #c8a84b; }
.team-card.tbd { opacity: 0.4; }

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
.team-card.winner .team-name { color: #e8f0d8; font-weight: 600; }
.team-score {
    font-size: 0.72rem;
    font-weight: 600;
    color: #556080;
    min-width: 20px;
    text-align: right;
}
.team-card.winner .team-score { color: #c8a84b; }

/* ── Bracket layout ── */
.bracket-wrapper {
    display: flex;
    align-items: center;
    gap: 0;
    position: relative;
    z-index: 1;
    overflow-x: auto;
    padding-bottom: 1rem;
}

.bracket-side {
    flex: 1;
    display: flex;
    gap: 0;
    min-width: 0;
}
.bracket-side.east { flex-direction: row; }
.bracket-side.west { flex-direction: row-reverse; }

/* ── Round columns ── */
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

/* ── Matchup blocks ── */
.matchup-group {
    display: flex;
    flex-direction: column;
    justify-content: center;
    flex: 1;
    position: relative;
}

/* bracket connector lines via pseudo-elements */
.matchup-group.has-connector::after {
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

.west .matchup-group.has-connector::after {
    right: auto;
    left: -4px;
    border-right: none;
    border-left: 2px solid #1e2d4a;
}

.matchup {
    background: linear-gradient(135deg, #0d1625 0%, #0f1a2a 100%);
    border: 1px solid #161f30;
    border-radius: 8px;
    padding: 0.4rem;
    margin: 0.25rem 0;
    position: relative;
}
.matchup::after {
    content: attr(data-series);
    position: absolute;
    right: 4px;
    top: -10px;
    font-size: 0.55rem;
    color: #2a3a5a;
    letter-spacing: 0.08em;
}

/* ── Finals ── */
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
.finals-matchup .team-card { min-width: 0; }

/* ── Legend ── */
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
.legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}
</style>
"""

# ─── Data ────────────────────────────────────────────────────────────────────────

EAST = {
    "playin": {
        "78_game": ("7 Heat",    "8 Sixers"),
        "910_game": ("9 Bulls",   "10 Hawks"),
        "loser_game": ("Loser 7/8", "Winner 9/10"),
    },
    "r1": [
        [("1", "Celtics", 4, True),    ("8", "Heat",   1, False)],
        [("4", "Cavaliers", 3, True),  ("5", "Magic",  2, False)],
        [("3", "Bucks", 1, False),     ("6", "Pacers", 3, True)],
        [("2", "Knicks", 4, True),     ("7", "Sixers", 2, False)],
    ],
    "r2": [
        [("1", "Celtics", 4, True),  ("4", "Cavaliers", 1, False)],
        [("3", "Pacers", 4, True),   ("2", "Knicks",    3, False)],
    ],
    "r3": [
        [("1", "Celtics", 4, True),  ("3", "Pacers", 0, False)],
    ],
    "finals": ("1", "Celtics", 4, True),
}

WEST = {
    "playin": {
        "78_game": ("7 Lakers",   "8 Pelicans"),
        "910_game": ("9 Kings",   "10 Suns"),
        "loser_game": ("Loser 7/8", "Winner 9/10"),
    },
    "r1": [
        [("1", "Thunder",   4, True),  ("8", "Pelicans", 0, False)],
        [("4", "Clippers",  2, False), ("5", "Mavericks", 4, True)],
        [("3", "Timberwlvs", 4, True), ("6", "Suns",    0, False)],
        [("2", "Nuggets",   4, True),  ("7", "Lakers",  1, False)],
    ],
    "r2": [
        [("1", "Thunder",    4, True),  ("5", "Mavericks", 2, False)],
        [("3", "Timberwlvs", 2, False), ("2", "Nuggets",   4, True)],
    ],
    "r3": [
        [("2", "Mavericks", 4, True),  ("2", "Nuggets",  3, False)],
    ],
    "finals": ("2", "Mavericks", 0, False),
}

FINALIST_EAST   = EAST["finals"]
FINALIST_WEST   = WEST["finals"]
CHAMPION = ("1", "Celtics", "4-1")

# ─── HTML helpers ─────────────────────────────────────────────────────────────

TEAM_COLORS = {
    "Celtics": "#007a33",   "Heat": "#98002e",    "Cavaliers": "#860038",
    "Magic": "#007dc5",     "Bucks": "#00471b",   "Pacers": "#fdbb30",
    "Knicks": "#006bb6",    "Sixers": "#006bb6",  "Thunder": "#007ac1",
    "Pelicans": "#0c2340",  "Clippers": "#c8102e","Mavericks": "#00538c",
    "Timberwlvs": "#236192","Suns": "#e56020",    "Nuggets": "#0e2240",
    "Lakers": "#552583",    "Bulls": "#ce1141",   "Hawks": "#e03a3e",
    "Kings": "#5a2d81",     "Suns": "#e56020",
}

def team_card(seed, name, score, winner, show_score=True):
    color = TEAM_COLORS.get(name, "#1e2d4a")
    w_cls = "winner" if winner else ""
    score_html = f'<span class="team-score">{score}</span>' if show_score and score > 0 else ""
    return f"""
    <div class="team-card {w_cls}" style="--accent:{color}">
        <span class="seed">{seed}</span>
        <span class="team-name">{name}</span>
        {score_html}
    </div>"""

def matchup_html(teams, series_label="", connector=False):
    t1, t2 = teams
    conn = "has-connector" if connector else ""
    series = series_label
    return f"""
    <div class="matchup-group {conn}">
      <div class="matchup" data-series="{series}">
        {team_card(*t1)}{team_card(*t2)}
      </div>
    </div>"""

def round_col(label, matchups, connector=False):
    inner = "".join(matchup_html(m, connector=connector) for m in matchups)
    return f"""
    <div class="round-col">
      <div class="round-label">{label}</div>
      {inner}
    </div>"""

def playin_html(conf_data, conf_name):
    def pi_match(t1_label, t2_label, note=""):
        return f"""
        <div class="playin-match">
          <div class="playin-match-label">{note}</div>
          <div class="matchup">
            <div class="team-card"><span class="seed"></span><span class="team-name">{t1_label}</span></div>
            <div class="team-card"><span class="seed"></span><span class="team-name">{t2_label}</span></div>
          </div>
        </div>"""
    return f"""
    <div class="playin-conference">
      <div class="playin-title">{conf_name} Play-In Tournament</div>
      <div class="playin-matches">
        {pi_match(*conf_data["78_game"],  note="Win → 7 Seed")}
        <div class="playin-arrow">→</div>
        {pi_match(*conf_data["910_game"], note="Win advances")}
        <div class="playin-arrow">→</div>
        {pi_match(*conf_data["loser_game"], note="Win → 8 Seed")}
      </div>
    </div>"""

# ─── Build full bracket HTML ──────────────────────────────────────────────────

def build_bracket():
    # East side
    east_r1   = round_col("First Round",   EAST["r1"],  connector=True)
    east_r2   = round_col("Conf. Semis",   EAST["r2"],  connector=True)
    east_r3   = round_col("Conf. Finals",  EAST["r3"],  connector=True)

    # West side
    west_r1   = round_col("First Round",   WEST["r1"],  connector=True)
    west_r2   = round_col("Conf. Semis",   WEST["r2"],  connector=True)
    west_r3   = round_col("Conf. Finals",  WEST["r3"],  connector=True)

    # Finals center
    ef = FINALIST_EAST
    wf = FINALIST_WEST
    finals_html = f"""
    <div class="finals-col">
      <div class="finals-label">NBA Finals</div>
      <div class="finals-trophy">🏆</div>
      <div class="finals-matchup">
        {team_card(ef[0], ef[1], ef[2], ef[3])}
        {team_card(wf[0], wf[1], wf[2], wf[3])}
      </div>
      <div style="text-align:center;margin-top:0.5rem;font-size:0.65rem;color:#c8a84b;letter-spacing:0.12em;font-family:'Bebas Neue',sans-serif;">
        Champion: {CHAMPION[1]} {CHAMPION[2]}
      </div>
    </div>"""

    return f"""
    <div class="bracket-wrapper">
      <div class="bracket-side east">
        {east_r1}{east_r2}{east_r3}
      </div>
      {finals_html}
      <div class="bracket-side west">
        {west_r3}{west_r2}{west_r1}
      </div>
    </div>"""

# ─── App layout ──────────────────────────────────────────────────────────────

st.markdown(CSS, unsafe_allow_html=True)

page_open = '<div class="bracket-page">'
page_close = '</div>'

header = """
<div class="nba-header">
  <h1>2024 NBA <span>Playoffs</span></h1>
  <div class="divider"></div>
  <p>Eastern Conference &nbsp;·&nbsp; Western Conference &nbsp;·&nbsp; Play-In Tournament</p>
</div>"""

conf_labels = """
<div class="conf-labels">
  <span class="conf-label">⬡ Eastern Conference</span>
  <span class="conf-label">Western Conference ⬡</span>
</div>"""

playin = f"""
<div class="playin-section">
  {playin_html(EAST["playin"], "EAST")}
  {playin_html(WEST["playin"], "WEST")}
</div>"""

bracket = build_bracket()

legend = """
<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#c8a84b"></div> Series Winner</div>
  <div class="legend-item"><div class="legend-dot" style="background:#e05c2a"></div> Play-In</div>
  <div class="legend-item"><div class="legend-dot" style="background:#1e2d4a"></div> Eliminated</div>
</div>"""

full_html = (
    page_open + header + conf_labels + playin + bracket + legend + page_close
)

full_doc = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{CSS.replace('<style>', '<style>')}
</head>
<body>
{page_open + header + conf_labels + playin + bracket + legend + page_close}
</body>
</html>
"""

components.html(full_doc, height=1800, scrolling=True)
