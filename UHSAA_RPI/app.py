import streamlit as st
import pandas as pd
import random
import time
import matplotlib

st.set_page_config(
    page_title="NBA Draft Lottery Simulator",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800;900&family=Barlow:wght@300;400;500;600&display=swap');

html, body, [class*="css"], .stApp { font-family: 'Barlow', sans-serif; }

#MainMenu, footer, header { visibility: hidden; }

.stApp { background: #080c14; }

[data-testid="stSidebar"] {
    background: #0c1220 !important;
    border-right: 1px solid #1e2d45;
}
[data-testid="stSidebar"] * { color: #c8d8f0 !important; }

.hero {
    background: linear-gradient(135deg, #0d1b35 0%, #081020 60%, #0d1b35 100%);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '🏀';
    position: absolute;
    right: 24px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 6rem;
    opacity: 0.08;
}
.hero h1 {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 900;
    font-size: 2.8rem;
    color: #ffffff;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 0 0 6px 0;
    line-height: 1;
}
.hero p {
    color: #6a8ab0;
    font-size: 0.95rem;
    margin: 0;
    font-weight: 300;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.hero .accent { color: #f7941d; }

.stat-strip {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
}
.stat-box {
    flex: 1;
    background: #0c1220;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.stat-box .label {
    font-family: 'Barlow Condensed', sans-serif;
    color: #4a6a8a;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 600;
}
.stat-box .value {
    font-family: 'Barlow Condensed', sans-serif;
    color: #f7941d;
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.1;
}
.stat-box .sub {
    color: #4a6a8a;
    font-size: 0.7rem;
}

.section-header {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800;
    font-size: 1.5rem;
    color: #ffffff;
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 2px;
    background: linear-gradient(90deg, #f7941d, transparent);
}

.pick-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Barlow', sans-serif;
}
.pick-table tr {
    border-bottom: 1px solid #12213a;
    transition: background 0.15s;
}
.pick-table tr:hover { background: #0f1e32; }
.pick-table tr.top3 { background: #0f1e32; }
.pick-table tr.penalized { background: #1a0f0f; }
.pick-table tr.champ { background: #121a0f; }

.pick-num {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 900;
    font-size: 1.4rem;
    color: #f7941d;
    padding: 10px 16px;
    width: 56px;
    text-align: center;
}
.pick-num.mid { color: #7aabdc; }
.pick-num.late { color: #4a6a8a; }

.pick-team {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 1.15rem;
    color: #ddeeff;
    letter-spacing: 0.5px;
    padding: 10px 8px;
}

.pick-balls {
    color: #4a6a8a;
    font-size: 0.8rem;
    padding: 10px 8px;
    text-align: center;
    width: 60px;
}

.pick-note {
    font-size: 0.75rem;
    padding: 10px 8px 10px 0;
    text-align: right;
}

.tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 0.7rem;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.tag-protect { background: #1a3a6a; color: #7aabdc; border: 1px solid #2a5a9a; }
.tag-champ   { background: #1a3a1a; color: #7adc7a; border: 1px solid #2a6a2a; }
.tag-penalty { background: #3a1a0a; color: #dcaa50; border: 1px solid #6a3a0a; }
.tag-top3    { background: #2a1a3a; color: #c07adc; border: 1px solid #4a2a6a; }

.balls-pips { display: inline-flex; gap: 3px; align-items: center; }
.pip {
    width: 7px; height: 7px; border-radius: 50%;
    background: #2a4a6a;
    display: inline-block;
}
.pip.active { background: #f7941d; }

.odds-note {
    background: #0c1220;
    border: 1px solid #1e2d45;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.8rem;
    color: #4a6a8a;
    margin-bottom: 16px;
    font-style: italic;
}

/* Sidebar elements */
.sidebar-rule {
    background: #0f1a2a;
    border: 1px solid #1e2d45;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 12px;
    font-size: 0.78rem;
    color: #6a8ab0 !important;
    line-height: 1.5;
}
.sidebar-rule strong { color: #c8d8f0 !important; }

/* Streamlit overrides */
div[data-testid="stButton"] > button {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    font-size: 0.9rem !important;
    border-radius: 8px !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #f7941d, #e06000) !important;
    border: none !important;
    color: white !important;
}
div[data-testid="stButton"] > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #1e3a5f !important;
    color: #7aabdc !important;
}

.stSelectbox label, .stMultiSelect label {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    color: #c8d8f0 !important;
    font-size: 0.8rem !important;
}

[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

.stProgress > div > div { background: #f7941d !important; }

.stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
TEAMS = ["Wizards", "Pacers", "Nets", "Jazz", "Kings", "Grizzlies",
         "Mavericks", "Pelicans", "Bulls", "Bucks", "Warriors",
         "Clippers", "Heat", "Hornets", "Suns", "Magic"]
BALLS = [2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 1, 1]
TOTAL_BALLS = sum(BALLS)  # 37
TEAM_BALLS = dict(zip(TEAMS, BALLS))
PROTECTED = {"Wizards", "Pacers", "Nets"}  # Slots 1-3: cannot finish 13-16


# ── Lottery Logic ─────────────────────────────────────────────────────────────
def run_lottery(won_last_year=None, two_straight=None):
    if two_straight is None:
        two_straight = []
    two_straight_set = set(two_straight)
    events = {}  # position → event tag

    # Build pool and shuffle
    pool = []
    for team, count in zip(TEAMS, BALLS):
        pool.extend([team] * count)
    random.shuffle(pool)

    # First occurrence of each team = draft order
    seen = set()
    order = []
    for team in pool:
        if team not in seen:
            seen.add(team)
            order.append(team)

    # ── Rule 1: Slot 1-3 protection ──────────────────────────────────────────
    # Wizards/Pacers/Nets cannot land in positions 13-16 (index 12-15)
    late_protected = [(i, order[i]) for i in range(12, 16) if order[i] in PROTECTED]
    if late_protected:
        teams_to_move = [t for _, t in late_protected]
        for team in teams_to_move:
            order.remove(team)
        for j, team in enumerate(teams_to_move):
            order.insert(11 + j, team)  # insert at position 12 (index 11), shift rest down

    # ── Rule 2: Won Last Year ────────────────────────────────────────────────
    # If selected team draws #1, they swap with #2
    if won_last_year and order[0] == won_last_year:
        order[0], order[1] = order[1], order[0]

    # ── Rule 3: Two Straight Top 5's ─────────────────────────────────────────
    # Filtered teams in positions 1-5 get pushed to 6+
    # Non-filtered teams fill 1-5 in original relative order
    if two_straight_set:
        top5 = order[:5]
        rest = order[5:]
        penalized = [t for t in top5 if t in two_straight_set]
        not_penalized = [t for t in top5 if t not in two_straight_set]
        if penalized:
            needed = 5 - len(not_penalized)
            filler = rest[:needed]
            remaining = rest[needed:]
            order = not_penalized + filler + penalized + remaining

    # Build event annotations on final positions
    for i, team in enumerate(order):
        if team in PROTECTED and i == 11 and any(t == team for _, t in late_protected):
            events[i] = "protect"
        elif won_last_year and team == won_last_year and i == 1:
            if len(late_protected) == 0 or team not in [t for _, t in late_protected]:
                events[i] = "champ"
        elif team in two_straight_set and i >= 5:
            top5_draw = any(t == team for t in (order[:5] if not two_straight_set else []))
            events[i] = "penalty"

    # Simpler annotation: just flag by rule type
    events = {}
    if late_protected:
        for team in [t for _, t in late_protected]:
            idx = order.index(team)
            events[idx] = "protect"
    if won_last_year and order[1] == won_last_year:
        # could be champ or coincidence - track via pre-swap
        pass
    # Re-derive who was penalized
    if two_straight_set:
        for team in two_straight:
            if team in order:
                idx = order.index(team)
                if idx >= 5:
                    events[idx] = "penalty"

    return order, events


def run_lottery_clean(won_last_year=None, two_straight=None):
    """Run lottery, return order + structured event list."""
    if two_straight is None:
        two_straight = []
    two_straight_set = set(two_straight)

    pool = []
    for team, count in zip(TEAMS, BALLS):
        pool.extend([team] * count)
    random.shuffle(pool)

    seen = set()
    order = []
    for team in pool:
        if team not in seen:
            seen.add(team)
            order.append(team)

    events = {}  # final_index -> tag

    # Rule 1
    late_protected = [(i, order[i]) for i in range(12, 16) if order[i] in PROTECTED]
    protected_moved = set()
    if late_protected:
        teams_to_move = [t for _, t in late_protected]
        protected_moved = set(teams_to_move)
        for team in teams_to_move:
            order.remove(team)
        for j, team in enumerate(teams_to_move):
            order.insert(11 + j, team)

    # Rule 2
    champ_swapped = False
    if won_last_year and order[0] == won_last_year:
        order[0], order[1] = order[1], order[0]
        champ_swapped = True

    # Rule 3
    penalized_teams = set()
    if two_straight_set:
        top5 = order[:5]
        rest = order[5:]
        penalized = [t for t in top5 if t in two_straight_set]
        not_penalized = [t for t in top5 if t not in two_straight_set]
        if penalized:
            penalized_teams = set(penalized)
            needed = 5 - len(not_penalized)
            filler = rest[:needed]
            remaining = rest[needed:]
            order = not_penalized + filler + penalized + remaining

    # Annotate
    for i, team in enumerate(order):
        if team in protected_moved:
            events[i] = "protect"
        elif champ_swapped and team == won_last_year and i == 1:
            events[i] = "champ"
        elif team in penalized_teams:
            events[i] = "penalty"
        elif i < 3:
            events[i] = "top3"

    return order, events


def run_sims(n=10000, won_last_year=None, two_straight=None):
    counts = {team: [0] * 16 for team in TEAMS}
    for _ in range(n):
        result, _ = run_lottery_clean(won_last_year, two_straight)
        for pos, team in enumerate(result):
            counts[team][pos] += 1

    rows = []
    for team in TEAMS:
        row = {"Team": team}
        for pos in range(16):
            row[f"#{pos+1}"] = round(counts[team][pos] / n * 100, 1)
        avg = sum((pos + 1) * counts[team][pos] for pos in range(16)) / n
        row["Avg Pick"] = round(avg, 2)
        rows.append(row)

    return pd.DataFrame(rows)


def balls_html(n, total=3):
    pips = ""
    for i in range(total):
        cls = "pip active" if i < n else "pip"
        pips += f'<span class="{cls}"></span>'
    return f'<span class="balls-pips">{pips}</span>'


# ── Session State ─────────────────────────────────────────────────────────────
if "lottery_result" not in st.session_state:
    st.session_state.lottery_result = None
    st.session_state.lottery_events = {}
if "sim_result" not in st.session_state:
    st.session_state.sim_result = None
if "sim_filters" not in st.session_state:
    st.session_state.sim_filters = None


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Barlow Condensed',sans-serif;font-weight:900;font-size:1.4rem;
         color:#f7941d;text-transform:uppercase;letter-spacing:3px;margin-bottom:4px;">
    ⚙️ Lottery Rules
    </div>
    <div style="height:1px;background:linear-gradient(90deg,#f7941d,transparent);margin-bottom:18px;"></div>
    """, unsafe_allow_html=True)

    won_last_year_opt = st.selectbox(
        "🏆 Won Last Year",
        ["— None —"] + TEAMS,
        help="If this team draws #1, they swap with #2"
    )
    won_last_year = None if won_last_year_opt == "— None —" else won_last_year_opt

    st.markdown("<br>", unsafe_allow_html=True)

    two_straight = st.multiselect(
        "🔁 Two Straight Top 5's",
        TEAMS,
        max_selections=5,
        help="These teams drop to position 6+ if they land in the top 5"
    )

    st.markdown("""
    <div style="height:1px;background:#1e2d45;margin:18px 0 14px;"></div>
    <div style="font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:0.75rem;
         color:#4a6a8a;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">
    Active Rules
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sidebar-rule">
    <strong>Slot 1-3 Protection</strong><br>
    Wizards, Pacers, Nets cannot finish 13–16. Bumped to position 12.
    </div>
    <div class="sidebar-rule" style="{'border-color:#f7941d;' if won_last_year else ''}">
    <strong>Defending Champion</strong><br>
    {"<span style='color:#7adc7a'>"+won_last_year+" cannot draw #1</span>" if won_last_year else "No team selected"}
    </div>
    <div class="sidebar-rule" style="{'border-color:#f7941d;' if two_straight else ''}">
    <strong>Top 5 Penalty</strong><br>
    {"<span style='color:#dcaa50'>" + ", ".join(two_straight) + "</span>" if two_straight else "No teams selected"}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="height:1px;background:#1e2d45;margin:18px 0 14px;"></div>
    <div style="font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:0.75rem;
         color:#4a6a8a;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">
    Lottery Pool (37 Balls)
    </div>
    """, unsafe_allow_html=True)

    pool_rows = []
    for team, b in zip(TEAMS, BALLS):
        pool_rows.append({"Team": team, "Balls": b, "Odds": f"{b/TOTAL_BALLS*100:.1f}%"})
    st.dataframe(pd.DataFrame(pool_rows), hide_index=True, use_container_width=True, height=572)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>NBA Draft <span class="accent">Lottery</span></h1>
    <p>Simulator &nbsp;·&nbsp; 16 Teams &nbsp;·&nbsp; 37 Balls &nbsp;·&nbsp; 10,000 Sims</p>
</div>
""", unsafe_allow_html=True)

# Stats strip
active_rules = sum([won_last_year is not None, len(two_straight) > 0, True])  # protection always on
st.markdown(f"""
<div class="stat-strip">
    <div class="stat-box">
        <div class="label">Total Balls</div>
        <div class="value">37</div>
        <div class="sub">in the lottery drum</div>
    </div>
    <div class="stat-box">
        <div class="label">Teams</div>
        <div class="value">16</div>
        <div class="sub">lottery participants</div>
    </div>
    <div class="stat-box">
        <div class="label">Protected</div>
        <div class="value">3</div>
        <div class="sub">slots 1–3 teams</div>
    </div>
    <div class="stat-box">
        <div class="label">Active Rules</div>
        <div class="value" style="color:{'#f7941d' if active_rules > 1 else '#4a6a8a'}">{active_rules}</div>
        <div class="sub">adjustments enabled</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Single Run ────────────────────────────────────────────────────────────────
left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="section-header">🎲 Single Run</div>', unsafe_allow_html=True)

    if st.button("🔄  Run Lottery", type="primary", use_container_width=True):
        st.session_state.lottery_result, st.session_state.lottery_events = run_lottery_clean(
            won_last_year, two_straight
        )

    if st.session_state.lottery_result is None:
        st.session_state.lottery_result, st.session_state.lottery_events = run_lottery_clean(
            won_last_year, two_straight
        )

    result = st.session_state.lottery_result
    events = st.session_state.lottery_events

    tag_map = {
        "top3":   '<span class="tag tag-top3">Top 3</span>',
        "protect":'<span class="tag tag-protect">⬆ Protected</span>',
        "champ":  '<span class="tag tag-champ">⬇ Champ Rule</span>',
        "penalty":'<span class="tag tag-penalty">⬇ Top 5 Penalty</span>',
    }

    rows_html = ""
    for i, team in enumerate(result):
        pos = i + 1
        ev = events.get(i, "")
        if i < 3:
            num_cls = "pick-num"
        elif i < 10:
            num_cls = "pick-num mid"
        else:
            num_cls = "pick-num late"

        row_cls = ""
        if ev == "top3":     row_cls = "top3"
        elif ev == "protect": row_cls = "top3"
        elif ev == "penalty": row_cls = "penalized"
        elif ev == "champ":   row_cls = "champ"

        b = TEAM_BALLS[team]
        bpips = balls_html(b)
        tag_html = tag_map.get(ev, "")

        rows_html += f"""
        <tr class="{row_cls}">
            <td class="{num_cls}">#{pos}</td>
            <td class="pick-team">{team}</td>
            <td class="pick-balls">{bpips} {b}</td>
            <td class="pick-note">{tag_html}</td>
        </tr>"""

    st.markdown(f"""
    <table class="pick-table">
        <thead>
            <tr style="border-bottom:2px solid #1e3a5f;">
                <th style="color:#4a6a8a;font-size:0.65rem;text-transform:uppercase;
                           letter-spacing:2px;padding:8px 16px;font-family:'Barlow Condensed';">Pick</th>
                <th style="color:#4a6a8a;font-size:0.65rem;text-transform:uppercase;
                           letter-spacing:2px;padding:8px;font-family:'Barlow Condensed';">Team</th>
                <th style="color:#4a6a8a;font-size:0.65rem;text-transform:uppercase;
                           letter-spacing:2px;padding:8px;text-align:center;font-family:'Barlow Condensed';">Balls</th>
                <th style="color:#4a6a8a;font-size:0.65rem;text-transform:uppercase;
                           letter-spacing:2px;padding:8px;text-align:right;font-family:'Barlow Condensed';">Note</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)


with right:
    st.markdown('<div class="section-header">📊 10,000 Simulations</div>', unsafe_allow_html=True)

    current_filters = (won_last_year, tuple(sorted(two_straight)))
    filters_changed = (
        st.session_state.sim_result is not None
        and st.session_state.sim_filters != current_filters
    )

    if filters_changed:
        st.warning("⚠️ Rules changed — re-run simulations for updated odds.")

    if st.button("▶  Run 10,000 Sims", type="primary", use_container_width=True):
        prog = st.progress(0, text="Simulating lottery draws...")
        start = time.time()
        sim_df = run_sims(10000, won_last_year, two_straight)
        st.session_state.sim_result = sim_df
        st.session_state.sim_filters = current_filters
        elapsed = time.time() - start
        prog.empty()
        st.success(f"✅ Done — {10000:,} sims in {elapsed:.1f}s")

    if st.session_state.sim_result is not None and not filters_changed:
        sim_df = st.session_state.sim_result
        pick_cols = [f"#{i+1}" for i in range(16)]

        styled = (
            sim_df.style
            .background_gradient(subset=pick_cols, cmap="YlOrRd", vmin=0, vmax=sim_df[pick_cols].max().max())
            .format({col: "{:.1f}%" for col in pick_cols})
            .format({"Avg Pick": "{:.2f}"})
            .set_properties(**{"font-family": "Barlow Condensed, sans-serif", "font-size": "13px"})
        )

        st.markdown("""
        <div class="odds-note">
        Percentages show how often each team finished at each pick across 10,000 simulations.
        Darker orange = higher probability. Avg Pick is weighted mean draft position.
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(styled, hide_index=True, use_container_width=True, height=580)

    elif st.session_state.sim_result is None:
        st.markdown("""
        <div style="background:#0c1220;border:1px dashed #1e3a5f;border-radius:12px;
             padding:48px 24px;text-align:center;margin-top:8px;">
            <div style="font-size:3rem;margin-bottom:12px;">📊</div>
            <div style="font-family:'Barlow Condensed';font-size:1.2rem;color:#4a6a8a;
                 text-transform:uppercase;letter-spacing:2px;">
                Run simulations to see<br>pick probability odds
            </div>
        </div>
        """, unsafe_allow_html=True)