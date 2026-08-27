from __future__ import annotations

import hashlib
import html
import random
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Thanos League · Year 8",
    page_icon="🫰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SEED = 2018
POSITION_SEQUENCE = ["QB", "RB", "WR", "TE", "K", "DST"]
STAGES = ["Teams", *POSITION_SEQUENCE, "Team Order"]
SHEET_ID = "1xzjWIp8K2mqWREVIkwmirCyLTrC4KuS-yXL9mmN6sgg"
DRAFT_GID = "1410253704"
PLAYERS_GID = "1215542528"
DRAFT_COLUMNS = ["Draft", "Round", "Pick", "Player"]
SILHOUETTE_PLAYER_HEADSHOT = (
    "data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 200 200%27%3E"
    "%3Crect width=%27200%27 height=%27200%27 fill=%27%231c1822%27/%3E"
    "%3Ccircle cx=%27100%27 cy=%2772%27 r=%2742%27 fill=%27%23615a69%27/%3E"
    "%3Cpath d=%27M30 200c4-55 30-82 70-82s66 27 70 82z%27 fill=%27%23615a69%27/%3E%3C/svg%3E"
)

TEAMS = [
    "The Mad Titans", "Reality Check", "Infinity Stoners", "Endgame Theory",
    "Wakanda Forever", "Glorious Purpose", "The Variants", "Quantum Mania",
    "Vibranium Vultures", "Asgardians", "Web Slingers", "Scarlet Winners",
    "Guardians of the Goal Line", "Loki Charms", "Multiverse of Madness", "The Blipped",
]

NFL_TEAMS = [
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
    "DET", "GB", "HOU", "IND", "JAX", "KC", "LV", "LAC", "LAR", "MIA",
    "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
    "TEN", "WAS",
]

POSITION_COUNTS = {"QB": 32, "RB": 80, "WR": 96, "TE": 40, "K": 32, "DST": 32}

# These legal picks are deliberately added only after the seeded player split.
# They therefore cannot change any existing Alive/Dusted assignment.
SPECIAL_UNRANKED_PLAYERS = {
    "Odell Beckham Jr.": "WR",
    "Darren Waller": "TE",
}

POSITION_STYLE = {
    "QB": ("#FF0000", "#FFFFFF"),
    "RB": ("#FF9900", "#000000"),
    "WR": ("#FFFF00", "#000000"),
    "TE": ("#00FF00", "#000000"),
    "DST": ("#0000FF", "#FFFFFF"),
    "K": ("#FF00FF", "#FFFFFF"),
    "FLX": ("#00FFFF", "#000000"),
    "BENCH": ("#CCCCCC", "#000000"),
}

POSITION_SOFT_STYLE = {
    "QB": ("#F2B7B7", "#5C2020"),
    "RB": ("#F6D7AC", "#5A3814"),
    "WR": ("#F4F1B8", "#514E18"),
    "TE": ("#BCE8BC", "#174D20"),
    "DST": ("#B7C1EA", "#1D2D68"),
    "K": ("#EDB9E4", "#5E1C54"),
}


@dataclass(frozen=True)
class Split:
    alive: list[str]
    dusted: list[str]


def stable_seed(label: str) -> int:
    digest = hashlib.sha256(f"thano-league-{SEED}-{label}".encode()).hexdigest()
    return int(digest[:12], 16)


def seeded_split(items: list[str], label: str) -> Split:
    shuffled = sorted(items, key=str.casefold)
    random.Random(stable_seed(label)).shuffle(shuffled)
    half = len(shuffled) // 2
    return Split(alive=shuffled[:half], dusted=shuffled[half:])


def sheet_csv_url(gid: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"


@st.cache_data(ttl=15)
def load_google_tab(gid: str) -> pd.DataFrame:
    return pd.read_csv(sheet_csv_url(gid), dtype=str).dropna(how="all")


def fallback_player_pool() -> dict[str, list[str]]:
    pool: dict[str, list[str]] = {}
    for position, count in POSITION_COUNTS.items():
        if position == "DST":
            pool[position] = [f"{team} Defense" for team in NFL_TEAMS]
        else:
            pool[position] = [f"{position} Player {n:02d}" for n in range(1, count + 1)]
    return pool


def live_player_data() -> tuple[list[str], dict[str, list[str]], bool]:
    """Return teams, positional pools, and whether the public Sheet loaded successfully."""
    try:
        frame = load_google_tab(PLAYERS_GID)
        if not {"Type", "Name"}.issubset(frame.columns):
            raise ValueError("Player grouping tab needs Type and Name columns")
        frame = frame[["Type", "Name"]].dropna()
        frame["Type"] = frame["Type"].astype(str).str.strip()
        frame["Name"] = frame["Name"].astype(str).str.strip()
        frame = frame[(frame["Type"] != "") & (frame["Name"] != "")]
        teams = frame.loc[frame["Type"].str.casefold() == "team", "Name"].tolist()
        pools = {
            position: frame.loc[frame["Type"].str.upper() == position, "Name"].tolist()
            for position in POSITION_COUNTS
        }
        if len(teams) != 16 or any(not names for names in pools.values()):
            raise ValueError("Player grouping tab is incomplete")
        return teams, pools, True
    except Exception:
        return TEAMS, fallback_player_pool(), False


def picture_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())


@st.cache_data
def player_picture_lookup() -> dict[str, str]:
    image_file = Path(__file__).with_name("player_images.csv")
    if not image_file.exists():
        return {}
    images = pd.read_csv(image_file, dtype=str).fillna("")
    lookup: dict[str, str] = {}
    for row in images.to_dict("records"):
        url = str(row.get("HeadshotURL", "")).strip() or str(row.get("PFRHeadshotURL", "")).strip()
        if url:
            lookup[picture_key(row.get("Player", ""))] = url
    return lookup


def player_picture(player: object) -> str:
    return player_picture_lookup().get(picture_key(player), SILHOUETTE_PLAYER_HEADSHOT)


@st.cache_data
def dummy_draft() -> pd.DataFrame:
    """Deterministic demo data matching the five-column draft sheet."""
    rng = random.Random(stable_seed("dummy-draft"))
    positions = (
        ["RB", "WR"] * 45 + ["QB"] * 30 + ["TE"] * 26 +
        ["K"] * 16 + ["DST"] * 16 + ["RB", "WR"] * 31
    )[:256]
    rng.shuffle(positions)
    counters = {p: 0 for p in POSITION_COUNTS}
    rows = []
    for overall in range(1, 257):
        round_no = (overall - 1) // 16 + 1
        slot = (overall - 1) % 16
        team_index = slot if round_no % 2 else 15 - slot
        position = positions[overall - 1]
        counters[position] += 1
        player = (
            f"{NFL_TEAMS[counters[position] - 1]} Defense"
            if position == "DST"
            else f"{position} Player {counters[position]:02d}"
        )
        rows.append({
            "Draft": "",
            "Round": round_no,
            "Pick": overall,
            "Team": TEAMS[team_index],
            "Player": player,
            "Position": position,
        })
    return pd.DataFrame(rows)


def live_draft_data() -> tuple[pd.DataFrame, bool]:
    try:
        frame = load_google_tab(DRAFT_GID)
        missing = [column for column in DRAFT_COLUMNS if column not in frame.columns]
        if missing:
            raise ValueError(f"Draft tab is missing: {', '.join(missing)}")
        frame = frame[DRAFT_COLUMNS].copy()
        frame = frame.dropna(subset=["Player"])
        for column in ["Round", "Pick"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
        teams, pools, _ = live_player_data()
        position_by_player = {
            picture_key(name): position
            for position, names in pools.items()
            for name in names
        }
        position_by_player.update({
            picture_key(name): position
            for name, position in SPECIAL_UNRANKED_PLAYERS.items()
        })
        frame["Position"] = frame["Player"].map(
            lambda player: position_by_player.get(picture_key(player), "")
            if pd.notna(player) else ""
        )
        teams_split = seeded_split(teams, "teams")
        realm_orders = {
            "alive": seeded_team_order(teams_split.alive, "Alive"),
            "dusted": seeded_team_order(teams_split.dusted, "Dusted"),
        }

        def infer_team(row: pd.Series) -> str:
            realm = str(row.get("Draft", "")).strip().casefold()
            order = realm_orders.get(realm)
            round_number = row.get("Round")
            pick_number = row.get("Pick")
            if order is None or pd.isna(round_number) or pd.isna(pick_number):
                return ""
            round_number = int(round_number)
            pick_in_round = (int(pick_number) - 1) % 8
            team_index = pick_in_round if round_number % 2 else 7 - pick_in_round
            return order[team_index]

        frame["Team"] = frame.apply(infer_team, axis=1)
        return frame, True
    except Exception:
        return dummy_draft(), False


def init_state() -> None:
    st.session_state.setdefault("snap_count", 8)
    st.session_state.setdefault("just_snapped", None)
    st.session_state.setdefault("position_view", "QB")
    st.session_state.setdefault("pending_position_view", None)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap');
        :root { --gold:#f6c65b; --purple:#6f45c7; --ink:#09070d; --ash:#8d8993; }
        .stApp {
            background:
              radial-gradient(circle at 80% 5%, rgba(111,69,199,.28), transparent 31rem),
              radial-gradient(circle at 10% 60%, rgba(246,198,91,.08), transparent 28rem),
              linear-gradient(155deg, #08060b 0%, #13101a 55%, #08070a 100%);
            color: #f6f2fb;
        }
        .block-container { max-width:2400px; width:98%; padding:1.6rem 1rem 5rem; }
        header[data-testid="stHeader"] { background: transparent; }
        #MainMenu, footer { visibility: hidden; }
        h1, h2, h3 { font-family: 'Bebas Neue', Impact, sans-serif !important; letter-spacing:.045em; }
        p, div, button { font-family: 'Inter', sans-serif; }
        .eyebrow { color:var(--gold); text-transform:uppercase; letter-spacing:.22em; font-weight:800; font-size:.72rem; }
        .hero-title { font-family:'Bebas Neue', Impact; font-size:clamp(4.6rem,11vw,9.5rem); line-height:.76; margin:.25rem 0 1rem; letter-spacing:.02em; }
        .hero-title span { color:transparent; -webkit-text-stroke:1px var(--gold); }
        .hero-copy { max-width:650px; color:#bdb6c8; font-size:1.08rem; line-height:1.7; }
        .year-mark { color:#fff; border-left:2px solid var(--gold); padding-left:1rem; margin-top:2rem; font-weight:800; letter-spacing:.18em; }
        .snap-orbit { text-align:center; font-size:7rem; filter:drop-shadow(0 0 28px rgba(246,198,91,.44)); animation:float 3s ease-in-out infinite; }
        @keyframes float { 50% { transform:translateY(-9px) rotate(-3deg); } }
        .stButton > button {
            width:100%; border-radius:0; border:1px solid var(--gold); background:linear-gradient(100deg,#d99e32,#ffe399,#d39a31);
            color:#120d07; text-transform:uppercase; letter-spacing:.12em; font-weight:900; min-height:3.5rem;
            box-shadow:0 10px 40px rgba(246,198,91,.12); transition:.2s ease;
        }
        .stButton > button:hover { transform:translateY(-2px); color:#120d07; border-color:#fff1bd; box-shadow:0 12px 35px rgba(246,198,91,.25); }
        .section-rule { height:1px; background:linear-gradient(90deg,var(--gold),transparent); margin:.4rem 0 1.5rem; }
        .stage-track { display:grid; grid-template-columns:repeat(8,1fr); gap:6px; margin:1.4rem 0 2.2rem; }
        .stage { padding:.7rem .2rem; font-size:.62rem; text-align:center; text-transform:uppercase; letter-spacing:.06em; color:#716b79; border-top:2px solid #2b2631; }
        .stage.done { color:var(--gold); border-color:var(--gold); }
        .stage.now { color:#fff; border-color:#fff; background:linear-gradient(180deg,rgba(255,255,255,.07),transparent); }
        .realm-head { padding:.8rem 0; border-bottom:1px solid #312b39; margin-bottom:.75rem; }
        .realm-head.alive { border-color:var(--gold); }
        .realm-head.dusted { border-color:#77717c; }
        .realm-title { font-family:'Bebas Neue'; font-size:2.2rem; letter-spacing:.08em; }
        .realm-sub { color:#8f8997; text-transform:uppercase; letter-spacing:.13em; font-size:.68rem; }
        .team-grid { display:grid; grid-template-columns:1fr; gap:7px; margin-bottom:1rem; }
        .team-card { border:1px solid #302b35; background:#050506; color:#fff; padding:.7rem .8rem; font-size:.76rem; min-height:3.2rem; display:flex; align-items:center; }
        .team-card.alive { border-left:3px solid var(--gold); }
        .team-card.dusted { border-left:3px solid #68636c; color:#aaa4ad; }
        .team-card.snap-left { --start-x:calc(50% + 5px); animation:sortedMove 1.25s cubic-bezier(.2,.8,.2,1) both; }
        .team-card.snap-right { --start-x:calc(-50% - 5px); animation:sortedMove 1.25s cubic-bezier(.2,.8,.2,1) both; }
        @keyframes sortedMove { from { opacity:.12; transform:translate(var(--start-x),var(--start-y)) scaleX(2); } to { opacity:1; transform:translate(0,0) scaleX(1); } }
        .center-roster { max-width:560px; margin:0 auto 2.5rem; }
        .center-roster-title { text-align:center; color:#77717f; font-size:.66rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.8rem; }
        .position-wait { min-height:7rem; display:flex; align-items:center; justify-content:center; border:1px dashed #3b3542; color:#817a88; background:rgba(5,5,6,.6); text-transform:uppercase; letter-spacing:.14em; font-size:.7rem; }
        .player-list-shell { max-height:none; overflow:visible; padding-right:0; }
        .player-list { display:grid; grid-template-columns:1fr; gap:6px; }
        .player-card { min-height:2.7rem; display:flex; align-items:center; padding:.55rem .8rem; font-size:.76rem; font-weight:800; border:1px solid rgba(255,255,255,.25); }
        .player-card.drafted-player { border-color:rgba(255,255,255,.14); filter:saturate(.7); }
        .player-rank { flex:0 0 2rem; margin-right:.4rem; font-size:.55rem; font-weight:1000; opacity:.68; letter-spacing:.04em; }
        .taken-chip { margin-left:auto; padding:.2rem .35rem; border:1px solid currentColor; border-radius:999px; font-size:.48rem; line-height:1; letter-spacing:.1em; text-transform:uppercase; opacity:.7; }
        .all-player-swipe { overflow-x:auto; scrollbar-width:none; -ms-overflow-style:none; }
        .all-player-swipe::-webkit-scrollbar { display:none; width:0; height:0; }
        .all-realms-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; min-width:900px; }
        .all-realm-grid { display:grid; grid-template-columns:repeat(4,minmax(100px,1fr)); gap:6px; }
        .all-player-card { min-height:3rem; padding:.45rem .5rem; display:flex; flex-direction:column; justify-content:center; border:1px solid rgba(255,255,255,.18); border-radius:5px; font-size:.64rem; font-weight:900; overflow-wrap:anywhere; }
        .all-player-card .all-pos { margin-top:.25rem; font-size:.48rem; opacity:.65; letter-spacing:.1em; text-transform:uppercase; }
        .all-player-card .all-rank { font-size:.48rem; opacity:.68; letter-spacing:.08em; }
        .all-player-card.drafted-player { filter:saturate(.7); }
        .player-card.player-left { --start-x:calc(50% + 5px); animation:sortedMove 1s cubic-bezier(.2,.8,.2,1) both; }
        .player-card.player-right { --start-x:calc(-50% - 5px); animation:sortedMove 1s cubic-bezier(.2,.8,.2,1) both; }
        .pool-heading { text-align:center; margin:.5rem 0 1rem; }
        .pool-heading strong { display:block; font-family:'Bebas Neue'; font-size:2rem; letter-spacing:.07em; }
        .pool-heading span { color:#817a88; font-size:.65rem; text-transform:uppercase; letter-spacing:.13em; }
        .pool-card { border:1px solid #2d2833; padding:.8rem; margin-bottom:.55rem; background:rgba(12,10,15,.72); }
        .pool-pos { font-family:'Bebas Neue'; font-size:1.5rem; color:var(--gold); }
        .pool-names { font-size:.68rem; color:#96909e; line-height:1.55; }
        .order-row { display:flex; gap:.75rem; align-items:center; border-bottom:1px solid #2b2630; padding:.6rem .2rem; font-size:.76rem; }
        .order-pick { font-family:'Bebas Neue'; color:var(--gold); font-size:1.35rem; width:1.5rem; }
        .empty-state { border:1px dashed #3b3542; color:#746e7b; padding:2rem; text-align:center; text-transform:uppercase; letter-spacing:.1em; font-size:.7rem; }
        div[data-testid="stDataFrame"] { border:1px solid #312b38; }
        .draft-label { font-family:'Bebas Neue'; font-size:1.55rem; letter-spacing:.08em; margin-top:.5rem; }
        .source-live { display:inline-flex; align-items:center; gap:.45rem; color:#a8e6b0; border:1px solid #294d31; background:#102016; padding:.35rem .55rem; font-size:.6rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; }
        .source-live:before { content:''; width:6px; height:6px; background:#66dc79; border-radius:50%; box-shadow:0 0 8px #66dc79; }
        .source-fallback { color:#d9b46a; border-color:#574729; background:#211b10; }
        .source-fallback:before { background:#d9b46a; box-shadow:none; }
        .position-legend { display:flex; flex-wrap:wrap; gap:7px; margin:.9rem 0 1.5rem; }
        .pos-chip { padding:.38rem .62rem; font-size:.62rem; font-weight:900; letter-spacing:.08em; border-radius:2px; }
        .split-stage { max-width:920px; margin:0 auto 2rem; }
        .split-grid { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:12px; }
        .realm-column { min-width:0; }
        div[data-baseweb="tab-list"] { overflow-x:auto; scrollbar-width:none; gap:5px; }
        div[data-baseweb="tab-list"]::-webkit-scrollbar { display:none; }
        div[data-baseweb="tab-list"] button[role="tab"] { min-width:72px; color:#fff !important; background:#17131d; border:1px solid #45394f; border-radius:7px 7px 0 0; opacity:1; }
        div[data-baseweb="tab-list"] button[role="tab"] * { color:#fff !important; opacity:1 !important; }
        div[data-baseweb="tab-list"] button[role="tab"][aria-selected="true"] { background:#6f45c7; border-color:#f6c65b; box-shadow:inset 0 -3px 0 #f6c65b,0 0 15px rgba(111,69,199,.35); }
        .draft-universes { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:20px; align-items:start; }
        .draft-universe { min-width:0; border:1px solid #3c3345; border-radius:12px; background:linear-gradient(160deg,rgba(24,19,29,.96),rgba(5,5,6,.96)); padding:.8rem; box-shadow:0 18px 50px rgba(0,0,0,.28); }
        .draft-universe-head { display:flex; align-items:end; justify-content:space-between; gap:1rem; border-bottom:1px solid #3a3341; padding:.25rem .2rem .7rem; }
        .draft-universe-title { font-family:'Bebas Neue'; font-size:2rem; letter-spacing:.08em; line-height:1; }
        .draft-universe-meta { color:#837b8b; font-size:.57rem; text-transform:uppercase; letter-spacing:.1em; text-align:right; }
        .board-label { display:flex; align-items:center; gap:.55rem; color:var(--gold); text-transform:uppercase; letter-spacing:.14em; font-size:.62rem; font-weight:900; margin:1rem 0 .45rem; }
        .board-label:after { content:''; height:1px; flex:1; background:linear-gradient(90deg,#55462b,transparent); }
        .board-swipe { overflow-x:auto; scrollbar-width:none; -ms-overflow-style:none; overscroll-behavior-x:contain; touch-action:pan-x pan-y; }
        .board-swipe::-webkit-scrollbar { display:none; width:0; height:0; }
        .draft-grid { display:grid; grid-template-columns:38px repeat(8,minmax(0,1fr)); width:100%; min-width:0; gap:2px; background:#211d25; border:1px solid #312a36; border-radius:7px; overflow:hidden; }
        .draft-cell { min-width:0; min-height:3rem; padding:.34rem .36rem; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; font-size:.6rem; font-weight:800; line-height:1.08; overflow:hidden; overflow-wrap:anywhere; transition:filter .16s ease; }
        .draft-cell:hover { filter:brightness(1.1); }
        .draft-cell.header { min-height:3.15rem; background:linear-gradient(180deg,#17131b,#050506); color:#fff; font-size:.56rem; border-bottom:1px solid #5c4a28; }
        .draft-cell.header .slot-badge { color:var(--gold); font-family:'Bebas Neue'; font-size:1rem; line-height:1; margin-bottom:.15rem; }
        .draft-cell.header .team-name { max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .draft-cell.row-label { font-size:.58rem; letter-spacing:.02em; }
        .draft-cell.pick { background:linear-gradient(145deg,#dedede,#bdbdbd); color:#000; }
        .draft-cell.empty-pick { background:linear-gradient(145deg,#a9a9a9,#8e8e8e); color:#444; }
        .board-player-name { font-weight:900; line-height:1.05; }
        .board-player-meta { margin-top:.22rem; font-size:.48rem; font-weight:700; opacity:.65; letter-spacing:.04em; text-transform:uppercase; }
        .order-universes { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:20px; margin-bottom:1.25rem; }
        .order-realm { border:1px solid #362f3d; border-radius:10px; padding:.7rem; background:rgba(5,5,6,.7); }
        .order-title { font-family:'Bebas Neue'; font-size:1.6rem; letter-spacing:.08em; color:var(--gold); margin-bottom:.5rem; }
        .order-slots { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:6px; }
        .order-card { min-width:0; border:1px solid #4b4053; background:linear-gradient(145deg,#241c2b,#0b090e); padding:.55rem; border-radius:6px; opacity:1; }
        .order-card.reveal { animation:slotReveal .8s cubic-bezier(.2,.8,.2,1) both; }
        .order-realm.sequential-dusted .order-title { animation:realmTitleReveal .45s 6.15s ease both; }
        .draft-universes.order-pending { animation:boardAfterOrder .5s 12.35s ease both; }
        .order-number { font-family:'Bebas Neue'; font-size:1.45rem; color:var(--gold); line-height:1; }
        .order-team { margin-top:.2rem; color:#fff; font-size:.64rem; font-weight:800; overflow-wrap:anywhere; }
        .order-wait { border:1px dashed #4b4053; color:#8e8596; text-align:center; padding:1.2rem; margin:1rem 0; text-transform:uppercase; letter-spacing:.12em; font-size:.65rem; }
        .clock-wrap { margin:1.35rem 0 1rem; }
        .clock-kicker { text-align:center; color:var(--gold); font-family:'Bebas Neue'; font-size:2.15rem; letter-spacing:.16em; line-height:1; margin-bottom:.65rem; }
        .clock-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
        .clock-card { position:relative; overflow:hidden; border:1px solid #69517d; border-radius:10px; padding:1rem; text-align:center; background:radial-gradient(circle at 50% 0,rgba(111,69,199,.35),transparent 70%),#08060b; box-shadow:0 0 28px rgba(111,69,199,.18); }
        .clock-card::before { content:''; position:absolute; inset:0; border-top:3px solid var(--gold); pointer-events:none; }
        .clock-realm { color:#a69eac; font-size:.58rem; font-weight:900; letter-spacing:.18em; text-transform:uppercase; }
        .clock-team { margin:.25rem 0; color:#fff; font-family:'Bebas Neue'; font-size:clamp(2rem,4.3vw,4.4rem); letter-spacing:.035em; line-height:.95; overflow-wrap:anywhere; }
        .clock-pick { color:var(--gold); font-size:.64rem; font-weight:900; letter-spacing:.12em; text-transform:uppercase; }
        .clock-wrap.order-pending { animation:boardAfterOrder .5s 12.35s ease both; }
        @keyframes slotReveal { from { opacity:0; transform:translateY(22px) scale(.9); filter:blur(5px); } to { opacity:1; transform:none; filter:none; } }
        @keyframes realmTitleReveal { from { opacity:.15; } to { opacity:1; } }
        @keyframes boardAfterOrder { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }
        .duplicate-alarm { position:sticky; top:.5rem; z-index:50; border:4px solid #fff; background:#ff0000; color:#fff; padding:1rem; margin:1rem 0; text-align:center; font-weight:1000; letter-spacing:.08em; text-transform:uppercase; box-shadow:0 0 0 5px #ff0000,0 0 35px rgba(255,0,0,.8); animation:alarmPulse .75s steps(2,end) infinite; }
        .duplicate-alarm strong { display:block; font-family:'Bebas Neue'; font-size:2rem; letter-spacing:.1em; }
        .unique-ok { border:1px solid #285b36; background:#102417; color:#83e398; padding:.65rem .8rem; margin:.8rem 0; text-align:center; font-size:.65rem; font-weight:900; letter-spacing:.1em; text-transform:uppercase; }
        @keyframes alarmPulse { 50% { background:#fff; color:#ff0000; border-color:#ff0000; transform:scale(1.012); } }
        @media (min-width:801px) and (max-width:1100px) {
            .draft-universes { grid-template-columns:1fr; gap:14px; }
        }
        @media (max-width:800px) {
            .block-container { padding-left:.8rem; padding-right:.8rem; padding-top:.8rem; }
            .hero-title { font-size:4.7rem; }
            .stage-track { display:flex; overflow-x:auto; gap:4px; margin-bottom:1.25rem; scrollbar-width:thin; }
            .stage { min-width:78px; font-size:.48rem; flex:0 0 auto; }
            .split-grid { gap:6px; }
            .realm-head { padding:.45rem 0; margin-bottom:.45rem; }
            .realm-title { font-size:1.45rem; }
            .team-card { min-height:2.75rem; padding:.45rem .5rem; font-size:.66rem; }
            .player-list-shell { max-height:none; overflow:visible; padding-right:0; }
            .player-card { min-height:2.45rem; padding:.4rem .42rem; font-size:.64rem; overflow-wrap:anywhere; }
            .player-rank { flex-basis:1.65rem; margin-right:.25rem; font-size:.48rem; }
            .taken-chip { font-size:.43rem; padding:.17rem .25rem; }
            .all-realms-grid { grid-template-columns:405px 405px; min-width:824px; gap:14px; }
            .all-realm-grid { grid-template-columns:repeat(4,96px); gap:5px; }
            .all-player-card { min-height:2.75rem; padding:.38rem .4rem; font-size:.58rem; }
            .center-roster { max-width:100%; }
            .pool-heading strong { font-size:1.65rem; }
            div[data-baseweb="tab-list"] { gap:4px; padding-bottom:3px; }
            div[data-baseweb="tab-list"] button[role="tab"] { min-width:62px; min-height:2.65rem; padding:.35rem .55rem; font-size:.72rem; font-weight:900; }
            .stButton > button { min-height:3rem; font-size:.72rem; }
            .draft-universes { grid-template-columns:1fr; gap:14px; }
            .draft-universe { padding:.45rem; }
            .draft-grid { grid-template-columns:36px repeat(8,98px); min-width:834px; }
            .draft-cell { min-height:2.7rem; font-size:.56rem; padding:.25rem; }
            .draft-cell.header { min-height:2.9rem; }
            .order-universes { grid-template-columns:1fr; gap:10px; }
            .order-slots { grid-template-columns:repeat(2,minmax(0,1fr)); }
            .order-card { padding:.45rem .35rem; }
            .order-team { font-size:.58rem; }
            .clock-grid { grid-template-columns:1fr; gap:8px; }
            .clock-kicker { font-size:1.65rem; }
            .clock-card { padding:.8rem .55rem; }
            .clock-team { font-size:2.35rem; }
            .duplicate-alarm { position:static; font-size:.7rem; padding:.75rem .5rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def stage_track(count: int) -> None:
    parts = []
    for index, label in enumerate(STAGES, 1):
        state = "done" if index <= count else "now" if index == count + 1 else ""
        parts.append(f'<div class="stage {state}">{index:02d} · {label}</div>')
    st.markdown(f'<div class="stage-track">{"".join(parts)}</div>', unsafe_allow_html=True)


def team_cards(
    teams: list[str],
    realm: str,
    animate: bool = False,
    source_order: list[str] | None = None,
) -> str:
    source = sorted(source_order or teams, key=str.casefold)
    source_indices = {picture_key(name): index for index, name in enumerate(source)}
    cards = []
    for final_index, team in enumerate(teams):
        original_index = source_indices.get(team, final_index)
        delay = original_index * 5.25 / max(len(source) - 1, 1) if animate else 0
        start_y = (original_index - final_index) * 3.6375 if animate else 0
        motion = "snap-left" if animate and realm == "alive" else "snap-right" if animate else ""
        cards.append(
            f'<div class="team-card {realm} {motion}" '
            f'style="--start-y:{start_y:.3f}rem;animation-delay:{delay:.2f}s">'
            f'{html.escape(team)}</div>'
        )
    return f'<div class="team-grid">{"".join(cards)}</div>'


def team_split_html(split: Split, source_order: list[str], animate: bool) -> str:
    columns = []
    for realm, names in (("alive", split.alive), ("dusted", split.dusted)):
        sorted_names = sorted(names, key=str.casefold)
        columns.append(
            f'<div class="realm-column"><div class="realm-head {realm}">'
            f'<div class="realm-title">{realm.upper()}</div></div>'
            f'{team_cards(sorted_names, realm, animate, source_order)}</div>'
        )
    return f'<div class="split-stage"><div class="split-grid">{"".join(columns)}</div></div>'


def sorted_player_names(
    names: list[str],
    drafted_keys: set[str],
    ranking: list[str] | None = None,
) -> list[str]:
    """Return players in their immutable pre-snap Sheet ranking order."""
    ranking = ranking or names
    rank = {picture_key(name): index for index, name in enumerate(ranking)}
    return sorted(
        names,
        key=lambda name: (
            picture_key(name) in drafted_keys,
            rank.get(picture_key(name), len(rank)),
        ),
    )


def player_cards(
    names: list[str],
    position: str,
    realm: str = "",
    animate: bool = False,
    source_order: list[str] | None = None,
    drafted_keys: set[str] | None = None,
    rank_labels: dict[str, str] | None = None,
) -> str:
    drafted_keys = drafted_keys or set()
    rank_labels = rank_labels or {}
    source = list(source_order or names)
    source_indices = {picture_key(name): index for index, name in enumerate(source)}
    last_source_index = max(len(source) - 1, 1)
    cards = []
    for final_index, name in enumerate(names):
        is_drafted = picture_key(name) in drafted_keys
        background, foreground = POSITION_SOFT_STYLE[position] if is_drafted else POSITION_STYLE[position]
        original_index = source_indices.get(picture_key(name), final_index)
        delay = (original_index * 6 / last_source_index) if animate else 0
        start_y = (original_index - final_index) * 3.075 if animate else 0
        motion = "player-left" if animate and realm == "alive" else "player-right" if animate else ""
        taken_html = '<span class="taken-chip">Taken</span>' if is_drafted else ""
        rank_label = rank_labels.get(picture_key(name), f"#{original_index + 1}")
        cards.append(
            f'<div class="player-card {motion} {"drafted-player" if is_drafted else ""}" '
            f'data-status="{"drafted" if is_drafted else "available"}" '
            f'style="background:{background};color:{foreground};'
            f'--start-y:{start_y:.3f}rem;animation-delay:{delay:.2f}s">'
            f'<span class="player-rank">{html.escape(rank_label)}</span>{html.escape(name)}{taken_html}</div>'
        )
    return f'<div class="player-list-shell"><div class="player-list">{"".join(cards)}</div></div>'


def player_split_html(names: list[str], position: str, animate: bool, drafted_keys: set[str]) -> str:
    split = seeded_split(names, position)
    special_names = [
        name for name, special_position in SPECIAL_UNRANKED_PLAYERS.items()
        if special_position == position
    ]
    special_rank_labels = {picture_key(name): "UR" for name in special_names}
    columns = []
    for realm, realm_names in (("alive", split.alive), ("dusted", split.dusted)):
        sorted_names = sorted_player_names(realm_names, drafted_keys, names)
        display_names = [*sorted_names, *special_names]
        columns.append(
            f'<div class="realm-column"><div class="realm-head {realm}">'
            f'<div class="realm-title">{realm.upper()}</div></div>'
            f'{player_cards(display_names, position, realm, animate, names, drafted_keys, special_rank_labels)}</div>'
        )
    return f'<div class="split-stage"><div class="split-grid">{"".join(columns)}</div></div>'


def all_players_html(
    pools: dict[str, list[str]],
    drafted_keys: set[str],
    snapped_positions: list[str],
) -> str:
    rank_by_position = {
        position: {picture_key(name): index for index, name in enumerate(pools[position])}
        for position in snapped_positions
    }
    realm_columns = []
    for realm in ("alive", "dusted"):
        players: list[tuple[str, str]] = []
        for position in snapped_positions:
            split = seeded_split(pools[position], position)
            realm_names = split.alive if realm == "alive" else split.dusted
            players.extend((name, position) for name in realm_names)
        players.extend(
            (name, position)
            for name, position in SPECIAL_UNRANKED_PLAYERS.items()
            if position in snapped_positions
        )
        players.sort(
            key=lambda item: (
                picture_key(item[0]) in drafted_keys,
                rank_by_position[item[1]].get(picture_key(item[0]), len(pools[item[1]])),
                POSITION_SEQUENCE.index(item[1]),
            )
        )
        cards = []
        for name, position in players:
            is_drafted = picture_key(name) in drafted_keys
            is_unranked = name in SPECIAL_UNRANKED_PLAYERS
            rank_number = rank_by_position[position].get(picture_key(name), 0) + 1
            rank_label = "UR" if is_unranked else f"#{rank_number}"
            background, foreground = POSITION_SOFT_STYLE[position] if is_drafted else POSITION_STYLE[position]
            status_class = "drafted-player" if is_drafted else ""
            status = " - Taken" if is_drafted else ""
            cards.append(
                f'<div class="all-player-card {status_class}" data-status="{"drafted" if is_drafted else "available"}" '
                f'style="background:{background};color:{foreground}">'
                f'<span class="all-rank">{rank_label}</span>{html.escape(name)}'
                f'<span class="all-pos">{position}{status}</span></div>'
            )
        realm_columns.append(
            f'<div class="realm-column"><div class="realm-head {realm}">'
            f'<div class="realm-title">{realm.upper()}</div></div>'
            f'<div class="all-realm-grid">{"".join(cards)}</div></div>'
        )
    return f'<div class="all-player-swipe"><div class="all-realms-grid">{"".join(realm_columns)}</div></div>'


def position_tabs(
    count: int,
    pools: dict[str, list[str]],
    just_snapped: str | None,
    drafted_keys: set[str],
) -> None:
    tabs = st.tabs([*POSITION_SEQUENCE, "All"])
    for index, (tab, position) in enumerate(zip(tabs[:-1], POSITION_SEQUENCE)):
        stage_number = index + 2
        pool_names = pools[position]
        names = sorted_player_names(pool_names, drafted_keys, pool_names)
        drafted_count = sum(picture_key(name) in drafted_keys for name in pools[position])
        with tab:
            if count >= stage_number:
                st.markdown(
                    player_split_html(pool_names, position, animate=just_snapped == position, drafted_keys=drafted_keys),
                    unsafe_allow_html=True,
                )
            elif count == stage_number - 1:
                st.markdown(
                    f'<div class="pool-heading"><strong>{position}</strong><span>{len(names) - drafted_count} available · {drafted_count} taken</span></div>',
                    unsafe_allow_html=True,
                )
                button_left, button_center, button_right = st.columns([1, 1.25, 1])
                with button_center:
                    if st.button(f"🫰 Snap {position}", key=f"snap_{position}"):
                        st.session_state.snap_count = stage_number
                        st.session_state.just_snapped = position
                        st.rerun()
                st.markdown(
                    f'<div class="center-roster">{player_cards(names, position, source_order=pool_names, drafted_keys=drafted_keys)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="position-wait">Not Yet Snapped</div>', unsafe_allow_html=True)
    with tabs[-1]:
        snapped_positions = [
            position
            for index, position in enumerate(POSITION_SEQUENCE)
            if count >= index + 2
        ]
        all_count = sum(len(pools[position]) for position in snapped_positions)
        drafted_count = sum(
            picture_key(name) in drafted_keys
            for position in snapped_positions
            for name in pools[position]
        )
        if not snapped_positions:
            st.markdown('<div class="position-wait">No position pools snapped yet</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="pool-heading"><strong>ALL SNAPPED PLAYERS</strong><span>{all_count - drafted_count} available · {drafted_count} taken · combined snap results</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                all_players_html(pools, drafted_keys, snapped_positions),
                unsafe_allow_html=True,
            )


def pool_cards(realm: str, count: int, pools: dict[str, list[str]]) -> None:
    plural_stage_to_position = {"QBs": "QB", "RBs": "RB", "WRs": "WR", "TEs": "TE", "Ks": "K", "DSTs": "DST"}
    visible = [s for s in STAGES[1:7] if STAGES.index(s) + 1 <= count]
    if not visible:
        st.markdown('<div class="empty-state">Awaiting the next snap</div>', unsafe_allow_html=True)
        return
    for stage in visible:
        pos = plural_stage_to_position[stage]
        split = seeded_split(pools[pos], pos)
        names = split.alive if realm == "alive" else split.dusted
        preview = " · ".join(names[:5]) + (f" · +{len(names)-5}" if len(names) > 5 else "")
        st.markdown(
            f'<div class="pool-card"><div class="pool-pos">{pos} <span style="color:#5f5966;font-size:.8rem">{len(names)} players</span></div>'
            f'<div class="pool-names">{preview}</div></div>', unsafe_allow_html=True,
        )


def order_list(teams: list[str]) -> None:
    ordered = teams.copy()
    random.Random(stable_seed("team-order-" + "|".join(sorted(teams)))).shuffle(ordered)
    for index, team in enumerate(ordered, 1):
        st.markdown(f'<div class="order-row"><div class="order-pick">{index}</div><div>{team}</div></div>', unsafe_allow_html=True)
    st.caption("Snake: 1→8 in odd rounds · 8→1 in even rounds")


def render_draft_board(teams_split: Split) -> None:
    st.markdown("## The Draft Board")
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    draft, is_live = live_draft_data()
    source_class = "source-live" if is_live else "source-live source-fallback"
    source_label = "Google Sheet connected" if is_live else "Offline demo data"
    st.markdown(f'<div class="{source_class}">{source_label}</div>', unsafe_allow_html=True)
    legend = "".join(
        f'<span class="pos-chip" style="background:{background};color:{foreground}">{position}</span>'
        for position, (background, foreground) in POSITION_STYLE.items()
    )
    st.markdown(f'<div class="position-legend">{legend}</div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")
    for column, realm, teams in ((left, "ALIVE", teams_split.alive), (right, "DUSTED", teams_split.dusted)):
        with column:
            st.markdown(f'<div class="draft-label">{realm} UNIVERSE</div>', unsafe_allow_html=True)
            explicit_realm = draft["Draft"].fillna("").astype(str).str.strip().str.casefold()
            if explicit_realm.ne("").any():
                realm_df = draft[explicit_realm == realm.casefold()].copy()
            else:
                realm_df = draft[draft["Team"].isin(teams)].copy()
            realm_df.insert(0, "Photo", realm_df["Player"].map(player_picture))
            realm_df = realm_df.drop(columns=["Draft"])
            styled_df = realm_df.style.map(
                lambda value: (
                    f"background-color: {POSITION_STYLE[value][0]}; "
                    f"color: {POSITION_STYLE[value][1]}; font-weight: 800"
                ),
                subset=["Position"],
            )
            st.dataframe(
                styled_df,
                width="stretch",
                hide_index=True,
                height=520,
                column_config={
                    "Photo": st.column_config.ImageColumn("", width="small"),
                    "Round": st.column_config.NumberColumn("RD", width="small"),
                    "Pick": st.column_config.NumberColumn("PK", width="small"),
                    "Position": st.column_config.TextColumn("POS", width="small"),
                },
            )


ROSTER_SCHEMA = [
    ("QB", "QB"),
    ("RB1", "RB"),
    ("RB2", "RB"),
    ("WR1", "WR"),
    ("WR2", "WR"),
    ("TE", "TE"),
    ("FLEX", "FLX"),
    ("K", "K"),
    ("DST", "DST"),
    *[(f"BENCH{index}", "BENCH") for index in range(1, 8)],
]


def normalized_position(value: object) -> str:
    position = str(value).strip().upper().replace("D/ST", "DST").replace("DEF", "DST")
    return position


def seeded_team_order(teams: list[str], realm: str) -> list[str]:
    ordered = sorted(teams, key=str.casefold)
    random.Random(stable_seed(f"team-order-{realm}")).shuffle(ordered)
    return ordered


def draft_record(row: pd.Series | dict) -> dict[str, str]:
    def clean(field: str) -> str:
        value = str(row.get(field, "")).strip()
        return "" if value.casefold() in {"", "nan", "none", "<na>"} else value

    return {
        "player": clean("Player"),
        "position": normalized_position(row.get("Position", "")),
    }


def assigned_roster(team_picks: pd.DataFrame) -> dict[str, dict[str, str]]:
    if team_picks.empty:
        return {}
    ordered = team_picks.copy().sort_values(["Pick", "Round"], na_position="last").reset_index(drop=True)
    records = []
    for record_id, row in ordered.iterrows():
        player = str(row.get("Player", "")).strip()
        if player and player.casefold() not in {"nan", "none"}:
            records.append({"id": record_id, **draft_record(row)})

    roster: dict[str, dict[str, str]] = {}
    used: set[int] = set()
    fixed_slots = [
        ("QB", "QB"), ("RB1", "RB"), ("RB2", "RB"), ("WR1", "WR"),
        ("WR2", "WR"), ("TE", "TE"), ("K", "K"), ("DST", "DST"),
    ]
    for slot, wanted_position in fixed_slots:
        match = next((record for record in records if record["id"] not in used and record["position"] == wanted_position), None)
        if match:
            roster[slot] = match
            used.add(match["id"])

    flex = next(
        (record for record in records if record["id"] not in used and record["position"] in {"RB", "WR", "TE"}),
        None,
    )
    if flex:
        roster["FLEX"] = flex
        used.add(flex["id"])

    bench_position_order = {position: index for index, position in enumerate(POSITION_SEQUENCE)}
    bench = sorted(
        (record for record in records if record["id"] not in used),
        key=lambda record: (
            bench_position_order.get(record["position"], len(bench_position_order)),
            record["id"],
        ),
    )[:7]
    for index, record in enumerate(bench, 1):
        roster[f"BENCH{index}"] = record
    return roster


def draft_rows_for_realm(draft: pd.DataFrame, realm: str, teams: list[str]) -> pd.DataFrame:
    explicit = draft["Draft"].fillna("").astype(str).str.strip().str.casefold()
    if explicit.eq(realm.casefold()).any():
        return draft[explicit == realm.casefold()].copy()
    return draft[draft["Team"].isin(teams)].copy()


def board_player_html(record: dict[str, str] | None) -> str:
    if not record or not record.get("player"):
        return "&nbsp;"
    return f'<span class="board-player-name">{html.escape(record["player"])}</span>'


def draft_header_cells(team_order: list[str]) -> list[str]:
    cells = ['<div class="draft-cell header"></div>']
    for slot, team in enumerate(team_order, 1):
        cells.append(
            f'<div class="draft-cell header"><span class="slot-badge">{slot:02d}</span>'
            f'<span class="team-name">{html.escape(team)}</span></div>'
        )
    return cells


def roster_board_html(draft: pd.DataFrame, team_order: list[str]) -> str:
    rosters = {
        team: assigned_roster(draft[draft["Team"].fillna("").astype(str) == team])
        for team in team_order
    }
    cells = draft_header_cells(team_order)
    for slot_key, color_key in ROSTER_SCHEMA:
        background, foreground = POSITION_STYLE[color_key]
        label = "B" if color_key == "BENCH" else "FLX" if color_key == "FLX" else color_key
        cells.append(
            f'<div class="draft-cell row-label" style="background:{background};color:{foreground}">{label}</div>'
        )
        for team in team_order:
            record = rosters[team].get(slot_key)
            player = "" if not record else record.get("player", "")
            tile_background, tile_foreground = background, foreground
            if color_key in {"BENCH", "FLX"} and record:
                tile_background, tile_foreground = POSITION_STYLE.get(
                    record.get("position", ""), POSITION_STYLE[color_key]
                )
            cells.append(
                f'<div class="draft-cell" style="background:{tile_background};color:{tile_foreground}" title="{html.escape(player)}">'
                f'{board_player_html(record)}</div>'
            )
    return f'<div class="board-swipe"><div class="draft-grid">{"".join(cells)}</div></div>'


def round_board_html(draft: pd.DataFrame, team_order: list[str]) -> str:
    cells = draft_header_cells(team_order)
    cells[0] = '<div class="draft-cell header">RD</div>'
    for round_number in range(1, 17):
        arrow = "→" if round_number % 2 else "←"
        cells.append(f'<div class="draft-cell row-label pick">{arrow} {round_number}</div>')
        for team in team_order:
            matches = draft[
                (draft["Team"].fillna("").astype(str) == team)
                & (draft["Round"] == round_number)
            ]
            record = None if matches.empty else draft_record(matches.iloc[0])
            player = "" if record is None else record.get("player", "")
            cell_class = "draft-cell pick" if player else "draft-cell empty-pick"
            style = ""
            if player:
                background, foreground = POSITION_STYLE.get(
                    record.get("position", ""), POSITION_STYLE["BENCH"]
                )
                style = f' style="background:{background};color:{foreground}"'
            cells.append(
                f'<div class="{cell_class}"{style} title="{html.escape(player)}">'
                f'{board_player_html(record)}</div>'
            )
    return f'<div class="board-swipe"><div class="draft-grid">{"".join(cells)}</div></div>'


def duplicate_players(draft: pd.DataFrame) -> pd.Series:
    players = draft["Player"].dropna().astype(str).str.strip()
    players = players[~players.str.casefold().isin(["", "nan", "none"])]
    return players.value_counts()[lambda counts: counts > 1]


def league_assignment_issues(draft: pd.DataFrame, pools: dict[str, list[str]]) -> list[str]:
    expected_realm: dict[str, str] = {}
    for position, names in pools.items():
        split = seeded_split(names, position)
        expected_realm.update({picture_key(name): "Alive" for name in split.alive})
        expected_realm.update({picture_key(name): "Dusted" for name in split.dusted})

    issues = []
    legal_either_realm = {picture_key(name) for name in SPECIAL_UNRANKED_PLAYERS}
    for _, row in draft.iterrows():
        player = str(row.get("Player", "")).strip()
        if not player or player.casefold() in {"nan", "none", "<na>"}:
            continue
        expected = expected_realm.get(picture_key(player))
        actual_raw = str(row.get("Draft", "")).strip()
        actual = "Alive" if "alive" in actual_raw.casefold() else "Dusted" if "dust" in actual_raw.casefold() else ""
        if picture_key(player) in legal_either_realm:
            if not actual:
                issues.append(f"{player}: Draft must be Alive or Dusted (legal in either)")
        elif expected is None:
            issues.append(f"{player}: not found in the player pools")
        elif not actual:
            issues.append(f"{player}: Draft must be Alive or Dusted (belongs in {expected})")
        elif actual != expected:
            issues.append(f"{player}: entered in {actual}, belongs in {expected}")
    return issues


def draft_order_reveal_html(teams_split: Split, animate: bool) -> str:
    realms = []
    for realm_index, (realm, teams) in enumerate((("Alive", teams_split.alive), ("Dusted", teams_split.dusted))):
        order = seeded_team_order(teams, realm)
        cards = []
        realm_delay = 6.25 * realm_index if animate else 0
        for slot, team in enumerate(order, 1):
            reveal = "reveal" if animate else ""
            delay = realm_delay + ((slot - 1) * .75)
            cards.append(
                f'<div class="order-card {reveal}" style="animation-delay:{delay:.2f}s">'
                f'<div class="order-number">{slot:02d}</div><div class="order-team">{html.escape(team)}</div></div>'
            )
        realm_class = " sequential-dusted" if animate and realm == "Dusted" else ""
        realms.append(
            f'<section class="order-realm{realm_class}"><div class="order-title">{realm} Draft Order</div>'
            f'<div class="order-slots">{"".join(cards)}</div></section>'
        )
    return f'<div class="order-universes">{"".join(realms)}</div>'


def on_clock_html(draft: pd.DataFrame, teams_split: Split, animate: bool) -> str:
    cards = []
    for realm, realm_teams in (("Alive", teams_split.alive), ("Dusted", teams_split.dusted)):
        order = seeded_team_order(realm_teams, realm)
        realm_draft = draft_rows_for_realm(draft, realm, realm_teams)
        players = realm_draft["Player"].dropna().astype(str).str.strip()
        pick_count = int((~players.str.casefold().isin(["", "nan", "none"])).sum())
        if pick_count >= 128:
            team_text = "Draft Complete"
            pick_text = "All 128 selections are in"
        else:
            round_number = (pick_count // 8) + 1
            pick_in_round = pick_count % 8
            team_index = pick_in_round if round_number % 2 else 7 - pick_in_round
            team_text = order[team_index]
            pick_text = f"Round {round_number} · Pick {pick_count + 1}"
        cards.append(
            f'<div class="clock-card"><div class="clock-realm">{realm} Draft</div>'
            f'<div class="clock-team">{html.escape(team_text)}</div>'
            f'<div class="clock-pick">{html.escape(pick_text)}</div></div>'
        )
    pending_class = " order-pending" if animate else ""
    return (
        f'<section class="clock-wrap{pending_class}"><div class="clock-kicker">ON THE CLOCK</div>'
        f'<div class="clock-grid">{"".join(cards)}</div></section>'
    )


def render_draft_boards(teams_split: Split, animate_order: bool = False) -> None:
    st.markdown("## LIVE DRAFT BOARDS")
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    refresh_left, refresh_center, refresh_right = st.columns([1, 1.15, 1])
    with refresh_center:
        if st.button("↻ Update Draft Board", key="refresh_draft_board", type="primary"):
            load_google_tab.clear()
            st.rerun()
    draft, is_live = live_draft_data()
    st.markdown(on_clock_html(draft, teams_split, False), unsafe_allow_html=True)
    _, pools, _ = live_player_data()
    league_issues = league_assignment_issues(draft, pools) if is_live else []
    if league_issues:
        examples = " · ".join(league_issues[:8])
        extra = f" · +{len(league_issues) - 8} more" if len(league_issues) > 8 else ""
        st.markdown(
            f'<div class="duplicate-alarm"><strong>🚨 Wrong Draft Detected 🚨</strong>'
            f'{html.escape(examples + extra)}</div>',
            unsafe_allow_html=True,
        )
    elif is_live:
        st.markdown(
            '<div class="unique-ok">✓ League assignment check passed · every player is in the correct universe</div>',
            unsafe_allow_html=True,
        )
    duplicates = duplicate_players(draft)
    if not duplicates.empty:
        examples = ", ".join(f"{name} ×{count}" for name, count in duplicates.head(8).items())
        st.markdown(
            f'<div class="duplicate-alarm"><strong>🚨 Duplicate Players Detected 🚨</strong>'
            f'Fix the draft sheet now: {html.escape(examples)}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="unique-ok">✓ Uniqueness check passed · every drafted player appears once</div>',
            unsafe_allow_html=True,
        )

    universe_html = []
    for realm, realm_teams in (("Alive", teams_split.alive), ("Dusted", teams_split.dusted)):
        order = seeded_team_order(realm_teams, realm)
        realm_draft = draft_rows_for_realm(draft, realm, realm_teams)
        pick_count = int(realm_draft["Player"].notna().sum())
        universe_html.append(
            f'<section class="draft-universe"><div class="draft-universe-head">'
            f'<div class="draft-universe-title">{realm} Draft</div>'
            f'<div class="draft-universe-meta">8 teams · {pick_count} picks logged</div></div>'
            f'<div class="board-label">Roster by position</div>{roster_board_html(realm_draft, order)}'
            f'<div class="board-label">Draft order · snake</div>{round_board_html(realm_draft, order)}</section>'
        )
    st.markdown(f'<div class="draft-universes">{"".join(universe_html)}</div>', unsafe_allow_html=True)


def render_app() -> None:
    count = st.session_state.snap_count
    teams, pools, _ = live_player_data()
    draft_frame, _ = live_draft_data()
    drafted_keys = {
        picture_key(player)
        for player in draft_frame["Player"].dropna().astype(str).str.strip()
        if player and player.casefold() != "nan"
    }
    drafted_keys.update(picture_key(name) for name in SPECIAL_UNRANKED_PLAYERS)
    just_snapped = st.session_state.just_snapped
    teams_split = seeded_split(teams, "teams")
    st.markdown('<div class="eyebrow">Thanos League · Year 8</div>', unsafe_allow_html=True)
    st.markdown("# LIVE DRAFT COMMAND CENTER")
    render_draft_boards(teams_split)

    st.markdown("## AVAILABLE PLAYER POOLS")
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    position_tabs(8, pools, None, drafted_keys)

    st.markdown("## THANOS SNAP RANDOMIZATION")
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    with st.expander("View or replay the complete randomization", expanded=count < 8):
        control_left, control_center, control_right = st.columns(3)
        with control_left:
            if count == 0 and st.button("🫰 Snap Teams", key="next_snap"):
                st.session_state.snap_count = 1
                st.session_state.just_snapped = "Teams"
                st.rerun()
        with control_center:
            if count > 0 and st.button("Replay from beginning", key="reset"):
                st.session_state.snap_count = 0
                st.session_state.just_snapped = None
                st.rerun()
        with control_right:
            if count < 8 and st.button("Skip all randomizers", key="skip_all"):
                st.session_state.snap_count = 8
                st.session_state.just_snapped = None
                st.rerun()

        stage_track(count)
        if count == 0:
            st.markdown('<div class="center-roster"><div class="center-roster-title">16 teams awaiting the snap</div>', unsafe_allow_html=True)
            st.markdown(team_cards(sorted(teams, key=str.casefold), "unsnapped"), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                team_split_html(teams_split, teams, animate=just_snapped == "Teams"),
                unsafe_allow_html=True,
            )

        st.markdown("### POSITION SNAP REPLAY")
        position_tabs(count, pools, just_snapped, drafted_keys)
        if count == 7:
            st.markdown(
                '<div class="order-wait">Alive and Dusted teams are ready · Snap Team Order to assign draft slots 1–8</div>',
                unsafe_allow_html=True,
            )
            order_left, order_center, order_right = st.columns([1, 1.25, 1])
            with order_center:
                if st.button("🫰 Snap Team Order", key="snap_team_order"):
                    st.session_state.snap_count = 8
                    st.session_state.just_snapped = "Team Order"
                    st.rerun()
        elif count >= 8:
            st.markdown(
                draft_order_reveal_html(teams_split, animate=just_snapped == "Team Order"),
                unsafe_allow_html=True,
            )
    st.session_state.just_snapped = None


init_state()
inject_css()
render_app()
