from __future__ import annotations

import html
from dataclasses import dataclass

import streamlit as st


st.set_page_config(
    page_title="Thanos League · Draft Room 2",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


TEAMS = [f"Team {letter}" for letter in "ABCDEFGHIJKL"]
POSITIONS = ["QB", "RB", "WR", "TE", "K", "DST"]
AUCTION_BUDGET = 200
MINIMUM_SLOT_BID = 1

# Total roster composition supplied for Draft Board 2.
TOTAL_BY_POSITION = {"QB": 2, "RB": 4, "WR": 5, "TE": 1, "K": 2, "DST": 2}
BENCH_BY_POSITION = {"QB": 1, "RB": 2, "WR": 2, "TE": 0, "K": 1, "DST": 1}

POSITION_STYLE = {
    "QB": ("#ff2d2d", "#ffffff"),
    "RB": ("#ff9d00", "#17100a"),
    "WR": ("#ffe600", "#17150a"),
    "TE": ("#29d95b", "#071b0d"),
    "K": ("#ef36c6", "#ffffff"),
    "DST": ("#315bea", "#ffffff"),
}

POSITION_SOFT_STYLE = {
    "QB": ("#f5c8c8", "#642626"),
    "RB": ("#f7dfbe", "#64451d"),
    "WR": ("#f7f2bf", "#5c581c"),
    "TE": ("#c9efd3", "#1d5b2d"),
    "K": ("#f3cae9", "#692358"),
    "DST": ("#c9d2f4", "#263c7a"),
}


@dataclass(frozen=True)
class RosterSlot:
    key: str
    position: str
    position_number: int
    bench: bool


def build_roster_schema() -> list[RosterSlot]:
    """Group rows by position and mark the final slots in each group as bench."""
    slots: list[RosterSlot] = []
    for position in POSITIONS:
        total = TOTAL_BY_POSITION[position]
        starter_count = total - BENCH_BY_POSITION[position]
        for number in range(1, total + 1):
            slots.append(
                RosterSlot(
                    key=f"{position}{number}",
                    position=position,
                    position_number=number,
                    bench=number > starter_count,
                )
            )
    return slots


ROSTER_SCHEMA = build_roster_schema()


def init_state() -> None:
    st.session_state.setdefault("app2_snake_picks", [])
    st.session_state.setdefault("app2_auction_picks", [])


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800;900&display=swap');
        :root { --gold:#f6c65b; --purple:#6f45c7; --ink:#09070d; }
        .stApp {
            background:
              radial-gradient(circle at 86% 5%, rgba(111,69,199,.28), transparent 30rem),
              radial-gradient(circle at 8% 68%, rgba(246,198,91,.09), transparent 26rem),
              linear-gradient(155deg,#08060b 0%,#15111b 55%,#08070a 100%);
            color:#f6f2fb;
        }
        .block-container { max-width:2400px; width:98%; padding:1.4rem 1rem 5rem; }
        header[data-testid="stHeader"] { background:transparent; }
        #MainMenu, footer { visibility:hidden; }
        h1, h2, h3 { font-family:'Bebas Neue',Impact,sans-serif !important; letter-spacing:.045em; }
        p, div, button, input { font-family:'Inter',sans-serif; }
        .eyebrow { color:var(--gold); text-transform:uppercase; letter-spacing:.22em; font-weight:900; font-size:.72rem; }
        .page-title { font-family:'Bebas Neue',Impact,sans-serif; font-size:clamp(3.2rem,7vw,6.6rem); line-height:.88; margin:.25rem 0 .65rem; }
        .page-title span { color:transparent; -webkit-text-stroke:1px var(--gold); }
        .page-copy { color:#aaa3b4; max-width:850px; margin-bottom:1rem; }
        .section-rule { height:1px; background:linear-gradient(90deg,var(--gold),transparent); margin:.45rem 0 1.1rem; }
        div[data-baseweb="tab-list"] { gap:7px; }
        div[data-baseweb="tab-list"] button[role="tab"] {
            min-width:150px; min-height:3.2rem; color:#fff !important; background:#17131d;
            border:1px solid #493b53; border-radius:8px 8px 0 0;
        }
        div[data-baseweb="tab-list"] button[role="tab"] * { color:#fff !important; font-weight:900; letter-spacing:.08em; text-transform:uppercase; }
        div[data-baseweb="tab-list"] button[role="tab"][aria-selected="true"] {
            background:#6f45c7; border-color:var(--gold); box-shadow:inset 0 -3px 0 var(--gold),0 0 18px rgba(111,69,199,.35);
        }
        .draft-status { display:grid; grid-template-columns:1fr auto; gap:1rem; align-items:center; border:1px solid #403548; background:rgba(10,8,12,.8); padding:.8rem 1rem; margin:.9rem 0; }
        .status-kicker { color:var(--gold); font-size:.58rem; font-weight:900; letter-spacing:.16em; text-transform:uppercase; }
        .status-team { font-family:'Bebas Neue'; font-size:1.75rem; letter-spacing:.07em; }
        .status-meta { color:#8f8798; font-size:.66rem; text-transform:uppercase; letter-spacing:.1em; text-align:right; }
        .legend { display:flex; flex-wrap:wrap; gap:7px; margin:.9rem 0; }
        .legend-chip { padding:.38rem .64rem; font-size:.61rem; font-weight:900; letter-spacing:.08em; border-radius:3px; }
        .bench-key { border:1px solid #5b5363; color:#c7c0cd; background:#211c25; }
        .board-label { display:flex; align-items:center; gap:.55rem; color:var(--gold); text-transform:uppercase; letter-spacing:.14em; font-size:.62rem; font-weight:900; margin:1rem 0 .45rem; }
        .board-label:after { content:''; height:1px; flex:1; background:linear-gradient(90deg,#55462b,transparent); }
        .board-swipe { overflow-x:auto; scrollbar-color:#5b4a67 #16121a; padding-bottom:.25rem; }
        .draft-grid {
            display:grid; grid-template-columns:52px repeat(12,minmax(92px,1fr)); min-width:1200px;
            gap:2px; background:#211d25; border:1px solid #39313f; border-radius:8px; overflow:hidden;
        }
        .draft-cell { min-width:0; min-height:3.25rem; padding:.33rem .36rem; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; overflow:hidden; }
        .draft-cell.header { min-height:3.35rem; background:linear-gradient(180deg,#1b1620,#08070a); color:#fff; border-bottom:1px solid #66522d; }
        .team-letter { color:var(--gold); font-family:'Bebas Neue'; font-size:.72rem; letter-spacing:.12em; }
        .team-name { font-size:.59rem; font-weight:900; line-height:1.12; overflow-wrap:anywhere; }
        .row-label { font-family:'Bebas Neue'; font-size:.9rem; font-weight:900; letter-spacing:.04em; position:relative; }
        .slot-type { font-family:'Inter'; font-size:.43rem; font-weight:900; letter-spacing:.08em; opacity:.68; }
        .player-name { font-size:.61rem; font-weight:900; line-height:1.12; overflow-wrap:anywhere; }
        .player-meta { margin-top:.23rem; font-size:.48rem; font-weight:800; opacity:.68; }
        .empty-slot { opacity:.24; font-size:.55rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
        .recent-shell { border:1px solid #39313f; background:rgba(8,7,10,.72); padding:.55rem .7rem; margin-top:1rem; }
        .recent-row { display:grid; grid-template-columns:48px 86px 54px 1fr 66px; gap:.6rem; align-items:center; padding:.43rem .2rem; border-bottom:1px solid #27222c; font-size:.65rem; }
        .recent-row:last-child { border-bottom:0; }
        .recent-number { color:var(--gold); font-family:'Bebas Neue'; font-size:1rem; }
        .recent-pos { font-weight:900; }
        .empty-state { border:1px dashed #49414f; color:#817987; padding:1.25rem; text-align:center; text-transform:uppercase; letter-spacing:.1em; font-size:.65rem; }
        .budget-swipe { overflow-x:auto; margin:.8rem 0 1rem; }
        .budget-grid { display:grid; grid-template-columns:repeat(12,minmax(92px,1fr)); min-width:1120px; gap:4px; }
        .budget-card { border:1px solid #403748; background:linear-gradient(160deg,#1b1620,#0a080c); padding:.62rem .55rem; text-align:center; }
        .budget-team { color:#aaa2b2; font-size:.55rem; font-weight:900; letter-spacing:.08em; text-transform:uppercase; }
        .budget-max { color:var(--gold); font-family:'Bebas Neue'; font-size:1.55rem; line-height:1.05; margin:.2rem 0; }
        .budget-detail { color:#827a8a; font-size:.48rem; font-weight:700; text-transform:uppercase; }
        .stButton > button { border-radius:0; border-color:var(--gold); font-weight:900; text-transform:uppercase; letter-spacing:.08em; }
        @media (max-width:800px) {
            .block-container { width:100%; padding:.9rem .65rem 4rem; }
            .draft-status { grid-template-columns:1fr; }
            .status-meta { text-align:left; }
            .recent-row { grid-template-columns:38px 68px 42px 1fr; }
            .recent-price { display:none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def snake_team_for_pick(pick_index: int) -> str:
    round_number = (pick_index // len(TEAMS)) + 1
    slot = pick_index % len(TEAMS)
    team_index = slot if round_number % 2 else len(TEAMS) - 1 - slot
    return TEAMS[team_index]


def roster_for_team(picks: list[dict[str, object]], team: str) -> dict[str, dict[str, object]]:
    roster: dict[str, dict[str, object]] = {}
    team_picks = [pick for pick in picks if pick["team"] == team]
    for pick in team_picks:
        matching_slots = [slot for slot in ROSTER_SCHEMA if slot.position == pick["position"]]
        open_slot = next((slot for slot in matching_slots if slot.key not in roster), None)
        if open_slot:
            roster[open_slot.key] = pick
    return roster


def board_html(picks: list[dict[str, object]], draft_type: str) -> str:
    rosters = {team: roster_for_team(picks, team) for team in TEAMS}
    cells = ['<div class="draft-cell header"></div>']
    for index, team in enumerate(TEAMS, 1):
        cells.append(
            f'<div class="draft-cell header"><span class="team-letter">{index:02d}</span>'
            f'<span class="team-name">{html.escape(team)}</span></div>'
        )

    for slot in ROSTER_SCHEMA:
        palette = POSITION_SOFT_STYLE if slot.bench else POSITION_STYLE
        background, foreground = palette[slot.position]
        slot_type = "BENCH" if slot.bench else "START"
        cells.append(
            f'<div class="draft-cell row-label" style="background:{background};color:{foreground}">'
            f'{slot.position}<span class="slot-type">{slot_type}</span></div>'
        )
        for team in TEAMS:
            pick = rosters[team].get(slot.key)
            if pick:
                price = f' · ${int(pick["price"])}' if draft_type == "auction" else ""
                content = (
                    f'<span class="player-name">{html.escape(str(pick["player"]))}</span>'
                    f'<span class="player-meta">{slot.position}{price}</span>'
                )
            else:
                reserve = " · $1" if draft_type == "auction" else ""
                content = f'<span class="empty-slot">Open{reserve}</span>'
            cells.append(
                f'<div class="draft-cell" style="background:{background};color:{foreground}">{content}</div>'
            )
    return f'<div class="board-swipe"><div class="draft-grid">{"".join(cells)}</div></div>'


def auction_finances(picks: list[dict[str, object]], team: str) -> tuple[int, int, int]:
    team_picks = [pick for pick in picks if pick["team"] == team]
    spent = sum(int(pick["price"]) for pick in team_picks)
    remaining = AUCTION_BUDGET - spent
    open_slots = len(ROSTER_SCHEMA) - len(team_picks)
    reserved_for_other_slots = max(0, open_slots - 1) * MINIMUM_SLOT_BID
    max_bid = max(0, remaining - reserved_for_other_slots) if open_slots else 0
    return spent, remaining, max_bid


def auction_budget_html(picks: list[dict[str, object]]) -> str:
    cards = []
    for team in TEAMS:
        spent, remaining, max_bid = auction_finances(picks, team)
        cards.append(
            f'<div class="budget-card"><div class="budget-team">{html.escape(team)}</div>'
            f'<div class="budget-max">${max_bid}</div>'
            f'<div class="budget-detail">Max bid · ${remaining} left · ${spent} spent</div></div>'
        )
    return f'<div class="budget-swipe"><div class="budget-grid">{"".join(cards)}</div></div>'


def recent_picks_html(picks: list[dict[str, object]], draft_type: str) -> str:
    if not picks:
        return '<div class="empty-state">No selections yet</div>'
    rows = []
    for pick_number, pick in list(enumerate(picks, 1))[-12:][::-1]:
        price = f'${int(pick["price"])}' if draft_type == "auction" else "—"
        rows.append(
            f'<div class="recent-row"><span class="recent-number">{pick_number:03d}</span>'
            f'<span>{html.escape(str(pick["team"]))}</span>'
            f'<span class="recent-pos">{html.escape(str(pick["position"]))}</span>'
            f'<span>{html.escape(str(pick["player"]))}</span>'
            f'<span class="recent-price">{price}</span></div>'
        )
    return f'<div class="recent-shell">{"".join(rows)}</div>'


def add_pick(state_key: str, player: str, position: str, team: str, price: int = 0) -> bool:
    picks = st.session_state[state_key]
    clean_player = player.strip()
    if not clean_player:
        st.error("Enter a player name.")
        return False
    if any(str(pick["player"]).strip().casefold() == clean_player.casefold() for pick in picks):
        st.error(f"{clean_player} has already been selected in this draft.")
        return False
    position_count = sum(1 for pick in picks if pick["team"] == team and pick["position"] == position)
    if position_count >= TOTAL_BY_POSITION[position]:
        st.error(f"{team} already has all {TOTAL_BY_POSITION[position]} {position} slots filled.")
        return False
    if sum(1 for pick in picks if pick["team"] == team) >= len(ROSTER_SCHEMA):
        st.error(f"{team}'s roster is full.")
        return False
    if state_key == "app2_auction_picks":
        _, _, max_bid = auction_finances(picks, team)
        if price < MINIMUM_SLOT_BID:
            st.error("Auction players must cost at least $1.")
            return False
        if price > max_bid:
            st.error(f"{team}'s current max bid is ${max_bid}.")
            return False
    picks.append({"player": clean_player, "position": position, "team": team, "price": price})
    return True


def render_controls(draft_type: str) -> None:
    state_key = f"app2_{draft_type}_picks"
    picks = st.session_state[state_key]
    is_snake = draft_type == "snake"
    on_clock = snake_team_for_pick(len(picks)) if is_snake and len(picks) < len(TEAMS) * len(ROSTER_SCHEMA) else "Draft Complete"
    round_number = (len(picks) // len(TEAMS)) + 1

    status_meta = (
        f"Round {round_number} · Pick {len(picks) + 1} of {len(TEAMS) * len(ROSTER_SCHEMA)}"
        if is_snake and on_clock != "Draft Complete"
        else f"{len(picks)} players purchased" if not is_snake else "All roster slots filled"
    )
    status_title = on_clock if is_snake else "Open Bidding"
    status_kicker = "On the clock" if is_snake else "Auction room"
    st.markdown(
        f'<div class="draft-status"><div><div class="status-kicker">{status_kicker}</div>'
        f'<div class="status-team">{html.escape(status_title)}</div></div>'
        f'<div class="status-meta">{html.escape(status_meta)}</div></div>',
        unsafe_allow_html=True,
    )

    with st.form(f"{draft_type}_entry", clear_on_submit=True):
        if is_snake:
            player_col, position_col, submit_col = st.columns([2.4, 1, 1])
            team = on_clock
            with player_col:
                player = st.text_input("Player", placeholder="Enter drafted player")
            with position_col:
                position = st.selectbox("Position", POSITIONS)
            price = 0
            with submit_col:
                st.write("")
                submitted = st.form_submit_button("Draft Player", type="primary", use_container_width=True)
        else:
            player_col, position_col, team_col, price_col, submit_col = st.columns([2.1, .8, 1.1, .7, 1])
            with player_col:
                player = st.text_input("Player", placeholder="Enter purchased player")
            with position_col:
                position = st.selectbox("Position", POSITIONS)
            with team_col:
                team = st.selectbox("Team", TEAMS)
            with price_col:
                price = st.number_input("Price", min_value=0, max_value=999, value=1, step=1)
            with submit_col:
                st.write("")
                submitted = st.form_submit_button("Add Player", type="primary", use_container_width=True)

        if submitted and team != "Draft Complete" and add_pick(state_key, player, position, team, int(price)):
            st.rerun()

    action_left, action_middle, action_right = st.columns([1, 1, 5])
    with action_left:
        if st.button("Undo Last", key=f"undo_{draft_type}", disabled=not picks, use_container_width=True):
            picks.pop()
            st.rerun()
    with action_middle:
        if st.button("Clear Board", key=f"clear_{draft_type}", disabled=not picks, use_container_width=True):
            picks.clear()
            st.rerun()

    legend = "".join(
        f'<span class="legend-chip" style="background:{background};color:{foreground}">{position}</span>'
        for position, (background, foreground) in POSITION_STYLE.items()
    )
    st.markdown(f'<div class="legend">{legend}<span class="legend-chip bench-key">LIGHT = BENCH</span></div>', unsafe_allow_html=True)
    if not is_snake:
        st.markdown('<div class="board-label">Auction budgets · $1 reserved per open slot</div>', unsafe_allow_html=True)
        st.markdown(auction_budget_html(picks), unsafe_allow_html=True)
    st.markdown('<div class="board-label">Roster by position</div>', unsafe_allow_html=True)
    st.markdown(board_html(picks, draft_type), unsafe_allow_html=True)
    st.markdown('<div class="board-label">Recent selections</div>', unsafe_allow_html=True)
    st.markdown(recent_picks_html(picks, draft_type), unsafe_allow_html=True)


def render_app() -> None:
    st.markdown('<div class="eyebrow">Thanos League · Draft Room 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">SECOND <span>DRAFT BOARD</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-copy">Two independent 12-team drafts. Each roster has 16 total slots, '
        'and bench slots retain their position color in a lighter shade.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)

    snake_tab, auction_tab = st.tabs(["Snake", "Auction"])
    with snake_tab:
        render_controls("snake")
    with auction_tab:
        render_controls("auction")


init_state()
inject_css()
render_app()
