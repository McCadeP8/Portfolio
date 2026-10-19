"""Fill missing cap sheet player pictures with verified ESPN headshots.

The Google Sheet picture tab stays the source of truth. Players it has no link
for are resolved here and saved to ``player_pictures_auto.csv``, which
``functions.get_pictures`` uses only to fill gaps.
"""
from __future__ import annotations

from pathlib import Path
import re
import time
import unicodedata

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTO_PICTURES_FILE = "player_pictures_auto.csv"
HEADSHOT_URL = "https://a.espncdn.com/i/headshots/nba/players/full/{}.png"
SEARCH_URL = "https://site.web.api.espn.com/apis/common/v3/search"
COLUMNS = ["Player", "Picture_Online", "espn_player_id", "Source"]
PENDING = "pending"
# Shown for pending players so every cap sheet player renders a picture.
PLACEHOLDER_PICTURE = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 96 96'%3E"
    "%3Crect width='96' height='96' rx='48' fill='%23111827'/%3E%3Ccircle cx='48' cy='35' r='17' fill='%23f8fafc'/%3E"
    "%3Cpath d='M18 83c4-20 17-31 30-31s26 11 30 31' fill='%23f8fafc'/%3E%3C/svg%3E"
)


def player_key(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    text = re.sub(r"\b(Jr|Sr|II|III|IV|V)\b\.?", "", text, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _known_espn_ids(root: Path) -> dict[str, str]:
    """Names to ESPN ids from the hand-matched overrides file."""
    path = root / "player_id_overrides.csv"
    if not path.exists():
        return {}
    table = pd.read_csv(path, dtype=str).dropna(subset=["espn_player_id"])
    ids: dict[str, str] = {}
    for column in ("fantrax_name", "espn_name"):
        for name, espn_id in zip(table.get(column, []), table["espn_player_id"]):
            if isinstance(name, str):
                ids.setdefault(player_key(name), espn_id)
    return ids


def _search_espn_id(session: requests.Session, name: str) -> str | None:
    response = session.get(SEARCH_URL, params={"query": name, "type": "player", "limit": 10}, timeout=15)
    response.raise_for_status()
    hits = [item for item in response.json().get("items", [])
            if item.get("league") == "nba" and player_key(item.get("displayName")) == player_key(name)]
    # Two NBA players with one normalized name is a coin flip; leave it unresolved.
    return str(hits[0]["id"]) if len(hits) == 1 else None


def _headshot_exists(session: requests.Session, espn_id: str) -> bool:
    return session.head(HEADSHOT_URL.format(espn_id), timeout=15).status_code == 200


def _read_table(root: Path) -> pd.DataFrame:
    path = root / AUTO_PICTURES_FILE
    return pd.read_csv(path, dtype=str) if path.exists() else pd.DataFrame(columns=COLUMNS)


def read_auto_pictures(root: Path = PROJECT_ROOT, include_placeholders: bool = False) -> pd.DataFrame:
    """Resolved pictures, plus a silhouette for pending players when asked."""
    table = _read_table(root)
    if include_placeholders:
        table = table.copy()
        table.loc[table["Source"] == PENDING, "Picture_Online"] = PLACEHOLDER_PICTURE
        return table.reset_index(drop=True)
    return table[table["Source"] != PENDING].reset_index(drop=True)


def pending_picture_players(root: Path = PROJECT_ROOT) -> set[str]:
    """Players with no NBA headshot anywhere yet; retried every night."""
    table = _read_table(root)
    return set(table.loc[table["Source"] == PENDING, "Player"])


def resolve_missing_pictures(players: list[str], root: Path = PROJECT_ROOT, pause: float = 0.25) -> dict[str, list[str]]:
    """Resolve players without pictures and merge the hits into the auto file."""
    known = _known_espn_ids(root)
    existing = read_auto_pictures(root)
    done = set(existing["Player"].map(player_key))  # pending players are retried
    session = requests.Session()
    added, unresolved = [], []
    for name in dict.fromkeys(p for p in players if isinstance(p, str) and p.strip()):
        if player_key(name) in done:
            continue
        espn_id, source = known.get(player_key(name)), "player_id_overrides"
        if espn_id is None:
            espn_id, source = _search_espn_id(session, name), "espn_search"
            time.sleep(pause)
        if espn_id and _headshot_exists(session, espn_id):
            added.append({"Player": name, "Picture_Online": HEADSHOT_URL.format(espn_id), "espn_player_id": espn_id, "Source": source})
        else:
            unresolved.append(name)
    pending = [{"Player": name, "Picture_Online": "", "espn_player_id": "", "Source": PENDING} for name in unresolved]
    table = pd.concat([existing, pd.DataFrame(added), pd.DataFrame(pending)], ignore_index=True).reindex(columns=COLUMNS)
    tmp = root / (AUTO_PICTURES_FILE + ".tmp")
    table.to_csv(tmp, index=False)
    tmp.replace(root / AUTO_PICTURES_FILE)
    return {"added": [row["Player"] for row in added], "unresolved": unresolved}


def fill_missing_from_cap_sheet(root: Path = PROJECT_ROOT) -> dict[str, list[str]]:
    import functions

    cap = functions.get_data()
    pics = functions.get_pictures()
    # Includes silhouette players, so pending ones are retried every night.
    missing = functions.data_picture_check(cap, pics)["Player"].tolist()
    return resolve_missing_pictures(missing, root)


if __name__ == "__main__":
    result = fill_missing_from_cap_sheet()
    print(f"Added {len(result['added'])}: {', '.join(result['added'])}")
    print(f"Unresolved {len(result['unresolved'])}: {', '.join(result['unresolved'])}")
