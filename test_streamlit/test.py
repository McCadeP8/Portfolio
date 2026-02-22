import streamlit as st
import pydeck as pdk
import pandas as pd
import math
from datetime import date

st.set_page_config(page_title="NBA Travel Tracker", layout="wide", page_icon="✈️")

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  [data-testid="stAppViewContainer"] { background: #080c14; }
  [data-testid="stSidebar"]          { background: #0d1117; border-right: 1px solid #1e2d40; }
  [data-testid="stSidebar"] * { color: #c9d8e8 !important; }
  h1, h2, h3 { font-family: 'Orbitron', monospace !important; }
  .block-container { padding-top: 1.5rem; }

  .trip-card {
    background: linear-gradient(135deg, #0d1f33 0%, #0a1520 100%);
    border: 1px solid #1a3a5c;
    border-left: 3px solid #00aaff;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    color: #a8c8e8;
  }
  .trip-card .leg-header { color: #00aaff; font-weight: 700; font-size: 14px; margin-bottom: 4px; }
  .trip-card .miles      { color: #00ffcc; font-size: 11px; margin-top: 4px; }
  .trip-card .past       { border-left-color: #334455; opacity: 0.6; }

  .stat-box {
    background: #0d1f33;
    border: 1px solid #1a3a5c;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    font-family: 'DM Mono', monospace;
  }
  .stat-num { font-size: 26px; font-weight: 700; color: #00aaff; font-family: 'Orbitron', monospace; }
  .stat-lbl { font-size: 11px; color: #557799; margin-top: 2px; letter-spacing: 0.08em; }

  .page-title {
    font-family: 'Orbitron', monospace;
    font-size: 28px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: 0.06em;
    margin-bottom: 0;
  }
  .page-sub {
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    color: #446688;
    margin-top: 2px;
    margin-bottom: 18px;
  }
</style>
""", unsafe_allow_html=True)

# ── Team data ─────────────────────────────────────────────────────────────────
TEAMS = {
    "Boston Celtics":        {"city": "Boston",        "lat": 42.3601, "lon": -71.0589, "color": [0,  122, 51],  "abbr": "BOS"},
    "Golden State Warriors": {"city": "San Francisco", "lat": 37.7749, "lon": -122.4194,"color": [29,  66,138],  "abbr": "GSW"},
    "LA Lakers":             {"city": "Los Angeles",   "lat": 34.0430, "lon": -118.2673,"color": [85,  37,130],  "abbr": "LAL"},
    "Miami Heat":            {"city": "Miami",         "lat": 25.7814, "lon": -80.1870, "color": [152, 0,  46],  "abbr": "MIA"},
    "Chicago Bulls":         {"city": "Chicago",       "lat": 41.8807, "lon": -87.6742, "color": [206, 17, 65],  "abbr": "CHI"},
    "Dallas Mavericks":      {"city": "Dallas",        "lat": 32.7767, "lon": -96.7970, "color": [0,   83,188],  "abbr": "DAL"},
    "Denver Nuggets":        {"city": "Denver",        "lat": 39.7392, "lon": -104.9903,"color": [13, 34, 64],   "abbr": "DEN"},
    "New York Knicks":       {"city": "New York",      "lat": 40.7128, "lon": -74.0060, "color": [0,  107,182],  "abbr": "NYK"},
    "Phoenix Suns":          {"city": "Phoenix",       "lat": 33.4455, "lon": -112.0712,"color": [29,  17, 96],  "abbr": "PHX"},
    "Toronto Raptors":       {"city": "Toronto",       "lat": 43.6435, "lon": -79.3791, "color": [206, 17, 65],  "abbr": "TOR"},
    "London Testicles":       {"city": "London",       "lat": 51.5072, "lon": 0.1276, "color": [206, 17, 65],  "abbr": "LOND"},

}

# Sample road trip schedule — (opponent, date, home/away)
SCHEDULES = {
    "Boston Celtics": [
        ("Miami Heat",        date(2025,  2,  5), "away"),
        ("Chicago Bulls",     date(2025,  2,  7), "away"),
        ("New York Knicks",   date(2025,  2,  9), "away"),
        ("London Testicles",   date(2025,  2,  10), "away"),
        ("Toronto Raptors",   date(2025,  2, 11), "away"),
        ("Boston Celtics",    date(2025,  2, 14), "home"),
        ("Dallas Mavericks",  date(2025,  2, 18), "away"),
        ("Denver Nuggets",    date(2025,  2, 20), "away"),
        ("Golden State Warriors", date(2025, 2, 22), "away"),
        ("LA Lakers",         date(2025,  2, 24), "away"),
        ("Boston Celtics",    date(2025,  2, 27), "home"),
    ],
    "Golden State Warriors": [
        ("LA Lakers",         date(2025,  2,  4), "away"),
        ("Phoenix Suns",      date(2025,  2,  6), "away"),
        ("Denver Nuggets",    date(2025,  2,  8), "away"),
        ("Dallas Mavericks",  date(2025,  2, 10), "away"),
        ("Golden State Warriors", date(2025, 2, 13), "home"),
        ("Chicago Bulls",     date(2025,  2, 17), "away"),
        ("Miami Heat",        date(2025,  2, 19), "away"),
        ("New York Knicks",   date(2025,  2, 21), "away"),
        ("Boston Celtics",    date(2025,  2, 23), "away"),
        ("Golden State Warriors", date(2025, 2, 26), "home"),
    ],
}
# Fill remaining teams with a short generic trip
for team in TEAMS:
    if team not in SCHEDULES:
        opponents = [t for t in list(TEAMS.keys()) if t != team][:5]
        SCHEDULES[team] = [(opp, date(2025, 2, 4 + i*2), "away") for i, opp in enumerate(opponents)] + \
                          [(team, date(2025, 2, 15), "home")]

# ── Helpers ───────────────────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def arc_points(lat1, lon1, lat2, lon2, n=40):
    """Generate intermediate points along a great-circle arc."""
    pts = []
    for i in range(n + 1):
        t = i / n
        lat = lat1 + t * (lat2 - lat1)
        lon = lon1 + t * (lon2 - lon1)
        # add slight vertical bow
        bow = math.sin(math.pi * t) * 3
        pts.append([lon, lat + bow])
    return pts

def build_trip_legs(team_name, schedule):
    """Turn a schedule into a list of travel legs."""
    home = TEAMS[team_name]
    legs = []
    current_lat, current_lon, current_city = home["lat"], home["lon"], home["city"]

    for opponent, game_date, ha in schedule:
        dest = TEAMS[opponent]
        if ha == "home":
            dest_lat, dest_lon, dest_city = home["lat"], home["lon"], home["city"]
        else:
            dest_lat, dest_lon, dest_city = dest["lat"], dest["lon"], dest["city"]

        if current_city == dest_city:
            current_lat, current_lon, current_city = dest_lat, dest_lon, dest_city
            continue

        miles = haversine(current_lat, current_lon, dest_lat, dest_lon)
        legs.append({
            "from_city":  current_city,
            "to_city":    dest_city,
            "from_lat":   current_lat,
            "from_lon":   current_lon,
            "to_lat":     dest_lat,
            "to_lon":     dest_lon,
            "miles":      miles,
            "date":       game_date,
            "opponent":   opponent,
            "home_away":  ha,
            "path":       arc_points(current_lat, current_lon, dest_lat, dest_lon),
        })
        current_lat, current_lon, current_city = dest_lat, dest_lon, dest_city

    return legs

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ✈️ TEAM TRAVEL TRACKER")
    st.divider()
    selected_team = st.selectbox("Select Team", list(TEAMS.keys()))
    today = st.date_input("Today's Date", value=date(2025, 2, 14))
    show_past = st.toggle("Show Past Legs", value=True)
    st.divider()
    st.caption("Arc lines show team travel routes.\nGlow = upcoming game.")

team_info = TEAMS[selected_team]
schedule  = SCHEDULES[selected_team]
legs      = build_trip_legs(selected_team, schedule)

past_legs     = [l for l in legs if l["date"] <  today]
upcoming_legs = [l for l in legs if l["date"] >= today]
visible_legs  = (past_legs if show_past else []) + upcoming_legs

# ── Build pydeck layers ───────────────────────────────────────────────────────
team_color   = team_info["color"]
team_color_a = team_color + [220]

# Arc paths
path_data = []
for leg in visible_legs:
    is_past = leg["date"] < today
    color = [255, 220, 0, 200]    
    path_data.append({"path": leg["path"], "color": color, "width": 2 if is_past else 4})

path_layer = pdk.Layer(
    "PathLayer",
    data=path_data,
    get_path="path",
    get_color="color",
    get_width="width",
    width_scale=1,
    width_min_pixels=1,
    pickable=False,
)

# City dots — all cities visited
visited = {}
for leg in visible_legs:
    visited[leg["from_city"]] = (leg["from_lat"], leg["from_lon"])
    visited[leg["to_city"]]   = (leg["to_lat"],   leg["to_lon"])

dot_data = [{"city": c, "lat": v[0], "lon": v[1]} for c, v in visited.items()]

dot_layer = pdk.Layer(
    "ScatterplotLayer",
    data=dot_data,
    get_position="[lon, lat]",
    get_radius=35000,
    get_fill_color=team_color_a,
    get_line_color=[255, 255, 255, 180],
    stroked=True,
    line_width_min_pixels=1,
    pickable=True,
)

# Home base pulsing ring
home_layer = pdk.Layer(
    "ScatterplotLayer",
    data=[{"lat": team_info["lat"], "lon": team_info["lon"]}],
    get_position="[lon, lat]",
    get_radius=60000,
    get_fill_color=team_color + [40],
    get_line_color=team_color + [255],
    stroked=True,
    line_width_min_pixels=2,
)

# Text labels
text_layer = pdk.Layer(
    "TextLayer",
    data=dot_data,
    get_position="[lon, lat]",
    get_text="city",
    get_size=13,
    get_color=[200, 220, 255, 220],
    get_anchor="'middle'",
    get_alignment_baseline="'bottom'",
    get_pixel_offset=[0, -18],
    font_family="'DM Mono', monospace",
)

# View centred on home city
view = pdk.ViewState(
    latitude=team_info["lat"],
    longitude=team_info["lon"],
    zoom=3.5,
    pitch=25,
    bearing=-10,
)

deck = pdk.Deck(
    layers=[path_layer, home_layer, dot_layer, text_layer],
    initial_view_state=view,
    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",    
    tooltip={"text": "{city}"},
)

# ── Page layout ───────────────────────────────────────────────────────────────
st.markdown(f'<div class="page-title">✈ {team_info["abbr"]} ROAD MAP</div>', unsafe_allow_html=True)
st.markdown(f'<div class="page-sub">{selected_team} · 2024–25 Season Travel</div>', unsafe_allow_html=True)

# Stats row
total_miles  = sum(l["miles"] for l in legs)
road_games   = sum(1 for l in legs if l["home_away"] == "away")
cities       = len(set([l["to_city"] for l in legs]))
flights      = len(legs)

c1, c2, c3, c4 = st.columns(4)
for col, num, lbl in [
    (c1, f"{int(total_miles):,}", "TOTAL MILES"),
    (c2, road_games,              "ROAD GAMES"),
    (c3, cities,                  "CITIES"),
    (c4, flights,                 "FLIGHTS"),
]:
    with col:
        st.markdown(f"""
        <div class="stat-box">
          <div class="stat-num">{num}</div>
          <div class="stat-lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Map + trip log side by side
map_col, log_col = st.columns([3, 1])

with map_col:
    st.pydeck_chart(deck, use_container_width=True, height=480)

with log_col:
    st.markdown("#### 🗓 TRIP LOG")
    for leg in sorted(visible_legs, key=lambda l: l["date"]):
        is_past = leg["date"] < today
        card_class = "trip-card past" if is_past else "trip-card"
        icon = "🏠" if leg["home_away"] == "home" else "✈️"
        status = "COMPLETED" if is_past else "UPCOMING"
        st.markdown(f"""
        <div class="{card_class}">
          <div class="leg-header">{icon} {leg['from_city']} → {leg['to_city']}</div>
          {leg['date'].strftime('%b %d')} · vs {TEAMS[leg['opponent']]['abbr']} · {status}
          <div class="miles">🛫 {int(leg['miles']):,} mi</div>
        </div>""", unsafe_allow_html=True)