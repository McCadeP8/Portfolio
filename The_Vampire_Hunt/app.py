from base64 import b64encode
import csv
import hashlib
import io
from html import escape
from pathlib import Path
import re

import streamlit as st

from fantrax_data import (
    DEFENSE_TEAMS,
    display_player_name,
    fetch_player_directory,
    fetch_roster_week,
    fetch_standings,
    enrich_roster_rows,
    load_snapshot,
)
from nfl_games import fetch_week_games, followers_left, game_marker, games_are_final, team_code

# Keep the app bootable while Streamlit Cloud rolls from an older data module.
# Player scores become available automatically as soon as the updated helper is
# present; until then the existing team-score and roster views still work.
try:
    from fantrax_data import fetch_player_scores
except ImportError:
    def fetch_player_scores(week: int, auth_cookie: str = "") -> dict[str, float]:
        import re
        import requests

        def score_value(cell):
            if isinstance(cell, (int, float)) and not isinstance(cell, bool):
                return float(cell)
            if isinstance(cell, str):
                value = cell.strip().replace(",", "")
                return float(value) if re.fullmatch(r"-?\d+(?:\.\d+)?", value) else None
            if isinstance(cell, dict):
                for key in ("value", "rawValue", "content", "text", "displayValue", "score"):
                    if key in cell:
                        value = score_value(cell[key])
                        if value is not None:
                            return value
            return None

        request_data = {
            "view": "STATS",
            "positionOrGroup": "ALL",
            "seasonOrProjection": "SEASON_23l_BY_PERIOD",
            "timeframeTypeCode": "BY_PERIOD",
            "transactionPeriod": str(int(week)),
            "statusOrTeamFilter": "ALL_TAKEN",
            "sortType": "SCORE",
            "sortReversed": False,
            "maxResultsPerPage": "500",
            "pageNumber": "1",
        }
        response = requests.post(
            "https://www.fantrax.com/fxpa/req",
            params={"leagueId": "et040dehmtxkchmx"},
            json={"msgs": [{"method": "getPlayerStats", "data": request_data}]},
            headers={"User-Agent": "Mozilla/5.0 (compatible; VampireHunt/1.0)"},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()["responses"][0]["data"]
        headers = data.get("tableHeader", {}).get("cells", [])
        score_index = next(
            index for index, header in enumerate(headers)
            if str(header.get("key", "")).lower() == "fpts"
            or str(header.get("sortKey", "")).upper() == "SCORE"
        )
        scores = {}
        for row in data.get("statsTable", []):
            scorer = row.get("scorer") or {}
            cells = row.get("cells") or []
            scorer_id = str(scorer.get("scorerId", "")).strip()
            if not scorer_id or score_index >= len(cells):
                continue
            value = score_value(cells[score_index])
            if value is None:
                continue
            scores[scorer_id] = value
            if scorer.get("team") and scorer.get("teamId") is not None:
                scores[str(scorer["teamId"])] = value
        return scores

try:
    from fantrax_data import fetch_available_players
except ImportError:
    def fetch_available_players(week: int) -> list[dict]:
        return []

try:
    from fantrax_data import fetch_fantasypros_weekly_rankings
except ImportError:
    def fetch_fantasypros_weekly_rankings(week: int) -> list[dict]:
        return []


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
        "rule": "Gains +2 for every opponent left beneath its score each week.",
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
CREATURE_LABELS = {
    "The King": "Aurelian the King",
    "The Juggernaut": "Brakk the Juggernaut",
    "The Hydra": "Vesper the Hydra",
    "The Oracle": "Sibyl the Oracle",
    "The Knight": "Roland the Knight",
    "The Wizard": "Eldrin the Wizard",
    "The Guardian": "Aegis the Guardian",
    "The Hunter": "Garrick the Hunter",
    "The Gambler": "Rook the Gambler",
    "The Alpha": "Fenrir the Alpha",
    "The Mortal": "Elias the Mortal",
}
BASE_ROSTER = [("QB", 2), ("RB", 6), ("WR", 6), ("TE", 2), ("DST", 2), ("K", 2)]
VAMPIRE_ROSTER = BASE_ROSTER
VAMPIRE_SHEET_ID = "15PuUSykO7h835WDMpThGmdWPNkckEUpiBW05pFO8NAs"


@st.cache_data(ttl=30, show_spinner=False)
def load_vampire_sheet() -> tuple[list[str], list[dict[str, str]]]:
    """Read the public lineup tracker as CSV; no Google credentials are stored in the app."""
    import requests

    url = f"https://docs.google.com/spreadsheets/d/{VAMPIRE_SHEET_ID}/export?format=csv&gid=0"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")))
    headers = [str(field or "").strip() for field in (reader.fieldnames or [])]
    teams = [field for field in headers[2:] if field]
    rows = []
    for row in reader:
        rows.append({str(key).strip(): str(value or "").strip() for key, value in row.items() if key})
    return teams, rows


@st.cache_data(ttl=3600, show_spinner=False)
def fantrax_player_directory() -> dict:
    return fetch_player_directory()


def sheet_vampire_rows(week: int, base_rows: list[dict], players: dict, team_name: str | None = None) -> list[dict]:
    """Overlay the selected Google Sheet column onto the Vampire roster."""
    team_name = team_name or active_vampire_name
    creature_rows = [row for row in base_rows if row.get("team") not in {"The Vampire", team_name}]
    if not vampire_sheet_rows:
        return creature_rows
    week_rows = [row for row in vampire_sheet_rows if str(row.get("Week", "")) == str(int(week))]
    if not week_rows:
        return creature_rows
    slots = []
    for row in week_rows:
        slot = str(row.get("Slot", "")).strip()
        player_name = str(row.get(team_name, "")).strip()
        if not slot or slot.lower() == "stolen" or not player_name:
            continue
        if slot == "K1" and any(existing_slot == "K1" for existing_slot, _ in slots):
            slot = "K2"
        slots.append((slot, player_name))
    if not slots:
        return creature_rows

    base_vampire = [row for row in base_rows if row.get("team") == "The Vampire" or row.get("team") == team_name]
    lives = next((row.get("lives_remaining") for row in base_vampire if row.get("lives_remaining") is not None), None)
    by_name = {player_match_key(row.get("player", "")): row for row in base_vampire}
    by_directory_name = {}
    for player_id, player in players.items():
        name = display_player_name(player.get("name", ""))
        if name:
            by_directory_name[player_match_key(name)] = (str(player_id), player)
    defense_ids = {player_match_key(name): (team_id, nfl_team) for team_id, (name, nfl_team) in DEFENSE_TEAMS.items()}

    rebuilt = []
    for slot, player_name in slots:
        clean_name = re.sub(r"\s*\([^)]*\)\s*$", "", player_name).strip()
        existing = by_name.get(player_match_key(clean_name), {})
        directory_entry = by_directory_name.get(player_match_key(clean_name))
        player_id = str(existing.get("player_id", ""))
        player_info = {}
        if directory_entry:
            player_id, player_info = directory_entry
        position = slot.rstrip("0123456789")
        if position == "DST" and player_match_key(clean_name) in defense_ids:
            player_id, nfl_team = defense_ids[player_match_key(clean_name)]
        else:
            nfl_team = str(existing.get("nfl_team") or player_info.get("team") or "FA")
        rebuilt.append({
            "week": int(week),
            "team_id": str(existing.get("team_id", "vampire-sheet")),
            "team": team_name,
            "lives_remaining": lives,
            "player_id": player_id,
            "player": clean_name,
            "position": position,
            "nfl_team": nfl_team,
            "status": "ROSTERED",
            "score": None,
            "slot": slot,
        })
    return creature_rows + rebuilt


@st.cache_data(ttl=30, show_spinner=False)
def fantrax_roster_for_week(week: int) -> tuple[list[dict], str]:
    try:
        players = fantrax_player_directory()
        rows = fetch_roster_week(int(week), players)
        if rows:
            return sheet_vampire_rows(int(week), rows, players), "live"
    except Exception:
        pass
    snapshot = load_snapshot()
    rows = snapshot.get("rosters", {}).get(str(int(week)), [])
    return sheet_vampire_rows(int(week), rows, {}), "snapshot"


@st.cache_data(ttl=30, show_spinner=False)
def vampire_world_rosters(week: int) -> dict[str, list[dict]]:
    """Build one sheet-backed Vampire roster per universe from the shared Fantrax pool."""
    players = fantrax_player_directory()
    try:
        raw = fetch_roster_week(int(week), players)
    except Exception:
        raw = load_snapshot().get("rosters", {}).get(str(int(week)), [])
    return {
        name: [row for row in sheet_vampire_rows(int(week), raw, players, name) if row.get("team") == name]
        for name in vampire_sheet_teams
    }


@st.cache_data(ttl=300, show_spinner=False)
def fantrax_standings() -> tuple[list[dict], str]:
    try:
        rows = fetch_standings()
        if rows:
            return rows, "live"
    except Exception:
        pass
    return load_snapshot().get("standings", []), "snapshot"


@st.cache_data(ttl=60, show_spinner=False)
def fantrax_player_scores(week: int) -> dict[str, float]:
    return fetch_player_scores(int(week))


@st.cache_data(ttl=90, show_spinner=False)
def nfl_week_games(season: int, week: int) -> list[dict]:
    return fetch_week_games(int(season), int(week))


@st.cache_data(ttl=60, show_spinner=False)
def fantrax_available_players(week: int) -> list[dict]:
    return fetch_available_players(int(week))


@st.cache_data(ttl=900, show_spinner=False)
def fantasypros_weekly_rankings(week: int) -> list[dict]:
    return fetch_fantasypros_weekly_rankings(int(week))


def automatic_active_week(snapshot: dict) -> tuple[int, int]:
    """Advance after the last NFL game of a week reaches final."""
    season = int(snapshot.get("season") or 2026)
    week = max(1, min(18, int(snapshot.get("current_week", 1))))
    while week < 18:
        try:
            games = nfl_week_games(season, week)
        except Exception:
            break
        if not games_are_final(games):
            break
        week += 1
    return week, season


def add_fantrax_player_scores(rows: list[dict], week: int) -> tuple[list[dict], str]:
    try:
        scores = fantrax_player_scores(int(week))
    except Exception:
        return rows, "unavailable"
    scored_rows = []
    for original in rows:
        row = dict(original)
        player_id = str(row.get("player_id", ""))
        if player_id in scores:
            row["score"] = scores[player_id]
        scored_rows.append(row)
    return scored_rows, "live"


def send_lineup_to_discord(submission: dict) -> None:
    """Post a completed Vampire roster without storing the webhook in code."""
    import requests

    webhook_url = str(st.secrets.get("DISCORD_WEBHOOK_URL", "")).strip()
    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL is missing from Streamlit Secrets.")

    position_order = ("QB", "RB", "WR", "TE", "K", "DST")
    fields = []
    copy_names = []
    for position in position_order:
        players = submission["lineup"].get(position, [])
        copy_names.extend(str(player.get("player", "")).strip() for player in players)
        player_lines = [
            f'''{index}. {player.get("player", "—")} ({player.get("nfl_team", "Other")})'''
            for index, player in enumerate(players, 1)
        ]
        fields.append(
            {
                "name": position,
                "value": "\n".join(player_lines) or "—",
                "inline": position not in {"RB", "WR"},
            }
        )

    payload = {
        "username": "The Vampire Hunt",
        "content": "Copy the lines inside the block into this Vampire's team column, starting at QB1:\n```\n" + "\n".join(copy_names + [""]) + "\n```",
        "embeds": [
            {
                "title": f'''🧛 New Vampire: {submission["team_name"]}''',
                "description": f'''A new roster has entered the Week {submission["week"]} hunt.''',
                "color": 10430009,
                "fields": fields,
                "footer": {"text": "20-player roster · Submitted through The Vampire Hunt"},
            }
        ],
    }
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()


def send_tribute_to_discord(owner: str, week: int, creature: str, follower: str) -> None:
    """Queue one confirmed weekly tribute for entry in the public realm sheet."""
    import requests

    webhook_url = str(st.secrets.get("DISCORD_WEBHOOK_URL", "")).strip()
    if not webhook_url:
        raise RuntimeError("The Discord webhook is not configured.")
    message = (
        f"🩸 **{owner} the Vampire has stolen {follower} from {team_label(creature)}!**\n"
        f"Week {week} · Tribute claimed using the current scoreboard.\n"
        f"Sheet entry: `{owner}` · Week `{week}` · `Stolen` → `{follower}`"
    )
    response = requests.post(webhook_url, json={"username": "The Vampire Hunt", "content": message}, timeout=15)
    response.raise_for_status()


LINEUP_SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE", "RWT FLEX", "DST", "K"]


def _scored_first(row: dict) -> tuple[bool, float, str]:
    score = row.get("score")
    return isinstance(score, (int, float)), float(score or 0), str(row.get("player", ""))


def best_ball_lineup(roster: list[dict]) -> list[dict]:
    """Choose eligible best-ball starters, filling the flex after fixed slots."""
    eligible = []
    seen_followers = set()
    for row in roster:
        if row.get("stolen"):
            continue
        follower_id = str(row.get("player_id") or "").strip() or str(row.get("player") or "").strip().casefold()
        if follower_id in seen_followers:
            continue
        seen_followers.add(follower_id)
        eligible.append(row)
    pools: dict[str, list[dict]] = {}
    for position in ("QB", "RB", "WR", "TE", "DST", "K"):
        pools[position] = sorted(
            [dict(row) for row in eligible if row.get("position") == position],
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


def seeded_pick(week: int, label: str, choices: list, universe: str = ""):
    digest = hashlib.sha256(f"et040dehmtxkchmx:{universe}:{week}:{label}".encode()).digest()
    return choices[int.from_bytes(digest[:8], "big") % len(choices)]


st.set_page_config(
    page_title="The Vampire Hunt",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    vampire_sheet_teams, vampire_sheet_rows = load_vampire_sheet()
except Exception:
    vampire_sheet_teams, vampire_sheet_rows = [], []
if not vampire_sheet_teams:
    vampire_sheet_teams = ["Vampire"]
active_vampire_name = st.selectbox(
    "Vampire",
    vampire_sheet_teams,
    key="active_vampire_name",
    label_visibility="visible",
)
# The selected sheet column is the Vampire identity for this multiverse.
if st.session_state.get("_last_active_vampire") != active_vampire_name:
    fantrax_roster_for_week.clear()
    fantrax_standings.clear()
    st.session_state["_last_active_vampire"] = active_vampire_name
VAMPIRE_TEAM["name"] = active_vampire_name
active_vampire_label = f"{active_vampire_name} the Vampire"
snapshot = load_snapshot()
active_week, nfl_season = automatic_active_week(snapshot)
previous_active_week = st.session_state.get("_automatic_active_week")
if previous_active_week is not None and previous_active_week != active_week:
    # Move every primary week control forward in an already-open browser session.
    st.session_state["creature_roster_week"] = active_week
    st.session_state["scoreboard_week"] = active_week
    st.session_state["realm_summary_week"] = active_week
st.session_state["_automatic_active_week"] = active_week


def team_label(name: str) -> str:
    return active_vampire_label if name == active_vampire_name else CREATURE_LABELS.get(name, name)


def player_match_key(name: str) -> str:
    """Normalize punctuation and generational suffixes for cross-source matching."""
    value = str(name or "").lower().replace("’", "'")
    # Common short-name variants used by different fantasy data providers.
    value = re.sub(r"\bcam(?=\s+skattebo\b)", "cameron", value)
    value = re.sub(r"\bkenny(?=\s+gainwell\b)", "kenneth", value)
    value = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?\b", "", value)
    value = re.sub(r"[^a-z0-9]", "", value)
    return value


def stolen_followers_before(week: int, realm_name: str | None = None) -> dict[str, int]:
    """Map stolen follower names to their claim week in one Vampire realm."""
    realm_name = realm_name or active_vampire_name
    stolen = {}
    for sheet_row in vampire_sheet_rows:
        if str(sheet_row.get("Slot", "")).strip().lower() != "stolen":
            continue
        try:
            claimed_week = int(str(sheet_row.get("Week", "")).strip())
        except (TypeError, ValueError):
            continue
        if claimed_week >= int(week):
            continue
        name = re.sub(r"\s*\([^)]*\)\s*$", "", str(sheet_row.get(realm_name, "")).strip())
        key = player_match_key(name)
        if key:
            stolen[key] = claimed_week
    return stolen


def claimed_followers_for_owner(realm_name: str) -> list[tuple[str, int]]:
    """Keep the claimed name as written in the sheet for the lineup picker."""
    claims = {}
    for sheet_row in vampire_sheet_rows:
        if str(sheet_row.get("Slot", "")).strip().lower() != "stolen":
            continue
        try:
            claimed_week = int(str(sheet_row.get("Week", "")).strip())
        except (TypeError, ValueError):
            continue
        name = re.sub(r"\s*\([^)]*\)\s*$", "", str(sheet_row.get(realm_name, "")).strip())
        key = player_match_key(name)
        if key:
            claims[key] = (name, claimed_week)
    return sorted(claims.values(), key=lambda item: (item[1], item[0]))


def mark_stolen_creature_followers(rows: list[dict], week: int, realm_name: str | None = None) -> list[dict]:
    """Keep stolen followers visible on creature rosters, but score them at zero."""
    stolen = stolen_followers_before(week, realm_name)
    if not stolen:
        return rows
    creature_names = {creature["name"] for creature in CREATURES}
    marked = []
    seen_stolen = set()
    for original in rows:
        row = dict(original)
        follower_key = player_match_key(row.get("player", ""))
        claimed_week = stolen.get(follower_key)
        if row.get("team") in creature_names and claimed_week is not None:
            row["stolen"] = True
            row["stolen_week"] = claimed_week
            row["score"] = 0.0
            seen_stolen.add(follower_key)
        marked.append(row)
    # A Fantrax transaction must not erase the historical creature slot.
    # The original Week 1 roster identifies which creature the follower came from.
    missing_stolen = set(stolen) - seen_stolen
    if missing_stolen:
        original_roster = enrich_roster_rows(load_snapshot().get("rosters", {}).get("1", []))
        for original in original_roster:
            follower_key = player_match_key(original.get("player", ""))
            if original.get("team") not in creature_names or follower_key not in missing_stolen:
                continue
            row = dict(original)
            row["week"] = int(week)
            row["stolen"] = True
            row["stolen_week"] = stolen[follower_key]
            row["score"] = 0.0
            marked.append(row)
            missing_stolen.remove(follower_key)
    return marked


def nfl_team_match_key(code: str) -> str:
    """Match the few NFL abbreviations Fantrax and FantasyPros spell differently."""
    value = str(code or "").upper().strip()
    return {"JAC": "JAX"}.get(value, value)


def complete_defense_recommendations(pool: list[dict], taken_teams: set[str]) -> list[dict]:
    """Keep every untaken NFL defense selectable if a rankings pull omits one."""
    listed_teams = {
        nfl_team_match_key(row.get("nfl_team", ""))
        for row in pool if row.get("position") == "DST"
    }
    completed = list(pool)
    for team_id, (short_name, nfl_team) in DEFENSE_TEAMS.items():
        code = nfl_team_match_key(nfl_team)
        if code in taken_teams or code in listed_teams:
            continue
        completed.append({
            "player_id": team_id,
            "player": "Arizona Cardinals" if code == "ARI" else short_name,
            "position": "DST",
            "nfl_team": nfl_team,
            "rank": 1000 + int(team_id),
            "projection": None,
            "score": None,
        })
        listed_teams.add(code)
    return completed


# Stable per-universe seed for all hidden season power schedules.
world_seed = hashlib.sha256(f"vampire-hunt-season-2026:{active_vampire_name}".encode()).hexdigest()


def life_diamonds(starting_lives: int, remaining_lives: int) -> str:
    """Keep every starting life visible, hollowing diamonds lost in this realm."""
    starting = max(0, int(starting_lives))
    remaining = max(0, min(starting, int(remaining_lives)))
    return "◆" * remaining + "◇" * (starting - remaining)


def mccade_week_one_preview() -> dict | None:
    """Treat current Week 1 Fantrax FPts as McCade's provisional final result."""
    if active_vampire_name != "McCade":
        return None
    rows, _ = fantrax_roster_for_week(1)
    rows = enrich_roster_rows(rows)
    rows, score_source = add_fantrax_player_scores(rows, 1)
    if score_source != "live":
        return None
    rosters = {
        name: [row for row in rows if row.get("team") == name]
        for name in [active_vampire_name] + [creature["name"] for creature in CREATURES]
    }
    lineups = {name: best_ball_lineup(roster) for name, roster in rosters.items()}
    if len(rosters[active_vampire_name]) != 20 or len(lineups[active_vampire_name]) != 9:
        return None
    base = {
        name: sum(float(row["score"]) for row in lineup if isinstance(row.get("score"), (int, float)))
        for name, lineup in lineups.items() if lineup
    }
    bonus = {name: 0.0 for name in rosters}
    knight_lives = next(
        (row.get("lives_remaining") for row in rosters["The Knight"] if row.get("lives_remaining") is not None),
        4,
    )
    bonus["The Knight"] = float((4 - max(1, min(4, int(knight_lives)))) * 5)
    bonus["The Gambler"] = float(seeded_pick(1, "gambler-flip", [12, -8], world_seed))
    vampire_lineup = lineups[active_vampire_name]
    wizard_target = seeded_pick(1, "wizard-hex", vampire_lineup, world_seed)
    eligible_positions = {"RB", "WR", "TE"} if wizard_target.get("slot") == "RWT FLEX" else {wizard_target.get("position")}
    chosen_ids = {row.get("player_id") for row in vampire_lineup}
    replacements = sorted(
        [row for row in rosters[active_vampire_name] if row.get("player_id") not in chosen_ids and row.get("position") in eligible_positions],
        key=_scored_first,
        reverse=True,
    )
    replacement_score = replacements[0].get("score") if replacements else None
    target_score = wizard_target.get("score")
    if isinstance(target_score, (int, float)) and isinstance(replacement_score, (int, float)):
        bonus["The Wizard"] = max(0.0, float(target_score) - float(replacement_score))
    preliminary = {name: score + bonus[name] for name, score in base.items()}
    if "The Juggernaut" in base:
        below = sum(
            1 for name, total in preliminary.items()
            if name != "The Juggernaut" and total < base["The Juggernaut"]
        )
        bonus["The Juggernaut"] = float(below * 2)
    scores = {name: score + bonus[name] for name, score in base.items()}
    vampire_score = scores.get(active_vampire_name)
    if vampire_score is None:
        return None
    outcomes = {}
    remaining = {}
    for creature in CREATURES:
        name = creature["name"]
        creature_score = scores.get(name)
        if creature_score is None:
            outcomes[name] = "pending"
        elif vampire_score > creature_score:
            outcomes[name] = "hit" if name == "The Hydra" else "lost"
        else:
            outcomes[name] = "survived"
        remaining[name] = creature["lives"] - (1 if outcomes[name] == "lost" else 0)
    return {"scores": scores, "outcomes": outcomes, "remaining": remaining}


# Week 1 is live again. Results and life changes stay pending until the normal
# weekly reveal; keep the preview helper available for a future finalization.
week_one_preview = None


def calculate_realm_battle(
    week: int,
    realm_name: str,
    vampire_roster: list[dict],
    creature_roster: list[dict],
    lives_before: dict[str, int],
    hydra_hit_before: bool,
    hunter_bonus_before: float,
) -> dict | None:
    """Score one universe from its own followers and resolve all eleven battles."""
    if len(vampire_roster) != 20:
        return None
    rosters = {realm_name: vampire_roster}
    rosters.update({creature["name"]: [row for row in creature_roster if row.get("team") == creature["name"]] for creature in CREATURES})
    lineups = {name: best_ball_lineup(roster) for name, roster in rosters.items()}
    if len(lineups[realm_name]) != 9 or not any(isinstance(row.get("score"), (int, float)) for row in vampire_roster):
        return None
    base = {
        name: sum(float(row["score"]) for row in lineup if isinstance(row.get("score"), (int, float)))
        for name, lineup in lineups.items() if len(lineup) == 9
    }
    seed = hashlib.sha256(f"vampire-hunt-season-2026:{realm_name}".encode()).hexdigest()
    bonus = {name: 0.0 for name in rosters}
    bonus["The Knight"] = float((4 - max(1, lives_before["The Knight"])) * 5)
    bonus["The Gambler"] = float(seeded_pick(week, "gambler-flip", [12, -8], seed))
    bonus["The Hunter"] = hunter_bonus_before
    oracle_weeks = sorted(range(5, 16), key=lambda number: hashlib.sha256(f"oracle:{seed}:{number}".encode()).digest())[:3]
    if week in oracle_weeks:
        bonus["The Oracle"] = 20.0

    vampire_lineup = lineups[realm_name]
    hex_target = seeded_pick(week, "wizard-hex", vampire_lineup, seed)
    hex_positions = {"RB", "WR", "TE"} if hex_target.get("slot") == "RWT FLEX" else {hex_target.get("position")}
    starter_ids = {row.get("player_id") for row in vampire_lineup}
    replacements = sorted(
        [row for row in vampire_roster if row.get("player_id") not in starter_ids and row.get("position") in hex_positions],
        key=_scored_first,
        reverse=True,
    )
    target_score = hex_target.get("score")
    replacement_score = replacements[0].get("score") if replacements else None
    if isinstance(target_score, (int, float)) and isinstance(replacement_score, (int, float)):
        bonus["The Wizard"] = max(0.0, float(target_score) - float(replacement_score))

    preliminary = {name: score + bonus[name] for name, score in base.items()}
    if "The Juggernaut" in base:
        bonus["The Juggernaut"] = float(2 * sum(
            total < base["The Juggernaut"] for name, total in preliminary.items() if name != "The Juggernaut"
        ))
    scores = {name: score + bonus[name] for name, score in base.items()}
    vampire_score = scores[realm_name]
    lives_after = dict(lives_before)
    outcomes = {}
    hydra_hit_after = False
    hunter_bonus_after = hunter_bonus_before
    for creature in CREATURES:
        name = creature["name"]
        creature_score = scores.get(name)
        if creature_score is None:
            outcomes[name] = "pending"
            continue
        if vampire_score > creature_score:
            if name == "The Hydra" and not hydra_hit_before:
                outcomes[name] = "hit"
                hydra_hit_after = True
            else:
                outcomes[name] = "lost"
                lives_after[name] = max(0, lives_after[name] - 1)
        else:
            outcomes[name] = "survived"
            if name == "The Hunter" and creature_score > vampire_score:
                hunter_bonus_after += 2.0
    return {
        "scores": scores,
        "outcomes": outcomes,
        "remaining": lives_after,
        "hydra_hit": hydra_hit_after,
        "hunter_bonus": hunter_bonus_after,
    }


def hydra_life_due_after(prior_wins: list[bool]) -> bool:
    """A first consecutive win is a hit; the second removes one Hydra life."""
    hit_pending = False
    lives_left = 2
    for win in prior_wins:
        if not win:
            hit_pending = False
        elif hit_pending:
            lives_left -= 1
            hit_pending = False
        else:
            hit_pending = True
    return hit_pending and lives_left > 0


def hydra_life_due_this_week(week: int, realm_name: str) -> bool:
    """Verify the selected realm's earlier Fantrax results before unlocking Hydra tribute."""
    if week <= 1:
        return False
    prior_wins = []
    for prior_week in range(1, week):
        rows, _ = fantrax_roster_for_week(prior_week)
        rows = enrich_roster_rows(rows)
        rows, score_source = add_fantrax_player_scores(rows, prior_week)
        if score_source != "live":
            return False
        rows = mark_stolen_creature_followers(rows, prior_week, realm_name)
        vampire_roster = [row for row in rows if row.get("team") == realm_name]
        hydra_roster = [row for row in rows if row.get("team") == "The Hydra"]
        vampire_lineup = best_ball_lineup(vampire_roster)
        hydra_lineup = best_ball_lineup(hydra_roster)
        if len(vampire_roster) != 20 or len(vampire_lineup) != 9 or len(hydra_lineup) != 9:
            return False
        vampire_score = sum(float(row["score"]) for row in vampire_lineup if isinstance(row.get("score"), (int, float)))
        hydra_score = sum(float(row["score"]) for row in hydra_lineup if isinstance(row.get("score"), (int, float)))
        prior_wins.append(vampire_score > hydra_score)
    return hydra_life_due_after(prior_wins)


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
        gap: 3.2rem;
        border-bottom: 1px solid #30292e;
    }

    .stTabs [data-baseweb="tab"] {
        height: 4.15rem;
        padding: 0 .35rem;
        color: #8f8788;
        background: transparent;
        font: 700 1.35rem/1 'Inter', sans-serif !important;
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        letter-spacing: .12em;
        text-transform: uppercase;
    }

    /* Streamlit renders each label inside a nested button/span; keep the
       typography large at every level so the visible label cannot shrink. */
    .stTabs [data-baseweb="tab"] *,
    .stTabs [data-baseweb="tab"] button,
    .stTabs [data-baseweb="tab"] span {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
    }

    /* Current Streamlit tab markup uses the stTab test id rather than
       BaseWeb's older data attribute. */
    .stTabs [data-testid="stTab"],
    .stTabs [data-testid="stTab"] *,
    .stTabs [data-testid="stTab"] p {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
    }
    [data-testid="stTabs"] [data-testid="stTab"],
    [data-testid="stTabs"] [data-testid="stTab"] *,
    [data-testid="stTabs"] [data-testid="stTab"] p {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
    }
    [data-testid="stTab"] {
        min-height: 4.2rem !important;
    }
    [data-testid="stTab"] p,
    [data-testid="stTab"] [data-testid="stMarkdownContainer"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
        letter-spacing: .04em !important;
    }
    [role="tab"] p,
    [role="tab"] [data-testid="stMarkdownContainer"],
    [role="tab"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
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
    .roster-row.stolen-following { background:linear-gradient(90deg,rgba(172,46,68,.25),rgba(38,19,25,.55)); box-shadow:inset 3px 0 #d4546a; }
    .roster-row.stolen-following .player strong { color:#ffd9df; }
    .stolen-badge { display:inline-block; margin-left:.6rem; padding:.17rem .4rem; border:1px solid #b74b60; border-radius:3px; background:#521d2b; color:#ffd7dc; font:700 .55rem 'Inter',sans-serif; letter-spacing:.05em; text-transform:uppercase; }
    .stolen-score-name { color:#ffb6c1 !important; }
    .stolen-origin { display:block; margin-top:.1rem; color:#a96875; font:500 .57rem 'Inter',sans-serif; }
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
    .lineup-row.stolen-following, .bench-row.stolen-following { background:linear-gradient(90deg,rgba(155,38,60,.22),rgba(30,17,22,.44)); }
    .lineup-slot { color:var(--score-accent); font:700 .58rem 'Inter',sans-serif; letter-spacing:.08em; }
    .lineup-player strong { display:block; color:#dcd3cc; font:500 .78rem 'Inter',sans-serif; }
    .lineup-player span { color:#746d6e; font:500 .59rem 'Inter',sans-serif; }
    .lineup-player .stolen-origin { color:#bd7d89; }
    .lineup-player .game-meta { display:flex; align-items:center; flex-wrap:wrap; gap:.35rem; margin-top:.12rem; }
    .game-marker { display:inline-flex; align-items:center; padding:.12rem .35rem; border:1px solid #4b4145; border-radius:3px; color:#b9aaa8; background:#211b1e; font:700 .54rem 'Inter',sans-serif; font-style:normal; white-space:nowrap; }
    .game-marker.scheduled { color:#e0bb78; border-color:#70522f; background:#2b2118; }
    .game-marker.live { color:#a8e8ba; border-color:#417950; background:#1a2a1e; }
    .game-marker.final { color:#9e9798; border-color:#484245; background:#1d1a1d; }
    .game-marker.bye { color:#777073; border-color:#393438; background:#171518; }
    .lineup-points { color:#e9dfd6; font:600 .86rem 'Inter',sans-serif; text-align:right; padding-right:.28rem; }
    .lineup-row.bonus { margin-top:.35rem; background:color-mix(in srgb,var(--score-accent) 8%,#151215); border-top:1px solid color-mix(in srgb,var(--score-accent) 42%,#302a2e); }
    .score-total { display:flex; align-items:end; justify-content:space-between; padding:1rem; background:#0c0b0d; border-top:1px solid #332c31; }
    .score-total span { color:#777071; font:600 .6rem 'Inter',sans-serif; letter-spacing:.12em; text-transform:uppercase; }
    .score-total b { color:var(--score-accent); font:700 2rem 'Cormorant Garamond',serif; }

    .league-board { --score-accent:#9f2639; min-height:1035px; box-sizing:border-box; padding:.7rem; background:linear-gradient(160deg,#241117,#0e0d0f 68%); }
    .league-board-title { color:#f0e2d9; font:700 1.8rem 'Cormorant Garamond',serif; margin:.15rem .25rem .7rem; }
    .rank-tiles { display:grid; height:calc(100% - 3rem); grid-template-rows:repeat(12,minmax(0,1fr)); gap:.45rem; }
    .rank-tile { position:relative; display:grid; grid-template-columns:26px minmax(0,1fr) 28px auto; gap:.45rem; align-items:center; min-height:55px; padding:.48rem .58rem; overflow:hidden; background:linear-gradient(100deg,color-mix(in srgb,var(--rank-accent) 20%,#171418),#111012 75%); border:1px solid color-mix(in srgb,var(--rank-accent) 35%,#2d282c); border-radius:5px; }
    .rank-team { min-width:0; }
    .rank-score { grid-column:4; white-space:nowrap; }
    .rank-tile.vampire-rank { border-color:#cf4058; background:linear-gradient(100deg,#4a1520,#171014 75%); box-shadow:0 0 15px rgba(190,40,64,.25); }
    .rank-tile.vampire-rank:after { content:none; }
    .rank-tile.vampire-rank { min-height:75px; grid-template-columns:28px minmax(0,1fr) 30px auto; padding:.55rem .62rem; }
    .rank-tile.vampire-rank .rank-team strong { color:#fff0e9; font-size:.98rem; }
    .rank-tile.vampire-rank .rank-team span { color:#e28b98; }
    .rank-tile.vampire-rank .rank-number { font-size:.82rem; }
    .rank-tile.vampire-rank .rank-score { color:#ffb5bd; font-size:1.05rem; }
    .rank-number { color:var(--rank-accent); font:700 .76rem 'Inter',sans-serif; text-align:center; }
    .rank-pending { display:grid; place-items:center; width:27px; height:27px; border:1px solid color-mix(in srgb,var(--rank-accent) 66%,#4b4145); border-radius:99px; color:#f4e9e2; background:color-mix(in srgb,var(--rank-accent) 28%,#1b1619); font:700 .72rem 'Inter',sans-serif; box-shadow:0 0 11px color-mix(in srgb,var(--rank-accent) 16%,transparent); }
    .rank-tile.vampire-rank .rank-pending { width:29px; height:29px; color:#fff; border-color:#e05268; background:#802338; box-shadow:0 0 14px rgba(224,82,104,.38); }
    .rank-pending.final, .rank-tile.vampire-rank .rank-pending.final { color:#fff; background:#080808; border-color:#6e696b; box-shadow:none; }
    .rank-team strong { display:block; overflow:hidden; color:#ddd3cc; font:600 .86rem 'Inter',sans-serif; white-space:nowrap; text-overflow:ellipsis; }
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
    .bench-row .bench-meta { display:inline-flex; align-items:center; gap:.28rem; margin-left:.35rem; color:#777071; font:500 .55rem 'Inter',sans-serif; }
    .bench-row b { color:#a49b97; font:600 .67rem 'Inter',sans-serif; text-align:right; }
    .opponent-picker-title { color:#d9c9c0; font:600 .62rem 'Inter',sans-serif; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.35rem; }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.opponent-picker-title) { min-height:108px; box-sizing:border-box; background:linear-gradient(145deg,#24151b,#130f12); border:1px solid #8f3a4c; border-radius:6px; padding:.55rem .7rem .7rem; box-shadow:0 0 22px rgba(159,38,57,.18); }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.opponent-picker-title) img { border-radius:5px; box-shadow:0 0 18px rgba(159,38,57,.35); }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.opponent-picker-title) [data-baseweb="select"] > div { min-height:62px; background:rgba(65,25,34,.92); border:1px solid #a34b60; color:#f5e9e2; font:600 1rem 'Cormorant Garamond',serif; box-shadow:0 0 18px rgba(159,38,57,.16); }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.opponent-picker-title) [data-baseweb="select"] svg { color:#e3a5ad; }

    .available-intro { display:flex; justify-content:space-between; align-items:end; gap:1rem; margin:.35rem 0 1.1rem; padding:1.15rem 1.3rem; background:linear-gradient(120deg,#251117,#111012 72%); border:1px solid #64303b; border-radius:6px; }
    .available-intro h2 { margin:0; color:#f0e3db; font:700 2rem 'Cormorant Garamond',serif; }
    .available-intro p { max-width:690px; margin:.25rem 0 0; color:#988f8d; font:500 .76rem/1.55 'Inter',sans-serif; }
    .available-week { flex:0 0 auto; color:#df8795; font:700 .7rem 'Inter',sans-serif; letter-spacing:.13em; text-transform:uppercase; }
    .pool-section { --pool-accent:#a82e43; margin:0 0 1.05rem; overflow:hidden; background:#111012; border:1px solid color-mix(in srgb,var(--pool-accent) 42%,#302a2f); border-radius:6px; }
    .pool-heading { display:flex; justify-content:space-between; align-items:center; padding:.8rem 1rem; background:linear-gradient(100deg,color-mix(in srgb,var(--pool-accent) 22%,#191519),#121012 74%); border-bottom:1px solid color-mix(in srgb,var(--pool-accent) 36%,#302a2f); }
    .pool-heading strong { color:#f1e5dd; font:700 1.45rem 'Cormorant Garamond',serif; }
    .pool-heading span { color:var(--pool-accent); font:700 .68rem 'Inter',sans-serif; letter-spacing:.13em; text-transform:uppercase; }
    .pool-row { display:grid; grid-template-columns:42px minmax(150px,1fr) 65px; gap:.5rem; align-items:center; min-height:42px; padding:0 .9rem; border-bottom:1px solid #292428; }
    .pool-row:last-child { border-bottom:0; }
    .pool-row.header { min-height:31px; color:#746d6e; font:700 .55rem 'Inter',sans-serif; letter-spacing:.12em; text-transform:uppercase; }
    .pool-rank { color:var(--pool-accent); font:700 .72rem 'Inter',sans-serif; }
    .pool-player { color:#ddd3cc; font:600 .79rem 'Inter',sans-serif; }
    .pool-team { overflow:hidden; color:#807879; font:500 .66rem 'Inter',sans-serif; white-space:nowrap; text-overflow:ellipsis; }
    .realm-intro { margin:.35rem 0 1rem; padding:1.15rem 1.3rem; background:linear-gradient(115deg,#251117,#111012 72%); border:1px solid #64303b; border-radius:6px; }
    .realm-intro h2 { margin:0; color:#f0e3db; font:700 2rem 'Cormorant Garamond',serif; }
    .realm-intro p { margin:.25rem 0 0; color:#988f8d; font:500 .76rem/1.5 'Inter',sans-serif; }
    .realm-table { overflow:hidden; background:#111012; border:1px solid #3d2b31; border-radius:6px; }
    .realm-row { display:grid; grid-template-columns:48px minmax(180px,1.2fr) 100px 110px minmax(170px,1fr) minmax(150px,1fr); gap:.55rem; align-items:center; min-height:65px; padding:.35rem .8rem; border-bottom:1px solid #292428; }
    .realm-row:last-child { border-bottom:0; }
    .realm-row.header { min-height:34px; color:#756d6e; font:700 .56rem 'Inter',sans-serif; letter-spacing:.1em; text-transform:uppercase; }
    .realm-row img { width:44px; height:44px; object-fit:cover; border-radius:4px; border:1px solid var(--realm-accent); }
    .realm-team strong { display:block; color:#e6dcd5; font:700 .9rem 'Inter',sans-serif; }
    .realm-team span,.realm-cell { color:#948a89; font:500 .67rem 'Inter',sans-serif; }
    .realm-score { color:#f0e5dc; font:700 1rem 'Inter',sans-serif; }
    .realm-row.vampire { background:linear-gradient(100deg,#4a1520,#171014 75%); box-shadow:inset 3px 0 #cf4058; }
    .realm-cross-wrap { overflow-x:auto; background:#111012; border:1px solid #3d2b31; border-radius:6px; }
    .realm-cross { width:100%; min-width:1080px; border-collapse:collapse; color:#eee; font-family:'Inter',sans-serif; }
    .realm-cross th,.realm-cross td { padding:.55rem .45rem; text-align:center; border-bottom:1px solid #292428; font-size:.7rem; }
    .realm-cross thead th { color:#a99b99; font-size:.58rem; text-transform:uppercase; letter-spacing:.06em; background:#1b1518; }
    .realm-cross thead th img { display:block; width:34px; height:34px; margin:0 auto .25rem; object-fit:cover; border-radius:50%; }
    .realm-cross tbody th { text-align:left; white-space:nowrap; color:#f0e5dc; font-size:.82rem; }
    .realm-cross tbody th small { display:block; color:#8f8182; font-size:.58rem; font-weight:500; }
    .realm-cross tbody tr.active { background:linear-gradient(100deg,#4a1520,#171014 75%); box-shadow:inset 3px 0 #cf4058; }
    .realm-cross td { color:#cbbfba; font-weight:700; }
    .realm-cross td.stolen { color:#e6b86a; font-weight:600; min-width:150px; }
    .realm-cross td.life-diamonds { color:#d45a68; letter-spacing:.12em; font-size:1rem; white-space:nowrap; }
    .realm-cross td.life-diamonds small { display:block; margin-top:.2rem; font:700 .52rem 'Inter',sans-serif; letter-spacing:.08em; }
    .realm-cross td.life-diamonds small.beat { color:#f6a7a9; }
    .realm-cross td.life-diamonds small.safe { color:#8fb4a4; }
    .realm-cross td.life-diamonds small.hit { color:#e7bb70; }
    .realm-cross td.life-diamonds small.live { color:#b5a8a0; }
    .realm-cross td.realm-score small { display:block; margin-top:.18rem; color:#998e8b; font:.55rem 'Inter',sans-serif; }

    @media (max-width: 760px) {
        .block-container { padding-top: 2rem; }
        .league-crest { width: 64px; height: 64px; }
        .vampire-card { grid-template-columns: 76px 1fr; }
        .vampire-card img { width: 72px; height: 72px; }
        .roster-mark { grid-column: 1 / -1; border-left: 0; border-top: 1px solid #603140; padding: .8rem 0 0; }
        .rules-strip { grid-template-columns: repeat(2, 1fr); }
        .stTabs [data-baseweb="tab-list"] { gap: 1.4rem; }
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
        .available-intro { align-items:start; flex-direction:column; }
        .pool-row { grid-template-columns:32px 1fr 62px; }
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

overview_tab, teams_tab, scoreboard_tab, realm_summary_tab, available_tab, about_tab = st.tabs(
    ["Overview", "Creatures", "Scoreboard", "Realm Summary", "Submit Lineup", "About"]
)

with overview_tab:
    st.markdown(
        f"""<div class="vampire-card">
            <img src="{VAMPIRE_LOGO}" alt="The Vampire logo">
            <div>
                <div class="ability-name">You are the monster in the dark</div>
                <div class="creature-name"><span class="emoji">🧛</span>{escape(active_vampire_label)}</div>
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
            <p>Every eighteen years, when the season turns and the stadium lights burn against the early dark, twelve creatures answer the same invitation. Eleven arrive believing they have been summoned to compete. The twelfth arrives hungry. This year, that creature is you: The Vampire.</p>
            <p>Your prey is not found in crypts or moonlit forests, but in eleven rival realms bound to the same cursed season. Every week, you face all eleven creatures at once, while the league's best performances quietly determine who grows weaker and who survives another night.</p>
            <p>The rule of blood is simple: if your weekly score is higher, your opponent loses one life. Ties go against you—the Vampire must outscore the creature to claim the kill. Every creature begins with a different number of lives and a different supernatural advantage, so every matchup carries its own danger.</p>
            <p>Whenever you defeat an opponent and take a life, you may steal one player from one creature you beat that week. That victory unlocks your next weekly choice: once each week, you may select a fresh 20-player following from your roster, your stolen players, and any other eligible choices. The eleven creatures cannot change their rosters this way; only the Vampire hunts and adapts from week to week.</p>
            <p>You have eighteen weeks to extinguish all eleven bloodlines. Study each creature's curse, decide which battle to pick, and build the strongest possible following before the next kickoff. By the final whistle, either every realm has fallen to your hunger—or dawn finds the Vampire with no lives left to claim.</p>
            <p><strong>Hunt wisely, feed completely, and leave no realm alive.</strong></p>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """<div class="rules-strip">
            <div class="rule-stat"><b>12</b><span>Creatures enter</span></div>
            <div class="rule-stat"><b>18</b><span>Weeks to hunt</span></div>
            <div class="rule-stat"><b>1 life</b><span>Lost when outscored</span></div>
            <div class="rule-stat"><b>1 follower</b><span>Stolen after a group of kills</span></div>
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
        lives_left = week_one_preview["remaining"].get(creature["name"], creature["lives"]) if week_one_preview else creature["lives"]
        hearts = life_diamonds(creature["lives"], lives_left)
        creature_logo = creature.get("logo", DEFAULT_LOGO)
        st.markdown(
            f"""<div class="monster-card" data-sigil="{creature['emoji']}" style="--card-accent:{creature['accent']}">
                <div class="lives">{lives_left} {'life' if lives_left == 1 else 'lives'} <span class="life-pips" title="{lives_left} of {creature['lives']} lives remain">{hearts}</span></div>
                <img src="{creature_logo}" alt="{creature['name']} logo">
                <div><div class="creature-name"><span class="emoji">{creature['emoji']}</span>{escape(team_label(creature['name']))}</div>
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
        format_func=lambda name: f"{next(team['emoji'] for team in all_teams if team['name'] == name)}  {team_label(name)}",
    )
    selected_team = next(team for team in all_teams if team["name"] == selected_name)
    is_vampire = selected_name == active_vampire_name
    selected_week = st.select_slider(
        "Roster week",
        options=list(range(1, 19)),
        value=active_week,
        format_func=lambda week: f"Week {week}",
        help="Review the roster and life timeline for any week. Vampire rosters can change after each hunt.",
        key="creature_roster_week",
    )

    roster_rows, roster_source = fantrax_roster_for_week(selected_week)
    roster_rows = enrich_roster_rows(roster_rows)
    roster_rows, player_score_source = add_fantrax_player_scores(roster_rows, selected_week)
    roster_rows = mark_stolen_creature_followers(roster_rows, selected_week)
    team_roster = [row for row in roster_rows if row.get("team") == selected_name]
    standings, _ = fantrax_standings()
    standing = next((row for row in standings if row.get("team") == selected_name), {})
    reported_lives = next(
        (row.get("lives_remaining") for row in team_roster if row.get("lives_remaining") is not None),
        standing.get("lives_remaining"),
    )
    if is_vampire:
        lives_display = "—"
    elif week_one_preview and selected_week >= 1:
        lives_display = str(week_one_preview["remaining"].get(selected_name, selected_team["lives"]))
    elif reported_lives is None:
        lives_display = str(selected_team["lives"])
    else:
        lives_display = str(min(int(reported_lives), int(selected_team["lives"])))
    condition_display = "HUNTING" if is_vampire else life_diamonds(selected_team["lives"], int(lives_display))

    previous_week = active_week - 1
    weekly_scores = snapshot.get("weekly_scores", {}).get(str(previous_week), []) if previous_week > 0 else []
    last_week_entry = next((row for row in weekly_scores if row.get("team") == selected_name), {})
    last_week_score = last_week_entry.get("score")
    last_week_finish = last_week_entry.get("finish")
    last_week_display = f"{last_week_score:.2f}" if isinstance(last_week_score, (int, float)) else "—"
    if isinstance(last_week_finish, int):
        suffix = "th" if 10 <= last_week_finish % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(last_week_finish % 10, "th")
        last_week_detail = f"{last_week_finish}{suffix} finish"
    elif previous_week < 1:
        last_week_detail = "No prior week"
    else:
        last_week_detail = "Awaiting Fantrax score"
    if week_one_preview and active_week == 1 and selected_name in week_one_preview["scores"]:
        last_week_display = f'{week_one_preview["scores"][selected_name]:.2f}'
        rank = 1 + sum(score > week_one_preview["scores"][selected_name] for score in week_one_preview["scores"].values())
        suffix = "th" if 10 <= rank % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(rank % 10, "th")
        last_week_detail = f"Week 1 · {rank}{suffix} finish"
    position_order = {position: index for index, (position, _) in enumerate(BASE_ROSTER)}
    team_roster.sort(
        key=lambda row: (
            position_order.get(str(row.get("position", "")), 99),
            str(row.get("player", "")),
        )
    )
    roster_html_parts = []
    for index, row in enumerate(team_roster, start=1):
        stolen_badge = f'<span class="stolen-badge">Stolen after Week {row["stolen_week"]}</span>' if row.get("stolen") else ""
        score_text = f'{row["score"]:.2f}' if isinstance(row.get("score"), (int, float)) else '—'
        roster_html_parts.append(
            f'''<div class="roster-row {'stolen-following' if row.get('stolen') else ''}">
                <div>{index}</div>
                <div class="player"><strong>{escape(str(row.get("player") or "Unknown follower"))}</strong>{stolen_badge}</div>
                <div><span class="pos-pill">{escape(str(row.get("position") or "—"))}</span></div>
                <div>{escape(str(row.get("nfl_team") or "FA"))}</div>
                <div class="score">{score_text}</div>
            </div>'''
        )
    roster_rows_html = "".join(roster_html_parts)
    if not roster_rows_html:
        roster_rows_html = '<div class="roster-empty"><div><strong>Roster unavailable</strong><br>The last Fantrax snapshot did not contain this team.</div></div>'
    roster_note = "Stolen followers remain visible here but score 0 FPts in this realm." if any(row.get("stolen") for row in team_roster) else ""
    roster_table = f'''<div class="roster-header">
        <div><div class="dossier-label">The active ledger</div><h3>Week {selected_week} roster</h3></div>
    </div>
    <div class="roster-table">
        <div class="roster-row header"><div>#</div><div>Follower</div><div>Position</div><div>NFL team</div><div>Week score</div></div>
        {roster_rows_html}
    </div>
    <div class="roster-note">{roster_note}</div>'''

    # A deterministic season timeline keeps special-week markers stable between reruns.
    oracle_weeks = sorted(
        sorted(range(5, 16), key=lambda week: hashlib.sha256(f"oracle:{world_seed}:{week}".encode()).digest())[:3]
    )
    active_vampire_rows = [row for row in roster_rows if row.get("team") == active_vampire_name]
    active_vampire_lineup = best_ball_lineup(active_vampire_rows)
    vampire_score = sum(
        float(row.get("score", 0))
        for row in active_vampire_lineup
        if isinstance(row.get("score"), (int, float))
    ) or next((row.get("score") for row in standings if row.get("team") == active_vampire_name), None)
    stolen_through_selected_week = stolen_followers_before(selected_week + 1)
    stolen_weeks = {
        stolen_through_selected_week[player_match_key(row.get("player", ""))]
        for row in team_roster
        if player_match_key(row.get("player", "")) in stolen_through_selected_week
        and not is_vampire
    }
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
            elif week == active_week:
                status, status_class, symbol = "Current week", "unknown", "?"
            if week == 1 and week_one_preview and not is_vampire:
                outcome = week_one_preview["outcomes"].get(selected_name, "pending")
                status, status_class, symbol = {
                    "survived": ("Survived", "survived", "✓"),
                    "lost": ("Lost a life", "lost", "✕"),
                    "hit": ("Hydra took a hit; no life lost", "danger", "⚠"),
                    "pending": ("Score pending", "unknown", "?"),
                }[outcome]
            if week in stolen_weeks:
                status, status_class, symbol = "Lost a life and follower stolen", "stolen", "☠"
        if selected_name == "The Gambler" and week <= active_week:
            gambler_outcome = seeded_pick(week, "gambler-flip", [12, -8], world_seed)
            status = f"Gambler {gambler_outcome:+d}"
            status_class = f"{status_class} gambler-positive" if gambler_outcome > 0 else f"{status_class} gambler-negative"
        if selected_name == "The Oracle" and week <= active_week and week in oracle_weeks:
            status = f"Oracle +20 week · {status}"
            status_class = f"{status_class} oracle-bonus"
        timeline_bits.append(f'<span class="hunt-week {status_class}" title="Week {week}: {status}">{symbol}</span>')
    selected_display_name = team_label(selected_name)
    timeline_html = f'''<div class="hunt-timeline"><div class="hunt-timeline-title">Season life timeline · {escape(selected_display_name)}</div>
        <div class="hunt-weeks">{''.join(timeline_bits)}</div>
    </div>'''
    timeline_fragment = timeline_html if not is_vampire else '<div class="timeline-slot"></div>'

    st.markdown(
        f"""<div style="--team-accent:{selected_team['accent']}">
            <div class="team-hero" data-sigil="{selected_team['emoji']}">
                <img src="{selected_team['logo']}" alt="{selected_display_name} logo">
                <div>
                    <div class="dossier-label">Official creature dossier</div>
                    <div class="team-name">{selected_team['emoji']} {escape(selected_display_name)}</div>
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
                <p>{TEAM_LORE.get(selected_name, TEAM_LORE["The Vampire"])}</p>
                </div>
            </div>
            {roster_table}
        </div>""",
        unsafe_allow_html=True,
    )
with scoreboard_tab:
    week_filter_col, live_score_col = st.columns([3, 2], vertical_alignment="bottom")
    with week_filter_col:
        scoreboard_week = st.selectbox(
            "Scoring week",
            list(range(1, 19)),
            index=active_week - 1,
            format_func=lambda week: f"Week {week}",
            key="scoreboard_week",
        )
    with live_score_col:
        if st.button(
            "↻  Check in on the battle",
            key="refresh_fantrax_scores",
            width="stretch",
            type="primary",
        ):
            fantrax_roster_for_week.clear()
            fantrax_standings.clear()
            fantrax_player_directory.clear()
            fantrax_player_scores.clear()
            nfl_week_games.clear()
            st.session_state["fantrax_refresh_notice"] = True
            st.rerun()

    if st.session_state.pop("fantrax_refresh_notice", False):
        st.success("Fantrax rosters and official player FPts refreshed; team scores are calculated here from players.", icon="✅")

    latest_completed_week = active_week - 1
    if latest_completed_week >= 1:
        latest_recorded_tribute = next(
            (
                str(row.get(active_vampire_name, "")).strip()
                for row in vampire_sheet_rows
                if str(row.get("Week", "")) == str(latest_completed_week)
                and str(row.get("Slot", "")).strip().lower() == "stolen"
                and str(row.get(active_vampire_name, "")).strip()
            ),
            "",
        )
        latest_tribute_key = f"tribute:{active_vampire_name}:{latest_completed_week}"
        if latest_recorded_tribute:
            st.success(f"Week {latest_completed_week} tribute selected: {latest_recorded_tribute}", icon="🩸")
        elif st.session_state.get(latest_tribute_key):
            st.success(
                f"Week {latest_completed_week} tribute sent: {st.session_state[latest_tribute_key]}. Waiting for the realm sheet to update.",
                icon="🩸",
            )
        elif scoreboard_week != latest_completed_week:
            def open_latest_tribute() -> None:
                st.session_state["scoreboard_week"] = latest_completed_week

            st.warning(f"Week {latest_completed_week} tribute is still waiting.", icon="🩸")
            st.button(
                f"Choose Week {latest_completed_week} tribute",
                key=f"open_tribute_week_{latest_completed_week}",
                on_click=open_latest_tribute,
            )

    score_rosters, score_roster_source = fantrax_roster_for_week(scoreboard_week)
    score_rosters = enrich_roster_rows(score_rosters)
    score_rosters, score_player_source = add_fantrax_player_scores(score_rosters, scoreboard_week)
    score_rosters = mark_stolen_creature_followers(score_rosters, scoreboard_week)
    scores_revealed = scoreboard_week <= active_week
    try:
        week_games = nfl_week_games(nfl_season, scoreboard_week)
    except Exception:
        week_games = None

    rosters_by_team = {
        team["name"]: [row for row in score_rosters if row.get("team") == team["name"]]
        for team in ALL_TEAMS
    }
    lineups = {name: best_ball_lineup(rows) for name, rows in rosters_by_team.items()}
    # Fantrax team totals are intentionally ignored. Every score is rebuilt
    # from the nine best-ball starters' individual weekly player FPts.
    base_scores = {}
    if scores_revealed:
        for name, lineup in lineups.items():
            if name == active_vampire_name and not rosters_by_team.get(name):
                continue
            scored_players = [row.get("score") for row in lineup if isinstance(row.get("score"), (int, float))]
            base_scores[name] = sum(float(score) for score in scored_players)

    vampire_lineup = lineups[active_vampire_name]
    wizard_target = None
    wizard_replacement = None
    wizard_bonus = 0.0
    if vampire_lineup:
        wizard_target = seeded_pick(scoreboard_week, "wizard-hex", vampire_lineup, world_seed)
        target_slot = wizard_target.get("slot")
        eligible_positions = {"RB", "WR", "TE"} if target_slot == "RWT FLEX" else {wizard_target.get("position")}
        chosen_ids = {row.get("player_id") for row in vampire_lineup}
        replacements = sorted(
            [
                row for row in rosters_by_team[active_vampire_name]
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
    if week_one_preview and scoreboard_week > 1:
        knight_reported_lives = week_one_preview["remaining"]["The Knight"]
    knight_lives = max(1, min(4, int(knight_reported_lives)))
    bonus_by_team["The Knight"] = float((4 - knight_lives) * 5)
    bonus_notes["The Knight"] = f"Last Stand · {knight_lives} lives"

    gambler_bonus = float(seeded_pick(scoreboard_week, "gambler-flip", [12, -8], world_seed)) if scores_revealed else 0.0
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

    game_by_team = {
        team_code(nfl_team): game
        for game in (week_games or [])
        for nfl_team in game["teams"]
    }

    def game_marker_html(nfl_team: str) -> str:
        code = team_code(nfl_team)
        if week_games is None or code in {"", "FA", "—"}:
            return ""
        label, status_class = game_marker(game_by_team.get(code))
        return f'<em class="game-marker {status_class}">{escape(label)}</em>'

    def lineup_html(team: dict, role: str, include_head: bool = True) -> str:
        display_name = active_vampire_label if team["name"] == active_vampire_name else team["name"]
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
            if row.get("stolen"):
                original_name = escape(str(row.get("player") or "Unknown follower"))
                player_markup = f'<strong class="stolen-score-name">Stolen Player</strong><span class="stolen-origin">{original_name} · taken after Week {row["stolen_week"]}</span>'
            else:
                player_markup = f'<strong>{escape(str(row.get("player") or "Awaiting roster"))}</strong>'
            nfl_team = escape(str(row.get("nfl_team") or "—"))
            score = row.get("score")
            score_text = f"{score:.2f}" if isinstance(score, (int, float)) else "—"
            display_slot = "FLX" if slot == "RWT FLEX" else slot
            rendered_rows.append(
                f'''<div class="lineup-row {'stolen-following' if row.get('stolen') else ''}"><div class="lineup-slot">{display_slot}</div>
                <div class="lineup-player">{player_markup}<span class="game-meta">{nfl_team} {'' if row.get('stolen') else game_marker_html(str(row.get('nfl_team') or ''))}</span></div>
                <div class="lineup-points">{score_text}</div></div>'''
            )
        bonus = bonus_by_team.get(team["name"], 0.0)
        bonus_text = f"{bonus:+.2f}" if bonus else "0.00"
        rendered_rows.append(
            f'''<div class="lineup-row bonus"><div class="lineup-slot">BONUS</div>
            <div class="lineup-player"><strong>{escape(bonus_notes.get(team['name'], 'No weekly score bonus'))}</strong></div>
            <div class="lineup-points">{bonus_text}</div></div>'''
        )
        total = adjusted_scores.get(team["name"])
        total_text = f"{total:.2f}" if isinstance(total, (int, float)) else "—"
        head_html = f'''<div class="score-card-head"><img src="{team['logo']}" alt="{display_name} logo">
            <div><span>{role} · Week {scoreboard_week}</span><h3>{team['emoji']} {display_name}</h3></div></div>''' if include_head else ""
        return f'''<div class="score-card {'vampire-side' if team['name'] == active_vampire_name else ''}" data-sigil="{team['emoji']}" style="--score-accent:{team['accent']}">
            {head_html}<div class="lineup-list">{''.join(rendered_rows)}</div>
        </div>'''

    def bench_html(team: dict) -> str:
        starters = {row.get("player_id") for row in lineups.get(team["name"], [])}
        position_order = {position: index for index, (position, _) in enumerate(BASE_ROSTER)}
        bench = sorted(
            [row for row in rosters_by_team.get(team["name"], []) if row.get("stolen") or row.get("player_id") not in starters],
            key=lambda row: (
                position_order.get(row.get("position"), 99),
                -float(row["score"]) if isinstance(row.get("score"), (int, float)) else float("inf"),
                str(row.get("player", "")).casefold(),
            ),
        )
        bench_rows = []
        for row in bench:
            original_name = escape(str(row.get("player") or "Awaiting roster"))
            stolen_origin = f'<small class="stolen-origin">{original_name} · taken after Week {row["stolen_week"]}</small>' if row.get("stolen") else ""
            display_name = "Stolen Player" if row.get("stolen") else original_name
            score_text = f'{row["score"]:.2f}' if isinstance(row.get("score"), (int, float)) else '—'
            bench_rows.append(
                f'''<div class="bench-row {'stolen-following' if row.get('stolen') else ''}"><span>{escape(str(row.get("position") or "—"))}</span>
                <strong class="{'stolen-score-name' if row.get('stolen') else ''}">{display_name}{stolen_origin}<small class="bench-meta">{escape(str(row.get("nfl_team") or "—"))} {'' if row.get('stolen') else game_marker_html(str(row.get('nfl_team') or ''))}</small></strong><b>{score_text}</b></div>'''
            )
        rows = "".join(bench_rows)
        empty = "<div class='score-note'>No bench data available.</div>"
        return f'<div class="bench-list"><div class="bench-title">Bench · {len(bench)} players</div>{rows or empty}</div>'

    ranked_teams = sorted(
        ALL_TEAMS,
        key=lambda team: (
            adjusted_scores.get(team["name"]) if adjusted_scores.get(team["name"]) is not None else float("-inf"),
            0 if team["name"] != active_vampire_name else -1,
        ),
        reverse=True,
    )
    rank_rows = []
    vampire_rank = next((index for index, team in enumerate(ranked_teams, start=1) if team["name"] == active_vampire_name), len(ranked_teams) + 1)
    for rank, team in enumerate(ranked_teams, start=1):
        total = adjusted_scores.get(team["name"])
        total_text = f"{total:.2f}" if isinstance(total, (int, float)) else "—"
        bonus = bonus_by_team.get(team["name"], 0.0)
        detail = f"Bonus {bonus:+.2f}" if bonus else "No bonus"
        pending_html = ""
        if week_games is not None and rosters_by_team.get(team["name"]):
            remaining = followers_left(rosters_by_team[team["name"]], week_games)
            pending_html = (
                '<div class="rank-pending final" title="All follower games final" aria-label="All follower games final">F</div>'
                if remaining == 0 else
                f'<div class="rank-pending" title="{remaining} followers with an NFL game not final" aria-label="{remaining} followers with an NFL game not final">{remaining}</div>'
            )
        if team["name"] == active_vampire_name:
            status_label, status_class = "", "hunter"
        elif week_one_preview and scoreboard_week == 1:
            status_label, status_class = {
                "survived": ("Survived", "safe"),
                "lost": ("Lost a life", "danger"),
                "hit": ("Took a hit", "danger"),
                "pending": ("Status pending", "unknown"),
            }[week_one_preview["outcomes"].get(team["name"], "pending")]
        elif rank < vampire_rank:
            status_label, status_class = "Safe", "safe"
        elif rank > vampire_rank:
            status_label, status_class = ("On pace to take a hit", "danger") if team["name"] == "The Hydra" else ("On pace to lose a life", "danger")
        else:
            status_label, status_class = "Status pending", "unknown"
        status_html = f'<span class="rank-status {status_class}">{status_label}</span>' if status_label else ""
        rank_rows.append(
            f'''<div class="rank-tile {'vampire-rank' if team['name'] == active_vampire_name else ''}" style="--rank-accent:{team['accent']}">
                <div class="rank-number">{rank}</div>
                <div class="rank-team"><strong>{team['emoji']} {escape(team_label(team['name']))}</strong>{status_html}<span>{detail}</span></div>
                {pending_html}
                <div class="rank-score">{total_text}</div>
            </div>'''
        )
    league_board = f'''<div class="league-board"><div class="league-board-title">Week {scoreboard_week} Scoreboard</div>
        <div class="rank-tiles">{''.join(rank_rows)}</div>
    </div>'''

    board_cols = st.columns([1.8, 1.8, 1.4], gap="medium")
    with board_cols[0]:
        with st.container(border=True):
            st.markdown(f'<div class="opponent-picker-title">Week {scoreboard_week}</div>', unsafe_allow_html=True)
            picker_cols = st.columns([.38, .62], gap="small")
            with picker_cols[0]:
                st.image(VAMPIRE_TEAM["logo"], width=96)
            with picker_cols[1]:
                st.markdown(f'<div style="padding-top:1.1rem;color:#f5e9e2;font:600 1.35rem Cormorant Garamond,serif;">{VAMPIRE_TEAM["emoji"]} {active_vampire_label}</div>', unsafe_allow_html=True)
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
                    format_func=lambda name: f"{next(team['emoji'] for team in CREATURES if team['name'] == name)}  {team_label(name)}",
                    key="scoreboard_opponent",
                    label_visibility="collapsed",
                )
        opponent_team = next(team for team in CREATURES if team["name"] == opponent_name)
        st.markdown(lineup_html(opponent_team, "THE HUNTED", include_head=False), unsafe_allow_html=True)
        st.markdown(bench_html(opponent_team), unsafe_allow_html=True)
    with board_cols[2]:
        st.markdown(league_board, unsafe_allow_html=True)

    # Keep the entire tribute interface hidden until the full NFL week is final.
    # Missing/incomplete NFL data must never unlock a claim.
    tribute_ready = games_are_final(week_games or [])
    if tribute_ready:
        st.divider()
        st.subheader("Claim your tribute")
    recorded_tribute = next(
        (
            str(row.get(active_vampire_name, "")).strip()
            for row in vampire_sheet_rows
            if str(row.get("Week", "")) == str(scoreboard_week)
            and str(row.get("Slot", "")).strip().lower() == "stolen"
            and str(row.get(active_vampire_name, "")).strip()
        ),
        "",
    )
    tribute_key = f"tribute:{active_vampire_name}:{scoreboard_week}"
    claim_lock = None
    if not tribute_ready:
        claim_lock = "pending"
    elif recorded_tribute:
        st.success(f"Week {scoreboard_week} tribute recorded: {recorded_tribute}")
        claim_lock = "recorded"
    elif st.session_state.get(tribute_key):
        st.success(f"Tribute sent: {st.session_state[tribute_key]}. It will appear here after the realm sheet is updated.")
        claim_lock = "sent"
    elif scoreboard_week > active_week:
        claim_lock = "This week has not begun."
    elif len(rosters_by_team.get(active_vampire_name, [])) != 20:
        claim_lock = "A complete 20-follower Vampire lineup is needed before claiming tribute."
    elif score_player_source != "live" or len(lineups.get(active_vampire_name, [])) != 9:
        claim_lock = "Fantrax follower scores are unavailable. The claim stays locked until scores can be verified."

    if claim_lock and claim_lock not in {"recorded", "sent", "pending"}:
        st.info(claim_lock)
    elif not claim_lock:
        vampire_total = adjusted_scores.get(active_vampire_name)
        try:
            hydra_claimable = hydra_life_due_this_week(scoreboard_week, active_vampire_name)
        except Exception:
            hydra_claimable = False
        eligible_creatures = [
            creature for creature in CREATURES
            if isinstance(vampire_total, (int, float))
            and isinstance(adjusted_scores.get(creature["name"]), (int, float))
            and vampire_total > adjusted_scores[creature["name"]]
            and len(lineups.get(creature["name"], [])) == 9
            and rosters_by_team.get(creature["name"])
            and (creature["name"] != "The Hydra" or hydra_claimable)
        ]
        if not eligible_creatures:
            st.info("No creature lost a life to this Vampire this week, so there is no tribute to claim.")
        else:
            st.caption("Choose from creatures that lost a life this week. A first hit on Hydra does not unlock its followers; the Guardian's top two scorers are protected.")
            claim_options = {}
            for creature in eligible_creatures:
                creature_name = creature["name"]
                following = rosters_by_team[creature_name]
                protected_indices = set()
                if creature_name == "The Guardian":
                    protected_indices = {
                        index for index, _ in sorted(
                            ((index, row) for index, row in enumerate(following) if not row.get("stolen")),
                            key=lambda indexed: _scored_first(indexed[1]),
                            reverse=True,
                        )[:2]
                    }
                for index, row in enumerate(following):
                    if row.get("stolen") or index in protected_indices or not row.get("player"):
                        continue
                    option_key = (creature_name, str(row.get("player_id") or row["player"]))
                    claim_options[option_key] = row
            choices = sorted(
                claim_options,
                key=lambda option: _scored_first(claim_options[option]),
                reverse=True,
            )

            def claim_option_label(option: tuple[str, str]) -> str:
                creature_name, _ = option
                row = claim_options[option]
                score = row.get("score")
                score_label = f"{score:.2f} FPts" if isinstance(score, (int, float)) else "— FPts"
                return f'{score_label} · {row["player"]} ({row.get("position", "—")} · {row.get("nfl_team", "—")}) · {team_label(creature_name)}'

            with st.form(f"tribute_form:{active_vampire_name}:{scoreboard_week}"):
                chosen_follower = st.selectbox(
                    "Follower to steal",
                    choices,
                    format_func=claim_option_label,
                ) if choices else None
                claim_submitted = st.form_submit_button("Steal this follower", type="primary", disabled=not choices)
            if claim_submitted and chosen_follower is not None:
                try:
                    creature_name = chosen_follower[0]
                    follower_name = str(claim_options[chosen_follower]["player"])
                    send_tribute_to_discord(active_vampire_name, scoreboard_week, creature_name, follower_name)
                    st.session_state[tribute_key] = follower_name
                    st.rerun()
                except Exception:
                    st.error("Could not send this tribute to Discord. Please try again; nothing was recorded.")

with realm_summary_tab:
    realm_week = st.selectbox("Summary week", list(range(1, 19)), index=active_week - 1, format_func=lambda week: f"Week {week}", key="realm_summary_week")
    st.markdown(f"<div class='realm-intro'><h2>Cross-Realm Summary · Week {realm_week}</h2><p>Each Vampire faces all eleven creatures every week. Scores update live; lives and results settle only after every NFL game is final.</p></div>", unsafe_allow_html=True)
    realm_states = {
        name: {
            "remaining": {creature["name"]: creature["lives"] for creature in CREATURES},
            "hydra_hit": False,
            "hunter_bonus": 0.0,
            "weeks": {},
        }
        for name in vampire_sheet_teams
    }
    selected_world_rosters = None
    week_final_by_week = {}
    prior_weeks_verified = True
    for battle_week in range(1, min(realm_week, active_week) + 1):
        if battle_week == scoreboard_week:
            weekly_games = week_games
        else:
            try:
                weekly_games = nfl_week_games(nfl_season, battle_week)
            except Exception:
                weekly_games = None
        week_is_final = games_are_final(weekly_games or []) and prior_weeks_verified
        week_final_by_week[battle_week] = week_is_final
        weekly_world_rosters = vampire_world_rosters(battle_week)
        if battle_week == realm_week:
            selected_world_rosters = weekly_world_rosters
        weekly_creatures, _ = fantrax_roster_for_week(battle_week)
        weekly_creatures = enrich_roster_rows(weekly_creatures)
        weekly_creatures, _ = add_fantrax_player_scores(weekly_creatures, battle_week)
        for world_name, state in realm_states.items():
            world_roster = weekly_world_rosters.get(world_name, [])
            world_roster, _ = add_fantrax_player_scores(world_roster, battle_week)
            creature_roster = mark_stolen_creature_followers(weekly_creatures, battle_week, world_name)
            battle = calculate_realm_battle(
                battle_week, world_name, world_roster, creature_roster,
                state["remaining"], state["hydra_hit"], state["hunter_bonus"],
            )
            if battle is not None:
                if week_is_final:
                    state["remaining"] = battle["remaining"]
                    state["hydra_hit"] = battle["hydra_hit"]
                    state["hunter_bonus"] = battle["hunter_bonus"]
                state["weeks"][battle_week] = battle
            elif week_is_final:
                state["hydra_hit"] = False
        prior_weeks_verified = week_is_final
    if selected_world_rosters is None:
        selected_world_rosters = vampire_world_rosters(realm_week)
    selected_week_final = week_final_by_week.get(realm_week, False)
    header_cells = "".join(f"<th><img src='{creature['logo']}' alt='' /><span>{escape(team_label(creature['name']))}</span></th>" for creature in CREATURES)
    body_rows = []
    for world_name in vampire_sheet_teams:
        state = realm_states[world_name]
        battle = state["weeks"].get(realm_week)
        score = battle["scores"].get(world_name) if battle else None
        stolen = next((str(row.get(world_name, "")).strip() for row in vampire_sheet_rows if str(row.get("Week", "")) == str(realm_week) and str(row.get("Slot", "")).strip().lower() == "stolen"), "") if selected_week_final else ""
        stolen = stolen or "—"
        cells = ""
        for creature in CREATURES:
            starting = creature["lives"]
            remaining = state["remaining"][creature["name"]]
            outcome = battle["outcomes"].get(creature["name"], "pending") if battle and selected_week_final else "pending"
            result_text, result_class = {
                "lost": ("BEAT", "beat"),
                "hit": ("HIT", "hit"),
                "survived": ("SAFE", "safe"),
                "pending": ("—", "pending"),
            }[outcome]
            if battle and not selected_week_final:
                result_text, result_class = "LIVE", "live"
            cells += f"<td class='life-diamonds' title='Week {realm_week}: {result_text.lower()} · {remaining} of {starting} lives remaining'>{life_diamonds(starting, remaining)}<small class='{result_class}'>{result_text}</small></td>"
        roster_count = len(selected_world_rosters.get(world_name, []))
        score_text = f"{score:.2f}" if isinstance(score, (int, float)) else ("No lineup" if roster_count == 0 else "Lineup incomplete" if roster_count < 20 else "Scheduled")
        if score == 0:
            score_text += "<small>No FPts yet</small>"
        elif isinstance(score, (int, float)) and not selected_week_final:
            score_text += "<small>Live score</small>"
        body_rows.append(f"<tr class='{'active' if world_name == active_vampire_name else ''}'><th>🧛 {escape(team_label(world_name))}<small>{'You' if world_name == active_vampire_name else 'Universe'}</small></th><td class='realm-score'>{score_text}</td>{cells}<td class='stolen'>{escape(stolen)}</td></tr>")
    st.markdown(f"<div class='realm-cross-wrap'><table class='realm-cross'><thead><tr><th>Vampire</th><th>Week {realm_week}</th>{header_cells}<th>Player stolen</th></tr></thead><tbody>{''.join(body_rows)}</tbody></table></div>", unsafe_allow_html=True)

with available_tab:
    available_snapshot = load_snapshot()
    available_week = active_week
    st.markdown(
        f'''<div class="available-intro">
            <div><h2>Choose Your Followers</h2>
            <p>Choose your followers: a complete 20-follower roster from the highest-ranked followers who are not owned by any of the eleven creatures. Current Vampire followers remain available to owners entering a new version of the hunt.</p></div>
            <div class="available-week">Week {available_week} · Recommendations</div>
        </div>''',
        unsafe_allow_html=True,
    )

    available_rosters, _ = fantrax_roster_for_week(available_week)
    available_rosters = mark_stolen_creature_followers(available_rosters, available_week)
    opponent_rows = [row for row in available_rosters if row.get("team") != active_vampire_name]
    creature_roster_members = {creature["name"]: set() for creature in CREATURES}
    for row in opponent_rows:
        team_name = row.get("team")
        if team_name in creature_roster_members:
            follower_id = str(row.get("player_id") or player_match_key(row.get("player", "")))
            if follower_id:
                creature_roster_members[team_name].add(follower_id)
    changed_rosters = [
        f"{team_label(name)} ({len(members)} followers)"
        for name, members in creature_roster_members.items()
        if members and len(members) != 20
    ]
    if changed_rosters:
        st.warning(
            "Creature roster alert: " + ", ".join(changed_rosters)
            + ". Each creature should have 20 followers; check these rosters before choosing your lineup.",
            icon="⚠️",
        )
    missing_rosters = [team_label(name) for name, members in creature_roster_members.items() if not members]
    if missing_rosters:
        st.warning(
            "Could not verify the roster for " + ", ".join(missing_rosters)
            + ". Recommendations may include followers who are already taken.",
            icon="⚠️",
        )
    still_owned_opponents = [row for row in opponent_rows if not row.get("stolen")]
    opponent_ids = {str(row.get("player_id", "")) for row in still_owned_opponents}
    opponent_names = {player_match_key(row.get("player", "")) for row in still_owned_opponents}
    opponent_dst_teams = {
        nfl_team_match_key(row.get("nfl_team", ""))
        for row in still_owned_opponents if row.get("position") == "DST"
    }
    try:
        player_pool = fantasypros_weekly_rankings(available_week)
    except Exception:
        player_pool = []

    player_pool = [
        row for row in player_pool
        if str(row.get("player_id", "")) not in opponent_ids
        and player_match_key(row.get("player", "")) not in opponent_names
        and not (row.get("position") == "DST" and nfl_team_match_key(row.get("nfl_team", "")) in opponent_dst_teams)
    ]
    player_pool = complete_defense_recommendations(player_pool, opponent_dst_teams)
    pool_settings = {
        "QB": (8, 2, "#b94a5e"),
        "TE": (8, 2, "#349b8d"),
        "RB": (20, 6, "#d2783d"),
        "WR": (20, 6, "#8b70d1"),
        "K": (10, 2, "#c89b43"),
        "DST": (10, 2, "#4d88b7"),
    }

    if not player_pool:
        st.info("Recommendations are temporarily unavailable. Refresh the page in a moment.")
    else:
        position_options = {}
        position_lookup = {}
        for position, (player_count, _, _) in pool_settings.items():
            rows = sorted(
                [row for row in player_pool if row.get("position") == position],
                key=lambda row: int(row.get("rank", 9999)),
            )[:player_count]
            position_options[position] = [
                f'''{row.get("player", "—")} — {row.get("nfl_team", "FA")}''' for row in rows
            ]
            position_lookup[position] = dict(zip(position_options[position], rows))

        selected_by_position = {}
        other_by_position = {}
        with st.form("new_vampire_lineup"):
            existing_owner = st.selectbox(
                "Existing owner",
                vampire_sheet_teams,
                index=vampire_sheet_teams.index(active_vampire_name) if active_vampire_name in vampire_sheet_teams else 0,
                key="submission_vampire_team_name",
            )
            new_owner_name = st.text_input(
                "New owner name (if you aren't listed above)",
                max_chars=40,
                placeholder="Enter your name to join the hunt",
                help="A name entered here will be used for this lineup instead of the existing-owner selection.",
            )
            for left_position, right_position in (("QB", "TE"), ("RB", "WR"), ("K", "DST")):
                pair_columns = st.columns(2)
                for column, position in zip(pair_columns, (left_position, right_position)):
                    player_count, select_count, accent = pool_settings[position]
                    rows = [position_lookup[position][option] for option in position_options[position]]
                    table_rows = "".join(
                        f'''<div class="pool-row">
                            <div class="pool-rank">{rank:02d}</div>
                            <div class="pool-player">{escape(str(row.get("player") or "—"))}</div>
                            <div class="pool-team">{escape(str(row.get("nfl_team") or "FA"))}</div>
                        </div>'''
                        for rank, row in enumerate(rows, 1)
                    )
                    with column:
                        st.markdown(
                            f'''<div class="pool-section" style="--pool-accent:{accent}">
            <div class="pool-heading"><strong>{position}</strong><span>Select {select_count} followers · Top {player_count}</span></div>
                            <div class="pool-row header"><div>#</div><div>Follower</div><div>NFL</div></div>
                                {table_rows}
                            </div>''',
                            unsafe_allow_html=True,
                        )
                        selected_by_position[position] = st.multiselect(
                            f"Select {select_count} {position}",
                            position_options[position],
                            max_selections=select_count,
                            key=f"available_{position.lower()}_selections",
                            placeholder=f"Choose up to {select_count}",
                        )
                        other_by_position[position] = st.text_input(
                            f"Other {position}",
                            key=f"available_{position.lower()}_other",
                            placeholder="Type another follower; separate multiple names with commas",
                        )
            submitted = st.form_submit_button("Submit Lineup", type="primary", width="stretch")

        if submitted:
            team_name = new_owner_name.strip() or existing_owner
            lineup = {}
            errors = []
            for position, (_, required, _) in pool_settings.items():
                selected_players = [
                    {
                        "player": position_lookup[position][option].get("player"),
                        "nfl_team": position_lookup[position][option].get("nfl_team"),
                    }
                    for option in selected_by_position[position]
                ]
                other_players = [
                    {"player": name.strip(), "nfl_team": "Other"}
                    for name in other_by_position[position].split(",")
                    if name.strip()
                ]
                lineup[position] = [*selected_players, *other_players]
                if len(lineup[position]) != required:
                    errors.append(f"{position}: select {required} total")
            if errors:
                st.error("Lineup incomplete — " + " · ".join(errors))
            else:
                submission = {
                    "team_name": team_name.strip(),
                    "week": available_week,
                    "lineup": lineup,
                }
                st.session_state["submitted_vampire_lineup"] = submission
                try:
                    send_lineup_to_discord(submission)
                except Exception as exc:
                    st.error(f"The lineup is complete, but Discord could not receive it: {exc}")
                else:
                    st.success(f"{team_name.strip()} is ready for the hunt. The 20-follower roster was sent to Discord.")

        saved_submission = st.session_state.get("submitted_vampire_lineup")
        if saved_submission and saved_submission.get("week") == available_week:
            st.markdown(
                f'''<div class="roster-header"><div><div class="section-kicker">Submitted roster</div>
                <h3>{escape(str(saved_submission.get("team_name") or "Your Vampire"))}</h3></div>
                <div class="data-status live">Week {available_week} · 20 followers</div></div>''',
                unsafe_allow_html=True,
            )
            submitted_rows = []
            for position in ("QB", "RB", "WR", "TE", "K", "DST"):
                for player in saved_submission.get("lineup", {}).get(position, []):
                    submitted_rows.append(
                        {
                            "Position": position,
                            "Player": player.get("player", "—"),
                            "NFL": player.get("nfl_team", "Other"),
                        }
                    )
            st.dataframe(submitted_rows, hide_index=True, width="stretch")

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
        - After a successful hunt, The Vampire may steal one follower from that opponent's roster.
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

        Best ball takes the highest-scoring eligible followers at each position first, then fills the flex with the best remaining eligible follower.
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
