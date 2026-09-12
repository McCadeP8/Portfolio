from base64 import b64encode
import hashlib
from html import escape
from pathlib import Path

import streamlit as st

from fantrax_data import (
    fetch_player_directory,
    fetch_roster_week,
    fetch_standings,
    enrich_roster_rows,
    load_snapshot,
)


ASSET_DIR = Path(__file__).parent / "assets"


def image_data_uri(filename: str) -> str:
    image_bytes = (ASSET_DIR / filename).read_bytes()
    return f"data:image/png;base64,{b64encode(image_bytes).decode('ascii')}"


DEFAULT_LOGO = "https://pbs.twimg.com/profile_images/2050674964735700992/VCvU540g_400x400.jpg"
LEAGUE_LOGO = image_data_uri("league-logo.png")
VAMPIRE_LOGO = image_data_uri("vampire.png")
KING_LOGO = image_data_uri("king.png")
JUGGERNAUT_LOGO = image_data_uri("juggernaut.png")
HYDRA_LOGO = image_data_uri("hydra.png")
GAMBLER_LOGO = image_data_uri("gambler.png")
ALPHA_LOGO = image_data_uri("alpha.png")
MORTAL_LOGO = image_data_uri("mortal.png")
ORACLE_LOGO = image_data_uri("oracle.png")
KNIGHT_LOGO = image_data_uri("knight.png")
WIZARD_LOGO = image_data_uri("wizard.png")
GUARDIAN_LOGO = image_data_uri("guardian.png")
HUNTER_LOGO = image_data_uri("hunter.png")

CREATURES = [
    {
        "name": "The King",
        "emoji": "👑",
        "lives": 5,
        "ability": "Royal Decree",
        "rule": "Claims the first pick, then drafts again at the end of Round 1.",
        "accent": "#d6ad59",
        "logo": KING_LOGO,
    },
    {
        "name": "The Juggernaut",
        "emoji": "🦾",
        "lives": 6,
        "ability": "Unstoppable Force",
        "rule": "Gains +2 for every team left beneath its score each week.",
        "accent": "#b75645",
        "logo": JUGGERNAUT_LOGO,
    },
    {
        "name": "The Hydra",
        "emoji": "🐍",
        "lives": 2,
        "ability": "Two-Week Severance",
        "rule": "Only back-to-back victories can sever one of its lives.",
        "accent": "#5d9b72",
        "logo": HYDRA_LOGO,
    },
    {
        "name": "The Oracle",
        "emoji": "🔮",
        "lives": 4,
        "ability": "Foretold Victory",
        "rule": "Foresees three random midseason weeks and gains +20 in each.",
        "accent": "#9974bd",
        "logo": ORACLE_LOGO,
    },
    {
        "name": "The Knight",
        "emoji": "⚔️",
        "lives": 4,
        "ability": "Last Stand",
        "rule": "Begins with no bonus. Every life lost adds +5 to each weekly score, up to +15 on its final life.",
        "accent": "#8fa8bc",
        "logo": KNIGHT_LOGO,
    },
    {
        "name": "The Wizard",
        "emoji": "🧙",
        "lives": 3,
        "ability": "Withering Hex",
        "rule": "Curses one random player in your starting lineup every week.",
        "accent": "#526fb1",
        "logo": WIZARD_LOGO,
    },
    {
        "name": "The Guardian",
        "emoji": "🛡️",
        "lives": 4,
        "ability": "Sacred Protection",
        "rule": "Shields its two highest scorers from being stolen that week.",
        "accent": "#4f91a7",
        "logo": GUARDIAN_LOGO,
    },
    {
        "name": "The Hunter",
        "emoji": "🏹",
        "lives": 3,
        "ability": "Marked Prey",
        "rule": "Each victory over you adds a permanent +2 to its future scores.",
        "accent": "#af7041",
        "logo": HUNTER_LOGO,
    },
    {
        "name": "The Gambler",
        "emoji": "🎲",
        "lives": 3,
        "ability": "Double or Nothing",
        "rule": "Flips fate each week: a 50–50 chance at +12 or −8.",
        "accent": "#b94355",
        "logo": GAMBLER_LOGO,
    },
    {
        "name": "The Alpha",
        "emoji": "🐺",
        "lives": 3,
        "ability": "First Among Beasts",
        "rule": "Muscles its way to an additional selection in Round 2.",
        "accent": "#817f85",
        "logo": ALPHA_LOGO,
    },
    {
        "name": "The Mortal",
        "emoji": "🕯️",
        "lives": 2,
        "ability": "No Dark Gift",
        "rule": "No gift. No curse. Only a roster and the will to survive.",
        "accent": "#a78d6b",
        "logo": MORTAL_LOGO,
    },
]

VAMPIRE_TEAM = {
    "name": "The Vampire",
    "emoji": "🧛",
    "lives": None,
    "ability": "The Endless Hunger",
    "rule": "Outscore the hunted, take a life, and steal one player from the fallen roster.",
    "accent": "#9f2639",
    "logo": VAMPIRE_LOGO,
}

TEAM_LORE = {
    "The Vampire": (
        "For generations, the league has whispered of a twelfth invitation written in blood and delivered without a sender. "
        "This season, it found you. The Vampire does not defend a finite store of lives—it hunts. Every weekly victory opens a vein in another creature's roster, allowing one player to be claimed as tribute. "
        "It begins with the same twenty-player roster as every rival, but unlike the hunted, its roster can change from week to week as stolen players join an eighteen-week campaign to extinguish every bloodline before the final dawn."
    ),
    "The King": (
        "The King ruled the old leagues before schedules were kept and champions were crowned beneath electric light. He enters with five lives, a court of scouts, and the ancient privilege of first choice. "
        "His Royal Decree bends the opening round around his throne, granting both the first selection and a bonus pick after every rival has spoken. Deep benches gather around him quickly; bringing down the crown will require surviving the kingdom it builds."
    ),
    "The Juggernaut": (
        "No record names the smith who forged the armor, only the cities flattened beneath it. The Juggernaut carries six lives—more than any creature in the hunt—and grows stronger whenever the week's standings place another team below its score. "
        "Every conquered opponent adds two points to its total, turning a strong week into an avalanche. It cannot be reasoned with, frightened, or slowed. The only answer is to score enough that the march finally stops."
    ),
    "The Hydra": (
        "Deep below the stadium, something learned to grow new heads from every defeat. The Hydra possesses only two lives, yet neither can be taken with a single victory. "
        "To cauterize the wound, The Vampire must outscore it in consecutive weeks; fail the second test and the creature returns whole, hissing from the same darkness. Its roster may look mortal on paper, but the schedule itself is its shield. Against the Hydra, timing is deadlier than strength."
    ),
    "The Oracle": (
        "The Oracle has already watched this season end a thousand different ways. She speaks rarely, keeps four lives behind the veil, and has marked three hidden weeks in the middle of the calendar. "
        "When those prophecies arrive, twenty points appear as though they had always been there. No opponent knows which weeks she has foreseen until the vision becomes reality. To hunt her is to prepare for a score that may suddenly stand twenty points taller than expected."
    ),
    "The Knight": (
        "The Knight was buried in armor after a final defense that lasted three nights. The invitation woke him before the fourth. He begins with four lives and no scoring bonus, but each wound draws more power from the oath sealed inside his steel. "
        "Every life lost adds five points to each weekly score, climbing to a fifteen-point last stand on his final life. Weakening the Knight does not make him safer. It only strips away restraint."
    ),
    "The Wizard": (
        "The Wizard studies a playbook written in moving ink, where every lineup contains one name destined to fail. Each week he reaches across the matchup and places a Withering Hex upon one random opposing starter. "
        "Projections bend, certainty disappears, and a trusted player becomes a liability without warning. Behind three lives and a disciplined roster, he prefers confusion to confrontation. Beating him means building a lineup strong enough to survive the one piece he quietly breaks."
    ),
    "The Guardian": (
        "The Guardian was made to protect treasures too dangerous to possess. Now it stands over four lives and treats the best performances on its roster as sacred relics. "
        "Even when defeated, its two highest-scoring players that week remain beyond The Vampire's reach; the rest may be claimed, but its brightest weapons stay behind the shield. Victory against the Guardian is therefore only half the puzzle. The true prize must be found among the players it failed to protect."
    ),
    "The Hunter": (
        "Long before The Vampire received the invitation, The Hunter had already begun tracking it. Patient, practical, and carrying three lives, he turns every victory over you into permanent momentum. "
        "Each week he outscores The Vampire, two points are added to every score he produces thereafter. A single loss leaves a scar; repeated losses create a predator that becomes harder to escape with every meeting. He is the only creature in the league whose favorite quarry is hunting back."
    ),
    "The Gambler": (
        "The Gambler arrived with no luggage, four aces, and a coin that has never landed on its edge. Every week he wagers his score against the dark: an even chance to gain twelve points or surrender eight. "
        "Across three lives, fortune can make him look untouchable one Sunday and doomed the next. Strategy matters around him, but never entirely. To face The Gambler is to accept that the matchup may be decided by a flip no projection can see."
    ),
    "The Alpha": (
        "The Alpha does not join a pack; the pack forms around it. Its howl secures an additional second-round draft pick, placing another premium player beneath its command before the season begins. "
        "With three lives and a roster built to overwhelm, it values dominance over deception. The Alpha wants every opponent to see it coming, because fear is part of the advantage. To take its lives, The Vampire must break both the lineup and the certainty that follows it."
    ),
    "The Mortal": (
        "No prophecy announced The Mortal. No curse protects him, no hidden bonus changes his score, and only two lives stand between him and elimination. Yet every ancient creature in the league watches him carefully. "
        "Mortals built fantasy football, learned its patterns, and survived by making better choices than monsters who believed power was enough. He enters with nothing except the standard roster and the freedom of having no trick to expose. Sometimes the simplest threat is the one the darkness overlooks."
    ),
}

ALL_TEAMS = [VAMPIRE_TEAM, *CREATURES]
BASE_ROSTER = [("QB", 2), ("RB", 6), ("WR", 6), ("TE", 2), ("DST", 2), ("K", 2)]
VAMPIRE_ROSTER = BASE_ROSTER


@st.cache_data(ttl=3600, show_spinner=False)
def fantrax_player_directory() -> dict:
    return fetch_player_directory()


@st.cache_data(ttl=600, show_spinner=False)
def fantrax_roster_for_week(week: int) -> tuple[list[dict], str]:
    try:
        rows = fetch_roster_week(int(week), fantrax_player_directory())
        if rows:
            return rows, "live"
    except Exception:
        pass
    snapshot = load_snapshot()
    return snapshot.get("rosters", {}).get(str(int(week)), []), "snapshot"


@st.cache_data(ttl=300, show_spinner=False)
def fantrax_standings() -> tuple[list[dict], str]:
    try:
        rows = fetch_standings()
        if rows:
            return rows, "live"
    except Exception:
        pass
    return load_snapshot().get("standings", []), "snapshot"


LINEUP_SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE", "RWT FLEX", "DST", "K"]


def _scored_first(row: dict) -> tuple[bool, float, str]:
    score = row.get("score")
    return isinstance(score, (int, float)), float(score or 0), str(row.get("player", ""))


def best_ball_lineup(roster: list[dict]) -> list[dict]:
    """Choose the nine best-ball starters, filling the flex after fixed slots."""
    pools: dict[str, list[dict]] = {}
    for position in ("QB", "RB", "WR", "TE", "DST", "K"):
        pools[position] = sorted(
            [dict(row) for row in roster if row.get("position") == position],
            key=_scored_first,
            reverse=True,
        )

    chosen: list[dict] = []

    def take(position: str, count: int) -> None:
        for _ in range(count):
            if pools[position]:
                row = pools[position].pop(0)
                row["slot"] = position
                chosen.append(row)

    take("QB", 1)
    take("RB", 2)
    take("WR", 2)
    take("TE", 1)
    flex_pool = sorted(pools["RB"] + pools["WR"] + pools["TE"], key=_scored_first, reverse=True)
    if flex_pool:
        flex = flex_pool[0]
        for pool in (pools["RB"], pools["WR"], pools["TE"]):
            pool[:] = [row for row in pool if row.get("player_id") != flex.get("player_id")]
        flex["slot"] = "RWT FLEX"
        chosen.append(flex)
    take("DST", 1)
    take("K", 1)
    slot_order = {slot: index for index, slot in enumerate(LINEUP_SLOTS)}
    return sorted(chosen, key=lambda row: slot_order.get(row.get("slot", ""), 99))


def seeded_pick(week: int, label: str, choices: list):
    digest = hashlib.sha256(f"et040dehmtxkchmx:{week}:{label}".encode()).digest()
    return choices[int.from_bytes(digest[:8], "big") % len(choices)]


st.set_page_config(
    page_title="The Vampire Hunt",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    :root {
        --wine: #9f2639;
        --gold: #c8a66a;
        --ink: #e8e0d7;
        --muted: #9d9591;
    }

    .stApp {
        background:
          radial-gradient(circle at 76% 4%, rgba(128, 28, 47, .20), transparent 29rem),
          radial-gradient(circle at 5% 78%, rgba(117, 83, 48, .11), transparent 28rem),
          #0b0a0c;
        color: var(--ink);
    }

    .block-container {
        max-width: 1700px;
        padding-top: 3rem;
        padding-bottom: 4rem;
    }

    [data-testid="stHeader"] { background: transparent; }

    .masthead {
        display: flex;
        align-items: center;
        gap: 1.4rem;
    }

    .league-crest {
        width: 86px;
        height: 86px;
        object-fit: cover;
        border-radius: 50%;
        border: 1px solid #6e4f45;
        box-shadow: 0 0 0 5px rgba(159,38,57,.10), 0 12px 36px rgba(0,0,0,.45);
    }

    .league-kicker {
        color: var(--gold);
        font: 600 .7rem/1 'Inter', sans-serif;
        letter-spacing: .23em;
        text-transform: uppercase;
        margin-bottom: .8rem;
    }

    .league-title {
        color: #f3ece4;
        font: 700 clamp(3.4rem, 8vw, 6rem)/.88 'Cormorant Garamond', serif;
        letter-spacing: .01em;
        margin: 0;
    }

    .league-title span {
        color: var(--wine);
        font-style: italic;
    }

    .league-subtitle {
        color: var(--muted);
        font: 500 .76rem/1.5 'Inter', sans-serif;
        letter-spacing: .16em;
        text-transform: uppercase;
        margin-top: 1.25rem;
    }

    .rule {
        height: 1px;
        background: linear-gradient(90deg, var(--wine), #3b292e 45%, transparent);
        margin: 2rem 0 1.6rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2.5rem;
        border-bottom: 1px solid #30292e;
    }

    .stTabs [data-baseweb="tab"] {
        height: 3.25rem;
        padding: 0 .2rem;
        color: #8f8788;
        background: transparent;
        font: 600 .73rem/1 'Inter', sans-serif;
        letter-spacing: .17em;
        text-transform: uppercase;
    }

    .stTabs [aria-selected="true"] { color: #f0e5dd !important; }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: var(--wine);
        height: 2px;
    }

    .stTabs [data-baseweb="tab-border"] { display: none; }

    .section-kicker {
        color: var(--gold);
        font: 600 .68rem/1 'Inter', sans-serif;
        letter-spacing: .2em;
        text-transform: uppercase;
        margin-bottom: .7rem;
    }

    .section-title {
        color: #f0e7df;
        font: 600 clamp(2rem, 4vw, 3rem)/1 'Cormorant Garamond', serif;
        margin-bottom: .8rem;
    }

    .vampire-card {
        position: relative;
        overflow: hidden;
        display: grid;
        grid-template-columns: 118px 1fr auto;
        align-items: center;
        gap: 1.35rem;
        padding: 1.45rem;
        margin: 2rem 0 2.5rem;
        background: linear-gradient(120deg, rgba(71,18,32,.88), rgba(22,17,21,.98) 60%);
        border: 1px solid #783146;
        border-radius: 6px;
        box-shadow: 0 22px 60px rgba(0,0,0,.24);
    }

    .vampire-card:after {
        content: "";
        position: absolute;
        width: 220px;
        height: 220px;
        right: -85px;
        top: -120px;
        border: 1px solid rgba(200,166,106,.16);
        border-radius: 50%;
    }

    .vampire-card img {
        width: 112px;
        height: 112px;
        border-radius: 4px;
        object-fit: cover;
        border: 1px solid #916174;
    }

    .creature-name {
        color: #f3ebe3;
        font: 600 1.85rem/1 'Cormorant Garamond', serif;
        margin: .25rem 0 .55rem;
    }

    .creature-name .emoji { font-size: 1.35rem; margin-right: .4rem; }

    .ability-name {
        color: var(--gold);
        font: 600 .66rem/1 'Inter', sans-serif;
        letter-spacing: .16em;
        text-transform: uppercase;
    }

    .creature-rule {
        color: #a69e9b;
        font: 400 .84rem/1.55 'Inter', sans-serif;
        max-width: 34rem;
    }

    .roster-mark {
        min-width: 178px;
        color: #d6c9bf;
        font: 500 .73rem/1.8 'Inter', sans-serif;
        letter-spacing: .04em;
        border-left: 1px solid #603140;
        padding-left: 1.2rem;
    }

    .roster-mark strong { color: #f0d9a8; font-weight: 600; }

    .lore {
        max-width: none;
        padding: .5rem 0 1.3rem 1.3rem;
        border-left: 2px solid var(--wine);
    }

    .lore p {
        color: #aaa19f;
        font: 400 1.08rem/1.85 'Inter', sans-serif;
        margin: 0 0 1rem;
    }

    .rules-strip {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1px;
        margin: 1.3rem 0 3.5rem;
        background: #342b30;
        border: 1px solid #342b30;
    }

    .rule-stat { background: #151316; padding: 1rem; }
    .rule-stat b { display: block; color: #eee4dc; font: 600 1.45rem 'Cormorant Garamond', serif; }
    .rule-stat span { color: #827b7b; font: 500 .62rem 'Inter', sans-serif; letter-spacing: .12em; text-transform: uppercase; }

    .monster-card {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        display: grid;
        grid-template-columns: 68px 1fr;
        gap: 1.1rem;
        align-items: center;
        padding: 1rem 1.2rem;
        margin-bottom: .75rem;
        background:
            linear-gradient(105deg, color-mix(in srgb, var(--card-accent) 26%, #171317), rgba(18,16,19,.96) 55%),
            #171317;
        border: 1px solid color-mix(in srgb, var(--card-accent) 54%, #332c31);
        border-left: 5px solid var(--card-accent);
        border-radius: 5px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.035), 0 10px 25px rgba(0,0,0,.16);
    }

    .monster-card:after {
        content: attr(data-sigil);
        position: absolute;
        z-index: -1;
        left: 42%;
        right: auto;
        top: 50%;
        transform: translateY(-50%) rotate(-8deg);
        color: color-mix(in srgb, var(--card-accent) 14%, transparent);
        font-size: 8rem;
        filter: grayscale(1);
        opacity: .42;
        pointer-events: none;
    }

    .monster-card img {
        width: 64px;
        height: 64px;
        border-radius: 4px;
        object-fit: cover;
        filter: grayscale(.18) contrast(1.1);
        border: 1px solid color-mix(in srgb, var(--card-accent) 62%, #4b4148);
        box-shadow: 0 0 18px color-mix(in srgb, var(--card-accent) 20%, transparent);
    }

    .monster-card .creature-name { font-size: 1.5rem; margin: 0 0 .35rem; }

    .ability-line {
        color: #a9a0a0;
        font: 400 .79rem/1.5 'Inter', sans-serif;
        padding-right: 10rem;
    }

    .ability-line strong {
        color: var(--card-accent);
        font-size: .68rem;
        letter-spacing: .13em;
        text-transform: uppercase;
    }

    .lives {
        position: absolute;
        top: 1rem;
        right: 1rem;
        color: #d8ccc4;
        font: 700 1rem 'Inter', sans-serif;
        letter-spacing: .1em;
        text-transform: uppercase;
    }

    .life-pips { color: var(--card-accent); letter-spacing: .08em; margin-left: .3rem; font-size:1.25rem; }

    .base-roster {
        color: #827b7b;
        font: 500 .68rem/1.5 'Inter', sans-serif;
        letter-spacing: .06em;
        text-transform: uppercase;
        margin: -.2rem 0 1.3rem;
    }

    [data-testid="stSelectbox"] {
        max-width: 420px;
        margin: 1.2rem 0 1.7rem;
    }

    [data-testid="stSelectbox"] label p {
        color: var(--gold);
        font-size: .68rem;
        font-weight: 600;
        letter-spacing: .15em;
        text-transform: uppercase;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: #171418;
        border-color: #41363d;
    }

    .team-hero {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        display: grid;
        grid-template-columns: 250px 1fr;
        gap: 2rem;
        align-items: center;
        padding: 1.6rem;
        background:
            radial-gradient(circle at 15% 50%, color-mix(in srgb, var(--team-accent) 28%, transparent), transparent 25rem),
            linear-gradient(120deg, color-mix(in srgb, var(--team-accent) 19%, #171419), #111013 62%);
        border: 1px solid color-mix(in srgb, var(--team-accent) 58%, #342d32);
        border-radius: 7px;
        box-shadow: 0 24px 65px rgba(0,0,0,.27);
    }

    .team-hero:after {
        content: attr(data-sigil);
        position: absolute;
        z-index: -1;
        right: 2rem;
        top: 50%;
        transform: translateY(-50%) rotate(-9deg);
        font-size: 12rem;
        opacity: .045;
        filter: grayscale(1);
    }

    .team-hero img {
        width: 250px;
        height: 250px;
        object-fit: cover;
        border-radius: 6px;
        border: 1px solid color-mix(in srgb, var(--team-accent) 68%, #4a4146);
        box-shadow: 0 14px 38px rgba(0,0,0,.42);
    }

    .dossier-label {
        color: var(--team-accent);
        font: 600 .68rem 'Inter', sans-serif;
        letter-spacing: .19em;
        text-transform: uppercase;
    }

    .team-name {
        color: #f2e9e1;
        font: 700 clamp(2.7rem, 6vw, 4.6rem)/.95 'Cormorant Garamond', serif;
        margin: .45rem 0 .8rem;
    }

    .team-power {
        max-width: 42rem;
        color: #b1a7a5;
        font: 400 .91rem/1.65 'Inter', sans-serif;
    }

    .team-power strong { color: var(--team-accent); }

    .dossier-stats {
        display: flex;
        gap: 2.2rem;
        margin-top: 1.5rem;
    }

    .dossier-stat b {
        display: block;
        color: #f0e6de;
        font: 600 1.55rem 'Cormorant Garamond', serif;
    }

    .dossier-stat span {
        color: #7f7778;
        font: 600 .6rem 'Inter', sans-serif;
        letter-spacing: .13em;
        text-transform: uppercase;
    }

    .hunt-timeline { margin-top:1.25rem; padding-top:.9rem; border-top:1px solid color-mix(in srgb,var(--team-accent) 28%,#302a2e); }
    .hunt-timeline-title { color:#8d8584; font:600 .58rem 'Inter',sans-serif; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.55rem; }
    .hunt-weeks { display:flex; gap:.28rem; flex-wrap:nowrap; }
    .hunt-week { width:1.58rem; height:1.58rem; display:flex; align-items:center; justify-content:center; border-radius:50%; border:1px solid #4a4145; background:#171417; color:#8f8787; font:700 .78rem 'Inter',sans-serif; box-sizing:border-box; }
    .hunt-week.survived { color:#8ed3a4; border-color:#4f8d68; background:#13251b; }
    .hunt-week.lost { color:#f08e87; border-color:#9e4b50; background:#32171b; }
    .hunt-week.danger { color:#f2c06b; border-color:#a87736; background:#302312; }
    .hunt-week.stolen { color:#ffb2b4; border-color:#d0495c; background:#4a1520; box-shadow:0 0 10px rgba(210,58,79,.35); }
    .hunt-week.eliminated { color:#726b6d; border-color:#393336; background:#111012; }
    .hunt-week.scheduled { color:#686162; border-color:#302b2f; background:#111012; }
    .hunt-week.gambler-positive { text-decoration:underline 2px #7fc39a; text-underline-offset:3px; }
    .hunt-week.gambler-negative { text-decoration:overline 2px #ef8b83; text-decoration-thickness:2px; }
    .hunt-week.oracle-bonus { box-shadow:0 0 0 2px #9974bd, 0 0 12px rgba(153,116,189,.45); }
    .hunt-legend { margin-top:.55rem; color:#81797a; font:500 .58rem 'Inter',sans-serif; line-height:1.55; }

    .profile-grid {
        display: grid;
        grid-template-columns: 1.4fr .8fr;
        gap: 1rem;
        margin-top: 1rem;
    }

    .profile-grid.archive-full { grid-template-columns: 1fr; }

    .profile-panel {
        background: linear-gradient(145deg, rgba(24,21,25,.98), rgba(15,14,16,.98));
        border: 1px solid #312b30;
        border-radius: 5px;
        padding: 1.35rem 1.45rem;
    }

    .profile-panel h3 {
        color: #eee4dc;
        font: 600 1.5rem 'Cormorant Garamond', serif;
        margin: .25rem 0 .7rem;
    }

    .profile-panel p {
        color: #9f9795;
        font: 400 .86rem/1.75 'Inter', sans-serif;
        margin: 0;
    }

    .position-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: .55rem;
        margin-top: .7rem;
    }

    .position-slot {
        background: #111012;
        border: 1px solid #302a2e;
        border-top-color: var(--team-accent);
        padding: .7rem;
        text-align: center;
    }

    .position-slot b { display: block; color: #e6ddd5; font: 600 1.2rem 'Cormorant Garamond', serif; }
    .position-slot span { color: #777071; font: 600 .6rem 'Inter', sans-serif; letter-spacing: .1em; }

    .roster-empty {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-top: 1rem;
        padding: 1rem 1.15rem;
        background: color-mix(in srgb, var(--team-accent) 7%, #121013);
        border: 1px dashed color-mix(in srgb, var(--team-accent) 42%, #393137);
        border-radius: 4px;
        color: #898182;
        font: 400 .78rem/1.5 'Inter', sans-serif;
    }

    .roster-empty strong { color: var(--team-accent); font-weight: 600; }

    .roster-header { display:flex; justify-content:space-between; align-items:end; gap:1rem; margin:1.3rem 0 .65rem; }
    .roster-header h3 { color:#eee4dc; font:600 1.75rem 'Cormorant Garamond',serif; margin:.2rem 0 0; }
    .data-status { color:#8c8484; font:600 .61rem 'Inter',sans-serif; letter-spacing:.12em; text-transform:uppercase; }
    .data-status.live { color:#76b790; }
    .roster-table { overflow:hidden; background:#121013; border:1px solid #302a2f; border-radius:5px; }
    .roster-row { display:grid; grid-template-columns:58px minmax(180px,1fr) 100px 110px 90px; align-items:center; min-height:47px; border-bottom:1px solid #272226; }
    .roster-row:last-child { border-bottom:0; }
    .roster-row > div { padding:.62rem .82rem; }
    .roster-row.header { min-height:34px; background:color-mix(in srgb,var(--team-accent) 12%,#171418); color:#827a7b; font:600 .59rem 'Inter',sans-serif; letter-spacing:.12em; text-transform:uppercase; }
    .roster-player { color:#ddd4cd; font:500 .82rem 'Inter',sans-serif; }
    .roster-meta,.roster-score { color:#807879; font:500 .7rem 'Inter',sans-serif; }
    .pos-pill { display:inline-block; min-width:38px; padding:.25rem .45rem; color:var(--team-accent); background:color-mix(in srgb,var(--team-accent) 10%,#121013); border:1px solid color-mix(in srgb,var(--team-accent) 40%,#302a2f); border-radius:99px; font:600 .62rem 'Inter',sans-serif; text-align:center; }

    .scoreboard-grid {
        display: grid;
        grid-template-columns: minmax(310px, 2fr) minmax(310px, 2fr) minmax(230px, 1fr);
        gap: 1rem;
        align-items: start;
        margin-top: 1rem;
    }

    .score-card, .league-board {
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(circle at 90% 4%, color-mix(in srgb, var(--score-accent) 24%, transparent), transparent 32%),
            linear-gradient(155deg, color-mix(in srgb, var(--score-accent) 15%, #171418), #0d0c0e 62%);
        border: 1px solid color-mix(in srgb, var(--score-accent) 45%, #322b30);
        border-radius: 6px;
        box-shadow: 0 20px 55px rgba(0,0,0,.32), inset 0 1px color-mix(in srgb,var(--score-accent) 55%,transparent);
    }

    .score-card:after { content:attr(data-sigil); position:absolute; right:-.35rem; top:4.2rem; color:color-mix(in srgb,var(--score-accent) 9%,transparent); font-size:8rem; line-height:1; pointer-events:none; }
    .score-card.vampire-side { border-width:2px; box-shadow:0 0 34px rgba(159,38,57,.28),0 22px 60px rgba(0,0,0,.38); }
    .score-card-head { position:relative; z-index:1; display:flex; align-items:center; gap:1rem; min-height:108px; box-sizing:border-box; padding:1.15rem; border-bottom:1px solid #302a2e; }
    .score-card-head img { width:82px; height:82px; object-fit:cover; border-radius:5px; border:1px solid var(--score-accent); box-shadow:0 0 20px color-mix(in srgb,var(--score-accent) 28%,transparent); }
    .score-card-head h3 { color:#f3e9e1; font:700 clamp(1.55rem,2.5vw,2.15rem) 'Cormorant Garamond',serif; margin:.12rem 0 0; }
    .score-card-head span { color:#81797a; font:600 .57rem 'Inter',sans-serif; letter-spacing:.12em; text-transform:uppercase; }
    .head-score { margin-left:auto; text-align:right; }
    .head-score b { display:block; color:var(--score-accent); font:700 2.25rem 'Cormorant Garamond',serif; line-height:.9; }
    .head-score span { font-size:.5rem; }
    .block-mark { margin-left:auto; color:#e5a353 !important; border:1px solid #8d582d; padding:.35rem .5rem; border-radius:3px; }
    .lineup-list { padding:.35rem .8rem; }
    .lineup-row { display:grid; grid-template-columns:68px 1fr 72px; gap:.55rem; align-items:center; min-height:43px; border-bottom:1px solid #292428; }
    .lineup-row:last-child { border-bottom:0; }
    .lineup-slot { color:var(--score-accent); font:700 .58rem 'Inter',sans-serif; letter-spacing:.08em; }
    .lineup-player strong { display:block; color:#dcd3cc; font:500 .78rem 'Inter',sans-serif; }
    .lineup-player span { color:#746d6e; font:500 .59rem 'Inter',sans-serif; }
    .lineup-points { color:#e9dfd6; font:600 .86rem 'Inter',sans-serif; text-align:right; padding-right:.28rem; }
    .lineup-row.bonus { margin-top:.35rem; background:color-mix(in srgb,var(--score-accent) 8%,#151215); border-top:1px solid color-mix(in srgb,var(--score-accent) 42%,#302a2e); }
    .score-total { display:flex; align-items:end; justify-content:space-between; padding:1rem; background:#0c0b0d; border-top:1px solid #332c31; }
    .score-total span { color:#777071; font:600 .6rem 'Inter',sans-serif; letter-spacing:.12em; text-transform:uppercase; }
    .score-total b { color:var(--score-accent); font:700 2rem 'Cormorant Garamond',serif; }

    .league-board { --score-accent:#9f2639; min-height:1035px; box-sizing:border-box; padding:.7rem; background:linear-gradient(160deg,#241117,#0e0d0f 68%); }
    .league-board-title { color:#f0e2d9; font:700 1.8rem 'Cormorant Garamond',serif; margin:.15rem .25rem .7rem; }
    .rank-tiles { display:grid; height:calc(100% - 3rem); grid-template-rows:repeat(12,minmax(0,1fr)); gap:.45rem; }
    .rank-tile { position:relative; display:grid; grid-template-columns:26px 1fr auto; gap:.5rem; align-items:center; min-height:55px; padding:.48rem .58rem; overflow:hidden; background:linear-gradient(100deg,color-mix(in srgb,var(--rank-accent) 20%,#171418),#111012 75%); border:1px solid color-mix(in srgb,var(--rank-accent) 35%,#2d282c); border-radius:5px; }
    .rank-team { min-width:0; }
    .rank-score { white-space:nowrap; }
    .rank-tile.vampire-rank { border-color:#cf4058; background:linear-gradient(100deg,#4a1520,#171014 75%); box-shadow:0 0 15px rgba(190,40,64,.25); }
    .rank-tile.vampire-rank:after { content:none; }
    .rank-tile.vampire-rank { min-height:75px; grid-template-columns:28px 1fr auto; padding:.55rem .62rem; }
    .rank-tile.vampire-rank .rank-team strong { color:#fff0e9; font-size:.82rem; }
    .rank-tile.vampire-rank .rank-team span { color:#e28b98; }
    .rank-tile.vampire-rank .rank-number { font-size:.82rem; }
    .rank-tile.vampire-rank .rank-score { color:#ffb5bd; font-size:1.05rem; }
    .rank-number { color:var(--rank-accent); font:700 .76rem 'Inter',sans-serif; text-align:center; }
    .rank-team strong { display:block; overflow:hidden; color:#ddd3cc; font:600 .72rem 'Inter',sans-serif; white-space:nowrap; text-overflow:ellipsis; }
    .rank-team span { display:block; overflow:hidden; color:#746c6e; font:500 .55rem 'Inter',sans-serif; white-space:nowrap; text-overflow:ellipsis; }
    .rank-team span.rank-status { font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
    .rank-status.safe { color:#7fc39a; }
    .rank-status.danger { color:#ef8b83; }
    .rank-status.hunter { color:#f2a4b0; }
    .rank-status.unknown { color:#8b8382; }
    .rank-score { color:#f0e5dc; font:700 1rem 'Inter',sans-serif; }
    .bench-list { margin:.55rem 0 1rem; padding:.35rem .75rem; background:#0e0d0f; border:1px solid #302a2e; border-radius:5px; }
    .bench-title { color:#837b7c; font:700 .56rem 'Inter',sans-serif; letter-spacing:.13em; text-transform:uppercase; padding:.55rem 0 .35rem; }
    .bench-row { display:grid; grid-template-columns:52px 1fr 52px; gap:.5rem; align-items:center; min-height:35px; border-top:1px solid #282327; }
    .bench-row span { color:#756e6f; font:600 .55rem 'Inter',sans-serif; }
    .bench-row strong { color:#c8bfb9; font:500 .68rem 'Inter',sans-serif; }
    .bench-row b { color:#a49b97; font:600 .67rem 'Inter',sans-serif; text-align:right; }
    .opponent-picker-title { color:#d9c9c0; font:600 .62rem 'Inter',sans-serif; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.35rem; }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.opponent-picker-title) { min-height:108px; box-sizing:border-box; background:linear-gradient(145deg,#24151b,#130f12); border:1px solid #8f3a4c; border-radius:6px; padding:.55rem .7rem .7rem; box-shadow:0 0 22px rgba(159,38,57,.18); }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.opponent-picker-title) img { border-radius:5px; box-shadow:0 0 18px rgba(159,38,57,.35); }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.opponent-picker-title) [data-baseweb="select"] > div { min-height:62px; background:rgba(65,25,34,.92); border:1px solid #a34b60; color:#f5e9e2; font:600 1rem 'Cormorant Garamond',serif; box-shadow:0 0 18px rgba(159,38,57,.16); }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.opponent-picker-title) [data-baseweb="select"] svg { color:#e3a5ad; }

    @media (max-width: 760px) {
        .block-container { padding-top: 2rem; }
        .league-crest { width: 64px; height: 64px; }
        .vampire-card { grid-template-columns: 76px 1fr; }
        .vampire-card img { width: 72px; height: 72px; }
        .roster-mark { grid-column: 1 / -1; border-left: 0; border-top: 1px solid #603140; padding: .8rem 0 0; }
        .rules-strip { grid-template-columns: repeat(2, 1fr); }
        .stTabs [data-baseweb="tab-list"] { gap: 1.1rem; }
        .monster-card:after { display: none; }
        .ability-line { padding-right: 0; }
        .lives { position: static; grid-column: 2; grid-row: 2; margin-top: .4rem; }
        .team-hero { grid-template-columns: 1fr; }
        .team-hero img { width: 100%; height: auto; aspect-ratio: 1; }
        .profile-grid { grid-template-columns: 1fr; }
        .scoreboard-grid { grid-template-columns: 1fr; }
        .league-board { min-height:0; }
        .rank-tiles { height:auto; grid-template-rows:none; }
        .roster-row { grid-template-columns:52px 1fr 70px; }
        .roster-row > div:nth-child(4), .roster-row > div:nth-child(5) { display:none; }
    }

    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    f"""<div class="masthead">
        <img class="league-crest" src="{LEAGUE_LOGO}" alt="The Vampire Hunt league crest">
        <div><div class="league-kicker">Fantasy Football League</div>
        <div class="league-title">The Vampire <span>Hunt</span></div>
        <div class="league-subtitle">Can you kill them all?</div></div>
    </div>""",
    unsafe_allow_html=True,
)
st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

overview_tab, teams_tab, scoreboard_tab, about_tab = st.tabs(["Overview", "Teams", "Scoreboard", "About"])

with overview_tab:
    st.markdown(
        f"""<div class="vampire-card">
            <img src="{VAMPIRE_LOGO}" alt="The Vampire logo">
            <div>
                <div class="ability-name">You are the monster in the dark</div>
                <div class="creature-name"><span class="emoji">🧛</span>The Vampire</div>
                <div class="creature-rule">Hunt every creature. Your roster evolves whenever you take a life and claim a player from the fallen.</div>
            </div>
            <div class="roster-mark"><strong>STANDARD ROSTER</strong><br>2 QB · 6 RB · 6 WR<br>2 TE · 2 DST · 2 K</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-kicker">The covenant</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Twelve entered. One must feed.</div>', unsafe_allow_html=True)
    st.markdown(
        """<div class="lore">
            <p>Every eighteen years, when the season turns and the stadium lights burn against the early dark, twelve creatures answer the same invitation. Eleven arrive believing they have been summoned to compete. The twelfth arrives hungry. This year, that creature is you.</p>
            <p>Your prey will not be found in crypts or moonlit forests, but across the weekly ledger of fantasy football. Outscore the creature opposite you and it loses one of its lives. With that life comes tribute: once each week you defeat an opponent and draw blood, you may steal one player from its roster and make that player your own.</p>
            <p>You have eighteen weeks to extinguish all eleven bloodlines. Each creature carries a different curse, gift, or cruel protection—and each begins with only so many lives. Learn what guards them. Choose where to strike. By the final whistle, either the league belongs to The Vampire… or dawn finds you starving.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """<div class="rules-strip">
            <div class="rule-stat"><b>12</b><span>Teams enter</span></div>
            <div class="rule-stat"><b>18</b><span>Weeks to hunt</span></div>
            <div class="rule-stat"><b>1 life</b><span>Lost when outscored</span></div>
            <div class="rule-stat"><b>1 player</b><span>Stolen after a group of kills</span></div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-kicker">The hunted</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Eleven creatures stand between you and dawn.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="base-roster">Base roster · 2 QB · 6 RB · 6 WR · 2 TE · 2 DST · 2 K</div>',
        unsafe_allow_html=True,
    )

    for creature in CREATURES:
        hearts = "◆" * creature["lives"]
        creature_logo = creature.get("logo", DEFAULT_LOGO)
        st.markdown(
            f"""<div class="monster-card" data-sigil="{creature['emoji']}" style="--card-accent:{creature['accent']}">
                <div class="lives">{creature['lives']} lives <span class="life-pips">{hearts}</span></div>
                <img src="{creature_logo}" alt="{creature['name']} logo">
                <div><div class="creature-name"><span class="emoji">{creature['emoji']}</span>{creature['name']}</div>
                <div class="ability-line"><strong>{creature['ability']}</strong> — {creature['rule']}</div></div>
            </div>""",
            unsafe_allow_html=True,
        )

with teams_tab:
    st.markdown('<div class="section-kicker">Creature dossiers</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Know what waits across the field.</div>', unsafe_allow_html=True)
    st.caption("Select a team to inspect its history, power, lives, and roster.")

    all_teams = ALL_TEAMS
    team_names = [team["name"] for team in all_teams]
    selected_name = st.selectbox(
        "Choose a team",
        team_names,
        format_func=lambda name: f"{next(team['emoji'] for team in all_teams if team['name'] == name)}  {name}",
    )
    selected_team = next(team for team in all_teams if team["name"] == selected_name)
    is_vampire = selected_name == "The Vampire"
    snapshot = load_snapshot()
    active_week = max(1, min(18, int(snapshot.get("current_week", 1))))
    if is_vampire:
        selected_week = st.select_slider(
            "Vampire roster week",
            options=list(range(1, 19)),
            value=active_week,
            format_func=lambda week: f"Week {week}",
            help="The Vampire's roster can change after every successful hunt.",
        )
    else:
        selected_week = active_week

    roster_rows, roster_source = fantrax_roster_for_week(selected_week)
    roster_rows = enrich_roster_rows(roster_rows)
    team_roster = [row for row in roster_rows if row.get("team") == selected_name]
    standings, _ = fantrax_standings()
    standing = next((row for row in standings if row.get("team") == selected_name), {})
    reported_lives = next(
        (row.get("lives_remaining") for row in team_roster if row.get("lives_remaining") is not None),
        standing.get("lives_remaining"),
    )
    if is_vampire:
        lives_display = "—"
    elif reported_lives is None:
        lives_display = str(selected_team["lives"])
    else:
        lives_display = str(min(int(reported_lives), int(selected_team["lives"])))
    condition_display = "HUNTING" if is_vampire else "◆" * int(lives_display)

    previous_week = active_week - 1
    weekly_scores = snapshot.get("weekly_scores", {}).get(str(previous_week), []) if previous_week > 0 else []
    last_week_entry = next((row for row in weekly_scores if row.get("team") == selected_name), {})
    last_week_score = last_week_entry.get("score")
    last_week_finish = last_week_entry.get("finish")
    last_week_display = f"{last_week_score:.1f}" if isinstance(last_week_score, (int, float)) else "—"
    if isinstance(last_week_finish, int):
        suffix = "th" if 10 <= last_week_finish % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(last_week_finish % 10, "th")
        last_week_detail = f"{last_week_finish}{suffix} finish"
    elif previous_week < 1:
        last_week_detail = "No prior week"
    else:
        last_week_detail = "Awaiting Fantrax score"
    position_order = {position: index for index, (position, _) in enumerate(BASE_ROSTER)}
    team_roster.sort(
        key=lambda row: (
            position_order.get(str(row.get("position", "")), 99),
            str(row.get("player", "")),
        )
    )
    roster_rows_html = "".join(
        f'''<div class="roster-row">
            <div>{index}</div>
            <div class="player"><strong>{escape(str(row.get("player") or "Unknown player"))}</strong></div>
            <div><span class="pos-pill">{escape(str(row.get("position") or "—"))}</span></div>
            <div>{escape(str(row.get("nfl_team") or "FA"))}</div>
            <div class="score">{f'{row["score"]:.1f}' if isinstance(row.get("score"), (int, float)) else '—'}</div>
        </div>'''
        for index, row in enumerate(team_roster, start=1)
    )
    if not roster_rows_html:
        roster_rows_html = '<div class="roster-empty"><div><strong>Roster unavailable</strong><br>The last Fantrax snapshot did not contain this team.</div></div>'
    source_label = "Live from Fantrax" if roster_source == "live" else "Saved Fantrax snapshot"
    roster_table = f'''<div class="roster-header">
        <div><div class="dossier-label">The active ledger</div><h3>Week {selected_week} roster</h3></div>
        <span class="data-status {roster_source}">{source_label}</span>
    </div>
    <div class="roster-table">
        <div class="roster-row header"><div>#</div><div>Player</div><div>Position</div><div>NFL team</div><div>Week score</div></div>
        {roster_rows_html}
    </div>
    <div class="roster-note">Player scores require an authenticated Fantrax session; roster names, positions, NFL teams, and current league points are connected.</div>'''

    # A deterministic season timeline keeps special-week markers stable between reruns.
    oracle_weeks = sorted(
        sorted(range(5, 16), key=lambda week: hashlib.sha256(f"oracle:{week}".encode()).digest())[:3]
    )
    vampire_score = next((row.get("score") for row in standings if row.get("team") == "The Vampire"), None)
    stolen_weeks: set[int] = set()
    timeline_bits = []
    for week in range(1, 19):
        status, status_class, symbol = "Scheduled", "scheduled", "·"
        if week <= active_week:
            week_rows = snapshot.get("weekly_scores", {}).get(str(week), [])
            if week == active_week:
                week_rows = standings
            team_score = next((row.get("score") for row in week_rows if row.get("team") == selected_name), None)
            if isinstance(team_score, (int, float)) and isinstance(vampire_score, (int, float)):
                if team_score >= vampire_score:
                    status, status_class, symbol = "Survived", "survived", "✓"
                else:
                    status, status_class, symbol = "Lost a life", "lost", "✕"
                    if selected_name == "The Hydra" and week == active_week:
                        status, status_class, symbol = "Danger: first loss", "danger", "⚠"
                if week in stolen_weeks:
                    status, status_class, symbol = "Lost a life and player stolen", "stolen", "☠"
            elif week == active_week:
                status, status_class, symbol = "Current week", "unknown", "?"
        if selected_name == "The Gambler" and week <= active_week:
            gambler_outcome = seeded_pick(week, "gambler-flip", [12, -8])
            status = f"Gambler {gambler_outcome:+d}"
            status_class = f"{status_class} gambler-positive" if gambler_outcome > 0 else f"{status_class} gambler-negative"
        if selected_name == "The Oracle" and week <= active_week and week in oracle_weeks:
            status = f"Oracle +20 week · {status}"
            status_class = f"{status_class} oracle-bonus"
        timeline_bits.append(f'<span class="hunt-week {status_class}" title="Week {week}: {status}">{symbol}</span>')
    timeline_html = f'''<div class="hunt-timeline"><div class="hunt-timeline-title">Season life timeline · {selected_name}</div>
        <div class="hunt-weeks">{''.join(timeline_bits)}</div>
    </div>'''
    timeline_fragment = timeline_html if not is_vampire else '<div class="timeline-slot"></div>'

    st.markdown(
        f"""<div style="--team-accent:{selected_team['accent']}">
            <div class="team-hero" data-sigil="{selected_team['emoji']}">
                <img src="{selected_team['logo']}" alt="{selected_name} logo">
                <div>
                    <div class="dossier-label">Official creature dossier</div>
                    <div class="team-name">{selected_team['emoji']} {selected_name}</div>
                    <div class="team-power"><strong>{selected_team['ability']}</strong> — {selected_team['rule']}</div>
                    <div class="dossier-stats">
                        <div class="dossier-stat"><b>{condition_display}</b><span>Current condition</span></div>
                        <div class="dossier-stat"><b>{last_week_display}</b><span>Last week score · {last_week_detail}</span></div>
                    </div>
                    {timeline_fragment}
                </div>
            </div>
            <div class="profile-grid archive-full">
                <div class="profile-panel">
                    <div class="dossier-label">From the forbidden archive</div>
                    <h3>Origin &amp; legend</h3>
                    <p>{TEAM_LORE[selected_name]}</p>
                </div>
            </div>
            {roster_table}
        </div>""",
        unsafe_allow_html=True,
    )
with scoreboard_tab:
    scoreboard_week = st.selectbox(
        "Scoring week",
        list(range(1, 19)),
        index=active_week - 1,
        format_func=lambda week: f"Week {week}",
        key="scoreboard_week",
    )

    score_rosters, score_roster_source = fantrax_roster_for_week(scoreboard_week)
    score_rosters = enrich_roster_rows(score_rosters)
    current_standings, score_standing_source = fantrax_standings()
    scores_revealed = scoreboard_week <= active_week
    if scoreboard_week == active_week:
        score_rows = current_standings
    elif scores_revealed:
        score_rows = snapshot.get("weekly_scores", {}).get(str(scoreboard_week), [])
    else:
        score_rows = []
    base_scores = {
        row.get("team"): row.get("score")
        for row in score_rows
        if isinstance(row.get("score"), (int, float))
    }

    rosters_by_team = {
        team["name"]: [row for row in score_rosters if row.get("team") == team["name"]]
        for team in ALL_TEAMS
    }
    lineups = {name: best_ball_lineup(rows) for name, rows in rosters_by_team.items()}

    vampire_lineup = lineups["The Vampire"]
    wizard_target = None
    wizard_replacement = None
    wizard_bonus = 0.0
    if vampire_lineup:
        wizard_target = seeded_pick(scoreboard_week, "wizard-hex", vampire_lineup)
        target_slot = wizard_target.get("slot")
        eligible_positions = {"RB", "WR", "TE"} if target_slot == "RWT FLEX" else {wizard_target.get("position")}
        chosen_ids = {row.get("player_id") for row in vampire_lineup}
        replacements = sorted(
            [
                row for row in rosters_by_team["The Vampire"]
                if row.get("player_id") not in chosen_ids and row.get("position") in eligible_positions
            ],
            key=_scored_first,
            reverse=True,
        )
        wizard_replacement = replacements[0] if replacements else None
        target_score = wizard_target.get("score")
        replacement_score = wizard_replacement.get("score") if wizard_replacement else None
        if isinstance(target_score, (int, float)) and isinstance(replacement_score, (int, float)):
            wizard_bonus = max(0.0, float(target_score) - float(replacement_score))

    bonus_by_team = {team["name"]: 0.0 for team in ALL_TEAMS}
    bonus_notes = {team["name"]: "No weekly score bonus" for team in ALL_TEAMS}

    knight_roster = rosters_by_team.get("The Knight", [])
    knight_reported_lives = next(
        (row.get("lives_remaining") for row in knight_roster if row.get("lives_remaining") is not None),
        4,
    )
    knight_lives = max(1, min(4, int(knight_reported_lives)))
    bonus_by_team["The Knight"] = float((4 - knight_lives) * 5)
    bonus_notes["The Knight"] = f"Last Stand · {knight_lives} lives"

    gambler_bonus = float(seeded_pick(scoreboard_week, "gambler-flip", [12, -8])) if scores_revealed else 0.0
    bonus_by_team["The Gambler"] = gambler_bonus
    bonus_notes["The Gambler"] = ("Fate's draw · +12" if gambler_bonus > 0 else "Fate's draw · −8") if scores_revealed else "Fate's draw · revealed at kickoff"

    bonus_notes["The Hunter"] = "Marked Prey · +0 to start"
    bonus_by_team["The Wizard"] = wizard_bonus
    if wizard_target:
        replacement_name = wizard_replacement.get("player", "no replacement") if wizard_replacement else "no replacement"
        bonus_notes["The Wizard"] = f"Hex · {wizard_target.get('player')} → {replacement_name}"
    else:
        bonus_notes["The Wizard"] = "Hex draw pending roster"
    bonus_notes["The Oracle"] = "Prophecy not selected"
    bonus_notes["The Hydra"] = "Two-week shield intact"

    preliminary_totals = {
        name: float(score) + bonus_by_team.get(name, 0.0)
        for name, score in base_scores.items()
    }
    juggernaut_base = base_scores.get("The Juggernaut")
    if isinstance(juggernaut_base, (int, float)):
        teams_below = sum(
            1 for name, total in preliminary_totals.items()
            if name != "The Juggernaut" and total < float(juggernaut_base)
        )
        bonus_by_team["The Juggernaut"] = float(teams_below * 2)
        bonus_notes["The Juggernaut"] = f"Unstoppable Force · above {teams_below} teams"

    adjusted_scores = {
        team["name"]: (
            float(base_scores[team["name"]]) + bonus_by_team[team["name"]]
            if team["name"] in base_scores else None
        )
        for team in ALL_TEAMS
    }

    def lineup_html(team: dict, role: str, include_head: bool = True) -> str:
        rows = lineups.get(team["name"], [])
        by_slot: dict[str, list[dict]] = {}
        for row in rows:
            by_slot.setdefault(row.get("slot", ""), []).append(row)
        rendered_rows = []
        used_by_slot: dict[str, int] = {}
        for slot in LINEUP_SLOTS:
            slot_index = used_by_slot.get(slot, 0)
            candidates = by_slot.get(slot, [])
            row = candidates[slot_index] if slot_index < len(candidates) else {}
            used_by_slot[slot] = slot_index + 1
            player = escape(str(row.get("player") or "Awaiting roster"))
            nfl_team = escape(str(row.get("nfl_team") or "—"))
            score = row.get("score")
            score_text = f"{score:.1f}" if isinstance(score, (int, float)) else "—"
            display_slot = "FLX" if slot == "RWT FLEX" else slot
            rendered_rows.append(
                f'''<div class="lineup-row"><div class="lineup-slot">{display_slot}</div>
                <div class="lineup-player"><strong>{player}</strong><span>{nfl_team}</span></div>
                <div class="lineup-points">{score_text}</div></div>'''
            )
        bonus = bonus_by_team.get(team["name"], 0.0)
        bonus_text = f"{bonus:+.1f}" if bonus else "0.0"
        rendered_rows.append(
            f'''<div class="lineup-row bonus"><div class="lineup-slot">BONUS</div>
            <div class="lineup-player"><strong>{escape(bonus_notes.get(team['name'], 'No weekly score bonus'))}</strong></div>
            <div class="lineup-points">{bonus_text}</div></div>'''
        )
        total = adjusted_scores.get(team["name"])
        total_text = f"{total:.2f}" if isinstance(total, (int, float)) else "—"
        head_html = f'''<div class="score-card-head"><img src="{team['logo']}" alt="{team['name']} logo">
            <div><span>{role} · Week {scoreboard_week}</span><h3>{team['emoji']} {team['name']}</h3></div></div>''' if include_head else ""
        return f'''<div class="score-card {'vampire-side' if team['name'] == 'The Vampire' else ''}" data-sigil="{team['emoji']}" style="--score-accent:{team['accent']}">
            {head_html}<div class="lineup-list">{''.join(rendered_rows)}</div>
        </div>'''

    def bench_html(team: dict) -> str:
        starters = {row.get("player_id") for row in lineups.get(team["name"], [])}
        position_order = {position: index for index, (position, _) in enumerate(BASE_ROSTER)}
        bench = sorted(
            [row for row in rosters_by_team.get(team["name"], []) if row.get("player_id") not in starters],
            key=lambda row: (position_order.get(row.get("position"), 99), str(row.get("player", ""))),
        )
        rows = "".join(
            f'''<div class="bench-row"><span>{escape(str(row.get("position") or "—"))}</span>
            <strong>{escape(str(row.get("player") or "Awaiting roster"))}</strong><b>{f'{row["score"]:.1f}' if isinstance(row.get("score"), (int, float)) else '—'}</b></div>'''
            for row in bench
        )
        empty = "<div class='score-note'>No bench data available.</div>"
        return f'<div class="bench-list"><div class="bench-title">Bench · {len(bench)} players</div>{rows or empty}</div>'

    ranked_teams = sorted(
        ALL_TEAMS,
        key=lambda team: (
            adjusted_scores.get(team["name"]) if adjusted_scores.get(team["name"]) is not None else float("-inf"),
            0 if team["name"] != "The Vampire" else -1,
        ),
        reverse=True,
    )
    rank_rows = []
    vampire_rank = next((index for index, team in enumerate(ranked_teams, start=1) if team["name"] == "The Vampire"), len(ranked_teams) + 1)
    for rank, team in enumerate(ranked_teams, start=1):
        total = adjusted_scores.get(team["name"])
        total_text = f"{total:.2f}" if isinstance(total, (int, float)) else "—"
        bonus = bonus_by_team.get(team["name"], 0.0)
        detail = f"Bonus {bonus:+.1f}" if bonus else "No bonus"
        if team["name"] == "The Vampire":
            status_label, status_class = "The hunter", "hunter"
        elif rank < vampire_rank:
            status_label, status_class = "Safe", "safe"
        elif rank > vampire_rank:
            status_label, status_class = "On pace to lose a life", "danger"
        else:
            status_label, status_class = "Status pending", "unknown"
        rank_rows.append(
            f'''<div class="rank-tile {'vampire-rank' if team['name'] == 'The Vampire' else ''}" style="--rank-accent:{team['accent']}">
                <div class="rank-number">{rank}</div>
                <div class="rank-team"><strong>{team['emoji']} {team['name']}</strong><span class="rank-status {status_class}">{status_label}</span><span>{detail}</span></div>
                <div class="rank-score">{total_text}</div>
            </div>'''
        )
    league_board = f'''<div class="league-board"><div class="league-board-title">Week {scoreboard_week} standings</div>
        <div class="rank-tiles">{''.join(rank_rows)}</div>
    </div>'''

    board_cols = st.columns([1.8, 1.8, 1.4], gap="medium")
    with board_cols[0]:
        with st.container(border=True):
            st.markdown('<div class="opponent-picker-title">Week {}</div>'.format(scoreboard_week), unsafe_allow_html=True)
            picker_cols = st.columns([.38, .62], gap="small")
            with picker_cols[0]:
                st.image(VAMPIRE_TEAM["logo"], width=96)
            with picker_cols[1]:
                st.markdown(f'<div style="padding-top:1.1rem;color:#f5e9e2;font:600 1.35rem Cormorant Garamond,serif;">{VAMPIRE_TEAM["emoji"]} {VAMPIRE_TEAM["name"]}</div>', unsafe_allow_html=True)
        st.markdown(lineup_html(VAMPIRE_TEAM, "THE HUNTER", include_head=False), unsafe_allow_html=True)
        st.markdown(bench_html(VAMPIRE_TEAM), unsafe_allow_html=True)
    with board_cols[1]:
        opponent_name = st.session_state.get("scoreboard_opponent", "The King")
        opponent_team = next(team for team in CREATURES if team["name"] == opponent_name)
        with st.container(border=True):
            st.markdown('<div class="opponent-picker-title">Choose your prey</div>', unsafe_allow_html=True)
            picker_cols = st.columns([.38, .62], gap="small")
            with picker_cols[0]:
                st.image(opponent_team["logo"], width=96)
            with picker_cols[1]:
                opponent_name = st.selectbox(
                    "Opponent",
                    [team["name"] for team in CREATURES],
                    format_func=lambda name: f"{next(team['emoji'] for team in CREATURES if team['name'] == name)}  {name}",
                    key="scoreboard_opponent",
                    label_visibility="collapsed",
                )
        opponent_team = next(team for team in CREATURES if team["name"] == opponent_name)
        st.markdown(lineup_html(opponent_team, "THE HUNTED", include_head=False), unsafe_allow_html=True)
        st.markdown(bench_html(opponent_team), unsafe_allow_html=True)
    with board_cols[2]:
        st.markdown(league_board, unsafe_allow_html=True)

with about_tab:
    st.header("About The Vampire Hunt")
    st.write("A quick reference for the league rules, roster settings, weekly lineup process, and scoring.")

    st.subheader("How the league works")
    st.markdown(
        """
        - There are 12 teams: The Vampire and 11 opposing creatures.
        - The season runs for 18 scoring weeks.
        - Each week, teams are compared by their fantasy football score.
        - When The Vampire outscores an opponent, that opponent loses one life.
        - After a successful hunt, The Vampire may steal one player from that opponent's roster.
        - The Vampire may set a different starting lineup every week. Other teams use their standard roster and best-ball scoring.
        """
    )

    st.subheader("Roster settings")
    st.markdown(
        """
        **All teams (including The Vampire)**

        - 2 QB
        - 6 RB
        - 6 WR
        - 2 TE
        - 2 DST
        - 2 K

        **Weekly best-ball starters shown on the Scoreboard**

        QB, RB, RB, WR, WR, TE, FLX, DST, K, plus a Bonus slot when a team has a weekly league bonus.

        Best ball takes the highest-scoring eligible players at each position first, then fills the flex with the best remaining eligible player.
        """
    )

    st.subheader("Team abilities")
    abilities = [
        {
            "Team": team["name"],
            "Starting lives": team["lives"],
            "Ability": team["ability"],
            "Rule": team["rule"],
        }
        for team in ALL_TEAMS
    ]
    st.dataframe(
        abilities,
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("Scoring")
    scoring_rows = [
        ("Off", "Fumbles Lost", "FL", -2),
        ("Off", "Fumbles Recovered for Touchdowns - Offense", "FRTD", 6),
        ("Off", "Interceptions Thrown", "Int", -2),
        ("Off", "Kickoff Return Yards", "KRY", 0.04),
        ("Off", "Kickoff Punt Return Touchdown Yards", "RPTY", 6),
        ("Off", "Passing Touchdowns", "TD", 6),
        ("Off", "Passing Yards", "YDS", 0.04),
        ("Off", "Punt Return Yards", "PRY", 0.05),
        ("Off", "Receiving Touchdowns", "TD", 6),
        ("Off", "Receiving Yards", "YDS", 0.1),
        ("Off", "Receptions", "REC", 1),
        ("Off", "Rushing Touchdowns", "TD", 6),
        ("Off", "Rushing Yards", "YDS", 0.1),
        ("Off", "Sack Yards Lost", "SkY", -0.1),
        ("Off", "Two Point Conversion Passes", "2Pa", 2.08),
        ("Off", "Two Point Conversion Receptions", "2Rc", 3.2),
        ("Off", "Two Point Conversion Rushes", "2Ru", 2.2),
        ("Kick", "Extra Points Made", "XP", 1.06),
        ("Kick", "Extra Points Missed", "XPM", -0.55),
        ("Kick", "Field Goal Yards - Sum of all in game", "FGYd", 0.1),
        ("Kick", "Field Goals Missed", "FGM", -1.25),
        ("DST", "Blocked Kicks", "BK", 2),
        ("DST", "Extra/2Pt Point Attempts Returned for 2Pt", "XPB2P", 2),
        ("DST", "Points Allowed by the Defense", "PA-Def", -0.25),
        ("DST", "Sacks", "Sk", 2),
        ("DST", "Safeties by the Defense", "Sft", 2),
        ("DST", "Takeaways", "TA", 2),
        ("DST", "Total Yards Allowed", "YdA", -0.01),
        ("DST", "Touchdowns - Defense/Special Teams", "TDDST", 6),
    ]
    scoring_rows = [
        {"Group": group, "Category": category, "Stat key": stat_key, "Points": points}
        for group, category, stat_key, points in scoring_rows
    ]
    st.dataframe(
        scoring_rows,
        hide_index=True,
        use_container_width=True,
    )
