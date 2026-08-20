from __future__ import annotations

import random
import ast
import re
from collections import Counter

import streamlit as st

from game import (
    POWER_UPS,
    SIGNS,
    apply_sign,
    apply_powerup,
    blackjack_result,
    blackjack_is_soft,
    blackjack_outcome,
    blackjack_score,
    blackjack_value,
    build_hidden_players,
    dealer_play,
    dice_delta,
    draw_blackjack_card,
    finish_hidden_players,
    fourth_quarter_result,
    overtime_result,
    simulate_game,
)

st.set_page_config(page_title="Smack Talkers Draft", page_icon="🏆", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Oswald:wght@600;700&display=swap');
:root { --navy:#061a35; --navy2:#0c2a50; --gold:#f3bd3d; --lime:#88d940; --paper:#f7f5ef; }
.stApp { background: radial-gradient(circle at 50% -20%, #153b68 0, #071a34 42%, #041226 100%); color:#f7f8fb; }
.block-container { max-width:1120px; padding-top:1.3rem; padding-bottom:5rem; }
html, body, [class*="css"] { font-family:'Inter',sans-serif; }
h1,h2,h3 { font-family:'Oswald',sans-serif !important; letter-spacing:.02em; }
.hero { border:1px solid rgba(243,189,61,.7); border-radius:20px; padding:2.2rem 2rem 1.7rem; text-align:center;
 background:linear-gradient(135deg,rgba(6,26,53,.96),rgba(14,47,84,.95)); box-shadow:0 24px 80px rgba(0,0,0,.35); margin-bottom:1rem; }
.hero .kicker { color:var(--gold); font-family:'Oswald'; font-size:1.05rem; letter-spacing:.2em; text-transform:uppercase; }
.hero h1 { font-size:clamp(2.4rem,6vw,5rem); line-height:.95; margin:.35rem 0; color:#fff; text-shadow:0 3px 0 #000; }
.hero .tag { color:var(--lime); font-weight:800; letter-spacing:.11em; }
.score-ribbon { position:sticky; top:2.8rem; z-index:99; background:rgba(6,26,53,.94); backdrop-filter:blur(12px); border:1px solid rgba(243,189,61,.55); border-radius:14px; padding:.7rem 1rem; margin:.8rem 0 1rem; display:flex; justify-content:space-between; box-shadow:0 10px 30px rgba(0,0,0,.25); }
.score-ribbon span { color:#b9c7d9; font-size:.8rem; text-transform:uppercase; letter-spacing:.08em; }
.score-ribbon strong { color:var(--gold); font-size:1.3rem; }
div[data-testid="stExpander"] { border:1px solid rgba(255,255,255,.16); border-radius:14px; background:rgba(255,255,255,.055); margin:.65rem 0; overflow:hidden; box-shadow:0 10px 25px rgba(0,0,0,.12); }
div[data-testid="stExpander"] summary { font-family:'Oswald'; font-size:1.15rem; letter-spacing:.04em; padding:.9rem 1rem; }
.rule { color:#c7d4e5; line-height:1.65; }
.pill { display:inline-block; border:1px solid rgba(243,189,61,.5); background:rgba(243,189,61,.1); color:#ffd66f; border-radius:999px; padding:.24rem .65rem; margin:.15rem; font-size:.78rem; font-weight:700; }
.done { color:#9be35e; font-weight:700; }
.result-card { background:linear-gradient(135deg,#faf8f1,#e8edf5); color:#0b2342; border-radius:18px; padding:2rem; box-shadow:0 20px 60px rgba(0,0,0,.35); margin-top:1.2rem; border:3px solid #e3ad2d; }
.final-number { font-family:'Oswald'; color:#a76b00; font-size:4rem; line-height:1; }
.timeline { border-left:2px solid #d7a62f; padding-left:1rem; line-height:1.85; }
.score-flow { display:flex; gap:.5rem; overflow-x:auto; padding:.45rem 0 1rem; }
.score-step { min-width:145px; padding:.7rem .85rem; border-radius:11px; background:rgba(255,255,255,.09); border:1px solid rgba(255,255,255,.14); }
.score-step small { color:#b9c7d9; display:block; font-weight:700; text-transform:uppercase; font-size:.67rem; }
.score-step b { color:#fff; font-size:1.1rem; }
.draw-row { display:flex; gap:1rem; flex-wrap:wrap; margin:.8rem 0 1rem; }
.draw-card { width:150px; min-height:175px; border-radius:16px; background:linear-gradient(145deg,#fff,#e8edf5); color:#08213f; border:3px solid #efbd42; box-shadow:0 12px 28px rgba(0,0,0,.3); display:flex; flex-direction:column; justify-content:center; align-items:center; }
.draw-card small { text-transform:uppercase; letter-spacing:.12em; font-weight:800; color:#617086; }
.draw-card strong { font-family:'Oswald'; font-size:3.6rem; line-height:1; }
.bj-table { background:radial-gradient(ellipse at center,#117040,#064729); border:9px solid #6f4728; border-radius:120px 120px 28px 28px; padding:2rem 1rem 1.2rem; box-shadow:inset 0 0 40px rgba(0,0,0,.35),0 18px 40px rgba(0,0,0,.3); }
.bj-seats { display:grid; grid-template-columns:repeat(6,1fr); gap:.65rem; }
.bj-seat { text-align:center; color:#fff; font-size:.72rem; min-height:92px; }
.playing-card { display:inline-flex; width:34px; height:48px; margin:2px; border-radius:5px; background:#fff; color:#111; align-items:center; justify-content:center; font-weight:800; box-shadow:0 3px 8px rgba(0,0,0,.35); }
[data-testid="stMetricValue"] { color:#f3bd3d; }
.stButton>button { border-radius:10px; font-weight:700; }
footer { visibility:hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def fresh_state(seed: int | None = None) -> dict:
    seed = seed if seed is not None else random.SystemRandom().randint(1, 999_999)
    opponents, user_sign = build_hidden_players(seed)
    return {
        "seed": seed,
        "rng": random.Random(seed),
        "score": None,
        "history": [],
        "completed": set(),
        "sign_deck": [s for s in SIGNS for _ in range(3)],
        "user_sign": user_sign,
        "opponents": opponents,
        "opponents_finished": False,
        "auction_results": [],
        "auction_reveal_count": 0,
        "view_stage": "Pre-Game",
        "user_reveals": {},
        "powerups": [],
        "redo": False,
        "bj_player": [],
        "bj_dealer": [],
        "table_bj": [],
        "blackjack_resolved": False,
        "bj_reveal_count": 2,
        "bj_turn": None,
        "bj_user_playing": False,
        "bj_dealer_revealed": False,
        "dice": [],
        "q4_pending": None,
        "q4_reveal_player": 0,
        "q4_reveal_phase": 0,
        "ot_pending": None,
    }


if "game" not in st.session_state:
    st.session_state.game = fresh_state()
g = st.session_state.game
if "opponents" not in g or "view_stage" not in g or "table_bj" not in g:
    st.session_state.game = fresh_state(g.get("seed"))
    st.rerun()
for key, default in {
    "auction_reveal_count": 0,
    "user_reveals": {},
    "bj_reveal_count": 2,
    "bj_turn": None,
    "bj_user_playing": False,
    "bj_dealer_revealed": False,
    "q4_pending": None,
    "q4_reveal_player": 0,
    "q4_reveal_phase": 0,
    "ot_pending": None,
    "blackjack_resolved": False,
}.items():
    g.setdefault(key, default)


def record(stage: str, before: float | None, after: float, detail: str) -> None:
    g["score"] = after
    g["history"].append({"stage": stage, "before": before, "after": after, "detail": detail})
    g["completed"].add(stage)
    g["view_stage"] = stage


def stage_title(number: int, name: str, key: str) -> str:
    mark = "✓" if key in g["completed"] else f"{number:02d}"
    return f"{mark}  {name}"


def fmt(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.4f}".rstrip("0").rstrip(".")


def reveal_opponent_stage(stage: str, heading: str = "Table reveal") -> None:
    rows = []
    for player in g["opponents"]:
        events = [event for event in player["path"] if event["stage"] == stage]
        if events:
            event = events[-1]
            if stage in ("First Quarter", "Second Quarter"):
                reveal = "DRAW" if event["detail"].startswith("drew") else "KEEP"
            else:
                reveal = " | ".join(item["detail"] for item in events)
            rows.append({"Player": player["name"], "Reveal": reveal, "Score": "SEALED"})
    if rows:
        st.markdown(f"#### {heading}")
        st.dataframe(rows, hide_index=True, use_container_width=True, height=455)


def draw_tiles(items: list[tuple[str, str]]) -> None:
    cards = "".join(f'<div class="draw-card"><small>{label}</small><strong>{value}</strong></div>' for label, value in items)
    st.markdown(f'<div class="draw-row">{cards}</div>', unsafe_allow_html=True)


def q4_columns(event: dict) -> dict:
    """Normalize current and pre-update Q4 events without resetting an active game."""
    if all(key in event for key in ("multiplier", "quantity", "dice", "adjustment")):
        return event
    match = re.search(r"rolled\s+(\[[^\]]*\]);\s*([+-]?\d+)\s*[×x]\s*(\d+)", event.get("detail", ""))
    if not match:
        return {"multiplier": "—", "quantity": "—", "dice": [], "adjustment": "—", "redo_used": "redo" in event.get("detail", "").lower()}
    dice = ast.literal_eval(match.group(1))
    base, multiplier = int(match.group(2)), int(match.group(3))
    return {"multiplier": multiplier, "quantity": len(dice), "dice": dice, "adjustment": base * multiplier, "redo_used": "redo" in event.get("detail", "").lower()}


def start_blackjack_table(user_plays: bool) -> None:
    g["bj_dealer"] = [draw_blackjack_card(g["rng"]), draw_blackjack_card(g["rng"])]
    g["bj_user_playing"] = user_plays
    g["bj_dealer_revealed"] = False
    if user_plays:
        g["bj_player"] = [draw_blackjack_card(g["rng"]), draw_blackjack_card(g["rng"])]
    seats = []
    for player in g["opponents"]:
        playing = g["rng"].random() < 0.72
        hand = []
        if playing:
            hand = [draw_blackjack_card(g["rng"]), draw_blackjack_card(g["rng"])]
        seats.append({"name": player["name"], "playing": playing, "hand": hand, "stood": False})
    g["table_bj"] = seats
    g["bj_turn"] = 0 if user_plays else next_blackjack_turn(1)


def next_blackjack_turn(start: int) -> int:
    """Turn 0 is You, 1–11 are opponents, and 12 is the dealer."""
    turn = start
    while 1 <= turn <= 11 and not g["table_bj"][turn - 1]["playing"]:
        turn += 1
    return min(turn, 12)


def render_blackjack_table() -> None:
    dealer_cards = [g["bj_dealer"][0]]
    if g["bj_dealer_revealed"] or g["blackjack_resolved"]:
        dealer_cards = g["bj_dealer"]
    dealer_html = "".join(f'<span class="playing-card">{"A" if card == 11 else card}</span>' for card in dealer_cards)
    seats_html = []
    for seat in g["table_bj"]:
        cards = "".join(f'<span class="playing-card">{"A" if card == 11 else card}</span>' for card in seat["hand"])
        status = "KEEP" if not seat["playing"] else ("BUST" if blackjack_value(seat["hand"]) > 21 else "PLAY")
        seats_html.append(f'<div class="bj-seat"><b>{seat["name"]}</b><br>{cards or "—"}<br>{status}</div>')
    user_cards = "".join(f'<span class="playing-card">{"A" if card == 11 else card}</span>' for card in g["bj_player"])
    user_html = f'<div class="bj-seat"><b>YOU</b><br>{user_cards or "—"}<br>{"PLAY" if g["bj_user_playing"] else "KEEP"}</div>'
    st.markdown(f'<div class="bj-table"><div style="text-align:center;color:#f7d36c;font-weight:800;margin-bottom:1rem">DEALER<br>{dealer_html}</div><div class="bj-seats">{user_html}{"".join(seats_html)}</div></div>', unsafe_allow_html=True)


def resolve_blackjack_table() -> None:
    for seat, player in zip(g["table_bj"], g["opponents"]):
        if seat["playing"]:
            outcome = blackjack_outcome(seat["hand"], g["bj_dealer"])
            player["score"] = blackjack_score(player["score"], seat["hand"], outcome)
            detail = f"{outcome} with {seat['hand']} ({blackjack_value(seat['hand'])})"
        else:
            detail = "kept; sat out"
        player["path"].append({"stage": "Halftime", "detail": detail, "score": player["score"]})
    g["blackjack_resolved"] = True


st.markdown("""
<div class="hero"><div class="kicker">31st Annual</div><h1>SMACK TALKERS DRAFT</h1>
<div class="tag">LOWER SCORE = BETTER PICK</div><p>Solo rules lab · deliberate play · endless replays</p></div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Game controls")
    seed_input = st.number_input("Random seed", 1, 999_999, int(g["seed"]), help="Reuse a seed to replay the same random sequence.")
    if st.button("↻ Start a new game", type="primary", use_container_width=True):
        st.session_state.game = fresh_state(int(seed_input))
        st.rerun()
    st.caption(f"Seed {g['seed']} · {len(g['completed'])}/7 stages complete")
    st.progress(len(g["completed"]) / 7)
    if g["history"]:
        st.divider()
        st.subheader("Score trail")
        for event in g["history"]:
            st.caption(f"{event['stage']}: {fmt(event['before'])} → {fmt(event['after'])}")

score_text = fmt(g["score"])
st.markdown(f'<div class="score-ribbon"><div><span>Current score</span><br><strong>{score_text}</strong></div><div style="text-align:right"><span>Progress</span><br><strong>{len(g["completed"])} / 7</strong></div></div>', unsafe_allow_html=True)
if g["history"]:
    flow = "".join(f'<div class="score-step"><small>{e["stage"]}</small><b>{fmt(e["after"])}</b></div>' for e in g["history"])
    st.markdown(f'<div class="score-flow">{flow}</div>', unsafe_allow_html=True)

with st.expander(stage_title(1, "PRE-GAME · Secret starting score", "Pre-Game"), expanded=g["view_stage"] == "Pre-Game"):
    st.markdown('<p class="rule">Draw one number from <b>21–100</b>. This is your starting score. Keep it secret from the table.</p>', unsafe_allow_html=True)
    st.info("12-player table seated: **You + 11 hidden opponents**. Their decisions remain sealed until Final Results.")
    if "Pre-Game" not in g["completed"]:
        mode = st.radio("Starting method", ["Draw for me", "Enter a physical draw"], horizontal=True)
        manual = st.number_input("Starting number", 21, 100, 50, disabled=mode == "Draw for me")
        if st.button("Reveal starting score", type="primary"):
            start = g["rng"].randint(21, 100) if mode == "Draw for me" else manual
            g["user_reveals"]["Pre-Game"] = [("Starting score", str(start))]
            record("Pre-Game", None, start, f"Starting draw: {start}")
            st.rerun()
    else:
        st.success(f"Starting score: {g['history'][0]['after']}")
        draw_tiles(g["user_reveals"].get("Pre-Game", [("Starting score", fmt(g["score"]))]))

with st.expander(stage_title(2, "FIRST QUARTER · Keep or draw", "First Quarter"), expanded=g["view_stage"] == "First Quarter"):
    st.markdown('<p class="rule"><b>KEEP</b> your score, or <b>DRAW</b> a new number from 1–100. The choice is final.</p>', unsafe_allow_html=True)
    if "Pre-Game" not in g["completed"]:
        st.info("Complete Pre-Game first.")
    elif "First Quarter" not in g["completed"]:
        c1, c2 = st.columns(2)
        if c1.button("Keep my score", use_container_width=True):
            missed = g["rng"].randint(1, 100)
            g["user_reveals"]["First Quarter"] = [("Passed-up draw", str(missed))]
            record("First Quarter", g["score"], g["score"], f"Kept. Annoyingly, the draw would have been {missed}.")
            st.rerun()
        if c2.button("Draw 1–100", type="primary", use_container_width=True):
            before = g["score"]
            new = g["rng"].randint(1, 100)
            g["user_reveals"]["First Quarter"] = [("New score", str(new))]
            record("First Quarter", before, new, f"Drew {new}")
            st.rerun()
    else:
        q1_detail = next(x["detail"] for x in g["history"] if x["stage"] == "First Quarter")
        (st.warning if "Annoyingly" in q1_detail else st.success)(q1_detail)
        draw_tiles(g["user_reveals"].get("First Quarter", []))
        reveal_opponent_stage("First Quarter", "The other 11 players reveal their choices")

with st.expander(stage_title(3, "SECOND QUARTER · Sign & card", "Second Quarter"), expanded=g["view_stage"] == "Second Quarter"):
    counts = Counter(g["sign_deck"])
    st.markdown("".join(f'<span class="pill">{s} × {counts[s]}</span>' for s in SIGNS), unsafe_allow_html=True)
    st.caption("Shared card pool: exactly 12 total — three MIN, three MAX, three ABS, and three SUM. This solo run consumes one.")
    if "First Quarter" not in g["completed"]:
        st.info("Complete First Quarter first.")
    elif "Second Quarter" not in g["completed"]:
        action = st.radio("Choose", ["Keep", "Draw a sign + number"], horizontal=True)
        if action == "Draw a sign + number":
            st.markdown('<p class="rule"><b>MIN</b> smaller · <b>MAX</b> larger · <b>ABS</b> absolute difference · <b>SUM</b> addition</p>', unsafe_allow_html=True)
        if st.button("Lock Second Quarter", type="primary"):
            before = g["score"]
            if action == "Keep":
                missed_card = g["rng"].randint(1, 100)
                missed_score = apply_sign(before, missed_card, g["user_sign"])
                g["user_reveals"]["Second Quarter"] = [("Passed-up sign", g["user_sign"]), ("Passed-up card", str(missed_card))]
                record("Second Quarter", before, before, f"Kept. Annoyingly, {g['user_sign']} + {missed_card} would have made {fmt(missed_score)}.")
            else:
                sign = g["user_sign"]
                g["sign_deck"].remove(sign)
                new = g["rng"].randint(1, 100)
                after = apply_sign(before, new, sign)
                g["user_reveals"]["Second Quarter"] = [("Sign", sign), ("Number", str(new))]
                record("Second Quarter", before, after, f"Drew {sign} and {new}: {before} → {after}")
            st.rerun()
    elif len(g["history"]) > 2:
        q2_detail = next(x["detail"] for x in g["history"] if x["stage"] == "Second Quarter")
        (st.warning if "Annoyingly" in q2_detail else st.success)(q2_detail)
        draw_tiles(g["user_reveals"].get("Second Quarter", []))
        reveal_opponent_stage("Second Quarter", "All Sign & Card choices revealed")

with st.expander(stage_title(4, "HALFTIME · Blackjack", "Halftime"), expanded=g["view_stage"] == "Halftime"):
    st.markdown('<p class="rule">Beat the shared dealer: a two-card 21 divides by <b>3</b>; another win divides by <b>2</b>; a loss doubles; a push changes nothing. Turns run You → Player 2…12 → Dealer. Dealer hits soft 17.</p>', unsafe_allow_html=True)
    if "Second Quarter" not in g["completed"]:
        st.info("Complete Second Quarter first.")
    elif "Halftime" not in g["completed"]:
        if not g["table_bj"]:
            c1, c2 = st.columns(2)
            if c1.button("Keep score", use_container_width=True):
                start_blackjack_table(False)
                st.rerun()
            if c2.button("Deal blackjack", type="primary", use_container_width=True):
                start_blackjack_table(True)
                st.rerun()
        else:
            playing_count = int(g["bj_user_playing"]) + sum(seat["playing"] for seat in g["table_bj"])
            st.markdown(f"#### Shared table · {playing_count} of 12 players are in")
            render_blackjack_table()
            turn = g["bj_turn"]
            if turn == 0:
                total = blackjack_value(g["bj_player"])
                st.markdown(f"### Your turn · total {total}")
                c1, c2 = st.columns(2)
                if total < 21 and c1.button("Deal me one card", type="primary", use_container_width=True):
                    g["bj_player"].append(draw_blackjack_card(g["rng"]))
                    if blackjack_value(g["bj_player"]) >= 21:
                        g["bj_turn"] = next_blackjack_turn(1)
                    st.rerun()
                if c2.button("Stand" if total <= 21 else "Continue after bust", use_container_width=True):
                    g["bj_turn"] = next_blackjack_turn(1)
                    st.rerun()
            elif 1 <= turn <= 11:
                seat = g["table_bj"][turn - 1]
                total = blackjack_value(seat["hand"])
                st.markdown(f"### {seat['name']}'s turn · total {total}")
                if total < 17:
                    if st.button(f"Deal one card to {seat['name']}", type="primary", use_container_width=True):
                        seat["hand"].append(draw_blackjack_card(g["rng"]))
                        if blackjack_value(seat["hand"]) >= 17:
                            seat["stood"] = blackjack_value(seat["hand"]) <= 21
                            g["bj_turn"] = next_blackjack_turn(turn + 1)
                        st.rerun()
                elif st.button(f"{seat['name']} stands · continue", type="primary", use_container_width=True):
                    seat["stood"] = True
                    g["bj_turn"] = next_blackjack_turn(turn + 1)
                    st.rerun()
            else:
                st.markdown("### Dealer's turn")
                if not g["bj_dealer_revealed"]:
                    if st.button("Reveal dealer hole card", type="primary", use_container_width=True):
                        g["bj_dealer_revealed"] = True
                        st.rerun()
                else:
                    dealer_total = blackjack_value(g["bj_dealer"])
                    must_hit = dealer_total < 17 or (dealer_total == 17 and blackjack_is_soft(g["bj_dealer"]))
                    if must_hit:
                        if st.button("Deal one card to dealer", type="primary", use_container_width=True):
                            g["bj_dealer"].append(draw_blackjack_card(g["rng"]))
                            st.rerun()
                    elif st.button("Settle every hand", type="primary", use_container_width=True):
                        before = g["score"]
                        resolve_blackjack_table()
                        if g["bj_user_playing"]:
                            outcome = blackjack_outcome(g["bj_player"], g["bj_dealer"])
                            after = blackjack_score(before, g["bj_player"], outcome)
                            detail = f"{outcome.title()}: you {blackjack_value(g['bj_player'])}, dealer {blackjack_value(g['bj_dealer'])}"
                        else:
                            after, detail = before, "Kept score; watched the shared table"
                        record("Halftime", before, after, detail)
                        st.rerun()
    else:
        halftime_detail = next(x["detail"] for x in g["history"] if x["stage"] == "Halftime")
        if halftime_detail.startswith("Loss"):
            st.error(halftime_detail)
        elif halftime_detail.startswith("Push"):
            st.info(halftime_detail)
        else:
            st.success(halftime_detail)
        render_blackjack_table()
        st.caption(f"Dealer total {blackjack_value(g['bj_dealer'])} · complete table remains visible")
        reveal_opponent_stage("Halftime", "Shared-dealer results for all 11 opponents")

with st.expander(stage_title(5, "THIRD QUARTER · Blind auction", "Third Quarter"), expanded=g["view_stage"] == "Third Quarter"):
    st.markdown('<p class="rule">Five Power-Ups are auctioned. Enter a secret bid for each; a simulated table sets the opposing high bid. Winners add their bid immediately, then apply the power-up.</p>', unsafe_allow_html=True)
    if "Halftime" not in g["completed"]:
        st.info("Complete Halftime first.")
    elif "Third Quarter" not in g["completed"]:
        bids = {}
        for i, power in enumerate(POWER_UPS):
            bids[i] = st.number_input(power, 0, 100, 0, key=f"bid_{i}", help="0 passes on this item.")
        if st.button("Run all five auctions", type="primary"):
            before = g["score"]
            score = before
            results = []
            user_bids = {power: int(bids[i]) for i, power in enumerate(POWER_UPS)}
            for i, power in enumerate(POWER_UPS):
                table = [("You", user_bids[power])] + [(p["name"], p["bids"][power]) for p in g["opponents"]]
                high = max(value for _, value in table)
                tied = [name for name, value in table if value == high]
                winner = g["rng"].choice(tied)
                result = {"power": power, "your_bid": user_bids[power], "winner": winner, "winning_bid": high, "bids": table}
                if winner == "You" and high > 0:
                    score, effect = apply_powerup(score, i, high, g["rng"])
                    result["effect"] = effect
                    g["powerups"].append(power)
                    if i == 4:
                        g["redo"] = True
                results.append(result)
            g["auction_results"] = results
            auction_winners = {result["power"]: result["winner"] for result in results}
            g["opponents"] = finish_hidden_players(g["opponents"], user_bids, g["rng"], auction_winners)
            for i, result in enumerate(results):
                effect = result.get("effect", "")
                if result["winner"] != "You":
                    winner_player = next(player for player in g["opponents"] if player["name"] == result["winner"])
                    matching = [event["detail"] for event in winner_player["path"] if event["stage"] == "Third Quarter" and result["power"] in event["detail"]]
                    effect = matching[-1] if matching else ""
                if i == 2 and result["winner"] == "You":
                    result["public_effect"] = "Your private result: " + effect
                elif i in (0, 2):
                    result["public_effect"] = "Effect and resulting score remain hidden."
                elif i == 1:
                    result["public_effect"] = effect
                elif i == 3:
                    result["public_effect"] = f"Visible effect: score becomes 10 + bid {result['winning_bid']}."
                else:
                    result["public_effect"] = "Visible effect: one redo is banked for Fourth Quarter or Overtime."
            g["opponents_finished"] = True
            g["auction_reveal_count"] = 1
            wins = [f"{r['power']} ({r['winning_bid']})" for r in results if r["winner"] == "You"]
            record("Third Quarter", before, score, "Won: " + (", ".join(wins) if wins else "none"))
            st.rerun()
    else:
        st.success(next(x["detail"] for x in g["history"] if x["stage"] == "Third Quarter"))
        shown_results = g["auction_results"][: g["auction_reveal_count"]]
        for auction_number, result in enumerate(shown_results, 1):
            with st.container(border=True):
                st.markdown(f"### Auction {auction_number} · {result['power']}")
                st.markdown(f"**{result['winner']}** won with **{result['winning_bid']}**. Your bid: **{result['your_bid']}**")
                st.info(result["public_effect"])
                st.caption("All bids: " + " · ".join(f"{name}: {bid}" for name, bid in result["bids"]))
        if g["auction_reveal_count"] < len(g["auction_results"]):
            next_power = g["auction_results"][g["auction_reveal_count"]]["power"]
            if st.button(f"Reveal next auction · {next_power}", type="primary"):
                g["auction_reveal_count"] += 1
                st.rerun()

with st.expander(stage_title(6, "FOURTH QUARTER · Dice & color", "Fourth Quarter"), expanded=g["view_stage"] == "Fourth Quarter"):
    st.markdown('<p class="rule">Pick 1–6 dice and a color multiplier. A face appearing once subtracts its value. A face appearing two or more times adds its value for every appearance. Final delta = result × multiplier.</p>', unsafe_allow_html=True)
    if "Third Quarter" not in g["completed"]:
        st.info("Complete Third Quarter first.")
    elif "Fourth Quarter" not in g["completed"]:
        if g["q4_pending"] is None:
            c1, c2 = st.columns(2)
            n_dice = c1.select_slider("Number of dice", options=list(range(1, 7)), value=3)
            color = c2.selectbox("Color / multiplier", ["White ×1", "Blue ×2", "Green ×3", "Purple ×4", "Black ×5"])
            multiplier = [1, 2, 3, 4, 5][["White ×1", "Blue ×2", "Green ×3", "Purple ×4", "Black ×5"].index(color)]
            if st.button("Lock choices & start rolling", type="primary"):
                g["q4_pending"] = {"quantity": n_dice, "multiplier": multiplier, "rolls": [g["rng"].randint(1, 6) for _ in range(n_dice)], "revealed": 0, "redo_note": ""}
                st.rerun()
        else:
            pending = g["q4_pending"]
            visible = pending["rolls"][: pending["revealed"]]
            running_adjustment = dice_delta(visible) * pending["multiplier"] if visible else 0
            q1, q2, q3, q4 = st.columns(4)
            q1.metric("Multiplier", f"×{pending['multiplier']}")
            q2.metric("Dice quantity", pending["quantity"])
            q3.metric("Dice revealed", str(visible) if visible else "—")
            q4.metric("Live adjustment", f"{running_adjustment:+d}")
            if pending["revealed"] < pending["quantity"]:
                if st.button(f"Watch die {pending['revealed'] + 1} roll", type="primary", use_container_width=True):
                    pending["revealed"] += 1
                    st.rerun()
            else:
                if g["redo"] and st.button("Use banked redo · reroll all dice", use_container_width=True):
                    old = pending["rolls"]
                    pending["rolls"] = [g["rng"].randint(1, 6) for _ in range(pending["quantity"])]
                    pending["revealed"] = 0
                    pending["redo_note"] = f"Used redo on {old}; "
                    g["redo"] = False
                    st.rerun()
                if st.button("Apply Fourth Quarter adjustment", type="primary", use_container_width=True):
                    before = g["score"]
                    g["dice"] = pending["rolls"]
                    adjustment = dice_delta(g["dice"]) * pending["multiplier"]
                    after = before + adjustment
                    record("Fourth Quarter", before, after, f"{pending['redo_note']}rolled {g['dice']}; {dice_delta(g['dice']):+d} × {pending['multiplier']} = {adjustment:+d}")
                    st.rerun()
    else:
        st.success(next(x["detail"] for x in g["history"] if x["stage"] == "Fourth Quarter"))
        user_pending = g.get("q4_pending") or {}
        user_multiplier = user_pending.get("multiplier", "—")
        user_quantity = user_pending.get("quantity", len(g.get("dice", [])))
        user_rolls = g.get("dice", [])
        user_adjustment = dice_delta(user_rolls) * user_multiplier if isinstance(user_multiplier, int) else "—"
        q4_rows = [{
            "Player": "You",
            "Multiplier": f"×{user_multiplier}" if isinstance(user_multiplier, int) else user_multiplier,
            "Dice quantity": user_quantity,
            "Dice rolled": str(user_rolls),
            "Adjustment": f"{user_adjustment:+d}" if isinstance(user_adjustment, int) else user_adjustment,
            "Redo used": "YES" if user_pending.get("redo_note") else "NO",
            "Score": fmt(g["score"]),
        }]
        reveal_index = g["q4_reveal_player"]
        reveal_phase = g["q4_reveal_phase"]
        for index, player in enumerate(g["opponents"]):
            if index > reveal_index or (index == reveal_index and reveal_phase == 0):
                break
            event = next(event for event in player["path"] if event["stage"] == "Fourth Quarter")
            columns = q4_columns(event)
            roll_visible = index < reveal_index
            adjustment = f"{columns['adjustment']:+d}" if roll_visible and isinstance(columns["adjustment"], int) else "HIDDEN"
            multiplier = f"×{columns['multiplier']}" if isinstance(columns["multiplier"], int) else columns["multiplier"]
            q4_rows.append({"Player": player["name"], "Multiplier": multiplier, "Dice quantity": columns["quantity"], "Dice rolled": str(columns["dice"]) if roll_visible else "HIDDEN", "Adjustment": adjustment, "Redo used": ("YES" if columns.get("redo_used") else "NO") if roll_visible else "HIDDEN", "Score": "SEALED"})
        if q4_rows:
            st.dataframe(q4_rows, hide_index=True, use_container_width=True, height=455)
        if reveal_index < len(g["opponents"]):
            player_name = g["opponents"][reveal_index]["name"]
            if reveal_phase == 0:
                if st.button(f"Reveal {player_name}'s color and dice quantity", type="primary", use_container_width=True):
                    g["q4_reveal_phase"] = 1
                    st.rerun()
            elif st.button(f"Reveal {player_name}'s dice roll", type="primary", use_container_width=True):
                g["q4_reveal_player"] += 1
                g["q4_reveal_phase"] = 0
                st.rerun()
        else:
            st.success("All 11 opponent rolls revealed.")

with st.expander(stage_title(7, "OVERTIME · Hail Mary", "Overtime"), expanded=g["view_stage"] == "Overtime"):
    st.markdown('<p class="rule"><b>KEEP</b>, or roll one mandatory die: 1 sets your score to 1; 2–6 multiplies your score by the face.</p>', unsafe_allow_html=True)
    if "Fourth Quarter" not in g["completed"]:
        st.info("Complete Fourth Quarter first.")
    elif "Overtime" not in g["completed"]:
        if g["ot_pending"] is None:
            c1, c2 = st.columns(2)
            if c1.button("Keep final score", use_container_width=True):
                record("Overtime", g["score"], g["score"], "Kept score")
                st.rerun()
            if c2.button("Roll Hail Mary", type="primary", use_container_width=True):
                g["ot_pending"] = {"die": g["rng"].randint(1, 6), "redo_note": ""}
                st.rerun()
        else:
            die = g["ot_pending"]["die"]
            draw_tiles([("Hail Mary", str(die))])
            if g["redo"] and st.button("Use banked redo · reroll Hail Mary", use_container_width=True):
                old = die
                g["ot_pending"] = {"die": g["rng"].randint(1, 6), "redo_note": f"Used redo on {old}; "}
                g["redo"] = False
                st.rerun()
            if st.button("Accept Hail Mary result", type="primary", use_container_width=True):
                before = g["score"]
                record("Overtime", before, overtime_result(before, die), f"{g['ot_pending']['redo_note']}rolled {die}")
                st.rerun()
    else:
        st.success(next(x["detail"] for x in g["history"] if x["stage"] == "Overtime"))
        reveal_opponent_stage("Overtime", "Every Hail Mary decision revealed")

st.markdown("## Final results")
if "Overtime" in g["completed"]:
    trail = "".join(f"<div><b>{e['stage']}</b> · {e['detail']} <b>→ {fmt(e['after'])}</b></div>" for e in g["history"])
    st.markdown(f'<div class="result-card"><div style="text-transform:uppercase;letter-spacing:.14em;font-weight:800">Final score</div><div class="final-number">{fmt(g["score"])}</div><p>Lower scores pick their draft slot first.</p><div class="timeline">{trail}</div></div>', unsafe_allow_html=True)
    st.download_button("Download game log", "\n".join(f"{e['stage']}: {e['detail']} | {e['before']} -> {e['after']}" for e in g["history"]), file_name=f"smack-talkers-{g['seed']}.txt")
    st.markdown("### Final table · all 12 players revealed")
    standings = [{"Player": "You", "Final score": g["score"]}] + [
        {"Player": player["name"], "Final score": player["score"]} for player in g["opponents"]
    ]
    standings.sort(key=lambda row: row["Final score"])
    for pick, row in enumerate(standings, 1):
        row["Pick order"] = pick
        row["Final score"] = fmt(row["Final score"])
    st.dataframe(standings, column_order=["Pick order", "Player", "Final score"], hide_index=True, use_container_width=True)
    st.markdown("### Full game matrix · 7 stages × 12 players")
    stage_order = ["Pre-Game", "First Quarter", "Second Quarter", "Halftime", "Third Quarter", "Fourth Quarter", "Overtime"]
    matrix_rows = []
    for stage in stage_order:
        row = {"Stage": stage}
        user_events = [event for event in g["history"] if event["stage"] == stage]
        row["You"] = " | ".join(f"{event['detail']} → {fmt(event['after'])}" for event in user_events)
        for player in g["opponents"]:
            events = [event for event in player["path"] if event["stage"] == stage]
            if events:
                details = " | ".join(event["detail"] for event in events)
                row[player["name"]] = f"{details} → {fmt(events[-1]['score'])}"
            else:
                row[player["name"]] = "—"
        matrix_rows.append(row)
    st.dataframe(
        matrix_rows,
        hide_index=True,
        use_container_width=True,
        height=330,
        column_config={name: st.column_config.TextColumn(name, width="large") for name in ["You"] + [player["name"] for player in g["opponents"]]},
    )
    st.caption("Scroll horizontally to compare all 12 players side by side. Every original card is unsealed here.")
    st.markdown("### Reveal every opponent path and bid")
    for player in g["opponents"]:
        final_pick = next(row["Pick order"] for row in standings if row["Player"] == player["name"])
        with st.expander(f"#{final_pick} · {player['name']} · final {fmt(player['score'])}"):
            st.markdown("**Score path**")
            path_rows = []
            for event in player["path"]:
                path_rows.append({"Stage": event["stage"], "Decision / result": event["detail"], "Score": fmt(event["score"])})
            st.dataframe(path_rows, hide_index=True, use_container_width=True)
            st.markdown("**Blind-auction bids**")
            bid_rows = [{"Power-Up": power, "Bid": player["bids"][power]} for power in POWER_UPS]
            st.dataframe(bid_rows, hide_index=True, use_container_width=True)
else:
    st.info("Complete all seven dropdowns to reveal your final score and full score trail.")

st.divider()
st.markdown("## Simulation lab")
st.caption("Run a fast baseline strategy repeatedly to pressure-test the score distribution. Every complete group of 12 uses exactly three MIN, three MAX, three ABS, and three SUM cards. The bot skips auction bidding to isolate the core random mechanics.")
n_sims = st.select_slider("Games", options=[100, 500, 1_000, 5_000, 10_000], value=1_000)
if st.button("Run simulations"):
    sim_rng = random.Random(int(g["seed"]) + 10_000)
    results = []
    while len(results) < n_sims:
        table_signs = [sign for sign in SIGNS for _ in range(3)]
        sim_rng.shuffle(table_signs)
        results.extend(simulate_game(sim_rng, sign) for sign in table_signs[: n_sims - len(results)])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Best", min(results))
    c2.metric("Median", sorted(results)[len(results) // 2])
    c3.metric("Average", f"{sum(results)/len(results):.1f}")
    c4.metric("Worst", max(results))
    distribution = Counter(round(x) for x in results)
    st.bar_chart({"Games": dict(sorted(distribution.items()))}, x_label="Final score", y_label="Games")
