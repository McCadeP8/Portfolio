#import os
#os.chdir("SBC_Streamlit")

import pandas as pd
import streamlit as st
import math as math
import numpy as np
import folium as folium
import streamlit.components.v1 as components
import base64
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from itertools import combinations
from urllib.parse import urlparse
import requests
import json
import altair as alt
import unicodedata
import re
from matplotlib import font_manager
from PIL import Image, ImageColor, ImageDraw, ImageFont
from data import current_salary_cap, current_luxury_tax, current_apron_1, current_apron_2, tax_bracket_increment, league_ratio, columns_order, current_year, year_offset, team_info, cap_sheets_to_fantrax_name_fix, minimum_sal, max_minimum, league_ids, team_id_history, stat_to_scipId, today
from sbc_backend import BackendSettings, get_repository
from sbc_backend.network import CachedHttpClient

APP_DIR = Path(__file__).resolve().parent
BACKEND_SETTINGS = BackendSettings.from_env(APP_DIR)
DATA_REPOSITORY = get_repository(APP_DIR)
SNAPSHOT_DIR = BACKEND_SETTINGS.snapshot_root
SNAPSHOT_HTTP = CachedHttpClient(timeout_seconds=BACKEND_SETTINGS.http_timeout_seconds)


def read_csv_snapshot(name: str, url: str, ttl_seconds: int = 86400, **kwargs) -> pd.DataFrame:
    return SNAPSHOT_HTTP.get_csv_snapshot(
        url,
        cache_path=SNAPSHOT_DIR / f"{name}.parquet",
        ttl_seconds=ttl_seconds,
        row_group_size=BACKEND_SETTINGS.parquet_row_group_size,
        **kwargs,
    )


def safe_team_info(team, field, default=""):
    return team_info.get(str(team), {}).get(field, default)

def normalize_player_key(value):
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = " ".join(text.lower().replace(".", "").replace("'", "").split())
    replacements = {
        "alperun sengun": "alperen sengun",
        "alex sarr": "alexandre sarr",
    }
    text = replacements.get(text, text)
    suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
    parts = [part for part in text.split() if part not in suffixes]
    return " ".join(parts)

@st.cache_data(ttl=60)
def get_data() -> pd.DataFrame:
    refresh_key = int(pd.Timestamp.now().timestamp() // 60)
    csv_url = f"https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1906653859&refresh={refresh_key}"
    df = read_csv_snapshot("cap_sheet_data", csv_url, ttl_seconds=0)
    for year in columns_order:
        salary_col = "Y" + str(year)
        type_col = "Type" + str(year)
        if salary_col not in df.columns:
            df[salary_col] = pd.NA
        if type_col not in df.columns:
            df[type_col] = ""
    return df

@st.cache_data()
def get_pictures() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1180190150"
    df = read_csv_snapshot("player_pictures", csv_url)
    df = df.drop(columns=["Picture"], errors="ignore")
    return df


PAID_SALARY_TYPES = {"Dead", "Guaranteed", "Non-Guaranteed"}


@st.cache_data(ttl=60, show_spinner=False)
def get_player_salary_history() -> pd.DataFrame:
    """Return one paid-salary row per player and SBCFBL season through the current year."""
    columns = ["Year", "Player", "Player Key", "Amount"]
    frames = []
    historical_path = APP_DIR / "historical_player_salaries.csv"
    if historical_path.exists():
        historical = pd.read_csv(historical_path)
        if {"Year", "Player", "Amount"}.issubset(historical.columns):
            historical = historical.copy()
            historical["Player Key"] = historical["Player"].map(normalize_player_key)
            historical["Amount"] = pd.to_numeric(historical["Amount"], errors="coerce")
            frames.append(historical[columns])

    cap = get_data().copy()
    if not cap.empty and "Player" in cap.columns:
        for salary_year in range(2023, int(current_year) + 1):
            salary_col = f"Y{salary_year}"
            type_col = f"Type{salary_year}"
            if salary_col not in cap.columns or type_col not in cap.columns:
                continue
            paid = cap[cap[type_col].isin(PAID_SALARY_TYPES)].copy()
            if paid.empty:
                continue
            paid["Player"] = paid["Player"].replace(cap_sheets_to_fantrax_name_fix).astype(str).str.strip()
            paid["Player Key"] = paid["Player"].map(normalize_player_key)
            paid["Amount"] = pd.to_numeric(paid[salary_col], errors="coerce")
            paid["Year"] = salary_year
            frames.append(paid[columns])

    if not frames:
        return pd.DataFrame(columns=columns)
    combined = pd.concat(frames, ignore_index=True).dropna(subset=["Player Key", "Amount"])
    combined = combined[combined["Player Key"].astype(str).str.strip().ne("")]
    return (
        combined.groupby(["Year", "Player Key"], as_index=False)
        .agg(Player=("Player", "first"), Amount=("Amount", "sum"))
        [["Year", "Player", "Player Key", "Amount"]]
        .sort_values(["Player Key", "Year"])
        .reset_index(drop=True)
    )

@st.cache_data(ttl=300)
def get_articles() -> pd.DataFrame:
    refresh_key = int(pd.Timestamp.now().timestamp() // 300)
    csv_url = (
        "https://docs.google.com/spreadsheets/d/"
        "11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/"
        f"export?format=csv&gid=1547958995&refresh={refresh_key}"
    )
    df = read_csv_snapshot(
        "articles",
        csv_url,
        ttl_seconds=300,
        dtype=str,
        keep_default_na=False,
    )
    for column in ["Date", "Author", "Headline", "Body"]:
        if column not in df.columns:
            df[column] = ""
    df = df[["Date", "Author", "Headline", "Body"]].copy()
    return df[df["Headline"].astype(str).str.strip().ne("")].reset_index(drop=True)

@st.cache_data(ttl=60)
def get_exceptions() -> pd.DataFrame:
    refresh_key = int(pd.Timestamp.now().timestamp() // 60)
    csv_url = f"https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1620818587&refresh={refresh_key}"
    df = read_csv_snapshot("exceptions", csv_url, ttl_seconds=0)
    current_salary_col = "Y" + str(current_year)
    for col in ["Team", "Player", current_salary_col, "BirdRights"]:
        if col not in df.columns:
            df[col] = 0 if col == current_salary_col else ""
    return df[["Team", "Player", current_salary_col, "BirdRights"]]

@st.cache_data(ttl=60)
def get_base_cap() -> pd.DataFrame:
    refresh_key = int(pd.Timestamp.now().timestamp() // 60)
    csv_url = f"https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=760630769&refresh={refresh_key}"
    df = read_csv_snapshot("base_cap", csv_url, ttl_seconds=0)
    return df

@st.cache_data(ttl=60)
def get_draft_picks() -> pd.DataFrame:
    refresh_key = int(pd.Timestamp.now().timestamp() // 60)
    csv_url = f"https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1612129799&refresh={refresh_key}"
    df = read_csv_snapshot("draft_picks", csv_url, ttl_seconds=0)
    df = df[df['Year'].between(current_year, current_year + 6)]
    return df

@st.cache_data(ttl=60)
def get_period_calendar() -> pd.DataFrame:
    refresh_key = int(pd.Timestamp.now().timestamp() // 60)
    csv_url = f"https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=698621872&refresh={refresh_key}"
    df = read_csv_snapshot("period_calendar", csv_url, ttl_seconds=0)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in ["Day", "Year", "Period"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

@st.cache_data(ttl=86400)
def get_all_time_team_stats() -> pd.DataFrame:
    return DATA_REPOSITORY.read("team_stats", required=True)

@st.cache_data(ttl=86400)
def get_all_time_rosters() -> pd.DataFrame:
    return DATA_REPOSITORY.read("rosters", required=True)

@st.cache_data(ttl=86400)
def get_fantrax_roster(year, period) -> pd.DataFrame:
    league_id = league_ids.get(year)
    if not league_id:
        return pd.DataFrame()
    all_rosters_list = []    
    roster_url = f"https://www.fantrax.com/fxea/general/getTeamRosters?leagueId={league_id}&period={period}"
    headers = {'Cookie': 'JSESSIONID='}
    response = requests.get(roster_url, headers=headers)
    if response.status_code == 200:
        roster_json = response.text
        roster_data = json.loads(roster_json)
        rosters = roster_data.get('rosters', {})
        for team_id, roster in rosters.items():
            team_name = roster.get('teamName')
            roster_items = roster.get('rosterItems')
            if roster_items is not None and len(roster_items) > 0:
                roster_df = pd.DataFrame(roster_items)
                roster_df['team_name'] = team_name
                roster_df['period'] = period
                roster_df['team_id'] = team_id
                all_rosters_list.append(roster_df)    
    if all_rosters_list:
        all_rosters_data = pd.concat(all_rosters_list, ignore_index=True)
    else:
        all_rosters_data = pd.DataFrame()
    return all_rosters_data

@st.cache_data()
def get_fantrax_players() -> pd.DataFrame:
    roster_url = "https://www.fantrax.com/fxea/general/getPlayerIds?sport=NBA"
    headers = {'Cookie': 'JSESSIONID='}
    response = requests.get(roster_url, headers=headers)
    players_df = pd.DataFrame(columns=["name", "fantraxId"])
    if response.status_code == 200:
        data = json.loads(response.text)
        players_list = []
        for player_id, player_info in data.items():
            player_record = player_info.copy()
            players_list.append(player_record)
        players_df = pd.DataFrame(players_list)
        players_df = players_df[['name', 'fantraxId']]
        new_row = pd.DataFrame([{"name": "Bogdanovic, Bojan", "fantraxId": "027pg"}])
        players_df = pd.concat([players_df, new_row], ignore_index=True)
        players_df['name'] = players_df['name'].str.split(', ').str[1] + ' ' + players_df['name'].str.split(', ').str[0]
        players_df.loc[players_df['name'] == 'Amari Bailey', 'fantraxId'] = '06cbt'
        players_df.loc[players_df['name'] == 'Tarik Biberovic', 'fantraxId'] = '06cdi'
        players_df = players_df[players_df['fantraxId'] != "067x0"]
        players_df = players_df[players_df['fantraxId'] != "06ps6"]
    else:
        print(f"Failed to fetch data - Status code: {response.status_code}")
    return players_df


FANTRAX_TRANSACTION_COLUMNS = [
    "Year", "View", "Transaction ID", "Type", "Player ID", "Player", "Positions",
    "NBA Team", "Headshot", "Asset Type", "Asset Team", "Team", "From", "To", "Date",
    "Date Sort", "Period", "Result", "Notes",
]


DRAFT_PICK_TRANSACTION_CUTOFF = pd.Timestamp("2023-06-01")
DRAFT_PICK_TEAM_ALIASES = {
    "austing": "Austin",
    "baltimiore": "Baltimore",
    "des moine": "Des Moines",
    "el pasp": "El Paso",
    "el pasol": "El Paso",
    "jakcsonville": "Jacksonville",
    "mancheseter": "Manchester",
    "san deigo": "San Diego",
    "tampa": "Tampa Bay",
}


def _draft_pick_team_key(value) -> str:
    """Translate sheet cities, historical full names, and known typos to a team_info key."""
    text = " ".join(str(value or "").strip().split())
    text = re.split(r"\s*[:;]\s*", text, maxsplit=1)[0].strip()
    lowered = text.lower()
    for trailing in [" unprotected", " as well"]:
        if lowered.endswith(trailing):
            text = text[:-len(trailing)].strip()
            lowered = text.lower()
    alias = DRAFT_PICK_TEAM_ALIASES.get(lowered)
    if alias:
        return alias
    if lowered == "san diego wave" or lowered == "san diego seals":
        return "San Diego"
    for city, info in team_info.items():
        nickname = str(info.get("nickname", "")).strip()
        full_name = f"{city} {nickname}".strip()
        if lowered in {city.lower(), nickname.lower(), full_name.lower()}:
            return city
        if lowered.startswith(f"{city.lower()} "):
            return city
    return text


def _draft_pick_team_name(value, season_year: int) -> str:
    city = _draft_pick_team_key(value)
    if city not in team_info:
        return str(value or "").strip()
    if city == "San Diego" and int(season_year) <= 2025:
        return "San Diego Wave"
    return f"{city} {team_info[city].get('nickname', '')}".strip()


def _draft_pick_note_target(note: str) -> str:
    direct_match = re.search(r"^(?:to|conveyed to)\s+([^;,]+)", note, flags=re.IGNORECASE)
    if direct_match:
        return _draft_pick_team_key(direct_match.group(1))
    swap_match = re.search(r"\bPick Swap\s+(?:with|to)\s+([^;,]+)", note, flags=re.IGNORECASE)
    if swap_match:
        swap_team = re.sub(r"'s\s+Pick\b", "", swap_match.group(1), flags=re.IGNORECASE)
        if "/" in swap_team:
            return ""
        return _draft_pick_team_key(swap_team)
    beneficiary_match = re.search(r"\b([A-Za-z .]+?)\s+gets first choice\b", note, flags=re.IGNORECASE)
    if beneficiary_match:
        return _draft_pick_team_key(beneficiary_match.group(1))
    return ""


def _draft_pick_season_year(value: pd.Timestamp) -> int:
    return int(value.year + 1 if value.month >= 6 else value.year)


@st.cache_data(ttl=300, show_spinner=False)
def _get_all_draft_pick_notes() -> pd.DataFrame:
    refresh_key = int(pd.Timestamp.now().timestamp() // 300)
    csv_url = (
        "https://docs.google.com/spreadsheets/d/"
        "11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/"
        f"export?format=csv&gid=1612129799&refresh={refresh_key}"
    )
    return read_csv_snapshot("draft_pick_transaction_notes", csv_url, ttl_seconds=300, dtype=str).fillna("")


@st.cache_data(ttl=300, show_spinner=False)
def get_offseason_signing_history() -> pd.DataFrame:
    """Load the original auction and infer the year of each later offseason block."""
    refresh_key = int(pd.Timestamp.now().timestamp() // 300)
    csv_url = (
        "https://docs.google.com/spreadsheets/d/"
        "11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/"
        f"export?format=csv&gid=1352017576&refresh={refresh_key}"
    )
    raw = read_csv_snapshot("offseason_signing_history", csv_url, ttl_seconds=300, dtype=str).fillna("")
    required = ["Player", "Day", "High Bid", "Team"]
    if raw.empty or not set(required).issubset(raw.columns):
        return pd.DataFrame(columns=[
            "Offseason Year", "Season Year", "Player", "Day", "Date", "Team", "Amount", "Original Team",
        ])

    rows = []
    offseason_year = None
    previous_month_day = None
    for _, source in raw.iterrows():
        player = str(source.get("Player", "")).strip()
        day = str(source.get("Day", "")).strip()
        team = _draft_pick_team_key(source.get("Team", ""))
        amount_text = str(source.get("High Bid", "")).strip()
        if not player or not day or not team:
            continue

        partial_date = pd.to_datetime(day, format="%b %d", errors="coerce")
        if pd.isna(partial_date):
            continue
        month_day = (int(partial_date.month), int(partial_date.day))
        if amount_text:
            offseason_year = 2020
        else:
            if offseason_year is None or offseason_year == 2020:
                offseason_year = 2021
            elif previous_month_day is not None and month_day < previous_month_day:
                offseason_year += 1
            previous_month_day = month_day

        amount = pd.to_numeric(re.sub(r"[^0-9.-]", "", amount_text), errors="coerce")
        full_date = pd.Timestamp(year=int(offseason_year), month=month_day[0], day=month_day[1])
        rows.append({
            "Offseason Year": int(offseason_year),
            "Season Year": int(offseason_year) + 1,
            "Player": player,
            "Day": day,
            "Date": full_date,
            "Team": team,
            "Amount": amount,
            "Original Team": bool(amount_text),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def get_original_team_rosters() -> pd.DataFrame:
    history = get_offseason_signing_history()
    if history.empty:
        return history
    return history[history["Original Team"]].copy().reset_index(drop=True)


def _offseason_transactions_for_year(year: int) -> pd.DataFrame:
    history = get_offseason_signing_history()
    if history.empty:
        return pd.DataFrame(columns=FANTRAX_TRANSACTION_COLUMNS)
    signings = history[history["Season Year"].eq(int(year))].copy()
    if signings.empty:
        return pd.DataFrame(columns=FANTRAX_TRANSACTION_COLUMNS)

    rows = []
    for source_index, signing in signings.iterrows():
        team_name = _draft_pick_team_name(signing["Team"], int(year))
        amount = pd.to_numeric(signing.get("Amount"), errors="coerce")
        original_team = bool(signing.get("Original Team", False))
        notes = f"Year 1 salary: ${amount:,.0f}" if original_team and pd.notna(amount) else "Offseason signing"
        rows.append({
            "Year": int(year),
            "View": "Claim/Drop",
            "Transaction ID": f"offseason-signing-{int(year)}-{int(source_index)}",
            "Type": "Original Signing" if original_team else "Signing",
            "Player ID": f"offseason-{normalize_player_key(signing['Player']).replace(' ', '-')}",
            "Player": str(signing["Player"]),
            "Positions": "",
            "NBA Team": "",
            "Headshot": "",
            "Asset Type": "Player",
            "Asset Team": "",
            "Team": team_name,
            "From": "Free Agency",
            "To": team_name,
            "Date": pd.Timestamp(signing["Date"]).strftime("%b %d, %Y"),
            "Date Sort": pd.Timestamp(signing["Date"]),
            "Period": "Offseason",
            "Result": "Executed",
            "Notes": notes,
        })
    return pd.DataFrame(rows, columns=FANTRAX_TRANSACTION_COLUMNS)


def _fantrax_cell_map(row: dict) -> dict:
    return {
        str(cell.get("key", "")): cell.get("content", "")
        for cell in row.get("cells", [])
        if cell.get("key")
    }


def _parse_fantrax_transaction_rows(rows: list[dict], year: int, view: str) -> pd.DataFrame:
    """Flatten Fantrax transaction rows while preserving grouped trade IDs."""
    parsed = []
    group_metadata = {}
    for row in rows:
        transaction_id = str(row.get("txSetId", ""))
        cells = _fantrax_cell_map(row)
        metadata = group_metadata.setdefault(transaction_id, {})
        for key in ["team", "from", "to", "date", "week"]:
            if cells.get(key) not in [None, ""]:
                metadata[key] = cells[key]

        scorer = row.get("scorer") or {}
        draft_pick = row.get("draftPickDisplayParts") or {}
        round_text = re.sub(r"<[^>]+>", "", str(draft_pick.get("roundInfo", ""))).strip()
        year_text = re.sub(r"<[^>]+>", "", str(draft_pick.get("year", ""))).strip()
        draft_year_match = re.search(r"\b(20\d{2})\b", year_text)
        draft_round_match = re.search(r"\bRound\s+(\d+)\b", round_text, flags=re.IGNORECASE)
        draft_team_match = re.search(r"\(([^)]+)\)", round_text)
        is_draft_pick = bool(draft_pick)
        draft_year = draft_year_match.group(1) if draft_year_match else ""
        draft_round = draft_round_match.group(1) if draft_round_match else ""
        draft_team = draft_team_match.group(1).strip() if draft_team_match else ""
        draft_pick_name = " ".join(
            part for part in [draft_year, f"Round {draft_round}" if draft_round else "", "Draft Pick"] if part
        )
        raw_date = str(cells.get("date") or metadata.get("date") or "")
        parsed_date = pd.to_datetime(raw_date, errors="coerce")
        parsed.append({
            "Year": int(year),
            "View": "Trade" if view == "TRADE" else "Claim/Drop",
            "Transaction ID": transaction_id,
            "Type": "Trade" if view == "TRADE" else str(row.get("transactionType") or row.get("transactionCode") or "Claim/Drop").title(),
            "Player ID": str(scorer.get("scorerId", "")),
            "Player": draft_pick_name if is_draft_pick else str(scorer.get("name") or "Unknown asset"),
            "Positions": str(scorer.get("posShortNames", "")),
            "NBA Team": str(scorer.get("teamShortName", "")),
            "Headshot": str(scorer.get("headshotUrl", "")),
            "Asset Type": "Draft Pick" if is_draft_pick else "Player",
            "Asset Team": draft_team,
            "Team": str(cells.get("team") or metadata.get("team") or ""),
            "From": str(cells.get("from") or metadata.get("from") or ""),
            "To": str(cells.get("to") or metadata.get("to") or ""),
            "Date": raw_date,
            "Date Sort": parsed_date,
            "Period": str(cells.get("week") or metadata.get("week") or ""),
            "Result": str((row.get("result") or {}).get("content") or row.get("resultCode") or ""),
            "Notes": "",
        })
    return pd.DataFrame(parsed, columns=FANTRAX_TRANSACTION_COLUMNS)


def _fantrax_transaction_page(league_id: str, view: str, page_number: int, per_page: int = 500) -> dict:
    payload = {
        "msgs": [{
            "method": "getTransactionDetailsHistory",
            "data": {
                "leagueId": league_id,
                "maxResultsPerPage": str(per_page),
                "executedOnly": "true",
                "includeDeleted": "false",
                "view": view,
                "pageNumber": str(page_number),
            },
        }],
    }
    response = requests.post(
        "https://www.fantrax.com/fxpa/req",
        params={"leagueId": league_id},
        json=payload,
        headers={"User-Agent": "Mozilla/5.0 (compatible; SBCFBL/1.0)"},
        timeout=30,
    )
    response.raise_for_status()
    response_data = response.json()
    if response_data.get("pageError"):
        raise RuntimeError(str(response_data["pageError"]))
    return response_data["responses"][0]["data"]


def _draft_pick_transactions_for_year(year: int, fantrax_trade_rows: pd.DataFrame) -> pd.DataFrame:
    """Convert dated draft-pick Notes entries into trade assets and join them to Fantrax trade IDs."""
    picks = _get_all_draft_pick_notes()
    required_columns = {"Year", "Round", "OGTeam", "Notes"}
    if picks.empty or not required_columns.issubset(picks.columns):
        return pd.DataFrame(columns=FANTRAX_TRANSACTION_COLUMNS)

    fantrax_groups = []
    if fantrax_trade_rows is not None and not fantrax_trade_rows.empty:
        for transaction_id, group in fantrax_trade_rows.groupby("Transaction ID", sort=False):
            date_sort = pd.to_datetime(group["Date Sort"].iloc[0], errors="coerce")
            if pd.isna(date_sort):
                continue
            team_keys = {
                _draft_pick_team_key(team)
                for column in ["From", "To"]
                for team in group[column].dropna().astype(str)
                if str(team).strip()
            }
            fantrax_groups.append({
                "id": str(transaction_id),
                "date": date_sort.normalize(),
                "date_label": str(group["Date"].iloc[0]),
                "date_sort": date_sort,
                "period": str(group["Period"].iloc[0]),
                "teams": team_keys,
            })

    parsed_rows = []
    for row_number, pick in picks.reset_index(drop=True).iterrows():
        draft_year = str(pick.get("Year", "")).strip()
        draft_round = str(pick.get("Round", "")).strip()
        original_team_key = _draft_pick_team_key(pick.get("OGTeam", ""))
        current_owner_key = original_team_key
        if not draft_year or not draft_round or not original_team_key:
            continue

        for note_number, raw_note in enumerate(re.split(r"[\r\n]+", str(pick.get("Notes", "")))):
            note_line = raw_note.strip()
            note_match = re.match(r"^(\d{1,2}/\d{1,2}/\d{4})(?:\s*;)?\s*(.*)$", note_line)
            if not note_match:
                continue
            note_date = pd.to_datetime(note_match.group(1), errors="coerce")
            note = note_match.group(2).strip(" ;,")
            if pd.isna(note_date):
                continue

            owner_before_key = current_owner_key
            target_key = _draft_pick_note_target(note)
            is_direct_transfer = bool(re.match(r"^(?:to|conveyed to)\s+", note, flags=re.IGNORECASE))
            other_side_match = re.search(r"\b(?:given|conveyed) to\s+([^;,.(]+)", note, flags=re.IGNORECASE)
            if other_side_match and not target_key:
                target_key = _draft_pick_team_key(other_side_match.group(1))
                is_direct_transfer = True
            if is_direct_transfer and target_key:
                current_owner_key = target_key

            if note_date < DRAFT_PICK_TRANSACTION_CUTOFF or "see this" in note.lower() or "see " in note.lower():
                continue
            season_year = _draft_pick_season_year(note_date)
            if season_year != int(year):
                continue

            participant_keys = {key for key in [owner_before_key, target_key] if key}
            matching_groups = [group for group in fantrax_groups if group["date"] == note_date.normalize()]
            best_group = None
            best_score = 0
            for group in matching_groups:
                overlap = len(participant_keys & group["teams"])
                route_match = bool(owner_before_key and target_key and {owner_before_key, target_key}.issubset(group["teams"]))
                score = overlap + (4 if route_match else 0)
                if score > best_score:
                    best_group = group
                    best_score = score
            if best_score < 2:
                best_group = None

            route_keys = sorted(participant_keys) or [original_team_key]
            synthetic_id = f"draft-notes-{note_date.strftime('%Y%m%d')}-{'-'.join(route_keys).lower().replace(' ', '-')}"
            transaction_id = best_group["id"] if best_group else synthetic_id
            date_label = best_group["date_label"] if best_group else note_date.strftime("%b %d, %Y")
            date_sort = best_group["date_sort"] if best_group else note_date
            period = best_group["period"] if best_group else ""
            from_team = _draft_pick_team_name(owner_before_key, season_year)
            to_team = _draft_pick_team_name(target_key, season_year) if target_key else from_team
            round_number_match = re.search(r"\d+", draft_round)
            round_number = round_number_match.group(0) if round_number_match else draft_round
            asset_name = f"{draft_year} Round {round_number} Draft Pick"

            parsed_rows.append({
                "Year": season_year,
                "View": "Trade",
                "Transaction ID": transaction_id,
                "Type": "Trade",
                "Player ID": f"pick-{draft_year}-{round_number}-{original_team_key.lower().replace(' ', '-')}",
                "Player": asset_name,
                "Positions": "",
                "NBA Team": "",
                "Headshot": "",
                "Asset Type": "Draft Pick",
                "Asset Team": _draft_pick_team_name(original_team_key, season_year),
                "Team": "",
                "From": from_team,
                "To": to_team,
                "Date": date_label,
                "Date Sort": date_sort,
                "Period": period,
                "Result": "Executed",
                "Notes": note,
                "_source_row": row_number,
                "_source_note": note_number,
            })

    if not parsed_rows:
        return pd.DataFrame(columns=FANTRAX_TRANSACTION_COLUMNS)
    parsed = pd.DataFrame(parsed_rows).drop_duplicates(
        subset=["Year", "Player ID", "Date Sort", "Notes", "From", "To"], keep="first"
    )
    return parsed[FANTRAX_TRANSACTION_COLUMNS]


@st.cache_data(ttl=300, show_spinner=False)
def get_fantrax_transactions(year: int) -> pd.DataFrame:
    """Load executed Claim/Drop and Trade activity for one SBCFBL season."""
    year = int(year)
    league_id = league_ids.get(year)
    if not league_id:
        return pd.DataFrame(columns=FANTRAX_TRANSACTION_COLUMNS)

    transaction_frames = []
    for view in ["CLAIM_DROP", "TRADE"]:
        page_number = 1
        while True:
            data = _fantrax_transaction_page(league_id, view, page_number)
            transaction_frames.append(_parse_fantrax_transaction_rows(data.get("table", {}).get("rows", []), year, view))
            pagination = data.get("paginatedResultSet", {})
            total_pages = max(1, int(pagination.get("totalNumPages", 1) or 1))
            if page_number >= total_pages:
                break
            page_number += 1

    transactions = [frame for frame in transaction_frames if not frame.empty]
    result = (
        pd.concat(transactions, ignore_index=True)
        if transactions else pd.DataFrame(columns=FANTRAX_TRANSACTION_COLUMNS)
    )
    offseason_transactions = _offseason_transactions_for_year(year)
    if not offseason_transactions.empty:
        signing_dates = {}
        for _, signing in offseason_transactions.iterrows():
            signing_key = (
                normalize_player_key(signing["Player"]),
                _draft_pick_team_key(signing["Team"]),
            )
            signing_dates.setdefault(signing_key, []).append(pd.Timestamp(signing["Date Sort"]).normalize())
        if not result.empty:
            duplicate_claim = []
            for _, transaction in result.iterrows():
                is_claim = (
                    str(transaction.get("View", "")) == "Claim/Drop"
                    and str(transaction.get("Type", "")).strip().lower() == "claim"
                )
                transaction_date = pd.to_datetime(transaction.get("Date Sort"), errors="coerce")
                transaction_key = (
                    normalize_player_key(transaction.get("Player", "")),
                    _draft_pick_team_key(transaction.get("Team", "")),
                )
                close_to_source = False
                if is_claim and pd.notna(transaction_date):
                    close_to_source = any(
                        abs((transaction_date.normalize() - source_date).days) <= 75
                        for source_date in signing_dates.get(transaction_key, [])
                    )
                duplicate_claim.append(close_to_source)
            result = result.loc[~pd.Series(duplicate_claim, index=result.index)].copy()
        result = pd.concat([result, offseason_transactions], ignore_index=True)
    pick_transactions = _draft_pick_transactions_for_year(
        year, result[result["View"].eq("Trade")].copy() if not result.empty else result
    )
    if not pick_transactions.empty:
        result = pd.concat([result, pick_transactions], ignore_index=True)
    if result.empty:
        return pd.DataFrame(columns=FANTRAX_TRANSACTION_COLUMNS)
    return result.sort_values(["Date Sort", "Transaction ID"], ascending=[False, True], na_position="last").reset_index(drop=True)

@st.cache_data(ttl=86400)
def get_standings() -> pd.DataFrame:
    return DATA_REPOSITORY.read("standings", required=True)

@st.cache_data()
def get_fantrax_matchups(year) -> pd.DataFrame:
    league_id = league_ids.get(year)
    if not league_id:
        return pd.DataFrame()
    roster_url = f"https://www.fantrax.com/fxea/general/getLeagueInfo?leagueId={league_id}"
    headers = {'Cookie': 'JSESSIONID='}
    response = requests.get(roster_url, headers=headers)
    if response.status_code == 200:
        Matchups = json.loads(response.text)
        df = pd.DataFrame(Matchups)
    else:
        print(f"Failed to fetch data - Status code: {response.status_code}")
    return df

@st.cache_data()
def get_draft_history() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1546613902"
    df = read_csv_snapshot("draft_history", csv_url)
    return df

@st.cache_data(ttl=300)
def get_award_history() -> pd.DataFrame:
    refresh_key = int(pd.Timestamp.now().timestamp() // 300)
    csv_url = (
        "https://docs.google.com/spreadsheets/d/"
        "1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/"
        f"export?format=csv&gid=1698988928&refresh={refresh_key}"
    )
    df = read_csv_snapshot("award_history", csv_url, ttl_seconds=0)
    df = df.melt(id_vars=["Award"], var_name="Year", value_name="Winner")
    df = df[df["Year"].str.isnumeric()] 
    df["Year"] = df["Year"].astype(int)    
    return df

@st.cache_data(ttl=300)
def get_team_award_history() -> pd.DataFrame:
    refresh_key = int(pd.Timestamp.now().timestamp() // 300)
    csv_url = (
        "https://docs.google.com/spreadsheets/d/"
        "1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/"
        f"export?format=csv&gid=451021615&refresh={refresh_key}"
    )
    df = read_csv_snapshot("team_award_history", csv_url, ttl_seconds=0)
    df = df.melt(id_vars=["Award"], var_name="Year", value_name="Winner")  
    df = df[df["Year"].str.isnumeric()] 
    df["Year"] = df["Year"].astype(int)    
    return df

@st.cache_data()
def get_all_time_schedule() -> pd.DataFrame:
    return DATA_REPOSITORY.read("schedule", required=True)


def future_matchup_periods(period_calendar: pd.DataFrame, as_of=None) -> set[tuple[int, int]]:
    """Return schedule periods whose first calendar date is still in the future."""
    required = {"Year", "Period", "Date"}
    if period_calendar is None or period_calendar.empty or not required.issubset(period_calendar.columns):
        return set()
    calendar = period_calendar[["Year", "Period", "Date"]].copy()
    calendar["Year"] = pd.to_numeric(calendar["Year"], errors="coerce")
    calendar["Period"] = pd.to_numeric(calendar["Period"], errors="coerce")
    calendar["Date"] = pd.to_datetime(calendar["Date"], errors="coerce")
    calendar = calendar.dropna(subset=["Year", "Period", "Date"])
    if calendar.empty:
        return set()
    cutoff = pd.Timestamp.now(tz="America/New_York") if as_of is None else pd.Timestamp(as_of)
    if cutoff.tzinfo is not None:
        cutoff = cutoff.tz_convert("America/New_York").tz_localize(None)
    cutoff = cutoff.normalize()
    starts = calendar.groupby(["Year", "Period"], as_index=False)["Date"].min()
    future = starts[starts["Date"].dt.normalize() > cutoff]
    return {(int(row.Year), int(row.Period)) for row in future.itertuples(index=False)}


def zero_future_matchup_scores(schedule: pd.DataFrame, period_calendar: pd.DataFrame, as_of=None) -> pd.DataFrame:
    """Keep every not-yet-started matchup at 0-0, even if stored scores are stale."""
    if schedule is None or schedule.empty or not {"Year", "Period"}.issubset(schedule.columns):
        return schedule.copy() if isinstance(schedule, pd.DataFrame) else pd.DataFrame()
    future_periods = future_matchup_periods(period_calendar, as_of=as_of)
    if not future_periods:
        return schedule.copy()
    work = schedule.copy()
    keys = list(zip(pd.to_numeric(work["Year"], errors="coerce"), pd.to_numeric(work["Period"], errors="coerce")))
    future_mask = pd.Series([key in future_periods for key in keys], index=work.index)
    for column in ["TeamAScore", "TeamBScore"]:
        if column in work.columns:
            work.loc[future_mask, column] = 0
    return work

def current_matchup_period() -> float:
    csv_url = "https://docs.google.com/spreadsheets/d/1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg/export?format=csv&gid=444367429"
    df = read_csv_snapshot("schedule_calendar", csv_url, ttl_seconds=3600)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    current_season = df[df["Year"] == current_year].sort_values("Date")
    df2 = current_season[current_season["Date"] == today]
    if len(df2) == 0:
        if current_season.empty:
            return 1
        elapsed = current_season[current_season["Date"] <= today]
        if elapsed.empty:
            return int(current_season["Period"].iloc[0])
        return int(elapsed["Period"].iloc[-1])
    if len(df2) == 1:
        return int(df2["Period"].iloc[0])
    return int(df2["Period"].iloc[-1])

def get_matchup_stats(year: int, period: int) -> pd.DataFrame:
    league_id = league_ids.get(year)
    if not league_id:
        return pd.DataFrame()
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json", "Cookie": "JSESSIONID=YOUR_REAL_SESSION_ID"})
    payload = {"msgs": [{"method": "getLiveScoringStats","data": {"sppId": "-1", "teamId": "ALL", "period": period, "date": today.isoformat(), "viewType": "2", "playerViewType": "1", "newView": False}}, {"method": "getScoresSummaryData", "data": {}}]}
    response = session.post("https://www.fantrax.com/fxpa/req", params={"leagueId": league_id}, json=payload)
    if response.status_code == 200:
        data = response.json()
        scoring_categories = ['Team', 'GP', 'MP', 'TS%', '2PTM', '2PTA', '2PT%', '3PTM', '3PTA', '3PT%', 'FTM', 'FTA', 'FT%', 'PTS', 'OREB', 'DREB', 'AST', 'ST', 'BLK', 'TO', '+/-']
        team_id_to_name = {}
        for team_name, years in team_id_history.items():
            for _, team_id in years.items():
                team_id_to_name[team_id] = team_name
        year_key = f"{year}_id"
        team_ids = [ids.get(year_key) for ids in team_id_history.values() if ids.get(year_key)]        
        rows = []
        for team_id in team_ids:
            row = {'Team': team_id}
            team_stats = (
                data['responses'][0]["data"]
                .get('statsPerTeam', {})
                .get('allTeamsStats', {})
                .get(team_id, {})
                .get('ACTIVE', {})
                .get('statsMap', {}))
            stats_list = (
                team_stats
                .get('_3010', {})
                .get('object2', []))
            stats_dict = {
                stat.get('scipId'): stat.get('av')
                for stat in stats_list
                if stat.get('scipId') is not None}
            if year <= 2025:
                for stat_name in scoring_categories[2:]:
                    scipId = stat_to_scipId.get(stat_name)
                    row[stat_name] = stats_dict.get(scipId, 0)
            else:
                for stat_name in scoring_categories[1:]:
                    scipId = stat_to_scipId.get(stat_name)
                    row[stat_name] = stats_dict.get(scipId, 0)
            rows.append(row)
        df = pd.DataFrame(rows, columns=scoring_categories)
        df["Team"] = df["Team"].map(team_id_to_name)
        df.loc[(df["2PTA"] < 10) | (df["3PTA"] < 10) | (df["FTA"] < 5), ['TS%', '2PT%', '3PT%', 'FT%']] = 0
        return df
    else:
        print(f"Error: Request failed for URL with status code {response.status_code}")
        return None

def style_salaries(row, type_colors):
    styles = [""] * len(row)
    for i, col in enumerate(row.index):
        if col.isdigit():
            type_col = f"Type{col}"
            if type_col in row.index:
                contract_type = row[type_col]
                color = type_colors.get(contract_type, None)
                if color:
                    styles[i] = f"background-color: {color}; color: black;"
    return styles

def active_roster_mask(df: pd.DataFrame) -> pd.Series:
    mask = df['Type'] == 'Active Players'
    type_col = "Type" + str(current_year)
    if type_col in df.columns:
        mask = mask & ~df[type_col].isin(["Unrestricted", "Restricted"])
    return mask

def contract_salary_mask(df: pd.DataFrame) -> pd.Series:
    type_col = "Type" + str(current_year)
    if type_col not in df.columns:
        return pd.Series(False, index=df.index)
    contract_types = ["Guaranteed", "Unguaranteed", "Non-Guaranteed", "Team"]
    return df[type_col].isin(contract_types)

def taxable_salary_mask(df: pd.DataFrame) -> pd.Series:
    type_col = "Type" + str(current_year)
    if type_col not in df.columns:
        return pd.Series(False, index=df.index)
    taxable_types = ["Dead", "Guaranteed", "Unguaranteed", "Non-Guaranteed", "Team"]
    return df[type_col].isin(taxable_types)

def cap_space_exception_mask(exceptions_df: pd.DataFrame) -> pd.Series:
    exception_name = exceptions_df["Player"].astype(str)
    normalized_name = exception_name.str.lower().str.replace(r"[^a-z0-9]+", "", regex=True)
    excluded = normalized_name.str.contains("midlevel|mle|biannual|bae|minimum", na=False)
    return ~excluded

def active_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[active_roster_mask(df)]
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def overseas_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Non-Active Players']
    df = df[contract_salary_mask(df)]
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def dead_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Non-Active Players']
    df = df[df["Type" + str(current_year)] == "Dead"]
    df = df[df["Trade.Restriction"] != "Retired"]
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def free_agent_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df["Type" + str(current_year + year_offset)].isin(['Unrestricted', 'Restricted'])]
    if "BirdRights" not in df.columns:
        df["BirdRights"] = ""
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year + year_offset), ascending=False)
    return df

def draft_retired_players(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[(df["Type" + str(current_year)] == 'Draft Rights') | (df['Trade.Restriction'] == 'Retired')]
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def exception_table(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['Team'] == SelectedTeam]
    df = df[df["Y" + str(current_year)] > 0]
    df = df.drop(columns=["Team"])
    df = df.rename(columns={'Player': 'Exception'})
    df = df.rename(columns={"Y" + str(current_year): 'Amount'})
    df = df.rename(columns={'BirdRights': 'Expiration Date'})
    df = df.sort_values('Amount', ascending=False)
    return df

def active_player_n(df: pd.DataFrame, SelectedTeam: str) -> float:
    df = df[df['Team'] == SelectedTeam]
    df = df[active_roster_mask(df)]
    return df.shape[0]

def inactive_player_n(df: pd.DataFrame, SelectedTeam: str) -> float:
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Type'] == 'Non-Active Players']
    df = df[contract_salary_mask(df)]
    return df.shape[0]

def get_cap_total(df: pd.DataFrame, exceptions_df: pd.DataFrame, SelectedTeam: str) -> float:
    df = df[df['Team'] == SelectedTeam]
    player_total = df["Y" + str(current_year)].sum()
    exceptions_df = exceptions_df[exceptions_df['Team'] == SelectedTeam]
    exceptions_df = exceptions_df[cap_space_exception_mask(exceptions_df)]
    exceptions_total = exceptions_df["Y" + str(current_year)].sum()
    total_cap = player_total + exceptions_total
    ap = 12-active_player_n(df, SelectedTeam)
    if ap > 0:
        min_penalty = minimum_sal * ap
        total_cap = min_penalty + total_cap
    return total_cap

def get_tax_total(df: pd.DataFrame, SelectedTeam: str) -> float:
    df = df[df['Team'] == SelectedTeam]
    df = df[taxable_salary_mask(df)]
    player_total = df["Y" + str(current_year)].sum()
    return player_total

def team_hard_cap(df: pd.DataFrame, SelectedTeam: str) -> str:
    df = df[df['Team'] == SelectedTeam]
    hard_cap = df['HardCap'].values[0]
    return hard_cap

def team_hard_cap_n(df: pd.DataFrame, SelectedTeam: str, base_cap: pd.DataFrame) -> str:
    tax_number = get_tax_total(df, SelectedTeam)
    hard_cap_type = team_hard_cap(base_cap, SelectedTeam)
    if hard_cap_type == "None":
        return None
    elif hard_cap_type == "First Apron":
        return tax_number-current_apron_1
    elif hard_cap_type == "Second Apron":
        return tax_number-current_apron_2

def base_fee(df: pd.DataFrame, SelectedTeam: str, base_cap: pd.DataFrame) -> float:
    payment = get_tax_total(df, SelectedTeam)
    payment = current_salary_cap * 0.9 if payment < current_salary_cap * 0.9 else payment
    payment = payment/league_ratio
    base_cap = base_cap[base_cap['Team'] == SelectedTeam]
    rate = base_cap["Rate"].iloc[0]
    payment = payment*rate
    payment = payment+3
    return payment

def luxury_fee(df: pd.DataFrame, SelectedTeam: str, base_cap: pd.DataFrame) -> float:
    df = df[df['Team'] == SelectedTeam]
    tax_number = get_tax_total(df, SelectedTeam)
    tax_number = tax_number-current_luxury_tax
    repeater_penalty = is_repeater_tax_team(base_cap, SelectedTeam)
    tax_amount = tax_amount_calc(tax_number, repeater_penalty)
    tax_amount = tax_amount/league_ratio
    base_cap = base_cap[base_cap['Team'] == SelectedTeam]
    rate = base_cap["Rate"].iloc[0]
    tax_amount = tax_amount*rate
    return tax_amount

def is_repeater_tax_team(base_cap: pd.DataFrame, SelectedTeam: str) -> bool:
    team_base = base_cap[base_cap['Team'] == SelectedTeam]
    if team_base.empty:
        return False
    tax_cols = [f"Tax{year}" for year in range(current_year - 4, current_year)]
    paid_years = 0
    for col in tax_cols:
        if col in team_base.columns:
            paid_years += pd.to_numeric(team_base[col], errors="coerce").fillna(0).iloc[0]
    return paid_years >= 3

def tax_amount_calc(fee: float, repeater: bool) -> float:
    penalty_false = [1.0, 0.25, 2.25, 1.25]
    penalty_true = [3.0, 0.25, 2.25, 1.25]
    if fee <= 0:
        return 0
    elif repeater:
        tax = fee * penalty_true[0]
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_true[1])
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_true[2])
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_true[3])
        fee = fee - tax_bracket_increment
        while fee > 0:
            tax = tax + (fee * 0.5)
            fee = fee - tax_bracket_increment
        return tax
    elif not repeater:
        tax = fee * penalty_false[0]
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_false[1])
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_false[2])
        fee = fee - tax_bracket_increment
        if fee <= 0:
            return tax
        tax = tax + (fee * penalty_false[3])
        fee = fee - tax_bracket_increment
        while fee > 0:
            tax = tax + (fee * 0.5)
            fee = fee - tax_bracket_increment
        return tax

def amount_paid(df: pd.DataFrame, SelectedTeam: str) -> float:
    df = df[df['Team'] == SelectedTeam]
    df = df["MoneyPaid"].iloc[0]
    return df

def net_fee(df: pd.DataFrame, SelectedTeam: str, base_cap: pd.DataFrame) -> float:
    fee = base_fee(df, SelectedTeam, base_cap)
    tax = luxury_fee(df, SelectedTeam, base_cap)
    paid = amount_paid(base_cap, SelectedTeam)
    net_fee = tax + fee - paid
    net_fee = -net_fee
    return math.ceil(net_fee * 100) / 100

def trade_restrictions(df: pd.DataFrame, pics: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Trade.Restriction'].notna()]
    df = df[df['Trade.Restriction'] != "Retired"]
    df = df[df['Player'] != "Minimum Salary Penalty"]
    df = df[['Picture_Online','Player','Trade.Restriction']]
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'Trade.Restriction': 'Trade Restriction'})
    df = df.sort_values('Player', ascending=True)
    return df

def active_players_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[active_roster_mask(df)]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def inactive_players_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Type'] == 'Non-Active Players']
    df = df[contract_salary_mask(df)]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def dead_players_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Type'] == 'Non-Active Players']
    df = df[df["Type" + str(current_year)] == "Dead"]
    df = df[df["Trade.Restriction"] != "Retired"]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df["Bird Rights"] = ""
    df = df.sort_values(str(current_year), ascending=False)
    return df

def draft_rights_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[(df["Type" + str(current_year)] == 'Draft Rights')]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values('Player', ascending=True)
    return df

def retired_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[(df['Trade.Restriction'] == 'Retired')]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values('Player', ascending=True)
    return df

def all_free_agents(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df["Type" + str(current_year + year_offset)].isin(['Unrestricted', 'Restricted'])]
    if "BirdRights" not in df.columns:
        df["BirdRights"] = ""
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year + year_offset), ascending=False)
    return df

def trade_restrictions_all(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Trade.Restriction'].notna()]
    df = df[df['Trade.Restriction'] != "Retired"]
    df = df[df['Player'] != "Minimum Salary Penalty"]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df[['Team_logo', 'Picture_Online','Player','Trade.Restriction']]
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'Trade.Restriction': 'Trade Restriction'})
    df = df.sort_values('Player', ascending=True)
    return df

def overall_cap_table(df: pd.DataFrame, exceptions_df: pd.DataFrame, base_cap: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "Logo": [info["logo"] for info in team_info.values()],
        "Team": list(team_info.keys()),
        "Active Players": [active_player_n(df, team) for team in team_info.keys()],
        "Cap Space": [current_salary_cap - get_cap_total(df, exceptions_df, team) for team in team_info.keys()],
        "Tax Space": [current_luxury_tax - get_tax_total(df, team) for team in team_info.keys()],
        "Hard Cap": [team_hard_cap(base_cap, team) for team in team_info.keys()],
        "Apron 1 Space": [current_apron_1 - get_tax_total(df, team) for team in team_info.keys()],
        "Apron 2 Space": [current_apron_2 - get_tax_total(df, team) for team in team_info.keys()],
        "Base Fee": [base_fee(df, team, base_cap) for team in team_info.keys()],
        "Luxury Fee": [luxury_fee(df, team, base_cap) for team in team_info.keys()],
        "Luxury Fee Type": ["Repeater" if is_repeater_tax_team(base_cap, team) else "Standard" for team in team_info.keys()],
        "Balance": [net_fee(df, team, base_cap) for team in team_info.keys()],
        "Amount Paid": [amount_paid(base_cap, team) for team in team_info.keys()]})
    return df

LEAGUE_FANTRAX_FEE = 130
LEAGUE_LARRY_COON_FEE = 100
LEAGUE_IST_POOL = 90
BASE_PAYOUT_UNITS = 24


def unit_payout(df: pd.DataFrame, exceptions_df: pd.DataFrame, base_cap: pd.DataFrame) -> float:
    df = overall_cap_table(df, exceptions_df, base_cap)
    total_fee = df["Base Fee"].sum()
    total_fee = total_fee - LEAGUE_FANTRAX_FEE - LEAGUE_LARRY_COON_FEE - LEAGUE_IST_POOL
    total_fee = total_fee / BASE_PAYOUT_UNITS
    return total_fee

def tax_payout_champ(df: pd.DataFrame, exceptions_df: pd.DataFrame, base_cap: pd.DataFrame) -> float:
    df = overall_cap_table(df, exceptions_df, base_cap)
    total_fee = df["Luxury Fee"].sum()
    total_fee = total_fee/2
    return total_fee

def tax_payout_split(df: pd.DataFrame, exceptions_df: pd.DataFrame, base_cap: pd.DataFrame) -> float:
    df = overall_cap_table(df, exceptions_df, base_cap)
    total_fee = df["Luxury Fee"].sum()
    total_fee = total_fee/2
    non_tax_teams = (df["Luxury Fee"] == 0).sum()
    total_fee = total_fee / non_tax_teams if non_tax_teams else 0
    return total_fee

def style_overall_cap(row):
    styles = [""] * len(row)
    for i, col in enumerate(row.index):
        value = row[col]
        if col == "Active Players":
            if 15 <= value <= 17:
                styles[i] = "color: #F9A01B;"
            elif value <= 11 or value >= 18 or value == 0:
                styles[i] = "color: red;"
        elif col in ["Cap Space", "Tax Space"]:
            color = "green" if value > 0 else "red"
            styles[i] = f"color: {color};"
        elif col == "Hard Cap":
            if value in ["Second Apron", "First Apron"]:
                styles[i] = "color: #F9A01B;"
        elif col == "Apron 1 Space":
            if value < 0:
                styles[i] = "color: red;"
            elif row.get("Hard Cap") == "First Apron":
                styles[i] = "color: #F9A01B;"
        elif col == "Apron 2 Space":
            if value < 0:
                styles[i] = "color: red;"
            elif row.get("Hard Cap") == "Second Apron":
                styles[i] = "color: #F9A01B;"
        elif col == "Balance":
            color = "green" if value > -0.005 else "red"
            styles[i] = f"color: {color};"
        elif col == "Amount Paid" and value == 0:
            styles[i] = "color: red;"
    return styles

def full_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['FullyOwned']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df[df['PickSwap'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def swap_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['PickSwap']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def split_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['FullyOwned'] == False]  # noqa: E712
    df = df[df['PickSwap'] == False]  # noqa: E712
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def locked_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam, na=False))]
    df = df[df['Locked']]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def original_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['OGTeam'] == SelectedTeam) & (df['CurrentTeam'].str.contains(SelectedTeam) == False)]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def touched_draft_picks(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['TeamTouched'].str.contains(SelectedTeam, na=False))]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def all_full_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['FullyOwned']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df[df['PickSwap'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def all_swap_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['PickSwap']]
    df = df[df['FullyOwned']]
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def all_split_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['FullyOwned'] == False]  # noqa: E712
    df = df[df['PickSwap'] == False]  # noqa: E712
    df = df[df['Locked'] == False]  # noqa: E712
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.rename(columns={'CurrentTeam': 'Potential Owners'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def all_locked_draft_picks(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df['TwoYearLimit'] == False]  # noqa: E712
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['Locked']]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes'])
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.rename(columns={'TeamTouched': 'Contacted'})
    df = df.sort_values(['Round', 'Year'], ascending=[True, True])
    return df

def data_picture_check(df: pd.DataFrame, pics: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Picture_Online'].isna()]
    df = df[['Player', 'Picture_Online']]
    df = df.rename(columns={'Picture_Online': 'Picture'})
    return df

def data_roster_check(df: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "Team": list(team_info.keys()),
        "Active Players": [active_player_n(df, team) for team in team_info.keys()]})
    df = df[(df['Active Players'] > 17) | (df['Active Players'] < 12)]
    return df

def data_missing_salary_check(df: pd.DataFrame) -> pd.DataFrame:
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team', 'Player'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    year_cols = [f"Y{year}" for year in columns_order]
    type_cols = [f"Type{year}" for year in columns_order]
    salary_long = df.melt(id_vars = ["Team", "Player"], value_vars = year_cols, var_name = "Year", value_name = "Salary")
    salary_long["Year"] = salary_long["Year"].str.replace("Y", "", regex=False)
    type_long = df.melt(id_vars = ["Team", "Player"], value_vars = type_cols, var_name = "Year",  value_name = "Type")
    type_long["Year"] = type_long["Year"].str.replace("Type", "", regex=False)
    long_df = salary_long.merge(type_long,on=["Team", "Player", "Year"], how="left")
    df = long_df[long_df["Type"].notna() & long_df["Salary"].isna()]
    return df

def hard_cap_check(df: pd.DataFrame, base_cap: pd.DataFrame) -> str:
    df = pd.DataFrame({
        "Team": team_info.keys(),
        "HardCapResult": [team_hard_cap_n(df, team, base_cap) for team in team_info.keys()]})
    df = df[df['HardCapResult'] > 0]
    df["HardCapResult"] = df["HardCapResult"].apply(lambda x: f"${x:,.0f}")
    df = df.rename(columns={'HardCapResult': 'Over Amount'})
    return df

def stepien_data_check(df: pd.DataFrame) -> pd.DataFrame:
    df = get_draft_picks()


    df2 = pd.DataFrame({
        "Year": [current_year-1] * 30,
        "Round": ["1st Round"] * 30,
        "CurrentTeam": list(team_info.keys())
    })
    df = df[(df['FullyOwned']) | (df['Locked']) | (df['TwoYearLimit'])]
    df['Year'] = np.where(df['TwoYearLimit'], df['Year'] + 0.5, df['Year'])
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes','OGTeam','TeamTouched','Explanation', 'TwoYearLimit'])
    df = df[df['Round'] == "1st Round"]
    df = df.assign(CurrentTeam=df['CurrentTeam'].str.split(', ')) \
       .explode('CurrentTeam') \
       .reset_index(drop=True)
    df = pd.concat([df2, df], ignore_index=True)
    df = df.sort_values(["CurrentTeam", "Year"])
    df["next_year"] = df.groupby("CurrentTeam")["Year"].shift(-1)
    df["next_year"] = df["next_year"].fillna(current_year + 7)
    df["gap"] = df["next_year"] - df["Year"]
    mask = ((df["Year"] % 1 == 0.5) & (df["next_year"] % 1 == 0.5) & (df["gap"] == 2))
    df.loc[mask, "gap"] = 3
    df = df[df["gap"] > 2]
    df = df[['CurrentTeam', 'Year','next_year']]
    df = df.rename(columns={'CurrentTeam': 'Team'})
    df = df.rename(columns={'year': 'Gap Open'})
    df = df.rename(columns={'next_year': 'Gap Closed'})
    return df

def tradeable_players_out(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df[df['Team'] == SelectedTeam]
    df = df[df['Trade.Restriction'].isna()]
    df = df[['Player']]
    df = df.sort_values('Player', ascending=True)
    df_list = df['Player'].tolist()
    return df_list

def tradeable_players_in(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df[df['Team'] != SelectedTeam]
    df = df[df['Trade.Restriction'].isna()]
    df = df[['Player']]
    df = df.sort_values('Player', ascending=True)
    df_list = df['Player'].tolist()
    return df_list

def tradeable_picks_out(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df.drop(columns=["TwoYearLimit"])
    df = df[df['CurrentTeam'].str.contains(SelectedTeam)]
    df = df[df['Locked'] == False] #noqa: E712
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df.sort_values('Pick', ascending=True)
    df_list = df['Pick'].tolist()
    return df_list

def tradeable_picks_in(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df.drop(columns=["TwoYearLimit"])
    df = df[(df['CurrentTeam'].str.contains(SelectedTeam)) == False]  # noqa: E712
    df = df[df['Locked'] == False]  # noqa: E712
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df.sort_values('Pick', ascending=True)
    df_list = df['Pick'].tolist()
    return df_list

def tradeable_exceptions_in(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df[df["Y" + str(current_year)] > 0]
    df = df[df["Player"] != "Minimum"]
    df = df[df["Team"] != SelectedTeam]
    df["Exception"] = (df["Team"].astype(str) + " " + df["Player"].astype(str))
    df = df.sort_values('Exception', ascending=True)
    df_list = df['Exception'].tolist()
    df_list.append("Minimum")
    return df_list

def tradeable_exceptions_out(df: pd.DataFrame, SelectedTeam: str) -> list[str]:
    df = df[df["Y" + str(current_year)] > 0]
    df = df[df["Player"] != "Minimum"]
    df = df[df["Team"] == SelectedTeam]
    df["Exception"] = (df["Team"].astype(str) + " " + df["Player"].astype(str))
    df = df.sort_values('Exception', ascending=True)
    df_list = df['Exception'].tolist()
    df_list.append("Minimum")
    return df_list

def players_out_table(df: pd.DataFrame, pics: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Player'].isin(selected_players)]
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def players_in_table(df: pd.DataFrame, pics: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df = df.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    df = df[df['Player'].isin(selected_players)]
    df["Team_logo"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    year_cols = ["Y" + year for year in columns_order]
    type_cols_keep = ["Type" + year for year in columns_order]
    cols_to_keep = ['Team_logo', 'Picture_Online','Player','BirdRights'] + year_cols + type_cols_keep
    df = df[cols_to_keep].copy()
    df = df.rename(columns={'Picture_Online': ' '})
    df = df.rename(columns={'BirdRights': 'Bird Rights'})
    df = df.rename(columns={col: col[1:] for col in year_cols})
    df = df.sort_values(str(current_year), ascending=False)
    return df

def picks_out_table(df: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df = df.drop(columns=["TwoYearLimit"])
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df[df['Pick'].isin(selected_players)]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes', 'TeamTouched','Pick'])
    df["CurrentTeam"] = df["CurrentTeam"].apply(lambda x: team_info.get(x.split(",")[0].strip(), {}).get("logo", ""))
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def picks_in_table(df: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df = df.drop(columns=["TwoYearLimit"])
    df["Pick"] = (df["OGTeam"].astype(str) + " " + df["Year"].astype(str) + " " + df["Round"].astype(str))
    df = df[df['Pick'].isin(selected_players)]
    df = df.drop(columns=['PickSwap', 'FullyOwned', 'Locked', 'Notes', 'TeamTouched','Pick'])
    df["OGTeam"] = df["OGTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df["CurrentTeam"] = df["CurrentTeam"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.sort_values('Year', ascending=True)
    df = df.sort_values('Round', ascending=True)
    return df

def exceptions_in_table(df: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df["Exception"] = (df["Team"].astype(str) + " " + df["Player"].astype(str))
    df = df[df['Exception'].isin(selected_players)]
    df["Team"] = df["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    df = df.drop(columns=['Exception'])
    df = df.rename(columns={'Player': 'Exception'})
    df = df.rename(columns={"Y" + str(current_year): str(current_year)})
    df[str(current_year)] = df[str(current_year)].apply(lambda x: f"${x:,.0f}")
    df = df.rename(columns={'BirdRights': 'Expiration Date'})
    df = df.sort_values('Team', ascending=True)
    df = df.sort_values('Exception', ascending=True)
    return df

def exceptions_out_table(df: pd.DataFrame, selected_players: list[str]) -> pd.DataFrame:
    df["Exception"] = (df["Team"].astype(str) + " " + df["Player"].astype(str))
    df = df[df['Exception'].isin(selected_players)]
    df = df.drop(columns=['Exception'])
    df = df.rename(columns={'Player': 'Exception'})
    df = df.rename(columns={"Y" + str(current_year): str(current_year)})
    df[str(current_year)] = df[str(current_year)].apply(lambda x: f"${x:,.0f}")
    df = df.rename(columns={'BirdRights': 'Expiration Date'})
    df = df.drop(columns=['Team'])
    df = df.sort_values('Exception', ascending=True)
    return df

def net_players_check(df: pd.DataFrame, SelectedTeam: str, selected_players_in: list[str], selected_players_out: list[str]) -> float:
    n_in = df[df['Player'].isin(selected_players_in)]
    n_in = n_in[active_roster_mask(n_in)]
    n_in = len(n_in)
    n_out = df[df['Player'].isin(selected_players_out)]
    n_out = n_out[active_roster_mask(n_out)]
    n_out = len(n_out)
    current_players = active_player_n(df, SelectedTeam)
    current_players = current_players-n_out+n_in
    if current_players > 17:
        excess_players = current_players - 17
        st.error(f"Roster exceeds the maximum limit of 17 players. You would need to cut at least {excess_players} player(s) to comply with roster rules.", icon = "❌")
    elif 15 <= current_players <= 17:
        st.warning("Roster is within 15-17 players. Ensure you have sufficient IR-eligible players to maintain compliance and flexibility.", icon = "✅")
    elif 12 <= current_players <= 14:
        st.success(f"Roster size of {current_players} players is within the standard limits. No immediate action required.", icon = "✅")
    elif current_players < 12:
        players_needed = 12 - current_players
        st.warning(f"Roster is below the minimum limit of 12 players. You need to sign at least {players_needed} player(s) to comply with roster requirements.", icon = "✅")
    return current_players

def check_cash_after(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str) -> str:
    team_total = get_tax_total(df, SelectedTeam)
    df1 = df[df['Player'].isin(PlayersIn)]
    df1 = df1["Y" + str(current_year)].sum()
    df2 = df[df['Player'].isin(PlayersOut)]
    df2 = df2["Y" + str(current_year)].sum()
    team_total = team_total - df2 + df1
    if team_total < current_salary_cap:
        return "Cap"
    elif current_salary_cap <= team_total < current_luxury_tax:
        return "Standard"
    elif current_luxury_tax <= team_total < current_apron_1:
        return "Tax"
    elif current_apron_1 <= team_total < current_apron_2:
        return "First"
    else:
        return "Second" #ABC

def no_cash(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame, CashOut: float):
    try:
        CashOut = float(CashOut) 
    except (TypeError, ValueError):
        CashOut = 0.0
    if np.isnan(CashOut):
        CashOut = 0.0
    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
    HardCap = team_hard_cap(base_cap, SelectedTeam)
    if CapType == "Second" and CashOut > 0:
        st.error("This transaction is not permitted. Teams above the Second Apron are prohibited from sending out cash in a trade.", icon="❌")
    elif HardCap in ["First Apron", "No Cap"] and CashOut > 0:
        st.warning("Sending out cash in this trade will hard cap your team at the Second Apron for the remainder of the season. Please proceed with caution.", icon="✅")
    elif CashOut > 0:
        st.success("There are no cap-related restrictions preventing you from sending out cash in this trade.",icon="✅")
    else:
        st.success("No outgoing cash was included in this transaction.",icon="✅")

def tpe_st_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame, SelectedExceptionOut: list[str]):
    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
    HardCap = team_hard_cap(base_cap, SelectedTeam)
    flagged = any("S&T" in exc for exc in SelectedExceptionOut)
    if CapType == "Second" and flagged == 1:
        st.error("This transaction is not permitted. Teams operating above the Second Apron are prohibited from acquiring players via a Traded-Player Exception created from a Sign-And-Trade.", icon="❌")
    elif HardCap in ["First Apron", "No Cap"] and flagged == 1:
        st.warning("This transaction utilizes an outgoing Traded-Player Exception created via a Sign-And-Trade. As a result, your team will be hard-capped at the Second Apron for the remainder of the season.", icon="✅")
    elif flagged == 1:
        st.success("There are no cap-related restrictions preventing your team from using a Traded-Player Exception created from a Sign-And-Trade", icon="✅")
    else: 
        st.success("This transaction does not utilize a Traded-Player Exception created from a Sign-And-Trade to acquire a player.", icon="✅")

#def no_aggregation_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: no_aggregation_check", icon = "⚠️")
#    return "A"

def under_100_percent_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame, SelectedExceptionOut: list[str]):
    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
    HardCap = team_hard_cap(base_cap, SelectedTeam)
    df1 = df[df['Player'].isin(PlayersIn)]
    df1 = df1["Y" + str(current_year)].sum()
    df2 = df[df['Player'].isin(PlayersOut)]
    df2 = df2["Y" + str(current_year)].sum()
    Diff = df1 / df2 if df2 != 0 else 1000
    if len(PlayersIn) == 1 and len(PlayersOut) == 0 and len(SelectedExceptionOut) == 1:
        if "Minimum" in SelectedExceptionOut[0]:
            if df1 < max_minimum:
                Diff = 1.0
    if CapType in ["First", "Second"] and Diff > 1:
        st.error("This transaction is not permitted. Teams above the First Apron are not allowed to take back more than 100% of outgoing salary, unless the incoming player is on a minimum contract.", icon="❌")
    elif HardCap in ["No Cap"] and Diff > 1:
        st.warning("This transaction is allowed, but taking back more than 100% of outgoing salary will hard-cap your team at the First Apron for the remainder of the season.", icon="✅")
    elif Diff > 1:
        st.success("There are no cap-related restrictions preventing your team from taking back more than 100% of outgoing salary.", icon="✅")
    else: 
        st.success("Your team is taking back less than or equal to 100% of outgoing salary. No further action is required.", icon="✅")

def no_bae_mle_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame, SelectedExceptionOuts: list[str]):
    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
    HardCap = team_hard_cap(base_cap, SelectedTeam)
    flagged = any("Bi-Annual" in exc or "Mid-Level" in exc for exc in SelectedExceptionOuts)
    if CapType in ["First", "Second"] and flagged == 1:
        st.error("This transaction is not permitted. Teams operating above the First Apron are prohibited from trading for players via the Bi-Annual Exception (BAE) or Mid-Level Exception (MLE).", icon="❌")
    elif HardCap in ["No Cap"] and flagged == 1:
        st.warning("This transaction utilizes an outgoing Bi-Annual Exception (BAE) or Mid-Level Exception (MLE). As a result, your team will be hard-capped at the First Apron for the remainder of the season.", icon="✅")
    elif flagged == 1:
        st.success("There are no cap-related restrictions preventing your team from using the Bi-Annual Exception (BAE) or Mid-Level Exception (MLE) to acquire a player.",icon="✅")
    else: 
        st.success("This transaction does not utilize the Bi-Annual Exception (BAE) or Mid-Level Exception (MLE) to acquire a player.",icon="✅")

#def salary_trade_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: salary_trade_check", icon = "⚠️")
#    return "A"

#def tpe_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: tpe_check", icon = "⚠️")
#    return "A"

#def bae_mle_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: bae_mle_check", icon = "⚠️")
#    return "A"

#def player_agg_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: player_agg_check", icon = "⚠️")
#    return "A"

#def create_tpe_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: create_tpe_check", icon = "⚠️")
#    return "A"

#def new_trade_rest_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: new_trade_rest_check", icon = "⚠️")
#    return "A"

#def old_team_check(df: pd.DataFrame, PlayersIn: list[str], PlayersOut: list[str], SelectedTeam: str, base_cap: pd.DataFrame):
#    CapType = check_cash_after(df, PlayersIn, PlayersOut, SelectedTeam)
#    HardCap = team_hard_cap(base_cap, SelectedTeam)
#    st.warning("Under Construction: old_team_check", icon = "⚠️")
#    return "A"

def stepien_check(dp: pd.DataFrame, DraftPicksIn: list[str], DraftPicksOut: list[str], SelectedTeam: str):
    return "A"

def _ensure_check_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy() if df is not None else pd.DataFrame()
    for column in columns:
        if column not in df.columns:
            df[column] = pd.NA
    return df

def fantrax_players_check(df: pd.DataFrame, ft_players: pd.DataFrame, ft_roster: pd.DataFrame) -> pd.DataFrame:
    df = _ensure_check_columns(df, ['Player', 'Trade.Restriction']).copy()
    ft_players = _ensure_check_columns(ft_players, ['name', 'fantraxId'])
    ft_roster = _ensure_check_columns(ft_roster, ['id', 'team_name'])
    if ft_players['fantraxId'].dropna().empty or ft_roster['id'].dropna().empty:
        return pd.DataFrame([{
            'Cap Sheet Name': 'Fantrax data unavailable',
            'Fantrax Name': pd.NA,
            'id': pd.NA,
            'team_name': 'Refresh Fantrax data and rerun checks',
        }])
    df['Player'] = df['Player'].replace(cap_sheets_to_fantrax_name_fix)
    df = df[df['Player'] != "Minimum Salary Penalty"]
    df = df[df['Trade.Restriction'] != "Dead"]
    df = df[df['Trade.Restriction'] != "Banned"]
    df = df.merge(ft_players, how='left', left_on='Player', right_on='name')
    df = df.merge(ft_roster, how='outer', left_on='fantraxId', right_on='id')
    df = df[df['Player'].isna() | df['team_name'].isna()]
    df = df.rename(columns={'Player': 'Cap Sheet Name'})
    df = df.rename(columns={'name': 'Fantrax Name'})
    df = df[['Cap Sheet Name', 'Fantrax Name', 'id', 'team_name']]
    return df

def fantrax_roster_check(df: pd.DataFrame, ft_players: pd.DataFrame, ft_roster: pd.DataFrame) -> pd.DataFrame:
    df = _ensure_check_columns(df, ['Player', 'Trade.Restriction', 'Type']).copy()
    ft_players = _ensure_check_columns(ft_players, ['name', 'fantraxId'])
    ft_roster = _ensure_check_columns(ft_roster, ['id', 'team_name', 'status'])
    if ft_players['fantraxId'].dropna().empty or ft_roster['id'].dropna().empty:
        return pd.DataFrame([{
            'Player': 'Fantrax data unavailable',
            'team_name': 'Refresh Fantrax data and rerun checks',
            'Cap Sheet Location': pd.NA,
            'Fantrax Locatoin': pd.NA,
        }])
    df['Player'] = df['Player'].replace(cap_sheets_to_fantrax_name_fix)
    df = df[df['Player'] != "Minimum Salary Penalty"]
    df = df[df['Trade.Restriction'] != "Dead"]
    df = df[df['Trade.Restriction'] != "Banned"]
    df = df.merge(ft_players, how='left', left_on='Player', right_on='name')
    df = df.merge(ft_roster, how='outer', left_on='fantraxId', right_on='id')
    df['status2'] = df['status'].apply(lambda x: "Non-Active Players" if x == "MINORS" else "Active Players")
    df = df[df['Type'] != df["status2"]]
    df = df[['Player', 'team_name', 'Type', 'status']]
    df = df.rename(columns={'Type': 'Cap Sheet Location'})
    df = df.rename(columns={'status': 'Fantrax Locatoin'})
    return df

def fantrax_positional_check(df: pd.DataFrame, ft_players: pd.DataFrame, ft_rosters: pd.DataFrame) -> pd.DataFrame:
    df = get_data()
    df = _ensure_check_columns(df, ['Player', 'Type', 'Team']).copy()
    ft_players = _ensure_check_columns(ft_players, ['name', 'fantraxId'])
    ft_rosters = _ensure_check_columns(ft_rosters, ['id', 'position', 'status'])
    if ft_players['fantraxId'].dropna().empty or ft_rosters['id'].dropna().empty:
        return pd.DataFrame([{
            'Team': 'Fantrax data unavailable',
            'Type': 'Refresh Fantrax data and rerun checks',
        }])
    df_players = pd.DataFrame({
        "Team": list(team_info.keys()),
        "Active Players": [active_player_n(df, team) for team in team_info.keys()],})
    df['Player'] = df['Player'].replace(cap_sheets_to_fantrax_name_fix)
    df = df[df['Type'] == "Active Players"]
    df = df.merge(ft_players, how='left', left_on='Player', right_on='name')
    df = df.merge(ft_rosters, how='outer', left_on='fantraxId', right_on='id')

    df_ir = df[df['status'] == "INJURED_RESERVE"]
    df_ir = df_ir.groupby(['Team']).size().reset_index(name='Total')
    df_ir = df_ir.merge(df_players, how='left', left_on='Team', right_on='Team')
    df_ir['Count'] = df_ir['Active Players'] - df_ir['Total']
    df_ir = df_ir[df_ir['Count'] > 14]
    df_ir['Type'] = "IR"
    df_ir = df_ir[['Team', 'Type']]

    df_starters = df[df['status'] == "ACTIVE"]
    df_starters = df_starters[df_starters['position'].isin(['PG', 'SG', 'SF', 'PF', 'C'])]
    df_starters = df_starters.groupby(['Team','position']).size().reset_index(name='Total')
    df_starters = df_starters[df_starters['Total'] > 1]
    df_starters['Type'] = "Starters"
    df_starters = df_starters[['Team', 'Type']]

    df_flex = df[df['status'] == "ACTIVE"]
    df_flex = df_flex[df_flex['position'] == "Flx"]
    df_flex = df_flex.groupby(['Team']).size().reset_index(name='Total')
    df_flex = df_flex[df_flex['Total'] > 3]
    df_flex['Type'] = "Flex"
    df_flex = df_flex[['Team', 'Type']]

    df_reserve = df[df['status'] == "RESERVE"]
    df_reserve = df_reserve.groupby(['Team']).size().reset_index(name='Total')
    df_reserve = df_reserve[df_reserve['Total'] > 6]
    df_reserve['Type'] = "Reserve"
    df_reserve = df_reserve[['Team', 'Type']]

    df = pd.concat([df_ir, df_starters, df_flex, df_reserve], ignore_index=True)
    return df

def current_draft(df: pd.DataFrame, dp: pd.DataFrame, round: str) -> pd.DataFrame:
    required_standings = {"Year", "Period", "Record", "Team"}
    required_picks = {"Year", "Round", "OGTeam", "CurrentTeam", "Explanation"}
    if not required_standings.issubset(df.columns) or not required_picks.issubset(dp.columns):
        return pd.DataFrame(columns=["Pick", "Slot", "Team", "Explanation", "Time Due (ET)"])
    df = df[(df['Year'] == current_year) & (df['Period'] == 99)]
    if df.empty:
        return pd.DataFrame(columns=["Pick", "Slot", "Team", "Explanation", "Time Due (ET)"])
    df[['Wins', 'Losses']] = df['Record'].str.split('-', expand=True).astype(int)
    df['winPercentage'] = df['Wins'] / (df['Wins'] + df['Losses'])    
    df = df[['Team', 'winPercentage']]
    dp = dp[dp['Year'] == current_year].copy()
    dp = dp[dp['Round'] == round].copy()
    order_col = "CurrentTeam"
    dp["_DraftOrderTeam"] = dp[order_col].astype(str).str.split(",").str[0].str.strip()
    dp = dp.merge(df, how = 'left', left_on = '_DraftOrderTeam', right_on = 'Team')
    dp = dp.sort_values('winPercentage', ascending=True)
    pick_start = 1 if round == "1st Round" else 31
    dp['Pick'] = range(pick_start, pick_start + dp.shape[0])
    draft_times = ["10:30 AM", "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM","1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM", "5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM", "8:00 PM", "8:30 PM", "9:00 PM", "9:30 PM", "10:00 PM", "10:30 PM", "11:00 PM", "11:30 PM", "12:00 AM", "12:30 AM", "1:00 AM"]
    dp["Time Due (ET)"] = [draft_times[i % len(draft_times)] for i in range(dp.shape[0])]
    dp = dp[['Pick', '_DraftOrderTeam', 'CurrentTeam', 'Explanation', 'Time Due (ET)']]
    dp = dp.rename(columns={'_DraftOrderTeam': 'OGTeam'})
    dp = dp.rename(columns={'OGTeam': 'Slot'})
    dp = dp.rename(columns={'CurrentTeam': 'Team'})
    return dp

def past_draft(df: pd.DataFrame, pics: pd.DataFrame, dh: pd.DataFrame, year: float, round: float) -> pd.DataFrame:
    dh = dh[dh['Year'] == year]
    dh = dh[dh['Round'] == round]
    df = df[df["Type" + str(current_year)] != "Dead"]
    dh = dh.merge(df[['Player', 'Team']], on='Player', how='left')
    dh = dh.merge(pics[['Player', 'Picture_Online']], on='Player', how='left')
    dh = dh.drop(columns=["Year",'Round'])
    dh["Drafted Team Name"] = dh["Team_x"]
    dh["Current Team Name"] = dh["Team_y"]
    dh["Drafted Team"] = dh["Team_x"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    dh["Current Team"] = dh["Team_y"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    dh = dh[['Pick', 'Drafted Team Name', 'Drafted Team', 'Player', 'Picture_Online', 'Current Team Name', 'Current Team']]
    return dh

def lottery_table(standings: pd.DataFrame) -> pd.DataFrame:
    for city, info in team_info.items():
        standings.loc[standings["Team"].str.startswith(city), "conference"] = info["conf"]
    standings = standings[(standings['Year'] == current_year) & (standings['Period'] == 99)]
    standings[['Wins', 'Losses']] = standings['Record'].str.split('-', expand=True).astype(int)
    standings['winPercentage'] = standings['Wins'] / (standings['Wins'] + standings['Losses'])    
    standings = standings[['Team', 'winPercentage','conference']]
    standings["Conf_Rank"] = (standings.groupby("conference")["winPercentage"].rank(method="first", ascending=False).astype(int))
    standings = standings[standings['Conf_Rank'] >= 9]
    standings = standings.sort_values("winPercentage", ascending=True)
    items = list(range(1, 15)) 
    combos = list(combinations(items, 4))
    df = pd.DataFrame(combos, columns=["Lowest Ball", "Lower Ball", "Higher Ball", "Highest Ball"])
    df["Ownership"] = np.concatenate([
        #np.repeat(standings["Team"].iloc[0], 140),
        np.repeat("El Paso", 140),
        np.repeat("Little Rock", 140),
        np.repeat("Tulsa (Top 3), Else El Paso", 140),
        np.repeat("Tulsa 2", 115),
        np.repeat("Austin", 115),
        np.repeat("Nashville", 83),
        np.repeat("Manchester", 82),
        np.repeat("San Jose", 60),
        np.repeat("Jacksonville", 45),
        np.repeat("Vegas", 30),
        np.repeat("Birmingham", 20),
        np.repeat("Buffalo", 15),
        np.repeat("Albuquerque", 10),
        np.repeat("Des Moines", 5),
        np.repeat("Redraw", 1)])
    return df

def format_live_stats_df(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if col == 'Team':
            continue
        if col in ['TS%', '2PT%', '3PT%', 'FT%']:
            df.iloc[0, df.columns.get_loc(col)] = f"{float(df.iloc[0][col]) * 100:.2f}"
        elif col == 'MP':
            minutes = float(df.iloc[0][col])
            mins = int(minutes)
            secs = int((minutes - mins) * 60)
            df.iloc[0, df.columns.get_loc(col)] = f"{mins}:{secs:02d}"
        elif col == '+/-':
            val = float(df.iloc[0][col])
            df.iloc[0, df.columns.get_loc(col)] = f"{val:+.1f}"
        else: 
            df.iloc[0, df.columns.get_loc(col)] = f"{float(df.iloc[0][col]):.0f}"
    return df

def team_with_ranks(df: pd.DataFrame, SelectedTeam: str, SelectedYear: int, SelectedPeriod: int) -> pd.DataFrame:
    # --- Select numeric stat columns ---
    stat_cols = df.select_dtypes("number").columns.tolist()
    if SelectedYear <= 2025 and 'GP' in stat_cols:
        stat_cols.remove('GP')

    # --- Get team row safely ---
    team_row = df[df["Team"] == SelectedTeam]
    if team_row.empty:
        raise ValueError(f"Team '{SelectedTeam}' not found in dataframe.")

    team_idx = team_row.index[0]

    # --- Compute ranks (numeric) ---
    ranks = df[stat_cols].rank(ascending=False, method="min")

    # Keep numeric ranks for logic
    team_ranks = ranks.loc[team_idx].copy()

    # Create separate display version (strings)
    team_ranks_display = pd.Series(index=team_ranks.index, dtype="object")

    # --- Build rank strings ---
    for col in team_ranks.index:
        rank_val = int(team_ranks[col])
        is_tied = (ranks[col] == rank_val).sum() > 1

        # ordinal suffix
        if 11 <= rank_val % 100 <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(rank_val % 10, 'th')

        rank_str = f"{rank_val}{suffix}"
        team_ranks_display[col] = f"T-{rank_str}" if is_tied else rank_str

    # --- Combine stats + ranks ---
    out = pd.concat(
        [team_row[stat_cols].reset_index(drop=True),
         team_ranks_display.to_frame().T],
        ignore_index=True
    )

    # --- Add team column (logos) ---
    out.insert(0, "Team", [SelectedTeam, None])
    out["Team"] = out["Team"].map(lambda t: team_info.get(t, {}).get("logo", "") if t else "")

    return out

def team_stats_line_chart(df: pd.DataFrame, SelectedTeam: str, SelectedCategory: str, SelectedYear: int, SelectedMatchup: int) -> alt.Chart:
    df_year = df[df["Year"] == SelectedYear]
    df_year = df_year[df_year["MP"] != 0]
    league_median = (df_year
        .groupby("Period", as_index=False)[SelectedCategory]
        .median()
        .assign(Series="League Median"))
    team_series = (df_year[df_year["Team"] == SelectedTeam]
        .loc[:, ["Period", SelectedCategory]]
        .assign(Series=SelectedTeam))    
    plot_df = pd.concat([league_median, team_series], ignore_index=True)
    chart = (alt.Chart(plot_df)
        .mark_line(strokeWidth=2.5, interpolate='monotone')
        .encode(x=alt.X("Period:O", title="Period", axis=alt.Axis(labelAngle=0, labelFontSize=11, titleFontSize=12, titlePadding=10, grid=False)),
                y=alt.Y(f"{SelectedCategory}:Q", title=SelectedCategory, scale=alt.Scale(zero=False),
                axis=alt.Axis(labelFontSize=11, titleFontSize=12, titlePadding=10, gridOpacity=0.3)),
                color=alt.Color("Series:N", scale=alt.Scale(domain=["League Median", SelectedTeam], range=["#8B8B8B", "#3B82F6"]),
                legend=alt.Legend(title=None, orient="top", labelFontSize=11, symbolSize=100, symbolStrokeWidth=2.5)),
                tooltip=[alt.Tooltip("Series:N", title=""), alt.Tooltip("Period:O", title="Period"), alt.Tooltip(f"{SelectedCategory}:Q", title=SelectedCategory, format=".1f")])
        .properties(height=450))
    team_points = (alt.Chart(team_series)
        .mark_circle(size=80, opacity=1)
        .encode(x="Period:O", y=f"{SelectedCategory}:Q", color=alt.value("#3B82F6"), tooltip=[alt.Tooltip("Period:O", title="Period"), alt.Tooltip(f"{SelectedCategory}:Q", title=SelectedCategory, format=".1f")]))
    return (chart + team_points).configure_view(strokeWidth=0).configure_axis(domainColor="#E5E7EB", tickColor="#E5E7EB")

def matchup_scoreboard(df: pd.DataFrame, SelectedTeam: str, SelectedYear: int, SelectedPeriod: int, Opponent: str) -> pd.DataFrame:
    team1 = team_with_ranks(df, SelectedTeam, SelectedYear, SelectedPeriod)
    team2 = team_with_ranks(df, Opponent, SelectedYear, SelectedPeriod)
    for col in team1.columns:
        if col == 'Team':
            continue
        if col in ['TS%', '2PT%', '3PT%', 'FT%']:
            # Multiply by 100 and format
            team1.iloc[0, team1.columns.get_loc(col)] = f"{float(team1.iloc[0][col]) * 100:.2f}"
            team2.iloc[0, team2.columns.get_loc(col)] = f"{float(team2.iloc[0][col]) * 100:.2f}"
        elif col == 'MP':
            minutes1 = float(team1.iloc[0][col])
            mins1 = int(minutes1)
            secs1 = int((minutes1 - mins1) * 60)
            team1.iloc[0, team1.columns.get_loc(col)] = f"{mins1}:{secs1:02d}"
            minutes2 = float(team2.iloc[0][col])
            mins2 = int(minutes2)
            secs2 = int((minutes2 - mins2) * 60)
            team2.iloc[0, team2.columns.get_loc(col)] = f"{mins2}:{secs2:02d}"
        elif col == '+/-':
            val1 = float(team1.iloc[0][col])
            val2 = float(team2.iloc[0][col])
            team1.iloc[0, team1.columns.get_loc(col)] = f"{val1:+.1f}"
            team2.iloc[0, team2.columns.get_loc(col)] = f"{val2:+.1f}"
        else: 
            team1.iloc[0, team1.columns.get_loc(col)] = f"{float(team1.iloc[0][col]):.0f}"
            team2.iloc[0, team2.columns.get_loc(col)] = f"{float(team2.iloc[0][col]):.0f}"
    team1_scores = team1.iloc[0]
    team2_scores = team2.iloc[0]
    scores = pd.concat([team1_scores, team2_scores], axis=1).T
    green = '#6B9B6B'
    yellow = '#D4B963'
    red = '#CC8888'
    def get_color(col, reverse=False):
        val1 = scores.iloc[0][col]
        val2 = scores.iloc[1][col]
        if col == 'MP':
            def mp_to_float(v):
                mins, secs = v.split(':')
                return int(mins) + int(secs) / 60
            n1, n2 = mp_to_float(val1), mp_to_float(val2)
        else:
            n1, n2 = float(val1), float(val2)
        if n1 > n2:
            return green if not reverse else red
        elif n1 == n2:
            return yellow
        else:
            return red if not reverse else green    
    Color1 = get_color('MP')
    Color2 = get_color('TS%')
    Color3 = get_color('2PT%')
    Color4 = get_color('3PT%')
    Color5 = get_color('FT%')
    Color6 = get_color('PTS')
    Color7 = get_color('OREB')
    Color8 = get_color('DREB')
    Color9 = get_color('AST')
    Color10 = get_color('ST')
    Color11 = get_color('BLK')
    Color12 = get_color('+/-')
    Color13 = get_color('TO', reverse=True)
    def style_matchup(row):
        styles = [""] * len(row)
        color_map = {'MP': Color1, 'TS%': Color2, '2PT%': Color3, '3PT%': Color4, 'FT%': Color5, 'PTS': Color6, 'OREB': Color7, 'DREB': Color8, 'AST': Color9, 'ST': Color10, 'BLK': Color11, '+/-': Color12, 'TO': Color13}
        for i, col in enumerate(row.index):
            if col in color_map:
                styles[i] = f"background-color: {color_map[col]};"
        return styles
    styled_team2 = team2.style.apply(style_matchup, axis=1)
    return styled_team2

def get_opponents(df: pd.DataFrame, SelectedTeam: str, SelectedYear: int, SelectedPeriod: int, Type: str) -> list:    
    filtered = df[(df["Type"] == Type) & (df["Year"] == SelectedYear) & (df["Period"] == SelectedPeriod)].copy()
    filtered = filtered[(filtered["TeamA"].str.contains(SelectedTeam)) | (filtered["TeamB"].str.contains(SelectedTeam))]
    opponents = []
    for _, row in filtered.iterrows():
        if SelectedTeam in row["TeamA"]:
            opponents.append(row["TeamB"])
        else:
            opponents.append(row["TeamA"])
    return opponents

def get_transactions(df: pd.DataFrame, SelectedTeam: str) -> pd.DataFrame:
    team_df = df[df["team_name"].str.startswith(SelectedTeam, na=False)].copy()
    time_periods = df[['Year', 'period']].drop_duplicates().sort_values(['Year', 'period'])
    time_periods['time_seq'] = range(len(time_periods))
    team_df = team_df.merge(time_periods, on=['Year', 'period'], how='left')
    team_df = team_df.sort_values(['id', 'time_seq'])
    team_df['prev_time_seq'] = team_df.groupby('id')['time_seq'].shift(1)
    team_df['time_gap'] = team_df['time_seq'] - team_df['prev_time_seq']
    team_df['transaction_type'] = None
    team_df.loc[team_df['prev_time_seq'].isna(), 'transaction_type'] = 'joined' 
    team_df.loc[team_df['time_gap'] > 1, 'transaction_type'] = 'joined'
    team_df['next_time_seq'] = team_df.groupby('id')['time_seq'].shift(-1)
    team_df['next_gap'] = team_df['next_time_seq'] - team_df['time_seq']
    team_df.loc[team_df['next_time_seq'].isna(), 'transaction_type'] = 'left'
    team_df.loc[team_df['next_gap'] > 1, 'transaction_type'] = 'left'
    team_df = team_df[team_df['transaction_type'].notna()][['id', 'team_name', 'period', 'Year', 'transaction_type']]
    return team_df

def send_discord_message(DISCORD_WEBHOOK_URL: str, message: str):
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()


def post_fantrax_webhook(
    webhook_url: str,
    message: str = "This is working",
    image_bytes: bytes | None = None,
    image_filename: str = "sbcfbl-live-scores.png",
) -> int:
    """Post a chat message without leaking the secret webhook URL in errors."""
    parsed_url = urlparse(str(webhook_url).strip())
    if parsed_url.scheme != "https" or not parsed_url.netloc or parsed_url.username or parsed_url.password:
        raise ValueError("Enter a valid HTTPS webhook URL.")

    try:
        if image_bytes:
            response = requests.post(
                parsed_url.geturl(),
                data={"payload_json": json.dumps({"content": str(message)})},
                files={"files[0]": (image_filename, image_bytes, "image/png")},
                timeout=30,
            )
        else:
            response = requests.post(
                parsed_url.geturl(),
                json={"content": str(message)},
                timeout=15,
            )
        response.raise_for_status()
    except requests.RequestException as exc:
        status_code = getattr(exc.response, "status_code", None)
        if status_code is not None:
            raise RuntimeError(f"The webhook returned HTTP {status_code}.") from None
        raise RuntimeError("The webhook could not be reached.") from None
    return response.status_code


def matchup_period_progress(period_calendar: pd.DataFrame, year: int, period: int, as_of=None) -> float:
    """Return the share of matchup calendar days completed, from 0 through 100."""
    required = {"Year", "Period", "Date"}
    if period_calendar is None or period_calendar.empty or not required.issubset(period_calendar.columns):
        return 0.0
    calendar = period_calendar.copy()
    dates = pd.to_datetime(
        calendar.loc[
            (pd.to_numeric(calendar["Year"], errors="coerce") == int(year))
            & (pd.to_numeric(calendar["Period"], errors="coerce") == int(period)),
            "Date",
        ],
        errors="coerce",
    ).dropna()
    if dates.empty:
        return 0.0
    current_date = pd.Timestamp(as_of if as_of is not None else today).normalize()
    start_date = dates.min().normalize()
    end_date = dates.max().normalize()
    if current_date < start_date:
        return 0.0
    if current_date > end_date:
        return 100.0
    total_days = max(1, (end_date - start_date).days + 1)
    completed_days = (current_date - start_date).days + 1
    return round(max(0.0, min(100.0, completed_days / total_days * 100.0)), 1)


@lru_cache(maxsize=32)
def _scoreboard_font(size: int, bold: bool = False):
    font_properties = font_manager.FontProperties(family="DejaVu Sans", weight="bold" if bold else "normal")
    return ImageFont.truetype(font_manager.findfont(font_properties), size=size)


def _fit_scoreboard_font(draw, text: str, max_width: int, start_size: int = 24, minimum_size: int = 14):
    size = start_size
    while size > minimum_size:
        font = _scoreboard_font(size, True)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
        size -= 1
    return _scoreboard_font(minimum_size, True)


_SCOREBOARD_LOGO_CACHE: dict[str, bytes | None] = {}


def _scoreboard_logo_bytes(source: str) -> bytes | None:
    source = str(source or "").strip()
    if not source:
        return None
    if source in _SCOREBOARD_LOGO_CACHE:
        return _SCOREBOARD_LOGO_CACHE[source]
    try:
        if source.startswith(("http://", "https://")):
            response = requests.get(
                source,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SBCFBL/1.0)"},
                timeout=10,
            )
            response.raise_for_status()
            content = response.content
        else:
            content = Path(source).read_bytes()
    except (OSError, requests.RequestException):
        content = None
    # Keep successful downloads hot, but allow a transient CDN failure to retry.
    if content is not None:
        _SCOREBOARD_LOGO_CACHE[source] = content
    return content


def _scoreboard_logo_image(content: bytes | None, size: int):
    if not content:
        return None
    try:
        logo = Image.open(BytesIO(content)).convert("RGBA")
        logo.thumbnail((size, size), Image.Resampling.LANCZOS)
        return logo
    except (OSError, ValueError):
        return None


def _scoreboard_color(value, fallback="#64748b"):
    try:
        return ImageColor.getrgb(str(value))
    except (TypeError, ValueError):
        return ImageColor.getrgb(fallback)


def _scoreboard_team_name(team_key: str) -> str:
    nickname = str(safe_team_info(team_key, "nickname", "") or "").strip()
    return " ".join(part for part in [str(team_key).strip(), nickname] if part)


def _scoreboard_team_label(team_key: str) -> str:
    """Return the compact identity used in dense score lists."""
    nickname = str(safe_team_info(team_key, "nickname", "") or "").strip()
    return nickname or str(team_key).strip()


def _scoreboard_record(value) -> str:
    text = str(value or "").strip()
    return text if text and text.casefold() not in {"nan", "none"} else "—"


def _scoreboard_score(value) -> str:
    try:
        if pd.isna(value):
            return "—"
        number = float(value)
        return f"{int(number)}" if number.is_integer() else f"{number:.1f}"
    except (TypeError, ValueError):
        return str(value or "—")


def _scoreboard_score_number(value) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def build_live_scoreboard_image(
    scores_df: pd.DataFrame,
    progress_percent: float,
    season_label: str,
    period_label: str,
    generated_at=None,
) -> bytes:
    """Render an overnight, two-column league scoreboard as a webhook-ready PNG."""
    if scores_df is None or scores_df.empty:
        raise ValueError("No current matchups are available to render.")

    rows = scores_df.copy()
    if "Type" not in rows.columns:
        rows["Type"] = "Regular Season"
    rows["_game_type"] = rows["Type"].astype(str).replace({"nan": "Other", "": "Other"})
    rows["_home_sort"] = rows["TeamB"].apply(lambda team: _scoreboard_team_name(str(team)).casefold())
    rows["_conference"] = rows.apply(
        lambda row: str(
            safe_team_info(
                str(row.get("TeamB", "")),
                "conf",
                safe_team_info(str(row.get("TeamA", "")), "conf", ""),
            )
        ),
        axis=1,
    )
    preferred_types = ["Regular Season", "In-Season Tournament", "Play-In", "Playoffs"]
    available_types = rows["_game_type"].drop_duplicates().tolist()
    section_types = [value for value in preferred_types if value in available_types]
    section_types.extend(sorted(value for value in available_types if value not in preferred_types))
    sections = [
        (game_type, rows[rows["_game_type"] == game_type].sort_values("_home_sort").reset_index(drop=True))
        for game_type in section_types
    ]

    width = 2000
    outer_margin = 44
    column_gap = 24
    card_width = (width - outer_margin * 2 - column_gap) // 2
    regular_column_gap = 18
    regular_card_width = (width - outer_margin * 2 - regular_column_gap * 2) // 3
    header_height = 150
    section_header_height = 54
    row_height = 86
    regular_row_height = 112
    section_gap = 14
    footer_height = 46
    def section_display_rows(game_type, section_rows):
        if game_type == "Regular Season":
            return math.ceil(len(section_rows) / 3)
        west_count = int((section_rows["_conference"] == "West").sum())
        east_count = int((section_rows["_conference"] == "East").sum())
        return max(west_count, east_count, 1)

    content_height = sum(
        section_header_height
        + section_display_rows(game_type, section_rows) * (regular_row_height if game_type == "Regular Season" else row_height)
        + section_gap
        for game_type, section_rows in sections
    )
    height = header_height + content_height + footer_height
    image = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)

    # Quiet overnight-report header on a white canvas.
    for y in range(header_height):
        blend = y / max(1, header_height - 1)
        color = tuple(int(a + (b - a) * blend) for a, b in zip((248, 251, 255), (255, 255, 255)))
        draw.line((0, y, width, y), fill=color)
    draw.rounded_rectangle((outer_margin, 34, outer_margin + 58, 92), radius=14, fill="#f59e0b")
    draw.text((outer_margin + 29, 63), "S", font=_scoreboard_font(32, True), fill="#172033", anchor="mm")
    draw.text((outer_margin + 78, 50), "SBCFBL OVERNIGHT SCORES", font=_scoreboard_font(38, True), fill="#172033", anchor="lm")
    generated_timestamp = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now())
    scores_through = generated_timestamp.strftime("%A, %B %d").replace(" 0", " ")
    draw.text(
        (outer_margin + 78, 96),
        f"{period_label.upper()}  •  SCORES THROUGH {scores_through.upper()}",
        font=_scoreboard_font(19, True),
        fill="#5f7185",
        anchor="lm",
    )
    draw.rounded_rectangle((width - 246, 44, width - outer_margin, 86), radius=21, fill="#172033")
    draw.text((width - 145, 65), f"{len(rows)} GAMES", font=_scoreboard_font(20, True), fill="#ffffff", anchor="mm")
    draw.line((outer_margin, header_height - 1, width - outer_margin, header_height - 1), fill="#d9e2ec", width=2)

    logo_sources = set()
    for _, row in rows.iterrows():
        for side in ("A", "B"):
            team_key = str(row.get(f"Team{side}", ""))
            logo_sources.add(str(row.get(f"Team{side}_logo", safe_team_info(team_key, "logo", "")) or ""))
    logo_sources.discard("")
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(logo_sources)))) as pool:
        list(pool.map(_scoreboard_logo_bytes, logo_sources))

    progress = max(0.0, min(100.0, float(progress_percent)))

    def draw_matchup_card(row, card_left, card_top):
        card_right = card_left + card_width
        card_bottom = card_top + row_height - 8
        center_y = (card_top + card_bottom) // 2
        draw.rounded_rectangle((card_left, card_top, card_right, card_bottom), radius=12, fill="#f8fafc", outline="#d9e2ec", width=2)

        team_a = str(row.get("TeamA", ""))
        team_b = str(row.get("TeamB", ""))
        name_a = _scoreboard_team_label(team_a)
        name_b = _scoreboard_team_label(team_b)
        color_a = _scoreboard_color(row.get("TeamA_color", safe_team_info(team_a, "bg", "#64748b")))
        color_b = _scoreboard_color(row.get("TeamB_color", safe_team_info(team_b, "bg", "#64748b")))
        draw.rounded_rectangle((card_left, card_top, card_left + 7, card_bottom), radius=4, fill=color_a)
        draw.rounded_rectangle((card_right - 7, card_top, card_right, card_bottom), radius=4, fill=color_b)

        left_logo_x = card_left + 38
        right_logo_x = card_right - 38
        for side, team, logo_x, fallback_color in (
            ("A", team_a, left_logo_x, color_a),
            ("B", team_b, right_logo_x, color_b),
        ):
            source = str(row.get(f"Team{side}_logo", safe_team_info(team, "logo", "")) or "")
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(source), 44)
            if logo is not None:
                image.paste(logo, (logo_x - logo.width // 2, center_y - logo.height // 2), logo)
            else:
                draw.ellipse((logo_x - 20, center_y - 20, logo_x + 20, center_y + 20), fill=fallback_color)
                draw.text((logo_x, center_y), team[:2].upper(), font=_scoreboard_font(13, True), fill="#ffffff", anchor="mm")

        name_y = center_y - 10
        record_y = center_y + 20
        draw.text((card_left + 69, name_y), name_a, font=_fit_scoreboard_font(draw, name_a, 180, 25, 15), fill="#172033", anchor="lm")
        draw.text((card_right - 69, name_y), name_b, font=_fit_scoreboard_font(draw, name_b, 180, 25, 15), fill="#172033", anchor="rm")
        draw.text((card_left + 69, record_y), _scoreboard_record(row.get("TeamA_record")), font=_scoreboard_font(15, True), fill="#687b90", anchor="lm")
        draw.text((card_right - 69, record_y), _scoreboard_record(row.get("TeamB_record")), font=_scoreboard_font(15, True), fill="#687b90", anchor="rm")

        score_a = _scoreboard_score(row.get("TeamA_Score", row.get("TeamAScore")))
        score_b = _scoreboard_score(row.get("TeamB_Score", row.get("TeamBScore")))
        score_font = _scoreboard_font(30, True)
        score_a_position = (card_left + 370, center_y)
        score_b_position = (card_left + 575, center_y)
        draw.text(score_a_position, score_a, font=score_font, fill="#172033", anchor="rm")
        draw.text(score_b_position, score_b, font=score_font, fill="#172033", anchor="lm")
        score_a_number = _scoreboard_score_number(row.get("TeamA_Score", row.get("TeamAScore")))
        score_b_number = _scoreboard_score_number(row.get("TeamB_Score", row.get("TeamBScore")))
        if score_a_number is not None and score_b_number is not None and score_a_number != score_b_number:
            winning_side = "A" if score_a_number > score_b_number else "B"
            winning_text = score_a if winning_side == "A" else score_b
            winning_position = score_a_position if winning_side == "A" else score_b_position
            winning_anchor = "rm" if winning_side == "A" else "lm"
            winning_color = color_a if winning_side == "A" else color_b
            score_bounds = draw.textbbox(winning_position, winning_text, font=score_font, anchor=winning_anchor)
            underline_y = score_bounds[3] + 6
            draw.line((score_bounds[0], underline_y, score_bounds[2], underline_y), fill=winning_color, width=3)

        bar_left = card_left + 395
        bar_right = card_left + 550
        bar_width = bar_right - bar_left
        bar_top, bar_bottom = center_y - 15, center_y + 15
        if progress >= 100.0:
            draw.rounded_rectangle((bar_left, bar_top, bar_right, bar_bottom), radius=15, fill="#172033")
            draw.text(((bar_left + bar_right) // 2, center_y), "FINAL", font=_scoreboard_font(16, True), fill="#ffffff", anchor="mm")
        else:
            draw.rounded_rectangle((bar_left, bar_top, bar_right, bar_bottom), radius=9, fill="#dfe7ef", outline="#cbd6e2", width=1)
            fill_width = int(bar_width * progress / 100.0)
            if fill_width > 0:
                fill_right = min(bar_right, bar_left + fill_width)
                draw.rounded_rectangle((bar_left, bar_top, fill_right, bar_bottom), radius=9, fill=color_a)
                for x in range(max(0, fill_width - 8)):
                    blend = x / max(1, bar_width - 1)
                    color = tuple(int(a + (b - a) * blend) for a, b in zip(color_a, color_b))
                    draw.line((bar_left + 4 + x, bar_top + 2, bar_left + 4 + x, bar_bottom - 2), fill=color)
            draw.text(((bar_left + bar_right) // 2, center_y), f"{progress:.0f}%", font=_scoreboard_font(14, True), fill="#ffffff", anchor="mm", stroke_width=2, stroke_fill="#172033")

    def draw_regular_matchup_card(row, card_left, card_top):
        card_right = card_left + regular_card_width
        card_bottom = card_top + regular_row_height - 8
        team_a, team_b = str(row.get("TeamA", "")), str(row.get("TeamB", ""))
        name_a, name_b = _scoreboard_team_label(team_a), _scoreboard_team_label(team_b)
        color_a = _scoreboard_color(row.get("TeamA_color", safe_team_info(team_a, "bg", "#64748b")))
        color_b = _scoreboard_color(row.get("TeamB_color", safe_team_info(team_b, "bg", "#64748b")))
        draw.rounded_rectangle((card_left, card_top, card_right, card_bottom), radius=12, fill="#f8fafc", outline="#d9e2ec", width=2)
        draw.rounded_rectangle((card_left, card_top, card_left + 7, card_bottom), radius=4, fill=color_a)
        draw.rounded_rectangle((card_right - 7, card_top, card_right, card_bottom), radius=4, fill=color_b)

        identity_y = card_top + 32
        for side, team, logo_x, fallback_color in (
            ("A", team_a, card_left + 36, color_a),
            ("B", team_b, card_right - 36, color_b),
        ):
            source = str(row.get(f"Team{side}_logo", safe_team_info(team, "logo", "")) or "")
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(source), 44)
            if logo is not None:
                image.paste(logo, (logo_x - logo.width // 2, identity_y - logo.height // 2), logo)
            else:
                draw.ellipse((logo_x - 20, identity_y - 20, logo_x + 20, identity_y + 20), fill=fallback_color)
                draw.text((logo_x, identity_y), team[:2].upper(), font=_scoreboard_font(12, True), fill="#ffffff", anchor="mm")

        draw.text((card_left + 66, card_top + 25), name_a, font=_fit_scoreboard_font(draw, name_a, 180, 21, 14), fill="#172033", anchor="lm")
        draw.text((card_right - 66, card_top + 25), name_b, font=_fit_scoreboard_font(draw, name_b, 180, 21, 14), fill="#172033", anchor="rm")
        draw.text((card_left + 66, card_top + 52), _scoreboard_record(row.get("TeamA_record")), font=_scoreboard_font(13, True), fill="#687b90", anchor="lm")
        draw.text((card_right - 66, card_top + 52), _scoreboard_record(row.get("TeamB_record")), font=_scoreboard_font(13, True), fill="#687b90", anchor="rm")

        score_y = card_top + 81
        card_mid = (card_left + card_right) // 2
        score_font = _scoreboard_font(27, True)
        score_a = _scoreboard_score(row.get("TeamA_Score", row.get("TeamAScore")))
        score_b = _scoreboard_score(row.get("TeamB_Score", row.get("TeamBScore")))
        score_a_pos, score_b_pos = (card_mid - 78, score_y), (card_mid + 78, score_y)
        draw.text(score_a_pos, score_a, font=score_font, fill="#172033", anchor="rm")
        draw.text(score_b_pos, score_b, font=score_font, fill="#172033", anchor="lm")
        number_a = _scoreboard_score_number(row.get("TeamA_Score", row.get("TeamAScore")))
        number_b = _scoreboard_score_number(row.get("TeamB_Score", row.get("TeamBScore")))
        if number_a is not None and number_b is not None and number_a != number_b:
            winner_text, winner_pos, winner_anchor, winner_color = (
                (score_a, score_a_pos, "rm", color_a) if number_a > number_b else (score_b, score_b_pos, "lm", color_b)
            )
            bounds = draw.textbbox(winner_pos, winner_text, font=score_font, anchor=winner_anchor)
            draw.line((bounds[0], bounds[3] + 5, bounds[2], bounds[3] + 5), fill=winner_color, width=3)
        if progress >= 100:
            draw.rounded_rectangle((card_mid - 54, score_y - 16, card_mid + 54, score_y + 16), radius=16, fill="#172033")
            draw.text((card_mid, score_y), "FINAL", font=_scoreboard_font(13, True), fill="#ffffff", anchor="mm")
        else:
            draw.rounded_rectangle((card_mid - 54, score_y - 16, card_mid + 54, score_y + 16), radius=16, fill="#dfe7ef")
            draw.text((card_mid, score_y), f"{progress:.0f}%", font=_scoreboard_font(13, True), fill="#172033", anchor="mm")

    y_cursor = header_height
    for game_type, section_rows in sections:
        draw.rectangle((outer_margin, y_cursor + 10, width - outer_margin, y_cursor + section_header_height - 4), fill="#eef3f8")
        draw.rounded_rectangle((outer_margin, y_cursor + 10, outer_margin + 9, y_cursor + section_header_height - 4), radius=4, fill="#f59e0b")
        draw.text((outer_margin + 26, y_cursor + 30), game_type.upper(), font=_scoreboard_font(20, True), fill="#172033", anchor="lm")
        count_label = f"{len(section_rows)} GAME{'S' if len(section_rows) != 1 else ''}"
        draw.text((width - outer_margin - 18, y_cursor + 30), count_label, font=_scoreboard_font(14, True), fill="#607286", anchor="rm")
        y_cursor += section_header_height
        if game_type == "Regular Season":
            chunk_size = math.ceil(len(section_rows) / 3)
            column_rows = [
                section_rows.iloc[index * chunk_size:(index + 1) * chunk_size].reset_index(drop=True)
                for index in range(3)
            ]
            for row_index in range(max((len(values) for values in column_rows), default=0)):
                for column_index, values in enumerate(column_rows):
                    if row_index < len(values):
                        card_left = outer_margin + column_index * (regular_card_width + regular_column_gap)
                        draw_regular_matchup_card(values.iloc[row_index], card_left, y_cursor)
                y_cursor += regular_row_height
        else:
            left_rows = section_rows[section_rows["_conference"] == "West"].sort_values("_home_sort").reset_index(drop=True)
            right_rows = section_rows[section_rows["_conference"] == "East"].sort_values("_home_sort").reset_index(drop=True)
            for row_index in range(max(len(left_rows), len(right_rows))):
                if row_index < len(left_rows):
                    draw_matchup_card(left_rows.iloc[row_index], outer_margin, y_cursor)
                if row_index < len(right_rows):
                    draw_matchup_card(right_rows.iloc[row_index], outer_margin + card_width + column_gap, y_cursor)
                y_cursor += row_height
        y_cursor += section_gap

    generated = generated_timestamp.strftime("%b %d, %Y • %I:%M %p").replace(" 0", " ")
    draw.line((outer_margin, height - footer_height, width - outer_margin, height - footer_height), fill="#d9e2ec", width=1)
    draw.text((outer_margin, height - 21), f"UPDATED {generated}", font=_scoreboard_font(15, True), fill="#6d7f92", anchor="lm")
    draw.text((width - outer_margin, height - 21), "13-CATEGORY SCORING", font=_scoreboard_font(15, True), fill="#6d7f92", anchor="rm")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def build_mobile_live_scoreboard_image(
    scores_df: pd.DataFrame,
    progress_percent: float,
    season_label: str,
    period_label: str,
    generated_at=None,
) -> bytes:
    """Render a tall, single-column overnight scoreboard for mobile viewing."""
    if scores_df is None or scores_df.empty:
        raise ValueError("No current matchups are available to render.")

    rows = scores_df.copy()
    if "Type" not in rows.columns:
        rows["Type"] = "Regular Season"
    rows["_game_type"] = rows["Type"].astype(str).replace({"nan": "Other", "": "Other"})
    rows["_home_sort"] = rows["TeamB"].apply(lambda team: _scoreboard_team_name(str(team)).casefold())
    rows["_conference"] = rows.apply(
        lambda row: str(safe_team_info(str(row.get("TeamB", "")), "conf", safe_team_info(str(row.get("TeamA", "")), "conf", ""))),
        axis=1,
    )
    preferred_types = ["Regular Season", "In-Season Tournament", "Play-In", "Playoffs"]
    available_types = rows["_game_type"].drop_duplicates().tolist()
    section_types = [value for value in preferred_types if value in available_types]
    section_types.extend(sorted(value for value in available_types if value not in preferred_types))
    sections = []
    for game_type in section_types:
        section_rows = rows[rows["_game_type"] == game_type].copy()
        if game_type == "Regular Season":
            section_rows = section_rows.sort_values("_home_sort")
        else:
            section_rows["_conference_sort"] = section_rows["_conference"].map({"West": 0, "East": 1}).fillna(2)
            section_rows = section_rows.sort_values(["_conference_sort", "_home_sort"])
        sections.append((game_type, section_rows.reset_index(drop=True)))

    width = 1080
    margin = 24
    column_gap = 14
    mobile_card_width = (width - margin * 2 - column_gap) // 2
    header_height = 150
    section_header_height = 56
    row_height = 124
    section_gap = 14
    footer_height = 52
    def mobile_section_rows(game_type, section_rows):
        if game_type == "Regular Season":
            return math.ceil(len(section_rows) / 2)
        west_count = int((section_rows["_conference"] == "West").sum())
        east_count = int((section_rows["_conference"] == "East").sum())
        return max(west_count, east_count, 1)
    height = header_height + footer_height + sum(
        section_header_height + mobile_section_rows(game_type, section_rows) * row_height + section_gap
        for game_type, section_rows in sections
    )
    image = Image.new("RGB", (width, height), "#f4f7fb")
    draw = ImageDraw.Draw(image)
    navy, orange = "#172033", "#f59e0b"

    draw.rectangle((0, 0, width, header_height), fill="#ffffff")
    draw.rounded_rectangle((margin, 24, margin + 64, 88), radius=15, fill=orange)
    draw.text((margin + 32, 56), "S", font=_scoreboard_font(34, True), fill=navy, anchor="mm")
    draw.text((margin + 88, 52), "OVERNIGHT SCORES", font=_scoreboard_font(40, True), fill=navy, anchor="lm")
    generated_timestamp = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now())
    scores_through = generated_timestamp.strftime("%b %d").replace(" 0", " ").upper()
    draw.text((margin + 88, 105), f"{period_label.upper()}  •  THROUGH {scores_through}", font=_scoreboard_font(19, True), fill="#65778a", anchor="lm")
    draw.rounded_rectangle((width - 216, 32, width - margin, 80), radius=24, fill=navy)
    draw.text((width - 123, 56), f"{len(rows)} GAMES", font=_scoreboard_font(18, True), fill="#ffffff", anchor="mm")

    logo_sources = set()
    for _, row in rows.iterrows():
        for side in ("A", "B"):
            team = str(row.get(f"Team{side}", ""))
            logo_sources.add(str(row.get(f"Team{side}_logo", safe_team_info(team, "logo", "")) or ""))
    logo_sources.discard("")
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(logo_sources)))) as pool:
        list(pool.map(_scoreboard_logo_bytes, logo_sources))

    progress = max(0.0, min(100.0, float(progress_percent)))

    def paste_team_logo(row, side, team, center, fallback_color):
        source = str(row.get(f"Team{side}_logo", safe_team_info(team, "logo", "")) or "")
        logo = _scoreboard_logo_image(_scoreboard_logo_bytes(source), 60)
        if logo is not None:
            image.paste(logo, (center[0] - logo.width // 2, center[1] - logo.height // 2), logo)
        else:
            draw.ellipse((center[0] - 27, center[1] - 27, center[0] + 27, center[1] + 27), fill=fallback_color)
            draw.text(center, team[:2].upper(), font=_scoreboard_font(15, True), fill="#ffffff", anchor="mm")

    def draw_mobile_matchup(row, top, left):
        right, bottom = left + mobile_card_width, top + row_height - 8
        center_y = (top + bottom) // 2
        team_a, team_b = str(row.get("TeamA", "")), str(row.get("TeamB", ""))
        color_a = _scoreboard_color(row.get("TeamA_color", safe_team_info(team_a, "bg", "#64748b")))
        color_b = _scoreboard_color(row.get("TeamB_color", safe_team_info(team_b, "bg", "#64748b")))
        draw.rounded_rectangle((left, top, right, bottom), radius=18, fill="#ffffff", outline="#d8e2ec", width=2)
        draw.rounded_rectangle((left, top, left + 12, bottom), radius=6, fill=color_a)
        draw.rounded_rectangle((right - 12, top, right, bottom), radius=6, fill=color_b)
        paste_team_logo(row, "A", team_a, (left + 52, center_y), color_a)
        paste_team_logo(row, "B", team_b, (right - 52, center_y), color_b)

        score_a = _scoreboard_score(row.get("TeamA_Score", row.get("TeamAScore")))
        score_b = _scoreboard_score(row.get("TeamB_Score", row.get("TeamBScore")))
        score_font = _scoreboard_font(38, True)
        score_a_pos, score_b_pos = (left + 210, center_y), (right - 210, center_y)
        draw.text(score_a_pos, score_a, font=score_font, fill=navy, anchor="rm")
        draw.text(score_b_pos, score_b, font=score_font, fill=navy, anchor="lm")
        number_a = _scoreboard_score_number(row.get("TeamA_Score", row.get("TeamAScore")))
        number_b = _scoreboard_score_number(row.get("TeamB_Score", row.get("TeamBScore")))
        if number_a is not None and number_b is not None and number_a != number_b:
            winner_text, winner_pos, winner_anchor, winner_color = (
                (score_a, score_a_pos, "rm", color_a) if number_a > number_b else (score_b, score_b_pos, "lm", color_b)
            )
            bounds = draw.textbbox(winner_pos, winner_text, font=score_font, anchor=winner_anchor)
            draw.line((bounds[0], bounds[3] + 6, bounds[2], bounds[3] + 6), fill=winner_color, width=5)

        card_mid = (left + right) // 2
        pill_left, pill_right = card_mid - 31, card_mid + 31
        pill_top, pill_bottom = center_y - 26, center_y + 26
        if progress >= 100:
            draw.rounded_rectangle((pill_left, pill_top, pill_right, pill_bottom), radius=20, fill=navy)
            draw.text((card_mid, center_y), "F", font=_scoreboard_font(25, True), fill="#ffffff", anchor="mm")
        else:
            draw.rounded_rectangle((pill_left, pill_top, pill_right, pill_bottom), radius=20, fill="#dfe7ef")
            fill_right = pill_left + int((pill_right - pill_left) * progress / 100)
            if fill_right > pill_left:
                draw.rounded_rectangle((pill_left, pill_top, max(pill_left + 16, fill_right), pill_bottom), radius=20, fill=color_a)
            draw.text((card_mid, center_y), f"{progress:.0f}%", font=_scoreboard_font(14, True), fill="#ffffff", stroke_width=2, stroke_fill=navy, anchor="mm")

    cursor = header_height
    for game_type, section_rows in sections:
        draw.rectangle((margin, cursor + 8, width - margin, cursor + section_header_height - 4), fill="#e9eff5")
        draw.rounded_rectangle((margin, cursor + 8, margin + 8, cursor + section_header_height - 4), radius=4, fill=orange)
        draw.text((margin + 24, cursor + 30), game_type.upper(), font=_scoreboard_font(19, True), fill=navy, anchor="lm")
        draw.text((width - margin - 14, cursor + 30), f"{len(section_rows)} GAMES", font=_scoreboard_font(16, True), fill="#718398", anchor="rm")
        cursor += section_header_height
        if game_type == "Regular Season":
            split = math.ceil(len(section_rows) / 2)
            left_rows = section_rows.iloc[:split].reset_index(drop=True)
            right_rows = section_rows.iloc[split:].reset_index(drop=True)
        else:
            left_rows = section_rows[section_rows["_conference"] == "West"].reset_index(drop=True)
            right_rows = section_rows[section_rows["_conference"] == "East"].reset_index(drop=True)
        for row_index in range(max(len(left_rows), len(right_rows))):
            if row_index < len(left_rows):
                draw_mobile_matchup(left_rows.iloc[row_index], cursor, margin)
            if row_index < len(right_rows):
                draw_mobile_matchup(right_rows.iloc[row_index], cursor, margin + mobile_card_width + column_gap)
            cursor += row_height
        cursor += section_gap

    generated = generated_timestamp.strftime("%b %d  \u2022  %I:%M %p").replace(" 0", " ")
    draw.text((margin, height - 24), f"UPDATED {generated}", font=_scoreboard_font(15, True), fill="#718398", anchor="lm")
    draw.text((width - margin, height - 24), "13-CATEGORY SCORING", font=_scoreboard_font(15, True), fill="#718398", anchor="rm")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _paste_scoreboard_asset(canvas, content: bytes | None, box, padding=0):
    if not content:
        return False
    try:
        asset = Image.open(BytesIO(content)).convert("RGBA")
        left, top, right, bottom = box
        asset.thumbnail((max(1, right - left - padding * 2), max(1, bottom - top - padding * 2)), Image.Resampling.LANCZOS)
        x = left + (right - left - asset.width) // 2
        y = top + (bottom - top - asset.height) // 2
        canvas.paste(asset, (x, y), asset)
        return True
    except (OSError, ValueError):
        return False


def _recap_stat_text(value, stat, attempts=None):
    if stat in {"TS%", "2PT%", "3PT%", "FT%"} and attempts is not None:
        try:
            if float(attempts) == 0:
                return "—"
        except (TypeError, ValueError):
            pass
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    if stat in {"TS%", "2PT%", "3PT%", "FT%"}:
        return f"{number * 100:.1f}%"
    if stat == "MP":
        return f"{number:.0f}"
    if stat == "+/-":
        return f"{number:+.0f}"
    return f"{number:.0f}" if number.is_integer() else f"{number:.1f}"


def _recap_contrast_text(color) -> str:
    """Return readable dark or light text for a team-colored background."""
    rgb = color if isinstance(color, tuple) else _scoreboard_color(color)
    luminance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    return "#172033" if luminance >= 145 else "#ffffff"


def _recap_tint(color, white_mix=0.68):
    """Blend a team color toward white for a readable tie-state highlight."""
    rgb = color if isinstance(color, tuple) else _scoreboard_color(color)
    return tuple(round(channel * (1 - white_mix) + 255 * white_mix) for channel in rgb)


def build_matchup_recap_image(
    matchup_row,
    category_table: pd.DataFrame,
    aggregate_players: pd.DataFrame,
    trend_table: pd.DataFrame | None = None,
    court_image: bytes | None = None,
    road_jersey_image: bytes | None = None,
    home_jersey_image: bytes | None = None,
    road_edition: str = "Road",
    home_edition: str = "Home",
    generated_at=None,
    matchup_date_label: str = "",
    events_table: pd.DataFrame | None = None,
) -> bytes:
    """Build a single-page matchup recap from the app's existing box-score assets."""
    row = matchup_row.to_dict() if hasattr(matchup_row, "to_dict") else dict(matchup_row)
    team_a = str(row.get("TeamA", ""))
    team_b = str(row.get("TeamB", ""))
    name_a = _scoreboard_team_name(team_a)
    name_b = _scoreboard_team_name(team_b)
    color_a = _scoreboard_color(row.get("TeamA_color", safe_team_info(team_a, "bg", "#334155")))
    color_b = _scoreboard_color(row.get("TeamB_color", safe_team_info(team_b, "bg", "#64748b")))
    score_a = _scoreboard_score(row.get("TeamA_Score", row.get("TeamAScore")))
    score_b = _scoreboard_score(row.get("TeamB_Score", row.get("TeamBScore")))
    score_a_number = _scoreboard_score_number(row.get("TeamA_Score", row.get("TeamAScore")))
    score_b_number = _scoreboard_score_number(row.get("TeamB_Score", row.get("TeamBScore")))

    player_counts = []
    if aggregate_players is not None and not aggregate_players.empty and "sbc_team" in aggregate_players.columns:
        player_teams = aggregate_players["sbc_team"].astype(str)
        player_counts = [int((player_teams == team).sum()) for team in (team_a, team_b)]
    visible_player_rows = min(15, max(player_counts, default=0))
    table_height = max(300, 142 + visible_player_rows * 48)

    width = 3600
    margin = 48
    category_top = 352
    category_height = 216
    box_top = category_top + category_height + 48
    table_top = box_top + 46
    lower_title_top = table_top + table_height + 48
    lower_box_top = lower_title_top + 42
    lower_box_bottom = lower_box_top + 600
    height = lower_box_bottom + 76
    image = Image.new("RGB", (width, height), "#f4f7fb")
    draw = ImageDraw.Draw(image)

    # Matchup masthead.
    draw.rounded_rectangle((margin, 34, width - margin, 292), radius=24, fill="#ffffff", outline="#dbe4ee", width=2)
    draw.rectangle((margin, 34, margin + 14, 292), fill=color_a)
    draw.rectangle((width - margin - 14, 34, width - margin, 292), fill=color_b)
    draw.text((width // 2, 70), "SBCFBL MATCHUP RECAP", font=_scoreboard_font(30, True), fill="#607286", anchor="mm")
    draw.text((width // 2, 162), f"{score_a}  —  {score_b}", font=_scoreboard_font(78, True), fill="#172033", anchor="mm")
    draw.rounded_rectangle((width // 2 - 72, 216, width // 2 + 72, 258), radius=21, fill="#111111")
    draw.text((width // 2, 237), "FINAL", font=_scoreboard_font(17, True), fill="#ffffff", anchor="mm")

    for team, name, logo_x, name_x, anchor, color in (
        (team_a, name_a, margin + 112, margin + 205, "lm", color_a),
        (team_b, name_b, width - margin - 112, width - margin - 205, "rm", color_b),
    ):
        logo_source = str(safe_team_info(team, "logo", "") or "")
        logo = _scoreboard_logo_image(_scoreboard_logo_bytes(logo_source), 118)
        if logo is not None:
            image.paste(logo, (logo_x - logo.width // 2, 160 - logo.height // 2), logo)
        else:
            draw.ellipse((logo_x - 52, 108, logo_x + 52, 212), fill=color)
        draw.text((name_x, 148), name, font=_fit_scoreboard_font(draw, name, 720, 40, 24), fill="#172033", anchor=anchor)
        record_key = "TeamA_record" if team == team_a else "TeamB_record"
        record = str(row.get(record_key, "") or "")
        if record:
            draw.text((name_x, 203), record, font=_scoreboard_font(21, True), fill="#74869a", anchor=anchor)

    subtitle = " • ".join(
        value for value in [str(row.get("Type", "")), str(row.get("Round", "")), str(matchup_date_label)] if value
    )
    draw.text((width // 2, 280), subtitle, font=_scoreboard_font(18, True), fill="#74869a", anchor="mm")

    # Horizontal 13-category scoreboard.
    section_top = 318
    draw.text((margin, section_top), "13-CATEGORY SCOREBOARD", font=_scoreboard_font(30, True), fill="#172033", anchor="la")
    inner_width = width - margin * 2
    category_width = inner_width / 13
    category_lookup = category_table.set_index("Category") if category_table is not None and not category_table.empty else pd.DataFrame()
    category_order = ["MP", "TS%", "2PT%", "3PT%", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
    category_points = {"MP": 11, "TS%": 41, "2PT%": 31, "3PT%": 31, "FT%": 21, "PTS": 61, "OREB": 31, "DREB": 31, "AST": 41, "ST": 31, "BLK": 31, "TO": 21, "+/-": 31}
    shooting_columns = ["GP", "2PTM", "2PTA", "3PTM", "3PTA", "FTM", "FTA"]
    shooting_totals = pd.DataFrame()
    if aggregate_players is not None and not aggregate_players.empty and "sbc_team" in aggregate_players.columns:
        shooting_source = aggregate_players.copy()
        for column in shooting_columns:
            source_values = shooting_source[column] if column in shooting_source.columns else pd.Series(0, index=shooting_source.index)
            shooting_source[column] = pd.to_numeric(source_values, errors="coerce").fillna(0)
        shooting_totals = shooting_source.groupby("sbc_team")[shooting_columns].sum()
    shooting_pair = {"2PT%": ("2PTM", "2PTA"), "3PT%": ("3PTM", "3PTA"), "FT%": ("FTM", "FTA")}

    def percentage_attempts(source, stat):
        def numeric(column):
            try:
                return float(source.get(column, 0) or 0)
            except (TypeError, ValueError):
                return 0.0

        if stat in shooting_pair:
            return numeric(shooting_pair[stat][1])
        if stat == "TS%":
            return numeric("2PTA") + numeric("3PTA") + 0.44 * numeric("FTA")
        return None

    def category_value_text(team, stat, value):
        if stat not in {"TS%", *shooting_pair} or shooting_totals.empty or team not in shooting_totals.index:
            return _recap_stat_text(value, stat)
        return _recap_stat_text(value, stat, percentage_attempts(shooting_totals.loc[team], stat))

    def attempts_text(team, stat):
        if stat not in shooting_pair or shooting_totals.empty or team not in shooting_totals.index:
            return ""
        made_column, attempt_column = shooting_pair[stat]
        made = _recap_stat_text(shooting_totals.loc[team, made_column], made_column)
        attempted = _recap_stat_text(shooting_totals.loc[team, attempt_column], attempt_column)
        return f"{made} / {attempted}"

    def category_subtext(team, stat):
        if stat == "MP" and not shooting_totals.empty and team in shooting_totals.index:
            return f"{_recap_stat_text(shooting_totals.loc[team, 'GP'], 'GP')} GP"
        return attempts_text(team, stat)

    for index, stat in enumerate(category_order):
        left = int(margin + index * category_width)
        right = int(margin + (index + 1) * category_width - 6)
        value_a = value_b = None
        winner = ""
        votes = category_points.get(stat, "")
        if not category_lookup.empty and stat in category_lookup.index:
            category_row = category_lookup.loc[stat]
            value_a = category_row.get(team_a)
            value_b = category_row.get(team_b)
            winner = str(category_row.get("Winner", ""))
            votes = category_row.get("Votes", votes)
        is_tie = winner.casefold() == "tie"
        draw.rounded_rectangle(
            (left, category_top, right, category_top + category_height),
            radius=13,
            fill="#edf1f5" if is_tie else "#ffffff",
            outline="#94a3b8" if is_tie else "#dbe4ee",
            width=3 if is_tie else 2,
        )
        if winner == team_a:
            draw.rounded_rectangle((left + 6, category_top + 6, right - 6, category_top + 68), radius=10, fill=color_a)
        if winner == team_b:
            draw.rounded_rectangle((left + 6, category_top + 148, right - 6, category_top + 210), radius=10, fill=color_b)
        if is_tie:
            tie_color_a = _recap_tint(color_a)
            tie_color_b = _recap_tint(color_b)
            draw.rounded_rectangle((left + 6, category_top + 6, right - 6, category_top + 68), radius=10, fill=tie_color_a)
            draw.rounded_rectangle((left + 6, category_top + 148, right - 6, category_top + 210), radius=10, fill=tie_color_b)
        has_subtext = stat == "MP" or stat in shooting_pair
        draw.text(((left + right) // 2, category_top + (27 if has_subtext else 38)), category_value_text(team_a, stat, value_a), font=_scoreboard_font(27, True), fill=_recap_contrast_text(color_a) if winner == team_a else "#172033", anchor="mm")
        if has_subtext:
            subtext_color_a = _recap_contrast_text(color_a) if winner == team_a else "#42546a"
            draw.text(((left + right) // 2, category_top + 55), category_subtext(team_a, stat), font=_scoreboard_font(17, True), fill=subtext_color_a, anchor="mm")
        display_stat = {"2PT%": "2P%", "3PT%": "3P%", "ST": "STL", "TO": "TOV*"}.get(stat, stat)
        votes_text = _recap_stat_text(votes, "Votes") if votes != "" else ""
        center_label = f"{display_stat} ({votes_text})" if votes_text else display_stat
        draw.text(((left + right) // 2, category_top + (96 if is_tie else 108)), center_label, font=_scoreboard_font(21, True), fill="#52667b", anchor="mm")
        if is_tie:
            draw.text(((left + right) // 2, category_top + 122), "TIE", font=_scoreboard_font(15, True), fill="#475569", anchor="mm")
        draw.text(((left + right) // 2, category_top + (162 if has_subtext else 179)), category_value_text(team_b, stat, value_b), font=_scoreboard_font(27, True), fill=_recap_contrast_text(color_b) if winner == team_b else "#172033", anchor="mm")
        if has_subtext:
            subtext_color_b = _recap_contrast_text(color_b) if winner == team_b else "#42546a"
            draw.text(((left + right) // 2, category_top + 196), category_subtext(team_b, stat), font=_scoreboard_font(17, True), fill=subtext_color_b, anchor="mm")

    # Aggregate player box score, one team per half.
    draw.text((margin, box_top), "AGGREGATE PLAYER BOX SCORE", font=_scoreboard_font(30, True), fill="#172033", anchor="la")
    table_gap = 30
    table_width = (inner_width - table_gap) // 2
    player_columns = [
        ("Player", 280), ("GP", 68), ("MP", 68), ("TS%", 68),
        ("2PTM", 68), ("2PTA", 68), ("2PT%", 68),
        ("3PTM", 68), ("3PTA", 68), ("3PT%", 68),
        ("FTM", 68), ("FTA", 68), ("FT%", 68), ("PTS", 68),
        ("OREB", 68), ("DREB", 68), ("AST", 68), ("ST", 68),
        ("BLK", 68), ("TO", 68), ("+/-", 68),
    ]
    for team_index, (team, color) in enumerate(((team_a, color_a), (team_b, color_b))):
        left = margin + team_index * (table_width + table_gap)
        right = left + table_width
        draw.rounded_rectangle((left, table_top, right, table_top + table_height), radius=16, fill="#ffffff", outline="#dbe4ee", width=2)
        draw.rounded_rectangle((left, table_top, right, table_top + 64), radius=16, fill=color)
        draw.rectangle((left, table_top + 46, right, table_top + 64), fill=color)
        draw.text((left + 22, table_top + 33), _scoreboard_team_name(team), font=_fit_scoreboard_font(draw, _scoreboard_team_name(team), table_width - 44, 27, 18), fill=_recap_contrast_text(color), anchor="lm")
        header_y = table_top + 96
        x_cursor = left + 18
        for label, column_width in player_columns:
            display_label = {
                "MP": "MP", "TS%": "TS%", "2PTM": "2PM", "2PTA": "2PA", "2PT%": "2P%",
                "3PTM": "3PM", "3PTA": "3PA", "3PT%": "3P%", "FTM": "FTM", "FTA": "FTA",
                "FT%": "FT%", "OREB": "OREB", "DREB": "DREB", "ST": "STL", "TO": "TOV",
            }.get(label, label)
            anchor = "lm" if label == "Player" else "mm"
            x_position = x_cursor + (0 if label == "Player" else column_width // 2)
            draw.text((x_position, header_y), display_label, font=_scoreboard_font(17, True), fill="#52667b", anchor=anchor)
            x_cursor += column_width
        team_players = aggregate_players[aggregate_players.get("sbc_team", pd.Series(dtype=str)).astype(str) == team].copy() if aggregate_players is not None and not aggregate_players.empty else pd.DataFrame()
        if not team_players.empty:
            team_players = team_players.sort_values(["PTS", "display_player"], ascending=[False, True]).head(15)
        row_y = table_top + 130
        row_height = 48
        for player_index, (_, player) in enumerate(team_players.iterrows()):
            if player_index % 2 == 0:
                draw.rectangle((left + 7, row_y - 21, right - 7, row_y + 23), fill="#f2f6fa")
            x_cursor = left + 18
            for label, column_width in player_columns:
                value = player.get("display_player", "") if label == "Player" else _recap_stat_text(
                    player.get(label),
                    label,
                    percentage_attempts(player, label),
                )
                if label == "Player":
                    font = _fit_scoreboard_font(draw, str(value), column_width - 12, 20, 14)
                    draw.text((x_cursor, row_y), str(value), font=font, fill="#172033", anchor="lm")
                else:
                    draw.text((x_cursor + column_width // 2, row_y), str(value), font=_scoreboard_font(18, True), fill="#172033", anchor="mm")
                x_cursor += column_width
            row_y += row_height

    # Uniforms/home floor and score movement share one landscape row.
    presentation_left, presentation_right = margin, 1900
    trend_left, trend_right = 1924, width - margin
    draw.text((presentation_left, lower_title_top), "GAME PRESENTATION", font=_scoreboard_font(28, True), fill="#172033", anchor="la")
    draw.text((trend_left, lower_title_top), "OVERALL MATCHUP SCORE BY DAY", font=_scoreboard_font(28, True), fill="#172033", anchor="la")
    visuals_box_top, visuals_box_bottom = lower_box_top, lower_box_bottom
    draw.rounded_rectangle((presentation_left, visuals_box_top, presentation_right, visuals_box_bottom), radius=18, fill="#ffffff", outline="#dbe4ee", width=2)
    _paste_scoreboard_asset(image, road_jersey_image, (presentation_left + 20, visuals_box_top + 14, presentation_left + 455, visuals_box_bottom - 62), padding=6)
    _paste_scoreboard_asset(image, court_image, (presentation_left + 465, visuals_box_top + 18, presentation_right - 465, visuals_box_bottom - 62), padding=4)
    _paste_scoreboard_asset(image, home_jersey_image, (presentation_right - 455, visuals_box_top + 14, presentation_right - 20, visuals_box_bottom - 62), padding=6)
    draw.text((presentation_left + 238, visuals_box_bottom - 30), f"{name_a} • {road_edition}", font=_scoreboard_font(19, True), fill="#52667b", anchor="mm")
    draw.text(((presentation_left + presentation_right) // 2, visuals_box_bottom - 30), f"SHOT MAP • {name_b.upper()} HOME FLOOR", font=_scoreboard_font(19, True), fill="#52667b", anchor="mm")
    draw.text((presentation_right - 238, visuals_box_bottom - 30), f"{name_b} • {home_edition}", font=_scoreboard_font(19, True), fill="#52667b", anchor="mm")

    # Day-separated overall score timeline, matching the interactive box score.
    chart_left, chart_top = trend_left, lower_box_top
    chart_right, chart_bottom = trend_right, lower_box_bottom
    draw.rounded_rectangle((chart_left, chart_top, chart_right, chart_bottom), radius=16, fill="#ffffff", outline="#dbe4ee", width=2)
    draw.rectangle((chart_left + 28, chart_top + 18, chart_left + 54, chart_top + 44), fill=_recap_tint(color_a, 0.45))
    draw.text((chart_left + 66, chart_top + 31), name_a, font=_scoreboard_font(20, True), fill="#42546a", anchor="lm")
    draw.rectangle((chart_right - 54, chart_top + 18, chart_right - 28, chart_top + 44), fill=_recap_tint(color_b, 0.45))
    draw.text((chart_right - 66, chart_top + 31), name_b, font=_scoreboard_font(20, True), fill="#42546a", anchor="rm")
    plot_left, plot_top = chart_left + 70, chart_top + 58
    plot_right, plot_bottom = chart_right - 28, chart_bottom - 48
    if trend_table is not None and not trend_table.empty and team_a in trend_table.columns and team_b in trend_table.columns:
        trend = trend_table.copy().reset_index(drop=True)
        trend[team_a] = pd.to_numeric(trend[team_a], errors="coerce")
        trend[team_b] = pd.to_numeric(trend[team_b], errors="coerce")
        trend = trend.dropna(subset=[team_a, team_b])
        if "game_date" in trend.columns:
            trend["_day"] = pd.to_datetime(trend["game_date"].astype(str), format="%Y%m%d", errors="coerce")
        else:
            trend["_day"] = pd.NaT
        wallclock = pd.to_datetime(trend.get("wallclock", pd.Series(pd.NaT, index=trend.index)), errors="coerce", utc=True)
        trend["_day"] = trend["_day"].fillna(wallclock.dt.tz_localize(None).dt.normalize())
        if trend["_day"].isna().all():
            trend["_day"] = pd.date_range("2000-01-01", periods=len(trend), freq="D")
        else:
            trend["_day"] = trend["_day"].ffill().bfill()
        fallback_times = pd.to_datetime(trend["_day"], errors="coerce", utc=True) + pd.Timedelta(hours=20)
        trend["_wallclock"] = wallclock.fillna(pd.Series(fallback_times, index=trend.index))
        if score_a_number is not None and score_b_number is not None and not trend.empty:
            trend.loc[trend.index[-1], [team_a, team_b]] = [score_a_number, score_b_number]
        trend = trend.sort_values("_wallclock").reset_index(drop=True)

        game_counts = {}
        if events_table is not None and not events_table.empty:
            event_days = pd.to_datetime(events_table.get("game_date", pd.Series(dtype=str)).astype(str), format="%Y%m%d", errors="coerce")
            events_for_counts = events_table.copy()
            events_for_counts["_day"] = event_days
            if "game_id" in events_for_counts.columns:
                game_counts = events_for_counts.dropna(subset=["_day"]).groupby("_day")["game_id"].nunique().to_dict()

        days = list(pd.Series(trend["_day"].dropna().unique()).sort_values())
        panel_gap = 12
        panel_width = int((plot_right - plot_left - panel_gap * max(0, len(days) - 1)) / max(1, len(days)))
        header_height = 42
        graph_top = plot_top + header_height
        graph_bottom = plot_bottom - 40
        score_max = 413.0
        score_mid = score_max / 2
        top_fill = _recap_tint(color_a, 0.72)
        bottom_fill = _recap_tint(color_b, 0.72)

        def score_y(value):
            score = max(0.0, min(score_max, float(value)))
            return int(graph_bottom - score / score_max * (graph_bottom - graph_top))

        prior_score = score_mid
        tick_hours = [16, 18, 20, 22, 24, 25] if len(days) <= 4 else [16, 20, 24]
        for day_index, day in enumerate(days):
            panel_left = plot_left + day_index * (panel_width + panel_gap)
            panel_right = panel_left + panel_width
            day_value = pd.Timestamp(day)
            count = int(game_counts.get(day_value, 0))
            count_text = f" ({count} {'game' if count == 1 else 'games'})" if count else ""
            day_label = day_value.strftime("%a, %b %d").replace(" 0", " ") + count_text
            draw.text(((panel_left + panel_right) // 2, plot_top + 17), day_label, font=_fit_scoreboard_font(draw, day_label, panel_width - 8, 16, 12), fill="#344054", anchor="mm")

            day_rows = trend[trend["_day"] == day].copy().sort_values("_wallclock")
            timeline = [(16.0, prior_score)]
            for _, trend_row in day_rows.iterrows():
                eastern = pd.Timestamp(trend_row["_wallclock"]).tz_convert("America/New_York")
                chart_hour = eastern.hour + eastern.minute / 60 + eastern.second / 3600
                if chart_hour < 4:
                    chart_hour += 24
                timeline.append((max(16.0, min(25.0, chart_hour)), float(trend_row[team_b])))
            prior_score = timeline[-1][1]
            timeline.append((25.0, prior_score))

            def hour_x(hour):
                return int(panel_left + (hour - 16) / 9 * panel_width)

            for (hour_a, value_a), (hour_b, _) in zip(timeline, timeline[1:]):
                x1, x2 = hour_x(hour_a), hour_x(hour_b)
                y = score_y(value_a)
                draw.rectangle((x1, graph_top, x2, y), fill=top_fill)
                draw.rectangle((x1, y, x2, graph_bottom), fill=bottom_fill)

            for score_tick in [0, 113, score_mid, 300, score_max]:
                y = score_y(score_tick)
                draw.line((panel_left, y, panel_right, y), fill="#98a6b7" if score_tick == score_mid else "#d7e0e9", width=2 if score_tick == score_mid else 1)
            for hour in tick_hours:
                x = hour_x(hour)
                draw.line((x, graph_top, x, graph_bottom), fill="#d7e0e9", width=1)
                label_hour = 12 if hour == 24 else 1 if hour == 25 else hour - 12
                draw.text((x, graph_bottom + 18), f"{label_hour}:00", font=_scoreboard_font(13, True), fill="#607286", anchor="mm")
            draw.rectangle((panel_left, graph_top, panel_right, graph_bottom), outline="#344054", width=2)

            for (hour_a, value_a), (hour_b, value_b) in zip(timeline, timeline[1:]):
                x1, x2 = hour_x(hour_a), hour_x(hour_b)
                y1, y2 = score_y(value_a), score_y(value_b)
                draw.line((x1, y1, x2, y1), fill="#111827", width=4)
                draw.line((x2, y1, x2, y2), fill="#111827", width=4)

            if day_index == 0:
                axis_labels = [(score_max, "0"), (300, "300"), (score_mid, "206.5"), (113, "300"), (0, "0")]
                for score_tick, axis_label in axis_labels:
                    draw.text((panel_left - 12, score_y(score_tick)), axis_label, font=_scoreboard_font(13, True), fill="#475467", anchor="rm")
            draw.text(((panel_left + panel_right) // 2, plot_bottom - 4), "TIME (ET)", font=_scoreboard_font(14, True), fill="#607286", anchor="mm")
    else:
        draw.text(((chart_left + chart_right) // 2, (plot_top + plot_bottom) // 2), "Score movement data is unavailable for this matchup.", font=_scoreboard_font(21, True), fill="#8293a6", anchor="mm")

    generated = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now()).strftime("%b %d, %Y • %I:%M %p").replace(" 0", " ")
    draw.text((margin, height - 30), f"MATCHUP RECAP • GENERATED {generated}", font=_scoreboard_font(16, True), fill="#718398", anchor="lm")
    draw.text((width - margin, height - 30), "SBCFBL CATEGORY SCORING", font=_scoreboard_font(16, True), fill="#718398", anchor="rm")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def build_mobile_matchup_recap_image(
    matchup_row,
    category_table: pd.DataFrame,
    aggregate_players: pd.DataFrame,
    trend_table: pd.DataFrame | None = None,
    court_image: bytes | None = None,
    road_jersey_image: bytes | None = None,
    home_jersey_image: bytes | None = None,
    road_edition: str = "Road",
    home_edition: str = "Home",
    generated_at=None,
    matchup_date_label: str = "",
) -> bytes:
    """Build a phone-first matchup recap with readable, stacked detail sections."""
    row = matchup_row.to_dict() if hasattr(matchup_row, "to_dict") else dict(matchup_row)
    team_a, team_b = str(row.get("TeamA", "")), str(row.get("TeamB", ""))
    name_a = str(safe_team_info(team_a, "nickname", _scoreboard_team_name(team_a)) or _scoreboard_team_name(team_a))
    name_b = str(safe_team_info(team_b, "nickname", _scoreboard_team_name(team_b)) or _scoreboard_team_name(team_b))
    color_a = _scoreboard_color(row.get("TeamA_color", safe_team_info(team_a, "bg", "#334155")))
    color_b = _scoreboard_color(row.get("TeamB_color", safe_team_info(team_b, "bg", "#64748b")))
    score_a = _scoreboard_score(row.get("TeamA_Score", row.get("TeamAScore")))
    score_b = _scoreboard_score(row.get("TeamB_Score", row.get("TeamBScore")))
    score_a_number = _scoreboard_score_number(row.get("TeamA_Score", row.get("TeamAScore")))
    score_b_number = _scoreboard_score_number(row.get("TeamB_Score", row.get("TeamBScore")))
    width, margin, navy = 1080, 28, "#172033"

    def roster_for(team):
        if aggregate_players is None or aggregate_players.empty or "sbc_team" not in aggregate_players.columns:
            return pd.DataFrame()
        players = aggregate_players[aggregate_players["sbc_team"].astype(str) == team].copy()
        if players.empty:
            return players
        players["PTS"] = pd.to_numeric(players.get("PTS"), errors="coerce").fillna(0)
        return players.sort_values(["PTS", "display_player"], ascending=[False, True]).head(12)

    rosters = {team_a: roster_for(team_a), team_b: roster_for(team_b)}
    header_height, category_top, category_height = 330, 400, 90
    categories_bottom = category_top + 13 * category_height
    players_title_y = categories_bottom + 34
    players_top = players_title_y + 40
    team_header_height, player_row_height, table_padding = 70, 90, 14
    table_heights = {
        team: team_header_height + max(1, len(rosters[team])) * player_row_height + table_padding
        for team in (team_a, team_b)
    }
    table_a_top = players_top
    table_a_bottom = table_a_top + table_heights[team_a]
    table_b_top = table_a_bottom + 20
    table_b_bottom = table_b_top + table_heights[team_b]
    look_title_y = table_b_bottom + 44
    look_top, look_bottom = look_title_y + 38, look_title_y + 798
    flow_title_y = look_bottom + 44
    chart_top, chart_bottom = flow_title_y + 38, flow_title_y + 518
    height = chart_bottom + 66

    image = Image.new("RGB", (width, height), "#f3f6fa")
    draw = ImageDraw.Draw(image)

    # Score-first masthead.
    draw.rectangle((0, 0, width, header_height), fill="#ffffff")
    draw.rectangle((0, 0, width // 2, 14), fill=color_a)
    draw.rectangle((width // 2, 0, width, 14), fill=color_b)
    draw.text((width // 2, 42), "MATCHUP RECAP", font=_scoreboard_font(20, True), fill="#6b7e92", anchor="mm")
    for team, logo_x, color in ((team_a, 120, color_a), (team_b, width - 120, color_b)):
        logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), 126)
        if logo is not None:
            image.paste(logo, (logo_x - logo.width // 2, 112 - logo.height // 2), logo)
        else:
            draw.ellipse((logo_x - 55, 57, logo_x + 55, 167), fill=color)
    draw.text((405, 132), score_a, font=_scoreboard_font(74, True), fill=navy, anchor="rm")
    draw.text((675, 132), score_b, font=_scoreboard_font(74, True), fill=navy, anchor="lm")
    draw.text((width // 2, 132), "—", font=_scoreboard_font(38, True), fill="#8293a6", anchor="mm")
    draw.text((120, 202), name_a, font=_fit_scoreboard_font(draw, name_a, 220, 29, 18), fill=navy, anchor="mm")
    draw.text((width - 120, 202), name_b, font=_fit_scoreboard_font(draw, name_b, 220, 29, 18), fill=navy, anchor="mm")
    record_a, record_b = _scoreboard_record(row.get("TeamA_record")), _scoreboard_record(row.get("TeamB_record"))
    draw.text((120, 238), record_a, font=_scoreboard_font(18, True), fill="#718398", anchor="mm")
    draw.text((width - 120, 238), record_b, font=_scoreboard_font(18, True), fill="#718398", anchor="mm")
    status = "FINAL" if score_a_number is not None and score_b_number is not None else "RECAP"
    draw.rounded_rectangle((width // 2 - 88, 188, width // 2 + 88, 236), radius=24, fill="#111827")
    draw.text((width // 2, 212), status, font=_scoreboard_font(17, True), fill="#ffffff", anchor="mm")
    context = " • ".join(value for value in [str(row.get("Type", "")), str(row.get("Round", "")), str(matchup_date_label)] if value)
    draw.text((width // 2, 288), context, font=_fit_scoreboard_font(draw, context, width - 90, 19, 14), fill="#607286", anchor="mm")

    # Large one-row category comparisons.
    draw.text((margin, 370), "13-CATEGORY RESULT", font=_scoreboard_font(26, True), fill=navy, anchor="lm")
    category_order = ["MP", "TS%", "2PT%", "3PT%", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
    category_points = {"MP": 11, "TS%": 41, "2PT%": 31, "3PT%": 31, "FT%": 21, "PTS": 61, "OREB": 31, "DREB": 31, "AST": 41, "ST": 31, "BLK": 31, "TO": 21, "+/-": 31}
    category_lookup = category_table.set_index("Category") if category_table is not None and not category_table.empty else pd.DataFrame()
    shooting_columns = ["GP", "2PTM", "2PTA", "3PTM", "3PTA", "FTM", "FTA"]
    shooting_totals = pd.DataFrame()
    if aggregate_players is not None and not aggregate_players.empty and "sbc_team" in aggregate_players.columns:
        shooting = aggregate_players.copy()
        for column in shooting_columns:
            source = shooting[column] if column in shooting.columns else pd.Series(0, index=shooting.index)
            shooting[column] = pd.to_numeric(source, errors="coerce").fillna(0)
        shooting_totals = shooting.groupby("sbc_team")[shooting_columns].sum()
    shooting_pair = {"2PT%": ("2PTM", "2PTA"), "3PT%": ("3PTM", "3PTA"), "FT%": ("FTM", "FTA")}

    def stat_subtext(team, stat):
        if shooting_totals.empty or team not in shooting_totals.index:
            return ""
        if stat == "MP":
            return f"{_recap_stat_text(shooting_totals.loc[team, 'GP'], 'GP')} GP"
        if stat in shooting_pair:
            made, attempts = shooting_pair[stat]
            return f"{_recap_stat_text(shooting_totals.loc[team, made], made)}/{_recap_stat_text(shooting_totals.loc[team, attempts], attempts)}"
        return ""

    for index, stat in enumerate(category_order):
        top, bottom = category_top + index * category_height, category_top + (index + 1) * category_height - 6
        category_row = category_lookup.loc[stat] if not category_lookup.empty and stat in category_lookup.index else {}
        value_a, value_b = category_row.get(team_a), category_row.get(team_b)
        winner = str(category_row.get("Winner", ""))
        is_tie = winner.casefold() == "tie"
        left_fill = _recap_tint(color_a, 0.76) if is_tie else (color_a if winner == team_a else "#ffffff")
        right_fill = _recap_tint(color_b, 0.76) if is_tie else (color_b if winner == team_b else "#ffffff")
        draw.rounded_rectangle((margin, top, width - margin, bottom), radius=13, fill="#ffffff", outline="#dbe4ee", width=2)
        draw.rounded_rectangle((margin + 5, top + 5, 414, bottom - 5), radius=10, fill=left_fill)
        draw.rounded_rectangle((666, top + 5, width - margin - 5, bottom - 5), radius=10, fill=right_fill)
        display_stat = {"2PT%": "2P%", "3PT%": "3P%", "ST": "STL", "TO": "TOV*"}.get(stat, stat)
        votes = category_row.get("Votes", category_points.get(stat, ""))
        votes_text = _recap_stat_text(votes, "Votes") if votes != "" else ""
        draw.text((width // 2, top + 36), f"{display_stat} ({votes_text})" if votes_text else display_stat, font=_scoreboard_font(22, True), fill="#526579", anchor="mm")
        if is_tie:
            draw.text((width // 2, top + 59), "TIE", font=_scoreboard_font(13, True), fill="#718398", anchor="mm")
        for team, value, x, fill, won, anchor in (
            (team_a, value_a, 388, left_fill, winner == team_a, "rm"),
            (team_b, value_b, 692, right_fill, winner == team_b, "lm"),
        ):
            has_subtext = stat == "MP" or stat in shooting_pair
            draw.text((x, top + (30 if has_subtext else 43)), _recap_stat_text(value, stat), font=_scoreboard_font(32, True), fill=_recap_contrast_text(fill) if won else navy, anchor=anchor)
            subtext = stat_subtext(team, stat)
            if subtext:
                draw.text((x, top + 66), subtext, font=_scoreboard_font(17, True), fill=_recap_contrast_text(fill) if won else "#607286", anchor=anchor)

    # Full-width, stacked player boxes with two readable stat lines.
    draw.text((margin, players_title_y), "PLAYER BOX SCORE", font=_scoreboard_font(26, True), fill=navy, anchor="lm")

    def numeric(value):
        return pd.to_numeric(pd.Series([value]), errors="coerce").fillna(0).iloc[0]

    def draw_player_table(team, color, short_name, top):
        players = rosters[team]
        bottom = top + table_heights[team]
        draw.rounded_rectangle((margin, top, width - margin, bottom), radius=16, fill="#ffffff", outline="#dbe4ee", width=2)
        draw.rounded_rectangle((margin, top, width - margin, top + team_header_height), radius=16, fill=color)
        draw.rectangle((margin, top + 52, width - margin, top + team_header_height), fill=color)
        logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), 50)
        if logo is not None:
            image.paste(logo, (margin + 16, top + 10), logo)
        draw.text((margin + 82, top + 35), short_name, font=_fit_scoreboard_font(draw, short_name, 600, 27, 19), fill=_recap_contrast_text(color), anchor="lm")
        draw.text((width - margin - 18, top + 35), f"{len(players)} PLAYERS", font=_scoreboard_font(16, True), fill=_recap_contrast_text(color), anchor="rm")
        if players.empty:
            draw.text((width // 2, top + team_header_height + player_row_height // 2), "NO PLAYER DATA", font=_scoreboard_font(18, True), fill="#8293a6", anchor="mm")
            return bottom
        for player_index, (_, player) in enumerate(players.iterrows()):
            row_top = top + team_header_height + player_index * player_row_height
            row_bottom = row_top + player_row_height
            if player_index % 2 == 0:
                draw.rectangle((margin + 6, row_top, width - margin - 6, row_bottom), fill="#f2f6fa")
            rebounds = numeric(player.get("OREB")) + numeric(player.get("DREB"))
            player_name = str(player.get("display_player", ""))
            primary = f"{_recap_stat_text(player.get('PTS'), 'PTS')} PTS  •  {_recap_stat_text(rebounds, 'REB')} REB  •  {_recap_stat_text(player.get('AST'), 'AST')} AST"
            secondary = (
                f"{_recap_stat_text(player.get('MP'), 'MP')} MIN  •  {_recap_stat_text(player.get('TS%'), 'TS%')} TS  •  "
                f"{_recap_stat_text(player.get('ST'), 'ST')} STL  •  {_recap_stat_text(player.get('BLK'), 'BLK')} BLK  •  "
                f"{_recap_stat_text(player.get('TO'), 'TO')} TO  •  {_recap_stat_text(player.get('+/-'), '+/-')} +/-"
            )
            draw.text((margin + 18, row_top + 31), player_name, font=_fit_scoreboard_font(draw, player_name, 440, 25, 18), fill=navy, anchor="lm")
            draw.text((width - margin - 18, row_top + 31), primary, font=_scoreboard_font(24, True), fill=navy, anchor="rm")
            draw.text((margin + 18, row_top + 68), secondary, font=_scoreboard_font(20, True), fill="#42546a", anchor="lm")
        return bottom

    draw_player_table(team_a, color_a, name_a, table_a_top)
    draw_player_table(team_b, color_b, name_b, table_b_top)

    # Court first, then large jerseys beneath it so branding remains legible.
    draw.text((margin, look_title_y), "GAME PRESENTATION", font=_scoreboard_font(26, True), fill=navy, anchor="lm")
    draw.rounded_rectangle((margin, look_top, width - margin, look_bottom), radius=16, fill="#ffffff", outline="#dbe4ee", width=2)
    court_bottom = look_top + 408
    _paste_scoreboard_asset(image, court_image, (margin + 18, look_top + 16, width - margin - 18, court_bottom), padding=4)
    jersey_top = court_bottom + 6
    _paste_scoreboard_asset(image, road_jersey_image, (margin + 28, jersey_top, width // 2 - 18, look_bottom - 52), padding=4)
    _paste_scoreboard_asset(image, home_jersey_image, (width // 2 + 18, jersey_top, width - margin - 28, look_bottom - 52), padding=4)
    draw.text((width // 4, look_bottom - 27), f"{name_a} • {road_edition}", font=_scoreboard_font(18, True), fill="#52667b", anchor="mm")
    draw.text((width * 3 // 4, look_bottom - 27), f"{name_b} • {home_edition}", font=_scoreboard_font(18, True), fill="#52667b", anchor="mm")

    # Simplified differential flow with larger labels.
    draw.text((margin, flow_title_y), "MATCHUP FLOW", font=_scoreboard_font(26, True), fill=navy, anchor="lm")
    draw.rounded_rectangle((margin, chart_top, width - margin, chart_bottom), radius=16, fill="#ffffff", outline="#dbe4ee", width=2)
    plot_left, plot_right = margin + 58, width - margin - 28
    plot_top, plot_bottom = chart_top + 72, chart_bottom - 54
    mid_y = (plot_top + plot_bottom) // 2
    draw.line((plot_left, mid_y, plot_right, mid_y), fill="#aab6c3", width=3)
    draw.text((plot_left, chart_top + 30), name_a, font=_scoreboard_font(24, True), fill=color_a, anchor="lm")
    draw.text((plot_right, chart_top + 30), name_b, font=_scoreboard_font(24, True), fill=color_b, anchor="rm")
    draw.text((plot_left, plot_top + 4), f"{name_a.upper()} LEAD", font=_scoreboard_font(17, True), fill="#607286", anchor="la")
    draw.text((plot_left, plot_bottom - 4), f"{name_b.upper()} LEAD", font=_scoreboard_font(17, True), fill="#607286", anchor="ld")
    trend = trend_table.copy().reset_index(drop=True) if trend_table is not None else pd.DataFrame()
    if not trend.empty and team_a in trend.columns and team_b in trend.columns:
        trend[team_a] = pd.to_numeric(trend[team_a], errors="coerce")
        trend[team_b] = pd.to_numeric(trend[team_b], errors="coerce")
        trend = trend.dropna(subset=[team_a, team_b]).reset_index(drop=True)
    if not trend.empty:
        if score_a_number is not None and score_b_number is not None:
            trend.loc[trend.index[-1], [team_a, team_b]] = [score_a_number, score_b_number]
        differential = (trend[team_a] - trend[team_b]).astype(float)
        max_abs = max(1.0, float(differential.abs().max()))
        points = []
        for index, value in enumerate(differential):
            x = int(plot_left + index / max(1, len(differential) - 1) * (plot_right - plot_left))
            y = int(mid_y - value / max_abs * (plot_bottom - plot_top) * 0.41)
            points.append((x, y, value))
        for first, second in zip(points, points[1:]):
            segment_color = color_a if (first[2] + second[2]) / 2 >= 0 else color_b
            draw.line((first[0], first[1], second[0], second[1]), fill=segment_color, width=8)
        if points:
            last = points[-1]
            last_color = color_a if last[2] >= 0 else color_b
            draw.ellipse((last[0] - 9, last[1] - 9, last[0] + 9, last[1] + 9), fill=last_color)
        if "game_date" in trend.columns:
            dates = pd.to_datetime(trend["game_date"].astype(str), format="%Y%m%d", errors="coerce")
            valid_dates = dates.dropna()
            if not valid_dates.empty:
                unique_dates = list(pd.Series(valid_dates.dt.normalize().unique()).sort_values())
                for date_value in unique_dates:
                    indexes = dates[dates.dt.normalize() == date_value].index
                    if len(indexes):
                        x = int(plot_left + int(indexes.min()) / max(1, len(trend) - 1) * (plot_right - plot_left))
                        draw.line((x, plot_top, x, plot_bottom), fill="#e0e7ef", width=2)
                        draw.text((x + 5, plot_bottom + 24), pd.Timestamp(date_value).strftime("%a"), font=_scoreboard_font(18, True), fill="#52667b", anchor="mm")
    else:
        draw.text((width // 2, mid_y), "FLOW DATA UNAVAILABLE", font=_scoreboard_font(18, True), fill="#8293a6", anchor="mm")

    generated = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now()).strftime("%b %d • %I:%M %p").replace(" 0", " ")
    draw.text((margin, height - 26), f"SBCFBL • {generated}", font=_scoreboard_font(14, True), fill="#718398", anchor="lm")
    draw.text((width - margin, height - 26), "MATCHUP RECAP", font=_scoreboard_font(14, True), fill="#718398", anchor="rm")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _build_standings_bracket_image_legacy(
    west_standings: pd.DataFrame,
    east_standings: pd.DataFrame,
    postseason_games: pd.DataFrame | None,
    season_label: str,
    through_label: str,
    projected: bool = True,
    generated_at=None,
) -> bytes:
    """Build a standings one-pager with a projected/actual NBA-style postseason bracket."""
    width, height = 3800, 2000
    image = Image.new("RGB", (width, height), "#f3f6fa")
    draw = ImageDraw.Draw(image)
    navy, green, orange = "#09438e", "#009c3d", "#f59e0b"

    draw.rectangle((0, 0, width, 142), fill="#ffffff")
    draw.rounded_rectangle((42, 34, 104, 96), radius=14, fill=orange)
    draw.text((73, 65), "S", font=_scoreboard_font(30, True), fill="#172033", anchor="mm")
    draw.text((128, 57), "SBCFBL STANDINGS + POSTSEASON", font=_scoreboard_font(38, True), fill="#172033", anchor="lm")
    draw.text((128, 101), f"{season_label}  •  THROUGH {through_label.upper()}", font=_scoreboard_font(17, True), fill="#6b7e92", anchor="lm")
    status_text = "PROJECTED BRACKET" if projected else "PLAYOFF RESULTS + PROJECTIONS"
    draw.rounded_rectangle((width - 470, 42, width - 42, 96), radius=27, fill=navy if projected else green)
    draw.text((width - 256, 69), status_text, font=_scoreboard_font(17, True), fill="#ffffff", anchor="mm")

    table_top, panel_bottom = 178, height - 58
    table_width, side_margin = 780, 34
    west_box = (side_margin, table_top, side_margin + table_width, panel_bottom)
    east_box = (width - side_margin - table_width, table_top, width - side_margin, panel_bottom)

    def standing_value(row, *keys, default="-"):
        for key in keys:
            value = row.get(key, None)
            if value is not None and not pd.isna(value) and str(value).strip() != "":
                return str(value)
        return default

    def draw_standings(table, conference, box, color):
        left, top, right, bottom = box
        draw.rounded_rectangle(box, radius=22, fill="#ffffff", outline="#d7e1eb", width=2)
        draw.rounded_rectangle((left, top, right, top + 76), radius=22, fill=color)
        draw.rectangle((left, top + 54, right, top + 76), fill=color)
        draw.text((left + 24, top + 38), f"{conference.upper()} CONFERENCE", font=_scoreboard_font(23, True), fill="#ffffff", anchor="lm")
        headers = [("TEAM", left + 72, "lm"), ("W", right - 330, "mm"), ("L", right - 260, "mm"), ("GB", right - 188, "mm"), ("STRK", right - 105, "mm"), ("L10", right - 22, "rm")]
        header_y = top + 105
        for label, x, anchor in headers:
            draw.text((x, header_y), label, font=_scoreboard_font(13, True), fill="#6b7e92", anchor=anchor)
        rows = table.reset_index(drop=True).head(15) if table is not None else pd.DataFrame()
        row_top, row_height = top + 128, 102
        for index, (_, row) in enumerate(rows.iterrows()):
            y1 = row_top + index * row_height
            y2 = y1 + row_height - 4
            tier_fill = "#edf8f1" if index < 6 else "#fff8e6" if index < 10 else ("#f7f9fb" if index % 2 == 0 else "#ffffff")
            draw.rounded_rectangle((left + 8, y1, right - 8, y2), radius=9, fill=tier_fill)
            draw.text((left + 24, (y1 + y2) // 2), str(index + 1), font=_scoreboard_font(17, True), fill=color if index < 10 else "#8292a5", anchor="mm")
            team = standing_value(row, "Team", default="")
            logo_source = str(safe_team_info(team, "logo", "") or row.get("Logo", "") or "")
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(logo_source), 50)
            if logo is not None:
                image.paste(logo, (left + 39, (y1 + y2 - logo.height) // 2), logo)
            team_name = standing_value(row, "FullTeam", default=_scoreboard_team_name(team))
            draw.text((left + 102, (y1 + y2) // 2), team_name, font=_fit_scoreboard_font(draw, team_name, 325, 20, 13), fill="#172033", anchor="lm")
            wins = standing_value(row, "wins", "W", default="0")
            losses = standing_value(row, "losses", "L", default="0")
            values = [(wins, right - 330), (losses, right - 260), (standing_value(row, "GB"), right - 188), (standing_value(row, "Streak"), right - 105), (standing_value(row, "Last10", "Last 10"), right - 22)]
            for value, x in values:
                draw.text((x, (y1 + y2) // 2), value, font=_scoreboard_font(17, True), fill="#344054", anchor="rm" if x == right - 22 else "mm")
        draw.text(((left + right) // 2, bottom - 25), "TOP 6 PLAYOFFS  •  7-10 PLAY-IN", font=_scoreboard_font(13, True), fill="#718398", anchor="mm")

    draw_standings(west_standings, "West", west_box, green)
    draw_standings(east_standings, "East", east_box, navy)

    bracket_left, bracket_right = west_box[2] + 24, east_box[0] - 24
    bracket_mid = (bracket_left + bracket_right) // 2
    draw.rounded_rectangle((bracket_left, table_top, bracket_mid, panel_bottom), radius=22, fill=green)
    draw.rounded_rectangle((bracket_mid, table_top, bracket_right, panel_bottom), radius=22, fill=navy)
    field_points = [
        (bracket_left + 126, table_top + 18), (bracket_right - 126, table_top + 18),
        (bracket_right - 28, table_top + 138), (bracket_right - 28, panel_bottom - 138),
        (bracket_right - 126, panel_bottom - 18), (bracket_left + 126, panel_bottom - 18),
        (bracket_left + 28, panel_bottom - 138), (bracket_left + 28, table_top + 138),
    ]
    draw.polygon(field_points, fill="#c9ced3", outline="#172033")
    inner_points = [
        (bracket_left + 230, table_top + 102), (bracket_right - 230, table_top + 102),
        (bracket_right - 110, table_top + 220), (bracket_right - 110, panel_bottom - 220),
        (bracket_right - 230, panel_bottom - 102), (bracket_left + 230, panel_bottom - 102),
        (bracket_left + 110, panel_bottom - 220), (bracket_left + 110, table_top + 220),
    ]
    draw.polygon(inner_points, fill="#dfe3e6", outline="#a7afb7")

    def paste_vertical_label(text, x, center_y, clockwise=False):
        label = Image.new("RGBA", (720, 58), (0, 0, 0, 0))
        label_draw = ImageDraw.Draw(label)
        label_draw.text((360, 29), text, font=_scoreboard_font(31, True), fill="#ffffff", anchor="mm")
        rotated = label.rotate(-90 if clockwise else 90, expand=True, resample=Image.Resampling.BICUBIC)
        image.paste(rotated, (x - rotated.width // 2, center_y - rotated.height // 2), rotated)

    paste_vertical_label("WESTERN CONFERENCE", bracket_left + 18, (table_top + panel_bottom) // 2)
    paste_vertical_label("EASTERN CONFERENCE", bracket_right - 18, (table_top + panel_bottom) // 2, clockwise=True)
    draw.text((bracket_mid, table_top + 48), "SBCFBL POSTSEASON", font=_scoreboard_font(28, True), fill="#172033", anchor="mm")

    def seeded_teams(table):
        return [str(value) for value in table.get("Team", pd.Series(dtype=str)).head(10).tolist()]

    def projection_rounds(table, conference):
        seeds = seeded_teams(table)
        while len(seeds) < 10:
            seeds.append("TBD")
        return {
            "playin": [(seeds[6], seeds[7]), (seeds[8], seeds[9]), ("L 7/8", "W 9/10")],
            "first": [(seeds[0], seeds[7]), (seeds[3], seeds[4]), (seeds[2], seeds[5]), (seeds[1], seeds[6])],
            "semi": [(seeds[0], seeds[3]), (seeds[2], seeds[1])],
            "conf": [(seeds[0], seeds[1])],
        }

    games = postseason_games.copy() if postseason_games is not None else pd.DataFrame()
    if not games.empty:
        games["_type"] = games.get("Type", "").astype(str)
        games["_round"] = games.get("Round", "").astype(str).str.lower()
        games["_bucket"] = games.apply(lambda row: "playin" if row["_type"] == "Play-In" else "final" if "finals" in row["_round"] and "conference" not in row["_round"] else "conf" if "conference final" in row["_round"] else "semi" if "semi" in row["_round"] else "first", axis=1)
        games["_conf"] = games.apply(lambda row: safe_team_info(row.get("TeamA", ""), "conf", "Final") if safe_team_info(row.get("TeamA", ""), "conf", "") == safe_team_info(row.get("TeamB", ""), "conf", "") else "Final", axis=1)
        games["_period"] = pd.to_numeric(games.get("Period", 0), errors="coerce").fillna(0)
        games = games.sort_values(["_period", "_round"])

    def actual_pairs(conference, bucket):
        if games.empty:
            return []
        selected = games[(games["_conf"] == conference) & (games["_bucket"] == bucket)]
        return [(str(row.get("TeamA", "TBD")), str(row.get("TeamB", "TBD")), row) for _, row in selected.iterrows()]

    west_rounds = projection_rounds(west_standings, "West")
    east_rounds = projection_rounds(east_standings, "East")
    finals = [("West Champion", "East Champion")]
    for conference, rounds in (("West", west_rounds), ("East", east_rounds)):
        for bucket in ["playin", "first", "semi", "conf"]:
            actual = actual_pairs(conference, bucket)
            for index, (team_a, team_b, row) in enumerate(actual[:len(rounds[bucket])]):
                rounds[bucket][index] = (team_a, team_b, row)
    final_actual = actual_pairs("Final", "final")
    if final_actual:
        finals[0] = final_actual[-1]

    def seed_for_team(team):
        for standings_table in (west_standings, east_standings):
            reset = standings_table.reset_index(drop=True)
            if "Team" not in reset.columns:
                continue
            matches = reset.index[reset["Team"].astype(str) == str(team)].tolist()
            if matches:
                return str(matches[0] + 1)
        return ""

    def matchup_winner(card):
        if len(card) < 3:
            return ""
        row = card[2]
        score_a = _scoreboard_score_number(row.get("TeamAScore", row.get("TeamA_Score", "")))
        score_b = _scoreboard_score_number(row.get("TeamBScore", row.get("TeamB_Score", "")))
        if score_a is None or score_b is None or score_a == score_b:
            return ""
        return str(card[0] if score_a > score_b else card[1])

    def projected_card_winner(card):
        actual = matchup_winner(card)
        if actual:
            return actual
        teams = [str(card[0]), str(card[1])]
        return min(teams, key=lambda team: int(seed_for_team(team) or 99))

    # Carry actual results forward; unresolved rounds retain a chalk projection.
    for rounds in (west_rounds, east_rounds):
        seed_seven = matchup_winner(rounds["playin"][0])
        seed_eight = matchup_winner(rounds["playin"][2])
        if len(rounds["first"][0]) < 3 and seed_eight:
            rounds["first"][0] = (rounds["first"][0][0], seed_eight)
        if len(rounds["first"][3]) < 3 and seed_seven:
            rounds["first"][3] = (rounds["first"][3][0], seed_seven)
        first_winners = [projected_card_winner(card) for card in rounds["first"]]
        if len(rounds["semi"][0]) < 3:
            rounds["semi"][0] = (first_winners[0], first_winners[1])
        if len(rounds["semi"][1]) < 3:
            rounds["semi"][1] = (first_winners[2], first_winners[3])
        semi_winners = [projected_card_winner(card) for card in rounds["semi"]]
        if len(rounds["conf"][0]) < 3:
            rounds["conf"][0] = (semi_winners[0], semi_winners[1])
    if len(finals[0]) < 3:
        finals[0] = (projected_card_winner(west_rounds["conf"][0]), projected_card_winner(east_rounds["conf"][0]))

    # Arena rings and central information panel mirror the circular reference bracket.
    draw.ellipse((bracket_left + 92, table_top + 112, bracket_right - 92, panel_bottom - 112), outline="#6f7881", width=5)
    draw.ellipse((bracket_left + 310, table_top + 235, bracket_right - 310, panel_bottom - 235), outline="#89929a", width=4)
    draw.rounded_rectangle((bracket_mid - 265, table_top + 80, bracket_mid + 265, table_top + 252), radius=10, fill="#777777", outline="#ffffff", width=3)
    draw.text((bracket_mid, table_top + 126), "SBCFBL POSTSEASON", font=_scoreboard_font(21, True), fill="#ffffff", anchor="mm")
    draw.text((bracket_mid, table_top + 174), "Projected while the regular season is active", font=_scoreboard_font(15, True), fill="#eeeeee", anchor="mm")
    draw.text((bracket_mid, table_top + 211), "Completed rounds replace projections automatically", font=_scoreboard_font(13, False), fill="#eeeeee", anchor="mm")

    def elbow(start, end, color="#4f5861", line_width=4):
        x1, y1 = start
        x2, y2 = end
        middle_x = int((x1 + x2) / 2)
        draw.line((x1, y1, middle_x, y1, middle_x, y2, x2, y2), fill=color, width=line_width, joint="curve")

    def card_slots(cards):
        slots = []
        for card in cards:
            winner = matchup_winner(card)
            slots.extend([(str(card[0]), winner == str(card[0])), (str(card[1]), winner == str(card[1]))])
        return slots

    def draw_team_node(center, team, winner=False, size=72, show_seed=True):
        x, y = center
        half = size // 2
        real_team = team in team_info
        team_color = _scoreboard_color(safe_team_info(team, "bg", "#aeb5bc")) if real_team else _scoreboard_color("#aeb5bc")
        draw.rounded_rectangle((x - half, y - half, x + half, y + half), radius=max(10, size // 5), fill="#d7dadd", outline=team_color if winner else "#f6f7f8", width=6 if winner else 3)
        logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), int(size * 0.72)) if real_team else None
        if logo is not None:
            image.paste(logo, (x - logo.width // 2, y - logo.height // 2), logo)
        seed = seed_for_team(team)
        if show_seed and seed:
            draw.ellipse((x - half - 10, y - half - 10, x - half + 20, y - half + 20), fill="#172033")
            draw.text((x - half + 5, y - half + 5), seed, font=_scoreboard_font(10, True), fill="#ffffff", anchor="mm")

    def stage_positions(side):
        direction = 1 if side == "West" else -1
        edge = bracket_left if side == "West" else bracket_right
        return {
            "direction": direction,
            "first": [(edge + direction * 178, table_top + y) for y in (330, 465, 650, 785, 1045, 1180, 1365, 1500)],
            "semi": [(edge + direction * 370, table_top + y) for y in (398, 718, 1112, 1432)],
            "conf": [(edge + direction * 535, table_top + y) for y in (558, 1272)],
            "champ": (edge + direction * 680, table_top + 915),
        }

    west_positions, east_positions = stage_positions("West"), stage_positions("East")
    node_edge = 36
    for positions, conference_color in ((west_positions, green), (east_positions, navy)):
        direction = positions["direction"]
        first, semi, conf, champ = positions["first"], positions["semi"], positions["conf"], positions["champ"]
        for index in range(4):
            for source in first[index * 2:index * 2 + 2]:
                elbow((source[0] + direction * node_edge, source[1]), (semi[index][0] - direction * node_edge, semi[index][1]))
        for index in range(2):
            for source in semi[index * 2:index * 2 + 2]:
                elbow((source[0] + direction * node_edge, source[1]), (conf[index][0] - direction * node_edge, conf[index][1]))
        for source in conf:
            elbow((source[0] + direction * node_edge, source[1]), (champ[0] - direction * node_edge, champ[1]), color="#303840", line_width=5)

    final_center = (bracket_mid, table_top + 915)
    gold_points = [(bracket_mid - 255, final_center[1] - 235), (bracket_mid + 255, final_center[1] - 235), (bracket_mid + 320, final_center[1] - 170), (bracket_mid + 320, final_center[1] + 170), (bracket_mid + 255, final_center[1] + 235), (bracket_mid - 255, final_center[1] + 235), (bracket_mid - 320, final_center[1] + 170), (bracket_mid - 320, final_center[1] - 170)]
    draw.polygon(gold_points, fill="#e3b832", outline="#8d7012")
    draw.ellipse((bracket_mid - 350, final_center[1] - 42, bracket_mid - 266, final_center[1] + 42), fill=orange, outline="#ffffff", width=3)
    draw.ellipse((bracket_mid + 266, final_center[1] - 42, bracket_mid + 350, final_center[1] + 42), fill=orange, outline="#ffffff", width=3)
    elbow((west_positions["champ"][0] + node_edge, west_positions["champ"][1]), (bracket_mid - 350, final_center[1]), color="#172033", line_width=5)
    elbow((east_positions["champ"][0] - node_edge, east_positions["champ"][1]), (bracket_mid + 350, final_center[1]), color="#172033", line_width=5)
    draw.text((bracket_mid, final_center[1] - 58), "SBCFBL", font=_scoreboard_font(20, True), fill="#172033", anchor="mm")
    draw.text((bracket_mid, final_center[1]), "THE FINALS", font=_scoreboard_font(40, True), fill="#172033", anchor="mm")
    draw.text((bracket_mid, final_center[1] + 62), "WEST CHAMPION vs EAST CHAMPION", font=_scoreboard_font(14, True), fill="#4b3b0d", anchor="mm")

    for rounds, positions in ((west_rounds, west_positions), (east_rounds, east_positions)):
        first_slots, semi_slots, conf_slots = card_slots(rounds["first"]), card_slots(rounds["semi"]), card_slots(rounds["conf"])
        for center, (team, winner) in zip(positions["first"], first_slots):
            draw_team_node(center, team, winner)
        for center, (team, winner) in zip(positions["semi"], semi_slots):
            draw_team_node(center, team, winner)
        for center, (team, winner) in zip(positions["conf"], conf_slots):
            draw_team_node(center, team, winner)
        champion = matchup_winner(rounds["conf"][0]) or projected_card_winner(rounds["conf"][0])
        draw_team_node(positions["champ"], champion, bool(matchup_winner(rounds["conf"][0])), size=78, show_seed=False)

    final_winner = matchup_winner(finals[0])
    if final_winner:
        draw_team_node((bracket_mid, final_center[1] + 145), final_winner, True, size=82, show_seed=False)

    # Compact play-in lanes extend the arena without disturbing the circular playoff path.
    def draw_playin_lane(rounds, side, positions, conference_color):
        direction = positions["direction"]
        edge = bracket_left if side == "West" else bracket_right
        base_y = panel_bottom - 105
        centers = [(edge + direction * offset, base_y) for offset in (160, 285, 420)]
        lane_left, lane_right = sorted((edge + direction * 92, edge + direction * 490))
        draw.rounded_rectangle((lane_left, panel_bottom - 198, lane_right, panel_bottom - 30), radius=18, fill="#b8bec4", outline="#7f8993", width=2)
        draw.text(((lane_left + lane_right) // 2, panel_bottom - 178), f"{side.upper()} PLAY-IN", font=_scoreboard_font(11, True), fill=conference_color, anchor="mm")
        labels = ("7/8", "9/10", "#8 GAME")
        for center, card, label in zip(centers, rounds["playin"], labels):
            team_a, team_b = str(card[0]), str(card[1])
            winner = matchup_winner(card)
            draw_team_node((center[0], center[1] - 29), team_a, winner == team_a, size=45)
            draw_team_node((center[0], center[1] + 29), team_b, winner == team_b, size=45)
            draw.text((center[0], center[1] - 62), label, font=_scoreboard_font(9, True), fill="#344054", anchor="mm")
        qualifier_seven = positions["first"][7]
        qualifier_eight = positions["first"][1]
        elbow((centers[0][0] + direction * 24, centers[0][1]), (qualifier_seven[0] - direction * 38, qualifier_seven[1]), color=conference_color, line_width=4)
        elbow((centers[0][0] + direction * 24, centers[0][1]), (centers[2][0] - direction * 24, centers[2][1]))
        elbow((centers[1][0] + direction * 24, centers[1][1]), (centers[2][0] - direction * 24, centers[2][1]))
        elbow((centers[2][0] + direction * 24, centers[2][1]), (qualifier_eight[0] - direction * 38, qualifier_eight[1]), color=conference_color, line_width=4)

    draw_playin_lane(west_rounds, "West", west_positions, green)
    draw_playin_lane(east_rounds, "East", east_positions, navy)
    draw.text((bracket_mid, panel_bottom - 58), "7/8 WINNER = #7  •  7/8 LOSER vs 9/10 WINNER = #8", font=_scoreboard_font(13, True), fill="#4e5965", anchor="mm")

    generated = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now()).strftime("%b %d, %Y • %I:%M %p").replace(" 0", " ")
    draw.text((42, height - 22), f"STANDINGS REPORT • GENERATED {generated}", font=_scoreboard_font(12, True), fill="#718398", anchor="lm")
    draw.text((width - 42, height - 22), "SBCFBL POSTSEASON PICTURE", font=_scoreboard_font(12, True), fill="#718398", anchor="rm")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def build_standings_bracket_image(
    west_standings: pd.DataFrame,
    east_standings: pd.DataFrame,
    postseason_games: pd.DataFrame | None,
    season_label: str,
    through_label: str,
    projected: bool = True,
    generated_at=None,
) -> bytes:
    """Render large standings around a circular, results-driven postseason path."""
    width, height = 3800, 2000
    image = Image.new("RGB", (width, height), "#eef3f8")
    draw = ImageDraw.Draw(image)
    ink, muted = "#142033", "#66788d"
    navy, green, orange, gold = "#09438e", "#009c3d", "#f59e0b", "#efbd2e"

    draw.rectangle((0, 0, width, 142), fill="#ffffff")
    draw.rounded_rectangle((42, 31, 108, 101), radius=15, fill=orange)
    draw.text((75, 66), "S", font=_scoreboard_font(32, True), fill=ink, anchor="mm")
    draw.text((132, 54), "SBCFBL STANDINGS + POSTSEASON", font=_scoreboard_font(42, True), fill=ink, anchor="lm")
    draw.text((132, 104), f"{season_label}  •  THROUGH {through_label.upper()}", font=_scoreboard_font(20, True), fill=muted, anchor="lm")
    status_text = "CURRENT PLAYOFF PICTURE" if projected else "POSTSEASON RESULTS"
    draw.rounded_rectangle((width - 520, 39, width - 42, 101), radius=31, fill=navy if projected else green)
    draw.text((width - 281, 70), status_text, font=_scoreboard_font(20, True), fill="#ffffff", anchor="mm")

    table_top, panel_bottom = 170, height - 58
    side_margin, table_width = 30, 850
    west_box = (side_margin, table_top, side_margin + table_width, panel_bottom)
    east_box = (width - side_margin - table_width, table_top, width - side_margin, panel_bottom)

    def standing_value(row, *keys, default="-"):
        for key in keys:
            value = row.get(key, None)
            if value is not None and not pd.isna(value) and str(value).strip() != "":
                return str(value)
        return default

    def draw_standings(table, conference, box, color):
        left, top, right, bottom = box
        draw.rounded_rectangle(box, radius=24, fill="#ffffff", outline="#cbd8e5", width=3)
        draw.rounded_rectangle((left, top, right, top + 82), radius=24, fill=color)
        draw.rectangle((left, top + 56, right, top + 82), fill=color)
        draw.text((left + 26, top + 41), f"{conference.upper()} CONFERENCE", font=_scoreboard_font(27, True), fill="#ffffff", anchor="lm")
        headers = [
            ("TEAM", left + 84, "lm"), ("W", right - 340, "mm"), ("L", right - 266, "mm"),
            ("GB", right - 192, "mm"), ("STRK", right - 108, "mm"), ("L10", right - 24, "rm"),
        ]
        for label, x, anchor in headers:
            draw.text((x, top + 112), label, font=_scoreboard_font(16, True), fill=muted, anchor=anchor)
        rows = table.reset_index(drop=True).head(15) if table is not None else pd.DataFrame()
        row_top, row_height = top + 137, 101
        for index, (_, row) in enumerate(rows.iterrows()):
            y1, y2 = row_top + index * row_height, row_top + (index + 1) * row_height - 5
            fill = "#eaf7ef" if index < 6 else "#fff6df" if index < 10 else ("#f4f7fa" if index % 2 == 0 else "#ffffff")
            draw.rounded_rectangle((left + 9, y1, right - 9, y2), radius=11, fill=fill)
            row_mid = (y1 + y2) // 2
            draw.text((left + 27, row_mid), str(index + 1), font=_scoreboard_font(21, True), fill=color if index < 10 else "#8091a5", anchor="mm")
            team = standing_value(row, "Team", default="")
            logo_source = str(safe_team_info(team, "logo", "") or row.get("Logo", "") or "")
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(logo_source), 64)
            if logo is not None:
                image.paste(logo, (left + 41, row_mid - logo.height // 2), logo)
            team_name = standing_value(row, "FullTeam", default=_scoreboard_team_name(team))
            team_font = _fit_scoreboard_font(draw, team_name, 340, 26, 17)
            draw.text((left + 118, row_mid), team_name, font=team_font, fill=ink, anchor="lm")
            values = [
                (standing_value(row, "wins", "W", default="0"), right - 340),
                (standing_value(row, "losses", "L", default="0"), right - 266),
                (standing_value(row, "GB"), right - 192),
                (standing_value(row, "Streak"), right - 108),
                (standing_value(row, "Last10", "Last 10"), right - 24),
            ]
            for value, x in values:
                draw.text((x, row_mid), value, font=_scoreboard_font(20, True), fill="#28384c", anchor="rm" if x == right - 24 else "mm")
        draw.text(((left + right) // 2, bottom - 24), "TOP 6 PLAYOFFS  •  7–10 PLAY-IN", font=_scoreboard_font(16, True), fill=muted, anchor="mm")

    draw_standings(west_standings, "West", west_box, green)
    draw_standings(east_standings, "East", east_box, navy)

    bracket_left, bracket_right = west_box[2] + 20, east_box[0] - 20
    bracket_mid = (bracket_left + bracket_right) // 2
    arena_top, arena_bottom = table_top, panel_bottom
    draw.rounded_rectangle((bracket_left, arena_top, bracket_right, arena_bottom), radius=26, fill="#101b2b", outline="#253a54", width=3)
    draw.rectangle((bracket_left, arena_top, bracket_mid, arena_bottom), fill="#075c32")
    draw.rectangle((bracket_mid, arena_top, bracket_right, arena_bottom), fill="#0b477c")

    # A clean split field keeps the bracket legible; gold owns the championship.
    ring_center_y = 835
    draw.rounded_rectangle(
        (bracket_mid - 205, ring_center_y - 280, bracket_mid + 205, ring_center_y + 280),
        radius=34,
        fill="#17263a",
        outline=gold,
        width=10,
    )
    draw.text((bracket_mid, 206), "THE ROAD TO THE SBCFBL FINALS", font=_scoreboard_font(32, True), fill="#ffffff", anchor="mm")
    draw.text((bracket_mid, 247), "CURRENT SEEDS ENTER FROM THE OUTSIDE • RESULTS MOVE INWARD", font=_scoreboard_font(17, True), fill="#b9c5d2", anchor="mm")

    def seeded_teams(table):
        seeds = [str(value) for value in table.get("Team", pd.Series(dtype=str)).head(10).tolist()] if table is not None else []
        return seeds + ["TBD"] * max(0, 10 - len(seeds))

    def initial_rounds(table):
        seeds = seeded_teams(table)
        return {
            "playin": [(seeds[6], seeds[7]), (seeds[8], seeds[9]), ("L 7/8", "W 9/10")],
            "first": [(seeds[0], "PLAY-IN #8"), (seeds[3], seeds[4]), (seeds[2], seeds[5]), (seeds[1], "PLAY-IN #7")],
            "semi": [("", ""), ("", "")],
            "conf": [("", "")],
        }

    games = postseason_games.copy() if postseason_games is not None else pd.DataFrame()
    if not games.empty:
        games["_type"] = games.get("Type", "").astype(str)
        games["_round"] = games.get("Round", "").astype(str).str.lower()
        games["_bucket"] = games.apply(
            lambda row: "playin" if row["_type"] == "Play-In" else "final" if "finals" in row["_round"] and "conference" not in row["_round"] else "conf" if "conference final" in row["_round"] else "semi" if "semi" in row["_round"] else "first",
            axis=1,
        )
        games["_conf"] = games.apply(
            lambda row: safe_team_info(row.get("TeamA", ""), "conf", "Final") if safe_team_info(row.get("TeamA", ""), "conf", "") == safe_team_info(row.get("TeamB", ""), "conf", "") else "Final",
            axis=1,
        )
        games["_period"] = pd.to_numeric(games.get("Period", 0), errors="coerce").fillna(0)
        games = games.sort_values(["_period", "_round"])

    def actual_pairs(conference, bucket):
        if games.empty:
            return []
        selected = games[(games["_conf"] == conference) & (games["_bucket"] == bucket)]
        return [(str(row.get("TeamA", "")), str(row.get("TeamB", "")), row) for _, row in selected.iterrows()]

    west_rounds, east_rounds = initial_rounds(west_standings), initial_rounds(east_standings)
    for conference, rounds in (("West", west_rounds), ("East", east_rounds)):
        for bucket in ("playin", "first", "semi", "conf"):
            actual = actual_pairs(conference, bucket)
            for index, card in enumerate(actual[:len(rounds[bucket])]):
                rounds[bucket][index] = card
    finals = actual_pairs("Final", "final")
    final_card = finals[-1] if finals else ("", "")

    def seed_for_team(team):
        for standings_table in (west_standings, east_standings):
            reset = standings_table.reset_index(drop=True)
            if "Team" not in reset.columns:
                continue
            matches = reset.index[reset["Team"].astype(str) == str(team)].tolist()
            if matches:
                return str(matches[0] + 1)
        return ""

    def card_scores(card):
        if len(card) < 3:
            return None, None
        row = card[2]
        return (
            _scoreboard_score_number(row.get("TeamAScore", row.get("TeamA_Score", ""))),
            _scoreboard_score_number(row.get("TeamBScore", row.get("TeamB_Score", ""))),
        )

    def is_winner(card, team_index):
        score_a, score_b = card_scores(card)
        return score_a is not None and score_b is not None and score_a != score_b and ((team_index == 0 and score_a > score_b) or (team_index == 1 and score_b > score_a))

    card_w, card_h = 270, 112

    def team_label(team):
        if not team:
            return "—"
        if team in team_info:
            nickname = str(safe_team_info(team, "nickname", team) or team)
            city = str(team)
            return min((city, nickname), key=len)
        return str(team)

    def draw_matchup_card(center, card, color, compact=False, finals_card=False):
        x, y = center
        w, h = ((330, 136) if finals_card else ((226, 98) if compact else (card_w, card_h)))
        left, top, right, bottom = x - w // 2, y - h // 2, x + w // 2, y + h // 2
        draw.rounded_rectangle((left, top, right, bottom), radius=18, fill="#f8fafc", outline=color, width=4)
        draw.line((left + 10, y, right - 10, y), fill="#d8e0e9", width=2)
        scores = card_scores(card)
        for team_index, team in enumerate((str(card[0]), str(card[1]))):
            row_y = top + h // 4 if team_index == 0 else top + 3 * h // 4
            winner = is_winner(card, team_index)
            if winner:
                draw.rounded_rectangle((left + 5, row_y - h // 4 + 3, right - 5, row_y + h // 4 - 3), radius=12, fill="#e8f5ec")
            seed = seed_for_team(team)
            if seed and not compact:
                draw.text((left + 17, row_y), seed, font=_scoreboard_font(17, True), fill=color, anchor="lm")
            logo_size = 38 if compact else 44
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), logo_size) if team in team_info else None
            logo_x = left + (17 if compact else 42)
            if logo is not None:
                image.paste(logo, (logo_x, row_y - logo.height // 2), logo)
            text_x = logo_x + (logo_size + 7 if logo is not None else 2)
            score = scores[team_index] if scores[team_index] is not None else None
            score_space = 50 if score is not None else 10
            label = team_label(team)
            font = _fit_scoreboard_font(draw, label, right - score_space - text_x, 20 if compact else 23, 14)
            draw.text((text_x, row_y), label, font=font, fill=ink if team else "#93a1b2", anchor="lm")
            if score is not None:
                score_text = _scoreboard_score(score)
                draw.text((right - 13, row_y), score_text, font=_scoreboard_font(20, True), fill=color if winner else ink, anchor="rm")
        return left, top, right, bottom

    west_positions = {"first": [(1050, y) for y in (390, 665, 1005, 1280)], "semi": [(1335, y) for y in (530, 1140)], "conf": [(1555, ring_center_y)]}
    east_positions = {"first": [(2750, y) for y in (390, 665, 1005, 1280)], "semi": [(2465, y) for y in (530, 1140)], "conf": [(2245, ring_center_y)]}

    def draw_connections(positions, side, color):
        direction = 1 if side == "West" else -1
        for index in range(2):
            target = positions["semi"][index]
            for source in positions["first"][index * 2:index * 2 + 2]:
                draw.line((source[0] + direction * card_w // 2, source[1], target[0] - direction * card_w // 2, target[1]), fill=color, width=6)
        for source in positions["semi"]:
            target = positions["conf"][0]
            draw.line((source[0] + direction * card_w // 2, source[1], target[0] - direction * card_w // 2, target[1]), fill=color, width=7)

    draw_connections(west_positions, "West", "#4ba974")
    draw_connections(east_positions, "East", "#4c7fb9")
    draw.line((1690, ring_center_y, 1735, ring_center_y), fill=gold, width=8)
    draw.line((2065, ring_center_y, 2110, ring_center_y), fill=gold, width=8)

    stage_y = 292
    for x, label, color in ((1050, "FIRST ROUND", green), (1335, "SEMIFINALS", green), (1555, "WEST FINAL", green), (1900, "SBCFBL FINALS", gold), (2245, "EAST FINAL", navy), (2465, "SEMIFINALS", navy), (2750, "FIRST ROUND", navy)):
        draw.rounded_rectangle((x - 105, stage_y - 22, x + 105, stage_y + 22), radius=22, fill=color)
        draw.text((x, stage_y), label, font=_scoreboard_font(16, True), fill="#ffffff" if color != gold else ink, anchor="mm")

    for rounds, positions, color in ((west_rounds, west_positions, green), (east_rounds, east_positions, navy)):
        for bucket in ("first", "semi", "conf"):
            for center, card in zip(positions[bucket], rounds[bucket]):
                draw_matchup_card(center, card, color)

    draw.text((bracket_mid, ring_center_y - 118), "SBCFBL", font=_scoreboard_font(22, True), fill="#f8fafc", anchor="mm")
    draw.text((bracket_mid, ring_center_y - 78), "THE FINALS", font=_scoreboard_font(38, True), fill=gold, anchor="mm")
    draw_matchup_card((bracket_mid, ring_center_y + 22), final_card, gold, finals_card=True)

    # The play-in is a separate, readable flow instead of sharing bracket connector lines.
    playin_top, playin_bottom = 1510, 1900
    draw.rounded_rectangle((bracket_left + 24, playin_top, bracket_right - 24, playin_bottom), radius=24, fill="#f8fafc", outline="#cbd7e4", width=3)
    draw.text((bracket_mid, playin_top + 34), "PLAY-IN PATH", font=_scoreboard_font(29, True), fill=ink, anchor="mm")
    draw.text((bracket_mid, playin_top + 70), "7/8 WINNER EARNS #7  •  7/8 LOSER + 9/10 WINNER PLAY FOR #8", font=_scoreboard_font(17, True), fill=muted, anchor="mm")

    def draw_playin_group(rounds, side, group_left, color):
        group_right = group_left + 925
        draw.rounded_rectangle((group_left, playin_top + 90, group_right, playin_bottom - 20), radius=20, fill="#eef3f7", outline=color, width=3)
        draw.text((group_left + 24, playin_top + 117), f"{side.upper()} PLAY-IN", font=_scoreboard_font(22, True), fill=color, anchor="lm")
        centers = [(group_left + 145, playin_top + 226), (group_left + 450, playin_top + 226), (group_left + 775, playin_top + 226)]
        labels = ("#7 GAME", "ELIMINATION GAME", "#8 GAME")
        for center, card, label in zip(centers, rounds["playin"], labels):
            draw.text((center[0], playin_top + 154), label, font=_scoreboard_font(16, True), fill=ink, anchor="mm")
            draw_matchup_card(center, card, color, compact=True)
        draw.text((group_left + 295, playin_top + 226), "+", font=_scoreboard_font(34, True), fill=muted, anchor="mm")
        draw.text((group_left + 612, playin_top + 226), "→", font=_scoreboard_font(38, True), fill=color, anchor="mm")
        draw.text((group_left + 145, playin_bottom - 40), "WINNER → #7 SEED", font=_scoreboard_font(16, True), fill=color, anchor="mm")
        draw.text((group_left + 612, playin_bottom - 40), "LOSER 7/8 + WINNER 9/10 → #8 SEED", font=_scoreboard_font(15, True), fill=color, anchor="mm")

    draw_playin_group(west_rounds, "West", bracket_left + 42, green)
    draw_playin_group(east_rounds, "East", bracket_mid + 18, navy)

    generated = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now()).strftime("%b %d, %Y • %I:%M %p").replace(" 0", " ")
    draw.text((42, height - 22), f"STANDINGS REPORT • GENERATED {generated}", font=_scoreboard_font(14, True), fill=muted, anchor="lm")
    draw.text((width - 42, height - 22), "SBCFBL POSTSEASON PICTURE", font=_scoreboard_font(14, True), fill=muted, anchor="rm")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _build_mobile_standings_image_legacy(
    west_standings: pd.DataFrame,
    east_standings: pd.DataFrame,
    postseason_games: pd.DataFrame | None,
    season_label: str,
    through_label: str,
    projected: bool = True,
    generated_at=None,
) -> bytes:
    """Render phone-first standings followed by postseason matchup cards."""
    width, margin = 1080, 30
    header_height, standings_row_height = 176, 64
    conference_header_height, section_gap = 62, 18
    standings_height = conference_header_height + 15 * standings_row_height + section_gap

    games = postseason_games.copy() if postseason_games is not None else pd.DataFrame()

    def seeded_teams(table):
        teams = [str(value) for value in table.get("Team", pd.Series(dtype=str)).head(10).tolist()] if table is not None else []
        return teams + ["TBD"] * max(0, 10 - len(teams))

    def projected_cards(table):
        seeds = seeded_teams(table)
        return [
            {"label": "PLAY-IN 7/8", "TeamA": seeds[6], "TeamB": seeds[7]},
            {"label": "PLAY-IN 9/10", "TeamA": seeds[8], "TeamB": seeds[9]},
            {"label": "PLAY-IN #8", "TeamA": "7/8 LOSER", "TeamB": "9/10 WINNER"},
            {"label": "FIRST ROUND 1/8", "TeamA": seeds[0], "TeamB": seeds[7]},
            {"label": "FIRST ROUND 4/5", "TeamA": seeds[3], "TeamB": seeds[4]},
            {"label": "FIRST ROUND 3/6", "TeamA": seeds[2], "TeamB": seeds[5]},
            {"label": "FIRST ROUND 2/7", "TeamA": seeds[1], "TeamB": seeds[6]},
        ]

    def actual_cards(conference):
        if games.empty:
            return []
        conference_rows = games[
            games.apply(
                lambda game: str(safe_team_info(str(game.get("TeamA", "")), "conf", safe_team_info(str(game.get("TeamB", "")), "conf", ""))) == conference,
                axis=1,
            )
        ].copy()
        sort_columns = [column for column in ["Period", "Round", "Game_ID"] if column in conference_rows.columns]
        if sort_columns:
            conference_rows = conference_rows.sort_values(sort_columns)
        cards = []
        for _, game in conference_rows.iterrows():
            label = str(game.get("Round", "") or game.get("Type", "") or "POSTSEASON").upper()
            cards.append({
                "label": label,
                "TeamA": str(game.get("TeamA", "")),
                "TeamB": str(game.get("TeamB", "")),
                "TeamAScore": game.get("TeamAScore", game.get("TeamA_Score")),
                "TeamBScore": game.get("TeamBScore", game.get("TeamB_Score")),
                "actual": True,
            })
        return cards

    matchup_sections = []
    for conference, table in (("West", west_standings), ("East", east_standings)):
        cards = actual_cards(conference) if not projected else []
        if not cards:
            cards = projected_cards(table)
        matchup_sections.append((conference, cards))
    matchup_row_height = 84
    matchup_section_heights = [58 + len(cards) * matchup_row_height + section_gap for _, cards in matchup_sections]
    footer_height = 48
    height = header_height + standings_height * 2 + sum(matchup_section_heights) + footer_height + 58

    image = Image.new("RGB", (width, height), "#f3f6fa")
    draw = ImageDraw.Draw(image)
    navy, west_color, east_color, orange = "#172033", "#009c3d", "#09438e", "#f59e0b"
    draw.rectangle((0, 0, width, header_height), fill="#ffffff")
    draw.rounded_rectangle((margin, 28, margin + 60, 88), radius=14, fill=orange)
    draw.text((margin + 30, 58), "S", font=_scoreboard_font(31, True), fill=navy, anchor="mm")
    draw.text((margin + 82, 50), "STANDINGS", font=_scoreboard_font(34, True), fill=navy, anchor="lm")
    draw.text((margin + 82, 90), f"{season_label}  \u2022  {through_label}", font=_scoreboard_font(15, True), fill="#65778a", anchor="lm")
    status = "PROJECTED MATCHUPS" if projected else "POSTSEASON RESULTS"
    draw.rounded_rectangle((width - 290, 116, width - margin, 154), radius=19, fill=navy)
    draw.text((width - 160, 135), status, font=_scoreboard_font(13, True), fill="#ffffff", anchor="mm")

    def standing_value(row, *keys, default="-"):
        for key in keys:
            value = row.get(key, None)
            if value is not None and not pd.isna(value) and str(value).strip() != "":
                return str(value)
        return default

    def draw_conference_standings(table, conference, cursor, color):
        draw.rounded_rectangle((margin, cursor, width - margin, cursor + conference_header_height - 8), radius=14, fill=color)
        draw.text((margin + 20, cursor + 27), conference.upper(), font=_scoreboard_font(21, True), fill="#ffffff", anchor="lm")
        draw.text((width - margin - 18, cursor + 27), "W-L   GB   STRK   L10", font=_scoreboard_font(11, True), fill="#ffffff", anchor="rm")
        cursor += conference_header_height
        rows = table.reset_index(drop=True).head(15) if table is not None else pd.DataFrame()
        for index in range(15):
            top, bottom = cursor + index * standings_row_height, cursor + (index + 1) * standings_row_height - 5
            tier_fill = "#edf8f1" if index < 6 else "#fff8e6" if index < 10 else "#ffffff"
            draw.rounded_rectangle((margin, top, width - margin, bottom), radius=10, fill=tier_fill, outline="#dbe4ee", width=1)
            if index >= len(rows):
                continue
            row = rows.iloc[index]
            team = standing_value(row, "Team", default="")
            draw.text((margin + 22, (top + bottom) // 2), str(index + 1), font=_scoreboard_font(14, True), fill=color if index < 10 else "#8293a6", anchor="mm")
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", row.get("Logo", "")) or "")), 42)
            if logo is not None:
                image.paste(logo, (margin + 45, (top + bottom - logo.height) // 2), logo)
            nickname = str(safe_team_info(team, "nickname", _scoreboard_team_name(team)) or _scoreboard_team_name(team))
            draw.text((margin + 98, (top + bottom) // 2), nickname, font=_fit_scoreboard_font(draw, nickname, 345, 18, 11), fill=navy, anchor="lm")
            wins, losses = standing_value(row, "wins", "W", default="0"), standing_value(row, "losses", "L", default="0")
            values = [f"{wins}-{losses}", standing_value(row, "GB"), standing_value(row, "Streak"), standing_value(row, "Last10", "Last 10")]
            positions = [width - 350, width - 245, width - 145, width - margin - 14]
            for value, x in zip(values, positions):
                draw.text((x, (top + bottom) // 2), value, font=_scoreboard_font(14, True), fill="#344054", anchor="rm")
        return cursor + 15 * standings_row_height + section_gap

    cursor = header_height
    cursor = draw_conference_standings(west_standings, "West", cursor, west_color)
    cursor = draw_conference_standings(east_standings, "East", cursor, east_color)
    draw.text((margin, cursor + 22), "POSTSEASON MATCHUPS", font=_scoreboard_font(20, True), fill=navy, anchor="lm")
    cursor += 52

    def draw_matchup_card(card, top, conference_color):
        bottom = top + matchup_row_height - 7
        team_a, team_b = str(card.get("TeamA", "TBD")), str(card.get("TeamB", "TBD"))
        color_a = _scoreboard_color(safe_team_info(team_a, "bg", conference_color))
        color_b = _scoreboard_color(safe_team_info(team_b, "bg", conference_color))
        draw.rounded_rectangle((margin, top, width - margin, bottom), radius=12, fill="#ffffff", outline="#dbe4ee", width=2)
        draw.rounded_rectangle((margin, top, margin + 8, bottom), radius=4, fill=color_a)
        draw.rounded_rectangle((width - margin - 8, top, width - margin, bottom), radius=4, fill=color_b)
        for team, x, color in ((team_a, margin + 52, color_a), (team_b, width - margin - 52, color_b)):
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), 48)
            if logo is not None:
                image.paste(logo, (x - logo.width // 2, (top + bottom - logo.height) // 2), logo)
            elif team not in {"TBD", "7/8 LOSER", "9/10 WINNER"}:
                draw.ellipse((x - 21, (top + bottom) // 2 - 21, x + 21, (top + bottom) // 2 + 21), fill=color)
        label_a = str(safe_team_info(team_a, "nickname", team_a) or team_a)
        label_b = str(safe_team_info(team_b, "nickname", team_b) or team_b)
        draw.text((margin + 88, (top + bottom) // 2), label_a, font=_fit_scoreboard_font(draw, label_a, 265, 18, 10), fill=navy, anchor="lm")
        draw.text((width - margin - 88, (top + bottom) // 2), label_b, font=_fit_scoreboard_font(draw, label_b, 265, 18, 10), fill=navy, anchor="rm")
        draw.text((width // 2, top + 20), str(card.get("label", "MATCHUP")), font=_scoreboard_font(10, True), fill="#718398", anchor="mm")
        score_a = _scoreboard_score_number(card.get("TeamAScore"))
        score_b = _scoreboard_score_number(card.get("TeamBScore"))
        center_text = f"{_scoreboard_score(score_a)} — {_scoreboard_score(score_b)}" if score_a is not None and score_b is not None else "VS"
        draw.text((width // 2, top + 50), center_text, font=_scoreboard_font(17, True), fill=navy, anchor="mm")

    for conference, cards in matchup_sections:
        conference_color = west_color if conference == "West" else east_color
        draw.rounded_rectangle((margin, cursor, width - margin, cursor + 46), radius=12, fill=conference_color)
        draw.text((margin + 18, cursor + 23), conference.upper(), font=_scoreboard_font(16, True), fill="#ffffff", anchor="lm")
        draw.text((width - margin - 18, cursor + 23), f"{len(cards)} MATCHUPS", font=_scoreboard_font(11, True), fill="#ffffff", anchor="rm")
        cursor += 58
        for card in cards:
            draw_matchup_card(card, cursor, conference_color)
            cursor += matchup_row_height
        cursor += section_gap

    generated = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now()).strftime("%b %d  \u2022  %I:%M %p").replace(" 0", " ")
    draw.text((margin, height - 24), f"SBCFBL  \u2022  {generated}", font=_scoreboard_font(11, True), fill="#718398", anchor="lm")
    draw.text((width - margin, height - 24), "STANDINGS", font=_scoreboard_font(11, True), fill="#718398", anchor="rm")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def build_mobile_standings_image(
    west_standings: pd.DataFrame,
    east_standings: pd.DataFrame,
    postseason_games: pd.DataFrame | None,
    season_label: str,
    through_label: str,
    projected: bool = True,
    generated_at=None,
) -> bytes:
    """Render compact, logo-first mobile standings and a minimal postseason bracket."""
    width, height, margin = 1080, 2600, 28
    image = Image.new("RGB", (width, height), "#eef3f8")
    draw = ImageDraw.Draw(image)
    ink, muted = "#142033", "#687b90"
    west_color, east_color, orange, gold = "#009c3d", "#09438e", "#f59e0b", "#efbd2e"

    draw.rectangle((0, 0, width, 166), fill="#ffffff")
    draw.rounded_rectangle((margin, 26, margin + 62, 88), radius=14, fill=orange)
    draw.text((margin + 31, 57), "S", font=_scoreboard_font(32, True), fill=ink, anchor="mm")
    draw.text((margin + 82, 48), "STANDINGS", font=_scoreboard_font(38, True), fill=ink, anchor="lm")
    draw.text((margin + 82, 96), f"{season_label}  •  {through_label}", font=_scoreboard_font(18, True), fill=muted, anchor="lm")
    draw.rounded_rectangle((width - 300, 112, width - margin, 152), radius=20, fill=east_color)
    draw.text((width - 164, 132), "PLAYOFF PICTURE", font=_scoreboard_font(15, True), fill="#ffffff", anchor="mm")

    def standing_value(row, *keys, default="-"):
        for key in keys:
            value = row.get(key, None)
            if value is not None and not pd.isna(value) and str(value).strip() != "":
                return str(value)
        return default

    standings_top, panel_gap = 180, 24
    panel_width = (width - margin * 2 - panel_gap) // 2
    conference_header, row_height = 76, 68
    standings_bottom = standings_top + conference_header + 15 * row_height

    def draw_conference(table, conference, left, color):
        right = left + panel_width
        draw.rounded_rectangle((left, standings_top, right, standings_bottom), radius=20, fill="#ffffff", outline="#cbd8e5", width=2)
        draw.rounded_rectangle((left, standings_top, right, standings_top + conference_header), radius=20, fill=color)
        draw.rectangle((left, standings_top + 52, right, standings_top + conference_header), fill=color)
        draw.text((left + 20, standings_top + 28), conference.upper(), font=_scoreboard_font(24, True), fill="#ffffff", anchor="lm")
        draw.text((left + 82, standings_top + 58), "TEAM", font=_scoreboard_font(13, True), fill="#dff5e7" if conference == "West" else "#dbeafe", anchor="mm")
        draw.text((right - 136, standings_top + 28), "W–L", font=_scoreboard_font(17, True), fill="#ffffff", anchor="mm")
        draw.text((right - 34, standings_top + 28), "GB", font=_scoreboard_font(17, True), fill="#ffffff", anchor="mm")
        rows = table.reset_index(drop=True).head(15) if table is not None else pd.DataFrame()
        for index in range(15):
            top = standings_top + conference_header + index * row_height
            bottom = top + row_height - 4
            fill = "#eaf7ef" if index < 6 else "#fff6df" if index < 10 else ("#f4f7fa" if index % 2 == 0 else "#ffffff")
            draw.rounded_rectangle((left + 6, top, right - 6, bottom), radius=9, fill=fill)
            if index >= len(rows):
                continue
            row = rows.iloc[index]
            team = standing_value(row, "Team", default="")
            center_y = (top + bottom) // 2
            draw.text((left + 22, center_y), str(index + 1), font=_scoreboard_font(17, True), fill=color if index < 10 else "#8192a6", anchor="mm")
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", row.get("Logo", "")) or "")), 54)
            if logo is not None:
                image.paste(logo, (left + 46, center_y - logo.height // 2), logo)
            else:
                fallback_color = _scoreboard_color(safe_team_info(team, "bg", color))
                draw.ellipse((left + 48, center_y - 23, left + 94, center_y + 23), fill=fallback_color, outline="#ffffff", width=2)
                draw.text((left + 71, center_y), str(team)[:1].upper(), font=_scoreboard_font(17, True), fill="#ffffff", anchor="mm")
            nickname = _scoreboard_team_label(team)
            draw.text((left + 108, center_y), nickname, font=_fit_scoreboard_font(draw, nickname, 150, 20, 13), fill=ink, anchor="lm")
            wins = standing_value(row, "wins", "W", default="0")
            losses = standing_value(row, "losses", "L", default="0")
            draw.text((right - 136, center_y), f"{wins}–{losses}", font=_scoreboard_font(24, True), fill=ink, anchor="mm")
            draw.text((right - 34, center_y), standing_value(row, "GB"), font=_scoreboard_font(22, True), fill=ink, anchor="mm")

    draw_conference(west_standings, "West", margin, west_color)
    draw_conference(east_standings, "East", margin + panel_width + panel_gap, east_color)

    def seeded_teams(table):
        seeds = [str(value) for value in table.get("Team", pd.Series(dtype=str)).head(10).tolist()] if table is not None else []
        return seeds + [""] * max(0, 10 - len(seeds))

    def initial_rounds(table):
        seeds = seeded_teams(table)
        return {
            "playin": [(seeds[6], seeds[7]), (seeds[8], seeds[9]), ("", "")],
            "first": [(seeds[0], ""), (seeds[3], seeds[4]), (seeds[2], seeds[5]), (seeds[1], "")],
            "semi": [("", ""), ("", "")],
            "conf": [("", "")],
        }

    games = postseason_games.copy() if postseason_games is not None else pd.DataFrame()
    if not games.empty:
        games["_type"] = games.get("Type", "").astype(str)
        games["_round"] = games.get("Round", "").astype(str).str.lower()
        games["_bucket"] = games.apply(
            lambda row: "playin" if row["_type"] == "Play-In" else "final" if "finals" in row["_round"] and "conference" not in row["_round"] else "conf" if "conference final" in row["_round"] else "semi" if "semi" in row["_round"] else "first",
            axis=1,
        )
        games["_conf"] = games.apply(
            lambda row: safe_team_info(row.get("TeamA", ""), "conf", "Final") if safe_team_info(row.get("TeamA", ""), "conf", "") == safe_team_info(row.get("TeamB", ""), "conf", "") else "Final",
            axis=1,
        )
        games["_period"] = pd.to_numeric(games.get("Period", 0), errors="coerce").fillna(0)
        games = games.sort_values(["_period", "_round"])

    def actual_pairs(conference, bucket):
        if games.empty:
            return []
        selected = games[(games["_conf"] == conference) & (games["_bucket"] == bucket)]
        return [(str(row.get("TeamA", "")), str(row.get("TeamB", "")), row) for _, row in selected.iterrows()]

    west_rounds, east_rounds = initial_rounds(west_standings), initial_rounds(east_standings)
    for conference, rounds in (("West", west_rounds), ("East", east_rounds)):
        for bucket in ("playin", "first", "semi", "conf"):
            actual = actual_pairs(conference, bucket)
            for index, card in enumerate(actual[:len(rounds[bucket])]):
                rounds[bucket][index] = card
    finals = actual_pairs("Final", "final")
    final_card = finals[-1] if finals else ("", "")

    def card_scores(card):
        if len(card) < 3:
            return None, None
        row = card[2]
        return (
            _scoreboard_score_number(row.get("TeamAScore", row.get("TeamA_Score", ""))),
            _scoreboard_score_number(row.get("TeamBScore", row.get("TeamB_Score", ""))),
        )

    def slot_winner(card, index):
        score_a, score_b = card_scores(card)
        return score_a is not None and score_b is not None and score_a != score_b and ((index == 0 and score_a > score_b) or (index == 1 and score_b > score_a))

    bracket_top, bracket_bottom = standings_bottom + 28, height - 58
    bracket_mid = width // 2
    draw.rounded_rectangle((margin, bracket_top, width - margin, bracket_bottom), radius=22, fill=west_color)
    draw.rectangle((bracket_mid, bracket_top, width - margin, bracket_bottom), fill=east_color)
    draw.text((bracket_mid, bracket_top + 34), "POSTSEASON", font=_scoreboard_font(30, True), fill="#ffffff", anchor="mm")
    draw.text((bracket_mid, bracket_top + 70), "LOGOS MOVE TOWARD THE FINALS", font=_scoreboard_font(15, True), fill="#d8e3ee", anchor="mm")

    path_top, path_bottom = bracket_top + 126, bracket_bottom - 225
    path_mid_y = (path_top + path_bottom) // 2
    card_width, card_height = 72, 126
    west_positions = {"first": [(92, y) for y in (path_top + 45, path_top + 230, path_top + 455, path_top + 640)], "semi": [(265, y) for y in (path_top + 138, path_top + 548)], "conf": [(410, path_mid_y)]}
    east_positions = {"first": [(988, y) for y in (path_top + 45, path_top + 230, path_top + 455, path_top + 640)], "semi": [(815, y) for y in (path_top + 138, path_top + 548)], "conf": [(670, path_mid_y)]}

    def draw_connections(positions, side):
        direction = 1 if side == "West" else -1
        line_color = "#9ae0b4" if side == "West" else "#9dc2e8"
        for index in range(2):
            target = positions["semi"][index]
            for source in positions["first"][index * 2:index * 2 + 2]:
                draw.line((source[0] + direction * card_width // 2, source[1], target[0] - direction * card_width // 2, target[1]), fill=line_color, width=5)
        for source in positions["semi"]:
            target = positions["conf"][0]
            draw.line((source[0] + direction * card_width // 2, source[1], target[0] - direction * card_width // 2, target[1]), fill=line_color, width=6)

    draw_connections(west_positions, "West")
    draw_connections(east_positions, "East")

    def draw_logo_slot(center, team, color, winner=False, size=54):
        x, y = center
        radius = size // 2 + 5
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="#ffffff", outline=gold if winner else "#d9e3ed", width=5 if winner else 3)
        if team:
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), size)
            if logo is not None:
                image.paste(logo, (x - logo.width // 2, y - logo.height // 2), logo)
            else:
                draw.text((x, y), str(team)[:1].upper(), font=_scoreboard_font(21, True), fill=color, anchor="mm")

    def draw_logo_match(center, card, color, final=False):
        x, y = center
        spacing = 44 if final else 36
        for index, team in enumerate((str(card[0]), str(card[1]))):
            draw_logo_slot((x, y - spacing if index == 0 else y + spacing), team, color, slot_winner(card, index), 60 if final else 50)

    for rounds, positions, color in ((west_rounds, west_positions, west_color), (east_rounds, east_positions, east_color)):
        for bucket in ("first", "semi", "conf"):
            for center, card in zip(positions[bucket], rounds[bucket]):
                draw_logo_match(center, card, color)

    final_left, final_right = bracket_mid - 62, bracket_mid + 62
    draw.rounded_rectangle((final_left, path_mid_y - 180, final_right, path_mid_y + 180), radius=24, fill="#17263a", outline=gold, width=8)
    draw.text((bracket_mid, path_mid_y - 137), "FINALS", font=_scoreboard_font(18, True), fill=gold, anchor="mm")
    draw_logo_match((bracket_mid, path_mid_y + 18), final_card, gold, final=True)
    draw.line((446, path_mid_y, final_left, path_mid_y), fill=gold, width=7)
    draw.line((final_right, path_mid_y, 634, path_mid_y), fill=gold, width=7)

    playin_y = bracket_bottom - 88
    draw.rounded_rectangle((margin + 16, bracket_bottom - 194, width - margin - 16, bracket_bottom - 28), radius=18, fill="#f8fafc", outline="#d4dee8", width=2)
    draw.text((bracket_mid, bracket_bottom - 168), "PLAY-IN", font=_scoreboard_font(20, True), fill=ink, anchor="mm")

    def draw_playin_logos(rounds, start_x, color):
        labels = ("7 / 8", "9 / 10", "#8 GAME")
        for index, (card, label) in enumerate(zip(rounds["playin"], labels)):
            center_x = start_x + index * 135
            draw.text((center_x, bracket_bottom - 137), label, font=_scoreboard_font(12, True), fill=color, anchor="mm")
            draw_logo_slot((center_x - 24, playin_y), str(card[0]), color, slot_winner(card, 0), 38)
            draw_logo_slot((center_x + 24, playin_y), str(card[1]), color, slot_winner(card, 1), 38)

    draw_playin_logos(west_rounds, 105, west_color)
    draw_playin_logos(east_rounds, 705, east_color)

    generated = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now()).strftime("%b %d • %I:%M %p").replace(" 0", " ")
    draw.text((margin, height - 22), f"SBCFBL • {generated}", font=_scoreboard_font(13, True), fill=muted, anchor="lm")
    draw.text((width - margin, height - 22), "MOBILE STANDINGS", font=_scoreboard_font(13, True), fill=muted, anchor="rm")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def build_matchup_preview_image(
    matchups: pd.DataFrame,
    featured_matchups: list,
    featured_assets: list,
    season_label: str,
    period_label: str,
    generated_at=None,
) -> bytes:
    """Build a weekly slate with two presentation-heavy featured matchup previews."""
    width, height = 3000, 2000
    image = Image.new("RGB", (width, height), "#f3f6fa")
    draw = ImageDraw.Draw(image)
    navy, orange = "#172033", "#f59e0b"
    draw.rectangle((0, 0, width, 142), fill="#ffffff")
    draw.rounded_rectangle((42, 34, 104, 96), radius=14, fill=orange)
    draw.text((73, 65), "S", font=_scoreboard_font(30, True), fill=navy, anchor="mm")
    draw.text((128, 57), "SBCFBL MATCHUP PREVIEW", font=_scoreboard_font(38, True), fill=navy, anchor="lm")
    draw.text((128, 101), f"{season_label}  •  {period_label}", font=_scoreboard_font(17, True), fill="#6b7e92", anchor="lm")
    draw.rounded_rectangle((width - 410, 42, width - 42, 96), radius=27, fill=navy)
    draw.text((width - 226, 69), "WEEKLY PRIMER", font=_scoreboard_font(17, True), fill="#ffffff", anchor="mm")

    slate_left, slate_top, slate_right, slate_bottom = 34, 172, 620, height - 54
    draw.rounded_rectangle((slate_left, slate_top, slate_right, slate_bottom), radius=22, fill="#ffffff", outline="#d7e1eb", width=2)
    draw.text((slate_left + 24, slate_top + 42), "WEEKLY SLATE", font=_scoreboard_font(24, True), fill=navy, anchor="lm")
    draw.text((slate_right - 22, slate_top + 42), f"{len(matchups)} GAMES", font=_scoreboard_font(14, True), fill="#718398", anchor="rm")
    feature_ids = {str(row.get("Game_ID", "")) for row in featured_matchups}
    rows = matchups.copy().sort_values([column for column in ["Type", "TeamB", "TeamA"] if column in matchups.columns]).reset_index(drop=True)
    row_top = slate_top + 76
    row_height = min(104, max(55, int((slate_bottom - row_top - 20) / max(1, len(rows)))))
    for index, (_, row) in enumerate(rows.iterrows()):
        y1, y2 = row_top + index * row_height, row_top + (index + 1) * row_height - 4
        featured = str(row.get("Game_ID", "")) in feature_ids
        draw.rounded_rectangle((slate_left + 10, y1, slate_right - 10, y2), radius=10, fill="#fff7e6" if featured else ("#f5f8fb" if index % 2 == 0 else "#ffffff"), outline=orange if featured else None, width=3 if featured else 1)
        team_a, team_b = str(row.get("TeamA", "")), str(row.get("TeamB", ""))
        center_y = (y1 + y2) // 2
        for team, x in ((team_a, slate_left + 36), (team_b, slate_right - 36)):
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), min(46, row_height - 12))
            if logo is not None:
                image.paste(logo, (x - logo.width // 2, center_y - logo.height // 2), logo)
        name_a, name_b = _scoreboard_team_label(team_a), _scoreboard_team_label(team_b)
        matchup_line = f"{name_a} ({row.get('TeamA_record', '—')})  @  {name_b} ({row.get('TeamB_record', '—')})"
        draw.text(
            ((slate_left + slate_right) // 2, center_y),
            matchup_line,
            font=_fit_scoreboard_font(draw, matchup_line, slate_right - slate_left - 116, 18, 9),
            fill=orange if featured else navy,
            anchor="mm",
        )

    feature_left, feature_right = 650, width - 34
    feature_start = 228
    feature_gap = 22
    feature_height = (height - feature_start - 54 - feature_gap) // 2
    draw.text((feature_left + 4, 193), "FEATURED MATCHUPS", font=_scoreboard_font(32, True), fill=navy, anchor="lm")
    draw.line((feature_left + 360, 193, feature_right, 193), fill="#cfd9e4", width=2)

    def lineup_rows(asset, team):
        lineups = asset.get("lineups", {}) if isinstance(asset, dict) else {}
        values = lineups.get(team, pd.DataFrame())
        return values.to_dict("records") if isinstance(values, pd.DataFrame) else list(values or [])

    def split_player_name(value):
        parts = str(value or "").split()
        if len(parts) < 2:
            return "", parts[0] if parts else "TBD"
        suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
        last_start = len(parts) - 2 if parts[-1].lower().rstrip(".") in suffixes and len(parts) > 2 else len(parts) - 1
        return " ".join(parts[:last_start]), " ".join(parts[last_start:])

    def average_text(category, value):
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.isna(numeric):
            return "\u2014"
        if category in {"TS%", "2PT%", "3PT%", "FT%"}:
            return f"{float(numeric) * 100:.1f}%"
        if category == "+/-":
            return f"{float(numeric):+.1f}"
        return f"{float(numeric):.1f}"

    def draw_average_panel(box, team, values, team_color):
        left, top, right, bottom = box
        draw.rounded_rectangle(box, radius=15, fill=_recap_tint(team_color, 0.88), outline=_recap_tint(team_color, 0.58), width=2)
        team_label = _scoreboard_team_label(team)
        draw.text(((left + right) // 2, top + 27), team_label, font=_fit_scoreboard_font(draw, team_label, right - left - 24, 23, 16), fill=navy, anchor="mm")
        draw.text(((left + right) // 2, top + 57), "SEASON AVERAGES", font=_scoreboard_font(14, True), fill="#64748b", anchor="mm")
        labels = [("MP", "MP"), ("TS%", "TS%"), ("2PT%", "2P%"), ("3PT%", "3P%"), ("FT%", "FT%"), ("PTS", "PTS"), ("OREB", "OREB"), ("DREB", "DREB"), ("AST", "AST"), ("ST", "STL"), ("BLK", "BLK"), ("TO", "TOV*"), ("+/-", "+/-"), ("FPPG", "FPPG"), (None, "")]
        grid_top = top + 76
        column_width = (right - left - 18) // 3
        row_height = max(42, (bottom - grid_top - 9) // 5)
        for index, (category, label) in enumerate(labels):
            column, row_index = index // 5, index % 5
            x1 = left + 8 + column * column_width
            y1 = grid_top + row_index * row_height
            x2, y2 = x1 + column_width - 5, y1 + row_height - 4
            draw.rounded_rectangle((x1, y1, x2, y2), radius=6, fill="#ffffff")
            if category is None:
                continue
            draw.text((x1 + 12, (y1 + y2) // 2), label, font=_scoreboard_font(18, True), fill="#111827", anchor="lm")
            value_text = average_text(category, (values or {}).get(category))
            draw.text((x2 - 12, (y1 + y2) // 2), value_text, font=_fit_scoreboard_font(draw, value_text, column_width // 2 - 18, 27, 18), fill="#05070a", anchor="rm")

    def paste_player_photo(content, box):
        if not content:
            return False
        try:
            photo = Image.open(BytesIO(content)).convert("RGBA")
            left, top, right, bottom = box
            photo.thumbnail((max(1, right - left), max(1, bottom - top)), Image.Resampling.LANCZOS)
            x = left + (right - left - photo.width) // 2
            y = bottom - photo.height
            image.paste(photo, (x, y), photo)
            return True
        except Exception:
            return False

    def draw_rounded_gradient(box, start_color, end_color, radius, white_mix=0.0):
        left, top, right, bottom = [int(value) for value in box]
        gradient_width, gradient_height = max(1, right - left), max(1, bottom - top)
        start = _recap_tint(start_color, white_mix) if white_mix else (start_color if isinstance(start_color, tuple) else _scoreboard_color(start_color))
        end = _recap_tint(end_color, white_mix) if white_mix else (end_color if isinstance(end_color, tuple) else _scoreboard_color(end_color))
        gradient = Image.new("RGB", (gradient_width, gradient_height))
        gradient_draw = ImageDraw.Draw(gradient)
        for x in range(gradient_width):
            blend = x / max(1, gradient_width - 1)
            color = tuple(round(a + (b - a) * blend) for a, b in zip(start, end))
            gradient_draw.line((x, 0, x, gradient_height), fill=color)
        mask = Image.new("L", (gradient_width, gradient_height), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, gradient_width - 1, gradient_height - 1), radius=radius, fill=255)
        image.paste(gradient, (left, top), mask)

    for feature_index in range(2):
        top = feature_start + feature_index * (feature_height + feature_gap)
        bottom = top + feature_height
        row = featured_matchups[feature_index] if feature_index < len(featured_matchups) else {}
        asset = featured_assets[feature_index] if feature_index < len(featured_assets) else {}
        team_a, team_b = str(row.get("TeamA", "TBD")), str(row.get("TeamB", "TBD"))
        color_a = _scoreboard_color(safe_team_info(team_a, "bg", "#64748b"))
        color_b = _scoreboard_color(safe_team_info(team_b, "bg", "#64748b"))
        draw_rounded_gradient((feature_left, top, feature_right, bottom), color_a, color_b, 22, white_mix=0.91)
        draw.rounded_rectangle((feature_left, top, feature_right, bottom), radius=22, outline="#cfd9e4", width=2)
        matchup_title = f"{_scoreboard_team_label(team_a)} ({row.get('TeamA_record', '—')})  @  {_scoreboard_team_label(team_b)} ({row.get('TeamB_record', '—')})"
        draw.text(((feature_left + feature_right) // 2, top + 42), matchup_title, font=_fit_scoreboard_font(draw, matchup_title, feature_right - feature_left - 140, 34, 22), fill=navy, anchor="mm")

        visual_top, visual_bottom = top + 72, top + 464
        content_left, content_right, slot_gap = feature_left + 22, feature_right - 22, 12
        average_width, uniform_width = 840, 190
        court_width = content_right - content_left - (average_width * 2 + uniform_width + slot_gap * 3)
        slot_widths = [average_width, average_width, uniform_width, court_width]
        slots, slot_left = [], content_left
        for slot_width in slot_widths:
            slots.append((slot_left, visual_top, slot_left + slot_width, visual_bottom))
            slot_left += slot_width + slot_gap
        team_averages = asset.get("team_averages", {}) if isinstance(asset, dict) else {}
        draw_average_panel(slots[0], team_a, team_averages.get(team_a, {}), color_a)
        draw_average_panel(slots[1], team_b, team_averages.get(team_b, {}), color_b)
        uniform_left, uniform_top, uniform_right, uniform_bottom = slots[2]
        uniform_gap = 8
        uniform_height = (uniform_bottom - uniform_top - uniform_gap) // 2
        uniform_boxes = [
            (uniform_left, uniform_top, uniform_right, uniform_top + uniform_height),
            (uniform_left, uniform_top + uniform_height + uniform_gap, uniform_right, uniform_bottom),
        ]
        for jersey_box, jersey_content, color in (
            (uniform_boxes[0], asset.get("road_jersey"), color_a),
            (uniform_boxes[1], asset.get("home_jersey"), color_b),
        ):
            draw.rounded_rectangle(jersey_box, radius=15, fill="#f8fafc", outline=_recap_tint(color, 0.55), width=2)
            _paste_scoreboard_asset(image, jersey_content, (jersey_box[0] + 4, jersey_box[1] + 4, jersey_box[2] - 4, jersey_box[3] - 4), padding=2)
        draw.rounded_rectangle(slots[3], radius=15, fill="#f8fafc", outline="#d7e1eb", width=2)
        _paste_scoreboard_asset(image, asset.get("court"), (slots[3][0] + 4, slots[3][1] + 4, slots[3][2] - 4, slots[3][3] - 4), padding=3)

        draw.text((feature_left + 24, top + 493), "PROJECTED STARTING LINEUPS", font=_scoreboard_font(25, True), fill=navy, anchor="lm")
        lineup_top = top + 512
        for team_index, (team, color) in enumerate(((team_a, color_a), (team_b, color_b))):
            band_top = lineup_top + team_index * 170
            band_left, band_right, band_bottom = feature_left + 24, feature_right - 24, band_top + 154
            secondary = _scoreboard_color(safe_team_info(team, "bg2", color))
            draw_rounded_gradient((band_left, band_top, band_right, band_bottom), color, secondary, 14)
            team_panel_width = 150
            draw.line((band_left + team_panel_width, band_top + 8, band_left + team_panel_width, band_bottom - 8), fill="#ffffff", width=3)
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), 104)
            if logo is not None:
                image.paste(logo, (band_left + (team_panel_width - logo.width) // 2, band_top + (band_bottom - band_top - logo.height) // 2), logo)
            players = lineup_rows(asset, team)[:5]
            while len(players) < 5:
                players.append({"display_player": "TBD", "lineup_position": ["PG", "SG", "SF", "PF", "C"][len(players)]})
            start_x = band_left + team_panel_width
            player_width = (band_right - start_x) / 5
            for player_index, player in enumerate(players):
                player_left = int(start_x + player_index * player_width)
                player_right = int(start_x + (player_index + 1) * player_width)
                center_x = (player_left + player_right) // 2
                if player_index:
                    draw.line((player_left, band_top + 8, player_left, band_bottom - 8), fill="#ffffff", width=2)
                headshot = str(player.get("headshot", "") or "")
                photo_content = _scoreboard_logo_bytes(headshot) if headshot else None
                pasted = paste_player_photo(photo_content, (player_left + 6, band_top + 2, player_right - 6, band_bottom - 36))
                if not pasted:
                    draw.ellipse((center_x - 42, band_top + 22, center_x + 42, band_top + 106), fill=_recap_tint(color, 0.70), outline="#ffffff", width=3)
                badge_left, badge_top = player_left + 10, band_top + 10
                draw.rounded_rectangle((badge_left, badge_top, badge_left + 54, badge_top + 38), radius=8, fill="#ffffff")
                position = str(player.get("lineup_position", player.get("slot", "")) or "")
                draw.text((badge_left + 27, badge_top + 19), position, font=_scoreboard_font(15, True), fill=navy, anchor="mm")
                player_name = str(player.get("display_player", "TBD")).upper()
                strip_top = band_bottom - 36
                draw.rectangle((player_left, strip_top, player_right, band_bottom), fill="#17131d")
                draw.text(
                    (center_x, strip_top + 18),
                    player_name,
                    font=_fit_scoreboard_font(draw, player_name, int(player_width) - 24, 22, 13),
                    fill="#ffffff",
                    anchor="mm",
                )

    generated = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now()).strftime("%b %d, %Y • %I:%M %p").replace(" 0", " ")
    draw.text((42, height - 22), f"MATCHUP PREVIEW • GENERATED {generated}", font=_scoreboard_font(12, True), fill="#718398", anchor="lm")
    draw.text((width - 42, height - 22), "SBCFBL WEEKLY PRIMER", font=_scoreboard_font(12, True), fill="#718398", anchor="rm")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()

def build_mobile_matchup_preview_image(
    matchups: pd.DataFrame,
    featured_matchups: list,
    featured_assets: list,
    season_label: str,
    period_label: str,
    generated_at=None,
) -> bytes:
    """Build a tall weekly preview with a compact slate and two featured games."""
    if matchups is None or matchups.empty:
        raise ValueError("No matchups are available to preview.")
    width, margin = 1080, 30
    header_height, slate_title_height, slate_row_height = 166, 52, 56
    feature_title_height, feature_height, feature_gap, footer_height = 58, 1420, 20, 48
    slate_height = slate_title_height + len(matchups) * slate_row_height + 24
    height = header_height + slate_height + feature_title_height + feature_height * 2 + feature_gap + footer_height
    image = Image.new("RGB", (width, height), "#f3f6fa")
    draw = ImageDraw.Draw(image)
    navy, orange = "#172033", "#f59e0b"

    draw.rectangle((0, 0, width, header_height), fill="#ffffff")
    draw.rounded_rectangle((margin, 28, margin + 60, 88), radius=14, fill=orange)
    draw.text((margin + 30, 58), "S", font=_scoreboard_font(31, True), fill=navy, anchor="mm")
    draw.text((margin + 82, 50), "MATCHUP PREVIEW", font=_scoreboard_font(32, True), fill=navy, anchor="lm")
    draw.text((margin + 82, 90), f"{season_label}  \u2022  {period_label}", font=_scoreboard_font(15, True), fill="#65778a", anchor="lm")
    draw.rounded_rectangle((width - 230, 116, width - margin, 154), radius=19, fill=navy)
    draw.text((width - 130, 135), f"{len(matchups)} GAMES", font=_scoreboard_font(14, True), fill="#ffffff", anchor="mm")

    feature_ids = {str(row.get("Game_ID", "")) for row in featured_matchups}
    slate = matchups.copy().sort_values([column for column in ["Type", "TeamB", "TeamA"] if column in matchups.columns]).reset_index(drop=True)
    cursor = header_height
    draw.rounded_rectangle((margin, cursor + 5, width - margin, cursor + slate_title_height - 5), radius=12, fill="#e9eff5")
    draw.text((margin + 18, cursor + 26), "WEEKLY SLATE", font=_scoreboard_font(19, True), fill=navy, anchor="lm")
    cursor += slate_title_height
    for index, (_, row) in enumerate(slate.iterrows()):
        top, bottom = cursor + index * slate_row_height, cursor + (index + 1) * slate_row_height - 4
        is_featured = str(row.get("Game_ID", "")) in feature_ids
        draw.rounded_rectangle((margin, top, width - margin, bottom), radius=9, fill="#fff8e6" if is_featured else "#ffffff", outline=orange if is_featured else "#dbe4ee", width=2)
        team_a, team_b = str(row.get("TeamA", "")), str(row.get("TeamB", ""))
        color_a = _scoreboard_color(safe_team_info(team_a, "bg", "#64748b"))
        color_b = _scoreboard_color(safe_team_info(team_b, "bg", "#64748b"))
        center_y = (top + bottom) // 2
        for team, x, color in ((team_a, margin + 38, color_a), (team_b, width - margin - 38, color_b)):
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), 38)
            if logo is not None:
                image.paste(logo, (x - logo.width // 2, center_y - logo.height // 2), logo)
            else:
                draw.ellipse((x - 17, center_y - 17, x + 17, center_y + 17), fill=color)
        name_a, name_b = _scoreboard_team_label(team_a), _scoreboard_team_label(team_b)
        matchup_line = f"{name_a} ({row.get('TeamA_record', '—')})  @  {name_b} ({row.get('TeamB_record', '—')})"
        draw.text(
            (width // 2, center_y),
            matchup_line,
            font=_fit_scoreboard_font(draw, matchup_line, width - margin * 2 - 125, 18, 10),
            fill=orange if is_featured else navy,
            anchor="mm",
        )
    cursor += len(slate) * slate_row_height + 24
    draw.text((margin, cursor + 28), "FEATURED MATCHUPS", font=_scoreboard_font(27, True), fill=navy, anchor="lm")
    draw.line((margin + 318, cursor + 28, width - margin, cursor + 28), fill="#cfd9e4", width=2)
    cursor += feature_title_height

    def lineup_rows(asset, team):
        lineups = asset.get("lineups", {}) if isinstance(asset, dict) else {}
        values = lineups.get(team, pd.DataFrame())
        return values.to_dict("records") if isinstance(values, pd.DataFrame) else list(values or [])

    def average_text(category, value):
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.isna(numeric):
            return "—"
        if category in {"TS%", "2PT%", "3PT%", "FT%"}:
            return f"{float(numeric) * 100:.1f}%"
        if category == "+/-":
            return f"{float(numeric):+.1f}"
        return f"{float(numeric):.1f}"

    def draw_average_panel(box, team, values, color):
        left, top, right, bottom = box
        draw.rounded_rectangle(box, radius=13, fill=_recap_tint(color, 0.87), outline=_recap_tint(color, 0.55), width=2)
        name = _scoreboard_team_label(team)
        draw.text((left + 14, top + 24), name, font=_fit_scoreboard_font(draw, name, right - left - 190, 21, 14), fill=navy, anchor="lm")
        draw.text((right - 14, top + 24), "SEASON AVERAGES", font=_scoreboard_font(13, True), fill="#334155", anchor="rm")
        labels = [("MP", "MP"), ("TS%", "TS%"), ("2PT%", "2P%"), ("3PT%", "3P%"), ("FT%", "FT%"), ("PTS", "PTS"), ("OREB", "OREB"), ("DREB", "DREB"), ("AST", "AST"), ("ST", "STL"), ("BLK", "BLK"), ("TO", "TOV*"), ("+/-", "+/-"), ("FPPG", "FPPG"), (None, "")]
        grid_top = top + 48
        column_width = (right - left - 16) // 3
        row_height = max(38, (bottom - grid_top - 8) // 5)
        for stat_index, (category, label) in enumerate(labels):
            column, row_index = stat_index // 5, stat_index % 5
            x1 = left + 7 + column * column_width
            y1 = grid_top + row_index * row_height
            x2, y2 = x1 + column_width - 4, y1 + row_height - 3
            draw.rounded_rectangle((x1, y1, x2, y2), radius=5, fill="#ffffff")
            if category is None:
                continue
            draw.text((x1 + 8, (y1 + y2) // 2), label, font=_scoreboard_font(15, True), fill="#111827", anchor="lm")
            value_text = average_text(category, (values or {}).get(category))
            draw.text((x2 - 8, (y1 + y2) // 2), value_text, font=_fit_scoreboard_font(draw, value_text, column_width // 2 - 10, 20, 14), fill="#05070a", anchor="rm")

    def split_name(value):
        parts = str(value or "").split()
        return (" ".join(parts[:-1]), parts[-1]) if len(parts) > 1 else ("", parts[0] if parts else "TBD")

    def paste_player_photo(content, box):
        if not content:
            return False
        try:
            photo = Image.open(BytesIO(content)).convert("RGBA")
            left, top, right, bottom = box
            photo.thumbnail((right - left, bottom - top), Image.Resampling.LANCZOS)
            image.paste(photo, (left + (right - left - photo.width) // 2, bottom - photo.height), photo)
            return True
        except Exception:
            return False

    def draw_rounded_gradient(box, start_color, end_color, radius, white_mix=0.0):
        left, top, right, bottom = [int(value) for value in box]
        gradient_width, gradient_height = max(1, right - left), max(1, bottom - top)
        start = _recap_tint(start_color, white_mix) if white_mix else (start_color if isinstance(start_color, tuple) else _scoreboard_color(start_color))
        end = _recap_tint(end_color, white_mix) if white_mix else (end_color if isinstance(end_color, tuple) else _scoreboard_color(end_color))
        gradient = Image.new("RGB", (gradient_width, gradient_height))
        gradient_draw = ImageDraw.Draw(gradient)
        for x in range(gradient_width):
            blend = x / max(1, gradient_width - 1)
            gradient_color = tuple(round(a + (b - a) * blend) for a, b in zip(start, end))
            gradient_draw.line((x, 0, x, gradient_height), fill=gradient_color)
        mask = Image.new("L", (gradient_width, gradient_height), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, gradient_width - 1, gradient_height - 1), radius=radius, fill=255)
        image.paste(gradient, (left, top), mask)

    for feature_index in range(2):
        top = cursor + feature_index * (feature_height + feature_gap)
        bottom = top + feature_height
        row = featured_matchups[feature_index] if feature_index < len(featured_matchups) else {}
        asset = featured_assets[feature_index] if feature_index < len(featured_assets) else {}
        team_a, team_b = str(row.get("TeamA", "TBD")), str(row.get("TeamB", "TBD"))
        color_a = _scoreboard_color(safe_team_info(team_a, "bg", "#64748b"))
        color_b = _scoreboard_color(safe_team_info(team_b, "bg", "#64748b"))
        name_a, name_b = _scoreboard_team_label(team_a), _scoreboard_team_label(team_b)
        draw_rounded_gradient((margin, top, width - margin, bottom), color_a, color_b, 18, white_mix=0.91)
        draw.rounded_rectangle((margin, top, width - margin, bottom), radius=18, outline="#cfd9e4", width=2)
        matchup_title = f"{name_a} ({row.get('TeamA_record', '—')})  @  {name_b} ({row.get('TeamB_record', '—')})"
        draw.text((width // 2, top + 42), matchup_title, font=_fit_scoreboard_font(draw, matchup_title, width - margin * 2 - 70, 28, 17), fill=navy, anchor="mm")

        team_averages = asset.get("team_averages", {}) if isinstance(asset, dict) else {}
        avg_left, avg_right = margin + 14, width - margin - 14
        avg_top, average_height, avg_gap = top + 72, 286, 10
        draw_average_panel((avg_left, avg_top, avg_right, avg_top + average_height), team_a, team_averages.get(team_a, {}), color_a)
        draw_average_panel((avg_left, avg_top + average_height + avg_gap, avg_right, avg_top + average_height * 2 + avg_gap), team_b, team_averages.get(team_b, {}), color_b)

        visual_top, visual_bottom = top + 664, top + 914
        uniform_width, uniform_gap = 190, 8
        uniform_height = (visual_bottom - visual_top - uniform_gap) // 2
        uniform_boxes = (
            (margin + 14, visual_top, margin + 14 + uniform_width, visual_top + uniform_height),
            (margin + 14, visual_top + uniform_height + uniform_gap, margin + 14 + uniform_width, visual_bottom),
        )
        for box, content, color in (
            (uniform_boxes[0], asset.get("road_jersey"), color_a),
            (uniform_boxes[1], asset.get("home_jersey"), color_b),
        ):
            draw.rounded_rectangle(box, radius=12, fill="#f8fafc", outline=_recap_tint(color, 0.55), width=2)
            _paste_scoreboard_asset(image, content, (box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4), padding=2)
        court_box = (margin + 14 + uniform_width + 12, visual_top, width - margin - 14, visual_bottom)
        draw.rounded_rectangle(court_box, radius=12, fill="#f8fafc", outline="#d7e1eb", width=2)
        _paste_scoreboard_asset(image, asset.get("court"), (court_box[0] + 4, court_box[1] + 4, court_box[2] - 4, court_box[3] - 4), padding=3)

        draw.text((margin + 14, top + 948), "PROJECTED STARTING LINEUPS", font=_scoreboard_font(23, True), fill=navy, anchor="lm")
        lineup_top = top + 970
        for team_index, (team, color) in enumerate(((team_a, color_a), (team_b, color_b))):
            band_top, band_bottom = lineup_top + team_index * 204, lineup_top + team_index * 204 + 190
            band_left, band_right, team_panel_width = margin + 14, width - margin - 14, 110
            secondary = _scoreboard_color(safe_team_info(team, "bg2", color))
            draw_rounded_gradient((band_left, band_top, band_right, band_bottom), color, secondary, 12)
            draw.line((band_left + team_panel_width, band_top + 8, band_left + team_panel_width, band_bottom - 8), fill="#ffffff", width=3)
            logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), 82)
            if logo is not None:
                image.paste(logo, (band_left + (team_panel_width - logo.width) // 2, band_top + (band_bottom - band_top - logo.height) // 2), logo)
            players = lineup_rows(asset, team)[:5]
            while len(players) < 5:
                players.append({"display_player": "TBD", "lineup_position": ["PG", "SG", "SF", "PF", "C"][len(players)]})
            start_x = band_left + team_panel_width
            player_width = (band_right - start_x) / 5
            for player_index, player in enumerate(players):
                player_left, player_right = int(start_x + player_index * player_width), int(start_x + (player_index + 1) * player_width)
                if player_index:
                    draw.line((player_left, band_top + 8, player_left, band_bottom - 8), fill="#ffffff", width=2)
                headshot = str(player.get("headshot", "") or "")
                if not paste_player_photo(_scoreboard_logo_bytes(headshot) if headshot else None, (player_left + 3, band_top + 3, player_right - 3, band_bottom - 36)):
                    center_x = (player_left + player_right) // 2
                    draw.ellipse((center_x - 38, band_top + 38, center_x + 38, band_top + 114), fill=_recap_tint(color, 0.72), outline="#ffffff", width=2)
                draw.rounded_rectangle((player_left + 6, band_top + 6, player_left + 48, band_top + 36), radius=5, fill="#ffffff")
                position = str(player.get("lineup_position", player.get("slot", "")) or "")
                draw.text((player_left + 27, band_top + 21), position, font=_scoreboard_font(10, True), fill=navy, anchor="mm")
                player_name = str(player.get("display_player", "TBD")).upper()
                draw.rectangle((player_left, band_bottom - 36, player_right, band_bottom), fill="#17131d")
                draw.text((
                    (player_left + player_right) // 2,
                    band_bottom - 18,
                ), player_name, font=_fit_scoreboard_font(draw, player_name, int(player_width) - 10, 16, 9), fill="#ffffff", anchor="mm")

    generated = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now()).strftime("%b %d  \u2022  %I:%M %p").replace(" 0", " ")
    draw.text((margin, height - 24), f"SBCFBL  \u2022  {generated}", font=_scoreboard_font(11, True), fill="#718398", anchor="lm")
    draw.text((width - margin, height - 24), "MATCHUP PREVIEW", font=_scoreboard_font(11, True), fill="#718398", anchor="rm")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def build_record_leader_announcement_image(
    team: str,
    statistic: str,
    new_leader: str,
    previous_leader: str,
    new_value,
    previous_value,
    new_leader_image: str = "",
    previous_leader_image: str = "",
    generated_at=None,
) -> bytes:
    """Create a portrait record-breaker announcement suited to desktop and mobile feeds."""
    width, height = 1080, 1350
    primary = _scoreboard_color(safe_team_info(team, "bg", "#172033"))
    secondary = _scoreboard_color(safe_team_info(team, "bg2", primary))
    navy = "#172033"
    image = Image.new("RGB", (width, height), "#f4f7fb")
    draw = ImageDraw.Draw(image)

    def paste_photo(source, box, cover=False, zoom=1.0, align_top=False):
        content = _scoreboard_logo_bytes(str(source or ""))
        if not content:
            return False
        try:
            photo = Image.open(BytesIO(content)).convert("RGBA")
            left, top, right, bottom = box
            target_width, target_height = right - left, bottom - top
            if cover:
                scale = max(target_width / max(1, photo.width), target_height / max(1, photo.height))
                resized = photo.resize((max(1, int(photo.width * scale)), max(1, int(photo.height * scale))), Image.Resampling.LANCZOS)
                crop_left = max(0, (resized.width - target_width) // 2)
                crop_top = max(0, resized.height - target_height)
                photo = resized.crop((crop_left, crop_top, crop_left + target_width, crop_top + target_height))
                image.paste(photo, (left, top), photo)
            else:
                scale = min(target_width / max(1, photo.width), target_height / max(1, photo.height)) * max(1.0, float(zoom))
                photo = photo.resize((max(1, int(photo.width * scale)), max(1, int(photo.height * scale))), Image.Resampling.LANCZOS)
                clipped = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
                paste_x = (target_width - photo.width) // 2
                paste_y = 0 if align_top else target_height - photo.height
                clipped.paste(photo, (paste_x, paste_y), photo)
                image.paste(clipped, (left, top), clipped)
            return True
        except Exception:
            return False

    def split_name(value):
        parts = str(value or "").split()
        return (" ".join(parts[:-1]), parts[-1]) if len(parts) > 1 else ("", parts[0] if parts else "")

    def record_value(value):
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.isna(numeric):
            return str(value or "—")
        if statistic in {"TS%", "2PT%", "3PT%", "FT%"}:
            return f"{float(numeric) * 100:.1f}%"
        if statistic == "+/-":
            return f"{float(numeric):+,.0f}"
        return f"{float(numeric):,.0f}" if float(numeric).is_integer() else f"{float(numeric):,.1f}"

    stat_label = {
        "GP": "GAMES PLAYED", "MP": "MINUTES PLAYED", "TS%": "TRUE SHOOTING",
        "2PTM": "TWO-POINT MAKES", "2PTA": "TWO-POINT ATTEMPTS", "2PT%": "TWO-POINT PERCENTAGE",
        "3PTM": "THREE-POINT MAKES", "3PTA": "THREE-POINT ATTEMPTS", "3PT%": "THREE-POINT PERCENTAGE",
        "FTM": "FREE THROWS MADE", "FTA": "FREE THROW ATTEMPTS", "FT%": "FREE THROW PERCENTAGE",
        "PTS": "POINTS", "OREB": "OFFENSIVE REBOUNDS", "DREB": "DEFENSIVE REBOUNDS",
        "AST": "ASSISTS", "ST": "STEALS", "BLK": "BLOCKS", "TO": "TURNOVERS", "+/-": "PLUS / MINUS",
    }.get(str(statistic), str(statistic))
    team_name = _scoreboard_team_name(team)
    first_name, last_name = split_name(new_leader)

    # Team-branded header.
    draw.rectangle((0, 0, width, 164), fill="#ffffff")
    draw.rectangle((0, 0, width, 12), fill=primary)
    logo = _scoreboard_logo_image(_scoreboard_logo_bytes(str(safe_team_info(team, "logo", "") or "")), 104)
    if logo is not None:
        image.paste(logo, (42, 35), logo)
    draw.text((166, 69), team_name.upper(), font=_fit_scoreboard_font(draw, team_name.upper(), 520, 31, 18), fill=navy, anchor="lm")
    draw.text((166, 112), "FRANCHISE RECORD BOOK", font=_scoreboard_font(14, True), fill="#718398", anchor="lm")
    draw.rounded_rectangle((width - 380, 48, width - 34, 116), radius=34, fill=primary)
    draw.text((width - 207, 82), "NEW ALL-TIME LEADER", font=_scoreboard_font(18, True), fill=_recap_contrast_text(primary), anchor="mm")

    # Hero field with a subtle team-color gradient.
    hero_top, hero_bottom = 164, 850
    start_color, end_color = _recap_tint(primary, 0.84), _recap_tint(secondary, 0.63)
    for y in range(hero_top, hero_bottom):
        blend = (y - hero_top) / max(1, hero_bottom - hero_top - 1)
        color = tuple(int(a + (b - a) * blend) for a, b in zip(start_color, end_color))
        draw.line((0, y, width, y), fill=color)
    draw.rectangle((0, hero_top, 16, hero_bottom), fill=primary)
    draw.text((58, 226), "A NEW STANDARD", font=_scoreboard_font(18, True), fill=primary, anchor="lm")
    draw.text((58, 284), str(statistic).upper(), font=_scoreboard_font(45, True), fill=navy, anchor="lm")
    draw.text((58, 352), stat_label, font=_fit_scoreboard_font(draw, stat_label, 420, 18, 11), fill="#526579", anchor="lm")
    if not paste_photo(new_leader_image, (300, hero_top + 8, width - 4, hero_bottom), zoom=1.30, align_top=True):
        draw.ellipse((600, 260, 1010, 670), fill=_recap_tint(primary, 0.54), outline="#ffffff", width=6)
    record_box = (48, 424, 438, 600)
    draw.rounded_rectangle(record_box, radius=34, fill=primary, outline=_recap_tint(primary, 0.30), width=4)
    draw.text(((record_box[0] + record_box[2]) // 2, 490), record_value(new_value), font=_fit_scoreboard_font(draw, record_value(new_value), 330, 96, 62), fill=_recap_contrast_text(primary), anchor="mm")
    draw.text(((record_box[0] + record_box[2]) // 2, 557), f"NEW {stat_label} RECORD", font=_fit_scoreboard_font(draw, f"NEW {stat_label} RECORD", 330, 18, 12), fill=_recap_contrast_text(primary), anchor="mm")

    # Player nameplate.
    draw.rectangle((0, 770, width, 982), fill=navy)
    draw.rectangle((0, 770, 18, 982), fill=primary)
    draw.text((56, 828), first_name.upper(), font=_fit_scoreboard_font(draw, first_name.upper(), 940, 31, 18), fill="#ffffff", anchor="lm")
    draw.text((52, 921), last_name.upper(), font=_fit_scoreboard_font(draw, last_name.upper(), 960, 76, 42), fill="#ffffff", anchor="lm")

    # Former record holder context keeps the achievement grounded in history.
    card = (34, 1014, width - 34, 1276)
    draw.rounded_rectangle(card, radius=22, fill="#ffffff", outline="#d7e1eb", width=2)
    draw.rounded_rectangle((52, 1032, 300, 1258), radius=18, fill=_recap_tint(primary, 0.89))
    if not paste_photo(previous_leader_image, (60, 1040, 292, 1252), cover=True):
        draw.ellipse((104, 1068, 248, 1212), fill=_recap_tint(primary, 0.56))
    draw.text((340, 1110), str(previous_leader).upper(), font=_fit_scoreboard_font(draw, str(previous_leader).upper(), 650, 38, 22), fill=navy, anchor="lm")
    draw.text((340, 1200), record_value(previous_value), font=_scoreboard_font(58, True), fill=primary, anchor="lm")

    generated = pd.Timestamp(generated_at if generated_at is not None else pd.Timestamp.now()).strftime("%b %d, %Y").replace(" 0", " ")
    draw.text((34, height - 30), f"SBCFBL  \u2022  {generated}", font=_scoreboard_font(11, True), fill="#718398", anchor="lm")
    draw.text((width - 34, height - 30), "HISTORY MADE", font=_scoreboard_font(11, True), fill=primary, anchor="rm")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def get_single_award(df: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame, df4: pd.DataFrame, Year: int, Award: str) -> pd.DataFrame:
    df = df[df["Award"] == Award]
    df = df[df["Year"] == Year]
    df = df.copy()
    df2 = df2.copy()
    df4 = df4.copy()
    df["_player_key"] = df["Winner"].apply(normalize_player_key)
    df2["_player_key"] = df2["name"].apply(normalize_player_key)
    df4["_player_key"] = df4["Player"].apply(normalize_player_key)
    df = df.merge(df2, how="left", on="_player_key")
    df3 = df3[df3["Year"] == Year]
    df3 = df3[df3["period"] == df3["period"].max()]
    df = df.merge(df3, how="left", left_on="fantraxId", right_on="id")
    df = df.merge(df4, how="left", on="_player_key")
    def get_team_logo(team_name, team_info):
        for city, info in team_info.items():
            full_name = f"{city} {info['nickname']}"
            if team_name == full_name:
                return info["logo"]
        return None 
    df["logo"] = df["team_name"].apply(lambda x: get_team_logo(x, team_info))
    df = df[["logo", "Winner", "Picture_Online"]]
    df = df.sort_values("Winner")
    return df

def get_team_award(df: pd.DataFrame, Year: int, Award: str) -> str:
    df = df[df["Award"] == Award]
    df = df[df["Year"] == Year]
    winner = df.iloc[0]["Winner"]
    if winner == "Not Awarded":
        logo = "https://pbs.twimg.com/media/HCRpyEUaQAAPORi?format=png&name=medium"
    else:
        logo = team_info.get(winner, {}).get("wordmark", "")
    return logo

def get_all_stars_award(df: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame, df4: pd.DataFrame, Year: int, Award: str) -> pd.DataFrame:
    df = df[df["Award"] == Award]
    df = df[df["Year"] == Year]
    df = df.copy()
    df2 = df2.copy()
    df4 = df4.copy()
    df["_player_key"] = df["Winner"].apply(normalize_player_key)
    df2["_player_key"] = df2["name"].apply(normalize_player_key)
    df4["_player_key"] = df4["Player"].apply(normalize_player_key)
    df = df.merge(df2, how="left", on="_player_key")
    df3 = df3[df3["Year"] == Year]
    df3 = df3[df3["period"] == df3["period"].max()]
    df = df.merge(df3, how="left", left_on="fantraxId", right_on="id")
    df = df.merge(df4, how="left", on="_player_key")
    def get_team_logo(team_name, team_info):
        for city, info in team_info.items():
            full_name = f"{city} {info['nickname']}"
            if team_name == full_name:
                return info["logo"]
        return None
    def get_team_conf(team_name, team_info):
        for city, info in team_info.items():
            full_name = f"{city} {info['nickname']}"
            if team_name == full_name:
                return info["conf"]
        return None 
    df["logo"] = df["team_name"].apply(lambda x: get_team_logo(x, team_info))
    df["conf"] = df["team_name"].apply(lambda x: get_team_conf(x, team_info))
    df = df[["logo", "Winner", "Picture_Online"]]
    df = df.sort_values("Winner")
    return df

def get_short_term_awards(df: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame, df4: pd.DataFrame, Year: int, Award: str) -> pd.DataFrame:
    df["Week"] = df["Award"].str.extract(
    r'(Week \d+|January|February|March|April|May|June|July|August|September|October|November|December)')[0]
    df["Award_clean"] = df["Award"].apply(
    lambda x: " ".join([x.split()[0], x.split()[-1]]))
    df = df[df["Award_clean"] == Award]
    df = df[df["Year"] == Year]
    df = df.copy()
    df2 = df2.copy()
    df4 = df4.copy()
    df["_player_key"] = df["Winner"].apply(normalize_player_key)
    df2["_player_key"] = df2["name"].apply(normalize_player_key)
    df4["_player_key"] = df4["Player"].apply(normalize_player_key)
    df = df.merge(df2, how="left", on="_player_key")
    df3 = df3[df3["Year"] == Year]
    df3 = df3[df3["period"] == df3["period"].max()]
    df = df.merge(df3, how="left", left_on="fantraxId", right_on="id")
    df = df.merge(df4, how="left", on="_player_key")
    def get_team_logo(team_name, team_info):
        for city, info in team_info.items():
            full_name = f"{city} {info['nickname']}"
            if team_name == full_name:
                return info["logo"]
        return None
    def get_team_conf(team_name, team_info):
        for city, info in team_info.items():
            full_name = f"{city} {info['nickname']}"
            if team_name == full_name:
                return info["conf"]
        return None 
    df["logo"] = df["team_name"].apply(lambda x: get_team_logo(x, team_info))
    df["conf"] = df["team_name"].apply(lambda x: get_team_conf(x, team_info))
    df = df[["Week", "logo", "Winner", "Picture_Online"]]
    df["Week"] = pd.Categorical(df["Week"], categories=["November", "December", "January", "February", "March"] +[f"Week {i}" for i in range(1, 39)],ordered=True)
    df = df.sort_values("Week")
    return df
 # f
def img_to_base64(path: str) -> str:
    try:
        data = Path(path).read_bytes()
        ext = Path(path).suffix.lstrip(".").lower()
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "svg": "svg+xml", "webp": "webp"}.get(ext, "png")
        return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"
    except Exception:
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

def render_scorebug(row):
    team_a = row["TeamA_Nickname"]
    team_b = row["TeamB_Nickname"]
    logo_a = row["TeamA_logo"]
    logo_b = row["TeamB_logo"]
    record_a = row["TeamA_record"]
    record_b = row["TeamB_record"]
    score_a = row["TeamA_Score"]
    score_b = row["TeamB_Score"]
    color_a = row["TeamA_color"]
    color_b = row["TeamB_color"]
    logo_a_src = img_to_base64(logo_a) if not logo_a.startswith("http") else logo_a
    logo_b_src = img_to_base64(logo_b) if not logo_b.startswith("http") else logo_b


    html = f"""<!DOCTYPE html>
        <html>
        <head>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;800&family=Barlow:wght@400;500&display=swap" rel="stylesheet">
        <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            background: transparent;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 160px;
            font-family: 'Barlow Condensed', sans-serif;
        }}

        .scorebug {{
            position: relative;
            width: 420px;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 0 0 1px rgba(255,255,255,0.08), 0 24px 64px rgba(0,0,0,0.6);
            background: #0d0d0f;
        }}

        .team-row {{
            position: relative;
            display: flex;
            align-items: center;
            padding: 0 20px 0 24px;
            height: 72px;
            gap: 14px;
            overflow: hidden;
        }}

        .team-row::before {{
            content: '';
            position: absolute;
            inset: 0;
            opacity: 0.13;
            pointer-events: none;
        }}

        .row-a::before {{ background: radial-gradient(ellipse at 30% 50%, {color_a} 0%, transparent 70%); }}
        .row-b::before {{ background: radial-gradient(ellipse at 30% 50%, {color_b} 0%, transparent 70%); }}

        .row-a::after {{
            content: '';
            position: absolute;
            left: 0; right: 0; top: 0;
            height: 2px;
            background: linear-gradient(90deg, {color_a}, transparent 80%);
            box-shadow: 0 0 12px 2px {color_a};
            animation: glowPulse 2.4s ease-in-out infinite;
        }}

        .row-b::after {{
            content: '';
            position: absolute;
            left: 0; right: 0; bottom: 0;
            height: 2px;
            background: linear-gradient(90deg, {color_b}, transparent 80%);
            box-shadow: 0 0 12px 2px {color_b};
            animation: glowPulse 2.4s ease-in-out infinite 1.2s;
        }}

        @keyframes glowPulse {{
            0%, 100% {{ opacity: 1; }}
            50%       {{ opacity: 0.4; }}
        }}

        .divider {{
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 20%, rgba(255,255,255,0.15) 80%, transparent 100%);
        }}

        .accent-stripe {{
            position: absolute;
            left: 0; top: 0; bottom: 0;
            width: 4px;
        }}
        .row-a .accent-stripe {{ background: {color_a}; box-shadow: 2px 0 12px 0 {color_a}; }}
        .row-b .accent-stripe {{ background: {color_b}; box-shadow: 2px 0 12px 0 {color_b}; }}

        .team-logo {{
            width: 44px;
            height: 44px;
            object-fit: contain;
            flex-shrink: 0;
            filter: drop-shadow(0 2px 8px rgba(0,0,0,0.5));
        }}

        .team-info {{ flex: 1; min-width: 0; }}

        .team-name {{
            font-size: 15.8px;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: #ffffff;
            line-height: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .team-record {{
            font-family: 'Barlow', sans-serif;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.06em;
            color: rgba(255,255,255,0.45);
            margin-top: 3px;
            text-transform: uppercase;
        }}

        .team-score {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #ffffff;
            min-width: 52px;
            text-align: right;
            line-height: 1;
            text-shadow: 0 0 24px rgba(255,255,255,0.18);
        }}
        </style>
        </head>
        <body>
        <div class="scorebug">
            <div class="team-row row-a">
            <div class="accent-stripe"></div>
            <img class="team-logo" src="{logo_a_src}" alt="{team_a}" />
            <div class="team-info">
                <div class="team-name">{team_a}</div>
                <div class="team-record">{record_a}</div>
            </div>
            <div class="team-score">{score_a}</div>
            </div>
            <div class="divider"></div>
            <div class="team-row row-b">
            <div class="accent-stripe"></div>
            <img class="team-logo" src="{logo_b_src}" alt="{team_b}" />
            <div class="team-info">
                <div class="team-name">{team_b}</div>
                <div class="team-record">{record_b}</div>
            </div>
            <div class="team-score">{score_b}</div>
            </div>
        </div>
        </body>
        </html>"""
    components.html(html, height=180, scrolling=False)

def get_matchup_score(team_a: str, team_b: str, df: pd.DataFrame):
    if df is None or df.empty or "Team" not in df.columns:
        return None, None
    matchup = df[df["Team"].isin([team_a, team_b])].copy()
    if matchup.shape[0] != 2:
        return None, None
    matchup = matchup.set_index("Team").loc[[team_a, team_b]].reset_index()
    weights = {"PTS": 61, "AST": 41, "TS%": 41, "2PT%": 31, "+/-": 31, "3PT%": 31, "BLK": 31, "DREB": 31, "OREB": 31, "ST": 31, "FT%": 21, "MP": 11, "TO": 21}
    if any(stat not in matchup.columns for stat in weights):
        return None, None
    activity = matchup[list(weights)].apply(pd.to_numeric, errors="coerce").fillna(0).abs().to_numpy().sum()
    if activity == 0:
        return 0, 0
    team_a_score = 0
    team_b_score = 0
    for stat, weight in weights.items():
        val_a = matchup.loc[0, stat]
        val_b = matchup.loc[1, stat]
        if stat == "TO":
            if val_a < val_b:
                team_a_score += weight
            elif val_b < val_a:
                team_b_score += weight
            else:
                team_a_score += weight / 2
                team_b_score += weight / 2
        else:
            if val_a > val_b:
                team_a_score += weight
            elif val_b > val_a:
                team_b_score += weight
            else:
                team_a_score += weight / 2
                team_b_score += weight / 2
    return team_a_score, team_b_score

def saved_matchup_score(value):
    if pd.isna(value):
        return None
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return value

def get_weekly_scores_df(SelectedYear, SelectedPeriod, df, df2, df3):
    df = df[(df["Year"] == SelectedYear) & (df["Period"] == SelectedPeriod)].copy()
    if df.empty:
        return df
    df["TeamA_Nickname"] = df["TeamA"].apply(lambda x: safe_team_info(x, "nickname", str(x)))
    df["TeamB_Nickname"] = df["TeamB"].apply(lambda x: safe_team_info(x, "nickname", str(x)))
    df["TeamA_logo"] = df["TeamA"].apply(lambda x: safe_team_info(x, "logo"))
    df["TeamB_logo"] = df["TeamB"].apply(lambda x: safe_team_info(x, "logo"))
    df["TeamA_color"] = df["TeamA"].apply(lambda x: safe_team_info(x, "bg", "#111827"))
    df["TeamB_color"] = df["TeamB"].apply(lambda x: safe_team_info(x, "bg", "#111827"))
    conditions = [df["Type"] == "Regular Season", df["Round"] == "Group Stage", (df["Type"] == "In-Season Tournament") & (df["Round"] != "Group Stage"), df["Type"].isin(["Play-In", "Playoffs"])]
    choices = ["Record", "GSRecord", "IST Seed", "Playoff Seed"]
    df["lookup_col"] = np.select(conditions, choices, default=None)
    standings_cols = ["Year", "Period", "Team", "Record", "GSRecord", "IST Seed", "Playoff Seed"]
    if df3 is not None and not df3.empty and all(col in df3.columns for col in ["Year", "Period", "Team"]):
        year_rows = df3[df3["Year"] == SelectedYear].copy()
        available_periods = pd.to_numeric(year_rows["Period"], errors="coerce")
        if (available_periods == SelectedPeriod).any():
            chosen_period = SelectedPeriod
        elif (available_periods == 99).any():
            chosen_period = 99
        else:
            prior_periods = available_periods[available_periods < SelectedPeriod].dropna()
            chosen_period = prior_periods.max() if not prior_periods.empty else None
        df3 = year_rows[available_periods == chosen_period].copy() if chosen_period is not None else year_rows.iloc[0:0].copy()
        for col in standings_cols:
            if col not in df3.columns:
                df3[col] = None
        df3_melted = df3.melt(id_vars="Team", value_vars=["Record", "GSRecord", "IST Seed", "Playoff Seed"], var_name="lookup_col", value_name="value")
        df = df.merge(df3_melted, left_on=["TeamA", "lookup_col"], right_on=["Team", "lookup_col"], how="left")
        df = df.rename(columns={"value": "TeamA_record"})
        df = df.drop(columns=["Team"])
        df = df.merge(df3_melted, left_on=["TeamB", "lookup_col"], right_on=["Team", "lookup_col"],how="left")
        df = df.rename(columns={"value": "TeamB_record"})
        df = df.drop(columns=["Team"])
    else:
        df["TeamA_record"] = None
        df["TeamB_record"] = None
    def compute_scores(row):
        team_a = row["TeamA"]
        team_b = row["TeamB"]
        score_a, score_b = get_matchup_score(team_a, team_b, df2)
        if score_a is None or score_b is None:
            score_a = saved_matchup_score(row.get("TeamAScore"))
            score_b = saved_matchup_score(row.get("TeamBScore"))
        return pd.Series([score_a, score_b])
    df[["TeamA_Score", "TeamB_Score"]] = df.apply(compute_scores, axis=1)
    order = ["Regular Season", "In-Season Tournament", "Play-In", "Playoffs"]
    df["Type"] = pd.Categorical(df["Type"], categories=order, ordered=True)
    df = df.sort_values(["Type", "TeamB_Nickname"], ascending=[True, True])    
    return df

def get_standings_table(df, SelectedPeriod, SelectedYear, Conference):
    team_to_conf = {team: info["conf"] for team, info in team_info.items()}
    df["Conference"] = df["Team"].map(team_to_conf)
    mask = (df["Year"] == SelectedYear) & (df["Period"] == SelectedPeriod)
    if not mask.any():
        SelectedPeriod = 99
    df = df[(df["Year"] == SelectedYear) & (df["Period"] == SelectedPeriod) & (df["Conference"] == Conference)].copy()
    df[["wins", "losses"]] = df["Record"].str.split("-", expand=True).astype(int)
    df["Win %"] = df["wins"] / (df["wins"] + df["losses"])   
    max_wins = df["wins"].max()
    df["GB"] = (max_wins - df["wins"]).astype(float).round(1).astype(str)    
    df.loc[df["GB"] == "0.0", "GB"] = "—"
    team_to_logo = {team: info["logo"] for team, info in team_info.items()}
    df["Logo"] = df["Team"].map(team_to_logo)
    df = df[["Logo", "Record", "Win %", "GB", "ConfRecord", "DivRecord"]]    
    df = df.sort_values("Win %", ascending=False).reset_index(drop=True)
    df["Win %"] = (df["Win %"] * 100).round(2).astype(str) + "%"
    df = df.rename(columns={"ConfRecord": "Conf. Record", "DivRecord": "Div. Record"})
    green = '#6B9B6B'
    yellow = '#D4B963'
    red = '#CC8888'

    def tier_color(row):
        if row.name <= 5:
            color = green
        elif row.name <= 9:
            color = yellow
        else:
            color = red

        return [f'background-color: {color}'] * len(row)
    df = df.style.apply(tier_color, axis=1).hide(axis="index")
    return df

def get_team_schedule(df, SelectedTeam, SelectedYear):
    df = get_all_time_schedule()
    df = df[df["Year"] == SelectedYear].copy()
    df = df[(df["TeamA"].str.contains(SelectedTeam)) | (df["TeamB"].str.contains(SelectedTeam))]
    df["Team"] = SelectedTeam
    selected_is_home = df["TeamB"].str.contains(SelectedTeam, na=False)
    df["Opponent"] = np.where(selected_is_home, df["TeamA"], df["TeamB"])
    df["Location"] = np.where(selected_is_home, "vs", "@")
    df["TeamScore"] = np.where(selected_is_home, df["TeamBScore"], df["TeamAScore"])
    df["OpponentScore"] = np.where(selected_is_home, df["TeamAScore"], df["TeamBScore"])
    df["Result"] = np.where(df["TeamScore"] > df["OpponentScore"], "W", "L")
    df["Score"] = df["TeamScore"].astype(str) + "-" + df["OpponentScore"].astype(str)
    team_to_logo = {team: info["logo"] for team, info in team_info.items()}
    df["Logo"] = df["Opponent"].map(team_to_logo)
    green = '#6B9B6B'
    red = '#CC8888'
    def tier_color(row):
        color = green if row["Result"] == "W" else red
        return [f'background-color: {color}'] * len(row)
    df = df[["Period", "Location", "Logo", "Score", "Result"]]
    df = df.style.apply(tier_color, axis=1).hide(axis="index")
    return df

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def get_team_mileage(SelectedTeam, Year, df):
    team_df = df[(df["Year"] == Year) & (df["Type"].isin(["Regular Season", "In-Season Tournament"])) & ((df["TeamA"] == SelectedTeam) | (df["TeamB"] == SelectedTeam))].copy()
    type_order = {"Regular Season": 0, "In-Season Tournament": 1}
    team_df["TypeOrder"] = team_df["Type"].map(type_order)
    team_df = team_df.sort_values(["Period", "TypeOrder"]).reset_index(drop=True)
    team_df.drop(columns="TypeOrder", inplace=True)
    selected_info = team_info.get(SelectedTeam)
    if not selected_info:
        return 0, 0
    current_lat = selected_info["lat"]
    current_lon = selected_info["lon"]
    miles_per_game = []
    for _, row in team_df.iterrows():
        dest = SelectedTeam if row["TeamB"] == SelectedTeam else row["TeamB"]
        dest_info = team_info.get(dest)
        if not dest_info:
            continue
        dest_lat = dest_info["lat"]
        dest_lon = dest_info["lon"]
        miles = haversine(current_lat, current_lon, dest_lat, dest_lon)
        miles_per_game.append(miles)
        current_lat, current_lon = dest_lat, dest_lon
    team_df["MilesThisGame"] = miles_per_game
    team_df = team_df[["TeamA", "TeamB", "MilesThisGame"]]
    total_miles = team_df["MilesThisGame"].sum()
    num_flights = (team_df["MilesThisGame"] > 0).sum()
    return total_miles, num_flights

def arc_points(lat1, lon1, lat2, lon2, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        lat = lat1 + t * (lat2 - lat1)
        lon = lon1 + t * (lon2 - lon1)
        bow = math.sin(math.pi * t) * 3
        pts.append([lon, lat + bow])
    return pts

def plot_team_flights(SelectedTeam, Year, df):
    team_df = df[(df["Year"] == Year) & (df["Type"].isin(["Regular Season", "In-Season Tournament"])) & ((df["TeamA"] == SelectedTeam) | (df["TeamB"] == SelectedTeam))].copy()
    type_order = {"Regular Season": 0, "In-Season Tournament": 1}
    team_df["TypeOrder"] = team_df["Type"].map(type_order)
    team_df = team_df.sort_values(["Period", "TypeOrder"]).reset_index(drop=True)
    home = team_info.get(SelectedTeam)
    if not home:
        return folium.Map(location=[39.5, -98.35], zoom_start=4, tiles="CartoDB Positron", zoom_control=False)
    team_color = home["bg"]
    team_color2 = home["bg2"]
    current_lat = home["lat"]
    current_lon = home["lon"]
    m = folium.Map(location=[current_lat, current_lon], zoom_start=4, tiles="CartoDB Positron", zoom_control=False)
    visited = set()
    for _, row in team_df.iterrows():
        dest = SelectedTeam if row["TeamB"] == SelectedTeam else row["TeamB"]
        dest_info = team_info.get(dest)
        if not dest_info:
            continue
        dest_lat = dest_info["lat"]
        dest_lon = dest_info["lon"]
        if dest_lat != current_lat or dest_lon != current_lon:
            folium.PolyLine(locations=[[current_lat, current_lon], [dest_lat, dest_lon]], color=team_color, weight=3, opacity=0.8).add_to(m)
        if dest not in visited:
            folium.CircleMarker(location=[dest_lat, dest_lon], radius=5, color=team_color2, fill=True, fill_color=team_color, fill_opacity=0.9, tooltip=dest).add_to(m)
            visited.add(dest)
        current_lat, current_lon = dest_lat, dest_lon
    return m
