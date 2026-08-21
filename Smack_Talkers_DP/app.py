from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from history_metrics import (
    POSITION_ORDER,
    all_play_summary,
    attach_draft_outcomes,
    combined_draft_role_summary,
    coverage_summary,
    drafted_player_outcomes,
    draft_role_summary,
    draft_strategy_team_seasons,
    fantasy_weeks,
    lineup_week_metrics,
    load_history_data,
    owner_lineup_summary,
    perfect_start_counterfactual,
    prepare_draft_board,
    roster_decay,
    season_h2h_records,
    STARTER_SLOT_ORDER,
    starter_slot_rankings,
)


APP_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = APP_DIR / "data" / "processed"
AUCTION_VALUES_PATH = PROCESSED_DIR / "smack_talkers_2026_auction_values.csv"
AUCTION_BUDGET = 2400
TEAM_AUCTION_BUDGET = 200
DRAFT_ROSTER_SIZE = 16
DRAFT_POSITION_ORDER = ["QB", "RB", "WR", "TE", "K", "DST"]
DRAFT_POSITION_LIMITS = {"QB": 2, "RB": 4, "WR_FLEX": 5, "TE_STARTER": 1, "K": 2, "DST": 2}
SHARED_2026_OWNERS = ["Carson", "Woody", "McCade", "Colton", "ToddB", "Dallin", "Easton", "Reyes", "Shane", "Tyler"]
DRAFT_OWNERS = {
    "Auction": SHARED_2026_OWNERS + ["Kyle", "Kristin"],
    "Snake": SHARED_2026_OWNERS + ["ToddA", "Tyson"],
}

COLORS = {
    "QB": "#C05E85",
    "RB": "#CC8C4A",
    "WR": "#46A2CA",
    "TE": "#73C3A6",
    "K": "#E0B44C",
    "DST": "#8A7CC7",
    "Unknown": "#6B7280",
    "Starter": "#6FB1FC",
    "Bench": "#CC8C4A",
    "IR": "#6B7280",
}

st.set_page_config(page_title="Smack Talkers | League Lab", page_icon="🏈", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@300;400;500;600;700;800&display=swap');
:root {
  --canvas:#0D1117; --panel:#1C1F26; --panel2:#151A22; --blue:#3E92CC;
  --blue2:#6FB1FC; --ink:#F0F3F5; --muted:#9DA9B7; --line:rgba(111,177,252,.22);
}
html, body, [class*="css"], .stApp { font-family:'Barlow Semi Condensed',sans-serif; }
.stApp { background:radial-gradient(circle at 82% -12%,#173A58 0,#0D1117 34%,#090C11 100%); color:var(--ink); }
.block-container { max-width:1420px; padding-top:1.35rem; padding-bottom:4rem; }
[data-testid="stSidebar"] { background:#10151C; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:#E8EEF5; }
h1,h2,h3,h4 { color:#C3DDFD !important; font-weight:700 !important; letter-spacing:.015em; }
.hero { position:relative; overflow:hidden; border:1px solid rgba(62,146,204,.75); border-radius:18px;
  padding:2.15rem 2.25rem 1.9rem; margin-bottom:1.1rem; background:linear-gradient(125deg,rgba(28,31,38,.98),rgba(18,41,62,.94));
  box-shadow:0 24px 75px rgba(0,0,0,.30); }
.hero:after { content:""; position:absolute; width:320px; height:320px; right:-95px; top:-190px; border-radius:50%;
  border:42px solid rgba(111,177,252,.08); }
.eyebrow { color:#6FB1FC; text-transform:uppercase; letter-spacing:.19em; font-weight:700; font-size:.78rem; }
.hero h1 { color:#F6FAFF !important; font-size:clamp(2.5rem,5vw,4.6rem); line-height:.94; margin:.35rem 0 .55rem; }
.hero p { color:#B6C1CD; max-width:760px; font-size:1.07rem; margin:0; }
.coverage-chip { display:inline-block; margin-top:1rem; padding:.35rem .7rem; border-radius:999px; color:#C3DDFD;
  background:rgba(62,146,204,.12); border:1px solid rgba(111,177,252,.28); font-size:.82rem; font-weight:600; }
.section-kicker { color:#6FB1FC; text-transform:uppercase; letter-spacing:.16em; font-weight:700; font-size:.72rem; margin-bottom:-.35rem; }
.insight { background:linear-gradient(135deg,#171D25,#1C2733); border:1px solid var(--line); border-left:4px solid #3E92CC;
  padding:1rem 1.1rem; border-radius:10px; color:#C8D2DD; min-height:96px; }
.insight b { color:#F1F6FB; font-size:1.05rem; }
.warning-card { background:rgba(224,180,76,.08); border:1px solid rgba(224,180,76,.35); color:#E9D79D;
  padding:.8rem 1rem; border-radius:10px; margin:.45rem 0 1rem; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#1C1F26,#151A22); border:1px solid var(--line); border-radius:12px; padding:1rem 1.1rem; }
[data-testid="stMetricLabel"] { color:#9DA9B7; text-transform:uppercase; letter-spacing:.08em; font-size:.74rem; }
[data-testid="stMetricValue"] { color:#F0F6FC; font-weight:700; }
[data-testid="stMetricDelta"] { font-weight:600; }
[data-testid="stTabs"] button { color:#AAB6C3; font-weight:600; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#DCEEFF; }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:10px; overflow:hidden; }
[data-testid="stDataEditor"] { border:1px solid rgba(111,177,252,.38); border-radius:12px; overflow:hidden;
  box-shadow:0 16px 42px rgba(0,0,0,.18); }
div[data-testid="stExpander"] { background:#151A22; border:1px solid var(--line); border-radius:10px; }
.stSelectbox label, .stMultiSelect label { color:#AAB6C3 !important; font-weight:600; }
.auction-hero { position:relative; overflow:hidden; padding:1.35rem 1.5rem; margin:.2rem 0 1rem;
  border:1px solid rgba(204,140,74,.65); border-radius:16px;
  background:linear-gradient(125deg,rgba(39,29,23,.98),rgba(26,43,58,.96)); box-shadow:0 18px 55px rgba(0,0,0,.24); }
.auction-hero h2 { color:#FFF4E8 !important; font-size:2rem; margin:.15rem 0 .35rem; }
.auction-hero p { color:#C6D0DA; margin:0; max-width:900px; }
.auction-eyebrow { color:#F0B978; text-transform:uppercase; letter-spacing:.18em; font-size:.72rem; font-weight:800; }
.auction-chip { display:inline-block; margin:.75rem .45rem 0 0; padding:.28rem .62rem; border-radius:999px;
  background:rgba(204,140,74,.13); border:1px solid rgba(240,185,120,.28); color:#F3D0A7; font-size:.78rem; font-weight:700; }
footer { visibility:hidden; }
@media (max-width:700px) { .hero { padding:1.5rem 1.25rem; } .block-container { padding-left:.8rem; padding-right:.8rem; } }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Building the league-history model…")
def get_data() -> dict[str, pd.DataFrame]:
    history = load_history_data(PROCESSED_DIR)
    result_columns = history["scores"][["season", "league_id", "team_id", "week", "result", "opponent_score"]].drop_duplicates()
    history["scoring_history"] = history["lineup_scores"].merge(
        result_columns,
        on=["season", "league_id", "team_id", "week"],
        how="left",
        validate="one_to_one",
    )
    history["draft_board"] = prepare_draft_board(history["drafts_enriched"], history["owners"])
    history["draft_strategy"] = draft_strategy_team_seasons(history["draft_board"])
    history["all_lineup_weeks"] = lineup_week_metrics(history["lineups"])
    history["draft_outcomes"] = attach_draft_outcomes(
        history["draft_strategy"],
        history["standings"],
        history["scoring_history"],
        history["all_lineup_weeks"],
        history["lineups"],
        history["team_map"],
    )
    history["drafted_player_outcomes"] = drafted_player_outcomes(
        history["draft_board"], history["lineups"], history["team_map"]
    )
    return history


@st.cache_data(show_spinner=False)
def get_auction_values() -> pd.DataFrame:
    values = pd.read_csv(AUCTION_VALUES_PATH)
    values["fantasypros_injury_status"] = values["fantasypros_injury_status"].fillna("")
    values["auction_value"] = pd.to_numeric(values["auction_value"], errors="coerce").fillna(1).astype(int)
    values["fantasypros_roster_rank"] = pd.to_numeric(values["fantasypros_roster_rank"], errors="coerce")
    if "total_starting_vorp" not in values.columns:
        values["total_starting_vorp"] = np.nan
        for position in DRAFT_POSITION_ORDER:
            position_mask = values["position"].eq(position)
            starter_mask = position_mask & values["model_position_rank"].le(12)
            starter_vorps = values.loc[starter_mask, "starter_vorp"]
            values.loc[position_mask, "total_starting_vorp"] = (
                len(starter_vorps) * values.loc[position_mask, "starter_vorp"]
                - starter_vorps.sum()
            )
    projected_starter = values["projected_starter_pool"].astype(str).str.lower().eq("true")
    values.loc[~projected_starter, "total_starting_vorp"] = np.nan
    return values


@st.cache_data(show_spinner=False)
def get_position_confidence(drafted_outcomes: pd.DataFrame) -> pd.DataFrame:
    """Estimate how reliably preseason position order predicted realized starter contribution."""
    columns = ["position", "position_confidence", "confidence_sample", "confidence_seasons"]
    required = {"season", "draft_type", "position", "espn_overall_rank", "starter_points_per_observed_week"}
    if drafted_outcomes.empty or not required.issubset(drafted_outcomes.columns):
        return pd.DataFrame(columns=columns)

    confidence = drafted_outcomes.loc[
        drafted_outcomes["position"].isin(DRAFT_POSITION_ORDER)
        & drafted_outcomes["espn_overall_rank"].notna()
        & drafted_outcomes["starter_points_per_observed_week"].notna()
    ].copy()
    if confidence.empty:
        return pd.DataFrame(columns=columns)

    grouping = ["season", "draft_type", "position"]
    confidence["preseason_signal"] = confidence.groupby(grouping)["espn_overall_rank"].rank(
        pct=True, ascending=False
    )
    confidence["realized_signal"] = confidence.groupby(grouping)["starter_points_per_observed_week"].rank(
        pct=True, ascending=True
    )
    rows: list[dict[str, object]] = []
    for position, position_history in confidence.groupby("position"):
        correlation = position_history["preseason_signal"].corr(position_history["realized_signal"])
        rows.append(
            {
                "position": position,
                "position_confidence": float(np.clip(correlation, 0, 1)) if pd.notna(correlation) else 0.0,
                "confidence_sample": int(len(position_history)),
                "confidence_seasons": int(position_history["season"].nunique()),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def allocate_live_auction_values(frame: pd.DataFrame, budget: int) -> pd.Series:
    """Allocate an integer remaining budget with a $1 floor using baseline auction value as weight."""
    if frame.empty:
        return pd.Series(dtype="int64", index=frame.index)
    player_count = len(frame)
    if budget < player_count:
        return pd.Series(1, index=frame.index, dtype="int64")
    excess_budget = int(budget - player_count)
    weights = (pd.to_numeric(frame["auction_value"], errors="coerce").fillna(1) - 1).clip(lower=0)
    if weights.sum() <= 0:
        weights = pd.Series(1.0, index=frame.index)
    exact = 1 + weights / weights.sum() * excess_budget
    allocated = np.floor(exact).astype(int)
    dollars_left = int(budget - allocated.sum())
    if dollars_left > 0:
        fractional = (exact - allocated).sort_values(ascending=False, kind="stable")
        allocated.loc[fractional.index[:dollars_left]] += 1
    return allocated.astype(int)


def reset_live_draft(draft_format: str) -> None:
    ledgers = dict(st.session_state.get("live_draft_ledgers", {"Auction": [], "Snake": []}))
    ledgers[draft_format] = []
    st.session_state["live_draft_ledgers"] = ledgers
    st.session_state["live_draft_revision"] = st.session_state.get("live_draft_revision", 0) + 1


def undo_live_pick(draft_format: str) -> None:
    ledgers = dict(st.session_state.get("live_draft_ledgers", {"Auction": [], "Snake": []}))
    records = list(ledgers.get(draft_format, []))
    if records:
        records.pop()
        ledgers[draft_format] = records
        st.session_state["live_draft_ledgers"] = ledgers
        st.session_state["live_draft_revision"] = st.session_state.get("live_draft_revision", 0) + 1


def team_draft_counts(
    records: list[dict[str, object]], team: str, position_lookup: dict[str, str]
) -> dict[str, int]:
    counts = {position: 0 for position in DRAFT_POSITION_ORDER}
    for record in records:
        if str(record.get("drafting_team", "")) != team:
            continue
        position = position_lookup.get(str(record.get("player", "")), "")
        if position in counts:
            counts[position] += 1
    return counts


def roster_limit_error(counts: dict[str, int], new_position: str) -> str | None:
    """Return a message when a pick cannot fit the league's 16 active draft slots."""
    if new_position not in DRAFT_POSITION_ORDER:
        return f"{new_position or 'Unknown'} is not a supported draft position."
    if sum(counts.values()) >= DRAFT_ROSTER_SIZE:
        return "This owner already has a full 16-player roster."

    proposed = dict(counts)
    proposed[new_position] += 1
    fixed_limits = {
        "QB": DRAFT_POSITION_LIMITS["QB"],
        "RB": DRAFT_POSITION_LIMITS["RB"],
        "K": DRAFT_POSITION_LIMITS["K"],
        "DST": DRAFT_POSITION_LIMITS["DST"],
    }
    if new_position in fixed_limits and proposed[new_position] > fixed_limits[new_position]:
        return f"This owner already filled all {fixed_limits[new_position]} {new_position} slots."

    used_wr_flex = proposed["WR"] + max(proposed["TE"] - DRAFT_POSITION_LIMITS["TE_STARTER"], 0)
    if used_wr_flex > DRAFT_POSITION_LIMITS["WR_FLEX"]:
        return "The five WR/TE flex slots are full. Extra tight ends use a WR/TE flex slot."
    return None


def team_auction_status(records: list[dict[str, object]], team: str) -> tuple[int, int, int, int]:
    team_records = [record for record in records if str(record.get("drafting_team", "")) == team]
    spent = int(sum(int(record.get("price", 0) or 0) for record in team_records))
    rostered = len(team_records)
    open_slots = max(DRAFT_ROSTER_SIZE - rostered, 0)
    budget_left = TEAM_AUCTION_BUDGET - spent
    max_bid = max(0, budget_left - max(open_slots - 1, 0))
    return spent, budget_left, open_slots, max_bid


def polish(fig: go.Figure, height: int = 430, legend: str = "h") -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=18, r=18, t=56, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(21,26,34,.55)",
        font=dict(family="Barlow Semi Condensed", color="#D8E0E8", size=14),
        title_font=dict(size=20, color="#C3DDFD"),
        legend=dict(orientation=legend, yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="#111820", font_size=14, font_family="Barlow Semi Condensed"),
    )
    fig.update_xaxes(gridcolor="rgba(111,177,252,.10)", zerolinecolor="rgba(111,177,252,.18)")
    fig.update_yaxes(gridcolor="rgba(111,177,252,.10)", zerolinecolor="rgba(111,177,252,.18)")
    return fig


def render_plot(fig: go.Figure, key: str) -> None:
    st.plotly_chart(polish(fig), width="stretch", config={"displaylogo": False}, key=key)


def add_linear_trend_with_ci(fig: go.Figure, frame: pd.DataFrame, x_column: str, y_column: str) -> None:
    """Add an OLS mean trend and approximate 95% confidence band."""
    clean = frame[[x_column, y_column]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(clean) < 4 or clean[x_column].nunique() < 2:
        return
    x = clean[x_column].to_numpy(dtype=float)
    y = clean[y_column].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    grid = np.linspace(x.min(), x.max(), 120)
    fitted = intercept + slope * grid
    residuals = y - (intercept + slope * x)
    residual_se = np.sqrt(np.sum(residuals**2) / max(len(x) - 2, 1))
    spread = np.sum((x - x.mean()) ** 2)
    ci = 1.96 * residual_se * np.sqrt(1 / len(x) + ((grid - x.mean()) ** 2 / spread if spread else 0))
    fig.add_trace(go.Scatter(x=grid, y=fitted - ci, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(
        go.Scatter(
            x=grid,
            y=fitted + ci,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(111,177,252,.16)",
            name="95% confidence band",
            hoverinfo="skip",
        )
    )
    fig.add_trace(go.Scatter(x=grid, y=fitted, mode="lines", line=dict(color="#C3DDFD", width=3), name="Linear trend"))


def pct(value: float) -> str:
    return "—" if pd.isna(value) else f"{value:.1%}"


def ordinal(value: object) -> str:
    if pd.isna(value):
        return "—"
    number = int(value)
    suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def finish_label(value: object) -> str:
    if pd.isna(value):
        return "Result unavailable"
    rank = int(value)
    return {1: "Champion", 2: "Runner-up", 3: "Third place"}.get(rank, f"{ordinal(rank)} place")


def section_title(kicker: str, title: str, text: str | None = None) -> None:
    st.markdown(f'<div class="section-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f"## {title}")
    if text:
        st.caption(text)


data = get_data()
auction_values = get_auction_values()
position_confidence = get_position_confidence(data["drafted_player_outcomes"])
auction_values = auction_values.merge(position_confidence, on="position", how="left", validate="many_to_one")
auction_values["confidence_adjusted_total_starting_vorp"] = (
    auction_values["total_starting_vorp"] * auction_values["position_confidence"]
)
team_map = data["team_map"].copy()
available_seasons = sorted(team_map["season"].unique().tolist())

with st.sidebar:
    st.markdown("### LEAGUE LAB")
    st.caption("Smack Talkers · 31st season prep")
    season_type = st.radio("Season type", ["Both", "Snake", "Auction"], horizontal=True)
    year_range = st.slider(
        "Years",
        min_value=min(available_seasons),
        max_value=max(available_seasons),
        value=(min(available_seasons), max(available_seasons)),
        step=1,
    )
    st.markdown("---")
    st.markdown("#### How to read this")
    st.caption("Scoring and lineup metrics use every season week: 17 through 2020 and 18 from 2021 onward. Actual win rate uses recorded H2H matchups.")
    st.markdown("#### Position key")
    for position in ["QB", "RB", "WR", "TE", "K", "DST"]:
        st.markdown(
            f'<span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:{COLORS[position]};margin-right:7px"></span>{position}',
            unsafe_allow_html=True,
        )


def selected(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "season" not in frame:
        return frame.copy()
    mask = frame["season"].between(year_range[0], year_range[1])
    if season_type != "Both" and "draft_type" in frame:
        mask &= frame["draft_type"].eq(season_type.casefold())
    return frame.loc[mask].copy()


lineups = selected(data["lineups"])
scores = selected(data["scores"])
scoring_history = selected(data["scoring_history"])
matchups = selected(data["matchups"])
standings = selected(data["standings"])
lineup_weeks = selected(data["all_lineup_weeks"])
lineup_summary = owner_lineup_summary(lineup_weeks)
slot_rankings = starter_slot_rankings(lineups)
all_play_weekly, all_play = all_play_summary(scoring_history) if not scoring_history.empty else (pd.DataFrame(), pd.DataFrame())
counterfactual = perfect_start_counterfactual(lineup_weeks, scores)

owner_entry_counts = (
    standings[["season", "league_id", "team_id", "owner"]]
    .dropna(subset=["owner"])
    .drop_duplicates()
    .groupby("owner")
    .size()
    .astype(int)
    .to_dict()
)


def owner_sample_label(owner: object) -> str:
    """Add the number of filtered league-season entries to an owner name."""
    name = str(owner)
    return f"{name} ({owner_entry_counts.get(name, 0)})"

score_team_weeks = len(scores)
lineup_team_weeks = len(lineup_weeks)
team_seasons = standings[["season", "league_id", "team_id"]].drop_duplicates() if not standings.empty else pd.DataFrame()
expected_lineup_pages = int(team_seasons["season"].map(fantasy_weeks).sum()) if not team_seasons.empty else 0
coverage_rate = lineup_team_weeks / expected_lineup_pages if expected_lineup_pages else 0
hero_scope = f"{season_type} / {year_range[0]}–{year_range[1]}"
st.markdown(
    f"""
<div class="hero">
  <div class="eyebrow">League history · decision science</div>
  <h1>SMACK TALKERS<br>LEAGUE LAB</h1>
  <p>What creates points, where managers give them back, and which apparent results are skill versus schedule.</p>
  <span class="coverage-chip">{hero_scope} · lineup coverage {coverage_rate:.0%}</span>
</div>
""",
    unsafe_allow_html=True,
)

if coverage_rate < 0.95:
    st.markdown(
        f'<div class="warning-card"><b>Coverage-aware analysis:</b> detailed lineups are available for {lineup_team_weeks:,} of {expected_lineup_pages:,} expected team-week pages. Separately, Yahoo exposes {score_team_weeks:,} matchup-score rows. Lineup rankings below are labeled by observed team-weeks and should not be treated as full-season standings yet.</div>',
        unsafe_allow_html=True,
    )

m1, m2, m3, m4 = st.columns(4)
m1.metric("Owners represented", standings["owner"].nunique() if not standings.empty else 0)
m2.metric("Matchups observed", len(matchups))
m3.metric("Lineup decisions", f"{lineup_team_weeks:,}", f"{coverage_rate:.0%} coverage")
m4.metric("Player-week rows", f"{len(lineups):,}")

tab_live_auction, tab_pulse, tab_owner_history, tab_position, tab_draft_room, tab_decisions, tab_draft, tab_coverage = st.tabs(
    ["2026 Draft Board", "League pulse", "Owner history", "Position build", "Draft room", "Lineup decisions", "Drafted vs acquired", "Data coverage"]
)

with tab_live_auction:
    if "live_draft_ledgers" not in st.session_state:
        legacy_players = list(st.session_state.get("live_auction_drafted", []))
        legacy_prices = dict(st.session_state.get("live_auction_prices", {}))
        legacy_records = [
            {
                "pick": index + 1,
                "player": player,
                "drafting_team": "Unassigned",
                "price": int(legacy_prices.get(player, 1)),
            }
            for index, player in enumerate(legacy_players)
        ]
        st.session_state["live_draft_ledgers"] = {"Auction": legacy_records, "Snake": []}
    if "live_draft_revision" not in st.session_state:
        st.session_state["live_draft_revision"] = 0

    mode_col, undo_col, reset_col = st.columns([0.62, 0.19, 0.19], vertical_alignment="bottom")
    with mode_col:
        draft_format = st.segmented_control(
            "Draft format",
            ["Auction", "Snake"],
            default="Auction",
            selection_mode="single",
            key="live_draft_format",
        ) or "Auction"
    ledgers = st.session_state["live_draft_ledgers"]
    records = list(ledgers.get(draft_format, []))
    with undo_col:
        st.button(
            "↶ Undo last pick",
            width="stretch",
            disabled=not records,
            on_click=undo_live_pick,
            args=(draft_format,),
            key=f"undo_live_pick_{draft_format}",
        )
    with reset_col:
        with st.popover("⚠ Reset board", width="stretch"):
            st.warning(f"This will erase every recorded {draft_format.lower()} pick. It cannot be undone.")
            st.button(
                f"Confirm reset {draft_format}",
                type="primary",
                width="stretch",
                on_click=reset_live_draft,
                args=(draft_format,),
                key=f"confirm_reset_{draft_format}",
            )

    format_description = (
        "Enter the winning bid and the remaining $2,400 market will reprice immediately."
        if draft_format == "Auction"
        else "Enter each selection as it happens; available overall and position ranks compress immediately."
    )
    st.markdown(
        f"""
<div class="auction-hero">
  <div class="auction-eyebrow">Live {draft_format.lower()} command center</div>
  <h2>2026 {draft_format.upper()} BOARD</h2>
  <p>{format_description}</p>
  <span class="auction-chip">192-player pool</span><span class="auction-chip">12 drafting teams</span><span class="auction-chip">separate {draft_format.lower()} ledger</span>
</div>
""",
        unsafe_allow_html=True,
    )

    drafted_players = {str(record["player"]) for record in records}
    spent = int(sum(int(record.get("price", 0) or 0) for record in records)) if draft_format == "Auction" else 0
    remaining_budget = AUCTION_BUDGET - spent
    remaining_players = len(auction_values) - len(drafted_players)
    available = auction_values.loc[~auction_values["player"].isin(drafted_players)].copy()
    position_lookup = auction_values.set_index("player")["position"].astype(str).to_dict()
    legal_budget = remaining_budget >= remaining_players

    if draft_format == "Auction":
        available["live_value"] = allocate_live_auction_values(
            available, max(remaining_budget, remaining_players)
        )
        rank_sort = ["live_value", "composite_value_score", "auction_rank"]
        rank_ascending = [False, False, True]
    else:
        available["live_value"] = available["auction_value"]
        rank_sort = ["auction_rank", "composite_value_score"]
        rank_ascending = [True, False]
    ordered_available = available.sort_values(rank_sort, ascending=rank_ascending, kind="stable")
    available["available_rank"] = pd.Series(
        np.arange(1, len(ordered_available) + 1), index=ordered_available.index
    )
    position_ordered = available.sort_values(
        ["position", "model_position_rank"], ascending=[True, True], kind="stable"
    )
    available["available_position_rank"] = position_ordered.groupby("position").cumcount().add(1)

    revision = st.session_state["live_draft_revision"]
    with st.container(border=True):
        st.markdown("### Enter the next pick")
        entry_player_col, entry_team_col, entry_price_col, entry_confirm_col = st.columns(
            [1.75, 1.15, 0.72, 0.88], vertical_alignment="bottom"
        )
        with entry_player_col:
            selected_player = st.selectbox(
                "Player",
                ordered_available["player"].tolist(),
                index=None,
                placeholder="Start typing a player name…",
                key=f"live_pick_player_{draft_format}_{revision}",
            )
        with entry_team_col:
            drafting_team = st.selectbox(
                "Drafting team",
                DRAFT_OWNERS[draft_format],
                index=None,
                placeholder="Choose team…",
                format_func=owner_sample_label,
                key=f"live_pick_team_{draft_format}_{revision}",
            )
        suggested_value = (
            int(available.set_index("player").at[selected_player, "live_value"])
            if selected_player in set(available["player"])
            else 1
        )
        selected_counts = (
            team_draft_counts(records, drafting_team, position_lookup)
            if drafting_team
            else {position: 0 for position in DRAFT_POSITION_ORDER}
        )
        selected_position = position_lookup.get(str(selected_player), "") if selected_player else ""
        position_error = roster_limit_error(selected_counts, selected_position) if selected_player and drafting_team else None
        if draft_format == "Auction":
            _, selected_budget_left, selected_open_slots, selected_max_bid = (
                team_auction_status(records, drafting_team) if drafting_team else (0, TEAM_AUCTION_BUDGET, DRAFT_ROSTER_SIZE, 185)
            )
            legal_bid_ceiling = max(selected_max_bid, 1)
            with entry_price_col:
                winning_bid = st.number_input(
                    f"Winning bid · max ${selected_max_bid}",
                    min_value=1,
                    max_value=legal_bid_ceiling,
                    value=min(suggested_value, legal_bid_ceiling),
                    step=1,
                    disabled=bool(drafting_team and selected_max_bid < 1),
                    help=(
                        f"${selected_budget_left} left with {selected_open_slots} open roster slots. "
                        "The other open slots retain a $1 reserve."
                        if drafting_team
                        else "Choose an owner to calculate the legal maximum bid."
                    ),
                    key=f"live_pick_price_{draft_format}_{revision}_{drafting_team or 'none'}_{selected_player or 'none'}",
                )
        else:
            winning_bid = None
            with entry_price_col:
                st.metric("Next pick", len(records) + 1)
        with entry_confirm_col:
            confirm_pick = st.button(
                "Confirm pick",
                type="primary",
                width="stretch",
                key=f"confirm_live_pick_{draft_format}_{revision}",
            )
        if confirm_pick:
            if not selected_player or not drafting_team:
                st.error("Choose both a player and a drafting team before confirming the pick.")
            elif position_error:
                st.error(position_error)
            elif draft_format == "Auction" and int(winning_bid) > selected_max_bid:
                st.error(
                    f"{drafting_team}'s maximum legal bid is ${selected_max_bid:,}. "
                    "That preserves $1 for every remaining roster spot."
                )
            else:
                updated_ledgers = dict(st.session_state["live_draft_ledgers"])
                updated_records = list(updated_ledgers.get(draft_format, []))
                updated_records.append(
                    {
                        "pick": len(updated_records) + 1,
                        "player": selected_player,
                        "drafting_team": drafting_team,
                        "price": int(winning_bid) if draft_format == "Auction" else None,
                    }
                )
                updated_ledgers[draft_format] = updated_records
                st.session_state["live_draft_ledgers"] = updated_ledgers
                st.session_state["live_draft_revision"] += 1
                st.rerun()

    if draft_format == "Auction":
        available_model_total = int(available["auction_value"].sum())
        pressure = remaining_budget / available_model_total if available_model_total else 0
        top_live = int(available["live_value"].max()) if not available.empty else 0
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Budget left", f"${remaining_budget:,}", f"${spent:,} spent")
        k2.metric("Players left", remaining_players, f"{len(records)} drafted")
        k3.metric("Avg $ / player", f"${remaining_budget / remaining_players:,.1f}" if remaining_players else "$0")
        k4.metric("Top live value", f"${top_live}")
        k5.metric(
            "Market pressure",
            f"{pressure:.0%}",
            "values rise" if pressure > 1.01 else "values fall" if pressure < 0.99 else "on model",
        )
        if not legal_budget:
            st.error(
                f"The bids leave ${remaining_budget:,} for {remaining_players} players—${remaining_players - remaining_budget:,} below the required $1-per-player reserve."
            )
    else:
        next_player = ordered_available.iloc[0]["player"] if not ordered_available.empty else "Draft complete"
        next_position = ordered_available.iloc[0]["position"] if not ordered_available.empty else ""
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Picks entered", len(records))
        k2.metric("Players left", remaining_players)
        k3.metric("Next overall", next_player, next_position)
        k4.metric("Next pick number", len(records) + 1 if remaining_players else "—")

    rankings_tab, team_board_tab = st.tabs(["Player Rankings", "Team Draft Board"])

    confidence_summary = " · ".join(
        f"{row.position} {row.position_confidence:.0%} (n={int(row.confidence_sample)})"
        for row in position_confidence.sort_values(
            "position", key=lambda values: values.map({position: index for index, position in enumerate(DRAFT_POSITION_ORDER)})
        ).itertuples(index=False)
    )
    rankings_tab.caption(
        "Historical position confidence — correlation between 2023–2025 preseason order and realized starter points: "
        + confidence_summary
    )

    filter_col, sort_col = rankings_tab.columns([1.4, 1])
    with filter_col:
        board_positions = st.multiselect(
            "Positions shown",
            ["QB", "RB", "WR", "TE", "K", "DST"],
            default=["QB", "RB", "WR", "TE", "K", "DST"],
            key=f"live_board_positions_{draft_format}",
        )
    sort_choices = (
        ["Live value", "Available rank", "Position rank", "Projected points", "Starter VORP", "Total Starting VORP", "Confidence-Adjusted VORP", "Waiver VORP", "Draft order"]
        if draft_format == "Auction"
        else ["Available rank", "Position rank", "Projected points", "Starter VORP", "Total Starting VORP", "Confidence-Adjusted VORP", "Waiver VORP", "Draft order"]
    )
    with sort_col:
        board_sort = st.selectbox(
            "Sort board by",
            sort_choices,
            key=f"live_board_sort_{draft_format}",
        )

    record_frame = pd.DataFrame(records)
    board = auction_values.copy()
    live_lookup = available.set_index("player")[["live_value", "available_rank", "available_position_rank"]]
    board = board.join(live_lookup, on="player")
    if record_frame.empty:
        board["Pick"] = np.nan
        board["Drafting Team"] = ""
        board["Winning Bid"] = np.nan
    else:
        record_lookup = record_frame.set_index("player")
        board["Pick"] = board["player"].map(record_lookup["pick"])
        board["Drafting Team"] = board["player"].map(record_lookup["drafting_team"]).fillna("")
        board["Winning Bid"] = board["player"].map(record_lookup["price"]) if draft_format == "Auction" else np.nan
    board["Status"] = np.where(board["player"].isin(drafted_players), "✓ Drafted", "Available")
    board["Paid vs Model"] = (
        board["Winning Bid"] - board["auction_value"] if draft_format == "Auction" else np.nan
    )
    if board_positions:
        board = board.loc[board["position"].isin(board_positions)].copy()
    else:
        board = board.iloc[0:0].copy()

    sort_map = {
        "Live value": ("live_value", False),
        "Available rank": ("available_rank", True),
        "Position rank": ("available_position_rank", True),
        "Projected points": ("projected_points", False),
        "Starter VORP": ("starter_vorp", False),
        "Total Starting VORP": ("total_starting_vorp", False),
        "Confidence-Adjusted VORP": ("confidence_adjusted_total_starting_vorp", False),
        "Waiver VORP": ("waiver_vorp", False),
        "Draft order": ("Pick", True),
    }
    sort_column, sort_ascending = sort_map[board_sort]
    board["is_drafted"] = board["Status"].eq("✓ Drafted")
    board = board.sort_values(
        ["is_drafted", sort_column, "auction_rank"],
        ascending=[True, sort_ascending, True],
        na_position="last",
        kind="stable",
    )

    common_columns = [
        "Status", "Pick", "Drafting Team", "player", "available_rank",
        "available_position_rank", "projected_points", "starter_vorp", "waiver_vorp",
        "total_starting_vorp", "position_confidence", "confidence_adjusted_total_starting_vorp",
    ]
    if draft_format == "Auction":
        display_columns = common_columns + ["live_value", "auction_value", "Winning Bid", "Paid vs Model"]
    else:
        display_columns = common_columns
    board_display = board[display_columns].rename(
        columns={
            "player": "Player",
            "available_rank": "Overall",
            "available_position_rank": "Pos Rank",
            "live_value": "Live Value",
            "auction_value": "Opening Value",
            "projected_points": "Proj Pts",
            "starter_vorp": "Starter VORP",
            "total_starting_vorp": "Total Starting VORP",
            "position_confidence": "Pos Confidence",
            "confidence_adjusted_total_starting_vorp": "Confidence-Adjusted VORP",
            "waiver_vorp": "Waiver VORP",
        }
    )
    position_by_row = board["position"].to_dict()

    def color_code_draft_row(row: pd.Series) -> list[str]:
        position_color = COLORS.get(position_by_row.get(row.name, "Unknown"), COLORS["Unknown"])
        return [
            f"background-color: {position_color}24; border-bottom: 1px solid {position_color}55"
        ] * len(row)

    styled_board = board_display.style.apply(color_code_draft_row, axis=1)
    rankings_tab.dataframe(
        styled_board,
        hide_index=True,
        width="stretch",
        height=690,
        column_config={
            "Status": st.column_config.TextColumn(width=76),
            "Pick": st.column_config.NumberColumn(format="%d", width=48),
            "Drafting Team": st.column_config.TextColumn(width=95),
            "Player": st.column_config.TextColumn(width=155),
            "Overall": st.column_config.NumberColumn(format="%d", width=62),
            "Pos Rank": st.column_config.NumberColumn(format="%d", width=62),
            "Proj Pts": st.column_config.NumberColumn(format="%.1f", width=70),
            "Starter VORP": st.column_config.NumberColumn(format="%.1f", width=82),
            "Total Starting VORP": st.column_config.NumberColumn(
                "Total Starting VORP",
                help="Sum of this player's Starter VORP differences against the other top-12 players at the same position.",
                format="%.1f",
                width=105,
            ),
            "Pos Confidence": st.column_config.NumberColumn(
                "Pos Confidence",
                help="Historical rank correlation between preseason position order and realized starter contribution in this league (2023–2025).",
                format="percent",
                width=88,
            ),
            "Confidence-Adjusted VORP": st.column_config.NumberColumn(
                "Confidence-Adjusted VORP",
                help="Total Starting VORP multiplied by historical position confidence. Null for projected non-starters.",
                format="%.1f",
                width=112,
            ),
            "Waiver VORP": st.column_config.NumberColumn(format="%.1f", width=88),
            "Live Value": st.column_config.NumberColumn(format="$%d", width=68),
            "Opening Value": st.column_config.NumberColumn(format="$%d", width=78),
            "Winning Bid": st.column_config.NumberColumn(format="$%d", width=72),
            "Paid vs Model": st.column_config.NumberColumn(format="$%d", width=76),
        },
    )

    with team_board_tab:
        st.markdown("### Owner-by-position draft board")
        st.caption(
            "Roster rule: 2 QB · 4 RB · 5 WR/TE flex · 1 starting TE · 2 K · 2 DST. "
            "Every TE after the first occupies one of the five WR/TE flex slots."
        )
        board_rows: list[dict[str, str]] = []
        for position in DRAFT_POSITION_ORDER:
            board_row = {"Position": position}
            for owner in DRAFT_OWNERS[draft_format]:
                owner_position_records = [
                    record
                    for record in records
                    if str(record.get("drafting_team", "")) == owner
                    and position_lookup.get(str(record.get("player", "")), "") == position
                ]
                owner_position_records.sort(key=lambda record: int(record.get("pick", 0) or 0))
                if draft_format == "Auction":
                    board_row[owner] = "  ·  ".join(
                        f"{record['player']} (${int(record.get('price', 0) or 0)})"
                        for record in owner_position_records
                    )
                else:
                    board_row[owner] = "  ·  ".join(
                        f"#{int(record.get('pick', 0) or 0)} {record['player']}"
                        for record in owner_position_records
                    )
            board_rows.append(board_row)

        owner_board = pd.DataFrame(board_rows).rename(
            columns={owner: owner_sample_label(owner) for owner in DRAFT_OWNERS[draft_format]}
        )
        board_position_by_row = owner_board["Position"].to_dict()

        def color_code_position_row(row: pd.Series) -> list[str]:
            position_color = COLORS.get(board_position_by_row.get(row.name, "Unknown"), COLORS["Unknown"])
            return [
                f"background-color: {position_color}24; border-bottom: 1px solid {position_color}55"
            ] * len(row)

        styled_owner_board = owner_board.style.apply(color_code_position_row, axis=1)
        team_board_tab.dataframe(
            styled_owner_board,
            hide_index=True,
            width="stretch",
            height=285,
            column_config={
                "Position": st.column_config.TextColumn(width=72, pinned=True),
                **{
                    owner_sample_label(owner): st.column_config.TextColumn(width=155)
                    for owner in DRAFT_OWNERS[draft_format]
                },
            },
        )

        st.markdown("### Roster counts and limits")
        roster_rows: list[dict[str, object]] = []
        for owner in DRAFT_OWNERS[draft_format]:
            owner_counts = team_draft_counts(records, owner, position_lookup)
            rostered = sum(owner_counts.values())
            roster_row: dict[str, object] = {
                "Owner": owner_sample_label(owner),
                **owner_counts,
                "Rostered": rostered,
                "Open": max(DRAFT_ROSTER_SIZE - rostered, 0),
            }
            if draft_format == "Auction":
                owner_spent, owner_budget_left, _, owner_max_bid = team_auction_status(records, owner)
                roster_row.update(
                    {
                        "Spent": owner_spent,
                        "Budget Left": owner_budget_left,
                        "Max Bid": owner_max_bid,
                    }
                )
            roster_rows.append(roster_row)

        roster_summary = pd.DataFrame(roster_rows)
        roster_column_config: dict[str, object] = {
            "Owner": st.column_config.TextColumn(width=100, pinned=True),
            **{
                position: st.column_config.NumberColumn(format="%d", width=58)
                for position in DRAFT_POSITION_ORDER
            },
            "Rostered": st.column_config.NumberColumn(format="%d", width=72),
            "Open": st.column_config.NumberColumn(format="%d", width=60),
        }
        if draft_format == "Auction":
            roster_column_config.update(
                {
                    "Spent": st.column_config.NumberColumn(format="$%d", width=68),
                    "Budget Left": st.column_config.NumberColumn(format="$%d", width=82),
                    "Max Bid": st.column_config.NumberColumn(format="$%d", width=72),
                }
            )
        team_board_tab.dataframe(
            roster_summary,
            hide_index=True,
            width="stretch",
            height=465,
            column_config=roster_column_config,
        )

with tab_pulse:
    section_title(
        "Outcome quality",
        "Points tell the story. Schedule changes the ending.",
        "All-play win rate asks how often each score would have beaten every other team that week.",
    )
    if not all_play.empty:
        c1, c2, c3 = st.columns(3)
        luckiest = all_play.nlargest(1, "schedule_luck").iloc[0]
        strongest = all_play.nlargest(1, "all_play_win_pct").iloc[0]
        steadiest = all_play.dropna(subset=["score_std"]).nsmallest(1, "score_std").iloc[0]
        c1.markdown(f'<div class="insight"><b>{owner_sample_label(luckiest.owner)}</b><br>Most schedule help<br><span style="color:#6FB1FC">{luckiest.schedule_luck:+.1%} win-rate lift</span></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="insight"><b>{owner_sample_label(strongest.owner)}</b><br>Best all-play team<br><span style="color:#6FB1FC">{strongest.all_play_win_pct:.1%} all-play rate</span></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="insight"><b>{owner_sample_label(steadiest.owner)}</b><br>Most consistent scoring<br><span style="color:#6FB1FC">{steadiest.score_std:.1f} weekly SD</span></div>', unsafe_allow_html=True)

        all_play_chart = all_play.assign(owner_label=all_play["owner"].map(owner_sample_label))
        all_play_weekly_chart = all_play_weekly.assign(owner_label=all_play_weekly["owner"].map(owner_sample_label))

        left, right = st.columns([1.05, 1])
        with left:
            scatter = px.scatter(
                all_play_chart,
                x="all_play_win_pct",
                y="actual_win_pct",
                size="average_points",
                color="schedule_luck",
                text="owner_label",
                color_continuous_scale=["#C05E85", "#1C1F26", "#6FB1FC"],
                color_continuous_midpoint=0,
                labels={"all_play_win_pct": "All-play win rate", "actual_win_pct": "Actual win rate", "schedule_luck": "Schedule luck"},
                title="Actual record vs underlying weekly strength",
            )
            scatter.add_shape(type="line", x0=0, y0=0, x1=1, y1=1, line=dict(color="#6F7C89", dash="dash"))
            scatter.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="#D9E5F0")))
            scatter.update_xaxes(tickformat=".0%", range=[0, 1])
            scatter.update_yaxes(tickformat=".0%", range=[0, 1])
            render_plot(scatter, "luck_scatter")
        with right:
            score_box = px.box(
                all_play_weekly_chart,
                x="owner_label",
                y="net_points_vs_weekly_median",
                points="outliers",
                color="owner_label",
                title="Weekly scoring relative to that league's median",
                labels={"net_points_vs_weekly_median": "Net points vs weekly median", "owner_label": "Owner"},
            )
            score_box.add_hline(y=0, line_dash="dash", line_color="#7E8A96")
            score_box.update_layout(showlegend=False)
            score_box.update_xaxes(categoryorder="median descending")
            render_plot(score_box, "score_box")

        display = all_play.copy()
        display["Owner"] = display["owner"].map(owner_sample_label)
        display["Actual W%"] = display["actual_win_pct"].map(pct)
        display["All-play W%"] = display["all_play_win_pct"].map(pct)
        display["Wins + median W%"] = display["combined_win_pct"].map(pct)
        display["Schedule lift"] = display["schedule_luck"].map(lambda value: f"{value:+.1%}")
        display["Avg net vs median"] = display["average_net_points"].round(1)
        st.dataframe(
            display[["Owner", "weeks", "matchups", "Avg net vs median", "Actual W%", "Wins + median W%", "All-play W%", "Schedule lift"]].rename(columns={"weeks": "Scoring weeks", "matchups": "H2H matchups"}),
            hide_index=True,
            width="stretch",
        )
        st.caption("Wins + median W% = (actual H2H result value + above-weekly-median result value) ÷ 2, calculated only where a recorded H2H matchup exists.")


with tab_owner_history:
    section_title(
        "Owner dossier",
        "One owner. Every season, rivalry, and signature player.",
        "The global year and format filters apply here. Total points use every captured fantasy week; H2H records use Yahoo's recorded regular-season matchups.",
    )
    history_owners = sorted(standings["owner"].dropna().astype(str).unique(), key=str.casefold)
    if not history_owners:
        st.info("No owner history is available for the selected league seasons.")
    else:
        owner_default = history_owners.index("McCade") if "McCade" in history_owners else 0
        history_owner = st.selectbox(
            "Owner", history_owners, index=owner_default, format_func=owner_sample_label, key="owner_history_owner"
        )
        history_owner_label = owner_sample_label(history_owner)
        owner_standings = standings.loc[standings["owner"].eq(history_owner)].copy()
        owner_weekly = all_play_weekly.loc[all_play_weekly["owner"].eq(history_owner)].copy()
        owner_scores = scores.loc[scores["owner"].eq(history_owner)].copy()
        owner_lineups = lineups.loc[lineups["owner"].eq(history_owner)].copy()
        owner_h2h = season_h2h_records(owner_scores, owner_standings)

        league_all_week_points = (
            scoring_history
            .groupby(["season", "league_id", "team_id"], as_index=False)
            .agg(all_season_points=("team_score", "sum"), scoring_weeks=("week", "nunique"))
        )
        league_all_week_points["all_week_points_rank"] = league_all_week_points.groupby(
            ["season", "league_id"]
        )["all_season_points"].rank(method="min", ascending=False)
        all_week_points = league_all_week_points.merge(
            owner_standings[["season", "league_id", "team_id"]],
            on=["season", "league_id", "team_id"],
            how="inner",
            validate="one_to_one",
        )
        normalized_scoring = (
            owner_weekly.groupby(["season", "league_id", "team_id"], as_index=False)
            .agg(
                average_net_points=("net_points_vs_weekly_median", "mean"),
                median_net_points=("net_points_vs_weekly_median", "median"),
                all_play_win_pct=("all_play_win_value", "mean"),
            )
        )
        owner_execution = (
            lineup_weeks.loc[lineup_weeks["owner"].eq(history_owner)]
            .groupby(["season", "league_id", "team_id"], as_index=False)
            .agg(actual_points=("actual_points", "sum"), optimal_points=("optimal_points", "sum"))
        )
        if not owner_execution.empty:
            owner_execution["lineup_efficiency"] = owner_execution["actual_points"] / owner_execution["optimal_points"]

        owner_ledger = owner_standings.merge(
            all_week_points, on=["season", "league_id", "team_id"], how="left", validate="one_to_one"
        ).merge(
            normalized_scoring, on=["season", "league_id", "team_id"], how="left", validate="one_to_one"
        ).merge(
            owner_h2h[
                [
                    "season", "league_id", "team_id", "h2h_games", "h2h_wins",
                    "h2h_losses", "h2h_ties", "h2h_win_pct", "h2h_record",
                    "h2h_points_for", "h2h_points_against", "h2h_source",
                ]
            ],
            on=["season", "league_id", "team_id"],
            how="left",
            validate="one_to_one",
        )
        if not owner_execution.empty:
            owner_ledger = owner_ledger.merge(
                owner_execution[["season", "league_id", "team_id", "lineup_efficiency"]],
                on=["season", "league_id", "team_id"],
                how="left",
                validate="one_to_one",
            )
        else:
            owner_ledger["lineup_efficiency"] = np.nan
        owner_ledger["final_result"] = owner_ledger["rank"].map(finish_label)
        owner_ledger["entry"] = owner_ledger["season"].astype(str) + " " + owner_ledger["draft_type"].str.title()
        league_sizes = standings.groupby(["season", "league_id"], as_index=False).agg(team_count=("team_id", "nunique"))
        owner_ledger = owner_ledger.merge(
            league_sizes, on=["season", "league_id"], how="left", validate="many_to_one"
        )
        owner_ledger["prize_pool"] = owner_ledger["team_count"] * 100.0
        owner_ledger["total_points_payout_pct"] = owner_ledger["all_week_points_rank"].map(
            {1.0: 0.40, 2.0: 0.20, 3.0: 0.10}
        ).fillna(0.0)
        owner_ledger["h2h_payout_pct"] = owner_ledger["rank"].map(
            {1.0: 0.20, 2.0: 0.10}
        ).fillna(0.0)
        owner_ledger["gross_winnings"] = owner_ledger["prize_pool"] * (
            owner_ledger["total_points_payout_pct"] + owner_ledger["h2h_payout_pct"]
        )
        owner_ledger["net_profit"] = owner_ledger["gross_winnings"] - 100.0

        career_wins = int(owner_ledger["h2h_wins"].sum())
        career_losses = int(owner_ledger["h2h_losses"].sum())
        career_ties = int(owner_ledger["h2h_ties"].sum())
        career_points = float(all_week_points["all_season_points"].sum()) if not all_week_points.empty else 0.0
        career_net = float(owner_weekly["net_points_vs_weekly_median"].mean()) if not owner_weekly.empty else np.nan
        career_profit = float(owner_ledger["net_profit"].sum())
        h1, h2, h3, h4, h5 = st.columns(5)
        h1.metric("League entries", len(owner_ledger))
        h2.metric("H2H record", f"{career_wins}-{career_losses}-{career_ties}")
        h3.metric("Points · all weeks", f"{career_points:,.1f}")
        h4.metric("Avg weekly net vs median", "—" if pd.isna(career_net) else f"{career_net:+.1f}")
        h5.metric("Net profit", f"${career_profit:,.0f}")
        st.caption(
            "Profit model: $100 per entry; 40%/20%/10% of each league pool to the top three all-week point totals, "
            "plus 20%/10% to the H2H champion and runner-up."
        )

        st.markdown("### Championships")
        championships = owner_ledger.loc[owner_ledger["rank"].eq(1)].sort_values(["season", "draft_type"])
        if championships.empty:
            st.caption(f"{history_owner_label} has no championships in the selected seasons.")
        else:
            championship_lines = [
                f"- **{int(row.season)} {str(row.draft_type).title()}** — {row.team_name}"
                for row in championships.itertuples(index=False)
            ]
            st.markdown("\n".join(championship_lines))

        st.markdown("### Runner-up finishes")
        runners_up = owner_ledger.loc[owner_ledger["rank"].eq(2)].sort_values(["season", "draft_type"])
        if runners_up.empty:
            st.caption(f"{history_owner_label} has no H2H runner-up finishes in the selected seasons.")
        else:
            runner_up_lines = [
                f"- **{int(row.season)} {str(row.draft_type).title()}** — {row.team_name}"
                for row in runners_up.itertuples(index=False)
            ]
            st.markdown("\n".join(runner_up_lines))

        section_title("Season ledger", f"{history_owner_label}'s year-by-year results")
        trajectory = owner_ledger.sort_values(["season", "draft_type"]).copy()
        if not trajectory.empty:
            trajectory["Format"] = trajectory["draft_type"].str.title()
            owner_timeline = px.line(
                trajectory,
                x="season",
                y="average_net_points",
                color="Format",
                markers=True,
                text="final_result",
                color_discrete_map={"Snake": "#6FB1FC", "Auction": "#CC8C4A"},
                hover_data={
                    "all_season_points": ":.1f",
                    "record": True,
                    "all_play_win_pct": ":.1%",
                    "season": False,
                },
                title="Scoring trajectory relative to each league-week median",
                labels={"season": "Season", "average_net_points": "Average weekly points vs median"},
            )
            owner_timeline.add_hline(y=0, line_dash="dash", line_color="#7E8A96")
            owner_timeline.update_traces(textposition="top center")
            owner_timeline.update_xaxes(
                tickmode="linear",
                dtick=1,
                range=[year_range[0] - 0.2, year_range[1] + 0.2],
                tickformat="d",
            )
            render_plot(owner_timeline, "owner_history_trajectory")

            ledger_display = trajectory.copy()
            ledger_display["Season"] = ledger_display["season"].astype(int)
            ledger_display["Format"] = ledger_display["draft_type"].str.title()
            ledger_display["Team"] = ledger_display["team_name"]
            ledger_display["Result"] = ledger_display["final_result"]
            ledger_display["Record"] = ledger_display["h2h_record"]
            ledger_display["H2H win %"] = ledger_display["h2h_win_pct"].map(pct)
            ledger_display["All-week points"] = ledger_display["all_season_points"].round(1)
            ledger_display["Points rank"] = ledger_display["all_week_points_rank"].map(ordinal)
            ledger_display["H2H PF"] = ledger_display["h2h_points_for"].round(1)
            ledger_display["H2H PA"] = ledger_display["h2h_points_against"].round(1)
            ledger_display["Avg net vs median"] = ledger_display["average_net_points"].round(1)
            ledger_display["Lineup efficiency"] = ledger_display["lineup_efficiency"].map(pct)
            ledger_display["Gross winnings"] = ledger_display["gross_winnings"].map(lambda value: f"${value:,.0f}")
            ledger_display["Net profit"] = ledger_display["net_profit"].map(lambda value: f"${value:,.0f}")
            st.dataframe(
                ledger_display[
                    [
                        "Season", "Format", "Team", "Result", "Record", "H2H win %",
                        "All-week points", "Points rank", "H2H PF", "H2H PA",
                        "Avg net vs median", "Lineup efficiency", "Gross winnings", "Net profit",
                    ]
                ],
                hide_index=True,
                width="stretch",
            )
            best_season = trajectory.dropna(subset=["average_net_points"]).nlargest(1, "average_net_points")
            if not best_season.empty:
                best_row = best_season.iloc[0]
                st.caption(
                    f"Best normalized scoring season: {int(best_row.season)} {str(best_row.draft_type).title()} "
                    f"at {best_row.average_net_points:+.1f} points per week versus the league median."
                )

        section_title(
            "Starter-slot history",
            "Where the lineup ranked at every position",
            "Ranks compare total starter points within each league-season. W/T starters—including tight ends—fill WR1/WR2/WR3; only the dedicated TE slot counts as TE1.",
        )
        owner_slot_history = slot_rankings.loc[slot_rankings["owner"].eq(history_owner)].copy()
        if owner_slot_history.empty:
            st.info("No detailed starter-slot history is available for this owner in the selected seasons.")
        else:
            owner_slot_history["entry"] = (
                owner_slot_history["season"].astype(int).astype(str)
                + " "
                + owner_slot_history["draft_type"].str.title()
            )
            entry_order = (
                owner_slot_history[["season", "draft_type", "entry"]]
                .drop_duplicates()
                .sort_values(["season", "draft_type"])["entry"]
                .tolist()
            )
            rank_history = owner_slot_history.pivot(index="entry", columns="starter_slot", values="slot_rank").reindex(
                index=entry_order, columns=STARTER_SLOT_ORDER
            )
            point_history = owner_slot_history.pivot(
                index="entry", columns="starter_slot", values="starter_points"
            ).reindex(index=entry_order, columns=STARTER_SLOT_ORDER)
            rank_limit = max(float(owner_slot_history["league_teams"].max()), 2.0)
            history_heatmap = px.imshow(
                rank_history,
                aspect="auto",
                text_auto=".0f",
                color_continuous_scale=["#6FB1FC", "#1C1F26", "#C05E85"],
                zmin=1,
                zmax=rank_limit,
                labels=dict(x="Starting slot", y="League entry", color="League rank"),
                title=f"{history_owner_label}: starter-point rank by league-season",
            )
            history_heatmap.update_traces(
                customdata=point_history.to_numpy(),
                hovertemplate="Entry: %{y}<br>Slot: %{x}<br>Rank: %{z:.0f}<br>Starter points: %{customdata:.1f}<extra></extra>",
            )
            polish(history_heatmap, height=max(390, 34 * len(rank_history.index) + 170))
            st.plotly_chart(
                history_heatmap,
                width="stretch",
                config={"displaylogo": False},
                key="owner_history_slot_ranks",
            )
            st.caption("1 is best. RB TOTAL, WR TOTAL, and TOTAL rank the combined starter points in those groups. Weekly RB and W/T starters are ordered by fantasy points before their slot totals are accumulated.")

        section_title("Rivalry book", "Head-to-head record against every owner")
        opponent_lookup = selected(team_map)[["season", "league_id", "yahoo_team_id", "owner"]].drop_duplicates().rename(
            columns={"yahoo_team_id": "opponent_id", "owner": "opponent"}
        )
        rivalry_games = owner_scores.merge(
            opponent_lookup,
            on=["season", "league_id", "opponent_id"],
            how="left",
            validate="many_to_one",
        )
        rivalry_games = rivalry_games.loc[rivalry_games["opponent"].notna() & rivalry_games["opponent"].ne(history_owner)].copy()
        if rivalry_games.empty:
            st.info("No H2H opponent history is available in the selected seasons.")
        else:
            rivalry_games["win_value"] = np.select(
                [rivalry_games["result"].eq("win"), rivalry_games["result"].eq("tie")],
                [1.0, 0.5],
                default=0.0,
            )
            rivalry = rivalry_games.groupby("opponent", as_index=False).agg(
                games=("week", "size"),
                wins=("result", lambda values: int(values.eq("win").sum())),
                losses=("result", lambda values: int(values.eq("loss").sum())),
                ties=("result", lambda values: int(values.eq("tie").sum())),
                win_pct=("win_value", "mean"),
                points_for=("team_score", "sum"),
                points_against=("opponent_score", "sum"),
            )
            rivalry["margin_per_game"] = (rivalry["points_for"] - rivalry["points_against"]) / rivalry["games"]
            rivalry["record"] = rivalry.apply(lambda row: f"{row.wins}-{row.losses}-{row.ties}", axis=1)
            rivalry["opponent_label"] = rivalry["opponent"].map(owner_sample_label)
            established = rivalry.loc[rivalry["games"].ge(3)]
            r1, r2 = st.columns(2)
            if not established.empty:
                favorite = established.sort_values(["win_pct", "games"], ascending=[False, False]).iloc[0]
                nemesis = established.sort_values(["win_pct", "games"], ascending=[True, False]).iloc[0]
                r1.metric("Best matchup", owner_sample_label(favorite.opponent), favorite.record)
                r2.metric("Toughest rival", owner_sample_label(nemesis.opponent), nemesis.record)
            rivalry_chart = px.bar(
                rivalry.sort_values("win_pct"),
                x="win_pct",
                y="opponent_label",
                orientation="h",
                color="margin_per_game",
                text="record",
                color_continuous_scale=["#C05E85", "#1C1F26", "#6FB1FC"],
                color_continuous_midpoint=0,
                hover_data={"games": True, "points_for": ":.1f", "points_against": ":.1f", "margin_per_game": ":+.1f"},
                title="Career regular-season H2H win rate",
                labels={"win_pct": "Win rate", "opponent_label": "Opponent", "margin_per_game": "Margin / game"},
            )
            rivalry_chart.update_xaxes(tickformat=".0%", range=[0, 1])
            render_plot(rivalry_chart, "owner_history_rivalries")
            rivalry_display = rivalry.sort_values(["games", "win_pct"], ascending=[False, False]).copy()
            rivalry_display["Opponent"] = rivalry_display["opponent_label"]
            rivalry_display["Games"] = rivalry_display["games"]
            rivalry_display["Record"] = rivalry_display["record"]
            rivalry_display["Win %"] = rivalry_display["win_pct"].map(pct)
            rivalry_display["PF"] = rivalry_display["points_for"].round(1)
            rivalry_display["PA"] = rivalry_display["points_against"].round(1)
            rivalry_display["Margin / game"] = rivalry_display["margin_per_game"].round(1)
            st.dataframe(
                rivalry_display[["Opponent", "Games", "Record", "Win %", "PF", "PA", "Margin / game"]],
                hide_index=True,
                width="stretch",
            )

        section_title("Franchise players", "Who stayed on the roster—and who actually started")
        if owner_lineups.empty:
            st.info("No detailed weekly roster history is available for this owner in the selected seasons.")
        else:
            player_weeks = owner_lineups.loc[owner_lineups["player_name"].astype(str).str.strip().ne("")].copy()
            player_weeks = player_weeks.drop_duplicates(
                ["season", "league_id", "team_id", "week", "player_key"], keep="first"
            )
            player_weeks["starter_points"] = np.where(
                player_weeks["is_starter"], player_weeks["fan_points"].fillna(0), 0.0
            )
            player_usage = player_weeks.groupby(["player_key", "player_name", "position_group"], as_index=False).agg(
                rostered_weeks=("week", "size"),
                starts=("is_starter", "sum"),
                seasons=("season", "nunique"),
                starter_points=("starter_points", "sum"),
                total_points_on_roster=("fan_points", "sum"),
            )
            most_rostered = player_usage.sort_values(["rostered_weeks", "starts"], ascending=False).iloc[0]
            most_started = player_usage.sort_values(["starts", "rostered_weeks"], ascending=False).iloc[0]
            most_productive = player_usage.sort_values(["starter_points", "starts"], ascending=False).iloc[0]
            p1, p2, p3 = st.columns(3)
            p1.metric("Rostered most", most_rostered.player_name, f"{int(most_rostered.rostered_weeks)} team-weeks")
            p2.metric("Started most", most_started.player_name, f"{int(most_started.starts)} starts")
            p3.metric("Most starter points", most_productive.player_name, f"{most_productive.starter_points:,.1f} pts")
            franchise = player_usage.sort_values(["rostered_weeks", "starts"], ascending=False).head(15).copy()
            franchise_long = franchise.melt(
                id_vars=["player_name", "position_group"],
                value_vars=["rostered_weeks", "starts"],
                var_name="Usage",
                value_name="Team-weeks",
            )
            franchise_long["Usage"] = franchise_long["Usage"].map({"rostered_weeks": "Rostered", "starts": "Started"})
            franchise_chart = px.bar(
                franchise_long,
                x="Team-weeks",
                y="player_name",
                color="Usage",
                barmode="group",
                orientation="h",
                category_orders={"player_name": franchise["player_name"].iloc[::-1].tolist()},
                color_discrete_map={"Rostered": "#6FB1FC", "Started": "#CC8C4A"},
                title="Most-used players across all captured rosters",
                labels={"player_name": "Player"},
            )
            render_plot(franchise_chart, "owner_history_players")
            franchise_display = franchise.copy()
            franchise_display["Player"] = franchise_display["player_name"]
            franchise_display["Pos"] = franchise_display["position_group"]
            franchise_display["Rostered weeks"] = franchise_display["rostered_weeks"].astype(int)
            franchise_display["Starts"] = franchise_display["starts"].astype(int)
            franchise_display["Seasons"] = franchise_display["seasons"].astype(int)
            franchise_display["Starter points"] = franchise_display["starter_points"].round(1)
            st.dataframe(
                franchise_display[["Player", "Pos", "Rostered weeks", "Starts", "Seasons", "Starter points"]],
                hide_index=True,
                width="stretch",
            )

        section_title("Draft fingerprint", "How this owner invests early capital")
        draft_view = selected(data["draft_board"])
        owner_draft_view = draft_view.loc[draft_view["owner"].eq(history_owner)].copy()
        if owner_draft_view.empty:
            st.info("Draft-order data is not available for this owner in the selected seasons. Roster history above remains complete.")
        else:
            draft_entries = draft_view[["owner", "season", "draft_type", "team_name"]].drop_duplicates()
            positions = pd.DataFrame({"position": ["QB", "RB", "WR", "TE", "K", "DST"]})
            early_board = draft_view.loc[draft_view["capital_rank"].le(5 * draft_view["team_count"])].copy()
            early_counts = early_board.groupby(
                ["owner", "season", "draft_type", "team_name", "position"], as_index=False
            ).size()
            early_grid = draft_entries.merge(positions, how="cross").merge(
                early_counts,
                on=["owner", "season", "draft_type", "team_name", "position"],
                how="left",
            )
            early_grid["size"] = early_grid["size"].fillna(0)
            owner_mix = (
                early_grid.loc[early_grid["owner"].eq(history_owner)]
                .groupby("position", as_index=False)["size"]
                .mean()
                .rename(columns={"size": "Selections"})
            )
            owner_mix["Series"] = history_owner_label
            league_mix = early_grid.groupby("position", as_index=False)["size"].mean().rename(columns={"size": "Selections"})
            league_mix["Series"] = "League average"
            draft_mix = pd.concat([owner_mix, league_mix], ignore_index=True)
            role_metrics = combined_draft_role_summary(draft_view)
            core_roles = [
                role for role in ["QB1", "QB2", "RB1", "RB2", "RB3", "WR1", "WR2", "WR3", "WR4", "WR5", "TE1", "K1", "DST1"]
                if role in set(role_metrics["role"])
            ]
            owner_roles = role_metrics.loc[
                role_metrics["owner"].eq(history_owner) & role_metrics["role"].isin(core_roles)
            ].copy()
            draft_count = len(owner_draft_view[["season", "draft_type", "team_name"]].drop_duplicates())
            favorite_position = owner_mix.sort_values("Selections", ascending=False).iloc[0]
            d1, d2, d3 = st.columns(3)
            d1.metric("Drafts observed", draft_count)
            d2.metric("Early position lean", favorite_position.position, f"{favorite_position.Selections:.1f} in first five rounds")
            if not owner_roles.empty:
                aggressive = owner_roles.nlargest(1, "aggression_vs_league").iloc[0]
                d3.metric("Earliest role vs league", aggressive.role, f"{aggressive.aggression_vs_league:+.1f} rounds")
            else:
                d3.metric("Earliest role vs league", "—")

            draft_mix_chart = px.bar(
                draft_mix,
                x="position",
                y="Selections",
                color="Series",
                barmode="group",
                color_discrete_map={history_owner_label: "#6FB1FC", "League average": "#667483"},
                category_orders={"position": ["QB", "RB", "WR", "TE", "K", "DST"]},
                title="Average position allocation in the first five de facto rounds",
                labels={"position": "Position", "Selections": "Players selected per draft"},
            )
            render_plot(draft_mix_chart, "owner_history_draft_mix")
            if not owner_roles.empty:
                owner_roles["role"] = pd.Categorical(owner_roles["role"], categories=core_roles, ordered=True)
                owner_roles = owner_roles.sort_values("role")
                role_display = owner_roles.copy()
                role_display["Role"] = role_display["role"].astype(str)
                role_display[f"{history_owner_label} avg round"] = role_display["owner_average"].round(1)
                role_display["League avg round"] = role_display["league_average"].round(1)
                role_display["Rounds earlier"] = role_display["aggression_vs_league"].round(1)
                st.dataframe(
                    role_display[["Role", f"{history_owner_label} avg round", "League avg round", "Rounds earlier"]],
                    hide_index=True,
                    width="stretch",
                )
            st.caption("Auction purchases are converted to de facto rounds by price and nomination order so they can be compared with snake selections. Draft-order history currently begins in 2023.")


with tab_position:
    section_title(
        "Roster construction",
        "Where the points actually came from",
        "WR and TE are always shown as distinct player positions. The dedicated TE starter is enforced in perfect-lineup calculations, while the three W/T lineup slots may be filled by either position.",
    )
    if lineups.empty:
        st.info("No detailed roster pages have been normalized for this league-season yet.")
    else:
        plot_rows = lineups.loc[lineups["lineup_role"].isin(["Starter", "Bench"]) & lineups["position_group"].ne("Unknown")].copy()
        box = px.box(
            plot_rows,
            x="position_group",
            y="fan_points",
            color="lineup_role",
            category_orders={"position_group": POSITION_ORDER[:-1], "lineup_role": ["Starter", "Bench"]},
            color_discrete_map={"Starter": COLORS["Starter"], "Bench": COLORS["Bench"]},
            points="outliers",
            labels={"position_group": "Position", "fan_points": "Player-week points", "lineup_role": "Role"},
            title="Starter and bench scoring distributions",
        )
        render_plot(box, "position_box")

        starter_points = (
            lineups.loc[lineups["is_starter"]]
            .groupby(["owner", "position_group"], as_index=False)["fan_points"]
            .sum()
        )
        starter_points["owner_label"] = starter_points["owner"].map(owner_sample_label)
        owner_totals = starter_points.groupby("owner")["fan_points"].transform("sum")
        starter_points["share"] = starter_points["fan_points"] / owner_totals
        stack = px.bar(
            starter_points,
            x="owner_label",
            y="share",
            color="position_group",
            category_orders={"position_group": POSITION_ORDER},
            color_discrete_map=COLORS,
            text=starter_points["share"].map(lambda value: f"{value:.0%}" if value >= 0.06 else ""),
            labels={"owner_label": "Owner", "share": "Share of starter points", "position_group": "Position"},
            title="Position share of observed starter points",
        )
        stack.update_yaxes(tickformat=".0%")
        render_plot(stack, "position_share")

        section_title(
            "Starter-slot rankings",
            "Who squeezed the most scoring from each lineup spot",
            "Each team is ranked on total observed starter points inside its league-season. Across multiple selected seasons, the heatmap shows the owner's average rank.",
        )
        if slot_rankings.empty:
            st.info("No starter-slot rankings are available for the selected league seasons.")
        else:
            slot_summary = slot_rankings.copy()
            slot_summary["points_per_week"] = (
                slot_summary["starter_points"] / slot_summary["observed_weeks"].replace(0, np.nan)
            )
            slot_summary = slot_summary.groupby(["owner", "starter_slot"], as_index=False).agg(
                average_rank=("slot_rank", "mean"),
                points_per_week=("points_per_week", "mean"),
                team_seasons=("season", "size"),
            )
            rank_grid = slot_summary.pivot(index="owner", columns="starter_slot", values="average_rank").reindex(
                index=sorted(slot_summary["owner"].unique(), key=str.casefold),
                columns=STARTER_SLOT_ORDER,
            )
            scoring_grid = slot_summary.pivot(
                index="owner", columns="starter_slot", values="points_per_week"
            ).reindex(index=rank_grid.index, columns=STARTER_SLOT_ORDER)
            rank_grid.index = [owner_sample_label(owner) for owner in rank_grid.index]
            scoring_grid.index = rank_grid.index
            rank_limit = max(float(slot_rankings["league_teams"].max()), 2.0)
            slot_heatmap = px.imshow(
                rank_grid,
                aspect="auto",
                text_auto=".1f" if slot_rankings[["season", "league_id"]].drop_duplicates().shape[0] > 1 else ".0f",
                color_continuous_scale=["#6FB1FC", "#1C1F26", "#C05E85"],
                zmin=1,
                zmax=rank_limit,
                labels=dict(x="Starting slot", y="Owner", color="League rank"),
                title="Starter-point rank by lineup slot",
            )
            slot_heatmap.update_traces(
                customdata=scoring_grid.to_numpy(),
                hovertemplate="Owner: %{y}<br>Slot: %{x}<br>Rank: %{z:.1f}<br>Points / observed week: %{customdata:.1f}<extra></extra>",
            )
            polish(slot_heatmap, height=max(500, 29 * len(rank_grid.index) + 175))
            st.plotly_chart(
                slot_heatmap,
                width="stretch",
                config={"displaylogo": False},
                key="position_slot_rankings",
            )
            st.caption(
                "1 is best. RB TOTAL, WR TOTAL, and TOTAL rank combined starter points. RB1/RB2 and WR1/WR2/WR3 are assigned by weekly starter scoring; a TE used at W/T counts as a WR-slot performance."
            )

        position_table = (
            plot_rows.groupby(["position_group", "lineup_role"])["fan_points"]
            .agg(["count", "mean", lambda x: x.quantile(.25), "median", lambda x: x.quantile(.75)])
            .reset_index()
        )
        position_table.columns = ["Position", "Role", "Player-weeks", "Mean", "25th percentile", "Median", "75th percentile"]
        for column in ["Mean", "25th percentile", "Median", "75th percentile"]:
            position_table[column] = position_table[column].round(1)
        st.dataframe(position_table, hide_index=True, width="stretch")

with tab_draft_room:
    section_title(
        "Draft behavior",
        "What each owner pays—and when they strike",
        "Auction bids are converted to de facto picks by sorting cost descending, then nomination order. Snake and auction capital are expressed as fractional rounds so they can share one owner profile.",
    )
    draft_view = selected(data["draft_board"])

    if draft_view.empty:
        st.info("No drafts match the sidebar filters.")
    else:
        role_metrics = combined_draft_role_summary(draft_view)
        core_roles = [
            role for role in ["QB1", "QB2", "RB1", "RB2", "RB3", "RB4", "WR1", "WR2", "WR3", "WR4", "WR5", "TE1", "K1", "K2", "DST1", "DST2"]
            if role in set(role_metrics["role"])
        ]
        heat_data = role_metrics.loc[role_metrics["role"].isin(core_roles)]
        heat = heat_data.pivot(index="owner", columns="role", values="aggression_vs_league").reindex(columns=core_roles)
        heat = heat.reindex(sorted(heat.index, key=str.casefold))
        heat.index = [owner_sample_label(owner) for owner in heat.index]
        heat_limit = max(float(np.nanmax(np.abs(heat.to_numpy(dtype=float)))), 0.5)
        unit = "fractional rounds earlier"
        heatmap = px.imshow(
            heat,
            aspect="auto",
            text_auto=".1f",
            color_continuous_scale=["#46A2CA", "#1C1F26", "#C05E85"],
            color_continuous_midpoint=0,
            zmin=-heat_limit,
            zmax=heat_limit,
            labels=dict(x="Roster role", y="Owner", color=unit.title()),
            title="Combined snake + auction role aggression",
        )
        polish(heatmap, height=max(460, 28 * len(heat.index) + 170))
        st.plotly_chart(heatmap, width="stretch", config={"displaylogo": False}, key="role_aggression_heatmap")

        owner_names = sorted(draft_view["owner"].unique(), key=str.casefold)
        profile_default = owner_names.index("McCade") if "McCade" in owner_names else 0
        profile_owner = st.selectbox(
            "Owner profile", owner_names, index=profile_default, format_func=owner_sample_label, key="draft_profile_owner"
        )
        profile_owner_label = owner_sample_label(profile_owner)
        owner_roles = role_metrics.loc[role_metrics["owner"].eq(profile_owner) & role_metrics["role"].isin(core_roles)].copy()
        owner_roles["role"] = pd.Categorical(owner_roles["role"], categories=core_roles, ordered=True)
        owner_roles = owner_roles.sort_values("role")
        most_aggressive = owner_roles.nlargest(1, "aggression_vs_league").iloc[0]
        most_patient = owner_roles.nsmallest(1, "aggression_vs_league").iloc[0]
        profile_drafts = len(draft_view.loc[draft_view["owner"].eq(profile_owner), ["season", "draft_type"]].drop_duplicates())
        p1, p2, p3 = st.columns(3)
        p1.metric("Drafts in profile", int(profile_drafts))
        p2.metric("Most aggressive role", str(most_aggressive["role"]), f"{most_aggressive.aggression_vs_league:+.1f} {unit}")
        p3.metric("Most patient role", str(most_patient["role"]), f"{most_patient.aggression_vs_league:+.1f} {unit}")

        profile_long = owner_roles.melt(
            id_vars="role",
            value_vars=["owner_average", "league_average"],
            var_name="Series",
            value_name="Value",
        )
        profile_long["Series"] = profile_long["Series"].map({"owner_average": profile_owner_label, "league_average": "League average"})
        role_compare = px.bar(
            profile_long,
            x="role",
            y="Value",
            color="Series",
            barmode="group",
            color_discrete_map={profile_owner_label: "#6FB1FC", "League average": "#667483"},
            title=f"{profile_owner_label}: combined roster-role timing",
            labels={"role": "Roster role", "Value": "Average de facto round"},
        )
        render_plot(role_compare, "owner_role_compare")
        st.caption("Lower bars mean earlier capital. Auction ties are broken by nomination order; fractional rounds control for 10- versus 12-team leagues.")

        st.markdown("### Position allocation")
        round_window = st.slider("De facto rounds included", 1, 16, 5, key="allocation_rounds")
        early = draft_view.loc[
            draft_view["capital_rank"].le(round_window * draft_view["team_count"])
        ].copy()
        allocation_drafts = draft_view[["owner", "season", "draft_type"]].drop_duplicates()
        allocation_positions = pd.DataFrame({"position": ["QB", "RB", "WR", "TE", "K", "DST"]})
        allocation_grid = allocation_drafts.merge(allocation_positions, how="cross")
        allocation_counts = early.groupby(
            ["owner", "season", "draft_type", "position"], as_index=False
        ).size()
        allocation = (
            allocation_grid.merge(
                allocation_counts,
                on=["owner", "season", "draft_type", "position"],
                how="left",
            )
            .assign(size=lambda frame: frame["size"].fillna(0))
            .groupby(["owner", "position"], as_index=False)["size"].mean()
            .rename(columns={"position": "Position", "size": "Players"})
        )
        allocation["owner_label"] = allocation["owner"].map(owner_sample_label)
        allocation_chart = px.bar(
            allocation,
            x="owner_label",
            y="Players",
            color="Position",
            color_discrete_map=COLORS,
            text=allocation["Players"].map(lambda value: f"{value:.1f}"),
            title=f"Average position mix in the first {round_window} de facto rounds",
            labels={"owner_label": "Owner", "Players": "Players selected"},
        )
        allocation_totals = allocation.groupby("owner_label", as_index=False)["Players"].sum()
        allocation_chart.add_trace(
            go.Scatter(
                x=allocation_totals["owner_label"],
                y=allocation_totals["Players"] + 0.12,
                mode="text",
                text=allocation_totals["Players"].map(lambda value: f"{value:.1f}"),
                textfont=dict(color="#DCEEFF", size=13),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        render_plot(allocation_chart, "draft_allocation")
        if season_type == "Snake":
            st.caption(
                f"Each stack averages exactly {round_window} selections per draft unless a live pick trade changed an owner's count. "
                "Decimal position segments are averages across the selected seasons."
            )
        else:
            st.caption(
                "Snake drafts use the selected number of complete rounds. Auction drafts use the same number of league-wide "
                "de facto rounds after sorting purchases by price, so an owner's total can differ from the round count."
            )

        st.markdown("### Individual player reaches and discounts")
        market_view_choice = st.radio(
            "Market lens",
            ["Biggest reaches", "Biggest values"],
            horizontal=True,
            key="market_lens",
        )
        player_results = selected(data["drafted_player_outcomes"])
        player_results = player_results.loc[
            player_results["espn_overall_rank"].notna() & player_results["player_name"].astype(str).str.strip().ne("")
        ].copy()
        player_results["market_pick_gap"] = player_results["espn_overall_rank"] - player_results["capital_rank"]
        outcome_lookup = data["draft_outcomes"][
            ["season", "draft_type", "team_name", "owner", "points_per_game", "finish_rank", "all_play_win_pct", "median_net_points", "combined_win_pct"]
        ].drop_duplicates()
        player_results = player_results.merge(
            outcome_lookup,
            on=["season", "draft_type", "team_name", "owner"],
            how="left",
            validate="many_to_one",
        )
        position_options = [position for position in ["QB", "RB", "WR", "TE", "K", "DST"] if position in set(player_results["position"])]
        filter_left, filter_right = st.columns(2)
        market_positions = filter_left.multiselect("Positions", position_options, default=position_options, key="market_positions")
        owner_options = sorted(player_results["owner"].dropna().unique(), key=str.casefold)
        market_owners = filter_right.multiselect(
            "Owners", owner_options, default=owner_options, format_func=owner_sample_label, key="market_owners"
        )
        player_results = player_results.loc[player_results["position"].isin(market_positions) & player_results["owner"].isin(market_owners)]
        ascending_market = market_view_choice.endswith("values")
        market_table = player_results.sort_values("market_pick_gap", ascending=ascending_market).head(30).copy()
        market_table["Draft cost"] = np.where(
            market_table["draft_type"].eq("snake"),
            market_table["round_pick"].astype(str),
            "$" + market_table["amount"].astype(int).astype(str),
        )
        market_table["ESPN rank"] = "#" + market_table["espn_overall_rank"].round().astype("Int64").astype(str)
        market_table["De facto pick"] = market_table["capital_rank"].round().astype("Int64")
        market_table["Pick gap"] = market_table["market_pick_gap"].round(1)
        market_table["Starter pts / observed wk"] = market_table["starter_points_per_observed_week"].round(1)
        market_table["Roster weeks"] = market_table["roster_weeks"].fillna(0).astype(int)
        market_table["Latest roster week"] = market_table["latest_roster_week"].map(
            lambda value: "Not observed" if pd.isna(value) else str(int(value))
        )
        market_table["Owner"] = market_table["owner"].map(owner_sample_label)
        st.dataframe(
            market_table[
                ["season", "draft_type", "Owner", "player_name", "role", "position", "Draft cost", "De facto pick", "ESPN rank", "Pick gap", "observed_team_weeks", "Roster weeks", "Latest roster week", "Starter pts / observed wk", "median_net_points", "finish_rank"]
            ].rename(
                columns={
                    "season": "Season", "draft_type": "Format", "player_name": "Player", "role": "Role", "position": "Pos",
                    "observed_team_weeks": "Team weeks observed",
                    "median_net_points": "Median net pts", "finish_rank": "Finish",
                }
            ),
            hide_index=True,
            width="stretch",
        )
        st.caption("Positive pick gap means the league drafted the player earlier than ESPN's overall rank. Auction purchases use their price-sorted de facto pick.")

        observed_players = player_results.loc[player_results["observed_team_weeks"].fillna(0).ge(10)].copy()
        if not observed_players.empty:
            observed_players["Owner"] = observed_players["owner"].map(owner_sample_label)
            market_scatter = px.scatter(
                observed_players,
                x="market_pick_gap",
                y="starter_points_per_observed_week",
                color="position",
                color_discrete_map=COLORS,
                hover_name="player_name",
                hover_data={"Owner": True, "season": True, "role": True, "roster_weeks": True, "latest_roster_week": True},
                title="Did the market call turn into starter production? · owners with 10+ captured weeks",
                labels={"market_pick_gap": "De facto picks earlier than ESPN", "starter_points_per_observed_week": "Starter points per observed team-week", "position": "Position"},
            )
            market_scatter.add_vline(x=0, line_dash="dash", line_color="#7E8A96")
            render_plot(market_scatter, "market_outcome_scatter")

        st.markdown("### How did the strategy turn out?")
        outcome_view = selected(data["draft_outcomes"])
        outcome_view = outcome_view.loc[outcome_view["outcome_available"]].copy()
        if outcome_view.empty:
            st.info("Yahoo season outcomes have not been captured for the selected draft seasons yet.")
        else:
            strategy_options = {
                "First QB drafted": "first_qb_capital", "First RB drafted": "first_rb_capital",
                "Second RB drafted": "second_rb_capital", "First WR or TE drafted": "first_wrte_capital",
                "Third WR or TE drafted": "third_wrte_capital", "First TE drafted": "first_te_capital",
                "Second TE drafted": "second_te_capital", "First K drafted": "first_k_capital",
                "First DST drafted": "first_dst_capital",
            }
            outcome_options = {
                "Median points vs weekly median": "median_net_points", "Wins + above-median win rate": "combined_win_pct",
                "All-play win rate": "all_play_win_pct", "Final standings rank": "finish_rank", "Lineup efficiency": "lineup_efficiency",
            }
            sx, sy = st.columns(2)
            x_label = sx.selectbox("Strategy metric", list(strategy_options), key="strategy_x")
            y_label = sy.selectbox("Outcome metric", list(outcome_options), key="strategy_y")
            x_column, y_column = strategy_options[x_label], outcome_options[y_label]
            chart_rows = outcome_view.dropna(subset=[x_column, y_column]).copy()
            chart_rows["Season"] = chart_rows["season"].astype(str)
            chart_rows["owner_label"] = chart_rows["owner"].map(owner_sample_label)
            spread = max(float(chart_rows[x_column].max() - chart_rows[x_column].min()), 1.0)
            rng = np.random.default_rng(2026)
            chart_rows["x_jitter"] = chart_rows[x_column] + rng.normal(0, spread * .018, len(chart_rows))
            strategy_scatter = px.scatter(
                chart_rows,
                x="x_jitter",
                y=y_column,
                color="Season",
                text="owner_label",
                hover_name="owner_label",
                hover_data={"points_per_game": ":.1f", "finish_rank": ":.0f", "all_play_win_pct": ":.1%", "lineup_efficiency": ":.1%"},
                title=f"{x_label} vs {y_label} · {len(chart_rows)} team-seasons",
                labels={"x_jitter": x_label, y_column: y_label},
            )
            strategy_scatter.update_traces(textposition="top center", marker=dict(size=11, line=dict(width=1, color="#D9E5F0")))
            add_linear_trend_with_ci(strategy_scatter, chart_rows, x_column, y_column)
            if y_column in {"all_play_win_pct", "lineup_efficiency", "combined_win_pct"}:
                strategy_scatter.update_yaxes(tickformat=".0%")
            render_plot(strategy_scatter, "strategy_outcome_scatter")
            if y_column == "finish_rank":
                st.caption("For final standings rank, lower is better. These are descriptive relationships from a small historical sample—not causal estimates.")
            else:
                st.caption("These are descriptive relationships from the Yahoo seasons currently captured, not causal estimates. Use the season colors to spot rules or league-size effects.")

with tab_decisions:
    section_title(
        "Start / sit execution",
        "How much scoring was left unused?",
        "Perfect points choose the best legal lineup from active roster and bench players. IR players are excluded from the available pool.",
    )
    if lineup_summary.empty:
        st.info("This view will populate when detailed weekly rosters are captured.")
    else:
        best = lineup_summary.iloc[0]
        regret = lineup_summary.nsmallest(1, "points_left").iloc[0]
        d1, d2, d3 = st.columns(3)
        d1.metric("Best decision efficiency", pct(best.lineup_efficiency), owner_sample_label(best.owner))
        d2.metric("Fewest points left", f"{regret.points_left / regret.weeks_observed:.1f}/wk", owner_sample_label(regret.owner))
        d3.metric("Observed opportunities", f"{int(lineup_summary.weeks_observed.sum())}", "team-weeks")

        summary_chart = lineup_summary.copy()
        summary_chart["Points left / week"] = summary_chart["points_left"] / summary_chart["weeks_observed"]
        summary_chart["Efficiency"] = summary_chart["lineup_efficiency"]
        summary_chart["owner_label"] = summary_chart["owner"].map(owner_sample_label)
        left, right = st.columns(2)
        with left:
            efficiency = px.bar(
                summary_chart.sort_values("Efficiency"),
                x="Efficiency",
                y="owner_label",
                orientation="h",
                color="Efficiency",
                color_continuous_scale=["#C05E85", "#E0B44C", "#6FB1FC"],
                range_color=[max(0.7, summary_chart["Efficiency"].min()), 1],
                text=summary_chart.sort_values("Efficiency")["Efficiency"].map(lambda value: f"{value:.1%}"),
                title="Lineup efficiency",
                labels={"owner_label": "Owner"},
            )
            efficiency.update_xaxes(tickformat=".0%")
            efficiency.update_layout(coloraxis_showscale=False)
            render_plot(efficiency, "efficiency_bar")
        with right:
            regret_chart = px.bar(
                summary_chart.sort_values("Points left / week", ascending=False),
                x="owner_label",
                y="Points left / week",
                color="Points left / week",
                color_continuous_scale=["#6FB1FC", "#E0B44C", "#C05E85"],
                title="Start / sit regret per observed week",
                labels={"owner_label": "Owner"},
            )
            regret_chart.update_layout(coloraxis_showscale=False)
            render_plot(regret_chart, "regret_bar")

        heat = lineup_weeks.pivot_table(index="owner", columns="week", values="points_left", aggfunc="mean")
        average_season_total = (
            lineup_weeks.groupby(["season", "league_id", "team_id", "owner"], as_index=False)["points_left"].sum()
            .groupby("owner")["points_left"].mean()
        )
        heat["Total"] = average_season_total
        heat.index = [owner_sample_label(owner) for owner in heat.index]
        heat.columns = [str(column) for column in heat.columns]
        heat_color = heat.copy()
        heat_color["Total"] = heat_color["Total"] / 18
        heatmap = go.Figure(
            data=go.Heatmap(
                z=heat_color.to_numpy(dtype=float),
                x=heat.columns,
                y=heat.index,
                text=heat.round(0).to_numpy(),
                texttemplate="%{text:.0f}",
                colorscale=[[0, "#14283A"], [.5, "#E0B44C"], [1, "#C05E85"]],
                colorbar=dict(title="Points left / week"),
                customdata=np.broadcast_to(np.array(heat.columns), heat.shape),
                hovertemplate="Owner: %{y}<br>Column: %{customdata}<br>Displayed regret: %{text:.1f}<extra></extra>",
            )
        )
        heatmap.update_layout(title="Weekly regret heatmap · Total shows average season sum")
        render_plot(heatmap, "regret_heatmap")
        st.caption("Week cells are the owner's average regret in that numbered week across the league-seasons selected in the sidebar. Total is the owner's average 18-week season total, not the sum across every season.")

        st.markdown("### Strong bench or costly decisions?")
        decision_weeks = lineup_weeks.copy()
        decision_weeks["weekly_median_bench"] = decision_weeks.groupby(["season", "league_id", "week"])["bench_points"].transform("median")
        decision_weeks["bench_quality"] = decision_weeks["bench_points"] - decision_weeks["weekly_median_bench"]
        model_rows = decision_weeks[["bench_quality", "points_left"]].dropna()
        if len(model_rows) >= 4 and model_rows["bench_quality"].nunique() > 1:
            slope, intercept = np.polyfit(model_rows["bench_quality"], model_rows["points_left"], 1)
            decision_weeks["expected_regret"] = intercept + slope * decision_weeks["bench_quality"]
            decision_weeks["decision_residual"] = decision_weeks["points_left"] - decision_weeks["expected_regret"]
            owner_decisions = decision_weeks.groupby("owner", as_index=False).agg(
                weeks=("week", "size"),
                bench_quality=("bench_quality", "mean"),
                regret_per_week=("points_left", "mean"),
                expected_regret=("expected_regret", "mean"),
                decision_residual=("decision_residual", "mean"),
            )
            owner_decisions["owner_label"] = owner_decisions["owner"].map(owner_sample_label)
            decision_scatter = px.scatter(
                owner_decisions,
                x="bench_quality",
                y="regret_per_week",
                color="decision_residual",
                size="weeks",
                text="owner_label",
                color_continuous_scale=["#6FB1FC", "#1C1F26", "#C05E85"],
                color_continuous_midpoint=0,
                labels={
                    "bench_quality": "Bench points vs league-week median",
                    "regret_per_week": "Points left per week",
                    "decision_residual": "Regret beyond bench expectation",
                },
                title="Bench strength creates opportunity; residual regret isolates execution",
            )
            decision_scatter.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="#D9E5F0")))
            add_linear_trend_with_ci(decision_scatter, owner_decisions, "bench_quality", "regret_per_week")
            render_plot(decision_scatter, "bench_quality_decisions")
            decision_table = owner_decisions.copy()
            decision_table["Owner"] = decision_table["owner_label"]
            for column in ["bench_quality", "regret_per_week", "expected_regret", "decision_residual"]:
                decision_table[column] = decision_table[column].round(1)
            st.dataframe(
                decision_table[
                    ["Owner", "weeks", "bench_quality", "regret_per_week", "expected_regret", "decision_residual"]
                ].rename(
                    columns={
                        "weeks": "Team-weeks", "bench_quality": "Bench pts vs median / wk",
                        "regret_per_week": "Actual regret / wk", "expected_regret": "Expected from bench / wk",
                        "decision_residual": "Owner decision residual / wk",
                    }
                ),
                hide_index=True,
                width="stretch",
            )
            st.caption("A positive residual means more points were left than the league-wide relationship with bench strength predicts; a negative residual means the owner converted a difficult bench better than expected. This is descriptive, not causal.")

        st.markdown("### Would perfect starts make everyone a champion?")
        st.markdown(
            "Not automatically. Perfect decisions can recover individual matchups, but championships also depend on opponent paths and playoff weeks. The table below holds each real opponent score fixed and replaces only that owner's lineup with its best legal combination."
        )
        if not counterfactual.empty:
            cf = counterfactual.copy()
            cf["Owner"] = cf["owner"].map(owner_sample_label)
            for column in ["actual_wins", "perfect_start_wins", "wins_added", "points_left"]:
                cf[column] = cf[column].round(1)
            st.dataframe(
                cf[
                    ["Owner", "comparable_weeks", "actual_wins", "perfect_start_wins", "wins_added", "points_left"]
                ].rename(
                    columns={
                        "comparable_weeks": "Comparable weeks",
                        "actual_wins": "Actual wins",
                        "perfect_start_wins": "Perfect-start wins",
                        "wins_added": "Wins added",
                        "points_left": "Points left",
                    }
                ),
                hide_index=True,
                width="stretch",
            )

with tab_draft:
    section_title(
        "Roster identity",
        "Drafted, traded, or found later",
        "Homegrown means the current owner originally drafted the player. League-drafted also includes players acquired from another owner.",
    )
    if lineups.empty:
        st.info("Draft-retention analysis requires detailed lineup pages.")
    else:
        roster_weekly, decay_summary = roster_decay(lineups, include_draft_baseline=True)
        st.markdown("### Original-roster decay")
        st.caption(
            "Every player on the weekly roster counts—starter, bench, or IR. Homegrown means that owner originally drafted the player. "
            "The chart begins at the 16-player draft-day roster, then measures how many original selections remain on each weekly roster."
        )
        decay_owners = sorted(roster_weekly["owner"].unique(), key=str.casefold)
        default_decay_owner = decay_owners.index("McCade") if "McCade" in decay_owners else 0
        decay_filter_left, decay_filter_right = st.columns(2)
        primary_decay_owner = decay_filter_left.selectbox(
            "Primary owner", decay_owners, index=default_decay_owner,
            format_func=owner_sample_label, key="decay_primary_owner"
        )
        additional_decay_owners = decay_filter_right.multiselect(
            "Add owners",
            [owner for owner in decay_owners if owner != primary_decay_owner],
            default=[],
            format_func=owner_sample_label,
            key="decay_additional_owners",
        )
        shown_decay_owners = [primary_decay_owner, *additional_decay_owners]
        decay_average = (
            roster_weekly.loc[roster_weekly["owner"].isin(shown_decay_owners)]
            .groupby(["owner", "week"], as_index=False)
            .agg(
                homegrown_rostered=("homegrown_rostered", "mean"),
                rostered_players=("rostered_players", "mean"),
                league_drafted_rostered=("league_drafted_rostered", "mean"),
            )
        )
        decay_average["owner_label"] = decay_average["owner"].map(owner_sample_label)
        decay_count = px.line(
            decay_average,
            x="week",
            y="homegrown_rostered",
            color="owner_label",
            markers=True,
            custom_data=["rostered_players", "league_drafted_rostered"],
            title="Average original draftees still rostered by week",
            labels={"week": "Week", "homegrown_rostered": "Original players remaining", "owner_label": "Owner"},
        )
        decay_count.update_traces(
            hovertemplate=(
                "<b>%{fullData.name}</b><br>Week %{x}<br>Original players: %{y:.1f}"
                "<br>Total rostered: %{customdata[0]:.1f}<br>Drafted somewhere: %{customdata[1]:.1f}<extra></extra>"
            )
        )
        decay_count.update_yaxes(dtick=1)
        max_selected_week = int(lineups["week"].max()) if not lineups.empty else 18
        decay_count.update_xaxes(
            tickmode="array",
            tickvals=list(range(max_selected_week + 1)),
            ticktext=["Week 1 baseline", *map(str, range(1, max_selected_week + 1))],
        )
        render_plot(decay_count, "roster_decay_count")
        st.caption("When multiple league-seasons are selected, each owner-week is averaged across those selected drafts.")

        decay_display = decay_summary.copy()
        decay_display["Owner"] = decay_display["owner"].map(owner_sample_label)
        decay_display["latest_homegrown_share"] = decay_display["latest_homegrown_share"].map(pct)
        st.dataframe(
            decay_display[
                [
                    "Owner", "weeks_observed", "first_week", "latest_week", "homegrown_first",
                    "homegrown_latest", "players_replaced", "latest_homegrown_share",
                    "latest_league_drafted", "coverage_note",
                ]
            ].rename(
                columns={
                    "weeks_observed": "Weeks observed",
                    "first_week": "First week",
                    "latest_week": "Latest week",
                    "homegrown_first": "Original at first look",
                    "homegrown_latest": "Original at latest look",
                    "players_replaced": "Net original players lost",
                    "latest_homegrown_share": "Latest original share",
                    "latest_league_drafted": "Latest drafted somewhere",
                    "coverage_note": "Coverage",
                }
            ),
            hide_index=True,
            width="stretch",
        )

        st.markdown("### Starter identity")
        starter_week_choice = st.selectbox(
            "Starter week",
            ["All selected weeks", *range(1, max_selected_week + 1)],
            key="starter_identity_week",
        )
        starters = lineups.loc[lineups["is_starter"]].copy()
        if starter_week_choice != "All selected weeks":
            starters = starters.loc[starters["week"].eq(starter_week_choice)]
        shares = starters.groupby("owner", as_index=False).agg(
            homegrown=("drafted_by_owner", "mean"), league_drafted=("drafted_in_league", "mean"), starts=("player_name", "size")
        )
        shares["owner_label"] = shares["owner"].map(owner_sample_label)
        shares_long = shares.melt(
            id_vars=["owner", "owner_label", "starts"], value_vars=["homegrown", "league_drafted"], var_name="Measure", value_name="Share"
        )
        shares_long["Measure"] = shares_long["Measure"].map(
            {"homegrown": "Drafted by current owner", "league_drafted": "Drafted somewhere in league"}
        )
        retention = px.bar(
            shares_long,
            x="owner_label",
            y="Share",
            color="Measure",
            barmode="group",
            color_discrete_map={"Drafted by current owner": "#6FB1FC", "Drafted somewhere in league": "#73C3A6"},
            text=shares_long["Share"].map(lambda value: f"{value:.0%}"),
            title=f"Who was still starting drafted players? · {starter_week_choice}",
            labels={"owner_label": "Owner"},
        )
        retention.update_yaxes(tickformat=".0%", range=[0, 1.05])
        render_plot(retention, "draft_retention")

        origin = starters.groupby(["owner", "player_origin"], as_index=False)["fan_points"].sum()
        origin["share"] = origin["fan_points"] / origin.groupby("owner")["fan_points"].transform("sum")
        origin["owner_label"] = origin["owner"].map(owner_sample_label)
        origin_chart = px.bar(
            origin,
            x="owner_label",
            y="share",
            color="player_origin",
            color_discrete_map={
                "Drafted by current owner": "#6FB1FC",
                "Drafted by another owner": "#8A7CC7",
                "Undrafted / unmatched": "#E0B44C",
            },
            text=origin["share"].map(lambda value: f"{value:.0%}" if value >= .05 else ""),
            title="Source of observed starter points",
            labels={"owner_label": "Owner", "share": "Share of points", "player_origin": "Player origin"},
        )
        origin_chart.update_yaxes(tickformat=".0%")
        render_plot(origin_chart, "origin_points")

with tab_coverage:
    section_title(
        "Audit trail",
        "What is complete—and what is not",
        "The app never fills missing Yahoo pages with assumptions. Every visual is generated from the captured rows shown here.",
    )
    st.caption("Fantasy data provided by Yahoo Fantasy.")
    coverage = coverage_summary(data["lineups"], data["scores"])
    coverage["League"] = coverage.apply(lambda row: f"{row.season} {str(row.draft_type).title()} · {row.league_id}", axis=1)
    coverage_chart = px.bar(
        coverage,
        x="League",
        y="lineup_coverage",
        color="draft_type",
        text=coverage["lineup_coverage"].map(lambda value: f"{value:.0%}"),
        color_discrete_map={"snake": "#6FB1FC", "auction": "#CC8C4A"},
        title="Detailed lineup pages captured out of each season's expected weeks",
        labels={"lineup_coverage": "Coverage", "draft_type": "Draft format"},
    )
    coverage_chart.update_yaxes(tickformat=".0%", range=[0, 1.05])
    render_plot(coverage_chart, "coverage_chart")

    inventory = data["inventory"].copy()
    inventory["league"] = inventory.apply(
        lambda row: f"{row['season']} · {str(row['draft_type']).title() if row['draft_type'] else 'Pending'} · {row['league_id']}", axis=1
    )
    st.dataframe(
        inventory[["league", "team_count", "schedule_teams", "week1_teams", "detailed_lineup_pages", "status", "notes"]].rename(
            columns={
                "league": "League",
                "team_count": "Teams",
                "schedule_teams": "Schedules",
                "week1_teams": "Week 1 rosters",
                "detailed_lineup_pages": "Lineup pages",
                "status": "Status",
                "notes": "Notes",
            }
        ),
        hide_index=True,
        width="stretch",
    )

    with st.expander("Metric definitions"):
        st.markdown(
            """
- **Lineup efficiency:** actual starter points divided by the best legal score available from starters and bench. IR is excluded.
- **Points left:** best legal score minus actual starter score; it is not the sum of every bench player's points.
- **All-play win rate:** average percentage of league opponents beaten by the team's score each week.
- **Schedule luck:** actual win rate minus all-play win rate over the same observed matchup weeks.
- **Homegrown starter:** a starter originally drafted by the same owner in that league-season.
- **League-drafted starter:** a starter found anywhere in that league's draft, including players later traded.
"""
        )

st.caption("Smack Talkers League Lab · local Yahoo history · scoring and roster coverage updated from checkpointed league pages")
