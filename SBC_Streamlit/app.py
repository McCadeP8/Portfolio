#import os
#os.chdir("SBC_Streamlit")

import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium
import pandas as pd
import altair as alt
import pyarrow.parquet as pq
import re as re
import json
import math
import unicodedata
import matplotlib.pyplot as plt
from matplotlib.ft2font import FT2Font
import requests
from datetime import datetime, date, time
from html import escape
from pathlib import Path
from textwrap import dedent
from zoneinfo import ZoneInfo
from functions import read_csv_snapshot, get_data, get_pictures, active_players, style_salaries, overseas_players, free_agent_players, dead_players, draft_retired_players, active_player_n, inactive_player_n, get_exceptions, exception_table, get_cap_total, get_tax_total, get_base_cap, team_hard_cap, team_hard_cap_n, base_fee, amount_paid, net_fee, luxury_fee, trade_restrictions, active_players_all, inactive_players_all, dead_players_all, draft_rights_all, retired_all, all_free_agents, trade_restrictions_all, overall_cap_table, unit_payout, tax_payout_champ, tax_payout_split, style_overall_cap, get_draft_picks, full_draft_picks, swap_draft_picks, split_draft_picks, locked_draft_picks, original_draft_picks, touched_draft_picks, all_full_draft_picks, all_swap_draft_picks, all_split_draft_picks, all_locked_draft_picks, data_picture_check, data_roster_check, tradeable_players_in, tradeable_players_out, tradeable_picks_in, tradeable_picks_out, players_out_table, players_in_table, picks_out_table, picks_in_table, net_players_check, no_cash, tpe_st_check, under_100_percent_check, no_bae_mle_check, stepien_check, tradeable_exceptions_in, tradeable_exceptions_out, exceptions_in_table, exceptions_out_table, data_missing_salary_check, hard_cap_check, stepien_data_check, get_fantrax_roster, get_fantrax_players, fantrax_players_check, fantrax_roster_check, fantrax_positional_check, current_draft, get_standings, get_draft_history, past_draft, lottery_table, get_matchup_stats, format_live_stats_df, team_stats_line_chart, current_matchup_period, team_with_ranks, matchup_scoreboard, get_all_time_schedule, get_opponents, get_all_time_team_stats, get_all_time_rosters, get_award_history, get_single_award, get_team_award_history, get_team_award, get_all_stars_award, get_short_term_awards, render_scorebug, get_weekly_scores_df, get_standings_table, get_team_schedule, plot_team_flights, get_team_mileage, get_period_calendar
# no_aggregation_check, salary_trade_check, tpe_check, bae_mle_check, player_agg_check, create_tpe_check, new_trade_rest_check, old_team_check, team_with_ranks
from data import team_info, type_colors, current_salary_cap, current_luxury_tax, current_apron_1, current_apron_2, current_year, columns_order, year_offset, max_cash, max_minimum, period, stat_to_scipId
from court_engine import CourtConfig, draw_branded_court
from jersey_engine import JerseyConfig, draw_uniform


if not hasattr(st, "_sbc_native_metric"):
    st._sbc_native_metric = st.metric

_native_metric = st._sbc_native_metric

if not hasattr(st, "_sbc_native_dataframe"):
    st._sbc_native_dataframe = st.dataframe

_native_dataframe = st._sbc_native_dataframe


def _format_metric_money(value, decimals=0):
    try:
        if value is None or value == "":
            return value
        numeric_value = float(value)
        precision = int(decimals)
        if numeric_value < 0:
            return f"-${abs(numeric_value):,.{precision}f}"
        return f"${numeric_value:,.{precision}f}"
    except (TypeError, ValueError):
        return value


def _sbc_metric(*args, **kwargs):
    metric_format = kwargs.pop("format", None)
    kwargs.pop("delta_arrow", None)
    metric_decimals = 0
    if metric_format == "dollar2":
        metric_format = "dollar"
        metric_decimals = 2
    if metric_format == "dollar":
        if "value" in kwargs:
            kwargs["value"] = _format_metric_money(kwargs["value"], metric_decimals)
        elif len(args) >= 2:
            args = (args[0], _format_metric_money(args[1], metric_decimals), *args[2:])
        if "delta" in kwargs:
            kwargs["delta"] = _format_metric_money(kwargs["delta"], metric_decimals)
        elif len(args) >= 3:
            args = (*args[:2], _format_metric_money(args[2], metric_decimals), *args[3:])
    return _native_metric(*args, **kwargs)


if getattr(st.metric, "__name__", "") != "_sbc_metric":
    st.metric = _sbc_metric


def _sbc_dataframe(*args, **kwargs):
    if kwargs.get("width") == "stretch":
        kwargs.pop("width", None)
        kwargs.setdefault("use_container_width", True)
    if kwargs.get("height") == "content":
        kwargs.pop("height", None)
    return _native_dataframe(*args, **kwargs)


if getattr(st.dataframe, "__name__", "") != "_sbc_dataframe":
    st.dataframe = _sbc_dataframe

def render_html(markup):
    markup = dedent(str(markup)).strip()
    markup = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(markup, unsafe_allow_html=True)


APP_DIR = Path(__file__).resolve().parent

TEAM_FONTS = {
    "Albuquerque": "Amatic SC",
    "Anaheim": "Baloo 2",
    "Anchorage": "Fjalla One",
    "Austin": "Creepster",
    "Baltimore": "Lobster",
    "Birmingham": "Rye",
    "Boise": "Neucha",
    "Buffalo": "Teko",
    "Cincinnati": "Satisfy",
    "Columbus": "Arvo",
    "Des Moines": "Cabin Sketch",
    "El Paso": "Pathway Gothic One",
    "Honolulu": "Dancing Script",
    "Jacksonville": "Pacifico",
    "Kentucky": "Playfair Display",
    "Lansing": "Ubuntu",
    "Lincoln": "Bebas Neue",
    "Little Rock": "Alfa Slab One",
    "Manchester": "Quicksand",
    "Nashville": "Tangerine",
    "Pittsburgh": "Roboto Slab",
    "Providence": "IM Fell English",
    "San Diego": "Comfortaa",
    "San Jose": "Indie Flower",
    "Seattle": "Poppins",
    "St. Louis": "Oswald",
    "Tampa Bay": "Parisienne",
    "Tulsa": "Permanent Marker",
    "Vancouver": "Shadows Into Light",
    "Vegas": "Audiowide",
}

TEAM_ABBREVIATIONS = {
    "Albuquerque": "ABQ",
    "Anaheim": "ANA",
    "Anchorage": "ANC",
    "Austin": "AUS",
    "Baltimore": "BAL",
    "Birmingham": "BIR",
    "Boise": "BOI",
    "Buffalo": "BUF",
    "Cincinnati": "CIN",
    "Columbus": "COL",
    "Des Moines": "DMR",
    "El Paso": "EPV",
    "Honolulu": "HON",
    "Jacksonville": "JAX",
    "Kentucky": "KEN",
    "Lansing": "LAN",
    "Lincoln": "LIN",
    "Little Rock": "LBF",
    "Manchester": "MAN",
    "Nashville": "NSH",
    "Pittsburgh": "PIT",
    "Providence": "PRO",
    "San Diego": "SDS",
    "San Jose": "SJS",
    "Seattle": "SEA",
    "St. Louis": "STL",
    "Tampa Bay": "TBF",
    "Tulsa": "TUL",
    "Vancouver": "VAN",
    "Vegas": "VBJ",
}

LEAGUE_LOGO = "https://pbs.twimg.com/media/HLq5ARaaQAA4KwY?format=png&name=small"
LEAGUE_PRIMARY = "#09438E"
LEAGUE_SECONDARY = "#009C3D"
LEAGUE_FONT = "Bungee"
DRAFT_SILHOUETTE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 96 96'%3E%3Crect width='96' height='96' rx='48' fill='%23111827'/%3E%3Ccircle cx='48' cy='35' r='17' fill='%23f8fafc'/%3E%3Cpath d='M18 83c4-20 17-31 30-31s26 11 30 31' fill='%23f8fafc'/%3E%3C/svg%3E"
DRAFT_HISTORY_CSV_URL = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1546613902"
FREE_AGENCY_PASSWORD = "VovEmUmawrlcreMuzEtR"
APP_DIR = Path(__file__).resolve().parent
FREE_AGENT_BIDS_PATH = APP_DIR / "free_agent_bids.csv"
FREE_AGENCY_LEAGUE_VIEW_URL = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1031971950"
FREE_AGENCY_SURVEY_URL = "https://qfreeaccountssjc1.az1.qualtrics.com/jfe/form/SV_0ia5Die66G0LD14"

FREE_AGENCY_TEAM_CODES = {
    "CruKEvubububRaSlPLBr": "Albuquerque",
    "XEWROnikohlbrUprujIV": "Anaheim",
    "prLbruWrIChaXlmLqeha": "Anchorage",
    "pajUchopHiSpuMokLYEd": "Austin",
    "muqicuzlstlbrIkEkokU": "Baltimore",
    "KimlPiFRipLpiCuphETr": "Birmingham",
    "sWlchUbUbRlsigudRObR": "Boise",
    "koplfUglzinoThiwaspi": "Buffalo",
    "cicIbawijoyOsTecetho": "Cincinnati",
    "hEylzEcrichupRoJavuP": "Columbus",
    "spejuxLRedeYitrlBrlj": "Des Moines",
    "fafrlvUfathuyicichld": "El Paso",
    "tlZlbeRoCrlchosutuWo": "Honolulu",
    "phAdrUpUflNUgesOchIF": "Jacksonville",
    "boPhiCriWAKUfephlJlc": "Kentucky",
    "CRLSlpRlbrLQlcHlqaho": "Lansing",
    "SeTriphuKusPlpriJeth": "Lincoln",
    "faCHaswocrlsiVlYuplR": "Little Rock",
    "hespatRlBEwOrLSwatRa": "Manchester",
    "maqataxlxIclpRujUPHL": "Nashville",
    "PhOzithIdrUflZuCoprU": "Pittsburgh",
    "hOMaSepexeGEniGiswOd": "Providence",
    "bLmlrLXeThiyaboBLziG": "San Diego",
    "yeprIQlcHaxuSWePrIsW": "San Jose",
    "niFasiwewoVowlplkihi": "Seattle",
    "DroxUswebudofethOPrl": "St. Louis",
    "qOtrExicohuBRacoquca": "Tampa Bay",
    "cltroxUsToswojikubit": "Tulsa",
    "tuthUsajudrowIbesopr": "Vancouver",
    "tuthUsajudrowlbesopr": "Vancouver",
    "VovEmUmawrlcreMuzEtR": "Vegas",
    "TyF4LNkBNtAkEB4It2Hg": "Albuquerque",
    "FcLJLFN7i8QQiLYTzKWo": "Anaheim",
    "dGrUraAPmcqhK0m6ARWh": "Anchorage",
    "ZSHHRH81oj8sMcEdoY1l": "Austin",
    "D1B6j2xcdgHQPMdF4QOq": "Baltimore",
    "bxVOCQ1S5Q8pPrEU57xc": "Birmingham",
    "BxVOCQ1S5Q8pPrEU57xc": "Birmingham",
    "I6Pg736WoKYeVeI6U4e1": "Boise",
    "5162yikwsApWCLrX4UJs": "Buffalo",
    "jMYWLR2XrzlL7I4rmUOU": "Cincinnati",
    "rdQy1hcby0rS88x8ZNFz": "Columbus",
    "foRQTbf7X7sPzwToUqAy": "Des Moines",
    "MJ41zvbgwrKeZoTB7BWS": "El Paso",
    "HMUEn4W03Foc41CAECZm": "Honolulu",
    "45voC1imU3u8KP5dUwsf": "Jacksonville",
    "84F4QNW03LX2AI0s02dy": "Kentucky",
    "cFUiAg0LIxSESHeKgN1B": "Lansing",
    "VoCm4cWh5PZm9VehkM4x": "Lincoln",
    "bEvPh9hsVSyir9NSr6tA": "Little Rock",
    "BzyHZbJO6jiPO80dACaC": "Manchester",
    "aU1nz37NW5o0JIHilRH7": "Nashville",
    "t5xL0w4jV8TpJwYGpjbx": "Pittsburgh",
    "ZsszJyXaxCGg5E8vAb86": "Providence",
    "ZsszJyXaxCGg5E8vAb96": "Providence",
    "R0v8umk3ZaNp6OXaPYnB": "San Diego",
    "MQwfNLhUakQ13r7Ft1M4": "San Jose",
    "jsY6XYU5mzjSk7laetU3": "Seattle",
    "A8FpUrhgzTRMN1IOK4O9": "St. Louis",
    "NPme2qXwpi0LBcY73EFF": "Tampa Bay",
    "iIwpWRN1I9fkcvki1y8N": "Tulsa",
    " iIwpWRN1I9fkcvki1y8": "Tulsa",
    "BMro1UdTd6X488MU7ket": "Vancouver",
    "M8n43ZSLcJGCfWeF0RFn": "Vegas",
}

st.set_page_config(
    page_title="SBC Cap Sheets",
    page_icon=":basketball:",
    layout="wide")

def load_required_data(label, loader):
    try:
        return loader()
    except KeyError as exc:
        st.error(f"{label} is missing an expected field: {exc}")
        st.stop()
    except Exception as exc:
        st.error(f"{label} could not be loaded right now: {type(exc).__name__}: {exc}")
        st.stop()


def load_optional_data(label, loader):
    try:
        return loader()
    except Exception as exc:
        st.warning(f"{label} could not be loaded right now: {exc}")
        return pd.DataFrame()


def load_live_draft_history():
    # Manual draft-board refresh bypasses the cached draft history loader.
    return read_csv_snapshot("draft_history_live", f"{DRAFT_HISTORY_CSV_URL}&refresh={datetime.now().timestamp()}", ttl_seconds=60)


def ensure_columns(data, columns):
    table = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame()
    for col in columns:
        if col not in table.columns:
            table[col] = pd.Series(dtype="object")
    return table


def has_columns(data, columns):
    return isinstance(data, pd.DataFrame) and all(col in data.columns for col in columns)


def schedule_period_options(schedule_df, selected_year):
    if not has_columns(schedule_df, ["Year", "Period"]):
        return [1]
    period_raw = schedule_df[schedule_df["Year"] == selected_year]["Period"].max()
    if pd.isna(period_raw):
        return [1]
    return list(range(1, int(period_raw) + 1))


def period_date_range_text(dates, fallback=""):
    dates = pd.to_datetime(dates, errors="coerce").dropna()
    if dates.empty:
        return fallback
    start = dates.min()
    end = dates.max()

    def fmt_day(ts):
        return ts.strftime("%b %d").replace(" 0", " ")

    if start.date() == end.date():
        return fmt_day(start)
    return f"{fmt_day(start)}-{fmt_day(end)}"


def period_date_label(selected_year, selected_period, fallback=None):
    fallback = fallback or f"P{selected_period}"
    if not isinstance(period_calendar, pd.DataFrame) or period_calendar.empty:
        return fallback
    if not {"Year", "Period", "Date"}.issubset(period_calendar.columns):
        return fallback
    try:
        year = int(selected_year)
        selected_period = int(selected_period)
    except (TypeError, ValueError):
        return fallback
    dates = period_calendar[
        (pd.to_numeric(period_calendar["Year"], errors="coerce") == year)
        & (pd.to_numeric(period_calendar["Period"], errors="coerce") == selected_period)
    ]["Date"]
    return period_date_range_text(dates, fallback)


def period_select_label(selected_year):
    return lambda selected_period: period_date_label(selected_year, selected_period, f"P{selected_period}")


def period_range_label(selected_year, periods, fallback=""):
    clean_periods = []
    for value in periods:
        try:
            clean_periods.append(int(value))
        except (TypeError, ValueError):
            pass
    if not clean_periods:
        return fallback
    if isinstance(period_calendar, pd.DataFrame) and {"Year", "Period", "Date"}.issubset(period_calendar.columns):
        try:
            year = int(selected_year)
        except (TypeError, ValueError):
            year = None
        if year is not None:
            dates = period_calendar[
                (pd.to_numeric(period_calendar["Year"], errors="coerce") == year)
                & (pd.to_numeric(period_calendar["Period"], errors="coerce").isin(clean_periods))
            ]["Date"]
            label = period_date_range_text(dates, "")
            if label:
                return label
    labels = [period_date_label(selected_year, period, f"P{period}") for period in sorted(set(clean_periods))]
    if len(labels) == 1:
        return labels[0]
    return f"{labels[0]}-{labels[-1]}"


BOX_SCORE_STATS = ["GP", "MP", "TS%", "2PTM", "2PTA", "2PT%", "3PTM", "3PTA", "3PT%", "FTM", "FTA", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
BOX_SCORE_SUM_STATS = ["GP", "MP", "2PTM", "2PTA", "3PTM", "3PTA", "FTM", "FTA", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
BOX_SCORE_WEIGHTS = {"PTS": 61, "AST": 41, "TS%": 41, "2PT%": 31, "+/-": 31, "3PT%": 31, "BLK": 31, "DREB": 31, "OREB": 31, "ST": 31, "FT%": 21, "MP": 11, "TO": 21}
BOX_SCORE_CATEGORY_ORDER = ["MP", "TS%", "2PT%", "3PT%", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
HISTORY_LEADERBOARD_STATS = BOX_SCORE_CATEGORY_ORDER + ["Matchups", "Games Played"]
PBP_STAT_LABELS = {
    "ALL": "All Categories",
    "MP": "Minutes Played",
    "TS%": "TS%",
    "2PT%": "2PT%",
    "3PT%": "3PT%",
    "FT%": "FT%",
    "PTS": "Points",
    "OREB": "Offensive Rebounds",
    "DREB": "Defensive Rebounds",
    "AST": "Assists",
    "ST": "Steals",
    "BLK": "Blocks",
    "TO": "Turnovers",
    "+/-": "Plus/Minus",
}

TEAM_LOCATIONS = {
    "Albuquerque": ("Albuquerque", "New Mexico"), "Anaheim": ("Anaheim", "California"),
    "Anchorage": ("Anchorage", "Alaska"), "Austin": ("Austin", "Texas"),
    "Baltimore": ("Baltimore", "Maryland"), "Birmingham": ("Birmingham", "Alabama"),
    "Boise": ("Boise", "Idaho"), "Buffalo": ("Buffalo", "New York"),
    "Cincinnati": ("Cincinnati", "Ohio"), "Columbus": ("Columbus", "Ohio"),
    "Des Moines": ("Des Moines", "Iowa"), "El Paso": ("El Paso", "Texas"),
    "Honolulu": ("Honolulu", "Hawaii"), "Jacksonville": ("Jacksonville", "Florida"),
    "Kentucky": ("Louisville", "Kentucky"), "Lansing": ("Lansing", "Michigan"),
    "Lincoln": ("Lincoln", "Nebraska"), "Little Rock": ("Little Rock", "Arkansas"),
    "Manchester": ("Manchester", "New Hampshire"), "Nashville": ("Nashville", "Tennessee"),
    "Pittsburgh": ("Pittsburgh", "Pennsylvania"), "Providence": ("Providence", "Rhode Island"),
    "San Diego": ("San Diego", "California"), "San Jose": ("San Jose", "California"),
    "Seattle": ("Seattle", "Washington"), "St. Louis": ("St. Louis", "Missouri"),
    "Tampa Bay": ("Tampa", "Florida"), "Tulsa": ("Tulsa", "Oklahoma"),
    "Vancouver": ("Vancouver", "Canada"), "Vegas": ("Las Vegas", "Nevada"),
}


def _read_local_parquet(filename):
    candidates = [APP_DIR / filename, APP_DIR.parent / filename, Path(filename)]
    for path in candidates:
        if path.exists():
            return pd.read_parquet(path)
    return pd.DataFrame()


def _read_local_csv(filename):
    candidates = [APP_DIR / filename, APP_DIR.parent / filename, Path(filename)]
    for path in candidates:
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data(ttl=86400)
def load_nba_player_boxscores_archive():
    df = _read_local_parquet("nba_player_game_boxscores_2021_2026.parquet")
    if not df.empty and "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    return df


def pbp_archive_mtime():
    candidates = pbp_archive_candidates()
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return max(mtimes) if mtimes else 0


def pbp_archive_paths():
    return [path for path in pbp_archive_candidates() if path.exists()]


def pbp_archive_candidates():
    patterns = [
        "data_snapshots/pbp/pbp_stat_events_all_regular_season*.parquet",
        "data_snapshots/pbp/pbp_stat_events_202021.parquet",
        "data_snapshots/pbp/pbp_stat_events_202122.parquet",
        "data_snapshots/pbp/pbp_stat_events_202223.parquet",
        "data_snapshots/pbp/pbp_stat_events_202324.parquet",
        "data_snapshots/pbp/pbp_stat_events_202425.parquet",
        "data_snapshots/pbp/pbp_stat_events_202526.parquet",
        "data_snapshots/pbp/pbp_stat_events_20241022_20241025.parquet",
    ]
    roots = [APP_DIR, APP_DIR.parent, Path(".")]
    candidates: list[Path] = []
    for root in roots:
        for pattern in patterns:
            matches = sorted(root.glob(pattern), key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)
            candidates.extend(matches)
            direct = root / pattern
            if direct.exists():
                candidates.append(direct)
    seen: set[Path] = set()
    ordered: list[Path] = []
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(candidate)
    return ordered


@st.cache_data(ttl=86400)
def load_pbp_stat_events_archive(mtime=None):
    df = pd.DataFrame()
    candidates = pbp_archive_paths()
    if candidates:
        frames = [pd.read_parquet(candidate) for candidate in candidates]
        df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    if df.empty:
        return df
    for col in ["game_id", "player_id"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
    if "wallclock" in df.columns:
        df["wallclock"] = pd.to_datetime(df["wallclock"], errors="coerce", utc=True)
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)
    return df


def _pbp_archive_read(columns=None, filters=None):
    candidates = pbp_archive_paths()
    if not candidates:
        return pd.DataFrame()
    read_columns = list(columns) if columns else None
    try:
        dataset = pq.ParquetDataset([str(candidate) for candidate in candidates], filters=filters)
        table = dataset.read(columns=read_columns)
        return table.to_pandas()
    except Exception:
        if filters:
            fallback_frames = [pd.read_parquet(candidate, columns=read_columns) for candidate in candidates]
            fallback = pd.concat(fallback_frames, ignore_index=True) if len(fallback_frames) > 1 else fallback_frames[0]
            for column, op, values in filters:
                if op == "in":
                    fallback = fallback[fallback[column].astype(str).isin({str(value) for value in values})]
            return fallback
        raise


def _normalize_pbp_game_ids(game_ids):
    return sorted({str(game_id).strip() for game_id in game_ids if pd.notna(game_id) and str(game_id).strip()})


def _normalize_pbp_game_dates(game_dates):
    values = set()
    for game_date in game_dates:
        if pd.isna(game_date):
            continue
        value = str(game_date).strip()
        if not value:
            continue
        if len(value) == 10 and value[4] == "-" and value[7] == "-":
            value = value.replace("-", "")
        values.add(value)
    return sorted(values)


@st.cache_data(ttl=86400)
def load_pbp_stat_events_for_games(game_ids_key, mtime=None):
    game_ids = _normalize_pbp_game_ids(game_ids_key)
    if not game_ids:
        return pd.DataFrame()
    df = _pbp_archive_read(
        columns=["game_id", "game_date", "stat", "player_id", "player", "wallclock", "value", "scored", "description"],
        filters=[("game_id", "in", game_ids)],
    )
    if df.empty:
        return df
    for col in ["game_id", "player_id"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
    if "game_date" in df.columns:
        df["game_date"] = df["game_date"].astype(str)
    if "wallclock" in df.columns:
        df["wallclock"] = pd.to_datetime(df["wallclock"], errors="coerce", utc=True)
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=86400)
def load_pbp_slate_bounds_for_dates(game_dates_key, mtime=None):
    game_dates = _normalize_pbp_game_dates(game_dates_key)
    if not game_dates:
        return pd.DataFrame(columns=["game_id", "game_date", "wallclock"])
    df = _pbp_archive_read(
        columns=["game_id", "game_date", "wallclock"],
        filters=[("game_date", "in", game_dates)],
    )
    if df.empty:
        return df
    if "game_id" in df.columns:
        df["game_id"] = df["game_id"].astype(str)
    if "game_date" in df.columns:
        df["game_date"] = df["game_date"].astype(str)
    if "wallclock" in df.columns:
        df["wallclock"] = pd.to_datetime(df["wallclock"], errors="coerce", utc=True)
    return df


@st.cache_data(ttl=3600)
def load_sbc_player_matchup_stats_archive():
    df = _read_local_parquet("sbc_player_matchup_stats.parquet")
    if df.empty:
        return df
    for col in ["start_date", "end_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    if "fantrax_id" in df.columns:
        df["fantrax_id"] = df["fantrax_id"].astype(str)
    if "espn_player_id" in df.columns:
        df["espn_player_id"] = df["espn_player_id"].astype(str)
    return df


@st.cache_data(ttl=86400)
def load_fantrax_players_snapshot():
    df = _read_local_parquet("fantrax_players_snapshot.parquet")
    if df.empty:
        df = get_fantrax_players()
    return ensure_columns(df, ["name", "fantraxId"]).dropna(subset=["name", "fantraxId"])


def normalize_boxscore_player_key(value):
    text = str(value or "")
    text = re.sub(r"\b(Jr|Sr|II|III|IV|V)\b\.?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[^A-Za-z0-9]+", "", text).lower()
    return text


def team_short_name(team_name):
    text = str(team_name or "").strip()
    for city, info in team_info.items():
        full_name = f"{city} {info.get('nickname', '')}".strip()
        if text == city or text == full_name or text.startswith(f"{city} "):
            return city
    return text


@st.cache_data(ttl=86400)
def build_fantrax_to_espn_bridge():
    ft = load_fantrax_players_snapshot().copy()
    box = load_nba_player_boxscores_archive()
    if ft.empty or box.empty:
        return pd.DataFrame(columns=["fantraxId", "fantrax_name", "espn_player_id", "espn_name", "match_type"])

    ft = ft.rename(columns={"name": "fantrax_name"}).dropna(subset=["fantrax_name", "fantraxId"])
    ft["fantraxId"] = ft["fantraxId"].astype(str)
    ft["_player_key"] = ft["fantrax_name"].apply(normalize_boxscore_player_key)

    box_players = box[["nba_player_id", "player_name"]].dropna().drop_duplicates().copy()
    box_players["nba_player_id"] = box_players["nba_player_id"].astype(str)
    box_players["_player_key"] = box_players["player_name"].apply(normalize_boxscore_player_key)
    key_counts = box_players.groupby("_player_key")["nba_player_id"].nunique()
    unique_box_players = box_players[box_players["_player_key"].isin(key_counts[key_counts == 1].index)]

    bridge = ft.merge(unique_box_players, on="_player_key", how="inner")
    bridge = bridge.rename(columns={"nba_player_id": "espn_player_id", "player_name": "espn_name"})
    bridge["match_type"] = "name"
    bridge = bridge[["fantraxId", "fantrax_name", "espn_player_id", "espn_name", "match_type"]]

    overrides = _read_local_csv("player_id_overrides.csv")
    if not overrides.empty:
        overrides = ensure_columns(overrides, ["fantraxId", "fantrax_name", "espn_player_id", "espn_name"])
        overrides = overrides[["fantraxId", "fantrax_name", "espn_player_id", "espn_name"]].dropna(subset=["fantraxId", "espn_player_id"])
        overrides["fantraxId"] = overrides["fantraxId"].astype(str)
        overrides["espn_player_id"] = overrides["espn_player_id"].astype(str)
        overrides["match_type"] = "override"
        bridge = bridge[~bridge["fantraxId"].isin(overrides["fantraxId"])]
        bridge = pd.concat([bridge, overrides], ignore_index=True)
    return bridge.drop_duplicates("fantraxId").reset_index(drop=True)


def recalc_shooting_stats(df):
    out = df.copy()
    for col in BOX_SCORE_SUM_STATS:
        if col not in out.columns:
            out[col] = 0
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    fga = out["2PTA"] + out["3PTA"]
    out["TS%"] = (out["PTS"] / (2 * (fga + 0.44 * out["FTA"]))).where((fga + 0.44 * out["FTA"]) > 0, 0)
    out["2PT%"] = (out["2PTM"] / out["2PTA"]).where(out["2PTA"] > 0, 0)
    out["3PT%"] = (out["3PTM"] / out["3PTA"]).where(out["3PTA"] > 0, 0)
    out["FT%"] = (out["FTM"] / out["FTA"]).where(out["FTA"] > 0, 0)
    return out


def matchup_boxscore_rows(matchup_row, rosters_df):
    year = int(matchup_row.get("Year", 0))
    matchup_period = int(matchup_row.get("Period", 0))
    teams = [str(matchup_row.get("TeamA", "")), str(matchup_row.get("TeamB", ""))]

    if period_calendar.empty or rosters_df.empty:
        return pd.DataFrame()
    calendar = period_calendar.copy()
    calendar["Date"] = pd.to_datetime(calendar["Date"], errors="coerce").dt.date
    matchup_days = calendar[
        (pd.to_numeric(calendar["Year"], errors="coerce") == year)
        & (pd.to_numeric(calendar["Period"], errors="coerce") == matchup_period)
    ][["Year", "Day", "Date"]].dropna()
    if matchup_days.empty:
        return pd.DataFrame()
    matchup_days["Year"] = matchup_days["Year"].astype(int)
    matchup_days["Day"] = matchup_days["Day"].astype(int)

    bridge = build_fantrax_to_espn_bridge()
    if bridge.empty:
        return pd.DataFrame()

    active = rosters_df.copy()
    active["Year"] = pd.to_numeric(active["Year"], errors="coerce")
    active["period"] = pd.to_numeric(active["period"], errors="coerce")
    active = active[
        (active["Year"] == year)
        & (active["status"].astype(str).str.upper() == "ACTIVE")
        & (active["period"].isin(matchup_days["Day"]))
    ].copy()
    active["sbc_team"] = active["team_name"].apply(team_short_name)
    active = active[active["sbc_team"].isin(teams)].copy()
    active = active.rename(columns={"id": "fantraxId", "period": "Day"})
    active["fantraxId"] = active["fantraxId"].astype(str)
    active["Day"] = active["Day"].astype(int)
    active = active.merge(bridge, on="fantraxId", how="left")
    active = active.dropna(subset=["espn_player_id"])
    active["espn_player_id"] = active["espn_player_id"].astype(str)

    box = load_nba_player_boxscores_archive()
    if box.empty:
        return pd.DataFrame()
    box = box[box["sbc_year"].astype(int) == year].copy()
    box["Date"] = pd.to_datetime(box["Date"], errors="coerce").dt.date
    box = box[box["Date"].isin(matchup_days["Date"])].copy()
    box = box.merge(matchup_days[["Date", "Day"]], on="Date", how="inner")
    box["nba_player_id"] = box["nba_player_id"].astype(str)

    merged = active.merge(
        box,
        left_on=["Day", "espn_player_id"],
        right_on=["Day", "nba_player_id"],
        how="inner",
    )
    if merged.empty:
        return pd.DataFrame()
    merged["display_player"] = merged["fantrax_name"].fillna(merged["player_name"])
    return merged.sort_values(["sbc_team", "display_player", "Date", "nba_game_id"]).reset_index(drop=True)


def aggregate_boxscore_players(rows):
    if rows.empty:
        return rows
    grouped = rows.groupby(["sbc_team", "fantraxId", "espn_player_id", "display_player"], as_index=False)[BOX_SCORE_SUM_STATS].sum()
    grouped = recalc_shooting_stats(grouped)
    return grouped.sort_values(["sbc_team", "PTS", "display_player"], ascending=[True, False, True]).reset_index(drop=True)


def team_boxscore_totals(rows):
    if rows.empty:
        return rows
    grouped = rows.groupby("sbc_team", as_index=False)[BOX_SCORE_SUM_STATS].sum()
    grouped = recalc_shooting_stats(grouped)
    return grouped


def matchup_category_results(team_totals, team_a, team_b):
    if team_totals.empty or team_totals["sbc_team"].nunique() < 2:
        return pd.DataFrame(), 0, 0
    totals = team_totals.set_index("sbc_team")
    if team_a not in totals.index or team_b not in totals.index:
        return pd.DataFrame(), 0, 0
    rows = []
    score_a = 0
    score_b = 0
    for stat, weight in BOX_SCORE_WEIGHTS.items():
        val_a = float(totals.loc[team_a, stat])
        val_b = float(totals.loc[team_b, stat])
        if stat == "TO":
            winner = team_a if val_a < val_b else team_b if val_b < val_a else "Tie"
        else:
            winner = team_a if val_a > val_b else team_b if val_b > val_a else "Tie"
        if winner == team_a:
            score_a += weight
        elif winner == team_b:
            score_b += weight
        else:
            score_a += weight / 2
            score_b += weight / 2
        rows.append({"Category": stat, team_a: val_a, team_b: val_b, "Votes": weight, "Winner": winner})
    return pd.DataFrame(rows), score_a, score_b


def format_boxscore_table(df, include_games=False):
    if df.empty:
        return df
    table = df.copy()
    if include_games:
        table["Date"] = pd.to_datetime(table["Date"], errors="coerce").apply(lambda value: value.strftime("%b %d").replace(" 0", " ") if pd.notna(value) else "")
        table = table.rename(columns={"display_player": "Player", "sbc_team": "Team", "nba_team": "NBA", "opponent": "Opp"})
        columns = ["Team", "Player", "Date", "NBA", "Opp"] + BOX_SCORE_STATS
    else:
        table = table.rename(columns={"display_player": "Player", "sbc_team": "Team"})
        columns = ["Team", "Player"] + BOX_SCORE_STATS
    for pct_col in ["TS%", "2PT%", "3PT%", "FT%"]:
        if pct_col in table.columns:
            table[pct_col] = (pd.to_numeric(table[pct_col], errors="coerce").fillna(0) * 100).round(1)
    for stat in ["MP", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]:
        if stat in table.columns:
            table[stat] = pd.to_numeric(table[stat], errors="coerce").fillna(0).round(1)
    return table[[col for col in columns if col in table.columns]]


def boxscore_title_for_round(round_label, type_label):
    round_text = str(round_label or "")
    type_text = str(type_label or "")
    if "SBCFBL Finals" in round_text:
        return "SBCFBL Finals Box Score"
    if "Final" in round_text or "Championship" in round_text:
        return f"{round_text} Box Score"
    if type_text == "Regular Season":
        return "Regular Season Box Score"
    return f"{type_text or round_text or 'Matchup'} Box Score"


def boxscore_stat_label(stat):
    return {"2PT%": "2P%", "3PT%": "3P%", "ST": "STL", "TO": "TOV"}.get(stat, stat)


def stat_number(value, pct=False, signed=False):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0
    if pct:
        return f"{number * 100:.1f}%"
    if abs(number - round(number)) < 0.05:
        text = f"{int(round(number))}"
    else:
        text = f"{number:.1f}"
    if signed and number >= 0:
        return f"+{text}"
    return text


def shot_attempts(row, made_col, attempt_col):
    attempts = float(row.get(attempt_col, 0) or 0)
    if attempts <= 0:
        return ""
    return f"{stat_number(row.get(made_col, 0))} / {stat_number(attempts)}"


def stat_has_shooting_volume(row, stat):
    if stat == "TS%":
        return sum(float(row.get(col, 0) or 0) for col in ["2PTA", "3PTA", "FTA"]) > 0
    if stat == "2PT%":
        return float(row.get("2PTA", 0) or 0) > 0
    if stat == "3PT%":
        return float(row.get("3PTA", 0) or 0) > 0
    if stat == "FT%":
        return float(row.get("FTA", 0) or 0) > 0
    return True


def stat_subtext(row, stat, show_gp=True):
    if stat == "MP":
        if str(row.get("_basis", "")) == "per_sbc":
            matchups = row.get("_matchups", row.get("_denom_gp", 0))
            try:
                matchup_count = float(matchups)
            except (TypeError, ValueError):
                matchup_count = 0
            matchup_text = "Matchup" if abs(matchup_count - 1) < 0.05 else "Matchups"
            return f"{stat_number(row.get('GP', 0))} GP, {stat_number(matchup_count)} {matchup_text}" if show_gp else ""
        return f"{stat_number(row.get('GP', 0))} GP" if show_gp else ""
    if stat == "2PT%":
        return shot_attempts(row, "2PTM", "2PTA")
    if stat == "3PT%":
        return shot_attempts(row, "3PTM", "3PTA")
    if stat == "FT%":
        return shot_attempts(row, "FTM", "FTA")
    return ""


def stat_cell_html(row, stat, winner=False, tie=False, align="center", show_gp=True):
    is_pct = stat in ["TS%", "2PT%", "3PT%", "FT%"]
    if is_pct and not stat_has_shooting_volume(row, stat):
        value = "-"
    else:
        value = stat_number(row.get(stat, 0), pct=is_pct, signed=(stat == "+/-"))
    sub = stat_subtext(row, stat, show_gp=show_gp)
    sub_html = f"<em>{escape(sub)}</em>" if sub else ""
    cell_class = "sbc-box-stat-tie" if tie else "sbc-box-stat-win" if winner else ""
    return f"""
        <td class="sbc-box-stat-cell {cell_class}" style="text-align:{align};">
            <strong>{escape(value)}</strong>
            {sub_html}
        </td>
    """


def espn_headshot_url(player_id):
    player_id = str(player_id or "").strip()
    if not player_id:
        return ""
    return f"https://a.espncdn.com/i/headshots/nba/players/full/{escape(player_id, quote=True)}.png"


def render_category_votes_box(category_table, team_totals, team_a, team_b):
    if category_table.empty or team_totals.empty:
        return
    totals = team_totals.set_index("sbc_team")
    category_lookup = category_table.set_index("Category")
    info_a = team_info.get(team_a, {})
    info_b = team_info.get(team_b, {})
    font_a = team_font_for_name(team_a)
    font_b = team_font_for_name(team_b)
    rows_html = []
    for stat in BOX_SCORE_CATEGORY_ORDER:
        if stat not in category_lookup.index or team_a not in totals.index or team_b not in totals.index:
            continue
        cat_row = category_lookup.loc[stat]
        winner = cat_row.get("Winner", "Tie")
        team_a_win = winner == team_a
        team_b_win = winner == team_b
        tied_category = winner == "Tie"
        rows_html.append(f"""
            <tr>
                {stat_cell_html(totals.loc[team_a], stat, winner=team_a_win, tie=tied_category)}
                <td class="sbc-box-category-name">
                    <strong>{escape(boxscore_stat_label(stat))}</strong>
                    <em>{escape(str(BOX_SCORE_WEIGHTS.get(stat, '')))} points</em>
                </td>
                {stat_cell_html(totals.loc[team_b], stat, winner=team_b_win, tie=tied_category)}
            </tr>
        """)
    render_html(f"""
        <section class="sbc-box-panel sbc-box-category-panel" style="--cat-a:{escape(str(info_a.get('bg', '#111827')), quote=True)};--cat-b:{escape(str(info_b.get('bg', '#334155')), quote=True)};--cat-a-secondary:{escape(str(info_a.get('bg2', info_a.get('bg', '#111827'))), quote=True)};--cat-b-secondary:{escape(str(info_b.get('bg2', info_b.get('bg', '#334155'))), quote=True)};--cat-font-a:{escape(str(font_a), quote=True)};--cat-font-b:{escape(str(font_b), quote=True)};">
            <div class="sbc-box-panel-head">
                <span>Category Points</span>
            </div>
            <table class="sbc-box-category-table">
                <thead>
                    <tr>
                        <th class="sbc-box-category-team-header sbc-box-category-team-header-a"><span class="sbc-box-category-team-name sbc-box-category-team-a">{escape(live_team_full_name(team_a))}</span></th>
                        <th>Category</th>
                        <th class="sbc-box-category-team-header sbc-box-category-team-header-b"><span class="sbc-box-category-team-name sbc-box-category-team-b">{escape(live_team_full_name(team_b))}</span></th>
                    </tr>
                </thead>
                <tbody>{''.join(rows_html)}</tbody>
            </table>
        </section>
    """)


def matchup_label_for_row(row):
    matchup = str(row.get("matchup", "") or "").strip()
    if matchup:
        return matchup
    nba_team = str(row.get("nba_team", "") or "").strip()
    opponent = str(row.get("opponent", "") or "").strip()
    if nba_team and opponent:
        return f"{nba_team} vs. {opponent}"
    return nba_team or opponent


def render_player_boxscore_team(team_rows, team_name, aggregate):
    info = team_info.get(team_name, {})
    primary = info.get("bg", "#111827")
    secondary = info.get("bg2", primary)
    font = team_font_for_name(team_name)
    stats = ["MP", "TS%", "2PT%", "3PT%", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
    team_rows = team_rows.copy()
    if aggregate:
        mp_values = team_rows["MP"] if "MP" in team_rows else pd.Series(0, index=team_rows.index)
        team_rows["_sort_mp"] = pd.to_numeric(mp_values, errors="coerce").fillna(0)
        team_rows = team_rows.sort_values(["_sort_mp", "display_player"], ascending=[False, True])
    else:
        date_values = team_rows["Date"] if "Date" in team_rows else pd.Series(pd.NaT, index=team_rows.index)
        team_rows["_sort_date"] = pd.to_datetime(date_values, errors="coerce")
        team_rows = team_rows.sort_values(["_sort_date", "display_player"], ascending=[True, True])
    rows_html = []
    last_date_text = None
    for _, row in team_rows.iterrows():
        game_meta = ""
        if not aggregate:
            game_date = pd.to_datetime(row.get("Date"), errors="coerce")
            date_text = game_date.strftime("%b %d").replace(" 0", " ") if pd.notna(game_date) else ""
            if date_text != last_date_text:
                rows_html.append(f'<tr class="sbc-box-game-date-row"><td colspan="{len(stats) + 1}">{escape(date_text)}</td></tr>')
                last_date_text = date_text
            game_meta = f"<em>{escape(matchup_label_for_row(row))}</em>"
        stat_cells = "".join(stat_cell_html(row, stat, show_gp=aggregate) for stat in stats)
        rows_html.append(f"""
            <tr>
                <td class="sbc-box-player-cell">
                    <img src="{espn_headshot_url(row.get('espn_player_id'))}" alt="{escape(str(row.get('display_player', '')), quote=True)} headshot">
                    <span><strong>{escape(str(row.get('display_player', '')))}</strong>{game_meta}</span>
                </td>
                {stat_cells}
            </tr>
        """)
    headers = "".join(f"<th>{escape(boxscore_stat_label(stat))}</th>" for stat in stats)
    return f"""
        <section class="sbc-box-panel sbc-box-team-panel" style="--box-team:{escape(str(primary), quote=True)};--box-team-secondary:{escape(str(secondary), quote=True)};--box-team-font:{escape(str(font), quote=True)};">
            <div class="sbc-box-team-head">
                <img src="{escape(str(info.get('logo', '')), quote=True)}" alt="{escape(team_name, quote=True)} logo">
                <span>{escape(live_team_full_name(team_name))}</span>
            </div>
            <div class="sbc-box-table-scroll">
                <table class="sbc-box-player-table">
                    <thead><tr><th>Player</th>{headers}</tr></thead>
                    <tbody>{''.join(rows_html)}</tbody>
                </table>
            </div>
        </section>
    """


def render_player_boxscore_split(rows, team_a, team_b, aggregate=False):
    display_rows = aggregate_boxscore_players(rows) if aggregate else rows.copy()
    render_html(f"""
        <div class="sbc-box-player-grid">
            {render_player_boxscore_team(display_rows[display_rows["sbc_team"] == team_a], team_a, aggregate)}
            {render_player_boxscore_team(display_rows[display_rows["sbc_team"] == team_b], team_b, aggregate)}
        </div>
    """)


def format_pbp_wallclock(value):
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(ts):
        return ""
    eastern = ts.tz_convert(ZoneInfo("America/New_York"))
    text = eastern.strftime("%b %d, %I:%M %p ET") if hasattr(eastern, "strftime") else ""
    if not text:
        return ""
    text = re.sub(r", 0(\d):", r", \1:", text)
    return text.replace(" 0", " ").replace("AM", "a.m.").replace("PM", "p.m.")


def pbp_event_filter(df, category):
    if df.empty:
        return df
    stat = df["stat"].astype(str)
    descriptions = df["description"].astype(str).str.lower()
    if category == "MP":
        return df[stat == "minutes played"].copy()
    if category == "+/-":
        return df[stat == "+/-"].copy()
    if category == "PTS":
        return df[stat == "points"].copy()
    if category == "OREB":
        return df[stat == "offensive_rebound"].copy()
    if category == "DREB":
        return df[stat == "defensive_rebound"].copy()
    if category == "AST":
        return df[stat == "assist"].copy()
    if category == "ST":
        return df[stat == "steal"].copy()
    if category == "BLK":
        return df[stat == "block"].copy()
    if category == "TO":
        return df[stat == "turnover"].copy()
    if category == "2PT%":
        return df[stat.isin(["two-point make", "two-point miss"])].copy()
    if category == "3PT%":
        return df[stat.isin(["three-point make", "three-point miss"])].copy()
    if category == "FT%":
        return df[stat.isin(["free-throw make", "free-throw miss"])].copy()
    if category == "TS%":
        return df[stat.isin(["two-point make", "two-point miss", "three-point make", "three-point miss", "free-throw make", "free-throw miss"])].copy()
    return df.iloc[0:0].copy()


def pbp_category_delta(row, category):
    stat = str(row.get("stat", ""))
    value = float(row.get("value", 0) or 0)
    description = str(row.get("description", "")).lower()
    if category == "MP":
        return {"value": value}
    if category == "+/-":
        return {"value": value}
    if category == "PTS":
        return {"value": value if stat == "points" else 0}
    if category in ["OREB", "DREB", "AST", "ST", "BLK", "TO"]:
        return {"value": value}
    if category == "2PT%":
        return {"made": value if stat == "two-point make" else 0, "att": value}
    if category == "3PT%":
        return {"made": value if stat == "three-point make" else 0, "att": value}
    if category == "FT%":
        return {"made": value if stat == "free-throw make" else 0, "att": value}
    if category == "TS%":
        if stat == "two-point make":
            return {"points": 2 * value, "fga": value, "fta": 0}
        if stat == "three-point make":
            return {"points": 3 * value, "fga": value, "fta": 0}
        if stat == "free-throw make":
            return {"points": value, "fga": 0, "fta": value}
        if stat in ["two-point miss", "three-point miss"]:
            return {"points": 0, "fga": value, "fta": 0}
        if stat == "free-throw miss":
            return {"points": 0, "fga": 0, "fta": value}
    return {"value": 0}


def pbp_running_display(state, category):
    if category in ["2PT%", "3PT%", "FT%"]:
        made = state.get("made", 0)
        att = state.get("att", 0)
        pct = made / att if att else 0
        return f"{int(made)}/{int(att)} ({pct * 100:.1f}%)"
    if category == "TS%":
        points = state.get("points", 0)
        fga = state.get("fga", 0)
        fta = state.get("fta", 0)
        tsa = fga + 0.44 * fta
        denom = 2 * tsa
        ts = points / denom if denom else 0
        return f"{tsa:.1f} TSA ({ts * 100:.1f}%)"
    value = state.get("value", 0)
    if category == "MP":
        total_seconds = int(round(value * 60))
        minutes, seconds = divmod(max(0, total_seconds), 60)
        return f"{minutes}:{seconds:02d}"
    return stat_number(value, signed=(category == "+/-"))


def pbp_winner(states, category, team_a, team_b):
    def numeric(team):
        state = states.get(team, {})
        if category in ["2PT%", "3PT%", "FT%"]:
            att = state.get("att", 0)
            return state.get("made", 0) / att if att else 0
        if category == "TS%":
            denom = 2 * (state.get("fga", 0) + 0.44 * state.get("fta", 0))
            return state.get("points", 0) / denom if denom else 0
        return state.get("value", 0)

    val_a = numeric(team_a)
    val_b = numeric(team_b)
    if abs(val_a - val_b) < 0.000001:
        return "Tie"
    if category == "TO":
        return team_a if val_a < val_b else team_b
    return team_a if val_a > val_b else team_b


def pbp_category_score(category_states, team_a, team_b):
    score_a = 0.0
    score_b = 0.0
    for category, weight in BOX_SCORE_WEIGHTS.items():
        winner = pbp_winner(category_states.get(category, {}), category, team_a, team_b)
        if winner == team_a:
            score_a += weight
        elif winner == team_b:
            score_b += weight
        else:
            score_a += weight / 2
            score_b += weight / 2
    return score_a, score_b


def pbp_categories_for_event(row):
    stat = str(row.get("stat", ""))
    value = float(row.get("value", 0) or 0)
    description = str(row.get("description", "")).lower()
    categories = []
    if stat == "minutes played":
        categories.append("MP")
    elif stat == "+/-":
        categories.append("+/-")
    elif stat == "points":
        categories.append("PTS")
    elif stat == "two-point make":
        categories.extend(["2PT%", "TS%"])
    elif stat == "three-point make":
        categories.extend(["3PT%", "TS%"])
    elif stat == "free-throw make":
        categories.extend(["FT%", "TS%"])
    elif stat == "two-point miss":
        categories.extend(["2PT%", "TS%"])
    elif stat == "three-point miss":
        categories.extend(["3PT%", "TS%"])
    elif stat == "free-throw miss":
        categories.extend(["FT%", "TS%"])
    elif stat == "offensive_rebound":
        categories.append("OREB")
    elif stat == "defensive_rebound":
        categories.append("DREB")
    elif stat == "assist":
        categories.append("AST")
    elif stat == "steal":
        categories.append("ST")
    elif stat == "block":
        categories.append("BLK")
    elif stat == "turnover":
        categories.append("TO")
    return categories


def matchup_pbp_events(rows, team_a, team_b):
    if rows.empty:
        return pd.DataFrame()
    mapping = rows[["nba_game_id", "espn_player_id", "sbc_team", "display_player"]].dropna(subset=["nba_game_id", "espn_player_id", "sbc_team"]).drop_duplicates().copy()
    if mapping.empty:
        return pd.DataFrame()
    mapping["nba_game_id"] = mapping["nba_game_id"].astype(str)
    mapping["espn_player_id"] = mapping["espn_player_id"].astype(str)
    mapping = mapping[mapping["sbc_team"].isin([team_a, team_b])].copy()
    game_ids = tuple(sorted(mapping["nba_game_id"].dropna().astype(str).unique()))
    events = load_pbp_stat_events_for_games(game_ids, pbp_archive_mtime())
    if events.empty:
        return pd.DataFrame()
    merged = events.merge(
        mapping,
        left_on=["game_id", "player_id"],
        right_on=["nba_game_id", "espn_player_id"],
        how="inner",
    )
    if merged.empty:
        return pd.DataFrame()
    merged["display_player"] = merged["display_player"].fillna(merged["player"])
    merged = append_matchup_pbp_total_adjustments(merged, rows, team_a, team_b)
    return merged.sort_values(["wallclock", "game_id", "stat", "player"]).reset_index(drop=True)


def append_matchup_pbp_total_adjustments(events, box_rows, team_a, team_b):
    if events.empty or box_rows.empty:
        return events
    totals = team_boxscore_totals(box_rows)
    if totals.empty:
        return events
    totals = totals.set_index("sbc_team")
    output = [events]
    max_time = pd.to_datetime(events["wallclock"], errors="coerce", utc=True).max()
    if pd.isna(max_time):
        max_time = pd.Timestamp.utcnow()
    adjustment_time = max_time + pd.Timedelta(seconds=1)

    def current(team, stat):
        subset = events[(events["sbc_team"].astype(str) == str(team)) & (events["stat"].astype(str) == stat)]
        return float(pd.to_numeric(subset["value"], errors="coerce").fillna(0).sum())

    adjustment_rows = []
    simple_stats = [
        ("MP", "minutes played"),
        ("PTS", "points"),
        ("OREB", "offensive_rebound"),
        ("DREB", "defensive_rebound"),
        ("AST", "assist"),
        ("ST", "steal"),
        ("BLK", "block"),
        ("TO", "turnover"),
        ("+/-", "+/-"),
    ]
    shot_stats = [
        ("2PTM", "2PTA", "two-point make", "two-point miss"),
        ("3PTM", "3PTA", "three-point make", "three-point miss"),
        ("FTM", "FTA", "free-throw make", "free-throw miss"),
    ]
    for team in [team_a, team_b]:
        if team not in totals.index:
            continue
        team_total = totals.loc[team]
        for official_col, stat in simple_stats:
            target = float(pd.to_numeric(pd.Series([team_total.get(official_col, 0)]), errors="coerce").fillna(0).iloc[0])
            diff = target - current(team, stat)
            if abs(diff) >= 0.0001:
                adjustment_rows.append({
                    "game_id": "matchup_adjustment",
                    "game_date": "",
                    "stat": stat,
                    "player_id": f"{team}_adjustment",
                    "player": "Team Adjustment",
                    "wallclock": adjustment_time,
                    "value": round(diff, 4),
                    "scored": None,
                    "description": f"{live_team_full_name(team)} {boxscore_stat_label(official_col)} adjustment {stat_number(diff, signed=True)}",
                    "nba_game_id": "matchup_adjustment",
                    "espn_player_id": f"{team}_adjustment",
                    "sbc_team": team,
                    "display_player": "Team Adjustment",
                })
        for made_col, attempt_col, make_stat, miss_stat in shot_stats:
            target_made = float(pd.to_numeric(pd.Series([team_total.get(made_col, 0)]), errors="coerce").fillna(0).iloc[0])
            target_attempts = float(pd.to_numeric(pd.Series([team_total.get(attempt_col, 0)]), errors="coerce").fillna(0).iloc[0])
            made_diff = target_made - current(team, make_stat)
            if abs(made_diff) >= 0.0001:
                adjustment_rows.append({
                    "game_id": "matchup_adjustment",
                    "game_date": "",
                    "stat": make_stat,
                    "player_id": f"{team}_adjustment",
                    "player": "Team Adjustment",
                    "wallclock": adjustment_time,
                    "value": round(made_diff, 4),
                    "scored": None,
                    "description": f"{live_team_full_name(team)} {boxscore_stat_label(made_col)} adjustment {stat_number(made_diff, signed=True)}",
                    "nba_game_id": "matchup_adjustment",
                    "espn_player_id": f"{team}_adjustment",
                    "sbc_team": team,
                    "display_player": "Team Adjustment",
                })
            current_attempts_after_make = current(team, make_stat) + made_diff + current(team, miss_stat)
            miss_diff = target_attempts - current_attempts_after_make
            if abs(miss_diff) >= 0.0001:
                adjustment_rows.append({
                    "game_id": "matchup_adjustment",
                    "game_date": "",
                    "stat": miss_stat,
                    "player_id": f"{team}_adjustment",
                    "player": "Team Adjustment",
                    "wallclock": adjustment_time,
                    "value": round(miss_diff, 4),
                    "scored": None,
                    "description": f"{live_team_full_name(team)} {boxscore_stat_label(attempt_col)} adjustment {stat_number(miss_diff, signed=True)}",
                    "nba_game_id": "matchup_adjustment",
                    "espn_player_id": f"{team}_adjustment",
                    "sbc_team": team,
                    "display_player": "Team Adjustment",
                })

    if adjustment_rows:
        output.append(pd.DataFrame(adjustment_rows))
    return pd.concat(output, ignore_index=True, sort=False)


def build_pbp_running_table(events, category, team_a, team_b):
    filtered = pbp_event_filter(events, category)
    if filtered.empty:
        return filtered
    states = {
        team_a: {"value": 0, "made": 0, "att": 0, "points": 0, "fga": 0, "fta": 0},
        team_b: {"value": 0, "made": 0, "att": 0, "points": 0, "fga": 0, "fta": 0},
    }
    rows = []
    previous_winner = "Tie"
    for _, row in filtered.iterrows():
        sbc_team = str(row.get("sbc_team", ""))
        if sbc_team not in states:
            continue
        delta = pbp_category_delta(row, category)
        for key, amount in delta.items():
            states[sbc_team][key] = states[sbc_team].get(key, 0) + amount
        winner = pbp_winner(states, category, team_a, team_b)
        lead_change = previous_winner != winner and winner != "Tie"
        previous_winner = winner
        rows.append({
            "wallclock": row.get("wallclock"),
            "description": row.get("description", ""),
            "sbc_team": sbc_team,
            "team_a_total": pbp_running_display(states[team_a], category),
            "team_b_total": pbp_running_display(states[team_b], category),
            "winner": winner,
            "lead_change": lead_change,
            "tied": winner == "Tie",
        })
    return pd.DataFrame(rows)


def empty_pbp_category_states(team_a, team_b):
    base = {"value": 0, "made": 0, "att": 0, "points": 0, "fga": 0, "fta": 0}
    return {
        category: {team_a: base.copy(), team_b: base.copy()}
        for category in BOX_SCORE_CATEGORY_ORDER
    }


def build_pbp_all_category_leads(events, team_a, team_b):
    if events.empty:
        return pd.DataFrame(), pd.DataFrame()
    filtered = events.copy().sort_values(["wallclock", "game_id", "stat", "player"]).reset_index(drop=True)
    states = empty_pbp_category_states(team_a, team_b)
    previous_winners = {category: "" for category in BOX_SCORE_CATEGORY_ORDER}
    rows = []
    chart_rows = []
    score_a, score_b = pbp_category_score(states, team_a, team_b)
    first_row = filtered.iloc[0] if not filtered.empty else {}
    chart_rows.append({"wallclock": filtered["wallclock"].min(), "game_date": first_row.get("game_date", ""), team_a: score_a, team_b: score_b})
    previous_score = (score_a, score_b)

    for _, row in filtered.iterrows():
        sbc_team = str(row.get("sbc_team", ""))
        if sbc_team not in [team_a, team_b]:
            continue
        changed_categories = pbp_categories_for_event(row)
        if not changed_categories:
            continue
        for category in changed_categories:
            winner_before = previous_winners.get(category, "")
            delta = pbp_category_delta(row, category)
            for key, amount in delta.items():
                states[category][sbc_team][key] = states[category][sbc_team].get(key, 0) + amount
            winner = pbp_winner(states[category], category, team_a, team_b)
            score_a, score_b = pbp_category_score(states, team_a, team_b)
            lead_change = winner_before != winner and winner != "Tie"
            lead_tied = winner == "Tie" and winner_before not in ["", "Tie"]
            previous_winners[category] = winner
            current_score = (score_a, score_b)
            if current_score != previous_score:
                chart_rows.append({"wallclock": row.get("wallclock"), "game_date": row.get("game_date", ""), team_a: score_a, team_b: score_b})
                previous_score = current_score
            if lead_change or lead_tied:
                rows.append({
                    "wallclock": row.get("wallclock"),
                    "game_date": row.get("game_date", ""),
                    "category": category,
                    "description": row.get("description", ""),
                    "sbc_team": sbc_team,
                    "team_a_total": pbp_running_display(states[category][team_a], category),
                    "team_b_total": pbp_running_display(states[category][team_b], category),
                    "winner": winner,
                    "overall_a": score_a,
                    "overall_b": score_b,
                    "lead_change": lead_change,
                    "tied": lead_tied,
                })

    return pd.DataFrame(rows), pd.DataFrame(chart_rows)


def build_pbp_category_chart_data(events, team_a, team_b):
    if events.empty:
        return pd.DataFrame()
    filtered = events.copy().sort_values(["wallclock", "game_id", "stat", "player"]).reset_index(drop=True)
    states = empty_pbp_category_states(team_a, team_b)
    rows = []
    for _, row in filtered.iterrows():
        sbc_team = str(row.get("sbc_team", ""))
        if sbc_team not in [team_a, team_b]:
            continue
        for category in pbp_categories_for_event(row):
            delta = pbp_category_delta(row, category)
            for key, amount in delta.items():
                states[category][sbc_team][key] = states[category][sbc_team].get(key, 0) + amount
            for team in [team_a, team_b]:
                state = states[category][team]
                if category in ["2PT%", "3PT%", "FT%"]:
                    att = state.get("att", 0)
                    value = (state.get("made", 0) / att * 100) if att else 0
                elif category == "TS%":
                    denom = 2 * (state.get("fga", 0) + 0.44 * state.get("fta", 0))
                    value = (state.get("points", 0) / denom * 100) if denom else 0
                else:
                    value = state.get("value", 0)
                rows.append({
                    "wallclock": row.get("wallclock"),
                    "game_date": row.get("game_date", ""),
                    "category": PBP_STAT_LABELS.get(category, category),
                    "team": live_team_full_name(team),
                    "value": value,
                })
    return pd.DataFrame(rows)


def pbp_team_header_html(team):
    logo = team_logo_for_name(team)
    return f"""
        <span class="sbc-pbp-team-head">
            <img src="{escape(str(logo), quote=True)}" alt="{escape(live_team_full_name(team), quote=True)} logo">
            <strong>{escape(team_abbrev_for_name(team))}</strong>
        </span>
    """


def pbp_leader_html(winner):
    if winner == "Tie":
        return '<span class="sbc-pbp-tie-text">Tie</span>'
    logo = team_logo_for_name(winner)
    return f"""
        <span class="sbc-pbp-leader-logo">
            <img src="{escape(str(logo), quote=True)}" alt="{escape(live_team_full_name(winner), quote=True)} logo">
        </span>
    """


def pbp_row_class(row):
    if bool(row.get("lead_change")):
        return "sbc-pbp-lead-change-row"
    if bool(row.get("tied")) or str(row.get("winner", "")) == "Tie":
        return "sbc-pbp-tied-row"
    return ""


def pbp_chart_game_day(wallclock_series, game_date_series=None):
    if game_date_series is not None:
        dates = pd.to_datetime(game_date_series.astype(str), format="%Y%m%d", errors="coerce")
        labels = dates.dt.strftime("%b %d")
        if labels.notna().any():
            fallback = pbp_chart_game_day(wallclock_series)
            return labels.fillna(fallback)
    ts = pd.to_datetime(wallclock_series, errors="coerce", utc=True)
    return (ts.dt.tz_convert(ZoneInfo("America/New_York")) - pd.Timedelta(hours=4)).dt.strftime("%b %d")


def pbp_slate_day_label(game_day, game_date=None, game_count=0):
    parsed = pd.to_datetime(str(game_date), format="%Y%m%d", errors="coerce") if game_date is not None else pd.NaT
    if pd.notna(parsed):
        label = re.sub(r" 0(\d)", r" \1", parsed.strftime("%a, %b %d"))
    else:
        label = str(game_day)
    count = int(game_count or 0)
    game_word = "game" if count == 1 else "games"
    return f"{label} ({count} {game_word})"


def pbp_day_panel_width(day_count):
    try:
        count = max(1, int(day_count))
    except (TypeError, ValueError):
        count = 1
    return max(145, min(420, int(1180 / count)))


def pbp_slate_day_bounds(events):
    if events.empty:
        return pd.DataFrame(columns=["game_day", "game_day_label", "day_start", "day_end", "game_count"])
    bounds = events[["wallclock"] + (["game_date"] if "game_date" in events.columns else []) + (["game_id"] if "game_id" in events.columns else [])].copy()
    bounds["wallclock"] = pd.to_datetime(bounds["wallclock"], errors="coerce", utc=True)
    bounds = bounds.dropna(subset=["wallclock"])
    if bounds.empty:
        return pd.DataFrame(columns=["game_day", "game_day_label", "day_start", "day_end", "game_count"])
    bounds["game_day"] = pbp_chart_game_day(bounds["wallclock"], bounds["game_date"] if "game_date" in bounds.columns else None)
    agg = {"wallclock": ["min", "max"]}
    if "game_date" in bounds.columns:
        agg["game_date"] = "first"
    if "game_id" in bounds.columns:
        agg["game_id"] = pd.Series.nunique
    grouped = bounds.groupby("game_day").agg(agg)
    grouped.columns = ["day_start", "day_end"] + (["game_date"] if "game_date" in bounds.columns else []) + (["game_count"] if "game_id" in bounds.columns else [])
    grouped = grouped.reset_index()
    if "game_count" not in grouped.columns:
        grouped["game_count"] = 0
    if "game_date" not in grouped.columns:
        grouped["game_date"] = ""
    grouped["game_day_label"] = grouped.apply(lambda row: pbp_slate_day_label(row.get("game_day"), row.get("game_date"), row.get("game_count")), axis=1)
    same_time = grouped["day_start"] >= grouped["day_end"]
    grouped.loc[same_time, "day_end"] = grouped.loc[same_time, "day_start"] + pd.Timedelta(hours=1)
    return grouped.sort_values("day_start").reset_index(drop=True)


def pbp_full_slate_day_bounds(events):
    if events.empty or "game_date" not in events.columns:
        return pbp_slate_day_bounds(events)
    game_dates = tuple(sorted(events["game_date"].dropna().astype(str).unique()))
    archive = load_pbp_slate_bounds_for_dates(game_dates, pbp_archive_mtime())
    if archive.empty or "game_date" not in archive.columns:
        return pbp_slate_day_bounds(events)
    return pbp_slate_day_bounds(archive)


def add_pbp_day_positions(df, day_bounds=None):
    out = df.copy()
    out["wallclock"] = pd.to_datetime(out["wallclock"], errors="coerce", utc=True)
    out = out.dropna(subset=["wallclock"]).sort_values("wallclock").reset_index(drop=True)
    if out.empty:
        out["game_day"] = []
        out["day_event_index"] = []
        return out
    out["game_day"] = pbp_chart_game_day(out["wallclock"], out["game_date"] if "game_date" in out.columns else None)
    out["day_event_index"] = out.groupby("game_day").cumcount()
    if day_bounds is None or day_bounds.empty:
        day_bounds = pbp_slate_day_bounds(out)
    if day_bounds is not None and not day_bounds.empty:
        out = out.merge(day_bounds, on="game_day", how="left")
    return out


def add_pbp_category_day_boundaries(chart_data, day_bounds, team_a, team_b, selected_label):
    if chart_data.empty or day_bounds.empty:
        return chart_data
    base = chart_data.copy()
    base["wallclock"] = pd.to_datetime(base["wallclock"], errors="coerce", utc=True)
    additions = []
    for team in [live_team_full_name(team_a), live_team_full_name(team_b)]:
        team_rows = base[base["team"] == team].sort_values("wallclock")
        for _, bound in day_bounds.iterrows():
            for boundary in ["day_start", "day_end"]:
                ts = bound.get(boundary)
                if pd.isna(ts):
                    continue
                prior = team_rows[team_rows["wallclock"] <= ts]
                value = prior["value"].iloc[-1] if not prior.empty else 0
                additions.append({
                    "wallclock": ts,
                    "game_date": "",
                    "category": selected_label,
                    "team": team,
                    "value": value,
                    "game_day": bound.get("game_day", ""),
                })
    if additions:
        base = pd.concat([base, pd.DataFrame(additions)], ignore_index=True)
    return base.sort_values(["wallclock", "team"]).drop_duplicates(["game_day", "wallclock", "team"], keep="last").reset_index(drop=True)


def add_pbp_line_day_boundaries(chart_data, day_bounds, value_col):
    if chart_data.empty or day_bounds.empty or value_col not in chart_data.columns:
        return chart_data
    base = chart_data.copy()
    base["wallclock"] = pd.to_datetime(base["wallclock"], errors="coerce", utc=True)
    sorted_rows = base.sort_values("wallclock")
    additions = []
    for _, bound in day_bounds.iterrows():
        game_day = bound.get("game_day", "")
        game_day_label = bound.get("game_day_label", game_day)
        for boundary in ["day_start", "day_end"]:
            ts = bound.get(boundary)
            if pd.isna(ts):
                continue
            prior = sorted_rows[sorted_rows["wallclock"] <= ts]
            value = prior[value_col].iloc[-1] if not prior.empty else 0
            additions.append({
                "wallclock": ts,
                "game_date": "",
                "game_day": game_day,
                "game_day_label": game_day_label,
                value_col: value,
            })
    if additions:
        base = pd.concat([base, pd.DataFrame(additions)], ignore_index=True, sort=False)
    return base.sort_values("wallclock").drop_duplicates(["game_day", "wallclock"], keep="last").reset_index(drop=True)


def add_pbp_score_day_boundaries(chart_data, day_bounds, team_a, team_b):
    if chart_data.empty or day_bounds.empty:
        return chart_data
    base = chart_data.copy()
    base["wallclock"] = pd.to_datetime(base["wallclock"], errors="coerce", utc=True)
    additions = []
    sorted_rows = base.sort_values("wallclock")
    for _, bound in day_bounds.iterrows():
        for boundary in ["day_start", "day_end"]:
            ts = bound.get(boundary)
            if pd.isna(ts):
                continue
            prior = sorted_rows[sorted_rows["wallclock"] <= ts]
            score_a = prior[team_a].iloc[-1] if not prior.empty else 206.5
            score_b = prior[team_b].iloc[-1] if not prior.empty else 206.5
            additions.append({
                "wallclock": ts,
                "game_date": "",
                team_a: score_a,
                team_b: score_b,
                "game_day": bound.get("game_day", ""),
            })
    if additions:
        base = pd.concat([base, pd.DataFrame(additions)], ignore_index=True)
    return base.sort_values("wallclock").drop_duplicates(["game_day", "wallclock"], keep="last").reset_index(drop=True)


def pbp_chart_hour(value):
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(ts):
        return float("nan")
    eastern = ts.tz_convert(ZoneInfo("America/New_York"))
    hour = eastern.hour + eastern.minute / 60 + eastern.second / 3600
    if hour < 4:
        hour += 24
    return hour


def pbp_hour_axis_values(day_bounds):
    if day_bounds is None or day_bounds.empty:
        return list(range(17, 25)), [17, 25]
    starts = day_bounds["day_start"].apply(pbp_chart_hour)
    ends = day_bounds["day_end"].apply(pbp_chart_hour)
    start_value = pd.to_numeric(starts, errors="coerce").min()
    end_value = pd.to_numeric(ends, errors="coerce").max()
    if pd.isna(start_value) or pd.isna(end_value) or not math.isfinite(float(start_value)) or not math.isfinite(float(end_value)):
        start, end = 17, 25
    else:
        start = int(math.floor(float(start_value)))
        end = int(math.ceil(float(end_value)))
    domain_start = float(start_value)
    domain_end = float(end_value)
    if not math.isfinite(domain_start) or not math.isfinite(domain_end) or domain_start >= domain_end:
        domain_start, domain_end = 17, 25
        start, end = 17, 25
    elif start >= end:
        start, end = int(math.floor(domain_start)), int(math.ceil(domain_end))
    return list(range(start, end + 1)), [domain_start, domain_end]


def pbp_time_axis(values=None, grid=False):
    label_expr = "((datum.value % 24) % 12 == 0 ? '12' : format((datum.value % 24) % 12, '.0f')) + ':00'"
    axis_kwargs = {
        "title": "Time (ET)",
        "labelExpr": label_expr,
        "labelColor": "#667085",
        "titleColor": "#667085",
        "grid": grid,
        "gridColor": "#f2f4f7",
        "domainColor": "#d0d5dd",
        "tickColor": "#d0d5dd",
    }
    if values is not None:
        axis_kwargs["values"] = values
    return alt.Axis(**axis_kwargs)


def pbp_old_time_axis(grid=False):
    return alt.Axis(
        title="Time (ET)",
        format="%-I:00",
        labelColor="#667085",
        titleColor="#667085",
        grid=grid,
        gridColor="#f2f4f7",
        domainColor="#d0d5dd",
        tickColor="#d0d5dd",
        tickCount={"interval": "hour", "step": 1},
    )


def add_pbp_chart_time(df):
    out = df.copy()
    wallclock = pd.to_datetime(out["wallclock"], errors="coerce", utc=True)
    out["wallclock_et"] = wallclock.dt.tz_convert(ZoneInfo("America/New_York")).dt.tz_localize(None)
    out["chart_hour"] = wallclock.apply(pbp_chart_hour)
    return out


def add_pbp_chart_hour_edges(df, hour_domain, value_col, group_cols=None, start_value=None, start_overrides=None):
    if df.empty or value_col not in df.columns or "game_day" not in df.columns or "chart_hour" not in df.columns:
        return df
    if not hour_domain or len(hour_domain) < 2:
        return df
    start_hour, end_hour = hour_domain[0], hour_domain[1]
    group_cols = group_cols or []
    key_cols = ["game_day"] + [col for col in group_cols if col in df.columns]
    additions = []
    for _, group in df.sort_values("chart_hour").groupby(key_cols, dropna=False):
        if group.empty:
            continue
        group_day = group["game_day"].iloc[0]
        override_start = start_overrides.get(group_day) if start_overrides else None
        first = group.iloc[0].copy()
        first["chart_hour"] = start_hour
        first[value_col] = override_start if override_start is not None else start_value if start_value is not None else group[value_col].iloc[0]
        last = group.iloc[-1].copy()
        last["chart_hour"] = end_hour
        last[value_col] = group[value_col].iloc[-1]
        additions.extend([first, last])
    if additions:
        df = pd.concat([df, pd.DataFrame(additions)], ignore_index=True, sort=False)
    return df.sort_values(key_cols + ["chart_hour"]).drop_duplicates(key_cols + ["chart_hour"], keep="last").reset_index(drop=True)


def pbp_category_y_scale(selected_category):
    if selected_category in ["2PT%", "3PT%", "FT%"]:
        return alt.Scale(domain=[0, 100], clamp=True)
    if selected_category == "TS%":
        return alt.Scale(domain=[0, 150], clamp=True)
    return alt.Scale()


def pbp_category_y_axis(selected_category):
    values = [0, 25, 50, 75, 100] if selected_category in ["2PT%", "3PT%", "FT%"] else None
    if selected_category == "TS%":
        values = [0, 50, 100, 150]
    axis_kwargs = {
        "labelColor": "#475467",
        "grid": True,
        "gridColor": "#eef2f7",
        "domain": False,
        "title": None,
    }
    if values is not None:
        axis_kwargs["values"] = values
    return alt.Axis(**axis_kwargs)


def render_pbp_category_movement_charts(events, team_a, team_b, selected_category):
    category_chart = build_pbp_category_chart_data(events, team_a, team_b)
    if category_chart.empty:
        return
    selected_label = PBP_STAT_LABELS.get(selected_category, selected_category)
    category_chart = category_chart[category_chart["category"].astype(str) == selected_label].copy()
    if category_chart.empty:
        return
    day_bounds = pbp_full_slate_day_bounds(events)
    category_chart = add_pbp_category_day_boundaries(category_chart, day_bounds, team_a, team_b, selected_label)
    category_chart = add_pbp_day_positions(category_chart, day_bounds)
    if category_chart.empty:
        return
    category_chart = add_pbp_chart_time(category_chart)
    if "game_day_label" not in category_chart.columns:
        category_chart["game_day_label"] = category_chart["game_day"]
    else:
        category_chart["game_day_label"] = category_chart["game_day_label"].fillna(category_chart["game_day"])
    day_label_order = day_bounds.sort_values("day_start")["game_day_label"].dropna().astype(str).tolist() if "game_day_label" in day_bounds.columns else None
    category_chart = category_chart.sort_values(["game_day", "chart_hour", "team"]).drop_duplicates(["game_day", "chart_hour", "team"], keep="last").reset_index(drop=True)
    hour_ticks, hour_domain = pbp_hour_axis_values(day_bounds)
    category_chart = add_pbp_chart_hour_edges(category_chart, hour_domain, "value", group_cols=["team"])
    day_width = pbp_day_panel_width(category_chart["game_day"].nunique())
    render_html(f'<div class="sbc-pbp-mini-chart-title">{escape(selected_label)} Movement</div>')
    render_html(f"""
        <div class="sbc-pbp-chart-key sbc-pbp-chart-key-subtle">
            <span style="--chart-team-color:{escape(str(team_color_for_name(team_a)), quote=True)};">
                <img src="{escape(str(team_logo_for_name(team_a)), quote=True)}" alt="{escape(live_team_full_name(team_a), quote=True)} logo">
                <strong>{escape(team_abbrev_for_name(team_a))}</strong>
            </span>
            <span style="--chart-team-color:{escape(str(team_color_for_name(team_b)), quote=True)};">
                <img src="{escape(str(team_logo_for_name(team_b)), quote=True)}" alt="{escape(live_team_full_name(team_b), quote=True)} logo">
                <strong>{escape(team_abbrev_for_name(team_b))}</strong>
            </span>
        </div>
    """)
    base = alt.Chart(category_chart).encode(
        x=alt.X(
            "chart_hour:Q",
            scale=alt.Scale(domain=hour_domain),
            title="Time (ET)",
            axis=pbp_time_axis(values=hour_ticks, grid=True),
        ),
    )
    y_scale = pbp_category_y_scale(selected_category)
    y_axis = pbp_category_y_axis(selected_category)
    area = base.mark_area(opacity=0.22, interpolate="step-after", clip=True).encode(
        y=alt.Y("value:Q", title=None, scale=y_scale, axis=y_axis, stack=None),
        y2=alt.Y2(datum=0),
        color=alt.Color(
            "team:N",
            scale=alt.Scale(
                domain=[live_team_full_name(team_a), live_team_full_name(team_b)],
                range=[team_color_for_name(team_a), team_color_for_name(team_b)],
            ),
            legend=None,
        ),
    )
    line = base.mark_line(strokeWidth=2.35, interpolate="step-after", clip=True).encode(
        y=alt.Y("value:Q", title=None, scale=y_scale, axis=y_axis),
        color=alt.Color(
            "team:N",
            scale=alt.Scale(
                domain=[live_team_full_name(team_a), live_team_full_name(team_b)],
                range=[team_color_for_name(team_a), team_color_for_name(team_b)],
            ),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("team:N", title="Team"),
            alt.Tooltip("value:Q", title="Value", format=".1f"),
            alt.Tooltip("wallclock_et:T", title="Time (ET)", format="%b %d, %I:%M %p"),
        ],
    )
    mini = (area + line).properties(width=day_width, height=170).facet(
        column=alt.Column("game_day_label:N", title=None, sort=day_label_order, header=alt.Header(labelColor="#344054", labelFontWeight="bold")),
        spacing=6,
    ).resolve_scale(x="independent").configure(
        background="#ffffff",
        view=alt.ViewConfig(stroke="#111827", strokeWidth=1, strokeOpacity=1),
        axis=alt.AxisConfig(labelColor="#344054", titleColor="#344054"),
    )
    with st.container(border=True):
        st.altair_chart(mini, use_container_width=True)


def render_pbp_all_categories_score_chart(chart_table, team_a, team_b, events=None, expected_score_a=None, expected_score_b=None):
    if chart_table.empty:
        return
    chart_cols = ["wallclock", team_a, team_b] + (["game_date"] if "game_date" in chart_table.columns else [])
    chart_data = chart_table[chart_cols].copy()
    day_source = events if events is not None and not events.empty else chart_data
    day_bounds = pbp_full_slate_day_bounds(day_source)
    chart_data = add_pbp_score_day_boundaries(chart_data, day_bounds, team_a, team_b)
    chart_data = add_pbp_day_positions(chart_data, day_bounds)
    if chart_data.empty:
        return
    chart_data["tick_label"] = chart_data["wallclock"].dt.tz_convert(ZoneInfo("America/New_York")).dt.strftime("%b %d, %I:%M %p")
    chart_data["team_a_score"] = pd.to_numeric(chart_data[team_a], errors="coerce").fillna(206.5)
    chart_data["team_b_score"] = pd.to_numeric(chart_data[team_b], errors="coerce").fillna(206.5)
    if expected_score_a is not None and expected_score_b is not None and not chart_data.empty:
        chart_data.loc[chart_data.index[-1], "team_a_score"] = expected_score_a
        chart_data.loc[chart_data.index[-1], "team_b_score"] = expected_score_b
    chart_data = chart_data.sort_values("wallclock").drop_duplicates(["game_day", "wallclock"], keep="last").reset_index(drop=True)
    chart_data = add_pbp_line_day_boundaries(chart_data, day_bounds, "team_b_score")
    chart_data = add_pbp_chart_time(chart_data)
    hour_ticks, hour_domain = pbp_hour_axis_values(day_bounds)
    day_width = pbp_day_panel_width(chart_data["game_day"].nunique())
    chart_data = chart_data.sort_values(["game_day", "wallclock_et"]).drop_duplicates(["game_day", "wallclock_et"], keep="last").reset_index(drop=True)
    if "game_day_label" not in chart_data.columns:
        chart_data["game_day_label"] = chart_data["game_day"]
    else:
        chart_data["game_day_label"] = chart_data["game_day_label"].fillna(chart_data["game_day"])
    day_label_order = day_bounds.sort_values("day_start")["game_day_label"].dropna().astype(str).tolist() if "game_day_label" in day_bounds.columns else None
    score_chart = chart_data[["wallclock", "wallclock_et", "chart_hour", "game_day", "game_day_label", "team_b_score"]].copy()
    score_chart = score_chart.rename(columns={"team_b_score": "value"})
    score_chart["score_top"] = 413
    score_chart["score_bottom"] = 0
    score_chart["score_mid"] = 206.5
    score_chart = score_chart.dropna(subset=["value", "chart_hour"])
    score_chart = score_chart.sort_values(["game_day", "chart_hour"]).drop_duplicates(["game_day", "chart_hour"], keep="last").reset_index(drop=True)
    first_game_day = day_bounds.sort_values("day_start")["game_day"].iloc[0] if not day_bounds.empty else None
    start_overrides = {first_game_day: 206.5} if first_game_day is not None else None
    score_chart = add_pbp_chart_hour_edges(score_chart, hour_domain, "value", start_overrides=start_overrides)
    score_chart["score_top"] = 413
    score_chart["score_bottom"] = 0
    score_chart["score_mid"] = 206.5

    render_html('<div class="sbc-pbp-mini-chart-title">Overall Score</div>')
    base = alt.Chart(score_chart).encode(
        x=alt.X(
            "chart_hour:Q",
            scale=alt.Scale(domain=hour_domain),
            title="Time (ET)",
            axis=pbp_time_axis(values=hour_ticks, grid=True),
        )
    )
    y_axis = alt.Axis(
        values=[0, 113, 206.5, 300, 413],
        labelExpr="datum.value == 113 ? '300' : datum.value == 300 ? '300' : datum.value == 413 ? '0' : datum.value",
        title=None,
        labelColor="#475467",
        grid=True,
        gridColor="#eef2f7",
        tickColor="#d0d5dd",
        domain=False,
    )
    top_area = base.mark_area(color=team_color_for_name(team_a), opacity=0.28, interpolate="step-after", clip=True).encode(
        y=alt.Y("score_top:Q", scale=alt.Scale(domain=[0, 413]), axis=y_axis, stack=None),
        y2=alt.Y2("value:Q"),
    )
    bottom_area = base.mark_area(color=team_color_for_name(team_b), opacity=0.28, interpolate="step-after", clip=True).encode(
        y=alt.Y("value:Q", scale=alt.Scale(domain=[0, 413]), axis=y_axis, stack=None),
        y2=alt.Y2("score_bottom:Q"),
    )
    midpoint = base.mark_line(color="#111827", strokeWidth=1.2, opacity=0.82, interpolate="step-after").encode(
        y=alt.Y("score_mid:Q", scale=alt.Scale(domain=[0, 413]), axis=y_axis),
    )
    line = base.mark_line(color="#111827", strokeWidth=2.8, interpolate="step-after", clip=True).encode(
        y=alt.Y("value:Q", scale=alt.Scale(domain=[0, 413]), axis=y_axis),
        tooltip=[
            alt.Tooltip("wallclock_et:T", title="Time (ET)", format="%b %d, %I:%M %p"),
            alt.Tooltip("value:Q", title=live_team_full_name(team_b), format=".1f"),
        ],
    )
    chart = (top_area + bottom_area + midpoint + line).properties(width=day_width, height=220).facet(
        column=alt.Column("game_day_label:N", title=None, sort=day_label_order, header=alt.Header(labelColor="#344054", labelFontWeight="bold")),
        spacing=6,
    ).resolve_scale(x="independent").configure(
        background="#ffffff",
        axis=alt.AxisConfig(labelColor="#344054", titleColor="#344054", gridColor="#eef2f7", domainColor="#d0d5dd"),
        view=alt.ViewConfig(stroke="#111827", strokeWidth=1, strokeOpacity=1),
    )
    with st.container(border=True):
        render_html(f"""
            <div class="sbc-pbp-chart-key sbc-pbp-chart-key-subtle">
                <span style="--chart-team-color:{escape(str(team_color_for_name(team_a)), quote=True)};">
                    <img src="{escape(str(team_logo_for_name(team_a)), quote=True)}" alt="{escape(live_team_full_name(team_a), quote=True)} logo">
                    <strong>{escape(team_abbrev_for_name(team_a))}</strong>
                </span>
                <span style="--chart-team-color:{escape(str(team_color_for_name(team_b)), quote=True)};">
                    <img src="{escape(str(team_logo_for_name(team_b)), quote=True)}" alt="{escape(live_team_full_name(team_b), quote=True)} logo">
                    <strong>{escape(team_abbrev_for_name(team_b))}</strong>
                </span>
            </div>
        """)
        st.altair_chart(chart, use_container_width=True)


def render_matchup_pbp_tab(rows, team_a, team_b, key_prefix, expected_score_a=None, expected_score_b=None):
    events = matchup_pbp_events(rows, team_a, team_b)
    if events.empty:
        render_html('<div class="sbc-empty-state">No play-by-play rows are available for this matchup yet. The current PBP sample only covers the first 2024-25 matchup period.</div>')
        return

    category = st.selectbox(
        "Play-by-play category",
        options=["ALL"] + BOX_SCORE_CATEGORY_ORDER,
        format_func=lambda stat: PBP_STAT_LABELS.get(stat, boxscore_stat_label(stat)),
        key=f"{key_prefix}_pbp_category",
    )
    if category == "ALL":
        lead_table, chart_table = build_pbp_all_category_leads(events, team_a, team_b)
        if chart_table.empty:
            render_html('<div class="sbc-empty-state">No play-by-play rows are available for this matchup yet.</div>')
            return
        if lead_table.empty:
            render_html('<div class="sbc-empty-state">No category lead changes or lead ties have happened yet in this matchup.</div>')
            return
        table = lead_table
        if expected_score_a is not None and expected_score_b is not None:
            final_time = pd.to_datetime(chart_table["wallclock"], errors="coerce", utc=True).max()
            table = pd.concat(
                [
                    table,
                    pd.DataFrame([{
                        "wallclock": final_time,
                        "game_date": chart_table["game_date"].dropna().astype(str).iloc[-1] if "game_date" in chart_table.columns and not chart_table["game_date"].dropna().empty else "",
                        "category": "Final",
                        "description": "Final SBC category score",
                        "sbc_team": "",
                        "team_a_total": "",
                        "team_b_total": "",
                        "winner": team_a if expected_score_a > expected_score_b else team_b if expected_score_b > expected_score_a else "Tie",
                        "overall_a": expected_score_a,
                        "overall_b": expected_score_b,
                        "lead_change": False,
                        "tied": expected_score_a == expected_score_b,
                    }]),
                ],
                ignore_index=True,
            )
        render_pbp_all_categories_score_chart(
            table[["wallclock", "game_date", "overall_a", "overall_b"]].rename(columns={"overall_a": team_a, "overall_b": team_b}),
            team_a,
            team_b,
            events=events,
            expected_score_a=expected_score_a,
            expected_score_b=expected_score_b,
        )
        color_a = team_color_for_name(team_a)
        color_b = team_color_for_name(team_b)
        rows_html = []
        for _, row in table.iterrows():
            sbc_team = str(row.get("sbc_team", ""))
            winner = str(row.get("winner", "Tie"))
            overall_a = score_numeric(row.get("overall_a", 0))
            overall_b = score_numeric(row.get("overall_b", 0))
            overall_winner = team_a if overall_a > overall_b else team_b if overall_b > overall_a else "Tie"
            overall = f"{stat_number(row.get('overall_a', 0))}-{stat_number(row.get('overall_b', 0))}"
            row_class = pbp_row_class(row)
            team_a_active = "sbc-pbp-updated-total" if sbc_team == team_a else ""
            team_b_active = "sbc-pbp-updated-total" if sbc_team == team_b else ""
            rows_html.append(f"""
                <tr class="{row_class}" style="--pbp-active-color:{escape(str(team_color_for_name(sbc_team)), quote=True)};">
                    <td>{escape(format_pbp_wallclock(row.get('wallclock')))}</td>
                    <td><strong>{escape(PBP_STAT_LABELS.get(str(row.get('category', '')), str(row.get('category', ''))))}</strong></td>
                    <td class="sbc-pbp-description">{escape(str(row.get('description', '')))}</td>
                    <td class="sbc-pbp-total-cell {team_a_active}">{escape(str(row.get('team_a_total', '')))}</td>
                    <td class="sbc-pbp-total-cell {team_b_active}">{escape(str(row.get('team_b_total', '')))}</td>
                    <td>{pbp_leader_html(winner)}</td>
                    <td>{pbp_leader_html(overall_winner)}</td>
                    <td>{escape(overall)}</td>
                </tr>
            """)
        render_html(f"""
            <section class="sbc-box-panel sbc-pbp-panel" style="--pbp-a:{escape(str(color_a), quote=True)};--pbp-b:{escape(str(color_b), quote=True)};">
                <div class="sbc-box-panel-head">
                    <span>All Category Lead Changes</span>
                    <em>{escape(str(len(table)))} moments</em>
                </div>
                <div class="sbc-box-table-scroll">
                    <table class="sbc-pbp-table sbc-pbp-all-table">
                        <thead>
                            <tr>
                                <th>Wallclock</th>
                                <th>Category</th>
                                <th>Description</th>
                                <th>{pbp_team_header_html(team_a)}</th>
                                <th>{pbp_team_header_html(team_b)}</th>
                                <th>Leader</th>
                                <th>Overall Leader</th>
                                <th>Overall</th>
                            </tr>
                        </thead>
                        <tbody>{''.join(rows_html)}</tbody>
                    </table>
                </div>
            </section>
        """)
        return

    render_pbp_category_movement_charts(events, team_a, team_b, category)

    play_filter = st.radio(
        "Play filter",
        options=["All plays", "Lead changes only"],
        index=0,
        horizontal=True,
        key=f"{key_prefix}_pbp_play_filter",
    )
    lead_changes_only = play_filter == "Lead changes only"
    table = build_pbp_running_table(events, category, team_a, team_b)
    if lead_changes_only and not table.empty:
        table = table[table["lead_change"]].copy()
    if table.empty:
        render_html('<div class="sbc-empty-state">No plays matched that category for this matchup.</div>')
        return

    color_a = team_color_for_name(team_a)
    color_b = team_color_for_name(team_b)
    rows_html = []
    for _, row in table.iterrows():
        sbc_team = str(row.get("sbc_team", ""))
        winner = str(row.get("winner", "Tie"))
        row_class = pbp_row_class(row)
        team_a_active = "sbc-pbp-updated-total" if sbc_team == team_a else ""
        team_b_active = "sbc-pbp-updated-total" if sbc_team == team_b else ""
        rows_html.append(f"""
            <tr class="{row_class}" style="--pbp-active-color:{escape(str(team_color_for_name(sbc_team)), quote=True)};">
                <td>{escape(format_pbp_wallclock(row.get('wallclock')))}</td>
                <td class="sbc-pbp-description">{escape(str(row.get('description', '')))}</td>
                <td class="sbc-pbp-total-cell {team_a_active}">{escape(str(row.get('team_a_total', '')))}</td>
                <td class="sbc-pbp-total-cell {team_b_active}">{escape(str(row.get('team_b_total', '')))}</td>
                <td>{pbp_leader_html(winner)}</td>
            </tr>
        """)

    render_html(f"""
        <section class="sbc-box-panel sbc-pbp-panel" style="--pbp-a:{escape(str(color_a), quote=True)};--pbp-b:{escape(str(color_b), quote=True)};">
            <div class="sbc-box-panel-head">
                <span>{escape(PBP_STAT_LABELS.get(category, category))} Play-by-Play</span>
                <em>{escape(str(len(table)))} plays</em>
            </div>
            <div class="sbc-box-table-scroll">
                <table class="sbc-pbp-table">
                    <thead>
                        <tr>
                            <th>Wallclock</th>
                            <th>Description</th>
                            <th>{pbp_team_header_html(team_a)}</th>
                            <th>{pbp_team_header_html(team_b)}</th>
                            <th>Leader</th>
                        </tr>
                    </thead>
                    <tbody>{''.join(rows_html)}</tbody>
                </table>
            </div>
        </section>
    """)


@st.dialog("SBCFBL Box Score", width="large")
def render_matchup_boxscore_dialog(matchup_row, rosters_df):
    render_matchup_boxscore(matchup_row, rosters_df, key_prefix="dialog")


def render_matchup_boxscore(matchup_row, rosters_df, key_prefix="inline", show_players=True):
    team_a = str(matchup_row.get("TeamA", ""))
    team_b = str(matchup_row.get("TeamB", ""))
    score_a = matchup_row.get("TeamA_Score", matchup_row.get("TeamAScore", ""))
    score_b = matchup_row.get("TeamB_Score", matchup_row.get("TeamBScore", ""))
    info_a = team_info.get(team_a, {})
    info_b = team_info.get(team_b, {})
    color_a = info_a.get("bg", "#111827")
    color_b = info_b.get("bg", "#334155")
    secondary_a = info_a.get("bg2", color_a)
    secondary_b = info_b.get("bg2", color_b)
    font_a = team_font_for_name(team_a)
    font_b = team_font_for_name(team_b)
    period_label = period_date_label(matchup_row.get("Year", ""), matchup_row.get("Period", ""), f'P{matchup_row.get("Period", "")}')
    round_label = str(matchup_row.get("Round", matchup_row.get("Type", "")))
    type_label = str(matchup_row.get("Type", ""))
    title_label = boxscore_title_for_round(round_label, type_label)
    a_winner = score_numeric(score_a) >= score_numeric(score_b)
    b_winner = score_numeric(score_b) > score_numeric(score_a)

    render_html(f"""
        <section class="sbc-box-dialog-hero" style="--box-a:{escape(str(color_a), quote=True)}; --box-b:{escape(str(color_b), quote=True)};">
            <div class="sbc-box-dialog-kicker">{escape(period_label)}</div>
            <div class="sbc-box-dialog-title">{escape(title_label)}</div>
            <div class="sbc-box-dialog-matchup">
                <div class="sbc-box-dialog-team" style="--box-team:{escape(str(color_a), quote=True)};--box-team-secondary:{escape(str(secondary_a), quote=True)};--box-team-font:{escape(str(font_a), quote=True)};">
                    <img src="{escape(str(info_a.get('logo', '')), quote=True)}" alt="{escape(live_team_full_name(team_a), quote=True)} logo">
                    <div>
                        <strong>{escape(live_team_full_name(team_a))}</strong>
                        <em>{escape(str(matchup_row.get('TeamA_record', '')))}</em>
                    </div>
                    <b class="{'sbc-box-dialog-score-win' if a_winner else ''}">{escape(format_score_value(score_a))}</b>
                </div>
                <div class="sbc-box-dialog-score">
                    <i>Final</i>
                </div>
                <div class="sbc-box-dialog-team sbc-box-dialog-team-home" style="--box-team:{escape(str(color_b), quote=True)};--box-team-secondary:{escape(str(secondary_b), quote=True)};--box-team-font:{escape(str(font_b), quote=True)};">
                    <b class="{'sbc-box-dialog-score-win' if b_winner else ''}">{escape(format_score_value(score_b))}</b>
                    <div>
                        <strong>{escape(live_team_full_name(team_b))}</strong>
                        <em>{escape(str(matchup_row.get('TeamB_record', '')))}</em>
                    </div>
                    <img src="{escape(str(info_b.get('logo', '')), quote=True)}" alt="{escape(live_team_full_name(team_b), quote=True)} logo">
                </div>
            </div>
        </section>
    """)

    rows = matchup_boxscore_rows(matchup_row, rosters_df)
    if rows.empty:
        render_html('<div class="sbc-empty-state">No player-game box score rows matched this matchup yet. Check the Fantrax-to-ESPN mapping file for unmapped active players.</div>')
        return

    team_totals = team_boxscore_totals(rows)
    category_table, _, _ = matchup_category_results(team_totals, team_a, team_b)

    render_category_votes_box(category_table, team_totals, team_a, team_b)

    if not show_players:
        return

    box_tab, pbp_tab = st.tabs(["Box Score", "Play-by-play"])
    with box_tab:
        view_mode = st.radio(
            "Box score view",
            options=["Game rows", "Aggregate players"],
            index=0,
            horizontal=True,
            key=f"{key_prefix}_box_view_{matchup_row.get('Game_ID', matchup_row.get('Year', ''))}_{matchup_row.get('Period', '')}_{team_a}_{team_b}",
        )
        aggregate = view_mode == "Aggregate players"
        render_player_boxscore_split(rows, team_a, team_b, aggregate=aggregate)
    with pbp_tab:
        render_matchup_pbp_tab(
            rows,
            team_a,
            team_b,
            key_prefix=f"{key_prefix}_{matchup_row.get('Game_ID', matchup_row.get('Year', ''))}_{matchup_row.get('Period', '')}_{team_a}_{team_b}",
            expected_score_a=score_numeric(score_a),
            expected_score_b=score_numeric(score_b),
        )


def render_selected_team_player_boxscore(schedule_rows, selected_team, rosters_df, key_prefix):
    if schedule_rows is None or schedule_rows.shape[0] == 0:
        render_html('<div class="sbc-empty-state">No scheduled matchup player rows are available for this period.</div>')
        return
    pieces = []
    for _, schedule_row in schedule_rows.iterrows():
        matchup_rows = matchup_boxscore_rows(schedule_row.to_dict(), rosters_df)
        if not matchup_rows.empty:
            pieces.append(matchup_rows[matchup_rows["sbc_team"] == selected_team])
    pieces = [piece for piece in pieces if piece is not None and not piece.empty]
    if not pieces:
        render_html('<div class="sbc-empty-state">No player-game box score rows matched this team for the selected period.</div>')
        return
    rows = pd.concat(pieces, ignore_index=True)
    view_mode = st.radio(
        "Box score view",
        options=["Game rows", "Aggregate players"],
        index=0,
        horizontal=True,
        key=f"{key_prefix}_selected_team_box_view_{selected_team}",
    )
    aggregate = view_mode == "Aggregate players"
    render_player_boxscore_team(aggregate_boxscore_players(rows) if aggregate else rows, selected_team, aggregate)
    return aggregate


def render_team_player_boxscore_for_matchup(matchup_row, team_name, rosters_df, aggregate=False):
    rows = matchup_boxscore_rows(matchup_row, rosters_df)
    rows = rows[rows["sbc_team"] == team_name] if not rows.empty else rows
    if rows.empty:
        render_html(f'<div class="sbc-empty-state">No player-game rows matched {escape(live_team_full_name(team_name))} for this matchup.</div>')
        return
    render_player_boxscore_team(aggregate_boxscore_players(rows) if aggregate else rows, team_name, aggregate)


def season_label_from_year(year):
    try:
        year = int(year)
    except (TypeError, ValueError):
        return str(year or "")
    return f"{year - 1}-{str(year)[-2:]}"


def player_stats_options(rosters_df):
    if rosters_df is None or rosters_df.empty:
        return pd.DataFrame(columns=["fantrax_id", "display_name"])
    work = rosters_df.copy()
    year_col = "Year" if "Year" in work.columns else "year"
    work = work[work.get("status", "").astype(str).str.upper() == "ACTIVE"].copy()
    bridge = build_fantrax_to_espn_bridge().rename(columns={"fantraxId": "fantrax_id"})
    options = (
        work[["id"]]
        .dropna()
        .drop_duplicates()
        .rename(columns={"id": "fantrax_id"})
        .merge(bridge[["fantrax_id", "fantrax_name", "espn_player_id"]], on="fantrax_id", how="left")
    )
    options["display_name"] = options["fantrax_name"].fillna(options["fantrax_id"]).astype(str)
    options = options.sort_values("display_name", key=lambda col: col.str.lower()).reset_index(drop=True)
    return options


def player_name_match_key(value):
    text = "" if is_blank_value(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = " ".join(text.lower().replace(".", "").replace("'", "").split())
    replacements = {
        "alperun sengun": "alperen sengun",
        "cam thomas": "cameron thomas",
        "pj washington": "p.j. washington",
        "scotty pippen": "scotty pippen jr",
        "nikola jovic": "nikola jovi",
        "alex sarr": "alexandre sarr",
    }
    text = replacements.get(text, text)
    suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
    parts = [part for part in text.split() if part not in suffixes]
    return " ".join(parts)


def current_player_contract(player_name, cap_df):
    if cap_df is None or cap_df.empty or "Player" not in cap_df.columns:
        return {}
    match_key = player_name_match_key(player_name)
    row = cap_df[cap_df["Player"].apply(player_name_match_key) == match_key]
    if row.empty:
        return {}
    row = row.iloc[0]
    salary_col = f"Y{current_year}"
    type_col = f"Type{current_year}"
    salary = row.get(salary_col, "")
    active_types = {"Guaranteed", "Non-Guaranteed"}
    contract_types = active_types | {"Team"}
    future_years = []
    future_total = 0
    for col in cap_df.columns:
        match = re.fullmatch(r"Y(\d{4})", str(col))
        if not match:
            continue
        year = int(match.group(1))
        if year < current_year:
            continue
        year_type = row.get(f"Type{year}", "")
        if year_type not in contract_types:
            continue
        year_salary = pd.to_numeric(pd.Series([row.get(col, 0)]), errors="coerce").fillna(0).iloc[0]
        if year_salary <= 0:
            continue
        future_years.append(year)
        future_total += float(year_salary)
    year_count = len(future_years)
    summary = ""
    if year_count:
        summary = f"{year_count} year{'s' if year_count != 1 else ''}, {format_money(future_total)}"
    team = row.get("Team", "")
    current_type = row.get(type_col, "")
    active_roster = current_type in active_types
    return {
        "team": team,
        "team_key": resolve_team_key(team) if not is_blank_value(team) else "",
        "type": current_type,
        "salary": salary,
        "years": year_count,
        "total": future_total,
        "summary": summary,
        "active_roster": active_roster,
        "status": row.get("Type", ""),
    }


def current_player_contract_lookup(cap_df):
    if cap_df is None or cap_df.empty or "Player" not in cap_df.columns:
        return {}
    return {
        player_name_match_key(row.get("Player", "")): current_player_contract(row.get("Player", ""), cap_df)
        for _, row in cap_df.iterrows()
        if not is_blank_value(row.get("Player", ""))
    }


def current_active_player_keys_for_team(cap_df, team):
    if cap_df is None or cap_df.empty or "Player" not in cap_df.columns:
        return set()
    team_key = resolve_team_key(team)
    type_col = f"Type{current_year}"
    if type_col not in cap_df.columns or "Team" not in cap_df.columns:
        return set()
    work = cap_df.copy()
    work["_team_key"] = work["Team"].apply(resolve_team_key)
    active_types = {"Guaranteed", "Non-Guaranteed"}
    active = work[(work["_team_key"] == team_key) & (work[type_col].isin(active_types))].copy()
    return {player_name_match_key(value) for value in active["Player"].dropna().tolist()}


def player_awards_for_name(player_name, awards_df):
    work = player_awards_table_for_name(player_name, awards_df)
    if work.empty:
        return []
    return [f"{int(row['_year']) if pd.notna(row['_year']) else row.get('Year', '')} {row.get('Award', '')}" for _, row in work.iterrows()]


def player_awards_table_for_name(player_name, awards_df):
    if awards_df is None or awards_df.empty or not {"Award", "Year", "Winner"}.issubset(awards_df.columns):
        return pd.DataFrame()
    work = awards_df[awards_df["Winner"].astype(str).str.lower() == str(player_name).lower()].copy()
    if work.empty:
        return work
    work["_year"] = pd.to_numeric(work["Year"], errors="coerce")
    return work.sort_values(["_year", "Award"], ascending=[False, True])


def award_family_label(award):
    text = str(award)
    lowered = text.lower()
    if "champion" in lowered:
        return "Champion"
    if "all-star" in lowered or "all star" in lowered:
        return "All-Star"
    if "all-sbc" in lowered:
        return "All-SBC"
    if "pom" in lowered or "player of the month" in lowered:
        return "POM"
    if "pow" in lowered or "player of the week" in lowered:
        return "POW"
    if "rookie of the month" in lowered or "rom" in lowered:
        return "ROM"
    if "all-defense" in lowered:
        return "All-Defense"
    if "all-rookie" in lowered:
        return "All-Rookie"
    return text


def award_summary_chips(awards_table):
    if awards_table is None or awards_table.empty:
        return "<em>No manual awards listed yet.</em>"
    work = awards_table.copy()
    work["Family"] = work["Award"].apply(award_family_label)
    chips = []
    for family, frame in work.groupby("Family", sort=False):
        years = sorted(pd.to_numeric(frame["Year"], errors="coerce").dropna().astype(int).unique().tolist())
        if len(frame) == 1 and years:
            label = f"{years[0]} {family}"
        else:
            label = f"{len(frame)}x {family}"
        chips.append(f"<span>{escape(label)}</span>")
    return "".join(chips)


def render_award_detail_ledger(awards_table):
    if awards_table is None or awards_table.empty:
        return
    work = awards_table.copy()
    work["_award_family"] = work["Award"].apply(award_family_label)
    family_order = ["Champion", "MVP", "Finals MVP", "All-Star", "All-SBC", "All-Defense", "All-Rookie", "POM", "POW", "ROM"]
    order_lookup = {name: idx for idx, name in enumerate(family_order)}
    work["_family_order"] = work["_award_family"].map(order_lookup).fillna(999)
    work = work.sort_values(["_family_order", "Award", "_year"], ascending=[True, True, False])
    rows = []
    for _, row in work.iterrows():
        year_text = str(int(row["_year"])) if pd.notna(row.get("_year")) else str(row.get("Year", ""))
        rows.append(f"""
            <tr>
                <td>{escape(year_text)}</td>
                <td>{escape(str(row.get('Award', '')))}</td>
            </tr>
        """)
    render_html(f"""
        <div class="sbc-awards-section-head"><span>Award Ledger</span><em>Manual awards archive, unsummarized.</em></div>
        <div class="sbc-history-table-wrap">
            <table class="sbc-history-overview-table">
                <thead><tr><th>Year</th><th>Award</th></tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
    """)


def ordinal_text(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)
    suffix = "th"
    if value % 100 not in [11, 12, 13]:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def player_season_count_text(years, active_roster=False):
    if not years:
        if active_roster:
            return "1st year"
        return "No counted seasons"
    count = len(years)
    if active_roster:
        current_count = count if current_year in years else count + 1
        return f"{ordinal_text(current_count)} year"
    if max(years) == current_year:
        return f"{ordinal_text(count)} Season"
    return f"{count} Year{'s' if count != 1 else ''}"


def selected_player_game_rows(fantrax_id, rosters_df, schedule_df):
    if not fantrax_id or rosters_df is None or rosters_df.empty:
        return pd.DataFrame()
    bridge = build_fantrax_to_espn_bridge().rename(columns={"fantraxId": "fantrax_id"})
    bridge_row = bridge[bridge["fantrax_id"] == fantrax_id]
    if bridge_row.empty or is_blank_value(bridge_row.iloc[0].get("espn_player_id")):
        return pd.DataFrame()
    espn_id = str(bridge_row.iloc[0]["espn_player_id"])
    year_col = "Year" if "Year" in rosters_df.columns else "year"
    active = rosters_df[
        (rosters_df["id"].astype(str) == str(fantrax_id))
        & (rosters_df["status"].astype(str).str.upper() == "ACTIVE")
    ].copy()
    if active.empty:
        return pd.DataFrame()
    active["_year"] = pd.to_numeric(active[year_col], errors="coerce").astype("Int64")
    active["_day"] = pd.to_numeric(active["period"], errors="coerce").astype("Int64")
    calendar = period_calendar.copy()
    if calendar.empty:
        return pd.DataFrame()
    calendar["_year"] = pd.to_numeric(calendar["Year"], errors="coerce").astype("Int64")
    calendar["_day"] = pd.to_numeric(calendar["Day"], errors="coerce").astype("Int64")
    calendar["_period"] = pd.to_numeric(calendar["Period"], errors="coerce").astype("Int64")
    calendar["Date"] = pd.to_datetime(calendar["Date"], errors="coerce").dt.normalize()
    active_dates = active.merge(calendar[["_year", "_day", "_period", "Date"]], on=["_year", "_day"], how="left")
    active_dates = active_dates.dropna(subset=["Date"])
    if active_dates.empty:
        return pd.DataFrame()
    box = load_nba_player_boxscores_archive()
    box = box[box["nba_player_id"].astype(str) == espn_id].copy()
    box["Date"] = pd.to_datetime(box["Date"], errors="coerce").dt.normalize()
    rows = box.merge(
        active_dates[["_year", "_day", "_period", "Date", "team_name"]].rename(columns={"team_name": "sbc_team"}),
        left_on=["sbc_year", "Date"],
        right_on=["_year", "Date"],
        how="inner",
    )
    if rows.empty:
        return rows
    rows["sbc_team_key"] = rows["sbc_team"].apply(resolve_team_key)
    sched = schedule_df.copy() if schedule_df is not None else pd.DataFrame()
    if not sched.empty:
        sched["_year"] = pd.to_numeric(sched["Year"], errors="coerce").astype("Int64")
        sched["_period"] = pd.to_numeric(sched["Period"], errors="coerce").astype("Int64")
        sched_a = sched[["_year", "_period", "Type", "TeamA"]].rename(columns={"TeamA": "sbc_team_key", "Type": "sbc_matchup_type"})
        sched_b = sched[["_year", "_period", "Type", "TeamB"]].rename(columns={"TeamB": "sbc_team_key", "Type": "sbc_matchup_type"})
        sched_long = pd.concat([sched_a, sched_b], ignore_index=True).drop_duplicates()
        sched_long["sbc_team_key"] = sched_long["sbc_team_key"].apply(resolve_team_key)
        rows = rows.merge(sched_long[["_year", "_period", "sbc_team_key", "sbc_matchup_type"]], on=["_year", "_period", "sbc_team_key"], how="left")
    if "sbc_matchup_type" not in rows.columns:
        rows["sbc_matchup_type"] = "Regular Season"
    rows["sbc_matchup_type"] = rows["sbc_matchup_type"].fillna("Regular Season")
    return rows


def selected_player_matchup_rows(fantrax_id, rosters_df, schedule_df):
    archive = load_sbc_player_matchup_stats_archive()
    if not archive.empty and "fantrax_id" in archive.columns:
        rows = archive[archive["fantrax_id"].astype(str) == str(fantrax_id)].copy()
        if not rows.empty:
            rows["_period"] = pd.to_numeric(rows["sbc_period"], errors="coerce").astype("Int64")
            rows["Date"] = pd.to_datetime(rows.get("start_date"), errors="coerce")
            rows["display_player"] = rows.get("fantrax_name", rows.get("player_name", ""))
            return rows
    return selected_player_game_rows(fantrax_id, rosters_df, schedule_df)


def valid_matchup_archive_rows(rows):
    if rows is None or rows.empty:
        return rows
    work = rows.copy()
    if "sbc_opponent" in work.columns:
        work = work[~work["sbc_opponent"].apply(is_blank_value)].copy()
    if "Game_ID" in work.columns:
        work = work[~work["Game_ID"].apply(is_blank_value)].copy()
    return work


def dedupe_matchup_archive_for_totals(rows):
    if rows is None or rows.empty or "nba_game_ids" not in rows.columns:
        return rows
    work = rows.copy()
    period_col = "sbc_period" if "sbc_period" in work.columns else "_period"
    team_col = "sbc_team_key" if "sbc_team_key" in work.columns else "sbc_team"
    key_cols = [col for col in ["fantrax_id", "sbc_year", period_col, team_col] if col in work.columns]
    if len(key_cols) < 3:
        return work
    sort_cols = key_cols + [col for col in ["sbc_matchup_type", "Game_ID"] if col in work.columns]
    work = work.sort_values(sort_cols)
    first_rows = work.drop_duplicates(key_cols, keep="first").copy()
    if "sbc_opponent" in work.columns:
        opponents = (
            work.groupby(key_cols)["sbc_opponent"]
            .apply(lambda values: " / ".join(team_abbrev_for_name(resolve_team_key(value)) for value in pd.Series(values).dropna().astype(str).drop_duplicates() if not is_blank_value(value)))
            .reset_index()
        )
        first_rows = first_rows.drop(columns=["sbc_opponent"], errors="ignore").merge(opponents, on=key_cols, how="left")
    if "Game_ID" in work.columns:
        game_ids = (
            work.groupby(key_cols)["Game_ID"]
            .apply(lambda values: " / ".join(pd.Series(values).dropna().astype(str).drop_duplicates()))
            .reset_index()
        )
        first_rows = first_rows.drop(columns=["Game_ID"], errors="ignore").merge(game_ids, on=key_cols, how="left")
    return first_rows


def aggregate_player_season_rows(rows, basis="per_nba"):
    if rows.empty:
        return pd.DataFrame()
    rows = valid_matchup_archive_rows(rows)
    rows = dedupe_matchup_archive_for_totals(rows)
    if rows.empty:
        return pd.DataFrame()
    per_sbc_game = basis == "per_sbc"
    total_basis = basis == "total"
    group_cols = ["sbc_year", "sbc_team"]
    ordered_rows = rows.copy()
    ordered_rows["_sort_date"] = pd.to_datetime(ordered_rows.get("Date"), errors="coerce")
    ordered_rows = ordered_rows.sort_values(["sbc_year", "_sort_date", "_period", "sbc_team"])
    team_order = (
        ordered_rows[group_cols]
        .drop_duplicates()
        .assign(_team_order=lambda frame: frame.groupby("sbc_year").cumcount())
    )
    grouped = rows.groupby(group_cols, as_index=False)[BOX_SCORE_SUM_STATS].sum()
    grouped = grouped.merge(team_order, on=group_cols, how="left")
    if per_sbc_game:
        denom = (
            rows.dropna(subset=["_period"])
            .drop_duplicates(group_cols + ["_period"])
            .groupby(group_cols, as_index=False)
            .size()
            .rename(columns={"size": "_denom_gp"})
        )
        grouped = grouped.merge(denom, on=group_cols, how="left")
    else:
        grouped["_denom_gp"] = grouped["GP"]
    grouped["_matchups"] = grouped["_denom_gp"] if per_sbc_game else pd.NA
    grouped["TS%"] = grouped.apply(lambda row: row["PTS"] / (2 * (row["2PTA"] + row["3PTA"] + 0.44 * row["FTA"])) if (row["2PTA"] + row["3PTA"] + 0.44 * row["FTA"]) else 0, axis=1)
    grouped["2PT%"] = grouped.apply(lambda row: row["2PTM"] / row["2PTA"] if row["2PTA"] else 0, axis=1)
    grouped["3PT%"] = grouped.apply(lambda row: row["3PTM"] / row["3PTA"] if row["3PTA"] else 0, axis=1)
    grouped["FT%"] = grouped.apply(lambda row: row["FTM"] / row["FTA"] if row["FTA"] else 0, axis=1)
    multi = grouped.groupby("sbc_year").filter(lambda frame: frame["sbc_team"].nunique() > 1)
    totals = []
    for year, frame in multi.groupby("sbc_year"):
        total = {col: frame[col].sum() for col in BOX_SCORE_SUM_STATS}
        total["sbc_year"] = year
        total["sbc_team"] = "TOT"
        total["_team_order"] = 999
        if per_sbc_game:
            total["_denom_gp"] = rows[rows["sbc_year"] == year].dropna(subset=["_period"])["_period"].nunique()
            total["_matchups"] = total["_denom_gp"]
        else:
            total["_denom_gp"] = frame["_denom_gp"].sum()
            total["_matchups"] = pd.NA
        total["TS%"] = total["PTS"] / (2 * (total["2PTA"] + total["3PTA"] + 0.44 * total["FTA"])) if (total["2PTA"] + total["3PTA"] + 0.44 * total["FTA"]) else 0
        total["2PT%"] = total["2PTM"] / total["2PTA"] if total["2PTA"] else 0
        total["3PT%"] = total["3PTM"] / total["3PTA"] if total["3PTA"] else 0
        total["FT%"] = total["FTM"] / total["FTA"] if total["FTA"] else 0
        totals.append(total)
    if totals:
        grouped = pd.concat([grouped, pd.DataFrame(totals)], ignore_index=True)
    if not total_basis:
        per_game_cols = BOX_SCORE_SUM_STATS if per_sbc_game else [col for col in BOX_SCORE_SUM_STATS if col != "GP"]
        gp_values = pd.to_numeric(grouped["_denom_gp"], errors="coerce").replace(0, pd.NA)
        for col in per_game_cols:
            grouped[col] = pd.to_numeric(grouped[col], errors="coerce").div(gp_values).fillna(0)
    grouped["Season"] = grouped["sbc_year"].apply(season_label_from_year)
    grouped["_basis"] = basis
    grouped["_is_total"] = (grouped["sbc_team"] == "TOT").astype(int)
    grouped["_team_order"] = pd.to_numeric(grouped["_team_order"], errors="coerce").fillna(998)
    grouped = grouped.sort_values(["sbc_year", "_is_total", "_team_order"])
    return grouped


def stat_sort_ascending(stat):
    return stat == "TO"


def history_stat_column(stat):
    return {"Matchups": "_matchups", "Games Played": "GP"}.get(stat, stat)


def history_stat_label(stat):
    return {"Games Played": "GP"}.get(stat, boxscore_stat_label(stat))


def display_stat_value(row, stat):
    stat = history_stat_column(stat)
    is_pct = stat in ["TS%", "2PT%", "3PT%", "FT%"]
    if is_pct and not stat_has_shooting_volume(row, stat):
        return "-"
    return stat_number(row.get(stat, 0), pct=is_pct, signed=(stat == "+/-"))


def matchup_high_value_text(row, stat):
    display_stat = stat
    stat = history_stat_column(stat)
    if display_stat == "Matchups":
        return stat_number(row.get("_matchups", 1)), ""
    if display_stat == "Games Played":
        return stat_number(row.get("GP", 0)), ""
    if stat in ["2PT%", "3PT%", "FT%"]:
        attempt_col = {"2PT%": "2PTA", "3PT%": "3PTA", "FT%": "FTA"}[stat]
        attempts = stat_number(row.get(attempt_col, 0))
        return display_stat_value(row, stat), f"on {attempts} attempts"
    if stat == "TO":
        return stat_number(row.get("TO", 0)), f"in {stat_number(row.get('MP', 0))} minutes played"
    return display_stat_value(row, stat), stat_subtext(row, stat, show_gp=True)


def history_team_mark_html(team):
    team_key = resolve_team_key(team)
    if team_key not in team_info:
        return escape(str(team or ""))
    visuals = team_visuals(team_key)
    logo_html = f'<img src="{escape(str(visuals.get("logo", "")), quote=True)}" alt="{escape(live_team_full_name(team_key), quote=True)} logo">' if visuals.get("logo") else ""
    return (
        f'<span class="sbc-player-profile-team-mark" style="--profile-team-color:{escape(str(visuals["primary"]), quote=True)};'
        f'--profile-team-secondary:{escape(str(visuals["secondary"]), quote=True)};--profile-team-font:{escape(str(visuals["font"]), quote=True)};">'
        f'{logo_html}<strong>{escape(live_team_full_name(team_key))}</strong></span>'
    )


def matchup_date_text(row):
    start = pd.to_datetime(row.get("start_date", row.get("Date", "")), errors="coerce")
    end = pd.to_datetime(row.get("end_date", row.get("Date", "")), errors="coerce")
    if pd.isna(start):
        return ""
    if pd.isna(end) or start.date() == end.date():
        return start.strftime("%b %d").replace(" 0", " ")
    return f"{start.strftime('%b %d').replace(' 0', ' ')}-{end.strftime('%b %d').replace(' 0', ' ')}"


def player_history_cell_html(row):
    name = str(row.get("fantrax_name", row.get("player_name", "")))
    player_id = row.get("espn_player_id", "")
    image = espn_headshot_url(player_id) if not is_blank_value(player_id) else DRAFT_SILHOUETTE
    return f"""
        <span class="sbc-history-player-cell">
            <img src="{escape(str(image), quote=True)}" alt="{escape(name, quote=True)} headshot">
            <strong>{escape(name)}</strong>
        </span>
    """


def matchup_context_text(row):
    opponent = row.get("sbc_opponent", row.get("opponent", ""))
    period_text = f"P{int(row.get('sbc_period', row.get('_period', 0)))}" if pd.notna(row.get("sbc_period", row.get("_period", pd.NA))) else ""
    try:
        period_label = period_date_label(int(row.get("sbc_year", 0)), int(row.get("sbc_period", row.get("_period", 0))), matchup_date_text(row))
    except (TypeError, ValueError):
        period_label = matchup_date_text(row)
    if opponent and "/" not in str(opponent):
        opponent = team_abbrev_for_name(resolve_team_key(opponent))
    return " / ".join(part for part in [str(row.get("season", "")), period_text, period_label, f"vs {opponent}" if opponent else ""] if part)


def top_matchup_rows(rows, stat, limit=25):
    stat_col = history_stat_column(stat)
    if rows is None or rows.empty or stat_col not in rows.columns:
        return pd.DataFrame()
    work = valid_matchup_archive_rows(rows)
    work = dedupe_matchup_archive_for_totals(work)
    if work.empty:
        return work
    if stat_col in ["TS%", "2PT%", "3PT%", "FT%"]:
        work = work[work.apply(lambda row: stat_has_shooting_volume(row, stat_col), axis=1)].copy()
    work["_stat_sort"] = pd.to_numeric(work[stat_col], errors="coerce")
    work = work.dropna(subset=["_stat_sort"])
    if stat_col in ["2PT%", "3PT%", "FT%"]:
        attempt_col = {"2PT%": "2PTA", "3PT%": "3PTA", "FT%": "FTA"}[stat_col]
        work["_volume_sort"] = pd.to_numeric(work.get(attempt_col, 0), errors="coerce").fillna(0)
        return work.sort_values(["_stat_sort", "_volume_sort"], ascending=[False, False]).head(limit)
    if stat_col == "TO":
        work["_volume_sort"] = pd.to_numeric(work.get("MP", 0), errors="coerce").fillna(0)
        return work.sort_values(["_stat_sort", "_volume_sort"], ascending=[True, False]).head(limit)
    return work.sort_values("_stat_sort", ascending=stat_sort_ascending(stat_col)).head(limit)


def render_matchup_leaderboard(rows, stat, empty_text, limit=25, show_team=True):
    leaders = top_matchup_rows(rows, stat, limit=limit)
    if leaders.empty:
        render_html(f'<div class="sbc-empty-state">{escape(empty_text)}</div>')
        return
    body = []
    for rank, (_, row) in enumerate(leaders.iterrows(), start=1):
        team_value = row.get("sbc_team_key", row.get("sbc_team", ""))
        team_html = history_team_mark_html(team_value) if show_team else ""
        value_text, sub_text = matchup_high_value_text(row, stat)
        body.append(f"""
            <tr>
                <td><strong>{rank}</strong></td>
                <td>{player_history_cell_html(row)}</td>
                {f'<td>{team_html}</td>' if show_team else ''}
                <td><strong>{escape(value_text)}</strong><em>{escape(sub_text)}</em></td>
                <td>{escape(matchup_context_text(row))}</td>
            </tr>
        """)
    team_header = "<th>Team</th>" if show_team else ""
    render_html(f"""
        <div class="sbc-box-table-scroll">
            <table class="sbc-history-overview-table sbc-matchup-high-table">
                <thead><tr><th>#</th><th>Player</th>{team_header}<th>{escape(history_stat_label(stat))}</th><th>Matchup</th></tr></thead>
                <tbody>{''.join(body)}</tbody>
            </table>
        </div>
    """)


def render_player_season_leaders(rows, empty_text):
    if rows is None or rows.empty:
        render_html(f'<div class="sbc-empty-state">{escape(empty_text)}</div>')
        return
    body = []
    for stat in BOX_SCORE_CATEGORY_ORDER:
        work = rows.copy()
        if stat in ["TS%", "2PT%", "3PT%", "FT%"]:
            work = work[work.apply(lambda row: stat_has_shooting_volume(row, stat), axis=1)].copy()
        if work.empty or stat not in work.columns:
            continue
        work["_stat_sort"] = pd.to_numeric(work[stat], errors="coerce")
        work = work.dropna(subset=["_stat_sort"])
        if work.empty:
            continue
        row = work.sort_values("_stat_sort", ascending=stat_sort_ascending(stat)).iloc[0]
        team_value = str(row.get("sbc_team", ""))
        season_context = str(row.get("Season", ""))
        if team_value == "TOT":
            season_context = f"{season_context} / Total"
        elif team_value:
            season_context = f"{season_context} / {live_team_full_name(resolve_team_key(team_value))}"
        body.append(f"""
            <tr>
                <td><strong>{escape(boxscore_stat_label(stat))}</strong></td>
                <td><strong>{escape(display_stat_value(row, stat))}</strong><em>{escape(stat_subtext(row, stat, show_gp=(stat != "MP")))}</em></td>
                <td>{escape(season_context)}</td>
            </tr>
        """)
    if not body:
        render_html(f'<div class="sbc-empty-state">{escape(empty_text)}</div>')
        return
    render_html(f"""
        <div class="sbc-box-table-scroll">
            <table class="sbc-history-overview-table sbc-matchup-high-table">
                <thead><tr><th>Category</th><th>Best Season</th><th>Season</th></tr></thead>
                <tbody>{''.join(body)}</tbody>
            </table>
        </div>
    """)


def render_player_matchup_highs(rows, empty_text):
    if rows is None or rows.empty:
        render_html(f'<div class="sbc-empty-state">{escape(empty_text)}</div>')
        return
    body = []
    for stat in BOX_SCORE_CATEGORY_ORDER:
        leaders = top_matchup_rows(rows, stat, limit=1)
        if leaders.empty:
            continue
        row = leaders.iloc[0]
        value_text, sub_text = matchup_high_value_text(row, stat)
        body.append(f"""
            <tr>
                <td><strong>{escape(boxscore_stat_label(stat))}</strong></td>
                <td><strong>{escape(value_text)}</strong><em>{escape(sub_text)}</em></td>
                <td>{escape(matchup_context_text(row))}</td>
            </tr>
        """)
    if not body:
        render_html(f'<div class="sbc-empty-state">{escape(empty_text)}</div>')
        return
    render_html(f"""
        <div class="sbc-box-table-scroll">
            <table class="sbc-history-overview-table sbc-matchup-high-table">
                <thead><tr><th>Category</th><th>Best Matchup</th><th>Matchup</th></tr></thead>
                <tbody>{''.join(body)}</tbody>
            </table>
        </div>
    """)


def aggregate_matchup_player_rows(rows, basis="total", group_by_team=True):
    if rows is None or rows.empty:
        return pd.DataFrame()
    rows = valid_matchup_archive_rows(rows)
    rows = dedupe_matchup_archive_for_totals(rows)
    if rows.empty:
        return pd.DataFrame()
    group_cols = ["fantrax_id", "fantrax_name", "espn_player_id"]
    if group_by_team:
        group_cols += ["sbc_team", "sbc_team_key"]
    grouped = rows.groupby(group_cols, dropna=False, as_index=False)[BOX_SCORE_SUM_STATS].sum()
    matchups = (
        rows.groupby(group_cols, dropna=False, as_index=False)
        .size()
        .rename(columns={"size": "_matchups"})
    )
    grouped = grouped.merge(matchups, on=group_cols, how="left")
    seasons = (
        rows.groupby(group_cols, dropna=False)["sbc_year"]
        .nunique()
        .reset_index(name="_seasons")
    )
    grouped = grouped.merge(seasons, on=group_cols, how="left")
    grouped["_denom_gp"] = grouped["_matchups"] if basis == "per_sbc" else grouped["GP"]
    grouped = recalc_shooting_stats(grouped)
    if basis != "total":
        gp_values = pd.to_numeric(grouped["_denom_gp"], errors="coerce").replace(0, pd.NA)
        for col in (BOX_SCORE_SUM_STATS if basis == "per_sbc" else [col for col in BOX_SCORE_SUM_STATS if col != "GP"]):
            grouped[col] = pd.to_numeric(grouped[col], errors="coerce").div(gp_values).fillna(0)
    grouped["_basis"] = basis
    return grouped


def render_all_time_player_aggregate_table(rows, empty_text, limit=50, show_team=True, show_seasons=False, sort_stat="PTS", current_contracts=None, highlight_team=None, highlight_player_keys=None):
    if rows is None or rows.empty:
        render_html(f'<div class="sbc-empty-state">{escape(empty_text)}</div>')
        return
    contract_lookup = current_contracts if isinstance(current_contracts, dict) else current_player_contract_lookup(current_contracts)
    sort_col = history_stat_column(sort_stat)
    if sort_col in rows.columns:
        work = rows.sort_values([sort_col, "MP", "GP"], ascending=[stat_sort_ascending(sort_col), False, False]).head(limit).copy()
    else:
        work = rows.sort_values(["PTS", "MP", "GP"], ascending=[False, False, False]).head(limit).copy()
    stats = ["GP", "MP", "TS%", "2PT%", "3PT%", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
    header = "".join(f"<th>{escape(boxscore_stat_label(stat))}</th>" for stat in stats)
    body = []
    highlight_team_key = resolve_team_key(highlight_team) if highlight_team else ""
    highlight_keys = set(highlight_player_keys or [])
    for rank, (_, row) in enumerate(work.iterrows(), start=1):
        player_name = str(row.get("fantrax_name", row.get("player_name", "")))
        player_key = player_name_match_key(player_name)
        contract = contract_lookup.get(player_key, {})
        row_style = ""
        row_class = ""
        contract_team = contract.get("team_key")
        team_matches_scope = not highlight_team_key or contract_team == highlight_team_key
        if player_key in highlight_keys:
            row_style = f' style="--ledger-team-color:{escape(str(team_color_for_name(highlight_team_key)), quote=True)};"'
            row_class = ' class="sbc-ledger-active-row"'
        elif contract.get("active_roster") and contract_team in team_info and team_matches_scope:
            row_style = f' style="--ledger-team-color:{escape(str(team_color_for_name(contract.get("team_key"))), quote=True)};"'
            row_class = ' class="sbc-ledger-active-row"'
        team_html = history_team_mark_html(row.get("sbc_team_key", row.get("sbc_team", ""))) if show_team else ""
        cells = "".join(stat_cell_html(row, stat, show_gp=(stat != "MP")) for stat in stats)
        season_cell = f"<td>{escape(stat_number(row.get('_seasons', 0)))}</td>" if show_seasons else ""
        team_cell = f"<td>{team_html}</td>" if show_team else ""
        body.append(f"""
            <tr{row_class}{row_style}>
                <td><strong>{rank}</strong></td>
                <td>{player_history_cell_html(row)}</td>
                {season_cell}
                {team_cell}
                <td>{escape(stat_number(row.get('_matchups', 0)))} </td>
                {cells}
            </tr>
        """)
    season_header = "<th>Seasons</th>" if show_seasons else ""
    team_header = "<th>Team</th>" if show_team else ""
    render_html(f"""
        <div class="sbc-box-table-scroll">
            <table class="sbc-history-overview-table sbc-matchup-high-table sbc-ledger-table">
                <thead><tr><th>#</th><th>Player</th>{season_header}{team_header}<th>Matchups</th>{header}</tr></thead>
                <tbody>{''.join(body)}</tbody>
            </table>
        </div>
    """)


def render_player_stats_table(rows, empty_text):
    if rows.empty:
        render_html(f'<div class="sbc-empty-state">{escape(empty_text)}</div>')
        return
    stats = ["MP", "TS%", "2PT%", "3PT%", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
    header = "".join(f"<th>{escape(boxscore_stat_label(stat))}</th>" for stat in stats)
    body = []
    for _, row in rows.iterrows():
        cells = "".join(stat_cell_html(row, stat) for stat in stats)
        team_value = str(row.get("sbc_team", ""))
        if team_value == "TOT":
            team_html = f'<span class="sbc-player-profile-team-mark sbc-player-profile-team-total"><img src="{league_logo_html}" alt="SBCFBL logo"><strong>TOT</strong><em>Total</em></span>'
        else:
            team_key = resolve_team_key(team_value)
            visuals = team_visuals(team_key) if team_key in team_info else {"primary": LEAGUE_PRIMARY, "secondary": LEAGUE_SECONDARY, "font": LEAGUE_FONT, "logo": ""}
            logo_html = f'<img src="{escape(str(visuals.get("logo", "")), quote=True)}" alt="{escape(team_value, quote=True)} logo">' if visuals.get("logo") else ""
            team_html = (
                f'<span class="sbc-player-profile-team-mark" style="--profile-team-color:{escape(str(visuals["primary"]), quote=True)};'
                f'--profile-team-secondary:{escape(str(visuals["secondary"]), quote=True)};--profile-team-font:{escape(str(visuals["font"]), quote=True)};">'
                f'{logo_html}<strong>{escape(live_team_full_name(team_key) if team_key in team_info else team_value)}</strong></span>'
            )
        body.append(f"""
            <tr>
                <td class="sbc-player-profile-season {'sbc-player-profile-season-total' if team_value == 'TOT' else ''}"><strong>{escape(str(row.get('Season', '')))}</strong>{'<em>Total</em>' if team_value == 'TOT' else ''}</td>
                <td class="sbc-player-profile-team">{team_html}</td>
                {cells}
            </tr>
        """)
    render_html(f"""
        <div class="sbc-box-table-scroll">
            <table class="sbc-player-profile-table">
                <thead><tr><th>Season</th><th>Team</th>{header}</tr></thead>
                <tbody>{''.join(body)}</tbody>
            </table>
        </div>
    """)


def current_period_index(options):
    try:
        current_value = int(current_matchup)
    except (TypeError, ValueError):
        current_value = options[-1]
    return options.index(min(current_value, options[-1]))


MAIN_NAV_LABELS = {
    "Team Hub": "🏠 Team Hub",
    "League Hub": "🏟️ League Hub",
    "Trade Machine": "🔁 Trade Machine",
    "Free Agency": "📝 Free Agency",
    "About": "ℹ️ About",
    "Data Checks": "🧪 Data Checks",
}

TEAM_NAV_LABELS = {
    "Cap": "💰 Cap",
    "Picks": "🎯 Picks",
    "Live": "📡 Live",
    "Schedule": "🗓️ Schedule",
    "History": "📚 History",
}

LEAGUE_NAV_LABELS = {
    "Overview": "🌐 Overview",
    "Scoreboard": "🏀 Scoreboard",
    "Standings": "📊 Standings",
    "Players": "👤 Players",
    "Draft Picks": "🎯 Draft Picks",
    "History": "📚 History",
}

HISTORY_NAV_LABELS = {
    "Overview": "🌐 Overview",
    "Scoreboard": "🏀 Scoreboard",
    "Playoff Bracket": "🏆 Playoff Bracket",
    "In-Season Tournament": "🏅 In-Season Tournament",
    "Player Stats": "📈 Player Stats",
    "Awards": "⭐ Awards",
    "Draft History": "🎓 Draft History",
}
HISTORY_NAV_LABELS["All-Time Stats"] = "📊 All-Time Stats"

FREE_AGENCY_NAV_LABELS = {
    "League View": "🌐 League View",
    "My Bids": "🙋 My Bids",
    "Commish View": "🧑‍⚖️ Commish View",
}


def nav_label(labels):
    return lambda value: labels.get(value, value)


requested_main_page = st.session_state.get("sbc_main_page", "Team Hub")
requested_team_page = st.session_state.get("sbc_team_page", "Cap")
requested_league_page = st.session_state.get("sbc_league_page", "Overview")
requested_history_page = st.session_state.get("sbc_history_page", "Overview")

need_team_data = requested_main_page == "Team Hub" and requested_team_page in ["Cap", "Picks", "Live", "Schedule"]
need_trade_data = requested_main_page == "Trade Machine"
need_fa_data = requested_main_page == "Free Agency"
need_checks_data = requested_main_page == "Data Checks"
need_league_overview = requested_main_page == "League Hub" and requested_league_page == "Overview"
need_league_players = requested_main_page == "League Hub" and requested_league_page == "Players"
need_league_picks = requested_main_page == "League Hub" and requested_league_page == "Draft Picks"
need_league_standings = requested_main_page == "League Hub" and requested_league_page == "Standings"
need_league_scoreboard = requested_main_page == "League Hub" and requested_league_page == "Scoreboard"
need_history = requested_main_page == "League Hub" and requested_league_page == "History"
need_history_awards = need_history and requested_history_page in ["Awards", "Overview", "Player Stats"]
need_history_draft = need_history and requested_history_page == "Draft History"
need_history_stats = need_history and requested_history_page in ["Overview", "Scoreboard", "Playoff Bracket", "In-Season Tournament", "Player Stats", "All-Time Stats"]

need_team_history = requested_main_page == "Team Hub" and requested_team_page == "History"
need_df = need_team_data or need_team_history or need_trade_data or need_fa_data or need_checks_data or need_league_overview or need_league_players or need_history_draft or (need_history and requested_history_page in ["Overview", "Player Stats"])
need_pics = need_team_data or need_trade_data or need_fa_data or need_checks_data or need_league_players or need_history_awards or need_history_draft or (need_history and requested_history_page == "Player Stats")
need_exceptions = need_team_data or need_trade_data or need_fa_data or need_checks_data or need_league_overview
need_base_cap = need_team_data or need_trade_data or need_checks_data or need_league_overview
need_dp = (requested_main_page == "Team Hub" and requested_team_page == "Picks") or need_trade_data or need_checks_data or need_league_picks
need_ft = need_checks_data
need_standings = need_league_overview or need_league_standings or need_league_scoreboard or need_history_stats or need_history_draft
need_dh = need_history_draft
need_all_time_team_stats = (requested_main_page == "Team Hub" and requested_team_page == "Live") or need_history_stats or need_history_awards
need_boxscore_data = (requested_main_page == "Team Hub" and requested_team_page in ["Live", "Schedule"]) or need_league_scoreboard or (need_history and requested_history_page == "Scoreboard")
need_all_time_rosters = need_history_awards or need_boxscore_data or (need_history and requested_history_page == "Player Stats")
need_all_time_schedule = (requested_main_page == "Team Hub" and requested_team_page in ["Live", "Schedule"]) or need_league_scoreboard or need_league_standings or need_history
need_current_matchup = (requested_main_page == "Team Hub" and requested_team_page == "Live") or need_league_scoreboard or (need_history and requested_history_page == "Scoreboard")
need_period_calendar = need_all_time_schedule or need_all_time_team_stats or need_standings or need_current_matchup or need_history_awards

df = load_required_data("Cap sheet data", get_data) if need_df else pd.DataFrame()
pics = load_required_data("Player pictures", get_pictures) if need_pics else pd.DataFrame()
exceptions = load_required_data("Exceptions", get_exceptions) if need_exceptions else pd.DataFrame()
base_cap = load_required_data("Base cap", get_base_cap) if need_base_cap else pd.DataFrame()
dp = load_required_data("Draft picks", get_draft_picks) if need_dp else pd.DataFrame()
ft_roster = load_optional_data("Fantrax rosters", lambda: get_fantrax_roster(current_year, period)) if need_ft else pd.DataFrame()
ft_players = load_optional_data("Fantrax players", get_fantrax_players) if need_ft or need_history_awards else pd.DataFrame()
standings = load_optional_data("Standings", get_standings) if need_standings else pd.DataFrame()
dh = load_optional_data("Draft history", get_draft_history) if need_dh else pd.DataFrame()
all_time_team_stats = load_optional_data("All-time team stats", get_all_time_team_stats) if need_all_time_team_stats else pd.DataFrame()
all_time_rosters = load_optional_data("All-time rosters", get_all_time_rosters) if need_all_time_rosters else pd.DataFrame()
all_time_schedule = load_optional_data("All-time schedule", get_all_time_schedule) if need_all_time_schedule else pd.DataFrame()
current_matchup = load_optional_data("Current matchup period", current_matchup_period) if need_current_matchup else period
period_calendar = load_optional_data("Period calendar", get_period_calendar) if need_period_calendar else pd.DataFrame()
award_history = load_optional_data("Award history", get_award_history) if need_history_awards else pd.DataFrame()
team_award_history = load_optional_data("Team award history", get_team_award_history) if need_history_awards else pd.DataFrame()

all_time_schedule = ensure_columns(all_time_schedule, ["Year", "Period", "Type", "Round", "TeamA", "TeamB", "TeamAScore", "TeamBScore", "Game_ID"])
standings = ensure_columns(standings, ["Year", "Period", "Team", "Record", "ConfRecord", "DivRecord", "GSRecord", "Playoff Seed", "IST Seed"])
ft_players = ensure_columns(ft_players, ["name", "fantraxId"])
all_time_rosters = ensure_columns(all_time_rosters, ["Year", "period", "id", "team_name"])
award_history = ensure_columns(award_history, ["Award", "Year", "Winner"])
team_award_history = ensure_columns(team_award_history, ["Award", "Year", "Winner"])
period_calendar = ensure_columns(period_calendar, ["Day", "Year", "Date", "Period", "Season"])

Teams = sorted(team_info.keys())

if "_sbc_selected_team" not in st.session_state:
    st.session_state["_sbc_selected_team"] = "Vegas"
SelectedTeam = st.session_state.get("_sbc_selected_team", "Vegas")
if SelectedTeam not in Teams:
    SelectedTeam = "Vegas"
    st.session_state["_sbc_selected_team"] = SelectedTeam

previous_selected_team = st.session_state.get("_sbc_previous_selected_team")
selected_team_changed = previous_selected_team is not None and previous_selected_team != SelectedTeam
st.session_state["_sbc_previous_selected_team"] = SelectedTeam

bg_color = team_info[SelectedTeam]["bg"]
text_color = team_info[SelectedTeam]["text"]
text_color2 = team_info[SelectedTeam]["bg2"]
team_logo = team_info[SelectedTeam]["logo"]
nickname = team_info[SelectedTeam]["nickname"]
team_font = TEAM_FONTS.get(SelectedTeam, "Poppins")

team_logo_html = escape(str(team_logo), quote=True)
team_name_html = escape(str(SelectedTeam), quote=True)
nickname_html = escape(str(nickname), quote=True)
team_font_css = escape(str(team_font), quote=True)
league_logo_html = escape(str(LEAGUE_LOGO), quote=True)
league_font_css = escape(str(LEAGUE_FONT), quote=True)


@st.cache_data(show_spinner=False)
def load_branding_table(path_text, modified_time):
    del modified_time
    path = Path(path_text)
    return pd.read_csv(path).fillna("") if path.exists() else pd.DataFrame()


def branding_contrast_color(hex_color):
    try:
        value = str(hex_color).lstrip("#")
        red, green, blue = (int(value[index:index + 2], 16) for index in (0, 2, 4))
        luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255
        return "#111111" if luminance > 0.58 else "#FFFFFF"
    except (TypeError, ValueError):
        return "#FFFFFF"


@st.cache_resource(show_spinner=False)
def resolve_brand_font_path(font_family):
    """Return the exact local Google-font file used by the design tools."""
    family = str(font_family or "").strip()
    if not family or family.startswith("DejaVu"):
        return ""
    safe_name = re.sub(r"[^a-z0-9]+", "_", family.lower()).strip("_")
    cache_roots = [
        APP_DIR / ".streamlit_cache" / "jersey_fonts",
        APP_DIR / ".streamlit_cache" / "court_fonts",
    ]
    for cache_root in cache_roots:
        for candidate in cache_root.glob(f"{safe_name}.*") if cache_root.exists() else []:
            try:
                FT2Font(str(candidate))
                return str(candidate)
            except (RuntimeError, OSError):
                continue

    cache_root = cache_roots[0]
    cache_root.mkdir(parents=True, exist_ok=True)
    css_url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}"
    css = requests.get(css_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    css.raise_for_status()
    font_urls = re.findall(r"url\((https://[^)]+)\)", css.text)
    if not font_urls:
        return ""
    response = requests.get(font_urls[-1], headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    response.raise_for_status()
    suffix = ".woff2" if "woff2" in response.headers.get("content-type", "") else ".ttf"
    destination = cache_root / f"{safe_name}{suffix}"
    destination.write_bytes(response.content)
    FT2Font(str(destination))
    return str(destination)


def apply_resolved_brand_font(config, saved_path=""):
    path = Path(str(saved_path)) if str(saved_path).strip() else None
    if path is not None and path.exists():
        config.font_path = str(path)
        return config
    try:
        config.font_path = resolve_brand_font_path(config.font_family)
    except Exception:
        config.font_path = ""
    return config


def render_team_branding(team):
    info = team_info[team]
    city, region = TEAM_LOCATIONS.get(team, (team, "United States"))
    full_name = f"{team} {info['nickname']}"
    primary, secondary = str(info["bg"]), str(info["bg2"])
    font_name = TEAM_FONTS.get(team, "Poppins")

    render_html("""
        <style>
        .sbc-brand-hero { position:relative; overflow:hidden; display:flex; align-items:center; gap:28px; min-height:210px; padding:30px 34px; margin:10px 0 28px; border-radius:26px; color:white; background:linear-gradient(125deg,var(--brand-primary),var(--brand-secondary)); box-shadow:0 18px 45px rgba(15,23,42,.18); }
        .sbc-brand-hero::after { content:""; position:absolute; width:340px; height:340px; right:-120px; top:-170px; border:42px solid rgba(255,255,255,.13); border-radius:50%; }
        .sbc-brand-hero img { position:relative; z-index:1; width:150px; height:150px; object-fit:contain; filter:drop-shadow(0 14px 18px rgba(0,0,0,.28)); }
        .sbc-brand-hero div { position:relative; z-index:1; }
        .sbc-brand-hero h1 { margin:5px 0 7px; color:white; font-family:var(--brand-font),sans-serif; font-size:clamp(2.4rem,5.2vw,4.8rem); line-height:1; }
        .sbc-brand-hero p { margin:0; color:rgba(255,255,255,.9); font-weight:700; }
        .sbc-brand-kicker { font-size:.74rem; font-weight:900; letter-spacing:.18em; text-transform:uppercase; }
        .sbc-brand-section-title { margin:8px 0 12px; color:#64748b; font-size:.76rem; font-weight:900; letter-spacing:.15em; text-transform:uppercase; }
        .sbc-brand-art-title { margin-top:30px; padding-top:22px; border-top:1px solid #dbe3ee; }
        .sbc-brand-color-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
        .sbc-brand-swatch { min-height:150px; display:flex; flex-direction:column; justify-content:space-between; padding:22px; border-radius:18px; box-shadow:inset 0 0 0 1px rgba(0,0,0,.08); }
        .sbc-brand-swatch span { font-size:.7rem; font-weight:900; letter-spacing:.15em; text-transform:uppercase; opacity:.78; }
        .sbc-brand-swatch strong { font-size:1.25rem; letter-spacing:.05em; }
        .sbc-brand-type-card { padding:18px; overflow:hidden; border:1px solid #dbe3ee; border-radius:20px; background:#fff; color:#111827; }
        .sbc-brand-type-card-old { display:none; }
        .sbc-brand-glyph-group + .sbc-brand-glyph-group { margin-top:18px; }
        .sbc-brand-glyph-label { display:block; margin:0 0 8px 2px; color:#94a3b8; font-family:Poppins,sans-serif; font-size:.66rem; font-weight:900; letter-spacing:.14em; text-transform:uppercase; }
        .sbc-brand-glyph-grid { display:grid; grid-template-columns:repeat(var(--glyph-count),minmax(0,1fr)); gap:4px; font-family:var(--brand-font),sans-serif; }
        .sbc-brand-glyph { display:flex; align-items:center; justify-content:center; min-width:0; min-height:54px; padding:3px 1px; overflow:hidden; border:1px solid #e2e8f0; border-radius:7px; background:#f8fafc; font-size:clamp(.82rem,1.55vw,1.55rem); line-height:1; }
        .sbc-brand-edition-label { margin-top:-9px; text-align:center; color:#334155; font-size:.78rem; font-weight:900; letter-spacing:.14em; text-transform:uppercase; }
        .sbc-brand-edition-heading { display:flex; align-items:baseline; justify-content:space-between; margin:22px 0 6px; padding:12px 16px; border-left:5px solid var(--brand-primary,#334155); border-radius:0 12px 12px 0; background:#fff; color:#0f172a; font-size:1rem; font-weight:900; letter-spacing:.08em; text-transform:uppercase; }
        .sbc-brand-edition-heading span { color:#94a3b8; font-size:.68rem; letter-spacing:.14em; }
        div[data-testid="stSegmentedControl"] button[aria-pressed="true"] p { color:#fff !important; }
        @media(max-width:700px) { .sbc-brand-hero { padding:24px; gap:18px; } .sbc-brand-hero img { width:94px; height:94px; } .sbc-brand-glyph-grid { gap:2px; } .sbc-brand-glyph { min-height:38px; border-radius:4px; font-size:clamp(.55rem,2.5vw,.9rem); } }
        </style>
    """)

    render_html(f"""
        <section class="sbc-brand-hero" style="--brand-primary:{escape(primary)};--brand-secondary:{escape(secondary)};--brand-font:'{escape(font_name, quote=True)}'">
            <img src="{escape(str(info['logo']), quote=True)}" alt="{escape(full_name, quote=True)} logo">
            <div>
                <div class="sbc-brand-kicker">SBC Franchise Identity</div>
                <h1>{escape(full_name)}</h1>
                <p>{escape(city)}, {escape(region)} &nbsp;·&nbsp; {escape(str(info['conf']))} Conference &nbsp;·&nbsp; {escape(str(info['div']))} Division</p>
            </div>
        </section>
    """)

    identity_col = st.container()
    with identity_col:
        render_html('<div class="sbc-brand-section-title">Identity System</div>')
        render_html(f"""
            <div class="sbc-brand-color-grid">
                <div class="sbc-brand-swatch" style="background:{escape(primary)};color:{branding_contrast_color(primary)}">
                    <span>Primary</span><strong>{escape(primary.upper())}</strong>
                </div>
                <div class="sbc-brand-swatch" style="background:{escape(secondary)};color:{branding_contrast_color(secondary)}">
                    <span>Secondary</span><strong>{escape(secondary.upper())}</strong>
                </div>
            </div>
            <div class="sbc-brand-type-card-old" style="font-family:'{escape(font_name, quote=True)}', sans-serif">
                <span class="sbc-brand-font-label">TEAM TYPEFACE · {escape(font_name)}</span>
                <div>ABCDEFGHIJKLMNOPQRSTUVWXYZ</div>
                <div>abcdefghijklmnopqrstuvwxyz</div>
                <div>0123456789</div>
            </div>
        """)
    specimen_groups = [
        ("Uppercase", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("Lowercase", "abcdefghijklmnopqrstuvwxyz"),
        ("Numerals", "0123456789"),
    ]
    specimen_html = "".join(
        f'<div class="sbc-brand-glyph-group"><span class="sbc-brand-glyph-label">{label}</span>'
        f'<div class="sbc-brand-glyph-grid" style="--glyph-count:{len(characters)}">'
        + "".join(f'<span class="sbc-brand-glyph">{escape(character)}</span>' for character in characters)
        + '</div></div>'
        for label, characters in specimen_groups
    )
    render_html(f'<div class="sbc-brand-section-title sbc-brand-art-title">Team Typeface · {escape(font_name)}</div>')
    render_html(f'<div class="sbc-brand-type-card" style="--brand-font:\'{escape(font_name, quote=True)}\'">{specimen_html}</div>')

    court_path = APP_DIR / "court_team_configs.csv"
    court_table = load_branding_table(str(court_path), court_path.stat().st_mtime if court_path.exists() else 0)
    court_rows = court_table[court_table["team"].astype(str) == team] if "team" in court_table else pd.DataFrame()
    render_html('<div class="sbc-brand-section-title sbc-brand-art-title">Home Court</div>')
    if court_rows.empty:
        st.info("No saved court configuration is available for this team yet.")
    else:
        court_values = court_rows.iloc[0].to_dict()
        court_config = apply_resolved_brand_font(CourtConfig.from_mapping(court_values), court_values.get("font_path", ""))
        center_logo_team = str(court_rows.iloc[0].get("center_logo_team") or team)
        center_logo = team_info.get(center_logo_team, info).get("logo")
        court_figure, _ = draw_branded_court(
            court_config, logo=center_logo, league_logo=LEAGUE_LOGO,
            orientation="horizontal", dpi=125,
        )
        st.pyplot(court_figure, use_container_width=True)
        plt.close(court_figure)

    jersey_path = APP_DIR / "jersey_team_configs.csv"
    jersey_table = load_branding_table(str(jersey_path), jersey_path.stat().st_mtime if jersey_path.exists() else 0)
    jersey_rows = jersey_table[jersey_table["team"].astype(str) == team] if "team" in jersey_table else pd.DataFrame()
    render_html('<div class="sbc-brand-section-title sbc-brand-art-title">Uniform Collection</div>')
    edition_columns = st.columns(3, gap="medium")
    for column, edition in zip(edition_columns, ["Association", "Icon", "Statement"]):
        with column:
            row = jersey_rows[jersey_rows["edition"].astype(str) == edition]
            render_html(f'<div class="sbc-brand-edition-heading">{escape(edition)} <span>Front &amp; Back</span></div>')
            if row.empty:
                st.info(f"No {edition} configuration saved.")
                continue
            values = row.iloc[0].to_dict()
            uniform_config = apply_resolved_brand_font(JerseyConfig.from_mapping(values), values.get("font_path", ""))
            logo_team = str(values.get("logo_team") or team)
            uniform_logo = team_info.get(logo_team, info).get("logo")
            uniform_figure, _ = draw_uniform(uniform_config, logo=uniform_logo, view="front_and_back", dpi=130, background="#F5F7FB")
            st.pyplot(uniform_figure, use_container_width=True)
            plt.close(uniform_figure)

#ABC 
def format_money(value):
    try:
        if value is None or value == "":
            return "—"
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return value

def clean_cap_display(col, value):
    if is_blank_value(value):
        return "—"
    text = str(value)
    if col == "Exception":
        text = re.sub(r"(?i)(Traded-Player(?: Exception)?)(?:\s*#?\d+)$", r"\1", text).strip()
    return text

def parse_money_input(value):
    if is_blank_value(value):
        return None
    text = str(value).replace("$", "").replace(",", "").strip()
    if text == "":
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def render_cap_table(data, columns=None, image_columns=None, money_columns=None, contract_colors=True, row_team=None):
    image_columns = set(image_columns or [])
    money_columns = set(money_columns or [])
    if data is None or data.shape[0] == 0:
        render_html('<div class="sbc-empty-state">No records to display.</div>')
        return

    table_df = data.copy()
    if "Exception" in table_df.columns:
        table_df["Exception"] = table_df["Exception"].apply(lambda value: clean_cap_display("Exception", value))
    if columns is None:
        visible_columns = [c for c in table_df.columns if not str(c).startswith("Type")]
    else:
        visible_columns = [c for c in columns if c in table_df.columns]

    header_cells = "".join(f"<th>{escape(str(col))}</th>" for col in visible_columns)
    body_rows = []
    for _, row in table_df.iterrows():
        cells = []
        for col in visible_columns:
            raw_value = row.get(col, "")
            cell_classes = []
            style = ""
            value = "" if raw_value is None else raw_value

            if contract_colors and str(col).isdigit():
                contract_type = row.get(f"Type{col}", None)
                bg = type_colors.get(contract_type)
                if bg:
                    style = f' style="background:{escape(str(bg), quote=True)};"'
                    cell_classes.append("sbc-money-cell")

            if col in money_columns or str(col).isdigit():
                value_html = escape(str(format_money(value)))
                cell_classes.append("sbc-money-cell")
            elif col in image_columns and (not is_blank_value(value) or col != "Team_logo"):
                image_value = DRAFT_SILHOUETTE if col != "Team_logo" and is_blank_value(value) else value
                url = escape(str(image_value), quote=True)
                value_html = f'<img class="sbc-table-img" src="{url}" alt="" referrerpolicy="no-referrer">'
                cell_classes.append("sbc-image-cell")
            else:
                display = "—" if str(value) == "nan" or value == "" else value
                value_html = escape(str(display))

            class_attr = f' class="{" ".join(cell_classes)}"' if cell_classes else ""
            cells.append(f"<td{class_attr}{style}>{value_html}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    render_html(f"""
        <div class="sbc-table-wrap">
            <table class="sbc-cap-table">
                <thead><tr>{header_cells}</tr></thead>
                <tbody>{''.join(body_rows)}</tbody>
            </table>
        </div>
        """)

def is_blank_value(value):
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    if value == "":
        return True
    try:
        return float(value) != float(value)
    except (TypeError, ValueError):
        return str(value).strip().lower() in ["nan", "none", "nat"]

def format_money(value):
    try:
        if is_blank_value(value):
            return "—"
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return value

def render_cap_table(data, columns=None, image_columns=None, money_columns=None, contract_colors=True, row_team=None):
    image_columns = set(image_columns or [])
    money_columns = set(money_columns or [])
    if data is None or data.shape[0] == 0:
        render_html('<div class="sbc-empty-state">No records to display.</div>')
        return

    table_df = data.copy()
    if "Exception" in table_df.columns:
        table_df["Exception"] = table_df["Exception"].apply(lambda value: clean_cap_display("Exception", value))
    if columns is None:
        visible_columns = [c for c in table_df.columns if not str(c).startswith("Type")]
    else:
        visible_columns = [c for c in columns if c in table_df.columns]

    header_cells = []
    for col in visible_columns:
        th_classes = []
        if str(col).isdigit():
            th_classes.append("sbc-year-col")
        if col == "Player":
            th_classes.append("sbc-player-col")
        if col in image_columns:
            th_classes.append("sbc-image-col")
        class_attr = f' class="{" ".join(th_classes)}"' if th_classes else ""
        label = "" if col == "Team_logo" else str(col)
        header_cells.append(f"<th{class_attr}>{escape(label)}</th>")

    body_rows = []
    logo_to_team = {info.get("logo", ""): team for team, info in team_info.items()}
    for _, row in table_df.iterrows():
        cells = []
        team_logo_value = row.get("Team_logo", "")
        row_style = ""
        if row_team:
            row_color = team_info.get(str(row_team), {}).get("bg", "")
            if row_color:
                row_style = f' style="--row-team-color:{escape(str(row_color), quote=True)};"'
        elif str(team_logo_value).strip():
            logo_team = logo_to_team.get(str(team_logo_value), "")
            row_color = team_info.get(logo_team, {}).get("bg", "")
            if row_color:
                row_style = f' style="--row-team-color:{escape(str(row_color), quote=True)};"'
        for col in visible_columns:
            raw_value = row.get(col, "")
            cell_classes = []
            style = ""
            value = "" if is_blank_value(raw_value) else raw_value

            if contract_colors and str(col).isdigit():
                contract_type = row.get(f"Type{col}", None)
                bg = type_colors.get(contract_type)
                if bg:
                    style = f' style="background:{escape(str(bg), quote=True)};"'

            if col in money_columns or str(col).isdigit():
                value_html = escape(str(format_money(value)))
                cell_classes.append("sbc-money-cell")
                if str(col).isdigit():
                    cell_classes.append("sbc-year-col")
            elif col in image_columns and (not is_blank_value(value) or col != "Team_logo"):
                image_value = DRAFT_SILHOUETTE if col != "Team_logo" and is_blank_value(value) else value
                url = escape(str(image_value), quote=True)
                image_class = "sbc-team-logo-img" if col == "Team_logo" else "sbc-table-img"
                value_html = f'<img class="{image_class}" src="{url}" alt="" referrerpolicy="no-referrer">'
                cell_classes.extend(["sbc-image-cell", "sbc-image-col"])
            else:
                display = "—" if value == "" else value
                value_html = escape(str(display))
                if col == "Player":
                    cell_classes.append("sbc-player-cell")

            class_attr = f' class="{" ".join(cell_classes)}"' if cell_classes else ""
            cells.append(f"<td{class_attr}{style}>{value_html}</td>")
        body_rows.append(f"<tr{row_style}>{''.join(cells)}</tr>")

    render_html(f"""
        <div class="sbc-table-wrap">
            <table class="sbc-cap-table">
                <thead><tr>{''.join(header_cells)}</tr></thead>
                <tbody>{''.join(body_rows)}</tbody>
            </table>
        </div>
        """)

def safe_table_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return pd.DataFrame()


def parse_free_agency_money(value):
    if is_blank_value(value):
        return None
    text = str(value).replace("$", "").replace(",", "").strip()
    if text == "":
        return None
    try:
        amount = float(text)
    except ValueError:
        return None
    if "." in text and amount < 1000:
        amount *= 1000000
    return int(round(amount))


def parse_free_agency_years(value):
    if is_blank_value(value):
        return 1
    text = str(value).strip().lower()
    if text == "max":
        return 5
    try:
        return max(1, min(5, int(float(text))))
    except ValueError:
        return 1


def free_agency_team_from_code(value):
    code = "" if is_blank_value(value) else str(value)
    return FREE_AGENCY_TEAM_CODES.get(code, FREE_AGENCY_TEAM_CODES.get(code.strip(), code.strip()))


def clean_free_agency_player(value):
    text = "" if is_blank_value(value) else str(value)
    return re.sub(r"\s+", " ", text.replace("_", " ")).strip()


def free_agency_player_key(value):
    text = clean_free_agency_player(value).lower()
    text = re.sub(r"[.'’]", "", text)
    parts = [part for part in text.split() if part not in {"jr", "sr", "ii", "iii", "iv", "v"}]
    return " ".join(parts)


def load_free_agency_bids(path=FREE_AGENT_BIDS_PATH):
    try:
        raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception:
        return pd.DataFrame()
    if raw.shape[0] < 3:
        return pd.DataFrame()

    # Qualtrics exports with technical QID headers, then display labels, then import ids.
    labels = [str(col).strip() for col in raw.iloc[0].tolist()]
    data = raw.iloc[2:].copy().reset_index(drop=True)
    data.columns = labels

    recorded_col = "Recorded Date"
    team_col = "Team Code"
    response_col = "Response ID"
    comments_cols = [col for col in data.columns if "notes" in str(col).lower() or str(col).strip() == "QID8"]
    comments_col = comments_cols[0] if comments_cols else None

    bid_columns = []
    for col in data.columns[19:]:
        match = re.search(r" - (Salary|Years) - (.*?) - ", str(col))
        if match:
            bid_columns.append((col, match.group(2).strip(), match.group(1)))
    salary_cols = {player: col for col, player, kind in bid_columns if kind == "Salary"}
    year_cols = {player: col for col, player, kind in bid_columns if kind == "Years"}
    if not salary_cols:
        return pd.DataFrame()

    records = []
    for _, row in data.iterrows():
        recorded = row.get(recorded_col, "")
        team_code = row.get(team_col, "")
        team = free_agency_team_from_code(team_code)
        comments = row.get(comments_col, "") if comments_col else ""
        response_id = row.get(response_col, "")
        for player, salary_col in salary_cols.items():
            salary_raw = row.get(salary_col, "")
            years_raw = row.get(year_cols.get(player, ""), "")
            if is_blank_value(salary_raw) and is_blank_value(years_raw):
                continue
            records.append({
                "Recorded Date": recorded,
                "Timestamp": pd.to_datetime(recorded, errors="coerce"),
                "Team Code": team_code,
                "Team": team,
                "Player": clean_free_agency_player(player),
                "Salary": parse_free_agency_money(salary_raw) or 1,
                "Years": parse_free_agency_years(years_raw),
                "Comments": comments,
                "Response ID": response_id,
            })

    bids = pd.DataFrame(records)
    if bids.empty:
        return bids
    return bids.sort_values(["Timestamp", "Team", "Player"], na_position="last").reset_index(drop=True)


def load_free_agency_bid_players(path=FREE_AGENT_BIDS_PATH):
    try:
        raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception:
        return []
    if raw.empty:
        return []

    labels = [str(col).strip() for col in raw.iloc[0].tolist()]
    players = []
    seen = set()
    for col in labels[19:]:
        match = re.search(r" - Salary - (.*?) - ", str(col))
        if not match:
            continue
        player = clean_free_agency_player(match.group(1))
        key = free_agency_player_key(player)
        if player and key not in seen:
            players.append(player)
            seen.add(key)
    return players


def active_free_agency_bids(bids, signed_players=None, available_players=None):
    if bids is None or bids.empty:
        return pd.DataFrame()
    signed_set = {free_agency_player_key(player) for player in (signed_players or []) if str(player).strip()}
    active = bids.copy()
    active["_player_key"] = active["Player"].apply(free_agency_player_key)
    if signed_set:
        active = active[~active["_player_key"].isin(signed_set)]

    available_set = {free_agency_player_key(player) for player in (available_players or []) if str(player).strip()}
    overlap = set(active["_player_key"]).intersection(available_set)
    if available_set and overlap:
        active = active[active["_player_key"].isin(available_set)]

    active = active.sort_values(["Team", "_player_key", "Timestamp", "Player"], ascending=[True, True, False, True], na_position="last")
    active = active.groupby(["Team", "_player_key"], as_index=False, group_keys=False).head(1)
    active = active.sort_values(["Team", "Timestamp", "Player"], ascending=[True, False, True], na_position="last")
    active = active.groupby("Team", as_index=False, group_keys=False).head(20)
    return active.drop(columns=["_player_key"], errors="ignore").reset_index(drop=True)


def free_agency_bid_audit(bids, signed_players=None, available_players=None, released_players=None, league_view=None):
    if bids is None or bids.empty:
        return pd.DataFrame(), pd.DataFrame()
    signed_set = {free_agency_player_key(player) for player in (signed_players or []) if str(player).strip()}
    available_set = {free_agency_player_key(player) for player in (available_players or []) if str(player).strip()}
    released_set = {free_agency_player_key(player) for player in (released_players or []) if str(player).strip()}
    league_lookup = free_agency_league_lookup(league_view)
    work = bids.copy()
    work["_player_key"] = work["Player"].apply(free_agency_player_key)
    work["_sign_order_sort"] = work["_player_key"].map(lambda key: parse_free_agency_sign_order(league_lookup.get(key, {}).get("SignOrder", "")))
    work["_bid_status"] = "Active"
    if signed_set:
        work.loc[work["_player_key"].isin(signed_set), "_bid_status"] = "Signed player"
    overlap = set(work["_player_key"]).intersection(available_set)
    if available_set and overlap:
        work.loc[~work["_player_key"].isin(available_set), "_bid_status"] = "Not in free-agent pool"
    if released_set:
        unreleased_mask = ~work["_player_key"].isin(released_set)
        if available_set:
            unreleased_mask = unreleased_mask & work["_player_key"].isin(available_set)
        work.loc[(work["_bid_status"] == "Active") & unreleased_mask, "_bid_status"] = "Not Yet Released"

    eligible = work[work["_bid_status"] == "Active"].copy()
    eligible = eligible.sort_values(["Team", "_player_key", "Timestamp", "Player"], ascending=[True, True, False, True], na_position="last")
    eligible["_team_player_rank"] = eligible.groupby(["Team", "_player_key"]).cumcount() + 1
    eligible.loc[eligible["_team_player_rank"] > 1, "_bid_status"] = "Replaced by newer player bid"

    latest = eligible[eligible["_bid_status"] == "Active"].copy()
    latest["_team_active_rank"] = pd.NA
    ranked_teams = []
    for _, team_bids in latest.groupby("Team", dropna=False):
        team_bids = team_bids.sort_values(["Timestamp", "Player"], ascending=[False, True], na_position="last").copy()
        if team_bids.shape[0] > 20:
            cutoff_timestamp = team_bids.iloc[19]["Timestamp"]
            if pd.isna(cutoff_timestamp):
                latest_window = team_bids.copy()
            else:
                latest_window = team_bids[team_bids["Timestamp"] >= cutoff_timestamp].copy()
            older_window = team_bids.drop(index=latest_window.index).copy()
            if latest_window.shape[0] > 20:
                latest_window = latest_window.sort_values(["_sign_order_sort", "Timestamp", "Player"], ascending=[True, False, True], na_position="last").copy()
                keep_window = latest_window.head(20).copy()
                trim_window = latest_window.iloc[20:].copy()
                trim_window["_bid_status"] = "Outside latest 20"
                older_window["_bid_status"] = "Outside latest 20"
                team_bids = pd.concat([keep_window, trim_window, older_window], ignore_index=True)
            else:
                older_window["_bid_status"] = "Outside latest 20"
                team_bids = pd.concat([latest_window, older_window], ignore_index=True)
        team_bids = team_bids.sort_values(["Timestamp", "Player"], ascending=[False, True], na_position="last").copy()
        team_bids["_team_active_rank"] = range(1, team_bids.shape[0] + 1)
        ranked_teams.append(team_bids)
    latest = pd.concat(ranked_teams, ignore_index=True) if ranked_teams else latest

    audit = pd.concat([
        work[work["_bid_status"] != "Active"],
        eligible[eligible["_bid_status"] != "Active"],
        latest,
    ], ignore_index=True)
    active = latest[latest["_bid_status"] == "Active"].drop(columns=["_player_key", "_team_player_rank", "_team_active_rank", "_bid_status"], errors="ignore")
    excluded = audit[audit["_bid_status"] != "Active"].drop(columns=["_player_key"], errors="ignore")
    active = active.sort_values(["_sign_order_sort", "Player", "Salary", "Years", "Timestamp"], ascending=[True, True, False, False, True], na_position="last").drop(columns=["_sign_order_sort"], errors="ignore").reset_index(drop=True)
    excluded = excluded.sort_values(["Team", "_sign_order_sort", "Player", "Timestamp"], ascending=[True, True, True, False], na_position="last").drop(columns=["_sign_order_sort"], errors="ignore").reset_index(drop=True)
    return active, excluded


def free_agency_bid_status_label(value):
    labels = {
        "Signed player": "Signed",
        "Not in free-agent pool": "Not FA",
        "Not Yet Released": "Locked",
        "Replaced by newer player bid": "Old bid",
        "Outside latest 20": "Cut",
        "Inactive": "Inactive",
    }
    return labels.get(str(value), str(value))


def free_agency_submission_summary(bids, active_bids):
    if bids is None or bids.empty:
        return pd.DataFrame(columns=["Team", "Last Bid Timestamp", "Active Bids"])
    latest = bids.groupby("Team", as_index=False)["Timestamp"].max().rename(columns={"Timestamp": "Last Bid Timestamp"})
    counts = active_bids.groupby("Team", as_index=False).size().rename(columns={"size": "Active Bids"}) if active_bids is not None and not active_bids.empty else pd.DataFrame(columns=["Team", "Active Bids"])
    summary = latest.merge(counts, on="Team", how="left")
    summary["Active Bids"] = summary["Active Bids"].fillna(0).astype(int)
    return summary.sort_values("Last Bid Timestamp", ascending=False).head(30).reset_index(drop=True)


def free_agency_league_lookup(league_view):
    if league_view is None or league_view.empty or "Player" not in league_view.columns:
        return {}
    return {
        free_agency_player_key(row.get("Player", "")): row.to_dict()
        for _, row in league_view.iterrows()
        if not is_blank_value(row.get("Player", ""))
    }


def free_agency_released_players(league_view, release_month=7, release_days=(1, 5)):
    if league_view is None or league_view.empty or "Player" not in league_view.columns or "DayR" not in league_view.columns:
        return []
    release_days = {int(day) for day in ([release_days] if isinstance(release_days, int) else release_days)}
    released = []
    for _, row in league_view.iterrows():
        release_date = parse_free_agency_day(row.get("DayR", ""))
        if not pd.isna(release_date) and release_date.month == release_month and release_date.day in release_days:
            released.append(row.get("Player", ""))
    return released


def is_free_agency_signed_team_value(value):
    if is_blank_value(value):
        return False
    text = str(value).strip()
    if text.lower() in {"unsigned", "open", "none", "nan", "nat", "false"}:
        return False
    if text in {"-", "—", "–", "â€”"}:
        return False
    return True


def free_agency_signed_players(league_view):
    if league_view is None or league_view.empty or not {"Player", "Team"}.issubset(league_view.columns):
        return []
    signed = []
    for _, row in league_view.iterrows():
        player = row.get("Player", "")
        if not is_blank_value(player) and is_free_agency_signed_team_value(row.get("Team", "")):
            signed.append(player)
    return signed


def parse_free_agency_day(value):
    if is_blank_value(value):
        return pd.NaT
    text = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", str(value), flags=re.IGNORECASE)
    if not re.search(r"\b\d{4}\b", text):
        text = f"{text} {current_year}"
    return pd.to_datetime(text, errors="coerce")


def free_agency_due_text(day_value):
    due = parse_free_agency_day(day_value)
    if pd.isna(due):
        return "", False
    today_ts = pd.Timestamp(date.today())
    return f"{due.strftime('%b')} {due.day}" if hasattr(due, "strftime") else str(day_value), due.normalize() <= today_ts


def parse_free_agency_sign_order(value):
    if is_blank_value(value):
        return math.inf
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return math.inf


def render_free_agency_sign_order(value):
    order = parse_free_agency_sign_order(value)
    if math.isinf(order):
        return '<span class="sbc-fa-muted">Pending</span>'
    return f'<span class="sbc-fa-sign-order">{escape(str(order))}</span>'


def free_agency_bird_rights_lookup():
    if not isinstance(df, pd.DataFrame) or df.empty or "Player" not in df.columns or "BirdRights" not in df.columns:
        return {}
    rows = df[["Player", "Team", "BirdRights"]].copy()
    rows["_player_key"] = rows["Player"].apply(free_agency_player_key)
    lookup = {}
    for _, row in rows.iterrows():
        key = row["_player_key"]
        team = str(row.get("Team", "")).strip()
        rights = row.get("BirdRights", "")
        if key and not is_blank_value(rights):
            lookup[(key, team)] = rights
            lookup.setdefault((key, ""), rights)
    return lookup


def format_free_agency_timestamp(value):
    if pd.isna(value):
        return ""
    try:
        ts = pd.to_datetime(value)
        return f"{ts.strftime('%b')} {ts.day}, {ts.strftime('%I:%M %p').lstrip('0')}"
    except Exception:
        return str(value)


def render_commish_bid_rows(player_bids):
    if player_bids is None or player_bids.empty:
        return '<div class="sbc-fa-empty-mini">No active bids.</div>'
    rows = []
    ordered = player_bids.sort_values(["Salary", "Years", "Timestamp", "Team"], ascending=[False, False, True, True], na_position="last")
    for rank, (_, bid) in enumerate(ordered.iterrows(), start=1):
        rows.append(f"""
            <div class="sbc-fa-bid-row {'sbc-fa-bid-row-leader' if rank == 1 else ''}">
                <span class="sbc-fa-bid-rank">{rank}</span>
                <span class="sbc-fa-bid-team">{render_free_agency_team_badge(bid.get("Team", ""), empty_text="Unknown")}</span>
                <span class="sbc-fa-bid-money">{escape(str(format_money(bid.get("Salary", 0))))}</span>
                <span class="sbc-fa-bid-years">{escape(str(bid.get("Years", 1)))} yr</span>
                <span class="sbc-fa-bid-time">{escape(format_free_agency_timestamp(bid.get("Timestamp")))}</span>
                <span class="sbc-fa-bid-comment">{escape(str(bid.get("Comments", "")))}</span>
            </div>
        """)
    return "".join(rows)


def render_free_agency_response_audit(all_bids):
    if all_bids is None or all_bids.empty or not {"Response ID", "Team Code", "Team"}.issubset(all_bids.columns):
        return """
            <div class="sbc-fa-response-audit sbc-fa-response-audit-clear">
                <strong>Response Audit</strong>
                <span>No bid responses are available to check.</span>
            </div>
        """

    responses = all_bids.copy()
    responses["_code_trimmed"] = responses["Team Code"].astype(str).str.strip()
    responses["_known_team"] = responses["Team"].isin(team_info.keys())
    responses["_code_has_spaces"] = responses["Team Code"].astype(str) != responses["_code_trimmed"]
    responses["_code_blank"] = responses["_code_trimmed"].eq("")
    response_rows = (
        responses.groupby(["Response ID", "Team Code", "Team"], dropna=False)
        .agg(
            Timestamp=("Timestamp", "max"),
            Bids=("Player", "size"),
            KnownTeam=("_known_team", "first"),
            CodeHasSpaces=("_code_has_spaces", "first"),
            CodeBlank=("_code_blank", "first"),
        )
        .reset_index()
    )
    response_rows["Issue"] = ""
    response_rows.loc[~response_rows["KnownTeam"], "Issue"] = "Unknown code"
    response_rows.loc[response_rows["CodeBlank"], "Issue"] = "Blank code"
    response_rows.loc[response_rows["KnownTeam"] & response_rows["CodeHasSpaces"], "Issue"] = "Extra spaces"
    issues = response_rows[response_rows["Issue"] != ""].sort_values(["Timestamp", "Response ID"], ascending=[False, True])

    if issues.empty:
        return f"""
            <div class="sbc-fa-response-audit sbc-fa-response-audit-clear">
                <strong>Response Audit</strong>
                <span>{response_rows.shape[0]} responses checked. No team-code issues found.</span>
            </div>
        """

    rows = []
    for _, row in issues.head(12).iterrows():
        rows.append(f"""
            <div class="sbc-fa-response-row">
                <span class="sbc-fa-response-issue">{escape(str(row.get("Issue", "")))}</span>
                <strong>{escape(str(row.get("Team", "") or "Unknown"))}</strong>
                <span>{escape(str(row.get("Response ID", "")))}</span>
                <span>{escape(format_free_agency_timestamp(row.get("Timestamp")))}</span>
                <code>{escape(str(row.get("Team Code", "")))}</code>
                <em>{int(row.get("Bids", 0))} bids</em>
            </div>
        """)
    more = issues.shape[0] - min(issues.shape[0], 12)
    more_text = f"<span>{more} more issues not shown.</span>" if more > 0 else ""
    return f"""
        <div class="sbc-fa-response-audit">
            <div class="sbc-fa-response-head">
                <strong>Response Audit</strong>
                <span>{issues.shape[0]} response-code issues found</span>
                {more_text}
            </div>
            <div class="sbc-fa-response-list">{''.join(rows)}</div>
        </div>
    """


def render_free_agency_commish_desk(active_bids, excluded_bids, league_view, all_bids=None, bid_players=None):
    league_lookup = free_agency_league_lookup(league_view)
    signed_set = {free_agency_player_key(player) for player in free_agency_signed_players(league_view)}
    if active_bids is not None and not active_bids.empty:
        active_counts = active_bids.groupby("Player").size().rename("Active Bids").reset_index()
        salary_highs = active_bids.groupby("Player")["Salary"].max().rename("High Bid").reset_index()
        player_queue = active_counts.merge(salary_highs, on="Player", how="left")
    else:
        player_source = list(bid_players or [])
        if isinstance(league_view, pd.DataFrame) and "Player" in league_view.columns:
            player_source.extend(league_view["Player"].tolist())
        player_queue = pd.DataFrame({"Player": [clean_free_agency_player(player) for player in player_source if not is_blank_value(player)]})
        if not player_queue.empty:
            player_queue["_player_key"] = player_queue["Player"].apply(free_agency_player_key)
            player_queue = player_queue.drop_duplicates(subset=["_player_key"]).drop(columns=["_player_key"])
        player_queue["Active Bids"] = 0
        player_queue["High Bid"] = 0
    if player_queue.empty:
        render_html('<div class="sbc-empty-state">No free agency players are available from the league sheet or bid file.</div>')
        return

    player_queue["_player_key"] = player_queue["Player"].apply(free_agency_player_key)
    if signed_set:
        player_queue = player_queue[~player_queue["_player_key"].isin(signed_set)].copy()
    if player_queue.empty:
        render_html('<div class="sbc-empty-state">All listed free agents have signed or no unsigned players are available.</div>')
        return
    player_queue["DayS"] = player_queue["_player_key"].map(lambda key: league_lookup.get(key, {}).get("DayS", ""))
    player_queue["RFA"] = player_queue["_player_key"].map(lambda key: league_lookup.get(key, {}).get("RFA", ""))
    player_queue["OldTeam"] = player_queue["_player_key"].map(lambda key: league_lookup.get(key, {}).get("OldTeam", ""))
    player_queue["SignOrder"] = player_queue["_player_key"].map(lambda key: league_lookup.get(key, {}).get("SignOrder", ""))
    bird_lookup = free_agency_bird_rights_lookup()
    player_queue["BirdRights"] = player_queue.apply(
        lambda row: league_lookup.get(row["_player_key"], {}).get("BirdRights", "")
        or league_lookup.get(row["_player_key"], {}).get("Bird Rights", "")
        or bird_lookup.get((row["_player_key"], free_agency_team_key(row.get("OldTeam", ""))), "")
        or bird_lookup.get((row["_player_key"], ""), ""),
        axis=1,
    )
    player_queue["_days_due"] = player_queue["DayS"].apply(lambda value: free_agency_due_text(value)[1])
    player_queue["_five_plus"] = player_queue["Active Bids"] >= 5
    player_queue["_action"] = player_queue["_days_due"] | player_queue["_five_plus"]
    player_queue["_sign_order_sort"] = player_queue["SignOrder"].apply(parse_free_agency_sign_order)
    player_queue = player_queue.sort_values(
        ["_sign_order_sort", "_action", "_days_due", "_five_plus", "High Bid", "Player"],
        ascending=[True, False, False, False, False, True],
        na_position="last",
    )

    if active_bids is not None and not active_bids.empty:
        team_counts = active_bids.groupby("Team", as_index=False).size().rename(columns={"size": "Active Bids"})
    else:
        team_counts = pd.DataFrame(columns=["Team", "Active Bids"])
    team_order = pd.DataFrame({"Team": list(team_info.keys()), "_team_order": range(len(team_info))})
    team_audit = team_order.merge(team_counts, on="Team", how="left")
    team_audit["Active Bids"] = team_audit["Active Bids"].fillna(0).astype(int)
    if all_bids is not None and not all_bids.empty and {"Team", "Timestamp"}.issubset(all_bids.columns):
        last_bids = all_bids.groupby("Team", as_index=False)["Timestamp"].max().rename(columns={"Timestamp": "Last Bid"})
        team_audit = team_audit.merge(last_bids, on="Team", how="left")
    else:
        team_audit["Last Bid"] = pd.NaT
    team_audit = team_audit.sort_values("_team_order")
    over_20 = team_audit[team_audit["Active Bids"] > 20]

    cards = []
    picture_lookup = free_agency_player_picture_lookup()
    for _, player_row in player_queue.iterrows():
        player = player_row["Player"]
        key = player_row["_player_key"]
        if active_bids is not None and not active_bids.empty:
            player_bids = active_bids[active_bids["Player"].apply(free_agency_player_key) == key].copy()
        else:
            player_bids = pd.DataFrame()
        if player_bids.empty or not {"Salary", "Years", "Timestamp"}.issubset(player_bids.columns):
            leader = pd.DataFrame()
        else:
            leader = player_bids.sort_values(["Salary", "Years", "Timestamp"], ascending=[False, False, True], na_position="last").head(1)
        leader_team = leader.iloc[0]["Team"] if not leader.empty else ""
        leader_salary = leader.iloc[0]["Salary"] if not leader.empty else 0
        leader_years = leader.iloc[0]["Years"] if not leader.empty else 1
        day_s_label, day_s_due = free_agency_due_text(player_row.get("DayS", ""))
        reasons = []
        if day_s_due:
            reasons.append("Signing day reached")
        if player_row["Active Bids"] >= 5:
            reasons.append("5+ active bids")
        if not reasons:
            reasons.append("Monitor")
        cards.append(f"""
            <section class="sbc-fa-commish-card {'sbc-fa-commish-action' if player_row['_action'] else ''}">
                <div class="sbc-fa-commish-top">
                    <div>
                        <div class="sbc-fa-commish-player">{render_free_agency_player_cell(player, picture_lookup)}</div>
                        <div class="sbc-fa-commish-meta">
                            {render_free_agency_status_cell(player_row.get("OldTeam", ""), player_row.get("RFA", ""))}
                            {render_free_agency_sign_order(player_row.get("SignOrder", ""))}
                            <span>{escape(day_s_label or "No signing day")}</span>
                            <span>{escape(str(player_row.get("BirdRights", "") or "No Bird Rights"))}</span>
                        </div>
                    </div>
                    <div class="sbc-fa-commish-callout">
                        <span>{escape(" / ".join(reasons))}</span>
                        <strong>{escape(str(player_row["Active Bids"]))} bids</strong>
                    </div>
                </div>
                <div class="sbc-fa-commish-leader">
                    <span>Leader</span>
                    <strong>{render_free_agency_team_badge(leader_team, empty_text="None")}</strong>
                    <em>{escape(str(format_money(leader_salary)))} / {escape(str(leader_years))} yr</em>
                </div>
                <div class="sbc-fa-bid-list">
                    {render_commish_bid_rows(player_bids)}
                </div>
            </section>
        """)

    team_rows = []
    for _, row in team_audit.iterrows():
        last_bid = format_free_agency_timestamp(row.get("Last Bid")) or "No bid yet"
        team_rows.append(f"""
            <div class="sbc-fa-team-audit {'sbc-fa-team-audit-bad' if row['Active Bids'] > 20 else ''}">
                <div class="sbc-fa-team-audit-main">
                    {render_free_agency_team_badge(row.get("Team", ""), empty_text="Unknown")}
                    <strong>{int(row["Active Bids"])}/20</strong>
                </div>
                <div class="sbc-fa-team-audit-time">
                    <span>Last bid</span>
                    <em>{escape(last_bid)}</em>
                </div>
            </div>
        """)

    response_audit_html = render_free_agency_response_audit(all_bids)
    render_html(f"""
        <style>
            .sbc-fa-response-audit {{
                margin-bottom: 1rem;
                border: 1px solid rgba(23, 32, 42, 0.12);
                border-left: 0.35rem solid #dc2626;
                border-radius: 8px;
                background: #ffffff;
                box-shadow: 0 10px 28px rgba(18, 25, 38, 0.055);
                padding: 0.75rem;
            }}
            .sbc-fa-response-audit-clear {{
                border-left-color: {LEAGUE_SECONDARY};
                background: color-mix(in srgb, {LEAGUE_SECONDARY} 6%, #ffffff);
                display: flex;
                justify-content: space-between;
                gap: 0.75rem;
            }}
            .sbc-fa-response-audit strong {{
                color: var(--sbc-ink);
                font-weight: 950;
            }}
            .sbc-fa-response-audit span,
            .sbc-fa-response-audit em {{
                color: var(--sbc-muted);
                font-size: 0.78rem;
                font-style: normal;
                font-weight: 850;
            }}
            .sbc-fa-response-head {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 0.55rem;
                margin-bottom: 0.55rem;
            }}
            .sbc-fa-response-list {{
                display: grid;
                gap: 0.35rem;
            }}
            .sbc-fa-response-row {{
                display: grid;
                grid-template-columns: 6.5rem minmax(8rem, 0.8fr) minmax(9rem, 1fr) 8rem minmax(10rem, 1.2fr) 4rem;
                align-items: center;
                gap: 0.55rem;
                border-radius: 8px;
                background: #f8fafc;
                padding: 0.45rem 0.55rem;
                min-width: 0;
            }}
            .sbc-fa-response-row code {{
                overflow: hidden;
                color: #111827;
                font-size: 0.74rem;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            .sbc-fa-response-row > span,
            .sbc-fa-response-row strong {{
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            .sbc-fa-response-issue {{
                display: inline-flex;
                justify-content: center;
                border-radius: 999px;
                background: #fee2e2;
                color: #991b1b !important;
                padding: 0.18rem 0.45rem;
                font-size: 0.68rem !important;
                font-weight: 950 !important;
                text-transform: uppercase;
            }}
            .sbc-fa-commish-grid {{
                display: grid;
                grid-template-columns: minmax(0, 1fr);
                gap: 0.85rem;
            }}
            .sbc-fa-commish-card {{
                border: 1px solid rgba(23, 32, 42, 0.12);
                border-left: 0.35rem solid color-mix(in srgb, {LEAGUE_PRIMARY} 38%, #ffffff);
                border-radius: 8px;
                background: #ffffff;
                padding: 0.9rem;
                box-shadow: 0 10px 28px rgba(18, 25, 38, 0.055);
            }}
            .sbc-fa-commish-action {{
                border-left-color: {LEAGUE_SECONDARY};
                background: linear-gradient(135deg, #ffffff 0%, color-mix(in srgb, {LEAGUE_SECONDARY} 6%, #ffffff) 100%);
            }}
            .sbc-fa-commish-top {{
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                align-items: flex-start;
            }}
            .sbc-fa-commish-player .sbc-fa-player-img {{
                width: 2.65rem;
                height: 2.65rem;
            }}
            .sbc-fa-commish-player strong {{
                font-size: 1.05rem;
            }}
            .sbc-fa-commish-meta {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.45rem;
                align-items: center;
                margin-top: 0.45rem;
                color: var(--sbc-muted);
                font-size: 0.78rem;
                font-weight: 850;
            }}
            .sbc-fa-commish-meta .sbc-fa-status-wrap {{
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                min-height: 1.75rem;
                max-width: 100%;
            }}
            .sbc-fa-commish-meta .sbc-fa-status-logo {{
                width: 1.65rem !important;
                height: 1.65rem !important;
                max-width: 1.65rem !important;
                max-height: 1.65rem !important;
                object-fit: contain;
                flex: 0 0 1.65rem;
            }}
            .sbc-fa-commish-meta .sbc-fa-status-logo-empty {{
                width: 1.65rem !important;
                height: 1.65rem !important;
                flex-basis: 1.65rem;
            }}
            .sbc-fa-commish-callout {{
                text-align: right;
                min-width: 8.5rem;
            }}
            .sbc-fa-commish-callout span {{
                display: block;
                color: {LEAGUE_SECONDARY};
                font-size: 0.72rem;
                font-weight: 950;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }}
            .sbc-fa-commish-callout strong {{
                color: var(--sbc-ink);
                font-size: 1.25rem;
            }}
            .sbc-fa-commish-meta .sbc-fa-sign-order {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 2.4rem;
                min-height: 1.65rem;
                padding: 0.15rem 0.5rem;
                border-radius: 999px;
                background: color-mix(in srgb, {LEAGUE_PRIMARY} 10%, #ffffff);
                color: {LEAGUE_PRIMARY};
                font-size: 0.78rem;
                font-weight: 950;
                font-variant-numeric: tabular-nums;
                white-space: nowrap;
            }}
            .sbc-fa-commish-leader {{
                display: flex;
                gap: 0.7rem;
                align-items: center;
                margin: 0.8rem 0;
                padding: 0.55rem 0.65rem;
                border-radius: 8px;
                background: color-mix(in srgb, {LEAGUE_PRIMARY} 6%, #ffffff);
            }}
            .sbc-fa-commish-leader > span {{
                color: var(--sbc-muted);
                font-size: 0.72rem;
                font-weight: 950;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }}
            .sbc-fa-commish-leader em {{
                margin-left: auto;
                color: var(--sbc-ink);
                font-style: normal;
                font-weight: 950;
                font-variant-numeric: tabular-nums;
            }}
            .sbc-fa-bid-list {{
                display: grid;
                gap: 0.3rem;
            }}
            .sbc-fa-bid-row {{
                display: grid;
                grid-template-columns: 2rem minmax(11rem, 1.2fr) 7rem 4rem 8rem minmax(8rem, 1fr);
                gap: 0.55rem;
                align-items: center;
                padding: 0.42rem 0.55rem;
                border-radius: 8px;
                background: rgba(248, 250, 252, 0.9);
                font-size: 0.82rem;
            }}
            .sbc-fa-bid-row .sbc-draft-team-mark,
            .sbc-fa-commish-leader .sbc-draft-team-mark,
            .sbc-fa-team-audit .sbc-draft-team-mark {{
                display: inline-grid;
                grid-template-columns: 1.75rem minmax(0, 1fr);
                align-items: center;
                gap: 0.42rem;
                min-width: 0;
                max-width: 100%;
            }}
            .sbc-fa-bid-row .sbc-draft-team-mark img,
            .sbc-fa-commish-leader .sbc-draft-team-mark img,
            .sbc-fa-team-audit .sbc-draft-team-mark img {{
                width: 1.75rem !important;
                height: 1.75rem !important;
                max-width: 1.75rem !important;
                max-height: 1.75rem !important;
                object-fit: contain;
                flex: 0 0 1.75rem;
            }}
            .sbc-fa-bid-row .sbc-draft-team-wordmark,
            .sbc-fa-commish-leader .sbc-draft-team-wordmark,
            .sbc-fa-team-audit .sbc-draft-team-wordmark {{
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            .sbc-fa-bid-row-leader {{
                background: color-mix(in srgb, {LEAGUE_SECONDARY} 10%, #ffffff);
                outline: 1px solid color-mix(in srgb, {LEAGUE_SECONDARY} 22%, rgba(23, 32, 42, 0.12));
            }}
            .sbc-fa-bid-rank,
            .sbc-fa-bid-money,
            .sbc-fa-bid-years {{
                font-weight: 950;
                font-variant-numeric: tabular-nums;
            }}
            .sbc-fa-bid-time,
            .sbc-fa-bid-comment {{
                color: var(--sbc-muted);
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            .sbc-fa-team-audit-grid {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.5rem;
                margin-bottom: 1rem;
            }}
            .sbc-fa-team-audit {{
                display: grid;
                gap: 0.35rem;
                border: 1px solid rgba(23, 32, 42, 0.1);
                border-radius: 8px;
                padding: 0.5rem 0.55rem;
                background: #ffffff;
                min-width: 0;
            }}
            .sbc-fa-team-audit-main {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.45rem;
                min-width: 0;
            }}
            .sbc-fa-team-audit .sbc-draft-team-mark {{
                min-width: 0;
            }}
            .sbc-fa-team-audit .sbc-draft-team-wordmark {{
                font-family: var(--draft-team-font), "Poppins", "Segoe UI", sans-serif;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            .sbc-fa-team-audit strong {{
                font-weight: 950;
                font-variant-numeric: tabular-nums;
            }}
            .sbc-fa-team-audit-time {{
                display: flex;
                justify-content: space-between;
                gap: 0.45rem;
                color: var(--sbc-muted);
                font-size: 0.7rem;
                font-weight: 850;
                min-width: 0;
            }}
            .sbc-fa-team-audit-time span {{
                text-transform: uppercase;
                letter-spacing: 0.06em;
            }}
            .sbc-fa-team-audit-time em {{
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                font-style: normal;
                font-variant-numeric: tabular-nums;
            }}
            .sbc-fa-team-audit-bad {{
                border-color: #dc2626;
                background: #fff5f5;
            }}
            @media (max-width: 1200px) {{
                .sbc-fa-team-audit-grid {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }}
            }}
            @media (max-width: 760px) {{
                .sbc-fa-team-audit-grid {{
                    grid-template-columns: minmax(0, 1fr);
                }}
                .sbc-fa-commish-top,
                .sbc-fa-commish-leader {{
                    display: grid;
                }}
                .sbc-fa-commish-callout {{
                    text-align: left;
                }}
                .sbc-fa-bid-row {{
                    grid-template-columns: 2rem 1fr;
                }}
                .sbc-fa-response-row {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
        {response_audit_html}
        <div class="sbc-section-label">Team Bid Audit</div>
        <div class="sbc-fa-team-audit-grid">{''.join(team_rows)}</div>
        <div class="sbc-section-label">Signing Desk</div>
        <div class="sbc-fa-commish-grid">{''.join(cards)}</div>
    """)


def render_free_agency_my_bids(team, all_bids, active_bids, excluded_bids, league_view=None):
    team = free_agency_team_from_code(team)
    team_all = all_bids[all_bids["Team"] == team].copy() if all_bids is not None and not all_bids.empty and "Team" in all_bids.columns else pd.DataFrame()
    if team_all.empty:
        render_html(f"""
            <div class="sbc-empty-state">
                {render_free_agency_team_badge(team, empty_text="Your team")} does not have any bids in the current file yet.
            </div>
        """)
        return

    active_team = active_bids[active_bids["Team"] == team].copy() if active_bids is not None and not active_bids.empty and "Team" in active_bids.columns else pd.DataFrame()
    excluded_team = excluded_bids[excluded_bids["Team"] == team].copy() if excluded_bids is not None and not excluded_bids.empty and "Team" in excluded_bids.columns else pd.DataFrame()
    league_lookup = free_agency_league_lookup(league_view)
    signed_set = {free_agency_player_key(player) for player in free_agency_signed_players(league_view)}

    active_keys = {}
    if not active_team.empty:
        active_team["_sign_order_sort"] = active_team["Player"].map(lambda player: parse_free_agency_sign_order(league_lookup.get(free_agency_player_key(player), {}).get("SignOrder", "")))
        active_ranked = active_team.sort_values(["_sign_order_sort", "Timestamp", "Player"], ascending=[True, False, True], na_position="last").reset_index(drop=True)
        for idx, bid in active_ranked.iterrows():
            active_keys[(free_agency_player_key(bid.get("Player", "")), str(bid.get("Response ID", "")), format_free_agency_timestamp(bid.get("Timestamp")))] = idx + 1
    excluded_status = {}
    if not excluded_team.empty:
        for _, bid in excluded_team.iterrows():
            key = (free_agency_player_key(bid.get("Player", "")), str(bid.get("Response ID", "")), format_free_agency_timestamp(bid.get("Timestamp")))
            excluded_status.setdefault(key, free_agency_bid_status_label(bid.get("_bid_status", "Inactive")))

    rows = []
    display_rows = []
    for _, bid in team_all.iterrows():
        player_key = free_agency_player_key(bid.get("Player", ""))
        key = (player_key, str(bid.get("Response ID", "")), format_free_agency_timestamp(bid.get("Timestamp")))
        active_rank = None if player_key in signed_set else active_keys.get(key)
        sign_order_sort = parse_free_agency_sign_order(league_lookup.get(player_key, {}).get("SignOrder", ""))
        inactive_status = "Signed" if player_key in signed_set else excluded_status.get(key, "Inactive")
        display_rows.append((active_rank is None, bid.get("Timestamp"), bid.get("Player", ""), active_rank, inactive_status, bid, sign_order_sort))

    def my_bid_sort_key(item):
        timestamp = pd.to_datetime(item[1], errors="coerce")
        timestamp_sort = -timestamp.timestamp() if not pd.isna(timestamp) else math.inf
        active_sort = item[3] if item[3] else math.inf
        status_priority = {
            "Cut": 1,
            "Old bid": 2,
            "Signed": 3,
            "Locked": 4,
            "Not FA": 5,
            "Inactive": 6,
        }
        inactive_sort = status_priority.get(str(item[4]), 9)
        return (0 if item[3] else inactive_sort, active_sort, item[6], timestamp_sort, str(item[2]))

    display_rows = sorted(display_rows, key=my_bid_sort_key)
    for is_inactive, _, _, active_rank, inactive_status, bid, _ in display_rows:
        status = f"Active #{active_rank}" if active_rank else inactive_status
        row_class = "sbc-fa-my-bid-inactive" if is_inactive else "sbc-fa-my-bid-active"
        rows.append(f"""
            <div class="sbc-fa-my-bid-row {row_class}">
                <span class="sbc-fa-my-bid-status">{escape(status)}</span>
                <span>{render_free_agency_sign_order(league_lookup.get(free_agency_player_key(bid.get("Player", "")), {}).get("SignOrder", ""))}</span>
                <strong>{escape(str(bid.get("Player", "")))}</strong>
                <span>{escape(str(format_money(bid.get("Salary", 0))))}</span>
                <span>{escape(str(bid.get("Years", 1)))} yr</span>
                <span>{escape(format_free_agency_timestamp(bid.get("Timestamp")))}</span>
                <em>{escape(str(bid.get("Comments", "")))}</em>
            </div>
        """)

    render_html(f"""
        <style>
            .sbc-fa-my-bids-head {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                margin-bottom: 0.75rem;
                padding: 0.8rem 0.9rem;
                border: 1px solid rgba(23, 32, 42, 0.12);
                border-radius: 8px;
                background: #ffffff;
            }}
            .sbc-fa-my-bids-head strong {{
                color: var(--sbc-ink);
                font-size: 1rem;
            }}
            .sbc-fa-my-bids-head span {{
                color: var(--sbc-muted);
                font-size: 0.82rem;
                font-weight: 850;
            }}
            .sbc-fa-my-bids-list {{
                display: grid;
                gap: 0.35rem;
            }}
            .sbc-fa-my-bid-row {{
                display: grid;
                grid-template-columns: 6.4rem 5.2rem minmax(12rem, 1.4fr) 7rem 4rem 8rem minmax(8rem, 1fr);
                gap: 0.6rem;
                align-items: center;
                padding: 0.55rem 0.65rem;
                border-radius: 8px;
                border: 1px solid rgba(23, 32, 42, 0.1);
                background: #ffffff;
                font-size: 0.83rem;
            }}
            .sbc-fa-my-bid-active {{
                background: color-mix(in srgb, {LEAGUE_SECONDARY} 9%, #ffffff);
                border-color: color-mix(in srgb, {LEAGUE_SECONDARY} 24%, rgba(23, 32, 42, 0.1));
            }}
            .sbc-fa-my-bid-inactive {{
                background: #f3f4f6;
                color: #6b7280;
                opacity: 0.72;
            }}
            .sbc-fa-my-bid-status {{
                display: inline-flex;
                justify-content: center;
                padding: 0.18rem 0.45rem;
                border-radius: 999px;
                background: rgba(17, 24, 39, 0.08);
                font-size: 0.72rem;
                font-weight: 950;
                white-space: nowrap;
            }}
            .sbc-fa-my-bid-active .sbc-fa-my-bid-status {{
                background: color-mix(in srgb, {LEAGUE_SECONDARY} 18%, #ffffff);
                color: color-mix(in srgb, {LEAGUE_SECONDARY} 80%, #111827);
            }}
            .sbc-fa-my-bid-row .sbc-fa-sign-order {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 2.4rem;
                min-height: 1.65rem;
                padding: 0.15rem 0.5rem;
                border-radius: 999px;
                background: color-mix(in srgb, {LEAGUE_PRIMARY} 10%, #ffffff);
                color: {LEAGUE_PRIMARY};
                font-size: 0.78rem;
                font-weight: 950;
                font-variant-numeric: tabular-nums;
                white-space: nowrap;
            }}
            .sbc-fa-my-bid-row strong,
            .sbc-fa-my-bid-row span {{
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            .sbc-fa-my-bid-row em {{
                color: inherit;
                font-style: normal;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            @media (max-width: 760px) {{
                .sbc-fa-my-bids-head,
                .sbc-fa-my-bid-row {{
                    display: grid;
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
        <div class="sbc-fa-my-bids-head">
            <strong>{render_free_agency_team_badge(team, empty_text="Your team")}</strong>
            <span>{active_team.shape[0]} active bids / {team_all.shape[0]} total bids in file</span>
        </div>
        <div class="sbc-fa-my-bids-list">{''.join(rows)}</div>
    """)


def free_agency_team_snapshot():
    cap_table = safe_table_call(overall_cap_table, df, exceptions, base_cap)
    if cap_table.empty:
        return pd.DataFrame()
    cols = ["Team", "Active Players", "Cap Space", "Tax Space", "Hard Cap", "Apron 1 Space", "Apron 2 Space"]
    snapshot = cap_table[[col for col in cols if col in cap_table.columns]].copy()
    exception_rows = exceptions.copy() if isinstance(exceptions, pd.DataFrame) else pd.DataFrame()
    if not exception_rows.empty and {"Team", "Player", "Y" + str(current_year)}.issubset(exception_rows.columns):
        mle = exception_rows[exception_rows["Player"].astype(str).str.contains("Mid-Level|Bi-Annual", case=False, na=False)].copy()
        mle["Amount"] = pd.to_numeric(mle["Y" + str(current_year)], errors="coerce").fillna(0)
        mle_summary = mle.groupby("Team").apply(
            lambda group: ", ".join(
                f"{row['Player']} ({format_money(row['Amount'])})"
                for _, row in group.iterrows()
                if row["Amount"] > 0
            )
        ).reset_index(name="MLE / BAE Status")
        snapshot = snapshot.merge(mle_summary, on="Team", how="left")
    if "MLE / BAE Status" not in snapshot.columns:
        snapshot["MLE / BAE Status"] = ""
    snapshot["MLE / BAE Status"] = snapshot["MLE / BAE Status"].replace("", "None listed")
    return snapshot


@st.cache_data(ttl=300)
def load_free_agency_league_view():
    try:
        table = read_csv_snapshot("free_agency_league_view", FREE_AGENCY_LEAGUE_VIEW_URL, ttl_seconds=300)
    except Exception:
        return pd.DataFrame()
    expected = ["OldTeam", "Player", "RFA", "DayR", "DayS", "SignOrder", "Offers", "High Bid", "Yrs", "Team"]
    for col in expected:
        if col not in table.columns:
            table[col] = ""
    return table[expected].copy()


def free_agency_team_key(value):
    if is_blank_value(value):
        return ""
    text = clean_pick_display(value)
    if text in team_info:
        return text
    for team, info in team_info.items():
        nickname = str(info.get("nickname", ""))
        if str(text).startswith(team) or (nickname and nickname in str(text)):
            return team
    return ""


def render_free_agency_team_badge(value, empty_text="Open"):
    if is_blank_value(value):
        return f'<span class="sbc-fa-muted">{escape(empty_text)}</span>'
    text = clean_pick_display(value)
    if str(text).strip().lower() in ["no", "none", "nan"]:
        return '<span class="sbc-fa-no">No</span>'
    team = free_agency_team_key(text)
    if team:
        return render_draft_team_wordmark(team, empty_text=empty_text, include_nickname=True)
    return f'<span class="sbc-fa-muted">{escape(str(text))}</span>'


def render_free_agency_day(value):
    if is_blank_value(value):
        return '<span class="sbc-fa-muted">Pending</span>'
    text = clean_pick_display(value)
    return f'<span class="sbc-fa-day">{escape(str(text))}</span>'


def render_free_agency_rfa_status(value):
    text = clean_pick_display(value)
    status = str(text).strip().lower()
    if status == "restricted":
        return '<span class="sbc-fa-status sbc-fa-status-restricted">RFA</span>'
    if status == "unrestricted":
        return '<span class="sbc-fa-status sbc-fa-status-unrestricted">UFA</span>'
    if is_blank_value(value):
        return '<span class="sbc-fa-muted">Unknown</span>'
    return f'<span class="sbc-fa-muted">{escape(str(text))}</span>'


def free_agency_player_picture_lookup():
    if not isinstance(pics, pd.DataFrame) or not {"Player", "Picture_Online"}.issubset(pics.columns):
        return {}
    clean_pics = pics[["Player", "Picture_Online"]].drop_duplicates("Player")
    return {
        free_agency_player_key(row["Player"]): row["Picture_Online"]
        for _, row in clean_pics.iterrows()
        if not is_blank_value(row.get("Player", ""))
    }


def render_free_agency_player_cell(player, picture_lookup):
    player_name = clean_pick_display(player)
    picture = picture_lookup.get(free_agency_player_key(player_name), DRAFT_SILHOUETTE)
    if is_blank_value(picture):
        picture = DRAFT_SILHOUETTE
    return f"""
        <span class="sbc-fa-player-wrap">
            <img class="sbc-fa-player-img" src="{escape(str(picture), quote=True)}" alt="{escape(str(player_name), quote=True)}">
            <strong>{escape(str(player_name))}</strong>
        </span>
    """


def render_free_agency_bird_rights_pill(value):
    if is_blank_value(value):
        return ""
    text = clean_pick_display(value)
    if is_blank_value(text):
        return ""
    status = str(text).strip().lower()
    if "non" in status:
        status_class = "sbc-fa-bird-non"
    elif "early" in status:
        status_class = "sbc-fa-bird-early"
    elif status in {"no", "none", "nan", "n/a"} or "no bird" in status:
        status_class = "sbc-fa-bird-none"
    elif "bird" in status or "full" in status:
        status_class = "sbc-fa-bird-full"
    else:
        status_class = "sbc-fa-bird-other"
    return f'<span class="sbc-fa-bird-rights {status_class}">{escape(str(text))}</span>'


def render_free_agency_status_cell(old_team_value, rfa_value, bird_rights_value=""):
    old_team = free_agency_team_key(old_team_value)
    if old_team:
        logo = team_logo_for_name(old_team)
        team_label = live_team_full_name(old_team)
        logo_html = f'<img class="sbc-fa-status-logo" src="{escape(str(logo), quote=True)}" alt="{escape(str(team_label), quote=True)} logo" referrerpolicy="no-referrer">' if logo else ""
    else:
        logo_html = '<span class="sbc-fa-status-logo sbc-fa-status-logo-empty"></span>'
    return f'<span class="sbc-fa-status-wrap">{logo_html}{render_free_agency_rfa_status(rfa_value)}{render_free_agency_bird_rights_pill(bird_rights_value)}</span>'


def render_free_agency_number(value, money=False):
    if is_blank_value(value):
        return "$0" if money else "0"
    amount = parse_money_input(value)
    if money:
        return format_money(amount or 0)
    try:
        return str(int(float(str(value).replace(",", ""))))
    except ValueError:
        return escape(str(value))


def render_free_agency_offer_pill(value):
    try:
        amount = max(0, min(4, int(float(str(value).replace(",", "")))))
    except (TypeError, ValueError):
        amount = 0
    return f'<span class="sbc-fa-offer-pill sbc-fa-offer-{amount}">{amount}</span>'


def render_free_agency_high_bid_pill(value):
    amount = parse_money_input(value) or 0
    if amount <= 0:
        level = "zero"
    elif amount >= current_salary_cap * 0.25:
        level = "max"
    elif amount >= current_salary_cap * 0.12:
        level = "mid"
    else:
        level = "low"
    return f'<span class="sbc-fa-high-pill sbc-fa-high-{level}">{escape(str(format_money(amount)))}</span>'


def render_free_agency_years_pill(value):
    try:
        years = max(0, min(5, int(float(str(value).replace(",", "")))))
    except (TypeError, ValueError):
        years = 0
    return f'<span class="sbc-fa-years-pill sbc-fa-years-{years}">{years}</span>'


def render_free_agency_contract_pill(years_value, salary_value):
    try:
        years = max(0, int(float(str(years_value).replace(",", ""))))
    except (TypeError, ValueError):
        years = 0
    salary = parse_money_input(salary_value) or 0
    year_text = "year" if years == 1 else "years"
    return f'<span class="sbc-fa-contract-pill">{escape(str(years))} {year_text} starting at {escape(str(format_money(salary)))}</span>'


def render_free_agency_signed_team(team_value):
    team = free_agency_team_key(team_value)
    if not team:
        return render_free_agency_team_badge(team_value, empty_text="Signed")
    logo = team_logo_for_name(team)
    color = team_color_for_name(team)
    secondary = team_secondary_for_name(team)
    font = team_font_for_name(team)
    label = live_team_full_name(team)
    return f"""
        <span class="sbc-fa-signed-team" style="--signed-team-color:{escape(str(color), quote=True)};--signed-team-secondary:{escape(str(secondary), quote=True)};--signed-team-font:{escape(str(font), quote=True)};">
            <img src="{escape(str(logo), quote=True)}" alt="{escape(str(label), quote=True)} logo" referrerpolicy="no-referrer">
            <strong>{escape(str(label))}</strong>
        </span>
    """


def render_free_agency_league_table(data):
    if data is None or data.empty:
        render_html('<div class="sbc-empty-state">Free agency league table is not available yet.</div>')
        return
    rows = []
    signed_cards = []
    picture_lookup = free_agency_player_picture_lookup()
    bird_lookup = free_agency_bird_rights_lookup()
    display_data = data.copy()
    signed_mask = display_data["Team"].apply(is_free_agency_signed_team_value) if "Team" in display_data.columns else pd.Series(False, index=display_data.index)
    signed_data = display_data[signed_mask].copy()
    display_data = display_data[~signed_mask].copy()
    display_data["_signing_day_sort"] = display_data["DayS"].apply(parse_free_agency_day) if "DayS" in display_data.columns else pd.NaT
    display_data["_release_day_sort"] = display_data["DayR"].apply(parse_free_agency_day) if "DayR" in display_data.columns else pd.NaT
    display_data["_sign_order_sort"] = display_data["SignOrder"].apply(parse_free_agency_sign_order) if "SignOrder" in display_data.columns else math.inf
    display_data = display_data.sort_values(
        ["_signing_day_sort", "_release_day_sort", "_sign_order_sort", "Player"],
        ascending=[True, True, True, True],
        na_position="last",
    )
    for _, row in display_data.iterrows():
        player = clean_pick_display(row.get("Player", ""))
        player_key = free_agency_player_key(player)
        old_team = free_agency_team_key(row.get("OldTeam", ""))
        bird_rights = (
            row.get("BirdRights", "")
            or row.get("Bird Rights", "")
            or bird_lookup.get((player_key, old_team), "")
            or bird_lookup.get((player_key, ""), "")
        )
        row_color = team_color_for_name(old_team) if old_team in team_info else ""
        row_style = f' style="--fa-row-color:{escape(str(row_color), quote=True)};"' if row_color else ""
        rows.append(f"""
            <tr{row_style}>
                <td>{render_free_agency_status_cell(row.get("OldTeam", ""), row.get("RFA", ""), bird_rights)}</td>
                <td class="sbc-fa-player">{render_free_agency_player_cell(player, picture_lookup)}</td>
                <td>{render_free_agency_day(row.get("DayR", ""))}</td>
                <td>{render_free_agency_day(row.get("DayS", ""))}</td>
                <td>{render_free_agency_sign_order(row.get("SignOrder", ""))}</td>
                <td class="sbc-fa-number">{render_free_agency_offer_pill(row.get("Offers", ""))}</td>
                <td class="sbc-fa-number">{render_free_agency_high_bid_pill(row.get("High Bid", ""))}</td>
                <td class="sbc-fa-number">{render_free_agency_years_pill(row.get("Yrs", ""))}</td>
                <td>{render_free_agency_team_badge(row.get("Team", ""), empty_text="Unsigned")}</td>
            </tr>
        """)

    signed_data["_signing_day_sort"] = signed_data["DayS"].apply(parse_free_agency_day) if "DayS" in signed_data.columns else pd.NaT
    signed_data["_sign_order_sort"] = signed_data["SignOrder"].apply(parse_free_agency_sign_order) if "SignOrder" in signed_data.columns else math.inf
    signed_data = signed_data.sort_values(["_signing_day_sort", "_sign_order_sort", "Player"], ascending=[True, True, True], na_position="last")
    signed_data["_team_sort"] = signed_data["Team"].apply(lambda value: free_agency_team_key(value) or clean_pick_display(value)) if "Team" in signed_data.columns else ""
    signed_data = signed_data.sort_values(["_team_sort", "_signing_day_sort", "_sign_order_sort", "Player"], ascending=[True, True, True, True], na_position="last")
    signed_groups = {
        str(team_value): team_signings.copy()
        for team_value, team_signings in signed_data.groupby("_team_sort", sort=False, dropna=False)
        if not is_blank_value(team_value)
    }
    signed_team_order = list(Teams)
    signed_team_order.extend(team for team in signed_groups if team not in signed_team_order)
    for team_value in signed_team_order:
        team_signings = signed_groups.get(str(team_value), pd.DataFrame())
        signing_team = free_agency_team_key(team_value)
        team_display = signing_team or clean_pick_display(team_value)
        color = team_color_for_name(signing_team) if signing_team in team_info else LEAGUE_PRIMARY
        secondary = team_secondary_for_name(signing_team) if signing_team in team_info else LEAGUE_SECONDARY
        signing_rows = []
        if team_signings.empty:
            signing_rows.append('<div class="sbc-fa-no-signings">No signings</div>')
        else:
            team_signings = team_signings.sort_values(["_signing_day_sort", "_sign_order_sort", "Player"], ascending=[True, True, True], na_position="last")
            for _, row in team_signings.iterrows():
                player = clean_pick_display(row.get("Player", ""))
                signing_rows.append(f"""
                    <div class="sbc-fa-signing-row">
                        <div class="sbc-fa-signing-player">{render_free_agency_player_cell(player, picture_lookup)}</div>
                        <div class="sbc-fa-signing-meta">
                            {render_free_agency_sign_order(row.get("SignOrder", ""))}
                            {render_free_agency_contract_pill(row.get("Yrs", ""), row.get("High Bid", ""))}
                        </div>
                    </div>
                """)
        signed_cards.append(f"""
            <article class="sbc-fa-signing-card" style="--signed-team-color:{escape(str(color), quote=True)};--signed-team-secondary:{escape(str(secondary), quote=True)};">
                <div class="sbc-fa-signing-team-head">
                    {render_free_agency_signed_team(team_display)}
                    <span>{team_signings.shape[0]} signing{'s' if team_signings.shape[0] != 1 else ''}</span>
                </div>
                <div class="sbc-fa-signing-list">{''.join(signing_rows)}</div>
            </article>
        """)
    signed_section = ""
    if signed_cards:
        signed_section = f"""
            <div class="sbc-section-label">Signed Players</div>
            <div class="sbc-fa-signing-grid">{''.join(signed_cards)}</div>
            <div class="sbc-section-label">Available Players</div>
        """
    render_html(f"""
        <style>
            .sbc-fa-signing-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.6rem;
                margin-bottom: 1rem;
            }}
            .sbc-fa-signing-card {{
                display: grid;
                gap: 0.6rem;
                align-content: start;
                border-radius: 8px;
                border: 1px solid color-mix(in srgb, var(--signed-team-color) 28%, rgba(23, 32, 42, 0.12));
                border-left: 0.4rem solid var(--signed-team-color);
                background: linear-gradient(135deg, color-mix(in srgb, var(--signed-team-color) 13%, #ffffff), color-mix(in srgb, var(--signed-team-secondary) 10%, #ffffff));
                box-shadow: 0 10px 24px rgba(18, 25, 38, 0.075);
                min-height: 5.4rem;
                padding: 0.62rem 0.72rem;
                overflow: hidden;
            }}
            .sbc-fa-signing-team-head {{
                display: grid;
                grid-template-columns: minmax(0, 1fr) auto;
                align-items: center;
                gap: 0.75rem;
                padding-bottom: 0.52rem;
                border-bottom: 1px solid color-mix(in srgb, var(--signed-team-color) 18%, rgba(23, 32, 42, 0.1));
            }}
            .sbc-fa-signing-team-head > span {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-height: 1.65rem;
                border-radius: 999px;
                background: rgba(255,255,255,0.72);
                border: 1px solid color-mix(in srgb, var(--signed-team-color) 22%, rgba(23, 32, 42, 0.12));
                color: color-mix(in srgb, var(--signed-team-color) 78%, #111827);
                font-size: 0.74rem;
                font-weight: 950;
                padding: 0.15rem 0.55rem;
                white-space: nowrap;
            }}
            .sbc-fa-signing-list {{
                display: grid;
                gap: 0.42rem;
            }}
            .sbc-fa-signing-row {{
                display: grid;
                grid-template-columns: minmax(10rem, 1fr) auto;
                align-items: center;
                gap: 0.65rem;
                min-width: 0;
            }}
            .sbc-fa-signing-meta {{
                display: inline-flex;
                align-items: center;
                justify-content: flex-end;
                gap: 0.35rem;
                min-width: 0;
            }}
            .sbc-fa-no-signings {{
                min-height: 2.7rem;
                display: flex;
                align-items: center;
                border-radius: 8px;
                background: rgba(255,255,255,0.48);
                border: 1px dashed color-mix(in srgb, var(--signed-team-color) 24%, rgba(23, 32, 42, 0.14));
                color: var(--sbc-muted);
                font-size: 0.82rem;
                font-weight: 900;
                padding: 0.42rem 0.58rem;
            }}
            .sbc-fa-signing-card .sbc-fa-player-img {{
                width: 2.7rem;
                height: 2.7rem;
            }}
            .sbc-fa-signing-card .sbc-fa-player strong {{
                font-size: 0.96rem;
            }}
            .sbc-fa-signed-team {{
                display: grid;
                grid-template-columns: 2.9rem minmax(0, 1fr);
                align-items: center;
                gap: 0.55rem;
                color: color-mix(in srgb, var(--signed-team-color) 82%, #111827);
                min-width: 0;
            }}
            .sbc-fa-signed-team img {{
                width: 2.9rem;
                height: 2.9rem;
                object-fit: contain;
                filter: drop-shadow(0 10px 16px rgba(18,25,38,0.16));
            }}
            .sbc-fa-signed-team strong {{
                font-family: var(--signed-team-font), "Poppins", sans-serif;
                font-size: clamp(1.05rem, 1.7vw, 1.55rem);
                font-weight: 950;
                line-height: 0.95;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .sbc-fa-contract-pill {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-height: 1.75rem;
                border-radius: 999px;
                background: rgba(255,255,255,0.76);
                border: 1px solid color-mix(in srgb, var(--signed-team-color) 22%, rgba(23, 32, 42, 0.12));
                color: color-mix(in srgb, var(--signed-team-color) 78%, #111827);
                font-size: 0.76rem;
                font-weight: 950;
                font-variant-numeric: tabular-nums;
                padding: 0.18rem 0.58rem;
                white-space: nowrap;
            }}
            .sbc-fa-table-wrap {{
                overflow-x: auto;
                border: 1px solid rgba(23, 32, 42, 0.12);
                border-radius: 8px;
                background: #ffffff;
                box-shadow: 0 14px 34px rgba(18, 25, 38, 0.06);
            }}
            .sbc-fa-table {{
                width: 100%;
                border-collapse: collapse;
                min-width: 66rem;
            }}
            .sbc-fa-table th {{
                background: color-mix(in srgb, {LEAGUE_PRIMARY} 9%, #ffffff);
                color: {LEAGUE_PRIMARY};
                font-size: 0.74rem;
                font-weight: 950;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                text-align: left;
                padding: 0.75rem 0.8rem;
                border-bottom: 1px solid rgba(23, 32, 42, 0.12);
                white-space: nowrap;
            }}
            .sbc-fa-table td {{
                padding: 0.65rem 0.8rem;
                border-bottom: 1px solid rgba(23, 32, 42, 0.08);
                vertical-align: middle;
            }}
            .sbc-fa-table tr[style*="--fa-row-color"] td:first-child {{
                border-left: 0.3rem solid var(--fa-row-color);
            }}
            .sbc-fa-player-wrap {{
                display: inline-flex;
                align-items: center;
                gap: 0.55rem;
                min-width: 0;
            }}
            .sbc-fa-player-img {{
                width: 2.2rem;
                height: 2.2rem;
                object-fit: cover;
                border-radius: 999px;
                background: #111827;
                border: 1px solid rgba(23, 32, 42, 0.12);
                flex: 0 0 auto;
            }}
            .sbc-fa-player strong {{
                color: var(--sbc-ink);
                font-size: 0.95rem;
            }}
            .sbc-fa-number {{
                font-weight: 900;
                font-variant-numeric: tabular-nums;
                text-align: right;
                white-space: nowrap;
            }}
            .sbc-fa-offer-pill,
            .sbc-fa-high-pill,
            .sbc-fa-years-pill {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-height: 1.65rem;
                min-width: 2.35rem;
                padding: 0.15rem 0.55rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 950;
                font-variant-numeric: tabular-nums;
                white-space: nowrap;
            }}
            .sbc-fa-offer-0, .sbc-fa-years-0, .sbc-fa-high-zero {{ background: #f3f4f6; color: #6b7280; }}
            .sbc-fa-offer-1, .sbc-fa-years-1, .sbc-fa-high-low {{ background: color-mix(in srgb, #2563eb 14%, #ffffff); color: #1d4ed8; }}
            .sbc-fa-offer-2, .sbc-fa-years-2 {{ background: color-mix(in srgb, #16a34a 16%, #ffffff); color: #166534; }}
            .sbc-fa-offer-3, .sbc-fa-years-3, .sbc-fa-high-mid {{ background: color-mix(in srgb, #facc15 30%, #ffffff); color: #854d0e; }}
            .sbc-fa-offer-4, .sbc-fa-years-4, .sbc-fa-years-5, .sbc-fa-high-max {{ background: color-mix(in srgb, #dc2626 14%, #ffffff); color: #991b1b; }}
            .sbc-fa-day {{
                display: inline-flex;
                align-items: center;
                min-height: 1.65rem;
                padding: 0.15rem 0.5rem;
                border-radius: 999px;
                background: color-mix(in srgb, {LEAGUE_SECONDARY} 11%, #ffffff);
                color: color-mix(in srgb, {LEAGUE_SECONDARY} 82%, #111827);
                font-size: 0.78rem;
                font-weight: 900;
                white-space: nowrap;
            }}
            .sbc-fa-sign-order {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 2.4rem;
                min-height: 1.65rem;
                padding: 0.15rem 0.5rem;
                border-radius: 999px;
                background: color-mix(in srgb, {LEAGUE_PRIMARY} 10%, #ffffff);
                color: {LEAGUE_PRIMARY};
                font-size: 0.78rem;
                font-weight: 950;
                font-variant-numeric: tabular-nums;
                white-space: nowrap;
            }}
            .sbc-fa-status {{
                display: inline-flex;
                align-items: center;
                min-height: 1.65rem;
                padding: 0.15rem 0.6rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 950;
                white-space: nowrap;
            }}
            .sbc-fa-status-wrap {{
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                white-space: nowrap;
            }}
            .sbc-fa-status-logo {{
                width: 2rem;
                height: 2rem;
                object-fit: contain;
                border-radius: 999px;
                background: #ffffff;
                border: 1px solid rgba(23, 32, 42, 0.12);
                padding: 0.12rem;
            }}
            .sbc-fa-status-logo-empty {{
                background: color-mix(in srgb, {LEAGUE_PRIMARY} 8%, #ffffff);
            }}
            .sbc-fa-status-restricted {{
                background: color-mix(in srgb, #CFFFFF 72%, #ffffff);
                color: #0f766e;
            }}
            .sbc-fa-status-unrestricted {{
                background: color-mix(in srgb, #D9D2E9 72%, #ffffff);
                color: #6d28d9;
            }}
            .sbc-fa-bird-rights {{
                display: inline-flex;
                align-items: center;
                min-height: 1.65rem;
                padding: 0.15rem 0.5rem;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 950;
                white-space: nowrap;
            }}
            .sbc-fa-bird-full {{
                background: color-mix(in srgb, #16a34a 18%, #ffffff);
                color: #166534;
            }}
            .sbc-fa-bird-early {{
                background: color-mix(in srgb, #2563eb 16%, #ffffff);
                color: #1d4ed8;
            }}
            .sbc-fa-bird-non {{
                background: color-mix(in srgb, #f97316 18%, #ffffff);
                color: #9a3412;
            }}
            .sbc-fa-bird-none {{
                background: #f3f4f6;
                color: #6b7280;
            }}
            .sbc-fa-bird-other {{
                background: color-mix(in srgb, #facc15 28%, #ffffff);
                color: #854d0e;
            }}
            .sbc-fa-no,
            .sbc-fa-muted {{
                color: var(--sbc-muted);
                font-size: 0.82rem;
                font-weight: 850;
            }}
            @media (max-width: 980px) {{
                .sbc-fa-signing-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            @media (max-width: 680px) {{
                .sbc-fa-signing-team-head,
                .sbc-fa-signing-row {{
                    grid-template-columns: 1fr;
                }}
                .sbc-fa-signing-meta {{
                    justify-content: flex-start;
                    flex-wrap: wrap;
                }}
            }}
        </style>
        {signed_section}
        <div class="sbc-fa-table-wrap">
            <table class="sbc-fa-table">
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Player</th>
                        <th>Released</th>
                        <th>Signing Day</th>
                        <th>Sign Order</th>
                        <th>Offers</th>
                        <th>High Bid</th>
                        <th>Yrs</th>
                        <th>Team</th>
                    </tr>
                </thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
    """)


def team_logo_for_name(team):
    return team_info.get(str(team), {}).get("logo", "")


def team_color_for_name(team):
    return team_info.get(str(team), {}).get("bg", "var(--sbc-ink)")


def team_secondary_for_name(team):
    return team_info.get(str(team), {}).get("bg2", team_color_for_name(team))


def team_font_for_name(team):
    return TEAM_FONTS.get(str(team), "Poppins")


def team_nickname_for_name(team):
    return team_info.get(str(team), {}).get("nickname", "")


def team_abbrev_for_name(team):
    return TEAM_ABBREVIATIONS.get(str(team), str(team)[:3].upper())


def team_names_from_list(value):
    if is_blank_value(value):
        return []
    text = str(value)
    if text.lower().strip() in ["false", "nan", "none", "nat"]:
        return []
    names = []
    for part in re.split(r",|/|;|\bor\b", text):
        team = part.strip()
        if team in team_info:
            names.append(team)
    return names


def render_team_logo_cluster(value):
    teams = team_names_from_list(value)
    if not teams:
        display = clean_pick_display(value)
        return escape(str(display))
    logos = []
    for team in teams:
        logo = team_logo_for_name(team)
        logos.append(
            f'<span class="sbc-pick-logo-chip" title="{escape(live_team_full_name(team), quote=True)}">'
            f'<img class="sbc-pick-logo" src="{escape(str(logo), quote=True)}" alt="{escape(live_team_full_name(team), quote=True)} logo" referrerpolicy="no-referrer">'
            f'<span>{escape(team_abbrev_for_name(team))}</span>'
            f'</span>'
        )
    return f'<div class="sbc-pick-logo-cluster">{"".join(logos)}</div>'


def render_team_logo_chip_from_url(value):
    logo = "" if is_blank_value(value) else str(value)
    if not logo.strip():
        return escape(str(clean_pick_display(value)))
    logo_to_team = {info.get("logo", ""): team for team, info in team_info.items()}
    team = logo_to_team.get(logo, "")
    label = live_team_full_name(team) if team else ""
    abbrev = team_abbrev_for_name(team) if team else ""
    return (
        f'<div class="sbc-pick-logo-cluster sbc-pick-logo-cluster-single">'
        f'<span class="sbc-pick-logo-chip" title="{escape(label, quote=True)}">'
        f'<img class="sbc-pick-logo" src="{escape(logo, quote=True)}" alt="{escape(label, quote=True)} logo" referrerpolicy="no-referrer">'
        f'<span>{escape(abbrev)}</span>'
        f'</span></div>'
    )


def render_slot_team(value):
    team = clean_pick_display(value)
    font = team_font_for_name(team)
    return (
        f'<span class="sbc-pick-slot-team" '
        f'style="--slot-font:{escape(str(font), quote=True)};">'
        f'{escape(live_team_full_name(team))}'
        f'</span>'
    )


def render_draft_team_wordmark(value, empty_text="Not on roster", include_nickname=False):
    team = clean_pick_display(value)
    if is_blank_value(value) or team == "â€”" or team not in team_info:
        return f'<span class="sbc-draft-team-empty">{escape(empty_text)}</span>'
    color = team_color_for_name(team)
    secondary = team_secondary_for_name(team)
    font = team_font_for_name(team)
    logo = team_logo_for_name(team)
    display = live_team_full_name(team) if include_nickname else str(team)
    return (
        f'<span class="sbc-draft-team-mark" '
        f'style="--draft-team-color:{escape(str(color), quote=True)};--draft-team-secondary:{escape(str(secondary), quote=True)};--draft-team-font:{escape(str(font), quote=True)};">'
        f'<img src="{escape(str(logo), quote=True)}" alt="{escape(display, quote=True)} logo" referrerpolicy="no-referrer">'
        f'<span class="sbc-draft-team-wordmark">{escape(display)}</span>'
        f'</span>'
    )


def team_visuals(team):
    info = team_info.get(resolve_team_key(team), {})
    return {
        "logo": info.get("logo", ""),
        "primary": info.get("bg", LEAGUE_PRIMARY),
        "secondary": info.get("bg2", LEAGUE_SECONDARY),
        "text": info.get("text", "#ffffff"),
        "nickname": info.get("nickname", ""),
        "font": TEAM_FONTS.get(resolve_team_key(team), "Poppins"),
    }


def resolve_team_key(team):
    value = str(team).strip()
    if value in team_info:
        return value
    lowered = value.lower()
    if lowered == "san diego wave":
        return "San Diego"
    for key, info in team_info.items():
        nickname = str(info.get("nickname", "")).strip()
        full_name = f"{key} {nickname}".strip()
        if lowered in {str(key).lower(), nickname.lower(), full_name.lower()}:
            return key
    return value


def current_year_salary_for_players(data, players):
    if not players or f"Y{current_year}" not in data.columns:
        return 0
    return data[data["Player"].isin(players)][f"Y{current_year}"].fillna(0).sum()


def trade_active_player_options(data, trade_team=None, incoming=False):
    if data is None or data.empty:
        return []
    type_col = f"Type{current_year}"
    mask = data["Type"].eq("Active Players")
    if type_col in data.columns:
        mask = mask & ~data[type_col].isin(["Unrestricted", "Restricted", "Dead"])
    if "Trade.Restriction" in data.columns:
        mask = mask & (data["Trade.Restriction"].isna() | data["Trade.Restriction"].eq(""))
    if trade_team:
        mask = mask & (data["Team"].ne(trade_team) if incoming else data["Team"].eq(trade_team))
    return data.loc[mask, "Player"].dropna().sort_values().tolist()


def trade_sign_and_trade_options(data, trade_team=None, incoming=False):
    if data is None or data.empty:
        return []
    type_col = f"Type{current_year}"
    if type_col not in data.columns:
        return []
    mask = data[type_col].isin(["Unrestricted", "Restricted"])
    if trade_team:
        mask = mask & (data["Team"].ne(trade_team) if incoming else data["Team"].eq(trade_team))
    return data.loc[mask, "Player"].dropna().sort_values().tolist()


def trade_single_salary_map(player, salary):
    if not player:
        return {}
    return {player: float(salary or 0)}


def trade_salary_total(salary_map):
    return sum(float(value or 0) for value in salary_map.values())


TRADE_MATCH_SMALL_OUTGOING_LIMIT = 8846000
TRADE_MATCH_MID_OUTGOING_LIMIT = 35384000
TRADE_MATCH_MID_PADDING = 9096000
TRADE_MATCH_STANDARD_PADDING = 250000


def trade_salary_matching_review(outgoing_salary, incoming_salary, tax_before):
    outgoing_salary = float(outgoing_salary or 0)
    incoming_salary = float(incoming_salary or 0)
    if outgoing_salary <= 0 and incoming_salary > 0:
        return {
            "label": "No outgoing salary",
            "detail": "Incoming salary needs an exception, cap room, minimum exception, or S&T structure.",
            "max_incoming": 0,
            "tpe": 0,
            "status": "watch",
        }
    if incoming_salary < outgoing_salary:
        tpe_amount = outgoing_salary - incoming_salary
        return {
            "label": "Taking back less salary",
            "detail": f"Creates a trade exception of {format_money(tpe_amount)} if otherwise eligible.",
            "max_incoming": outgoing_salary,
            "tpe": tpe_amount,
            "status": "clear",
        }
    if tax_before >= current_luxury_tax:
        max_incoming = outgoing_salary * 1.25 + TRADE_MATCH_STANDARD_PADDING
        return {
            "label": "Always 125% + $250K",
            "detail": f"Tax-team matching band. Max incoming salary: {format_money(max_incoming)}.",
            "max_incoming": max_incoming,
            "tpe": 0,
            "status": "block" if incoming_salary > max_incoming else "clear",
        }
    if outgoing_salary <= TRADE_MATCH_SMALL_OUTGOING_LIMIT:
        max_incoming = outgoing_salary * 2 + TRADE_MATCH_STANDARD_PADDING
        return {
            "label": "Up to $8.846M",
            "detail": f"200% plus $250K. Max incoming salary: {format_money(max_incoming)}.",
            "max_incoming": max_incoming,
            "tpe": 0,
            "status": "block" if incoming_salary > max_incoming else "clear",
        }
    if outgoing_salary <= TRADE_MATCH_MID_OUTGOING_LIMIT:
        max_incoming = outgoing_salary + TRADE_MATCH_MID_PADDING
        return {
            "label": "$8.846M-$35.384M",
            "detail": f"$9.096M padding. Max incoming salary: {format_money(max_incoming)}.",
            "max_incoming": max_incoming,
            "tpe": 0,
            "status": "block" if incoming_salary > max_incoming else "clear",
        }
    max_incoming = outgoing_salary * 1.25 + TRADE_MATCH_STANDARD_PADDING
    return {
        "label": "$35.384M and up",
        "detail": f"125% plus $250K. Max incoming salary: {format_money(max_incoming)}.",
        "max_incoming": max_incoming,
        "tpe": 0,
        "status": "block" if incoming_salary > max_incoming else "clear",
    }


def trade_hard_cap_tile_labels(apron):
    current = {
        "First Apron": "Apron 1",
        "Second Apron": "Apron 2",
    }.get(apron.get("existing_hard_cap"), "None")
    activated_limits = {limit for _, limit in apron.get("activated_hard_caps", [])}
    if not activated_limits:
        activated = "None"
    elif activated_limits == {current_apron_1}:
        activated = "Apron 1"
    elif activated_limits == {current_apron_2}:
        activated = "Apron 2"
    else:
        activated = "Apron 1 + 2"
    effective_limit = apron.get("effective_hard_cap_limit")
    if effective_limit == current_apron_1:
        final = "Over Apron 1" if apron.get("tax_after", 0) > current_apron_1 else "Apron 1"
    elif effective_limit == current_apron_2:
        final = "Over Apron 2" if apron.get("tax_after", 0) > current_apron_2 else "Apron 2"
    else:
        final = "None"
    return current, activated, final


def render_trade_hero(team, outgoing_count=None, incoming_count=None):
    visuals = team_visuals(team)
    counts_html = ""
    if outgoing_count is not None and incoming_count is not None:
        counts_html = f"""
            <div class="sbc-trade-hero-counts">
                <span><strong>{escape(str(outgoing_count))}</strong><em>Outgoing</em></span>
                <span><strong>{escape(str(incoming_count))}</strong><em>Incoming</em></span>
            </div>
        """
    render_html(f"""
        <div class="sbc-trade-hero" style="--trade-primary:{escape(str(visuals["primary"]), quote=True)};--trade-secondary:{escape(str(visuals["secondary"]), quote=True)};--trade-text:{escape(str(visuals["text"]), quote=True)};">
            <div class="sbc-trade-hero-bg"></div>
            <div class="sbc-trade-hero-inner">
                <div class="sbc-trade-logo-frame">
                    <img src="{escape(str(visuals["logo"]), quote=True)}" alt="{escape(str(team), quote=True)} logo" referrerpolicy="no-referrer">
                </div>
                <div>
                    <div class="sbc-trade-eyebrow">Transaction Command Center</div>
                    <div class="sbc-trade-heading">Trade Machine</div>
                    <div class="sbc-trade-subcopy">Build the deal, inspect the assets, and run roster, apron, cash, exception, and salary-return checks from one front-office desk.</div>
                </div>
                {counts_html}
            </div>
        </div>
    """)


def render_trade_panel_header(title, subtitle, team=None, tone="blue"):
    style = ""
    logo_html = ""
    if team:
        visuals = team_visuals(team)
        style = f' style="--trade-primary:{escape(str(visuals["primary"]), quote=True)};--trade-secondary:{escape(str(visuals["secondary"]), quote=True)};"'
        logo_html = f'<img src="{escape(str(visuals["logo"]), quote=True)}" alt="{escape(str(team), quote=True)} logo" referrerpolicy="no-referrer">'
    render_html(f"""
        <div class="sbc-trade-panel-head sbc-trade-panel-{tone}"{style}>
            {logo_html}
            <div>
                <span>{escape(title)}</span>
                <em>{escape(subtitle)}</em>
            </div>
        </div>
    """)


def render_trade_summary_card(title, value, detail, tone="blue"):
    render_html(f"""
        <section class="sbc-trade-summary-card sbc-trade-summary-{tone}">
            <span>{escape(title)}</span>
            <strong>{escape(str(value))}</strong>
            <em>{escape(str(detail))}</em>
        </section>
    """)


def render_trade_asset_chips(title, items, empty_text, tone="blue"):
    if items:
        chips = "".join(f'<span class="sbc-trade-chip">{escape(str(item))}</span>' for item in items)
    else:
        chips = f'<span class="sbc-trade-empty-chip">{escape(empty_text)}</span>'
    render_html(f"""
        <section class="sbc-trade-chip-card sbc-trade-summary-{tone}">
            <div class="sbc-trade-chip-title">{escape(title)}</div>
            <div class="sbc-trade-chip-grid">{chips}</div>
        </section>
    """)


def team_from_logo(logo):
    for team, info in team_info.items():
        if str(info.get("logo", "")) == str(logo):
            return team
    return ""


def render_trade_team_mark(team):
    owner_teams = team_names_from_list(team)
    if len(owner_teams) > 1:
        return render_team_logo_cluster(team)
    if len(owner_teams) == 1:
        team = owner_teams[0]
    if not team or team not in team_info:
        return '<span class="sbc-trade-ledger-muted">League</span>'
    visuals = team_visuals(team)
    return (
        f'<span class="sbc-trade-ledger-team" style="--trade-ledger-team:{escape(str(visuals["primary"]), quote=True)};--trade-ledger-font:{escape(str(visuals["font"]), quote=True)};">'
        f'<img src="{escape(str(visuals["logo"]), quote=True)}" alt="{escape(str(team), quote=True)} logo" referrerpolicy="no-referrer">'
        f'<strong>{escape(live_team_full_name(team))}</strong>'
        f'</span>'
    )


def trade_pick_row_for_label(draft_picks, pick_label):
    key = trade_pick_key_from_label(pick_label)
    if key is None or draft_picks is None or draft_picks.empty:
        return None
    first_col = draft_picks["OGTeam"].astype(str).str.strip().eq(key[0])
    year_col = pd.to_numeric(draft_picks["Year"], errors="coerce").fillna(-1).astype(int).eq(key[1])
    round_col = draft_picks["Round"].apply(trade_pick_round_key).eq(key[2])
    matches = draft_picks[first_col & year_col & round_col]
    if matches.empty:
        return None
    return matches.iloc[0]


def trade_pick_owner_from_label(draft_picks, pick_label, fallback_team=""):
    row = trade_pick_row_for_label(draft_picks, pick_label)
    if row is None:
        return fallback_team
    owner_text = clean_pick_display(row.get("CurrentTeam", ""))
    owners = team_names_from_list(owner_text)
    return owner_text if owners else fallback_team


def trade_pick_note_from_label(draft_picks, pick_label):
    row = trade_pick_row_for_label(draft_picks, pick_label)
    if row is None:
        return ""
    if "Explanation" in row.index and not is_blank_value(row.get("Explanation", "")):
        return clean_pick_display(row.get("Explanation", ""))
    return ""


def trade_commissioner_paragraph(trade_team, players_in, players_out, picks_in, picks_out, exceptions_out, cash_out, roster_after, stepien, apron, salary_match=None):
    overall_priority = {"block": 2, "watch": 1, "clear": 0}
    overall_status = max([stepien["status"], apron["status"]], key=lambda item: overall_priority[item])
    overall_label = {"clear": "Green", "watch": "Yellow", "block": "Red"}[overall_status]
    status_word = {"clear": "approval-ready", "watch": "needs commissioner review", "block": "not approvable as submitted"}[overall_status]
    player_out_text = ", ".join(players_out) if players_out else "no players"
    player_in_text = ", ".join(players_in) if players_in else "no players"
    pick_out_text = ", ".join(picks_out) if picks_out else "no picks"
    pick_in_text = ", ".join(picks_in) if picks_in else "no picks"
    exceptions_text = ", ".join(exceptions_out) if exceptions_out else "no exceptions"
    salary_text = f"Salary matching: {salary_match['label']} - {salary_match['detail']} " if salary_match else ""
    return (
        f"{live_team_full_name(trade_team)} proposes to send out {player_out_text} and {pick_out_text}, "
        f"and receive {player_in_text} and {pick_in_text}. The trade changes team salary from "
        f"{format_money(apron['tax_before'])} to {format_money(apron['tax_after'])}, with "
        f"{format_money(apron['outgoing_salary'])} outgoing salary and {format_money(apron['incoming_salary'])} incoming salary. "
        f"Roster count would be {roster_after}. Stepien review: {stepien['message']} "
        f"{salary_text}"
        f"Apron review: {apron.get('hard_cap_summary', ' '.join(flag[2] for flag in apron['flags']))} Exceptions used: {exceptions_text}. "
        f"Overall flag: {overall_label} ({status_word})."
    )


def render_trade_asset_ledger(trade_team, players_out, players_in, picks_out, picks_in, exceptions_out, exceptions_in, cash_out, cash_in, incoming_salary, outgoing_salary, salary_delta, cap_after, roster_after, stepien=None, apron=None, sign_trade_out=None, sign_trade_in=None):
    visuals = team_visuals(trade_team)
    sign_trade_out = sign_trade_out or {}
    sign_trade_in = sign_trade_in or {}

    def asset_row(asset_type, asset, team, amount="", detail=""):
        detail_html = f'<em>{escape(str(detail))}</em>' if not is_blank_value(detail) else ""
        amount_html = f'<b>{escape(str(amount))}</b>' if not is_blank_value(amount) else ""
        return f"""
            <div class="sbc-trade-board-row">
                <div class="sbc-trade-board-type">{escape(asset_type)}</div>
                <div class="sbc-trade-board-asset">{asset}{detail_html}</div>
                <div class="sbc-trade-board-team">{render_trade_team_mark(team)}</div>
                <div class="sbc-trade-board-money">{amount_html}</div>
            </div>
        """

    outgoing_rows = []
    incoming_rows = []
    outgoing_names = []
    incoming_names = []
    player_out_names = []
    player_in_names = []
    for _, row in players_out.iterrows():
        name = str(row.get("Player", ""))
        outgoing_names.append(name)
        player_out_names.append(name)
        pic = row.get(" ", "")
        img = f'<img class="sbc-trade-player-img" src="{escape(str(pic), quote=True)}" alt="{escape(name, quote=True)}">' if not is_blank_value(pic) else '<span class="sbc-trade-player-img sbc-trade-player-empty"></span>'
        outgoing_rows.append(asset_row("Player", f'<span class="sbc-trade-player">{img}<strong>{escape(name)}</strong></span>', trade_team, format_money(row.get(str(current_year), "")), row.get("Bird Rights", "")))

    for _, row in players_in.iterrows():
        name = str(row.get("Player", ""))
        incoming_names.append(name)
        player_in_names.append(name)
        pic = row.get(" ", "")
        team = team_from_logo(row.get("Team_logo", ""))
        img = f'<img class="sbc-trade-player-img" src="{escape(str(pic), quote=True)}" alt="{escape(name, quote=True)}">' if not is_blank_value(pic) else '<span class="sbc-trade-player-img sbc-trade-player-empty"></span>'
        incoming_rows.append(asset_row("Player", f'<span class="sbc-trade-player">{img}<strong>{escape(name)}</strong></span>', team, format_money(row.get(str(current_year), "")), row.get("Bird Rights", "")))
        if team:
            incoming_names[-1] = f"{name} from {live_team_full_name(team)}"

    def sign_trade_row(player, amount, side):
        row = df[df["Player"].eq(player)]
        team = trade_team if side == "out" else (str(row.iloc[0].get("Team", "")) if not row.empty else "")
        pic = ""
        if not row.empty:
            pic_row = pics[pics["Player"].eq(player)] if "Player" in pics.columns else pd.DataFrame()
            if not pic_row.empty:
                pic = pic_row.iloc[0].get("Picture_Online", "")
        img = f'<img class="sbc-trade-player-img" src="{escape(str(pic), quote=True)}" alt="{escape(player, quote=True)}">' if not is_blank_value(pic) else '<span class="sbc-trade-player-img sbc-trade-player-empty"></span>'
        return asset_row("S&T Player", f'<span class="sbc-trade-player">{img}<strong>{escape(player)}</strong></span>', team, format_money(amount), "Sign-and-trade salary")

    for player, amount in sign_trade_out.items():
        if amount:
            outgoing_names.append(player)
            player_out_names.append(player)
            outgoing_rows.append(sign_trade_row(player, amount, "out"))

    for player, amount in sign_trade_in.items():
        if amount:
            incoming_names.append(player)
            player_in_names.append(player)
            incoming_rows.append(sign_trade_row(player, amount, "in"))

    for pick in picks_out:
        outgoing_names.append(str(pick))
        outgoing_rows.append(asset_row("Draft Pick", escape(str(pick)), trade_team, "", trade_pick_note_from_label(dp, pick)))
    for pick in picks_in:
        pick_team = trade_pick_owner_from_label(dp, pick)
        incoming_names.append(str(pick))
        incoming_rows.append(asset_row("Draft Pick", escape(str(pick)), pick_team, "", trade_pick_note_from_label(dp, pick)))
    for exception in exceptions_out:
        outgoing_names.append(str(exception))
        outgoing_rows.append(asset_row("Exception", escape(str(exception)), trade_team, "", "Exception used"))
    for exception in exceptions_in:
        incoming_names.append(str(exception))
        incoming_rows.append(asset_row("Exception", escape(str(exception)), "", "", "Exception received/used"))
    if cash_out:
        outgoing_names.append(format_money(cash_out))
        outgoing_rows.append(asset_row("Cash", "Cash Consideration", trade_team, format_money(cash_out), "Cash sent"))
    if cash_in:
        incoming_names.append(format_money(cash_in))
        incoming_rows.append(asset_row("Cash", "Cash Consideration", "", format_money(cash_in), "Cash received"))

    if not outgoing_rows:
        outgoing_rows.append('<div class="sbc-trade-board-empty">Nothing outgoing.</div>')
    if not incoming_rows:
        incoming_rows.append('<div class="sbc-trade-board-empty">Nothing incoming.</div>')

    def join_words(items):
        clean = [str(item) for item in items if str(item).strip()]
        if not clean:
            return "nothing"
        if len(clean) == 1:
            return clean[0]
        if len(clean) == 2:
            return f"{clean[0]} and {clean[1]}"
        return f"{', '.join(clean[:-1])}, and {clean[-1]}"

    stepien = stepien or trade_stepien_review(dp, trade_team, picks_in, picks_out)
    apron = apron or trade_apron_review(trade_team, player_in_names, player_out_names, exceptions_out, cash_out, trade_salary_total(sign_trade_in), trade_salary_total(sign_trade_out))
    salary_match = trade_salary_matching_review(outgoing_salary, incoming_salary, apron.get("tax_before", 0))
    narrative = trade_commissioner_paragraph(trade_team, player_in_names, player_out_names, picks_in, picks_out, exceptions_out, cash_out, roster_after, stepien, apron, salary_match)
    apron_status = apron.get("status", "clear")
    apron_tile_class = f"sbc-trade-apron-{escape(apron_status)}"
    current_hard_cap, activated_hard_cap, final_hard_cap = trade_hard_cap_tile_labels(apron)
    salary_match_class = f"sbc-trade-apron-{escape(salary_match.get('status', 'clear'))}"

    render_html(f"""
        <section class="sbc-trade-ledger sbc-trade-board" style="--trade-ledger-primary:{escape(str(visuals["primary"]), quote=True)};--trade-ledger-secondary:{escape(str(visuals["secondary"]), quote=True)};--trade-ledger-text:{escape(str(visuals["text"]), quote=True)};">
            <div class="sbc-trade-ledger-head">
                <span>Trade Board</span>
                <em>{escape(live_team_full_name(trade_team))} deal sheet</em>
            </div>
            <div class="sbc-trade-board-grid">
                <div class="sbc-trade-board-panel sbc-trade-board-out">
                    <div class="sbc-trade-board-title">Outgoing</div>
                    <div class="sbc-trade-board-headrow"><span>Type</span><span>Asset</span><span>Team</span><span>Amount</span></div>
                    {''.join(outgoing_rows)}
                </div>
                <div class="sbc-trade-board-panel sbc-trade-board-in">
                    <div class="sbc-trade-board-title">Incoming</div>
                    <div class="sbc-trade-board-headrow"><span>Type</span><span>Asset</span><span>Team</span><span>Amount</span></div>
                    {''.join(incoming_rows)}
                </div>
            </div>
            <div class="sbc-trade-math-strip">
                <span><strong>{escape(format_money(outgoing_salary))}</strong><em>Outgoing Salary</em></span>
                <span><strong>{escape(format_money(incoming_salary))}</strong><em>Incoming Salary</em></span>
                <span><strong>{escape(format_money(salary_delta))}</strong><em>Net Salary</em></span>
                <span class="{salary_match_class}"><strong>{escape(salary_match["label"])}</strong><em>Salary Match</em></span>
                <span><strong>{escape(str(roster_after))}</strong><em>Players After</em></span>
                <span class="{apron_tile_class}"><strong>{escape(current_hard_cap)}</strong><em>Current Hard Cap</em></span>
                <span class="{apron_tile_class}"><strong>{escape(activated_hard_cap)}</strong><em>Activated</em></span>
                <span class="{apron_tile_class}"><strong>{escape(final_hard_cap)}</strong><em>End Result</em></span>
            </div>
            <div class="sbc-trade-narrative">{escape(narrative)}</div>
        </section>
    """)


def trade_cap_type_after(players_in, players_out, trade_team, incoming_salary_extra=0, outgoing_salary_extra=0):
    team_total = get_tax_total(df, trade_team)
    team_total -= current_year_salary_for_players(df, players_out)
    team_total += current_year_salary_for_players(df, players_in) + float(incoming_salary_extra or 0)
    if team_total < current_salary_cap:
        return "Cap"
    if team_total < current_luxury_tax:
        return "Standard"
    if team_total < current_apron_1:
        return "Tax"
    if team_total < current_apron_2:
        return "First"
    return "Second"


def trade_pick_key_from_label(label):
    text = clean_pick_display(label)
    match = re.match(r"^(?P<team>.+?)\s+(?P<year>\d{4}(?:\.\d+)?)\s+(?P<round>.+)$", str(text).strip())
    if not match:
        return None
    try:
        year = int(float(match.group("year")))
    except (TypeError, ValueError):
        return None
    return match.group("team").strip(), year, trade_pick_round_key(match.group("round"))


def trade_pick_key_from_row(row):
    try:
        year = int(float(row.get("Year", 0)))
    except (TypeError, ValueError):
        return None
    return str(row.get("OGTeam", "")).strip(), year, trade_pick_round_key(row.get("Round", ""))


def trade_pick_round_key(value):
    text = clean_pick_display(value)
    normalized = str(text).strip().lower()
    if normalized in {"first", "first round", "round 1", "r1"} or "1st" in normalized:
        return "1"
    if normalized in {"second", "second round", "round 2", "r2"} or "2nd" in normalized:
        return "2"
    match = re.search(r"\d+", str(text))
    return match.group(0) if match else str(text).strip().lower()


def trade_pick_is_first(value):
    return trade_pick_round_key(value) == "1"


def team_list_contains(value, team):
    return team in team_names_from_list(value) or team in [part.strip() for part in str(value).split(",")]


def trade_truthy(value):
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def trade_stepien_review(draft_picks, trade_team, picks_in, picks_out):
    future_years = list(range(current_year, current_year + 7))
    firsts = draft_picks[draft_picks["Round"].apply(trade_pick_is_first)].copy()
    outgoing_keys = {trade_pick_key_from_label(pick) for pick in picks_out}
    incoming_keys = {trade_pick_key_from_label(pick) for pick in picks_in}
    outgoing_keys.discard(None)
    incoming_keys.discard(None)
    coverage = {}
    for _, row in firsts.iterrows():
        key = trade_pick_key_from_row(row)
        if key is None:
            continue
        if key in outgoing_keys:
            continue
        if key in incoming_keys:
            coverage.setdefault(key[1], []).append(key)
            continue
        if trade_truthy(row.get("FullyOwned", False)) and team_list_contains(row.get("CurrentTeam", ""), trade_team):
            coverage.setdefault(key[1], []).append(key)
    for key in incoming_keys:
        if key and key[2] == "1":
            coverage.setdefault(key[1], []).append(key)
    missing_years = [year for year in future_years if not coverage.get(year)]
    broken_pairs = [(year, year + 1) for year in future_years[:-1] if year in missing_years and year + 1 in missing_years]
    outgoing_firsts = [
        pick for pick in picks_out
        if (trade_pick_key_from_label(pick) or ("", 0, ""))[2] == "1"
    ]
    if broken_pairs:
        status = "block"
        message = f"Projected first-round coverage has consecutive open years: {', '.join(f'{a}-{b}' for a, b in broken_pairs)}."
    elif outgoing_firsts:
        status = "watch"
        message = f"{live_team_full_name(trade_team)} is trading {len(outgoing_firsts)} first-round pick(s), but still has first-round coverage in every rolling two-year window."
    else:
        status = "clear"
        message = "No outgoing first-round picks, so the Stepien rule is not stressed."
    covered_years = sorted(coverage)
    return {
        "status": status,
        "message": message,
        "covered_years": covered_years,
        "missing_years": missing_years,
        "broken_pairs": broken_pairs,
    }


def trade_apron_review(trade_team, players_in, players_out, exceptions_out, cash_out, incoming_salary_extra=0, outgoing_salary_extra=0):
    regular_outgoing_salary = current_year_salary_for_players(df, players_out)
    regular_incoming_salary = current_year_salary_for_players(df, players_in)
    outgoing_salary = regular_outgoing_salary + float(outgoing_salary_extra or 0)
    incoming_salary = regular_incoming_salary + float(incoming_salary_extra or 0)
    tax_before = get_tax_total(df, trade_team)
    tax_after = tax_before - regular_outgoing_salary + regular_incoming_salary + float(incoming_salary_extra or 0)
    existing_hard_cap = team_hard_cap(base_cap, trade_team)
    try:
        cash_value = 0.0 if cash_out is None else float(cash_out)
    except (TypeError, ValueError):
        cash_value = 0.0
    if math.isnan(cash_value):
        cash_value = 0.0

    hard_cap_levels = {"No Cap": 0, "First Apron": 1, "Second Apron": 2}
    hard_cap_limits_by_level = {1: current_apron_1, 2: current_apron_2}
    existing_level = hard_cap_levels.get(existing_hard_cap, 0)
    flags = []
    existing_caps = []
    activated_caps = []
    if existing_hard_cap == "First Apron":
        existing_caps.append(("Current First Apron hard cap", current_apron_1))
    elif existing_hard_cap == "Second Apron":
        existing_caps.append(("Current Second Apron hard cap", current_apron_2))

    minimum_exception_used = any("Minimum" in str(exc) for exc in exceptions_out)
    minimum_only_acquisition = minimum_exception_used and len(players_in) == 1 and len(players_out) == 0 and incoming_salary <= max_minimum
    if incoming_salary > outgoing_salary and not minimum_only_acquisition:
        activated_caps.append(("Taking back more salary than sent out", current_apron_1))
    if any("Bi-Annual" in str(exc) or "Mid-Level" in str(exc) for exc in exceptions_out):
        activated_caps.append(("Using BAE/MLE", current_apron_1))
    if cash_value > 0:
        activated_caps.append(("Sending cash", current_apron_2))
    if any("S&T" in str(exc) for exc in exceptions_out):
        activated_caps.append(("Using S&T-created TPE", current_apron_2))

    activated_level = max(
        [2 if limit == current_apron_2 else 1 for _, limit in activated_caps],
        default=0,
    )
    effective_level = max(existing_level, activated_level)
    effective_limit = hard_cap_limits_by_level.get(effective_level)
    if effective_limit and tax_after > effective_limit:
        flags.append(("block", "Effective hard cap", f"Post-trade tax total would be {format_money(tax_after)}, above the {format_money(effective_limit)} limit."))
    for label, limit in activated_caps:
        trigger_level = 2 if limit == current_apron_2 else 1
        if trigger_level > existing_level and (not effective_limit or tax_after <= effective_limit):
            flags.append(("watch", label, f"This creates a hard-cap trigger, but the post-trade tax total stays below {format_money(effective_limit)}."))

    if tax_before >= current_apron_2 and len(players_out) > 1 and incoming_salary > 0:
        flags.append(("block", "Second apron aggregation", "A team already above the second apron cannot aggregate multiple outgoing salaries in a trade."))
    if tax_after >= current_apron_2 and cash_value > 0:
        flags.append(("block", "Second apron cash", "A team above the second apron cannot send cash in a trade."))
    if not flags:
        flags.append(("clear", "Apron position", "No hard-cap or apron restriction is triggered by this proposal."))

    priority = {"block": 2, "watch": 1, "clear": 0}
    status = max((flag[0] for flag in flags), key=lambda item: priority[item])
    current_label = {
        "First Apron": f"Currently hard-capped at the First Apron ({format_money(current_apron_1)})",
        "Second Apron": f"Currently hard-capped at the Second Apron ({format_money(current_apron_2)})",
    }.get(existing_hard_cap, "Currently not hard-capped")
    if activated_caps:
        activated_text = "; ".join(
            f"{label} -> {'Second Apron' if limit == current_apron_2 else 'First Apron'} ({format_money(limit)})"
            for label, limit in activated_caps
        )
    else:
        activated_text = "No new hard cap is activated by this trade"
    if effective_level == 1:
        final_label = f"End result: hard-capped at the First Apron ({format_money(current_apron_1)})"
    elif effective_level == 2:
        final_label = f"End result: hard-capped at the Second Apron ({format_money(current_apron_2)})"
    else:
        final_label = "End result: no hard cap"
    if effective_limit and tax_after > effective_limit:
        final_label += f", but post-trade tax total is over it at {format_money(tax_after)}"
    elif effective_limit:
        final_label += f", with post-trade tax total at {format_money(tax_after)}"
    hard_cap_summary = f"{current_label}. Activated in this trade: {activated_text}. {final_label}."
    return {
        "status": status,
        "flags": flags,
        "current_hard_cap_label": current_label,
        "activated_hard_caps": activated_caps,
        "activated_hard_cap_label": activated_text,
        "effective_hard_cap_level": effective_level,
        "effective_hard_cap_limit": effective_limit,
        "effective_hard_cap_label": final_label,
        "hard_cap_summary": hard_cap_summary,
        "tax_before": tax_before,
        "tax_after": tax_after,
        "incoming_salary": incoming_salary,
        "outgoing_salary": outgoing_salary,
        "existing_hard_cap": existing_hard_cap,
    }


def render_trade_rule_card(title, status, message):
    render_html(f"""
        <section class="sbc-trade-rule-card sbc-trade-rule-{escape(status)}">
            <div class="sbc-trade-rule-status">{escape(status.upper())}</div>
            <div>
                <strong>{escape(title)}</strong>
                <span>{escape(message)}</span>
            </div>
        </section>
    """)


def render_trade_rule_checks(trade_team, selected_players_in, selected_players_out, selected_exception_out, cash_out, apron=None, stepien=None, incoming_salary_extra=0, outgoing_salary_extra=0, sign_trade_in_count=0):
    cap_type = trade_cap_type_after(selected_players_in, selected_players_out, trade_team, incoming_salary_extra, outgoing_salary_extra)
    hard_cap = team_hard_cap(base_cap, trade_team)
    apron = apron or trade_apron_review(trade_team, selected_players_in, selected_players_out, selected_exception_out, cash_out, incoming_salary_extra, outgoing_salary_extra)
    stepien = stepien or trade_stepien_review(dp, trade_team, [], [])
    try:
        cash_value = 0.0 if cash_out is None else float(cash_out)
    except (TypeError, ValueError):
        cash_value = 0.0
    if math.isnan(cash_value):
        cash_value = 0.0

    render_trade_rule_card("Stepien Rule", stepien["status"], stepien.get("message", "No Stepien summary available."))
    render_trade_rule_card("Apron / Hard Cap", apron["status"], apron.get("hard_cap_summary", "No apron summary available."))

    current_players = active_player_n(df, trade_team)
    current_type_col = "Type" + str(current_year)
    active_status = (df["Type"] == "Active Players") & ~df[current_type_col].isin(["Unrestricted", "Restricted", "Dead"])
    active_in = df[(df["Player"].isin(selected_players_in)) & active_status].shape[0]
    active_out = df[(df["Player"].isin(selected_players_out)) & active_status].shape[0]
    roster_after = current_players - active_out + active_in + int(sign_trade_in_count or 0)
    if roster_after > 17:
        render_trade_rule_card("Roster Limit", "block", f"Roster would reach {roster_after}. Cut at least {roster_after - 17} player(s) to comply.")
    elif roster_after >= 15:
        render_trade_rule_card("Roster Limit", "watch", f"Roster would reach {roster_after}. This is legal only with enough IR flexibility.")
    elif roster_after >= 12:
        render_trade_rule_card("Roster Limit", "clear", f"Roster would reach {roster_after}, inside the standard 12-14 player range.")
    else:
        render_trade_rule_card("Roster Limit", "watch", f"Roster would drop to {roster_after}. Add at least {12 - roster_after} player(s) to reach the minimum.")

    if cap_type == "Second" and cash_value > 0:
        render_trade_rule_card("Outgoing Cash", "block", "Teams above the Second Apron cannot send cash in a trade.")
    elif hard_cap in ["First Apron", "No Cap"] and cash_value > 0:
        render_trade_rule_card("Outgoing Cash", "watch", "Sending cash is allowed, but it hard caps the team at the Second Apron.")
    elif cash_value > 0:
        render_trade_rule_card("Outgoing Cash", "clear", "No cap-related cash restriction blocks this trade.")
    else:
        render_trade_rule_card("Outgoing Cash", "clear", "No outgoing cash included.")

    uses_st_tpe = any("S&T" in str(exc) for exc in selected_exception_out)
    if cap_type == "Second" and uses_st_tpe:
        render_trade_rule_card("S&T TPE", "block", "Teams above the Second Apron cannot acquire players via a sign-and-trade TPE.")
    elif hard_cap in ["First Apron", "No Cap"] and uses_st_tpe:
        render_trade_rule_card("S&T TPE", "watch", "Using a sign-and-trade TPE hard caps the team at the Second Apron.")
    elif uses_st_tpe:
        render_trade_rule_card("S&T TPE", "clear", "No cap restriction blocks this sign-and-trade TPE usage.")
    else:
        render_trade_rule_card("S&T TPE", "clear", "No sign-and-trade TPE is being used.")

    uses_bae_mle = any("Bi-Annual" in str(exc) or "Mid-Level" in str(exc) for exc in selected_exception_out)
    if cap_type in ["First", "Second"] and uses_bae_mle:
        render_trade_rule_card("BAE / MLE", "block", "Teams above the First Apron cannot trade for players via the BAE or MLE.")
    elif hard_cap == "No Cap" and uses_bae_mle:
        render_trade_rule_card("BAE / MLE", "watch", "Using the BAE or MLE hard caps the team at the First Apron.")
    elif uses_bae_mle:
        render_trade_rule_card("BAE / MLE", "clear", "No apron restriction blocks this BAE/MLE usage.")
    else:
        render_trade_rule_card("BAE / MLE", "clear", "No BAE or MLE is being used.")

    incoming_salary = current_year_salary_for_players(df, selected_players_in) + float(incoming_salary_extra or 0)
    outgoing_salary = current_year_salary_for_players(df, selected_players_out) + float(outgoing_salary_extra or 0)
    salary_match = trade_salary_matching_review(outgoing_salary, incoming_salary, apron.get("tax_before", 0))
    render_trade_rule_card("Salary Matching", salary_match["status"], f"{salary_match['label']}: {salary_match['detail']}")
    ratio = incoming_salary / outgoing_salary if outgoing_salary else 1000
    if cap_type in ["First", "Second"] and ratio > 1:
        render_trade_rule_card("100 Percent Rule", "block", "Teams above the First Apron cannot take back more than 100% of outgoing salary unless a minimum exception applies.")
    elif hard_cap == "No Cap" and ratio > 1:
        render_trade_rule_card("100 Percent Rule", "watch", "Taking back more than 100% is allowed, but hard caps the team at the First Apron.")
    elif ratio > 1:
        render_trade_rule_card("100 Percent Rule", "clear", "Taking back more than 100% is not blocked by apron rules.")
    else:
        render_trade_rule_card("100 Percent Rule", "clear", "Incoming salary is less than or equal to outgoing salary.")


def render_about_copy_card(title, body_html, accent="blue"):
    render_html(f"""
        <section class="sbc-about-copy-card sbc-about-feature-{accent}">
            <div class="sbc-about-copy-title">{escape(title)}</div>
            <div class="sbc-about-copy-body">{body_html}</div>
        </section>
    """)


def team_logo_name_mark(team, include_nickname=True, class_name="sbc-award-team-mark"):
    team = clean_pick_display(team)
    if team not in team_info:
        return f'<span class="{class_name} sbc-award-team-missing">{escape(str(team))}</span>'
    display = live_team_full_name(team) if include_nickname else str(team)
    logo = team_logo_for_name(team)
    color = team_color_for_name(team)
    secondary = team_secondary_for_name(team)
    return (
        f'<span class="{class_name}" style="--award-team-color:{escape(str(color), quote=True)};--award-team-secondary:{escape(str(secondary), quote=True)};">'
        f'<img src="{escape(str(logo), quote=True)}" alt="{escape(display, quote=True)} logo" referrerpolicy="no-referrer">'
        f'<strong>{escape(display)}</strong>'
        f'</span>'
    )


def render_team_name_stack(team):
    team = str(team)
    color = team_color_for_name(team)
    font = team_font_for_name(team)
    nickname = team_nickname_for_name(team)
    return (
        f'<div class="sbc-overview-team-name" '
        f'style="--overview-team-color:{escape(str(color), quote=True)};--overview-team-font:{escape(str(font), quote=True)};">'
        f'<strong>{escape(team)}</strong><em>{escape(str(nickname))}</em></div>'
    )


def render_overview_table(data):
    if data is None or data.empty:
        render_html('<div class="sbc-empty-state">No overview data is available.</div>')
        return
    table_df = data.copy()
    money_cols = ["Cap Space", "Tax Space", "Apron 1 Space", "Apron 2 Space", "Base Fee", "Luxury Fee", "Balance", "Amount Paid"]
    cents_cols = ["Base Fee", "Luxury Fee", "Balance", "Amount Paid"]
    visible_cols = ["Logo", "Team", "Active Players", "Hard Cap"] + money_cols
    visible_cols = [col for col in visible_cols if col in table_df.columns]
    rows = []
    for _, row in table_df.iterrows():
        cells = []
        hard_cap = str(row.get("Hard Cap", ""))
        for col in visible_cols:
            value = row.get(col, "")
            if col == "Logo":
                cells.append(f'<td class="sbc-overview-logo-cell"><img class="sbc-team-logo-img" src="{escape(str(value), quote=True)}" alt=""></td>')
            elif col in money_cols:
                numeric = 0
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    pass
                tone = "good" if numeric >= 0 else "bad"
                if col == "Amount Paid" and numeric == 0:
                    tone = "bad"
                important = (col == "Apron 1 Space" and hard_cap == "First Apron") or (col == "Apron 2 Space" and hard_cap == "Second Apron")
                formatted = f"${numeric:,.2f}" if col in cents_cols else format_money(value)
                important_class = " sbc-overview-important-money" if important else ""
                if col == "Luxury Fee" and row.get("Luxury Fee Type") == "Repeater":
                    cells.append(f'<td class="sbc-overview-money sbc-money-{tone}{important_class}"><span>{escape(str(formatted))}</span><em class="sbc-overview-fee-pill">Repeater</em></td>')
                else:
                    cells.append(f'<td class="sbc-overview-money sbc-money-{tone}{important_class}">{escape(str(formatted))}</td>')
            elif col == "Active Players":
                try:
                    active_n = int(float(value))
                except (TypeError, ValueError):
                    active_n = 0
                status = "danger" if active_n <= 11 or active_n >= 18 else "warn" if active_n <= 13 else "ok"
                cells.append(f'<td class="sbc-overview-center"><span class="sbc-overview-active sbc-overview-active-{status}">{escape(str(value))}</span></td>')
            elif col == "Hard Cap":
                cap_class = " sbc-overview-hardcap-alert" if hard_cap in ["First Apron", "Second Apron"] else ""
                flag = '<span class="sbc-hardcap-flag">!</span>' if cap_class else ""
                cells.append(f'<td class="sbc-overview-hardcap{cap_class}">{flag}{escape(str(value))}</td>')
            elif col == "Team":
                cells.append(f'<td>{render_team_name_stack(value)}</td>')
            else:
                cells.append(f'<td>{escape(str(value))}</td>')
        rows.append(f"<tr>{''.join(cells)}</tr>")
    header_labels = {
        "Logo": "",
        "Active Players": "Active",
        "Apron 1 Space": "A1 Space",
        "Apron 2 Space": "A2 Space",
    }
    headers = "".join(f"<th>{escape(str(header_labels.get(col, col)))}</th>" for col in visible_cols)
    render_html(f"""
        <div class="sbc-overview-table-wrap">
            <table class="sbc-overview-table">
                <thead><tr>{headers}</tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
        """)


def render_payout_cards(cards):
    card_html = []
    for label, value, note in cards:
        payout_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        payout_display = f"${payout_value:,.2f}" if not pd.isna(payout_value) else format_money(value)
        card_html.append(
            '<div class="sbc-payout-card">'
            f'<div class="sbc-payout-label">{escape(str(label))}</div>'
            f'<div class="sbc-payout-value">{escape(str(payout_display))}</div>'
            f'<div class="sbc-payout-note">{escape(str(note))}</div>'
            '</div>'
        )
    render_html(f'<div class="sbc-payout-grid">{"".join(card_html)}</div>')


def render_current_draft_table(data, title, icon, description):
    if data is None or data.empty:
        render_html(f"""
            <section class="sbc-draft-board sbc-current-draft-board">
                <div class="sbc-draft-board-head"><span>{icon}</span><div><strong>{escape(title)}</strong><em>{escape(description)}</em></div></div>
                <div class="sbc-pick-empty">No draft board data is available.</div>
            </section>
        """)
        return
    rows = []
    for _, row in data.iterrows():
        slot_team = clean_pick_display(row.get("Slot", ""))
        player_name = clean_draft_player(row.get("Player", ""))
        player_picture = row.get("Picture_Online", "")
        player_img = player_picture if not is_blank_value(player_picture) else DRAFT_SILHOUETTE
        player_label = player_name if player_name else f'{row.get("Time Due (ET)", "")} (ET)'
        player_class = "" if player_name else " sbc-draft-player-pending"
        row_color = team_color_for_name(slot_team) if slot_team in team_info else ""
        row_style = f' style="--draft-row-color:{escape(str(row_color), quote=True)};"' if row_color else ""
        rows.append(f"""
            <tr{row_style}>
                <td class="sbc-draft-pick-no"><span>{escape(str(row.get("Pick", "")))}</span></td>
                <td class="sbc-draft-team-cell sbc-draft-slot-cell">{render_draft_team_wordmark(slot_team, include_nickname=True)}</td>
                <td class="sbc-draft-player-cell{player_class}">
                    <img src="{escape(str(player_img), quote=True)}" alt="">
                    <strong>{escape(str(player_label))}</strong>
                </td>
            </tr>
        """)
    render_html(f"""
        <section class="sbc-draft-board sbc-current-draft-board">
            <div class="sbc-draft-board-head"><span>{icon}</span><div><strong>{escape(title)}</strong><em>{escape(description)}</em></div></div>
            <div class="sbc-draft-board-wrap">
                <table class="sbc-draft-board-table">
                    <thead><tr><th>Pick</th><th>Drafted By</th><th>Player</th></tr></thead>
                    <tbody>{''.join(rows)}</tbody>
                </table>
            </div>
        </section>
    """)


def clean_draft_player(value):
    if is_blank_value(value):
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    if text in ["-", "\u2014"]:
        return ""
    if re.fullmatch(r"\d{1,2}:\d{2}\s*[AP]M(?:\s*\(?ET\)?)?", text, flags=re.IGNORECASE):
        return ""
    return text


def current_draft_from_history(draft_history, round_name, pictures=None):
    expected = ["Pick", "Slot", "Team", "Player", "Picture_Online", "Time Due (ET)"]
    if draft_history is None or draft_history.empty or not {"Year", "Round", "Pick", "Team"}.issubset(draft_history.columns):
        return pd.DataFrame(columns=expected)
    history = draft_history.copy()
    history["_year_numeric"] = pd.to_numeric(history["Year"], errors="coerce")
    table = history[
        (history["_year_numeric"] == current_year)
        & (history["Round"].astype(str).str.strip() == str(round_name))
    ].copy()
    if table.empty:
        return pd.DataFrame(columns=expected)
    table["_pick_sort"] = pd.to_numeric(table["Pick"], errors="coerce")
    table = table.sort_values("_pick_sort", na_position="last").reset_index(drop=True)
    draft_times = ["10:30 AM", "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM", "1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM", "5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM", "8:00 PM", "8:30 PM", "9:00 PM", "9:30 PM", "10:00 PM", "10:30 PM", "11:00 PM", "11:30 PM", "12:00 AM", "12:30 AM", "1:00 AM"]
    if "Player" in table.columns:
        player_times = table["Player"].astype(str).str.extract(r"(\d{1,2}:\d{2}\s*[AP]M)", expand=False)
    else:
        player_times = pd.Series([None] * table.shape[0])
    table["Time Due (ET)"] = [
        re.sub(r"\s+", " ", str(player_times.iloc[idx]).upper()).strip()
        if idx < len(player_times) and pd.notna(player_times.iloc[idx])
        else draft_times[idx % len(draft_times)]
        for idx in range(table.shape[0])
    ]
    table["Player"] = table["Player"].apply(clean_draft_player) if "Player" in table.columns else ""
    if "Picture_Online" in table.columns:
        table = table.drop(columns=["Picture_Online"])
    if pictures is not None and not pictures.empty and {"Player", "Picture_Online"}.issubset(pictures.columns):
        picture_lookup = pictures[["Player", "Picture_Online"]].drop_duplicates("Player")
        table = table.merge(picture_lookup, how="left", on="Player")
    else:
        table["Picture_Online"] = ""
    table["Slot"] = table["Team"].astype(str).str.strip()
    table["Team"] = table["Slot"]
    return table[expected]


def draft_clock_picks(round_df, draft_date):
    if round_df is None or round_df.empty:
        return None, None, "Board not loaded"
    now_et = datetime.now(ZoneInfo("America/New_York"))
    clean_df = round_df.reset_index(drop=True).copy()
    if "Player" in clean_df.columns:
        drafted_mask = clean_df["Player"].apply(clean_draft_player).astype(bool)
        undrafted_df = clean_df[~drafted_mask].reset_index(drop=True)
        if undrafted_df.empty:
            return clean_df.iloc[-1], None, "Draft complete"
        return undrafted_df.iloc[0], undrafted_df.iloc[1] if undrafted_df.shape[0] > 1 else None, "On the clock"
    if now_et.date() < draft_date:
        on_clock = round_df.iloc[0]
        on_deck = round_df.iloc[1] if round_df.shape[0] > 1 else None
        return on_clock, on_deck, "On the clock"
    if now_et.date() > draft_date:
        return round_df.iloc[-1], None, "Draft day complete"
    active_idx = 0
    for idx, row in round_df.reset_index(drop=True).iterrows():
        try:
            pick_time = datetime.strptime(str(row.get("Time Due (ET)", "")), "%I:%M %p").time()
        except ValueError:
            continue
        if datetime.combine(draft_date, pick_time, ZoneInfo("America/New_York")) <= now_et:
            active_idx = idx
        else:
            break
    on_clock = clean_df.iloc[active_idx]
    on_deck = clean_df.iloc[active_idx + 1] if active_idx + 1 < clean_df.shape[0] else None
    return on_clock, on_deck, "On the clock"


def draft_countdown_text(target_dt, now_dt):
    delta = target_dt - now_dt
    total_seconds = max(0, int(delta.total_seconds()))
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def draft_target_iso(row, draft_date):
    if row is None:
        return ""
    try:
        target_time = datetime.strptime(str(row.get("Time Due (ET)", "")), "%I:%M %p").time()
    except ValueError:
        target_time = time(10, 30)
    return datetime.combine(draft_date, target_time, ZoneInfo("America/New_York")).isoformat()


def retired_render_draft_clock_card(row, label, draft_date):
    if row is None:
        return """
            <div class="sbc-live-draft-card">
                <div class="sbc-live-draft-empty">No next pick</div>
            </div>
        """
    slot_team = clean_pick_display(row.get("Slot", ""))
    team_label = live_team_full_name(slot_team)
    team_logo = team_logo_for_name(slot_team)
    primary = team_color_for_name(slot_team) if slot_team in team_info else LEAGUE_PRIMARY
    secondary = team_secondary_for_name(slot_team) if slot_team in team_info else LEAGUE_SECONDARY
    logo_html = f'<img src="{escape(str(team_logo), quote=True)}" alt="{escape(str(team_label), quote=True)} logo">' if team_logo else ""
    return f"""
        <div class="sbc-live-draft-card" style="--clock-team-color:{escape(str(primary), quote=True)};--clock-team-secondary:{escape(str(secondary), quote=True)};">
            <div class="sbc-live-draft-pick-circle">{escape(str(row.get("Pick", "--")))}</div>
            <div class="sbc-live-draft-logo">{logo_html}</div>
            <div class="sbc-live-draft-card-copy">
                <span>{escape(label)}</span>
                <strong>{escape(team_label)}</strong>
                <em class="sbc-countdown" data-target="{escape(draft_target_iso(row, draft_date), quote=True)}">Calculating...</em>
            </div>
        </div>
    """


def retired_render_live_draft_room_header(round_1_df, round_2_df):
    # Retired after the 2026 draft. Keep the hook for next year's reactivation.
    return None


def render_draft_history_table(data, title, description):
    if data is None or data.empty:
        render_html(f"""
            <section class="sbc-draft-board sbc-history-draft-board">
                <div class="sbc-draft-board-head"><span>✓</span><div><strong>{escape(title)}</strong><em>{escape(description)}</em></div></div>
                <div class="sbc-pick-empty">No draft history is available.</div>
            </section>
        """)
        return
    rows = []
    for _, row in data.iterrows():
        drafted_team = clean_pick_display(row.get("Drafted Team Name", ""))
        row_color = team_color_for_name(drafted_team) if drafted_team in team_info else ""
        row_style = f' style="--draft-row-color:{escape(str(row_color), quote=True)};"' if row_color else ""
        rows.append(f"""
            <tr{row_style}>
                <td class="sbc-draft-pick-no"><span>{escape(str(row.get("Pick", "")))}</span></td>
                <td class="sbc-draft-team-cell">{render_draft_team_wordmark(drafted_team)}</td>
                <td class="sbc-draft-player-cell">
                    <img src="{escape(str(row.get("Picture_Online", "")), quote=True)}" alt="">
                    <strong>{escape(str(row.get("Player", "")))}</strong>
                </td>
                <td class="sbc-draft-team-cell">{render_draft_team_wordmark(row.get("Current Team Name", ""))}</td>
            </tr>
        """)
    render_html(f"""
        <section class="sbc-draft-board sbc-history-draft-board">
            <div class="sbc-draft-board-head"><span>✓</span><div><strong>{escape(title)}</strong><em>{escape(description)}</em></div></div>
            <div class="sbc-draft-board-wrap">
                <table class="sbc-draft-board-table">
                    <thead><tr><th>Pick</th><th>Drafted By</th><th>Player</th><th>Current Team</th></tr></thead>
                    <tbody>{''.join(rows)}</tbody>
                </table>
            </div>
        </section>
    """)


def clean_pick_display(value):
    if is_blank_value(value):
        return "—"
    text = str(value).strip()
    return "—" if text.lower() in ["false", "nan", "none", "nat"] else text


def clean_pick_round(value):
    text = clean_pick_display(value)
    match = re.search(r"\d+", str(text))
    return match.group(0) if match else text


def pick_round_rank(value):
    text = clean_pick_round(value)
    try:
        return int(text)
    except (TypeError, ValueError):
        return 99


LIVE_STATS = [
    ("GP", "Games Played", "0 pts"),
    ("MP", "Minutes", "11 pts"),
    ("TS%", "TS %", "41 pts"),
    ("2PT%", "2PT Percentage", "31 pts"),
    ("2PTM/2PTA", "2PM / 2PA", "0 pts"),
    ("3PT%", "3PT Percentage", "31 pts"),
    ("3PTM/3PTA", "3PM / 3PA", "0 pts"),
    ("FT%", "Free Throw Percentage", "21 pts"),
    ("FTM/FTA", "FTM / FTA", "0 pts"),
    ("PTS", "Points", "61 pts"),
    ("OREB", "Off. Rebounds", "31 pts"),
    ("DREB", "Def. Rebounds", "31 pts"),
    ("AST", "Assists", "41 pts"),
    ("ST", "Steals", "31 pts"),
    ("BLK", "Blocks", "31 pts"),
    ("+/-", "Plus / Minus", "31 pts"),
    ("TO", "Turnovers", "21 pts, lower wins"),
]

LIVE_PAIRED_STATS = {
    "2PTM/2PTA": ("2PTM", "2PTA"),
    "3PTM/3PTA": ("3PTM", "3PTA"),
    "FTM/FTA": ("FTM", "FTA"),
}


def live_stat_points(points_text):
    match = re.search(r"\d+", points_text)
    return int(match.group(0)) if match else 0


def live_team_full_name(team):
    info = team_info.get(team, {})
    nickname_value = info.get("nickname", "")
    return f"{team} {nickname_value}".strip()


def live_chart_color(team, fallback):
    return team_info.get(team, {}).get("bg", fallback)


def first_round_control_years():
    return list(range(current_year, current_year + 7))


def first_round_control_status(draft_picks, team, year):
    if draft_picks is None or draft_picks.empty:
        return "none", "No first-round pick listed."
    required = {"Year", "Round", "CurrentTeam"}
    if not required.issubset(draft_picks.columns):
        return "none", "Draft-pick data is missing required columns."
    work = draft_picks.copy()
    work["_year"] = pd.to_numeric(work["Year"], errors="coerce").floordiv(1).astype("Int64")
    work = work[
        (work["_year"] == int(year))
        & work["Round"].apply(trade_pick_is_first)
        & work["CurrentTeam"].apply(lambda value: team_list_contains(value, team))
    ].copy()
    if work.empty:
        return "none", "No first-round pick listed."
    full = work[work["FullyOwned"].apply(trade_truthy)] if "FullyOwned" in work.columns else pd.DataFrame()
    if not full.empty:
        clean_full = full[~full["PickSwap"].apply(trade_truthy)] if "PickSwap" in full.columns else full
        if not clean_full.empty:
            slots = ", ".join(clean_pick_display(value) for value in clean_full["OGTeam"].dropna().unique())
            return "full", f"Full first-round pick: {slots}."
        slots = ", ".join(clean_pick_display(value) for value in full["OGTeam"].dropna().unique())
        return "swap-full", f"Full first-round coverage through swap language: {slots}."
    locked = work[work["Locked"].apply(trade_truthy)] if "Locked" in work.columns else pd.DataFrame()
    if not locked.empty:
        clean_locked = locked[~locked["PickSwap"].apply(trade_truthy)] if "PickSwap" in locked.columns else locked
        if not clean_locked.empty:
            slots = ", ".join(clean_pick_display(value) for value in clean_locked["OGTeam"].dropna().unique())
            return "full", f"Locked but no-doubt first-round pick: {slots}."
        slots = ", ".join(clean_pick_display(value) for value in locked["OGTeam"].dropna().unique())
        return "swap-full", f"Locked but full first-round coverage through swap language: {slots}."
    split = work[~work["FullyOwned"].apply(trade_truthy)] if "FullyOwned" in work.columns else work
    if not split.empty:
        slots = ", ".join(clean_pick_display(value) for value in split["OGTeam"].dropna().unique())
        return "split", f"Split/shared first-round rights: {slots}."
    return "none", "No first-round pick listed."


def render_first_round_control_grid(draft_picks, teams, title, description, compact=False):
    years = first_round_control_years()
    header_years = "".join(f"<th>{year}</th>" for year in years)
    rows = []
    for team in teams:
        logo = team_logo_for_name(team)
        team_cell = (
            f'<td class="sbc-first-team">'
            f'<img src="{escape(str(logo), quote=True)}" alt="{escape(live_team_full_name(team), quote=True)} logo" referrerpolicy="no-referrer">'
            f'<span>{escape(team_abbrev_for_name(team))}</span>'
            f'</td>'
        )
        cells = []
        for year in years:
            status, detail = first_round_control_status(draft_picks, team, year)
            label = {"full": "FULL", "swap-full": "SWAP", "split": "SPLIT", "none": "NO"}[status]
            cells.append(
                f'<td class="sbc-first-cell sbc-first-{status}" title="{escape(detail, quote=True)}">'
                f'<span>{escape(label)}</span>'
                f'</td>'
            )
        rows.append(f"<tr>{team_cell}{''.join(cells)}</tr>")
    compact_class = " sbc-first-grid-compact" if compact else ""
    render_html(f"""
        <style>
            .sbc-first-grid-card {{
                overflow: hidden;
                margin: 0.65rem 0 1rem;
                border: 1px solid color-mix(in srgb, {LEAGUE_PRIMARY} 22%, rgba(23, 32, 42, 0.12));
                border-top: 4px solid {LEAGUE_SECONDARY};
                border-radius: 8px;
                background: #ffffff;
                box-shadow: 0 14px 34px rgba(18, 25, 38, 0.07);
            }}
            .sbc-first-grid-head {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                padding: 0.72rem 0.85rem;
                background: linear-gradient(90deg, color-mix(in srgb, {LEAGUE_PRIMARY} 10%, #ffffff), color-mix(in srgb, {LEAGUE_SECONDARY} 12%, #ffffff));
                border-bottom: 1px solid rgba(23, 32, 42, 0.08);
            }}
            .sbc-first-grid-head strong,
            .sbc-first-grid-head span {{
                display: block;
            }}
            .sbc-first-grid-head strong {{
                color: var(--sbc-ink);
                font-size: 0.98rem;
                font-weight: 950;
                line-height: 1.08;
            }}
            .sbc-first-grid-head span {{
                color: var(--sbc-muted);
                font-size: 0.78rem;
                font-weight: 800;
            }}
            .sbc-first-legend {{
                display: flex;
                flex-wrap: wrap;
                justify-content: flex-end;
                gap: 0.42rem 0.58rem;
                color: var(--sbc-muted);
                font-size: 0.7rem;
                font-weight: 900;
                text-transform: uppercase;
                white-space: nowrap;
            }}
            .sbc-first-legend i {{
                width: 0.8rem;
                height: 0.8rem;
                border-radius: 999px;
                box-shadow: inset 0 0 0 1px rgba(255,255,255,0.48);
            }}
            .sbc-first-table-wrap {{
                overflow-x: auto;
            }}
            .sbc-first-table {{
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
            }}
            .sbc-first-table th {{
                background: #f8fafc;
                border-bottom: 1px solid rgba(23, 32, 42, 0.08);
                color: var(--sbc-muted);
                font-size: 0.72rem;
                font-weight: 950;
                padding: 0.44rem 0.38rem;
                text-align: center;
            }}
            .sbc-first-table th:first-child {{
                width: 5.2rem;
                text-align: left;
                padding-left: 0.72rem;
            }}
            .sbc-first-table td {{
                border-bottom: 1px solid rgba(23, 32, 42, 0.055);
                padding: 0.34rem;
                text-align: center;
            }}
            .sbc-first-table tr:last-child td {{
                border-bottom: none;
            }}
            .sbc-first-team {{
                display: flex;
                align-items: center;
                gap: 0.42rem;
                padding-left: 0.68rem !important;
                text-align: left !important;
            }}
            .sbc-first-team img {{
                width: 1.65rem;
                height: 1.65rem;
                object-fit: contain;
            }}
            .sbc-first-team span {{
                color: var(--sbc-ink);
                font-size: 0.72rem;
                font-weight: 950;
            }}
            .sbc-first-cell span {{
                display: inline-grid;
                place-items: center;
                width: 100%;
                min-height: 1.85rem;
                border-radius: 7px;
                color: #ffffff;
                font-size: 0.66rem;
                font-weight: 950;
                letter-spacing: 0.02em;
                box-shadow: inset 0 0 0 1px rgba(255,255,255,0.18);
            }}
            .sbc-first-full span,
            .sbc-first-legend .sbc-first-full {{
                background: #166534;
            }}
            .sbc-first-swap-full span,
            .sbc-first-legend .sbc-first-swap-full {{
                background: #65a30d;
            }}
            .sbc-first-split span,
            .sbc-first-legend .sbc-first-split {{
                background: #c99720;
            }}
            .sbc-first-none span,
            .sbc-first-legend .sbc-first-none {{
                background: #b91c1c;
            }}
            .sbc-first-grid-compact .sbc-first-table th:first-child {{
                width: 5.4rem;
            }}
            .sbc-first-grid-compact .sbc-first-table td {{
                padding: 0.42rem;
            }}
        </style>
        <section class="sbc-first-grid-card{compact_class}">
            <div class="sbc-first-grid-head">
                <div>
                    <strong>{escape(title)}</strong>
                    <span>{escape(description)}</span>
                </div>
                <div class="sbc-first-legend">
                    <i class="sbc-first-full"></i><span>Full</span>
                    <i class="sbc-first-swap-full"></i><span>Swap full</span>
                    <i class="sbc-first-split"></i><span>Split</span>
                    <i class="sbc-first-none"></i><span>No</span>
                </div>
            </div>
            <div class="sbc-first-table-wrap">
                <table class="sbc-first-table">
                    <thead><tr><th>Team</th>{header_years}</tr></thead>
                    <tbody>{''.join(rows)}</tbody>
                </table>
            </div>
        </section>
    """)


def render_league_first_round_control_matrix(draft_picks):
    years = first_round_control_years()

    def conference_panel(conf):
        teams = [team for team in Teams if team_info.get(team, {}).get("conf") == conf]
        year_cells = "".join(f"<span>{str(year)[-2:]}</span>" for year in years)
        rows = []
        for team in teams:
            logo = team_logo_for_name(team)
            cells = []
            for year in years:
                status, detail = first_round_control_status(draft_picks, team, year)
                cells.append(
                    f'<i class="sbc-first-mini-cell sbc-first-{status}" title="{escape(live_team_full_name(team), quote=True)} {year}: {escape(detail, quote=True)}"></i>'
                )
            rows.append(f"""
                <div class="sbc-first-mini-row">
                    <img src="{escape(str(logo), quote=True)}" alt="{escape(live_team_full_name(team), quote=True)} logo" referrerpolicy="no-referrer">
                    {''.join(cells)}
                </div>
            """)
        return f"""
            <section class="sbc-first-mini-panel sbc-first-mini-{escape(conf.lower())}">
                <div class="sbc-first-mini-title">{escape(conf)}</div>
                <div class="sbc-first-mini-years"><span></span>{year_cells}</div>
                <div class="sbc-first-mini-rows">{''.join(rows)}</div>
            </section>
        """

    render_html(f"""
        <style>
            .sbc-first-mini-board {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.75rem;
                margin: 0.75rem 0 1rem;
            }}
            .sbc-first-mini-panel {{
                border-radius: 8px;
                border: 1px solid rgba(23, 32, 42, 0.12);
                background: #ffffff;
                box-shadow: 0 10px 24px rgba(18, 25, 38, 0.055);
                padding: 0.55rem;
            }}
            .sbc-first-mini-west {{
                border-top: 4px solid {LEAGUE_SECONDARY};
            }}
            .sbc-first-mini-east {{
                border-top: 4px solid {LEAGUE_PRIMARY};
            }}
            .sbc-first-mini-title {{
                color: var(--sbc-ink);
                font-size: 0.76rem;
                font-weight: 950;
                letter-spacing: 0.06em;
                margin-bottom: 0.35rem;
                text-transform: uppercase;
            }}
            .sbc-first-mini-years,
            .sbc-first-mini-row {{
                display: grid;
                grid-template-columns: 1.45rem repeat(7, minmax(0, 1fr));
                align-items: center;
                gap: 0.22rem;
            }}
            .sbc-first-mini-years {{
                margin-bottom: 0.24rem;
            }}
            .sbc-first-mini-years span {{
                color: var(--sbc-muted);
                font-size: 0.58rem;
                font-weight: 950;
                text-align: center;
            }}
            .sbc-first-mini-rows {{
                display: grid;
                gap: 0.22rem;
            }}
            .sbc-first-mini-row img {{
                width: 1.18rem;
                height: 1.18rem;
                object-fit: contain;
                justify-self: center;
            }}
            .sbc-first-mini-cell {{
                display: block;
                width: 100%;
                aspect-ratio: 1 / 1;
                border-radius: 4px;
                box-shadow: inset 0 0 0 1px rgba(255,255,255,0.24);
            }}
            .sbc-first-mini-cell.sbc-first-full {{ background: #166534; }}
            .sbc-first-mini-cell.sbc-first-swap-full {{ background: #65a30d; }}
            .sbc-first-mini-cell.sbc-first-split {{ background: #c99720; }}
            .sbc-first-mini-cell.sbc-first-none {{ background: #b91c1c; }}
            .sbc-first-mini-legend {{
                display: flex;
                justify-content: flex-end;
                gap: 0.28rem;
                margin-top: 0.45rem;
            }}
            .sbc-first-mini-legend i {{
                width: 0.78rem;
                height: 0.78rem;
                border-radius: 4px;
            }}
            @media (max-width: 850px) {{
                .sbc-first-mini-board {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
        <div class="sbc-section-label">First-Round Control Matrix</div>
        <div class="sbc-first-mini-board">
            {conference_panel("West")}
            {conference_panel("East")}
        </div>
        <div class="sbc-first-mini-legend" title="Dark green: full. Light green: swap full. Yellow: split/shared. Red: no listed first.">
            <i class="sbc-first-mini-cell sbc-first-full"></i>
            <i class="sbc-first-mini-cell sbc-first-swap-full"></i>
            <i class="sbc-first-mini-cell sbc-first-split"></i>
            <i class="sbc-first-mini-cell sbc-first-none"></i>
        </div>
    """)


def render_pick_table(data, title, icon, description, empty_text, columns=None, image_columns=None, status="hold"):
    image_columns = set(image_columns or [])
    if data is None or data.shape[0] == 0:
        render_html(f"""
            <section class="sbc-pick-panel sbc-pick-panel-{status}">
                <div class="sbc-pick-panel-head">
                    <div class="sbc-pick-icon">{icon}</div>
                    <div>
                        <div class="sbc-pick-title">{escape(title)}</div>
                        <div class="sbc-pick-copy">{escape(description)}</div>
                    </div>
                    <div class="sbc-pick-count">0</div>
                </div>
                <div class="sbc-pick-empty">{escape(empty_text)}</div>
            </section>
            """)
        return

    table_df = data.copy()
    if columns is None:
        visible_columns = list(table_df.columns)
    else:
        visible_columns = [c for c in columns if c in table_df.columns]
    group_by_year = "Year" in visible_columns
    table_columns = [c for c in visible_columns if c != "Year"]

    if group_by_year:
        table_df["_sbc_round_rank"] = table_df["Round"].apply(pick_round_rank) if "Round" in table_df.columns else 99
        table_df = table_df.sort_values(["Year", "_sbc_round_rank"]).drop(columns=["_sbc_round_rank"])

    header_cells = []
    for col in table_columns:
        label = {
            "OGTeam": "Slot",
            "CurrentTeam": "Owner",
            "Contacted": "Contacted",
            "Explanation": "Details",
        }.get(col, col)
        classes = []
        if col in image_columns:
            classes.append("sbc-pick-logo-col")
        if col == "Round":
            classes.append("sbc-pick-round-col")
        if col in ["Contacted", "Potential Owners"]:
            classes.append("sbc-pick-contact-col")
        if col == "Explanation":
            classes.append("sbc-pick-detail-col")
        class_attr = f' class="{" ".join(classes)}"' if classes else ""
        header_cells.append(f"<th{class_attr}>{escape(str(label))}</th>")

    body_rows = []
    current_group_year = None
    for _, row in table_df.iterrows():
        if group_by_year:
            row_year = clean_pick_display(row.get("Year", ""))
            if row_year != current_group_year:
                current_group_year = row_year
                body_rows.append(f'<tr class="sbc-pick-year-row"><td colspan="{len(table_columns)}"><span>{escape(str(row_year))}</span></td></tr>')
        cells = []
        for col in table_columns:
            raw_value = row.get(col, "")
            value = "" if is_blank_value(raw_value) else raw_value
            cell_classes = []
            if col in image_columns and str(value).strip():
                value_html = render_team_logo_chip_from_url(value)
                cell_classes.extend(["sbc-pick-logo-cell", "sbc-pick-logo-col"])
            elif col == "OGTeam":
                value_html = render_slot_team(value)
                cell_classes.append("sbc-pick-slot-cell")
            elif col in ["Contacted", "Potential Owners"]:
                value_html = render_team_logo_cluster(value)
                cell_classes.append("sbc-pick-contact-cell")
            else:
                display = clean_pick_display(value)
                value_html = escape(str(display))
                if col == "Explanation":
                    cell_classes.append("sbc-pick-detail-cell")
                if col == "Year":
                    cell_classes.append("sbc-pick-year-cell")
                if col == "Round":
                    value_html = f'<span class="sbc-round-badge">{escape(str(clean_pick_round(value)))}</span>'
                    cell_classes.append("sbc-pick-round-cell")
            class_attr = f' class="{" ".join(cell_classes)}"' if cell_classes else ""
            cells.append(f"<td{class_attr}>{value_html}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    render_html(f"""
        <section class="sbc-pick-panel sbc-pick-panel-{status}">
            <div class="sbc-pick-panel-head">
                <div class="sbc-pick-icon">{icon}</div>
                <div>
                    <div class="sbc-pick-title">{escape(title)}</div>
                    <div class="sbc-pick-copy">{escape(description)}</div>
                </div>
                <div class="sbc-pick-count">{table_df.shape[0]}</div>
            </div>
            <div class="sbc-pick-table-wrap">
                <table class="sbc-pick-table">
                    <thead><tr>{''.join(header_cells)}</tr></thead>
                    <tbody>{''.join(body_rows)}</tbody>
                </table>
            </div>
        </section>
        """)

def live_stat_value(row, stat):
    if stat in LIVE_PAIRED_STATS:
        made_col, attempt_col = LIVE_PAIRED_STATS[stat]
        made_value = row.get(made_col, "")
        attempt_value = row.get(attempt_col, "")
        if is_blank_value(made_value) and is_blank_value(attempt_value):
            return "-"
        try:
            made_text = "-" if is_blank_value(made_value) else f"{float(made_value):.0f}"
            attempt_text = "-" if is_blank_value(attempt_value) else f"{float(attempt_value):.0f}"
            return f"{made_text} / {attempt_text}"
        except (TypeError, ValueError):
            return f"{made_value} / {attempt_value}"

    value = row.get(stat, "")
    if is_blank_value(value):
        return "—"
    try:
        if stat in ["TS%", "2PT%", "3PT%", "FT%"]:
            return f"{float(value) * 100:.2f}%"
        if stat == "MP":
            minutes = float(value)
            mins = int(minutes)
            secs = int((minutes - mins) * 60)
            return f"{mins}:{secs:02d}"
        if stat == "+/-":
            return f"{float(value):+.1f}"
        return f"{float(value):.0f}"
    except (TypeError, ValueError):
        return str(value)


def live_stat_score(values, stat):
    if len(values) <= 1:
        return ["neutral"] * len(values)
    parsed = []
    for value in values:
        if stat == "MP" and isinstance(value, str) and ":" in value:
            mins, secs = value.split(":", 1)
            parsed.append(float(mins) + float(secs) / 60)
        else:
            parsed.append(float(str(value).replace("%", "")))
    if stat == "TO":
        best = min(parsed)
    else:
        best = max(parsed)
    winners = sum(1 for val in parsed if val == best)
    return [("tie" if winners > 1 and val == best else "win" if val == best else "trail") for val in parsed]


def live_rank_label(live_df, team, stat):
    try:
        if stat not in live_df.columns:
            return ""
        ascending = stat == "TO"
        ranks = live_df[stat].rank(ascending=ascending, method="min")
        team_index = live_df.index[live_df["Team"] == team]
        if len(team_index) == 0:
            return ""
        rank_val = int(ranks.loc[team_index[0]])
        is_tied = (ranks == rank_val).sum() > 1
        if 11 <= rank_val % 100 <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(rank_val % 10, "th")
        prefix = "T-" if is_tied else ""
        return f"{prefix}{rank_val}{suffix}"
    except (TypeError, ValueError):
        return ""


def live_row_payload(live_df, team):
    row = live_df[live_df["Team"] == team]
    if row.shape[0] == 0:
        return None
    rank_stats = [stat for stat, _, _ in LIVE_STATS]
    for made_col, attempt_col in LIVE_PAIRED_STATS.values():
        rank_stats.extend([made_col, attempt_col])
    return {
        "team": team,
        "data": row.iloc[0],
        "ranks": {stat: live_rank_label(live_df, team, stat) for stat in dict.fromkeys(rank_stats)},
    }


def render_live_stat_board(title, kicker, rows, selected_team, tie_winner_team=None):
    if not rows:
        render_html('<div class="sbc-empty-state">No live stats are available for this selection.</div>')
        return

    team_headers = []
    for row in rows:
        logo = team_info.get(row["team"], {}).get("logo", "")
        logo_html = f'<img class="sbc-live-logo" src="{escape(str(logo), quote=True)}" alt="{escape(str(row["team"]), quote=True)} logo">' if logo else ""
        team_headers.append(f'<div class="sbc-live-team-head">{logo_html}<span>{escape(live_team_full_name(row["team"]))}</span></div>')

    stat_rows = []
    totals = [0] * len(rows)
    for stat, label, points in LIVE_STATS:
        displays = [live_stat_value(row["data"], stat) for row in rows]
        subtexts = []
        for row in rows:
            if stat in LIVE_PAIRED_STATS:
                made_col, attempt_col = LIVE_PAIRED_STATS[stat]
                made_rank = row.get("ranks", {}).get(made_col, "")
                attempt_rank = row.get("ranks", {}).get(attempt_col, "")
                subtexts.append(f"{made_rank} / {attempt_rank}".strip(" /"))
            else:
                subtexts.append(row.get("ranks", {}).get(stat, ""))
        try:
            states = live_stat_score(displays, stat)
        except (TypeError, ValueError):
            states = ["neutral"] * len(displays)
        point_value = live_stat_points(points)
        if point_value == 0:
            states = ["neutral"] * len(displays)
        elif tie_winner_team and "tie" in states:
            states = [
                "win" if state == "tie" and row.get("team") == tie_winner_team else "trail" if state == "tie" else state
                for state, row in zip(states, rows)
            ]
        point_winners = [idx for idx, state in enumerate(states) if state in ["win", "tie"]]
        split_value = point_value / len(point_winners) if point_winners else 0
        for idx in point_winners:
            if len(rows) > 1:
                totals[idx] += split_value
        value_cells = "".join(
            f'<div class="sbc-live-stat-value sbc-live-stat-{state}"><span>{escape(str(display))}</span><em>{escape(str(subtext))}</em></div>'
            for display, state, subtext in zip(displays, states, subtexts))
        stat_rows.append(
            dedent(f"""
            <div class="sbc-live-stat-row">
                <div class="sbc-live-stat-name">
                    <span>{escape(label)}</span>
                    <em>{escape(points)}</em>
                </div>
                {value_cells}
            </div>
            """))

    total_row = ""
    if len(rows) > 1:
        max_total = max(totals)
        total_leaders = [total == max_total for total in totals]
        if tie_winner_team and sum(total_leaders) > 1:
            total_leaders = [row.get("team") == tie_winner_team for row in rows]
        has_single_winner = sum(total_leaders) == 1
        total_cells = []
        for total, is_leader, row in zip(totals, total_leaders, rows):
            classes = "sbc-live-total-value"
            label = ""
            team_total_info = team_info.get(row["team"], {})
            total_bg = team_total_info.get("bg", bg_color)
            total_text = team_total_info.get("text", "#ffffff")
            total_secondary = team_total_info.get("bg2", total_text)
            style = (
                f' style="background:{escape(str(total_bg), quote=True)};'
                f' color:{escape(str(total_text), quote=True)};'
                f' box-shadow:inset 0 0 0 2px {escape(str(total_secondary), quote=True)};"')
            if is_leader and has_single_winner:
                classes += " sbc-live-total-leader"
                label = "Winner"
            elif is_leader:
                classes += " sbc-live-total-tie"
                label = "Tied"
            total_cells.append(f'<div class="{classes}"{style}><span>{total:g}</span><em>{label}</em></div>')
        total_cells = "".join(total_cells)
        total_row = dedent(f"""
        <div class="sbc-live-stat-row">
            <div class="sbc-live-total-name">
                <span>Total Score</span>
                <em>category points won</em>
            </div>
            {total_cells}
        </div>
        """)

    render_html(f"""
        <section class="sbc-live-board">
            <div class="sbc-live-board-head">
                <div>
                    <div class="sbc-live-card-kicker">{escape(kicker)}</div>
                    <div class="sbc-live-card-title">{escape(title)}</div>
                </div>
            </div>
            <div class="sbc-live-board-grid" style="--sbc-live-team-cols: {len(rows)};">
                <div class="sbc-live-team-spacer"></div>
                {''.join(team_headers)}
                {''.join(stat_rows)}
                {total_row}
            </div>
        </section>
        """)


def build_live_line_chart(data, selected_team, selected_category, selected_year, selected_period, opponents, team_color, accent_color):
    if data is None or data.shape[0] == 0:
        return None

    df_year = data[(data["Year"] == selected_year) & (data["MP"] != 0)].copy()
    if df_year.shape[0] == 0 or selected_category not in df_year.columns:
        return None

    opponents = [opponent for opponent in opponents if opponent != selected_team]
    league_median = (
        df_year.groupby("Period", as_index=False)[selected_category]
        .median()
        .assign(Series="League Median"))
    team_series = (
        df_year[df_year["Team"] == selected_team]
        .loc[:, ["Period", selected_category]]
        .assign(Series=selected_team))
    opponent_series = (
        df_year[df_year["Team"].isin(opponents)]
        .loc[:, ["Period", "Team", selected_category]]
        .rename(columns={"Team": "Series"}))
    plot_df = pd.concat([league_median, opponent_series, team_series], ignore_index=True)
    period_sort = sorted(pd.to_numeric(plot_df["Period"], errors="coerce").dropna().astype(int).unique().tolist())
    period_label_lookup = {period_value: period_date_label(selected_year, period_value, f"P{period_value}") for period_value in period_sort}
    plot_df["PeriodLabel"] = pd.to_numeric(plot_df["Period"], errors="coerce").astype("Int64").map(period_label_lookup).fillna(plot_df["Period"].astype(str))
    if selected_category in ["TS%", "2PT%", "3PT%", "FT%"]:
        plot_df["PlotValue"] = plot_df[selected_category] * 100
        value_format = ".1f"
    else:
        plot_df["PlotValue"] = plot_df[selected_category]
        value_format = ".2f"
    team_points = plot_df[plot_df["Series"] == selected_team].copy()
    plot_df["PeriodNumber"] = pd.to_numeric(plot_df["Period"], errors="coerce")
    selected_period_df = pd.DataFrame({"PeriodNumber": [selected_period]})
    color_domain = ["League Median"] + opponents + [selected_team]
    color_range = ["#9ca3af"] + [live_chart_color(opponent, "#a3aab5") for opponent in opponents] + [team_color]

    base = alt.Chart(plot_df).encode(
        x=alt.X(
            "PeriodNumber:Q",
            title="Period",
            scale=alt.Scale(domain=[min(period_sort), max(period_sort)]),
            axis=alt.Axis(labelAngle=0, labelFontSize=11, titleFontSize=12, titlePadding=10, grid=False)),
        y=alt.Y(
            "PlotValue:Q",
            title=selected_category,
            scale=alt.Scale(zero=False),
            axis=alt.Axis(labelFontSize=11, titleFontSize=12, titlePadding=10, gridOpacity=0.24)),
        tooltip=[
            alt.Tooltip("Series:N", title="Series"),
            alt.Tooltip("PeriodLabel:O", title="Window"),
            alt.Tooltip("PlotValue:Q", title=selected_category, format=value_format)])

    selected_band = (
        alt.Chart(selected_period_df)
        .mark_rect(color=team_color, opacity=0.10)
        .encode(x=alt.X("PeriodNumber:Q", title=None)))
    median_line = (
        base.transform_filter(alt.datum.Series == "League Median")
        .mark_line(strokeWidth=2.5, strokeDash=[5, 4], color="#7c8794", interpolate="monotone"))
    opponent_lines = (
        base.transform_filter((alt.datum.Series != "League Median") & (alt.datum.Series != selected_team))
        .mark_line(strokeWidth=2.4, opacity=0.62, interpolate="monotone")
        .encode(color=alt.Color("Series:N", scale=alt.Scale(domain=color_domain, range=color_range), legend=alt.Legend(title=None, orient="top"))))
    team_line = (
        base.transform_filter(alt.datum.Series == selected_team)
        .mark_line(strokeWidth=4, color=team_color, interpolate="monotone"))
    all_points = (
        base.mark_circle(size=58, stroke="#ffffff", strokeWidth=1.2, opacity=0.95)
        .encode(
            color=alt.Color("Series:N", scale=alt.Scale(domain=color_domain, range=color_range), legend=None),
            size=alt.condition(alt.datum.PeriodNumber == selected_period, alt.value(150), alt.value(54)),
            strokeWidth=alt.condition(alt.datum.PeriodNumber == selected_period, alt.value(2.4), alt.value(1.2))))
    points = (
        alt.Chart(team_points)
        .mark_circle(size=115, stroke="#ffffff", strokeWidth=1.8)
        .encode(
            x=alt.X("PeriodNumber:Q", title="Period", scale=alt.Scale(domain=[min(period_sort), max(period_sort)])),
            y="PlotValue:Q",
            color=alt.value(team_color),
            tooltip=[
                alt.Tooltip("PeriodLabel:O", title="Window"),
                alt.Tooltip("PlotValue:Q", title=selected_category, format=value_format)]))
    return (
        (selected_band + median_line + opponent_lines + team_line + all_points + points)
        .properties(height=340, width="container")
        .properties(background="#ffffff")
        .configure_view(strokeWidth=0)
        .configure_axis(domainColor="#dbe2ea", tickColor="#dbe2ea", labelColor="#17202a", titleColor="#17202a", gridColor="#edf1f5")
        .configure_legend(labelColor="#17202a"))


def schedule_result(team_score, opponent_score, selected_is_home):
    if is_blank_value(team_score) or is_blank_value(opponent_score):
        return "TBD"
    if float(team_score) > float(opponent_score):
        return "W"
    if float(team_score) < float(opponent_score):
        return "L"
    return "W" if selected_is_home else "L"


def schedule_regular_record(schedule_df, selected_team):
    if schedule_df is None or schedule_df.shape[0] == 0:
        return "0-0"
    regular_df = schedule_df[schedule_df["Type"] == "Regular Season"].copy()
    wins = 0
    losses = 0
    for _, row in regular_df.iterrows():
        is_home = row.get("TeamA") == selected_team
        team_score = row.get("TeamAScore") if is_home else row.get("TeamBScore")
        opponent_score = row.get("TeamBScore") if is_home else row.get("TeamAScore")
        result = schedule_result(team_score, opponent_score, is_home)
        if result == "W":
            wins += 1
        elif result == "L":
            losses += 1
    return f"{wins}-{losses}"


def render_schedule_table(schedule_df, selected_team, rosters_df=None, show_boxscores=False):
    if schedule_df is None or schedule_df.shape[0] == 0:
        render_html('<div class="sbc-empty-state">No schedule records are available for this selection.</div>')
        return

    type_order = {"Regular Season": 0, "In-Season Tournament": 1, "Play-In": 2, "Playoffs": 3}
    table_df = schedule_df.copy()
    table_df["TypeOrder"] = table_df["Type"].map(type_order).fillna(9)
    table_df = table_df.sort_values(["TypeOrder", "Period", "Game_ID"])

    current_type = None
    render_html('<div class="sbc-schedule-list">')
    for _, row in table_df.iterrows():
        is_home = row.get("TeamA") == selected_team
        opponent = row.get("TeamB") if is_home else row.get("TeamA")
        opponent_info = team_info.get(opponent, {})
        opponent_color = opponent_info.get("bg", "#94a3b8")
        logo = opponent_info.get("logo", "")
        logo_html = f'<img class="sbc-schedule-logo" src="{escape(str(logo), quote=True)}" alt="{escape(str(opponent), quote=True)} logo">' if logo else ""
        venue_mark = "vs" if is_home else "@"
        team_score = row.get("TeamAScore") if is_home else row.get("TeamBScore")
        opponent_score = row.get("TeamBScore") if is_home else row.get("TeamAScore")
        result = schedule_result(team_score, opponent_score, is_home)
        result_class = {"W": "win", "L": "loss"}.get(result, "tbd")
        score_text = "TBD" if result == "TBD" else f"{float(team_score):g}-{float(opponent_score):g}"
        type_text = clean_pick_display(row.get("Type", ""))
        if type_text != current_type:
            current_type = type_text
            render_html(f'<div class="sbc-schedule-group-card"><span>{escape(type_text)}</span></div>')
        render_html(dedent(f"""
        <article class="sbc-schedule-card sbc-schedule-{result_class}" style="--sbc-opponent-color:{escape(str(opponent_color), quote=True)};">
            <div class="sbc-schedule-period"><span>{escape(period_date_label(row.get("Year", ""), row.get("Period", ""), f'P{row.get("Period", "")}'))}</span></div>
            <div class="sbc-schedule-opponent">
                {logo_html}
                <div>
                    <strong>{escape(str(venue_mark))} {escape(str(opponent))}</strong>
                    <em>{escape(live_team_full_name(opponent))}</em>
                </div>
            </div>
            <div class="sbc-schedule-score"><strong>{escape(score_text)}</strong><em>{escape(result)}</em></div>
        </article>
        """))
        if show_boxscores and rosters_df is not None and result != "TBD":
            button_key = f"team_schedule_boxscore_{row.get('Game_ID', '')}_{row.get('Year', '')}_{row.get('Period', '')}_{row.get('TeamA', '')}_{row.get('TeamB', '')}"
            if st.button("Box Score", key=button_key, use_container_width=True, type="primary"):
                render_matchup_boxscore_dialog(row.to_dict(), rosters_df)
    render_html('</div>')


def render_team_travel_map(schedule_df, selected_team, selected_year, height=500):
    travel_df = schedule_df[schedule_df["Type"].isin(["Regular Season", "In-Season Tournament"])].copy()
    if travel_df.shape[0] == 0:
        render_html('<div class="sbc-empty-state">No travel route data is available for this selection.</div>')
        return

    type_order = {"Regular Season": 0, "In-Season Tournament": 1}
    travel_df["TypeOrder"] = travel_df["Type"].map(type_order).fillna(9)
    travel_df = travel_df.sort_values(["Period", "TypeOrder", "Game_ID"]).reset_index(drop=True)
    home_info = team_info.get(selected_team, {})
    current = {
        "team": selected_team,
        "lat": home_info.get("lat"),
        "lon": home_info.get("lon"),
    }
    if is_blank_value(current.get("lat")) or is_blank_value(current.get("lon")):
        render_html('<div class="sbc-empty-state">No travel route data is available for this team.</div>')
        return
    route_stops = [{
        "team": selected_team,
        "lat": float(current["lat"]),
        "lon": float(current["lon"]),
        "home": True,
        "pause": 18,
    }]
    arcs = []
    nodes = [{
        "team": selected_team,
        "lat": current["lat"],
        "lon": current["lon"],
        "home": True,
        "color": home_info.get("bg", bg_color),
    }]

    for _, row in travel_df.iterrows():
        destination_team = selected_team if row.get("TeamA") == selected_team else row.get("TeamA")
        dest_info = team_info.get(destination_team, {})
        dest = {"team": destination_team, "lat": dest_info.get("lat"), "lon": dest_info.get("lon")}
        if not is_blank_value(current.get("lat")) and not is_blank_value(current.get("lon")) and not is_blank_value(dest.get("lat")) and not is_blank_value(dest.get("lon")):
            same_location = float(current["lat"]) == float(dest["lat"]) and float(current["lon"]) == float(dest["lon"])
            if float(current["lat"]) != float(dest["lat"]) or float(current["lon"]) != float(dest["lon"]):
                arcs.append({
                    "src_lat": float(current["lat"]),
                    "src_lon": float(current["lon"]),
                    "dst_lat": float(dest["lat"]),
                    "dst_lon": float(dest["lon"]),
                    "color_hex": home_info.get("bg", bg_color),
                    "note": f"{period_date_label(row.get('Year', ''), row.get('Period'), f'P{row.get("Period")}')}: {selected_team} to {destination_team}",
                })
            route_stops.append({
                "team": destination_team,
                "lat": float(dest["lat"]),
                "lon": float(dest["lon"]),
                "home": destination_team == selected_team,
                "pause": 42 if same_location and destination_team == selected_team else 12,
            })
            nodes.append({
                "team": destination_team,
                "lat": float(dest["lat"]),
                "lon": float(dest["lon"]),
                "home": destination_team == selected_team,
                "color": dest_info.get("bg", "#64748b"),
            })
        current = dest

    if not arcs:
        render_html('<div class="sbc-empty-state">No away travel routes are available for this season.</div>')
        return

    node_df = pd.DataFrame(nodes).drop_duplicates(subset=["lat", "lon"]).to_dict("records")
    map_id = f"sbc-travel-map-{selected_team}-{selected_year}".replace(" ", "-").replace(".", "").lower()
    arcs_json = json.dumps(arcs)
    nodes_json = json.dumps(node_df)
    stops_json = json.dumps(route_stops)
    components.html(f"""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
  #{map_id} {{
    height: {height}px;
    width: 100%;
    border: 1px solid #d9e0ec;
    border-radius: 10px;
    overflow: hidden;
    background: #dbeafe;
  }}
  #{map_id} .leaflet-tile-pane {{
    filter: saturate(0.78) contrast(0.96) brightness(1.04);
  }}
</style>
<div id="{map_id}"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
(function() {{
  const arcs = {arcs_json};
  const nodes = {nodes_json};
  const stops = {stops_json};
  const mapEl = document.getElementById("{map_id}");
  function boot() {{
    if (!window.L || !mapEl) {{ setTimeout(boot, 60); return; }}
    const map = L.map(mapEl, {{ zoomControl: true, scrollWheelZoom: false, attributionControl: true, preferCanvas: true }});
    L.tileLayer("https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png", {{
      attribution: "&copy; OpenStreetMap &copy; CARTO",
      subdomains: "abcd",
      maxZoom: 18
    }}).addTo(map);
    const bounds = [];
    arcs.forEach(a => bounds.push([a.src_lat, a.src_lon], [a.dst_lat, a.dst_lon]));
    nodes.forEach(n => bounds.push([n.lat, n.lon]));
    if (bounds.length) map.fitBounds(bounds, {{ padding: [30, 30], maxZoom: 5 }});
    else map.setView([39.5, -98.35], 4);

    const routeLayer = L.svg({{ padding: 0.35 }}).addTo(map);
    const svg = routeLayer.getPane().querySelector("svg");
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    svg.appendChild(g);
    function curvePoints(a, steps) {{
      const p0 = map.latLngToLayerPoint([a.src_lat, a.src_lon]);
      const p2 = map.latLngToLayerPoint([a.dst_lat, a.dst_lon]);
      const dx = p2.x - p0.x, dy = p2.y - p0.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const lift = Math.min(Math.max(dist * 0.18, 34), 120);
      const p1 = L.point((p0.x + p2.x) / 2 - (dy / dist) * lift, (p0.y + p2.y) / 2 + (dx / dist) * lift);
      const pts = [];
      for (let i = 0; i <= steps; i++) {{
        const t = i / steps;
        pts.push([
          (1 - t) * (1 - t) * p0.x + 2 * (1 - t) * t * p1.x + t * t * p2.x,
          (1 - t) * (1 - t) * p0.y + 2 * (1 - t) * t * p1.y + t * t * p2.y
        ]);
      }}
      return pts;
    }}
    function stopPoint(stop) {{
      return map.latLngToLayerPoint([stop.lat, stop.lon]);
    }}
    function repeatPoint(route, point, count) {{
      const repeats = Math.max(0, Number(count) || 0);
      for (let i = 0; i < repeats; i++) {{
        route.push([point.x, point.y]);
      }}
    }}
    let traveler = null;
    let travelerRoute = [];
    function redraw() {{
      g.innerHTML = "";
      traveler = null;
      travelerRoute = [];
      if (stops.length) {{
        repeatPoint(travelerRoute, stopPoint(stops[0]), stops[0].pause || 10);
      }}
      for (let i = 1; i < stops.length; i++) {{
        const prior = stops[i - 1];
        const next = stops[i];
        const priorPoint = stopPoint(prior);
        const nextPoint = stopPoint(next);
        if (Math.abs(priorPoint.x - nextPoint.x) < 0.2 && Math.abs(priorPoint.y - nextPoint.y) < 0.2) {{
          repeatPoint(travelerRoute, nextPoint, next.pause || 28);
        }} else {{
          const pts = curvePoints({{ src_lat: prior.lat, src_lon: prior.lon, dst_lat: next.lat, dst_lon: next.lon }}, 42);
          travelerRoute = travelerRoute.concat(travelerRoute.length ? pts.slice(1) : pts);
          repeatPoint(travelerRoute, nextPoint, next.pause || 10);
        }}
      }}
      arcs.forEach((a, i) => {{
        const color = a.color_hex || "#2563eb";
        const pts = curvePoints(a, 36);
        const d = pts.map((p, idx) => `${{idx ? "L" : "M"}} ${{p[0].toFixed(1)}} ${{p[1].toFixed(1)}}`).join(" ");
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", d);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", color);
        path.setAttribute("stroke-width", "2.5");
        path.setAttribute("stroke-opacity", "0.42");
        path.setAttribute("stroke-linecap", "round");
        g.appendChild(path);
      }});
      nodes.forEach(n => {{
        const p = map.latLngToLayerPoint([n.lat, n.lon]);
        const ring = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        ring.setAttribute("cx", p.x);
        ring.setAttribute("cy", p.y);
        ring.setAttribute("r", n.home ? "6.8" : "5.5");
        ring.setAttribute("fill", "#ffffff");
        ring.setAttribute("stroke", n.home ? "{bg_color}" : (n.color || "#1a2030"));
        ring.setAttribute("stroke-width", n.home ? "2.8" : "2.1");
        ring.setAttribute("opacity", "0.96");
        g.appendChild(ring);
      }});
      if (travelerRoute.length) {{
        traveler = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        traveler.setAttribute("r", "6.2");
        traveler.setAttribute("fill", "{bg_color}");
        traveler.setAttribute("stroke", "#ffffff");
        traveler.setAttribute("stroke-width", "1.8");
        traveler.setAttribute("opacity", "0.96");
        g.appendChild(traveler);
      }}
    }}
    function animate(now) {{
      if (traveler && travelerRoute.length) {{
        const cycle = Math.max(9000, travelerRoute.length * 42);
        const raw = (now % cycle) / cycle;
        const idx = Math.min(Math.floor(raw * (travelerRoute.length - 1)), travelerRoute.length - 1);
        const p = travelerRoute[idx];
        traveler.setAttribute("cx", p[0]);
        traveler.setAttribute("cy", p[1]);
      }}
      requestAnimationFrame(animate);
    }}
    redraw();
    map.on("zoomend moveend resize", redraw);
    requestAnimationFrame(animate);
  }}
  boot();
}})();
</script>
""", height=height + 12)


def calculate_team_travel_summary(selected_team, selected_year, schedule_df):
    team_df = schedule_df[
        (schedule_df["Year"] == selected_year)
        & (schedule_df["Type"].isin(["Regular Season", "In-Season Tournament"]))
        & ((schedule_df["TeamA"] == selected_team) | (schedule_df["TeamB"] == selected_team))
    ].copy()
    if team_df.empty:
        return 0, 0

    type_order = {"Regular Season": 0, "In-Season Tournament": 1}
    team_df["TypeOrder"] = team_df["Type"].map(type_order).fillna(9)
    team_df = team_df.sort_values(["Period", "TypeOrder", "Game_ID"]).reset_index(drop=True)
    current = team_info.get(selected_team, {})
    current_lat = current.get("lat")
    current_lon = current.get("lon")
    total_miles = 0
    num_flights = 0

    for _, row in team_df.iterrows():
        destination_team = selected_team if row.get("TeamA") == selected_team else row.get("TeamA")
        dest_info = team_info.get(destination_team, {})
        dest_lat = dest_info.get("lat")
        dest_lon = dest_info.get("lon")
        if any(is_blank_value(v) for v in [current_lat, current_lon, dest_lat, dest_lon]):
            continue
        phi1, phi2 = math.radians(float(current_lat)), math.radians(float(dest_lat))
        d_phi = math.radians(float(dest_lat) - float(current_lat))
        d_lam = math.radians(float(dest_lon) - float(current_lon))
        a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
        miles = 3958.8 * 2 * math.asin(math.sqrt(a))
        total_miles += miles
        if miles > 0:
            num_flights += 1
        current_lat, current_lon = dest_lat, dest_lon

    return total_miles, num_flights


def format_score_value(value):
    if is_blank_value(value):
        return "-"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if numeric.is_integer():
        return f"{int(numeric)}"
    return f"{numeric:.1f}"


def score_numeric(value):
    if is_blank_value(value):
        return 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def parse_record_value(value):
    text = "" if is_blank_value(value) else str(value)
    match = re.search(r"(\d+)\s*-\s*(\d+)", text)
    if not match:
        return 0, 0
    return int(match.group(1)), int(match.group(2))


def pct_from_record_value(value):
    wins, losses = parse_record_value(value)
    total = wins + losses
    return wins / total if total else 0


def team_game_rows(schedule_df, selected_year, selected_period, competition_types=None):
    if schedule_df.empty:
        return schedule_df.copy()
    games = schedule_df[
        (schedule_df["Year"] == selected_year)
        & (schedule_df["Period"] <= selected_period)
    ].copy()
    if competition_types:
        games = games[games["Type"].astype(str).isin(competition_types)].copy()
    return games


def point_diff_for_games(team, games):
    if games.empty:
        return 0
    team_a = games["TeamA"].astype(str) == team
    team_b = games["TeamB"].astype(str) == team
    scored = games.loc[team_a, "TeamAScore"].map(score_numeric).sum() + games.loc[team_b, "TeamBScore"].map(score_numeric).sum()
    allowed = games.loc[team_a, "TeamBScore"].map(score_numeric).sum() + games.loc[team_b, "TeamAScore"].map(score_numeric).sum()
    return scored - allowed


def record_pct_for_games(team, games):
    if games.empty:
        return 0
    team_games = games[(games["TeamA"].astype(str) == team) | (games["TeamB"].astype(str) == team)]
    wins = 0
    losses = 0
    for _, game in team_games.iterrows():
        is_a = str(game.get("TeamA", "")) == team
        own = score_numeric(game.get("TeamAScore" if is_a else "TeamBScore", 0))
        opp = score_numeric(game.get("TeamBScore" if is_a else "TeamAScore", 0))
        if own > opp:
            wins += 1
        elif own < opp:
            losses += 1
    total = wins + losses
    return wins / total if total else 0


def tied_team_games(games, teams):
    teams = set(teams)
    if games.empty or not teams:
        return games.iloc[0:0].copy()
    return games[
        games["TeamA"].astype(str).isin(teams)
        & games["TeamB"].astype(str).isin(teams)
    ].copy()


def opponent_games(team, games, opponents):
    opponents = set(opponents)
    if games.empty or not opponents:
        return games.iloc[0:0].copy()
    is_team_a = games["TeamA"].astype(str) == team
    is_team_b = games["TeamB"].astype(str) == team
    return games[
        (is_team_a & games["TeamB"].astype(str).isin(opponents))
        | (is_team_b & games["TeamA"].astype(str).isin(opponents))
    ].copy()


def division_leaders_from_table(table):
    leaders = set()
    for _, div_table in table.groupby("Division"):
        if div_table.empty:
            continue
        ordered = div_table.sort_values(["WinPctRaw", "wins", "PointDiff", "Team"], ascending=[False, False, False, True])
        leaders.add(str(ordered.iloc[0]["Team"]))
    return leaders


def playoff_eligible_teams(table):
    eligible = set()
    for _, conf_table in table.groupby("Conference"):
        ordered = conf_table.sort_values(["WinPctRaw", "wins", "PointDiff", "Team"], ascending=[False, False, False, True])
        eligible.update(ordered.head(10)["Team"].astype(str).tolist())
    return eligible


def tiebreak_value(table, team, criterion, games, playoff_teams, division_leaders):
    info = team_info.get(team, {})
    if criterion == "division_leader":
        return 1 if team in division_leaders else 0
    if criterion == "division_pct":
        division_opponents = [name for name, item in team_info.items() if item.get("div") == info.get("div") and name != team]
        return record_pct_for_games(team, opponent_games(team, games, division_opponents))
    if criterion == "conference_pct":
        conference_opponents = [name for name, item in team_info.items() if item.get("conf") == info.get("conf") and name != team]
        return record_pct_for_games(team, opponent_games(team, games, conference_opponents))
    if criterion == "playoff_own_conf_pct":
        opponents = [name for name in playoff_teams if name != team and team_info.get(name, {}).get("conf") == info.get("conf")]
        return record_pct_for_games(team, opponent_games(team, games, opponents))
    if criterion == "playoff_other_conf_pct":
        opponents = [name for name in playoff_teams if team_info.get(name, {}).get("conf") != info.get("conf")]
        return record_pct_for_games(team, opponent_games(team, games, opponents))
    if criterion == "point_diff":
        return point_diff_for_games(team, games)
    return 0


def nba_style_rank_table(table, games):
    if table.empty:
        return table
    table = table.copy()
    table["PointDiff"] = table["Team"].map(lambda team: point_diff_for_games(str(team), games))
    table = table.sort_values(["WinPctRaw", "wins", "PointDiff", "Team"], ascending=[False, False, False, True])
    division_leaders = division_leaders_from_table(table)
    playoff_teams = playoff_eligible_teams(table)
    ranked_groups = []
    for _, group in table.groupby(["wins", "losses"], sort=False):
        teams = group["Team"].astype(str).tolist()
        if len(teams) == 1:
            ranked_groups.append(group)
            continue
        group = group.copy()
        common_games = tied_team_games(games, teams)
        if len(teams) == 2:
            criteria = ["head_to_head", "division_leader", "division_pct", "conference_pct", "playoff_own_conf_pct", "playoff_other_conf_pct", "point_diff"]
        else:
            criteria = ["division_leader", "head_to_head", "division_pct", "conference_pct", "playoff_own_conf_pct", "point_diff"]
        sort_cols = []
        for criterion in criteria:
            if criterion == "division_pct" and len(set(group["Division"].astype(str))) > 1:
                continue
            col = f"_tb_{criterion}"
            if criterion == "head_to_head":
                group[col] = group["Team"].map(lambda team: record_pct_for_games(str(team), common_games))
            else:
                group[col] = group["Team"].map(lambda team: tiebreak_value(table, str(team), criterion, games, playoff_teams, division_leaders))
            sort_cols.append(col)
        ranked_groups.append(group.sort_values(sort_cols + ["PointDiff", "Team"], ascending=[False] * len(sort_cols) + [False, True]))
    ranked = pd.concat(ranked_groups, ignore_index=True)
    return ranked.drop(columns=[col for col in ranked.columns if str(col).startswith("_tb_")], errors="ignore")


def standings_snapshot(standings_df, selected_year, selected_period, conference):
    team_to_conf = {team: info["conf"] for team, info in team_info.items()}
    team_to_div = {team: info["div"] for team, info in team_info.items()}
    snapshot_period = selected_period
    if not ((standings_df["Year"] == selected_year) & (standings_df["Period"] == snapshot_period)).any():
        snapshot_period = 99
    table = standings_df[
        (standings_df["Year"] == selected_year)
        & (standings_df["Period"] == snapshot_period)
    ].copy()
    table["Conference"] = table["Team"].map(team_to_conf)
    table["Division"] = table["Team"].map(team_to_div)
    if table.empty:
        return table
    table[["wins", "losses"]] = table["Record"].apply(lambda value: pd.Series(parse_record_value(value)))
    table["WinPctRaw"] = table["wins"] / (table["wins"] + table["losses"]).replace(0, pd.NA)
    table["WinPctRaw"] = table["WinPctRaw"].fillna(0)
    games = team_game_rows(all_time_schedule, selected_year, snapshot_period, ["Regular Season"])
    table = nba_style_rank_table(table, games)
    table = table[table["Conference"] == conference].copy()
    if table.empty:
        return table
    max_wins = table["wins"].max()
    table["GB"] = (max_wins - table["wins"]).astype(float).round(1).astype(str)
    table.loc[table["GB"] == "0.0", "GB"] = "-"
    table["Logo"] = table["Team"].map(lambda t: team_info.get(t, {}).get("logo", ""))
    table["FullTeam"] = table["Team"].map(live_team_full_name)
    table["WinPct"] = (table["WinPctRaw"] * 100).round(1).astype(str) + "%"
    return table.reset_index(drop=True)


def history_completed_games(schedule_df, competition_types=None):
    if schedule_df is None or schedule_df.empty:
        return pd.DataFrame()
    required = {"Year", "Period", "Type", "TeamA", "TeamB", "TeamAScore", "TeamBScore"}
    if not required.issubset(schedule_df.columns):
        return pd.DataFrame()
    games = schedule_df.copy()
    if competition_types:
        games = games[games["Type"].astype(str).isin(competition_types)].copy()
    games = games[
        games["TeamA"].astype(str).isin(list(team_info))
        & games["TeamB"].astype(str).isin(list(team_info))
        & ~games["TeamAScore"].apply(is_blank_value)
        & ~games["TeamBScore"].apply(is_blank_value)
    ].copy()
    if games.empty:
        return games
    games["TeamAScoreNum"] = games["TeamAScore"].map(score_numeric)
    games["TeamBScoreNum"] = games["TeamBScore"].map(score_numeric)
    games = games[(games["TeamAScoreNum"] > 0) | (games["TeamBScoreNum"] > 0)].copy()
    games["Winner"] = games.apply(lambda row: row["TeamA"] if row["TeamAScoreNum"] >= row["TeamBScoreNum"] else row["TeamB"], axis=1)
    games["Loser"] = games.apply(lambda row: row["TeamB"] if row["Winner"] == row["TeamA"] else row["TeamA"], axis=1)
    return games


def history_safe_int(value, default=0):
    try:
        if is_blank_value(value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def history_team_record_rows(games):
    rows = {team: {"Team": team, "Wins": 0, "Losses": 0, "PF": 0.0, "PA": 0.0} for team in Teams}
    if games is None or games.empty:
        return pd.DataFrame(rows.values())
    for _, game in games.iterrows():
        team_a = str(game.get("TeamA", ""))
        team_b = str(game.get("TeamB", ""))
        score_a = score_numeric(game.get("TeamAScoreNum", game.get("TeamAScore", 0)))
        score_b = score_numeric(game.get("TeamBScoreNum", game.get("TeamBScore", 0)))
        if team_a in rows:
            rows[team_a]["PF"] += score_a
            rows[team_a]["PA"] += score_b
            rows[team_a]["Wins" if score_a >= score_b else "Losses"] += 1
        if team_b in rows:
            rows[team_b]["PF"] += score_b
            rows[team_b]["PA"] += score_a
            rows[team_b]["Wins" if score_b > score_a else "Losses"] += 1
    table = pd.DataFrame(rows.values())
    table["Games"] = table["Wins"] + table["Losses"]
    table["WinPctRaw"] = table["Wins"] / table["Games"].replace(0, pd.NA)
    table["WinPctRaw"] = table["WinPctRaw"].fillna(0)
    table["Record"] = table["Wins"].astype(int).astype(str) + "-" + table["Losses"].astype(int).astype(str)
    table["WinPct"] = (table["WinPctRaw"] * 100).round(1).astype(str) + "%"
    table["Diff"] = table["PF"] - table["PA"]
    return table.sort_values(["Wins", "WinPctRaw", "Diff", "Team"], ascending=[False, False, False, True]).reset_index(drop=True)


def history_title_years(team_awards_df):
    title_years = {
        team: {
            "Championships": [],
            "Finals Appearances": [],
            "SBC Cup Wins": [],
            "Division Championships": [],
        }
        for team in Teams
    }
    if team_awards_df is None or team_awards_df.empty or not {"Award", "Year", "Winner"}.issubset(team_awards_df.columns):
        return pd.DataFrame([{"Team": team, **{col: "-" for col in values}} for team, values in title_years.items()])

    award_map = {
        "Champion": "Championships",
        "Cup Winner": "SBC Cup Wins",
        "WC Champion": "Finals Appearances",
        "EC Champion": "Finals Appearances",
        "Pacific Champion": "Division Championships",
        "Northwest Champion": "Division Championships",
        "Southwest Champion": "Division Championships",
        "Central Champion": "Division Championships",
        "Atlantic Champion": "Division Championships",
        "Southeast Champion": "Division Championships",
    }
    work = team_awards_df[team_awards_df["Award"].astype(str).isin(award_map)].copy()
    work["_year"] = pd.to_numeric(work["Year"], errors="coerce")
    work = work.dropna(subset=["_year"])
    for _, row in work.iterrows():
        team = clean_pick_display(row.get("Winner", ""))
        if team not in title_years:
            continue
        category = award_map.get(str(row.get("Award", "")))
        if not category:
            continue
        year = int(row["_year"])
        if year not in title_years[team][category]:
            title_years[team][category].append(year)

    rows = []
    for team, values in title_years.items():
        row = {"Team": team}
        for category, years in values.items():
            row[category] = ", ".join(str(year) for year in sorted(years)) if years else "-"
        rows.append(row)
    return pd.DataFrame(rows)


def history_years_count(value):
    if is_blank_value(value) or str(value).strip() == "-":
        return 0
    return len([part for part in str(value).split(",") if part.strip()])


def history_regular_season_h2h_matrix(schedule_df):
    games = history_completed_games(schedule_df, ["Regular Season"])
    matrix = pd.DataFrame("-", index=Teams, columns=Teams)
    if games.empty:
        return matrix.reset_index(names="Team")
    records = {(a, b): [0, 0] for a in Teams for b in Teams if a != b}
    for _, game in games.iterrows():
        team_a = str(game.get("TeamA", ""))
        team_b = str(game.get("TeamB", ""))
        if team_a not in Teams or team_b not in Teams:
            continue
        score_a = score_numeric(game.get("TeamAScoreNum", game.get("TeamAScore", 0)))
        score_b = score_numeric(game.get("TeamBScoreNum", game.get("TeamBScore", 0)))
        if score_a >= score_b:
            records[(team_a, team_b)][0] += 1
            records[(team_b, team_a)][1] += 1
        else:
            records[(team_b, team_a)][0] += 1
            records[(team_a, team_b)][1] += 1
    for row_team in Teams:
        for col_team in Teams:
            if row_team == col_team:
                continue
            wins, losses = records[(row_team, col_team)]
            matrix.loc[row_team, col_team] = f"{wins}-{losses}"
    return matrix.reset_index().rename(columns={"index": "Team"})


def history_team_stat_records(team_stats_df, schedule_df):
    records = []
    games = history_completed_games(schedule_df, ["Regular Season"])
    if not games.empty:
        team_rows = []
        for _, game in games.iterrows():
            for side in ["A", "B"]:
                team_rows.append({
                    "Record": "Matchup Score",
                    "Team": game.get(f"Team{side}", ""),
                    "Value": score_numeric(game.get(f"Team{side}ScoreNum", game.get(f"Team{side}Score", 0))),
                    "Year": game.get("Year", ""),
                    "Period": game.get("Period", ""),
                    "Opponent": game.get("TeamB" if side == "A" else "TeamA", ""),
                })
        if team_rows:
            rows_df = pd.DataFrame(team_rows)
            records.append(rows_df.sort_values("Value", ascending=False).iloc[0].to_dict())
    if team_stats_df is None or team_stats_df.empty or "Team" not in team_stats_df.columns:
        return pd.DataFrame(records)
    stats = team_stats_df.copy()
    if "Type" in stats.columns:
        stats = stats[stats["Type"].astype(str).eq("Regular Season")].copy()
    elif {"Year", "Period"}.issubset(stats.columns) and not games.empty:
        keys = set()
        for _, game in games.iterrows():
            keys.add((history_safe_int(game.get("Year", 0)), history_safe_int(game.get("Period", 0)), str(game.get("TeamA", ""))))
            keys.add((history_safe_int(game.get("Year", 0)), history_safe_int(game.get("Period", 0)), str(game.get("TeamB", ""))))
        stats = stats[
            stats.apply(lambda row: (history_safe_int(row.get("Year", 0)), history_safe_int(row.get("Period", 0)), str(row.get("Team", ""))) in keys, axis=1)
        ].copy()
    exclude = {"Year", "Period", "Team", "Opponent", "Type", "Round", "Game_ID", "Matchup", "Date"}
    priority = ["PTS", "AST", "OREB", "DREB", "REB", "BLK", "ST", "STL", "TO", "MP", "+/-", "TS%", "2PT%", "3PT%", "FT%"]
    numeric_cols = []
    for col in priority + [col for col in stats.columns if col not in priority]:
        if col in exclude or col in numeric_cols or col not in stats.columns:
            continue
        numeric = pd.to_numeric(stats[col], errors="coerce")
        if numeric.notna().any():
            numeric_cols.append(col)
    for col in numeric_cols[:18]:
        temp = stats.copy()
        temp["_value"] = pd.to_numeric(temp[col], errors="coerce")
        temp = temp.dropna(subset=["_value"])
        if temp.empty:
            continue
        row = temp.sort_values("_value", ascending=False).iloc[0]
        opponent = row.get("Opponent", "")
        if is_blank_value(opponent) and {"Year", "Period"}.issubset(row.index) and not games.empty:
            matchup = games[
                (games["Year"].astype(str) == str(row.get("Year", "")))
                & (games["Period"].astype(str) == str(row.get("Period", "")))
                & ((games["TeamA"].astype(str) == str(row.get("Team", ""))) | (games["TeamB"].astype(str) == str(row.get("Team", ""))))
            ]
            if not matchup.empty:
                game = matchup.iloc[0]
                opponent = game.get("TeamB") if str(game.get("TeamA")) == str(row.get("Team")) else game.get("TeamA")
        records.append({
            "Record": col,
            "Team": row.get("Team", ""),
            "Value": row.get("_value", 0),
            "Year": row.get("Year", ""),
            "Period": row.get("Period", ""),
            "Opponent": opponent,
        })
    return pd.DataFrame(records)


def history_all_time_team_stats_table(team_stats_df):
    stat_cols = ["GP", "MP", "TS%", "2PTM", "2PTA", "2PT%", "3PTM", "3PTA", "3PT%", "FTM", "FTA", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
    if team_stats_df is None or team_stats_df.empty or "Team" not in team_stats_df.columns:
        return pd.DataFrame(columns=["Team"] + stat_cols)
    stats = team_stats_df.copy()
    if "Type" in stats.columns:
        stats = stats[stats["Type"].astype(str).eq("Regular Season")].copy()
    for col in stat_cols:
        if col not in stats.columns:
            stats[col] = 0
        stats[col] = pd.to_numeric(stats[col], errors="coerce").fillna(0)
    totals = stats.groupby("Team", as_index=False)[[col for col in stat_cols if col not in ["TS%", "2PT%", "3PT%", "FT%"]]].sum()
    for team in Teams:
        if team not in set(totals["Team"].astype(str)):
            totals = pd.concat([totals, pd.DataFrame([{"Team": team}])], ignore_index=True)
    totals = totals.fillna(0)
    fga = totals["2PTA"] + totals["3PTA"]
    totals["TS%"] = (totals["PTS"] / (2 * (fga + 0.44 * totals["FTA"]))).where((fga + 0.44 * totals["FTA"]) > 0, 0)
    totals["2PT%"] = (totals["2PTM"] / totals["2PTA"]).where(totals["2PTA"] > 0, 0)
    totals["3PT%"] = (totals["3PTM"] / totals["3PTA"]).where(totals["3PTA"] > 0, 0)
    totals["FT%"] = (totals["FTM"] / totals["FTA"]).where(totals["FTA"] > 0, 0)
    totals = totals[["Team"] + stat_cols]
    totals = totals.sort_values(["PTS", "GP", "Team"], ascending=[False, False, True]).reset_index(drop=True)
    display = totals.copy()
    for col in ["TS%", "2PT%", "3PT%", "FT%"]:
        display[col] = (display[col] * 100).round(1).astype(str) + "%"
    for col in [c for c in stat_cols if c not in ["TS%", "2PT%", "3PT%", "FT%"]]:
        display[col] = display[col].round(0).astype(int)
    return display


def render_history_overview_table(data, columns):
    if data is None or data.empty:
        render_html('<div class="sbc-empty-state">No historical records are available yet.</div>')
        return
    head = "".join(f"<th>{escape(str(col))}</th>" for col in columns)
    rows = []
    for _, row in data.iterrows():
        cells = []
        for col in columns:
            value = row.get(col, "")
            if col == "Team":
                cells.append(f"<td>{render_draft_team_wordmark(value, include_nickname=True)}</td>")
            elif col in ["Championships", "Finals Appearances", "SBC Cup Wins", "Division Championships"]:
                cells.append(f'<td class="sbc-history-years-cell">{escape(str(value))}</td>')
            else:
                cells.append(f"<td>{escape(str(value))}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")
    render_html(f"""
        <div class="sbc-history-table-wrap">
            <table class="sbc-history-overview-table">
                <thead><tr>{head}</tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
    """)


def render_history_h2h_matrix(matrix):
    if matrix is None or matrix.empty:
        render_html('<div class="sbc-empty-state">No regular season head-to-head records are available yet.</div>')
        return

    def h2h_cell_style(value):
        try:
            wins_raw, losses_raw = str(value).split("-", 1)
            wins = float(wins_raw)
            losses = float(losses_raw)
            games = wins + losses
            if games <= 0:
                return "background: rgba(255,255,255,0.88);", "No games"
            pct = wins / games
            if pct < 0.5:
                strength = (0.5 - pct) / 0.5
                red = int(255 - (255 - 248) * strength)
                green = int(255 - (255 - 113) * strength)
                blue = int(255 - (255 - 113) * strength)
            else:
                strength = (pct - 0.5) / 0.5
                red = int(255 - (255 - 134) * strength)
                green = int(255 - (255 - 239) * strength)
                blue = int(255 - (255 - 172) * strength)
            return f"background: rgb({red}, {green}, {blue});", f"{pct:.1%} win rate"
        except (TypeError, ValueError):
            return "background: rgba(255,255,255,0.88);", "No games"

    teams = [team for team in matrix.columns if team != "Team" and team in team_info]
    header_cells = ['<th class="sbc-h2h-corner">Team</th>']
    for team in teams:
        logo = team_logo_for_name(team)
        header_cells.append(
            f'<th class="sbc-h2h-logo-head" title="{escape(live_team_full_name(team), quote=True)}">'
            f'<img src="{escape(str(logo), quote=True)}" alt="{escape(live_team_full_name(team), quote=True)} logo" referrerpolicy="no-referrer">'
            f'</th>'
        )
    rows = []
    for _, row in matrix.iterrows():
        team = str(row.get("Team", ""))
        logo = team_logo_for_name(team)
        cells = [
            f'<th class="sbc-h2h-row-head" title="{escape(live_team_full_name(team), quote=True)}">'
            f'<img src="{escape(str(logo), quote=True)}" alt="{escape(live_team_full_name(team), quote=True)} logo" referrerpolicy="no-referrer">'
            f'<span>{escape(team_abbrev_for_name(team))}</span></th>'
        ]
        for opp in teams:
            value = str(row.get(opp, "-"))
            cell_class = "sbc-h2h-self" if opp == team else ""
            cell_style, cell_title = h2h_cell_style(value)
            cells.append(
                f'<td class="{cell_class}" style="{escape(cell_style, quote=True)}" title="{escape(cell_title, quote=True)}">'
                f'{escape(value)}</td>'
            )
        rows.append(f"<tr>{''.join(cells)}</tr>")
    render_html(f"""
        <div class="sbc-h2h-read-key">
            <span>Read across</span>
            <em>Row logo's record against the column logo.</em>
        </div>
        <div class="sbc-h2h-wrap">
            <table class="sbc-h2h-table">
                <thead><tr>{''.join(header_cells)}</tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
    """)


def render_history_all_time_stats_table(data):
    if data is None or data.empty:
        render_html('<div class="sbc-empty-state">No all-time team stat archive is available yet.</div>')
        return
    data = data.reset_index(drop=True).copy()
    columns = ["Team", "GP", "MP", "TS%", "2PTM", "2PTA", "2PT%", "3PTM", "3PTA", "3PT%", "FTM", "FTA", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
    stat_columns = columns[1:]
    head = '<th class="sbc-history-stat-logo-head"></th>' + "".join(f"<th>{escape(str(col))}</th>" for col in stat_columns)
    rank_maps = {}
    for col in stat_columns:
        values = data[col].astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False)
        numeric = pd.to_numeric(values, errors="coerce").fillna(0)
        rank_maps[col] = numeric.rank(method="min", ascending=False).astype(int).to_dict()
    rows = []
    for idx, row in data.iterrows():
        team = str(row.get("Team", ""))
        logo = team_logo_for_name(team)
        cells = [
            f'<td class="sbc-history-stat-team-logo" title="{escape(live_team_full_name(team), quote=True)}">'
            f'<img src="{escape(str(logo), quote=True)}" alt="{escape(live_team_full_name(team), quote=True)} logo" referrerpolicy="no-referrer">'
            f'</td>',
        ]
        for col in stat_columns:
            value = row.get(col, "")
            rank = rank_maps.get(col, {}).get(idx, "")
            cells.append(f'<td><span>{escape(str(value))}</span><em>#{escape(str(rank))}</em></td>')
        rows.append(f"<tr>{''.join(cells)}</tr>")
    render_html(f"""
        <div class="sbc-history-table-wrap sbc-history-stats-wrap">
            <table class="sbc-history-overview-table sbc-history-stats-table">
                <thead><tr>{head}</tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
    """)


FRANCHISE_CHASER_STATS = ["GP", "MP", "TS%", "2PTM", "2PTA", "2PT%", "3PTM", "3PTA", "3PT%", "FTM", "FTA", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]


def active_franchise_record_chasers(matchup_archive, cap_df):
    if matchup_archive is None or matchup_archive.empty or cap_df is None or cap_df.empty:
        return pd.DataFrame()
    needed = {"sbc_team_key", "fantrax_name", "sbc_matchup_type"}
    if not needed.issubset(matchup_archive.columns):
        return pd.DataFrame()
    sum_stats = [stat for stat in BOX_SCORE_SUM_STATS if stat in matchup_archive.columns]
    if not sum_stats:
        return pd.DataFrame()
    rows = valid_matchup_archive_rows(matchup_archive)
    rows = dedupe_matchup_archive_for_totals(rows)
    rows = rows[rows["sbc_matchup_type"].astype(str) == "Regular Season"].copy()
    if rows.empty:
        return pd.DataFrame()
    rows["_player_key"] = rows["fantrax_name"].apply(player_name_match_key)
    group_cols = ["sbc_team_key", "fantrax_name", "_player_key"]
    if "espn_player_id" in rows.columns:
        group_cols.append("espn_player_id")
    grouped = rows.groupby(group_cols, dropna=False, as_index=False)[sum_stats].sum()
    grouped = recalc_shooting_stats(grouped)
    stats = [stat for stat in FRANCHISE_CHASER_STATS if stat in grouped.columns]
    active_key_map = {team: current_active_player_keys_for_team(cap_df, team) for team in team_info}
    records = []
    for team, team_rows in grouped.groupby("sbc_team_key", dropna=False):
        team_key = resolve_team_key(team)
        if team_key not in team_info:
            continue
        active_keys = active_key_map.get(team_key, set())
        if not active_keys:
            continue
        active_rows = team_rows[team_rows["_player_key"].isin(active_keys)].copy()
        if active_rows.empty:
            continue
        for stat in stats:
            stat_pool = team_rows.copy()
            if stat in ["TS%", "2PT%", "3PT%", "FT%"]:
                stat_pool = stat_pool[stat_pool.apply(lambda row: stat_has_shooting_volume(row, stat), axis=1)].copy()
            if stat_pool.empty:
                continue
            stat_values = pd.to_numeric(stat_pool[stat], errors="coerce").fillna(0)
            if stat_values.max() <= 0 and stat != "+/-":
                continue
            leader_idx = stat_values.idxmax()
            leader = stat_pool.loc[leader_idx]
            leader_value = float(stat_values.loc[leader_idx])
            leader_active = player_name_match_key(leader.get("fantrax_name", "")) in active_keys
            for _, player in active_rows.iterrows():
                if stat in ["TS%", "2PT%", "3PT%", "FT%"] and not stat_has_shooting_volume(player, stat):
                    continue
                current_value = float(pd.to_numeric(pd.Series([player.get(stat, 0)]), errors="coerce").fillna(0).iloc[0])
                gap = leader_value - current_value
                if gap <= 0:
                    continue
                records.append({
                    "Team": team_key,
                    "fantrax_name": player.get("fantrax_name", ""),
                    "espn_player_id": player.get("espn_player_id", ""),
                    "Stat": stat,
                    "Current": current_value,
                    "Leader": leader.get("fantrax_name", ""),
                    "LeaderEspnId": leader.get("espn_player_id", ""),
                    "LeaderValue": leader_value,
                    "LeaderActive": leader_active,
                    "Gap": gap,
                    "Progress": current_value / leader_value if leader_value else 0,
                })
    league_group_cols = ["fantrax_name", "_player_key"]
    if "espn_player_id" in rows.columns:
        league_group_cols.append("espn_player_id")
    league_grouped = rows.groupby(league_group_cols, dropna=False, as_index=False)[sum_stats].sum()
    league_grouped = recalc_shooting_stats(league_grouped)
    active_league_keys = set().union(*active_key_map.values()) if active_key_map else set()
    active_league_rows = league_grouped[league_grouped["_player_key"].isin(active_league_keys)].copy()
    if not active_league_rows.empty:
        for stat in stats:
            stat_pool = league_grouped.copy()
            if stat in ["TS%", "2PT%", "3PT%", "FT%"]:
                stat_pool = stat_pool[stat_pool.apply(lambda row: stat_has_shooting_volume(row, stat), axis=1)].copy()
            if stat_pool.empty:
                continue
            stat_values = pd.to_numeric(stat_pool[stat], errors="coerce").fillna(0)
            if stat_values.max() <= 0 and stat != "+/-":
                continue
            leader_idx = stat_values.idxmax()
            leader = stat_pool.loc[leader_idx]
            leader_value = float(stat_values.loc[leader_idx])
            leader_active = player_name_match_key(leader.get("fantrax_name", "")) in active_league_keys
            candidates = active_league_rows.copy()
            if stat in ["TS%", "2PT%", "3PT%", "FT%"]:
                candidates = candidates[candidates.apply(lambda row: stat_has_shooting_volume(row, stat), axis=1)].copy()
            if candidates.empty:
                continue
            candidates["_current_value"] = pd.to_numeric(candidates[stat], errors="coerce").fillna(0)
            candidates["_gap"] = leader_value - candidates["_current_value"]
            candidates = candidates[candidates["_gap"] > 0].copy()
            if candidates.empty:
                continue
            candidates["_progress"] = candidates["_current_value"].apply(lambda value: value / leader_value if leader_value else 0)
            player = candidates.sort_values(["_gap", "_progress"], ascending=[True, False]).iloc[0]
            records.append({
                "Team": "League",
                "fantrax_name": player.get("fantrax_name", ""),
                "espn_player_id": player.get("espn_player_id", ""),
                "Stat": stat,
                "Current": float(player.get("_current_value", 0)),
                "Leader": leader.get("fantrax_name", ""),
                "LeaderEspnId": leader.get("espn_player_id", ""),
                "LeaderValue": leader_value,
                "LeaderActive": leader_active,
                "Gap": float(player.get("_gap", 0)),
                "Progress": float(player.get("_progress", 0)),
                "Scope": "League",
            })
    if not records:
        return pd.DataFrame()
    chasers = pd.DataFrame(records)
    chasers["_gap_sort"] = pd.to_numeric(chasers["Gap"], errors="coerce").fillna(999999999)
    chasers["_progress_sort"] = pd.to_numeric(chasers["Progress"], errors="coerce").fillna(0)
    return chasers.sort_values(["_progress_sort", "_gap_sort"], ascending=[False, True]).reset_index(drop=True)


def render_franchise_record_chasers(chasers):
    if chasers is None or chasers.empty:
        render_html('<div class="sbc-empty-state">No active franchise record chases are available yet.</div>')
        return
    stat_options = ["All Categories"] + [stat for stat in FRANCHISE_CHASER_STATS if stat in set(chasers["Stat"].astype(str))]
    selected_stat = st.selectbox("Record Chase Category", stat_options, key="league_history_record_chase_stat")
    work = chasers.copy()
    if selected_stat != "All Categories":
        work = work[work["Stat"].astype(str) == selected_stat].copy()
        league_work = work[work["Team"].astype(str) == "League"].sort_values(["Gap", "Progress"], ascending=[True, False]).head(1)
        work = work[work["Team"].astype(str) != "League"].sort_values(["Gap", "Progress"], ascending=[True, False])
        work = pd.concat([work.drop_duplicates("Team", keep="first").head(30), league_work], ignore_index=True)
    else:
        league_work = work[work["Team"].astype(str) == "League"].sort_values(["Progress", "Gap"], ascending=[False, True]).head(1)
        work = work[work["Team"].astype(str) != "League"].sort_values(["Progress", "Gap"], ascending=[False, True]).head(30)
        work = pd.concat([work, league_work], ignore_index=True)
    body = []
    for rank, (_, row) in enumerate(work.iterrows(), start=1):
        is_league_row = str(row.get("Team", "")) == "League"
        team = resolve_team_key(row.get("Team", ""))
        stat = str(row.get("Stat", ""))
        is_pct = stat in ["TS%", "2PT%", "3PT%", "FT%"]
        gap_text = f"{float(row.get('Gap', 0) or 0) * 100:.1f} pct pts" if is_pct else stat_number(row.get("Gap", 0), signed=(stat == "+/-"))
        leader_marker = " ⭐" if bool(row.get("LeaderActive", False)) else ""
        leader_name = clean_pick_display(row.get("Leader", ""))
        leader_value_text = stat_number(row.get("LeaderValue", 0), pct=is_pct, signed=(stat == "+/-"))
        leader_image = espn_headshot_url(row.get("LeaderEspnId", "")) if not is_blank_value(row.get("LeaderEspnId", "")) else DRAFT_SILHOUETTE
        leader_html = f"""
            <span class="sbc-history-player-cell">
                <img src="{escape(str(leader_image), quote=True)}" alt="{escape(str(leader_name), quote=True)} headshot">
                <strong>{escape(str(leader_name))}{leader_marker}</strong>
            </span>
        """
        team_html = (
            f'<span class="sbc-player-profile-team-mark sbc-player-profile-team-total"><img src="{league_logo_html}" alt="SBCFBL logo"><strong>League</strong><em>Career</em></span>'
            if is_league_row else history_team_mark_html(team)
        )
        row_color = LEAGUE_PRIMARY if is_league_row else team_color_for_name(team)
        current_text = stat_number(row.get("Current", 0), pct=is_pct, signed=(stat == "+/-"))
        progress = float(row.get("Progress", 0) or 0)
        progress_text = f"{progress * 100:.1f}%"
        body.append(f"""
            <tr style="--record-team-color:{escape(str(row_color), quote=True)};">
                <td><strong>{rank}</strong></td>
                <td>{team_html}</td>
                <td>{player_history_cell_html(row)}</td>
                <td><strong>{escape(boxscore_stat_label(stat))}</strong><em>{escape(gap_text)} away</em></td>
                <td><strong>{escape(current_text)}</strong><em>{escape(progress_text)} of record</em></td>
                <td>{leader_html}<em>{escape(leader_value_text)}</em></td>
            </tr>
        """)
    render_html(f"""
        <div class="sbc-box-table-scroll">
            <table class="sbc-history-overview-table sbc-matchup-high-table sbc-record-chase-table">
                <thead><tr><th>#</th><th>Team</th><th>Active Player</th><th>Record Chase</th><th>Current</th><th>Franchise Leader</th></tr></thead>
                <tbody>{''.join(body)}</tbody>
            </table>
        </div>
    """)


def render_league_history_overview():
    regular_games = history_completed_games(all_time_schedule, ["Regular Season"])
    all_games = history_completed_games(all_time_schedule)
    team_records = history_team_record_rows(regular_games)
    title_counts = history_title_years(team_award_history)
    summary = team_records.merge(title_counts, on="Team", how="left").fillna(0)
    summary["PF"] = summary["PF"].round(1)
    summary["PA"] = summary["PA"].round(1)
    summary["Diff"] = summary["Diff"].round(1)
    seasons = sorted(all_games["Year"].dropna().astype(int).unique().tolist()) if not all_games.empty and "Year" in all_games.columns else []
    championship_total = int(summary["Championships"].map(history_years_count).sum()) if "Championships" in summary.columns else 0
    cup_total = int(summary["SBC Cup Wins"].map(history_years_count).sum()) if "SBC Cup Wins" in summary.columns else 0
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">League History</div>
                    <div class="sbc-draft-heading">SBCFBL Record Book</div>
                    <div class="sbc-draft-subcopy">All-time franchise records, title counts, regular-season head-to-head history, and single-matchup team records across the archive.</div>
                </div>
            </div>
        </div>
        <div class="sbc-history-kpi-grid">
            <div class="sbc-draft-tile"><div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">Y</div><div class="sbc-draft-tile-value">{escape(str(len(seasons)))}</div></div><div class="sbc-draft-tile-label">Seasons</div><div class="sbc-draft-tile-note">{escape(str(seasons[0] if seasons else '-'))} through {escape(str(seasons[-1] if seasons else '-'))}</div></div>
            <div class="sbc-draft-tile"><div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">G</div><div class="sbc-draft-tile-value">{escape(str(regular_games.shape[0]))}</div></div><div class="sbc-draft-tile-label">Regular Season Games</div><div class="sbc-draft-tile-note">Completed games in the H2H matrix.</div></div>
            <div class="sbc-draft-tile"><div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">C</div><div class="sbc-draft-tile-value">{escape(str(championship_total))}</div></div><div class="sbc-draft-tile-label">Championships Logged</div><div class="sbc-draft-tile-note">Playoff finals winners in the archive.</div></div>
            <div class="sbc-draft-tile"><div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">Cup</div><div class="sbc-draft-tile-value">{escape(str(cup_total))}</div></div><div class="sbc-draft-tile-label">SBC Cup Winners</div><div class="sbc-draft-tile-note">Cup championship results in history.</div></div>
        </div>
    """)
    render_html('<div class="sbc-awards-section-head"><span>All-Time Franchise Ledger</span><em>Regular season record with title seasons from the awards archive.</em></div>')
    ledger = summary[["Team", "Record", "WinPct", "PF", "PA", "Diff", "Championships", "Finals Appearances", "SBC Cup Wins", "Division Championships"]].copy()
    render_history_overview_table(
        ledger,
        ["Team", "Record", "WinPct", "PF", "PA", "Diff", "Championships", "Finals Appearances", "SBC Cup Wins", "Division Championships"],
    )
    render_html('<div class="sbc-awards-section-head"><span>Regular Season H2H Matrix</span><em>Cell is row team record against column team.</em></div>')
    h2h = history_regular_season_h2h_matrix(all_time_schedule)
    render_history_h2h_matrix(h2h)
    render_html('<div class="sbc-awards-section-head"><span>All-Time Team Stats</span><em>Regular season totals by franchise; percentages are recalculated from makes and attempts.</em></div>')
    all_time_stats = history_all_time_team_stats_table(all_time_team_stats)
    render_history_all_time_stats_table(all_time_stats)
    matchup_archive = load_sbc_player_matchup_stats_archive()
    render_html('<div class="sbc-awards-section-head"><span>Active Record Chasers</span><em>Current roster players closest to becoming their franchise leader. ⭐ means the leader is also active, so the target can move.</em></div>')
    render_franchise_record_chasers(active_franchise_record_chasers(matchup_archive, df))


def ist_group_games(selected_year):
    games = all_time_schedule[
        (all_time_schedule["Year"] == selected_year)
        & (all_time_schedule["Type"].astype(str) == "In-Season Tournament")
    ].copy()
    if games.empty:
        return games
    group_stage = games[games["Round"].astype(str).str.contains("Group", case=False, na=False)].copy()
    return group_stage if not group_stage.empty else games


def infer_ist_groups(selected_year):
    games = ist_group_games(selected_year)
    if games.empty:
        return {}
    teams = sorted(set(games["TeamA"].dropna().astype(str)).union(games["TeamB"].dropna().astype(str)))
    parent = {team: team for team in teams}

    def find(team):
        while parent[team] != team:
            parent[team] = parent[parent[team]]
            team = parent[team]
        return team

    def union(a, b):
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for _, game in games.iterrows():
        team_a = str(game.get("TeamA", ""))
        team_b = str(game.get("TeamB", ""))
        if team_a in parent and team_b in parent:
            union(team_a, team_b)

    components = {}
    for team in teams:
        components.setdefault(find(team), []).append(team)

    groups = {}
    for conference in ["West", "East"]:
        conf_components = [
            sorted(group)
            for group in components.values()
            if group and team_info.get(group[0], {}).get("conf") == conference
        ]
        conf_components = sorted(conf_components, key=lambda group: group[0])
        for idx, group in enumerate(conf_components[:3]):
            groups[f"{conference} {chr(ord('A') + idx)}"] = group
    return groups


def ist_record_for_team(team, games):
    team_games = games[(games["TeamA"].astype(str) == team) | (games["TeamB"].astype(str) == team)]
    wins = 0
    losses = 0
    for _, game in team_games.iterrows():
        is_a = str(game.get("TeamA", "")) == team
        own = score_numeric(game.get("TeamAScore" if is_a else "TeamBScore", 0))
        opp = score_numeric(game.get("TeamBScore" if is_a else "TeamAScore", 0))
        if own > opp:
            wins += 1
        elif own < opp:
            losses += 1
    return wins, losses


def rank_ist_teams(teams, games):
    rows = []
    for team in teams:
        wins, losses = ist_record_for_team(team, games)
        rows.append({
            "Team": team,
            "wins": wins,
            "losses": losses,
            "PointDiff": point_diff_for_games(team, games),
            "Record": f"{wins}-{losses}",
        })
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    table["WinPctRaw"] = table["wins"] / (table["wins"] + table["losses"]).replace(0, pd.NA)
    table["WinPctRaw"] = table["WinPctRaw"].fillna(0)
    ranked = []
    for _, group in table.sort_values(["WinPctRaw", "wins", "PointDiff", "Team"], ascending=[False, False, False, True]).groupby(["wins", "losses"], sort=False):
        tied = group["Team"].astype(str).tolist()
        common_games = tied_team_games(games, tied)
        group = group.copy()
        group["_h2h"] = group["Team"].map(lambda team: record_pct_for_games(str(team), common_games))
        ranked.append(group.sort_values(["_h2h", "PointDiff", "Team"], ascending=[False, False, True]))
    out = pd.concat(ranked, ignore_index=True).drop(columns=["_h2h"], errors="ignore")
    out["FullTeam"] = out["Team"].map(live_team_full_name)
    out["Logo"] = out["Team"].map(lambda team: team_info.get(team, {}).get("logo", ""))
    out["PointDiffDisplay"] = out["PointDiff"].map(lambda value: f"{value:+.0f}")
    return out.reset_index(drop=True)


def ist_group_tables(selected_year, selected_period):
    groups = infer_ist_groups(selected_year)
    if not groups:
        return {}
    played_games = team_game_rows(ist_group_games(selected_year), selected_year, selected_period)
    if played_games.empty:
        return {}
    grouped = {}
    for group_name, teams in groups.items():
        group_games = played_games[
            played_games["TeamA"].astype(str).isin(teams)
            & played_games["TeamB"].astype(str).isin(teams)
        ].copy()
        ranked = rank_ist_teams(teams, group_games)
        if not ranked.empty:
            grouped[group_name] = ranked
    for conference in ["West", "East"]:
        conference_groups = {name: table for name, table in grouped.items() if name.startswith(conference)}
        second_place_rows = []
        for table in conference_groups.values():
            if table.shape[0] > 1:
                second_place_rows.append(table.iloc[[1]].copy())
        if second_place_rows:
            wildcard_pool = pd.concat(second_place_rows, ignore_index=True)
            wildcard_pool = wildcard_pool.sort_values(["wins", "PointDiff", "Team"], ascending=[False, False, True])
            wildcard = wildcard_pool.iloc[0]["Team"]
            for table in conference_groups.values():
                table["Tier"] = ["winner" if idx == 0 else "wildcard" if row["Team"] == wildcard else "out" for idx, row in table.iterrows()]
        else:
            for table in conference_groups.values():
                table["Tier"] = ["winner" if idx == 0 else "out" for idx, _ in table.iterrows()]
    return grouped


def render_scoreboard_cards(scores_df):
    if scores_df.empty:
        render_html('<div class="sbc-empty-state">No scoreboards are available for this period.</div>')
        return

    type_labels = {
        "Regular Season": "Regular Season",
        "In-Season Tournament": "In-Season Tournament",
        "Play-In": "Play-In",
        "Playoffs": "Playoffs",
    }
    for type_name in ["Regular Season", "In-Season Tournament", "Play-In", "Playoffs"]:
        group_df = scores_df[scores_df["Type"].astype(str) == type_name].copy()
        if group_df.empty:
            continue
        group_df = group_df.sort_values(["Round", "TeamB_Nickname", "TeamA_Nickname"], na_position="last")
        render_html(f"""
            <section class="sbc-score-group">
                <div class="sbc-score-group-head">
                    <span>{escape(type_labels.get(type_name, type_name))}</span>
                    <em>{group_df.shape[0]} matchup{'s' if group_df.shape[0] != 1 else ''}</em>
                </div>
            </section>
        """)
        matchup_cols = st.columns(min(3, group_df.shape[0]))
        for card_idx, (_, row) in enumerate(group_df.iterrows()):
            team_a = str(row.get("TeamA", ""))
            team_b = str(row.get("TeamB", ""))
            score_a = row.get("TeamA_Score", row.get("TeamAScore", ""))
            score_b = row.get("TeamB_Score", row.get("TeamBScore", ""))
            score_a_num = score_numeric(score_a)
            score_b_num = score_numeric(score_b)
            a_winner = score_a_num >= score_b_num
            b_winner = score_b_num > score_a_num
            info_a = team_info.get(team_a, {})
            info_b = team_info.get(team_b, {})
            logo_a = row.get("TeamA_logo", info_a.get("logo", ""))
            logo_b = row.get("TeamB_logo", info_b.get("logo", ""))
            color_a = row.get("TeamA_color", info_a.get("bg", "#64748b"))
            color_b = row.get("TeamB_color", info_b.get("bg", "#64748b"))
            record_a = row.get("TeamA_record", "")
            record_b = row.get("TeamB_record", "")
            round_label = row.get("Round", type_name)
            period_label = period_date_label(row.get("Year", ""), row.get("Period", ""), f'P{row.get("Period", "")}')
            col_idx = card_idx % len(matchup_cols)
            with matchup_cols[col_idx]:
                render_html(f"""
                <article class="sbc-score-card">
                    <div class="sbc-score-card-top">
                        <span>{escape(str(round_label))}</span>
                        <em>{escape(period_label)}</em>
                    </div>
                    <div class="sbc-score-team {'sbc-score-winner' if a_winner else ''}" style="--score-color:{escape(str(color_a), quote=True)};">
                        <img src="{escape(str(logo_a), quote=True)}" alt="{escape(live_team_full_name(team_a), quote=True)} logo">
                        <div>
                            <strong>{escape(live_team_full_name(team_a))}</strong>
                            <em>{escape(str(record_a))}</em>
                        </div>
                        <b>{escape(format_score_value(score_a))}</b>
                    </div>
                    <div class="sbc-score-team {'sbc-score-winner' if b_winner else ''}" style="--score-color:{escape(str(color_b), quote=True)};">
                        <img src="{escape(str(logo_b), quote=True)}" alt="{escape(live_team_full_name(team_b), quote=True)} logo">
                        <div>
                            <strong>{escape(live_team_full_name(team_b))}</strong>
                            <em>{escape(str(record_b))}</em>
                        </div>
                        <b>{escape(format_score_value(score_b))}</b>
                    </div>
                </article>
                """)
                button_key = f"boxscore_{row.get('Game_ID', '')}_{row.get('Year', '')}_{row.get('Period', '')}_{team_a}_{team_b}"
                if st.button("Box Score", key=button_key, use_container_width=True, type="primary", help="Open matchup box score"):
                    render_matchup_boxscore_dialog(row.to_dict(), all_time_rosters)


def render_conference_standings(standings_df, selected_year, selected_period, conference):
    table = standings_snapshot(standings_df, selected_year, selected_period, conference)
    if table.empty:
        render_html(f'<div class="sbc-empty-state">No {escape(conference)} standings are available for this period.</div>')
        return

    rows = []
    for idx, row in table.iterrows():
        tier = "playoff" if idx <= 5 else "playin" if idx <= 9 else "lottery"
        rows.append(f"""
            <tr class="sbc-standings-{tier}">
                <td class="sbc-standings-rank"><span>{idx + 1}</span></td>
                <td class="sbc-standings-team">
                    <img src="{escape(str(row.get("Logo", "")), quote=True)}" alt="{escape(str(row.get("FullTeam", "")), quote=True)} logo">
                    <strong>{escape(str(row.get("FullTeam", "")))}</strong>
                </td>
                <td>{escape(str(row.get("Record", "")))}</td>
                <td>{escape(str(row.get("WinPct", "")))}</td>
                <td>{escape(str(row.get("GB", "")))}</td>
                <td>{escape(str(row.get("ConfRecord", "")))}</td>
                <td>{escape(str(row.get("DivRecord", "")))}</td>
            </tr>
        """)

    render_html(f"""
        <section class="sbc-standings-panel sbc-standings-{escape(str(conference).lower())}">
            <div class="sbc-standings-head">
                <span>{escape(conference)} Conference</span>
                <em>Through {escape(period_date_label(selected_year, selected_period, f'P{selected_period}'))}</em>
            </div>
            <div class="sbc-standings-table-wrap">
                <table class="sbc-standings-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Team</th>
                            <th>Record</th>
                            <th>Win %</th>
                            <th>GB</th>
                            <th>Conf.</th>
                            <th>Div.</th>
                        </tr>
                    </thead>
                    <tbody>{''.join(rows)}</tbody>
                </table>
            </div>
        </section>
    """)


def render_ist_standings(standings_df, selected_year, selected_period):
    grouped = ist_group_tables(selected_year, selected_period)
    if not grouped:
        return
    panels = []
    for conference in ["West", "East"]:
        sections = []
        for group_name in [f"{conference} A", f"{conference} B", f"{conference} C"]:
            table = grouped.get(group_name)
            if table is None or table.empty:
                continue
            rows = []
            for idx, row in table.iterrows():
                tier = {"winner": "playoff", "wildcard": "playin"}.get(row.get("Tier", "out"), "lottery")
                rows.append(f"""
                    <tr class="sbc-standings-{tier}">
                        <td class="sbc-standings-rank"><span>{idx + 1}</span></td>
                        <td class="sbc-standings-team">
                            <img src="{escape(str(row.get("Logo", "")), quote=True)}" alt="{escape(str(row.get("FullTeam", "")), quote=True)} logo">
                            <strong>{escape(str(row.get("FullTeam", "")))}</strong>
                        </td>
                        <td>{escape(str(row.get("Record", "")))}</td>
                        <td>{escape(str(row.get("PointDiffDisplay", "")))}</td>
                    </tr>
                """)
            sections.append(f"""
                <tr class="sbc-standings-group-row"><td colspan="4">{escape(group_name)}</td></tr>
                {''.join(rows)}
            """)
        if not sections:
            continue
        panels.append(f"""
            <section class="sbc-standings-panel sbc-standings-{escape(str(conference).lower())}">
                <div class="sbc-standings-head">
                    <span>{conference} Groups</span>
                    <em>Through {escape(period_date_label(selected_year, selected_period, f'P{selected_period}'))}</em>
                </div>
                <div class="sbc-standings-table-wrap">
                    <table class="sbc-standings-table sbc-ist-standings-table">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Team</th>
                                <th>Record</th>
                                <th>Diff</th>
                            </tr>
                        </thead>
                        <tbody>{''.join(sections)}</tbody>
                    </table>
                </div>
            </section>
        """)
    if not panels:
        return
    render_html('<div class="sbc-section-label">Tournament Snapshot</div>')
    render_html(f'<div class="sbc-standings-layout">{"".join(panels)}</div>')


def schedule_year_options_for_history():
    if all_time_schedule is None or all_time_schedule.empty or "Year" not in all_time_schedule.columns:
        return [current_year]
    years = sorted(all_time_schedule["Year"].dropna().astype(int).unique().tolist())
    return years or [current_year]


def latest_period_for_year(selected_year, fallback=99):
    if all_time_schedule is None or all_time_schedule.empty or not {"Year", "Period"}.issubset(all_time_schedule.columns):
        return fallback
    periods = all_time_schedule[all_time_schedule["Year"] == selected_year]["Period"].dropna()
    if periods.empty:
        return fallback
    return int(periods.max())


def history_round_rank(value):
    text = str(clean_pick_display(value)).lower()
    rank_map = [
        ("group", 0),
        ("play-in", 1),
        ("play in", 1),
        ("quarter", 2),
        ("first", 2),
        ("semifinal", 3),
        ("semi", 3),
        ("conference", 4),
        ("final", 5),
        ("champ", 6),
    ]
    for needle, rank in rank_map:
        if needle in text:
            return rank
    return 9


def history_game_winner(row):
    score_a = score_numeric(row.get("TeamAScore", row.get("TeamA_Score", "")))
    score_b = score_numeric(row.get("TeamBScore", row.get("TeamB_Score", "")))
    if score_a == 0 and score_b == 0:
        return ""
    return row.get("TeamA", "") if score_a >= score_b else row.get("TeamB", "")


def history_team_seed(team, seed_lookup):
    seed = seed_lookup.get(str(team), "")
    if is_blank_value(seed):
        return "-"
    return str(seed)


def bracket_seed_lookup(standings_df, selected_year, selected_period):
    lookup = {}
    for conference in ["West", "East"]:
        table = standings_snapshot(standings_df, selected_year, selected_period, conference)
        for idx, row in table.iterrows():
            lookup[str(row.get("Team", ""))] = idx + 1
    return lookup


def bracket_team_label(team, mode="abbr"):
    if is_blank_value(team):
        return "-"
    if mode == "logo":
        return ""
    if mode == "full":
        return live_team_full_name(str(team))
    return TEAM_ABBREVIATIONS.get(str(team), str(team))


def render_history_bracket_team(team, winner, seed_lookup, label_mode="abbr", score="", show_score=False):
    team = clean_pick_display(team)
    info = team_info.get(team, {})
    logo = info.get("logo", "")
    color = info.get("bg", LEAGUE_PRIMARY)
    secondary = info.get("bg2", LEAGUE_SECONDARY)
    seed_color = LEAGUE_SECONDARY if info.get("conf") == "West" else LEAGUE_PRIMARY
    is_winner = team == winner
    return f"""
        <div class="sbc-bracket-team {'sbc-bracket-team-winner' if is_winner else ''}" style="--bracket-team-color:{escape(str(color), quote=True)};--bracket-team-secondary:{escape(str(secondary), quote=True)};--bracket-seed-color:{escape(str(seed_color), quote=True)};">
            <span class="sbc-bracket-seed">{escape(history_team_seed(team, seed_lookup))}</span>
            <img src="{escape(str(logo), quote=True)}" alt="{escape(live_team_full_name(team), quote=True)} logo">
            <strong title="{escape(live_team_full_name(team), quote=True)}">{escape(bracket_team_label(team, label_mode))}</strong>
            {'<b class="sbc-bracket-score">' + escape(format_score_value(score)) + '</b>' if show_score and not is_blank_value(score) else ''}
        </div>
    """


def render_history_matchup_card(row):
    team_a = clean_pick_display(row.get("TeamA", ""))
    team_b = clean_pick_display(row.get("TeamB", ""))
    score_a = row.get("TeamAScore", row.get("TeamA_Score", ""))
    score_b = row.get("TeamBScore", row.get("TeamB_Score", ""))
    winner = history_game_winner(row)
    period_label = period_date_label(row.get("Year", ""), row.get("Period", ""), f'P{row.get("Period", "")}') if not is_blank_value(row.get("Period", "")) else ""
    rows = []
    for team, score in [(team_a, score_a), (team_b, score_b)]:
        info = team_info.get(team, {})
        logo = info.get("logo", "")
        color = info.get("bg", LEAGUE_PRIMARY)
        rows.append(f"""
            <div class="sbc-history-game-team {'sbc-history-game-winner' if team == winner else ''}" style="--history-team-color:{escape(str(color), quote=True)};">
                <img src="{escape(str(logo), quote=True)}" alt="{escape(live_team_full_name(team), quote=True)} logo">
                <strong>{escape(live_team_full_name(team))}</strong>
                <b>{escape(format_score_value(score))}</b>
            </div>
        """)
    return f"""
        <article class="sbc-history-game-card">
            <div class="sbc-history-game-top">
                <span>{escape(str(row.get("Round", row.get("Type", ""))))}</span>
                <em>{period_label}</em>
            </div>
            {''.join(rows)}
        </article>
    """


def render_history_bracket_matchup(row, seed_lookup, label_mode="abbr", show_score=False):
    team_a = clean_pick_display(row.get("TeamA", ""))
    team_b = clean_pick_display(row.get("TeamB", ""))
    score_a = row.get("TeamAScore", row.get("TeamA_Score", ""))
    score_b = row.get("TeamBScore", row.get("TeamB_Score", ""))
    winner = history_game_winner(row)
    winner_info = team_info.get(winner, {})
    winner_color = winner_info.get("bg", LEAGUE_PRIMARY)
    return f"""
        <article class="sbc-bracket-matchup" style="--bracket-winner-color:{escape(str(winner_color), quote=True)};">
            <div class="sbc-bracket-matchup-inner">
                {render_history_bracket_team(team_a, winner, seed_lookup, label_mode, score_a, show_score)}
                {render_history_bracket_team(team_b, winner, seed_lookup, label_mode, score_b, show_score)}
            </div>
        </article>
    """


def bracket_period_label(games):
    if games is None or games.empty or "Period" not in games.columns:
        return ""
    periods = pd.to_numeric(games["Period"], errors="coerce").dropna().astype(int).tolist()
    if not periods:
        return ""
    selected_year = games["Year"].dropna().iloc[0] if "Year" in games.columns and not games["Year"].dropna().empty else current_year
    return period_range_label(selected_year, periods, f"P{min(periods)}" if min(periods) == max(periods) else f"P{min(periods)}-P{max(periods)}")


def bracket_game_conference(row):
    team_a = str(row.get("TeamA", ""))
    team_b = str(row.get("TeamB", ""))
    conf_a = team_info.get(team_a, {}).get("conf", "")
    conf_b = team_info.get(team_b, {}).get("conf", "")
    if conf_a and conf_a == conf_b:
        return conf_a
    return "Finals"


def bracket_seed_number(team, seed_lookup):
    raw = seed_lookup.get(str(team), "")
    if str(raw).upper() == "WC":
        return 10
    try:
        return int(float(str(raw)))
    except (TypeError, ValueError):
        return 99


def game_seed_numbers(row, seed_lookup):
    return sorted([
        bracket_seed_number(row.get("TeamA", ""), seed_lookup),
        bracket_seed_number(row.get("TeamB", ""), seed_lookup),
    ])


def playoff_game_sort_key(row, seed_lookup, bucket):
    seeds = game_seed_numbers(row, seed_lookup)
    if bucket == "playin":
        if seeds == [7, 8]:
            return 3
        if seeds == [9, 10]:
            return 1
        return 0
    if bucket == "first":
        first_round_order = {
            (1, 8): 0,
            (1, 9): 0,
            (1, 10): 0,
            (4, 5): 1,
            (3, 6): 2,
            (2, 7): 3,
            (2, 8): 3,
            (2, 9): 3,
            (2, 10): 3,
        }
        return first_round_order.get(tuple(seeds), min(seeds) if seeds else 99)
    return min(seeds) if seeds else 99


def playoff_round_bucket(row):
    type_name = str(row.get("Type", ""))
    round_name = str(row.get("Round", "")).lower()
    if type_name == "Play-In":
        return "playin"
    if bracket_game_conference(row) == "Finals":
        return "finals"
    if "quarter" in round_name or "first" in round_name:
        return "first"
    if "semi" in round_name:
        return "semi"
    if "final" in round_name or "champ" in round_name:
        return "conf_final"
    return "first"


def render_bracket_empty(label="TBD"):
    return f"""
        <article class="sbc-bracket-matchup sbc-bracket-matchup-empty">
            <div class="sbc-bracket-matchup-inner">
                <div class="sbc-bracket-team" style="--bracket-team-color:#94a3b8;--bracket-team-secondary:#cbd5e1;--bracket-seed-color:#64748b;"><span class="sbc-bracket-seed">-</span><strong>{escape(label)}</strong></div>
                <div class="sbc-bracket-team" style="--bracket-team-color:#94a3b8;--bracket-team-secondary:#cbd5e1;--bracket-seed-color:#64748b;"><span class="sbc-bracket-seed">-</span><strong>{escape(label)}</strong></div>
            </div>
        </article>
    """


def render_playoff_playin_group(label, games, seed_lookup, show_head=False, subtitle=""):
    cards = [render_history_bracket_matchup(row, seed_lookup, label_mode="logo", show_score=True) for _, row in games.iterrows()]
    if not cards:
        cards = [render_bracket_empty("")]
    head_html = f'<div class="sbc-playin-group-head"><span>{escape(label)}</span><em>{escape(subtitle)}</em></div>' if show_head and label else ""
    return f"""
        <div class="sbc-playin-group">
            {head_html}
            <div class="sbc-playin-group-games">{''.join(cards)}</div>
        </div>
    """


def render_playoff_bracket_column(games, title, seed_lookup, minimum_slots=0, bucket=""):
    if games is None:
        games = pd.DataFrame()
    games = games.copy()
    if not games.empty:
        games["_game_sort"] = pd.to_numeric(games.get("Game_ID", pd.Series(range(games.shape[0]))), errors="coerce").fillna(0)
        games["_seed_sort"] = games.apply(lambda row: playoff_game_sort_key(row, seed_lookup, bucket), axis=1)
        games = games.sort_values(["_seed_sort", "Period", "_game_sort", "TeamA", "TeamB"])
    elif bucket == "playin":
        games["_seed_sort"] = pd.Series(dtype=int)
    if bucket == "playin":
        top_games = games[games["_seed_sort"] == 0].copy()
        nine_ten_games = games[games["_seed_sort"] == 1].copy()
        seven_eight_games = games[games["_seed_sort"] == 3].copy()
        cards = [
            render_playoff_playin_group("", top_games, seed_lookup),
            '<div class="sbc-playin-spacer"></div>',
            render_playoff_playin_group("Play-In Round 1", nine_ten_games, seed_lookup, show_head=True, subtitle=bracket_period_label(nine_ten_games)),
            render_playoff_playin_group("", seven_eight_games, seed_lookup),
        ]
        title = "Play-In Round 2"
        period_label = bracket_period_label(top_games)
    else:
        cards = [render_history_bracket_matchup(row, seed_lookup, label_mode="logo", show_score=True) for _, row in games.iterrows()]
        period_label = bracket_period_label(games)
    while len(cards) < minimum_slots:
        cards.append(render_bracket_empty())
    return f"""
        <section class="sbc-nba-bracket-column">
            <div class="sbc-nba-bracket-column-head">
                <span>{escape(title)}</span>
                <em>{escape(period_label)}</em>
            </div>
            <div class="sbc-bracket-games">{''.join(cards)}</div>
        </section>
    """


def render_playoff_bracket(games, title, empty_text, seed_lookup=None):
    if games is None or games.empty:
        render_html(f'<div class="sbc-empty-state">{escape(empty_text)}</div>')
        return
    seed_lookup = seed_lookup or {}
    bracket = games.copy()
    bracket["_bucket"] = bracket.apply(playoff_round_bucket, axis=1)
    bracket["_conference"] = bracket.apply(bracket_game_conference, axis=1)
    bracket["_game_sort"] = pd.to_numeric(bracket.get("Game_ID", pd.Series(range(bracket.shape[0]))), errors="coerce").fillna(0)
    champion_game = bracket[bracket["_bucket"] == "finals"].sort_values(["Period", "_game_sort"], na_position="last").tail(1)
    champion = history_game_winner(champion_game.iloc[0]) if not champion_game.empty else ""
    champion_info = team_info.get(champion, {})
    champion_logo = champion_info.get("logo", "")
    champion_color = champion_info.get("bg", LEAGUE_PRIMARY)
    champion_secondary = champion_info.get("bg2", LEAGUE_SECONDARY)
    champion_html = f"""
        <aside class="sbc-bracket-champion" style="--champion-color:{escape(str(champion_color), quote=True)};--champion-secondary:{escape(str(champion_secondary), quote=True)};">
            <span>SBCFBL Champion</span>
            {'<img src="' + escape(str(champion_logo), quote=True) + '" alt="' + escape(live_team_full_name(champion), quote=True) + ' logo">' if champion else ''}
            <strong>{escape(live_team_full_name(champion)) if champion else 'TBD'}</strong>
        </aside>
    """

    def conf_games(conference, bucket):
        return bracket[(bracket["_conference"] == conference) & (bracket["_bucket"] == bucket)].copy()

    finals_games = bracket[bracket["_bucket"] == "finals"].copy()
    west_html = "".join([
        render_playoff_bracket_column(conf_games("West", "playin"), "Play-In Round 2", seed_lookup, minimum_slots=4, bucket="playin"),
        render_playoff_bracket_column(conf_games("West", "first"), "First Round", seed_lookup, minimum_slots=4, bucket="first"),
        render_playoff_bracket_column(conf_games("West", "semi"), "Semifinals", seed_lookup, minimum_slots=2, bucket="semi"),
        render_playoff_bracket_column(conf_games("West", "conf_final"), "Conference Finals", seed_lookup, minimum_slots=1, bucket="conf_final"),
    ])
    east_html = "".join([
        render_playoff_bracket_column(conf_games("East", "conf_final"), "Conference Finals", seed_lookup, minimum_slots=1, bucket="conf_final"),
        render_playoff_bracket_column(conf_games("East", "semi"), "Semifinals", seed_lookup, minimum_slots=2, bucket="semi"),
        render_playoff_bracket_column(conf_games("East", "first"), "First Round", seed_lookup, minimum_slots=4, bucket="first"),
        render_playoff_bracket_column(conf_games("East", "playin"), "Play-In Round 2", seed_lookup, minimum_slots=4, bucket="playin"),
    ])
    finals_html = render_playoff_bracket_column(finals_games, "SBCFBL Finals", seed_lookup, minimum_slots=1, bucket="finals")

    render_html(f"""
        <section class="sbc-bracket-panel sbc-nba-bracket-panel">
            <div class="sbc-bracket-head">
                <span>{escape(title)}</span>
                <em>{escape(bracket_period_label(bracket))}</em>
            </div>
            <div class="sbc-nba-bracket">
                <div class="sbc-nba-bracket-side sbc-nba-bracket-west"><div class="sbc-nba-conference-title">Western Conference</div>{west_html}</div>
                <div class="sbc-nba-bracket-center">{finals_html}{champion_html}</div>
                <div class="sbc-nba-bracket-side sbc-nba-bracket-east"><div class="sbc-nba-conference-title">Eastern Conference</div>{east_html}</div>
            </div>
        </section>
    """)


def render_history_bracket(games, title, empty_text, seed_lookup=None):
    if games is None or games.empty:
        render_html(f'<div class="sbc-empty-state">{escape(empty_text)}</div>')
        return
    seed_lookup = seed_lookup or {}
    bracket = games.copy()
    bracket["_type_sort"] = bracket["Type"].map({"Play-In": 0, "Playoffs": 1, "In-Season Tournament": 0}).fillna(9)
    bracket["_round_sort"] = bracket["Round"].apply(history_round_rank)
    bracket["_game_sort"] = pd.to_numeric(bracket.get("Game_ID", pd.Series(range(bracket.shape[0]))), errors="coerce").fillna(0)
    bracket = bracket.sort_values(["_type_sort", "_round_sort", "Period", "_game_sort", "TeamA", "TeamB"])

    round_blocks = []
    for (type_name, round_name), round_games in bracket.groupby(["Type", "Round"], sort=False, dropna=False):
        round_label = clean_pick_display(round_name)
        if str(type_name) == "Play-In" and "play" not in str(round_label).lower():
            round_label = f"Play-In - {round_label}"
        periods = pd.to_numeric(round_games["Period"], errors="coerce").dropna().astype(int).tolist() if "Period" in round_games.columns else []
        if not periods:
            period_label = ""
        else:
            period_year = round_games["Year"].dropna().iloc[0] if "Year" in round_games.columns and not round_games["Year"].dropna().empty else current_year
            period_label = period_range_label(period_year, periods, f"P{min(periods)}" if min(periods) == max(periods) else f"P{min(periods)}-P{max(periods)}")
        cards = "".join(render_history_bracket_matchup(row, seed_lookup) for _, row in round_games.iterrows())
        round_blocks.append(f"""
            <section class="sbc-bracket-round">
                <div class="sbc-bracket-round-head">
                    <span>{escape(str(round_label))}</span>
                    <em>{escape(period_label)}</em>
                </div>
                <div class="sbc-bracket-games">{cards}</div>
            </section>
        """)

    champion = history_game_winner(bracket.iloc[-1]) if not bracket.empty else ""
    champion_info = team_info.get(champion, {})
    champion_logo = champion_info.get("logo", "")
    champion_color = champion_info.get("bg", LEAGUE_PRIMARY)
    champion_secondary = champion_info.get("bg2", LEAGUE_SECONDARY)
    champion_html = ""
    if champion:
        champion_html = f"""
            <aside class="sbc-bracket-champion" style="--champion-color:{escape(str(champion_color), quote=True)};--champion-secondary:{escape(str(champion_secondary), quote=True)};">
                <span>Champion</span>
                <img src="{escape(str(champion_logo), quote=True)}" alt="{escape(live_team_full_name(champion), quote=True)} logo">
                <strong>{escape(live_team_full_name(champion))}</strong>
            </aside>
        """
    split_at = math.ceil(len(round_blocks) / 2)
    left_blocks = round_blocks[:split_at]
    right_blocks = list(reversed(round_blocks[split_at:]))
    if not right_blocks and len(left_blocks) > 1:
        right_blocks = [left_blocks.pop()]

    render_html(f"""
        <section class="sbc-bracket-panel">
            <div class="sbc-bracket-head">
                <span>{escape(title)}</span>
                <em>{bracket.shape[0]} game path</em>
            </div>
            <div class="sbc-bracket-stage">
                <div class="sbc-bracket-side sbc-bracket-side-left">{''.join(left_blocks)}</div>
                {champion_html}
                <div class="sbc-bracket-side sbc-bracket-side-right">{''.join(right_blocks)}</div>
            </div>
        </section>
    """)


def render_ist_conference_history_panel(selected_year, selected_period, conference):
    grouped = ist_group_tables(selected_year, selected_period)
    sections = []
    for group_name in [f"{conference} A", f"{conference} B", f"{conference} C"]:
        table = grouped.get(group_name)
        if table is None or table.empty:
            continue
        rows = []
        for idx, row in table.iterrows():
            tier = {"winner": "playoff", "wildcard": "playin"}.get(row.get("Tier", "out"), "lottery")
            rows.append(f"""
                <tr class="sbc-standings-{tier}">
                    <td class="sbc-standings-rank"><span>{idx + 1}</span></td>
                    <td class="sbc-standings-team">
                        <img src="{escape(str(row.get("Logo", "")), quote=True)}" alt="{escape(str(row.get("FullTeam", "")), quote=True)} logo">
                        <strong>{escape(str(row.get("FullTeam", "")))}</strong>
                    </td>
                    <td>{escape(str(row.get("Record", "")))}</td>
                    <td>{escape(str(row.get("PointDiffDisplay", "")))}</td>
                </tr>
            """)
        sections.append(f'<tr class="sbc-standings-group-row"><td colspan="4">{escape(group_name)}</td></tr>{"".join(rows)}')
    if not sections:
        render_html(f'<div class="sbc-empty-state">No {escape(conference)} tournament standings are available for this year.</div>')
        return
    render_html(f"""
        <section class="sbc-standings-panel sbc-standings-{escape(str(conference).lower())}">
            <div class="sbc-standings-head">
                <span>{escape(conference)} Groups</span>
                <em>{escape(str(selected_year))}</em>
            </div>
            <div class="sbc-standings-table-wrap">
                <table class="sbc-standings-table sbc-ist-standings-table">
                    <thead><tr><th>Rank</th><th>Team</th><th>Record</th><th>Diff</th></tr></thead>
                    <tbody>{''.join(sections)}</tbody>
                </table>
            </div>
        </section>
    """)


def ist_bracket_seed_lookup(selected_year, selected_period):
    lookup = {}
    grouped = ist_group_tables(selected_year, selected_period)
    for conference in ["West", "East"]:
        winner_rows = []
        second_place_rows = []
        for group_name in [f"{conference} A", f"{conference} B", f"{conference} C"]:
            table = grouped.get(group_name)
            if table is None or table.empty:
                continue
            winner_rows.append(table.iloc[[0]].copy())
            if table.shape[0] > 1:
                second_place_rows.append(table.iloc[[1]].copy())
        if winner_rows:
            winner_pool = pd.concat(winner_rows, ignore_index=True)
            winner_pool = winner_pool.sort_values(["wins", "PointDiff", "Team"], ascending=[False, False, True])
            for idx, (_, row) in enumerate(winner_pool.head(3).iterrows(), start=1):
                team = str(row.get("Team", ""))
                if team:
                    lookup[team] = str(idx)
        wildcard = ""
        if second_place_rows:
            wildcard_pool = pd.concat(second_place_rows, ignore_index=True)
            wildcard_pool = wildcard_pool.sort_values(["wins", "PointDiff", "Team"], ascending=[False, False, True])
            wildcard = str(wildcard_pool.iloc[0].get("Team", ""))
        if wildcard:
            lookup[wildcard] = "WC"
    return lookup


def ist_game_sort_key(row, seed_lookup):
    conference_sort = {"West": 0, "East": 1, "Finals": 2}.get(bracket_game_conference(row), 3)
    seeds = {str(seed_lookup.get(str(row.get("TeamA", "")), "")), str(seed_lookup.get(str(row.get("TeamB", "")), ""))}
    if {"1", "WC"}.issubset(seeds):
        matchup_sort = 0
    elif {"2", "3"}.issubset(seeds):
        matchup_sort = 1
    else:
        matchup_sort = 2
    return conference_sort, matchup_sort


def ist_bracket_round_label(round_name):
    label = str(clean_pick_display(round_name)).lower()
    if "quarter" in label:
        return "Quarterfinals"
    if "semi" in label:
        return "Semifinals"
    if "champ" in label or "final" in label:
        return "SBCFBL Cup"
    return "Quarterfinals"


def render_ist_bracket(games, title, empty_text, seed_lookup=None):
    if games is None or games.empty:
        render_html(f'<div class="sbc-empty-state">{escape(empty_text)}</div>')
        return
    seed_lookup = seed_lookup or {}
    bracket = games.copy()
    bracket["_conference"] = bracket.apply(bracket_game_conference, axis=1)
    bracket["_round_sort"] = bracket["Round"].apply(history_round_rank)
    bracket["_game_sort"] = pd.to_numeric(bracket.get("Game_ID", pd.Series(range(bracket.shape[0]))), errors="coerce").fillna(0)
    bracket["_conf_sort"] = bracket["_conference"].map({"West": 0, "East": 1, "Finals": 2}).fillna(3)
    bracket = bracket.sort_values(["_round_sort", "_conf_sort", "_game_sort", "TeamA", "TeamB"])
    columns = []
    for round_name, round_games in bracket.groupby("Round", sort=False, dropna=False):
        west_games = round_games[round_games["_conference"] == "West"].copy()
        east_games = round_games[round_games["_conference"] == "East"].copy()
        finals_games = round_games[round_games["_conference"] == "Finals"].copy()
        ordered_games = pd.concat([west_games, east_games, finals_games], ignore_index=True)
        if not ordered_games.empty:
            ordered_games[["_conf_order", "_match_order"]] = ordered_games.apply(lambda row: pd.Series(ist_game_sort_key(row, seed_lookup)), axis=1)
            ordered_games = ordered_games.sort_values(["_conf_order", "_match_order", "_game_sort", "TeamA", "TeamB"])
        cards = "".join(render_history_bracket_matchup(row, seed_lookup, label_mode="full", show_score=True) for _, row in ordered_games.iterrows())
        columns.append(f"""
            <section class="sbc-bracket-round sbc-ist-bracket-round">
                <div class="sbc-bracket-round-head">
                    <span>{escape(ist_bracket_round_label(round_name))}</span>
                    <em>{escape(bracket_period_label(ordered_games))}</em>
                </div>
                <div class="sbc-bracket-games">{cards}</div>
            </section>
        """)
    champion = history_game_winner(bracket.iloc[-1]) if not bracket.empty else ""
    champion_info = team_info.get(champion, {})
    champion_logo = champion_info.get("logo", "")
    champion_color = champion_info.get("bg", LEAGUE_PRIMARY)
    champion_secondary = champion_info.get("bg2", LEAGUE_SECONDARY)
    render_html(f"""
        <section class="sbc-bracket-panel sbc-ist-bracket-panel">
            <div class="sbc-bracket-head">
                <span>{escape(title)}</span>
                <em>{escape(bracket_period_label(bracket))}</em>
            </div>
            <div class="sbc-ist-bracket-stage">
                <div class="sbc-ist-bracket-flow">{''.join(columns)}</div>
                <aside class="sbc-bracket-champion" style="--champion-color:{escape(str(champion_color), quote=True)};--champion-secondary:{escape(str(champion_secondary), quote=True)};">
                    <span>SBCFBL Cup Champion</span>
                    {'<img src="' + escape(str(champion_logo), quote=True) + '" alt="' + escape(live_team_full_name(champion), quote=True) + ' logo">' if champion else ''}
                    <strong>{escape(live_team_full_name(champion)) if champion else 'TBD'}</strong>
                </aside>
            </div>
        </section>
    """)


def render_under_construction(title, body):
    render_html(f"""
        <section class="sbc-under-construction">
            <div class="sbc-under-icon">...</div>
            <div>
                <strong>{escape(title)}</strong>
                <span>{escape(body)}</span>
            </div>
        </section>
    """)

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Amatic+SC:wght@700&family=Arvo:wght@400;700&family=Audiowide&family=Baloo+2:wght@700;800&family=Bebas+Neue&family=Bungee&family=Cabin+Sketch:wght@700&family=Comfortaa:wght@700&family=Creepster&family=Dancing+Script:wght@700&family=Fjalla+One&family=IM+Fell+English&family=Indie+Flower&family=Lobster&family=Neucha&family=Oswald:wght@700&family=Pacifico&family=Parisienne&family=Pathway+Gothic+One&family=Permanent+Marker&family=Playfair+Display:wght@800&family=Poppins:wght@400;600;700;800;900&family=Quicksand:wght@700&family=Roboto+Slab:wght@800&family=Rye&family=Satisfy&family=Shadows+Into+Light&family=Tangerine:wght@700&family=Teko:wght@700&family=Ubuntu:wght@700&display=swap');

    :root {{
        --sbc-team-primary: {LEAGUE_PRIMARY};
        --sbc-team-secondary: {LEAGUE_SECONDARY};
        --sbc-team-text: #ffffff;
        --sbc-team-font: "{league_font_css}", "Poppins", sans-serif;
        --sbc-selected-primary: {bg_color};
        --sbc-selected-secondary: {text_color2};
        --sbc-selected-text: {text_color};
        --sbc-selected-font: "{team_font_css}", "Poppins", sans-serif;
        --sbc-bg: #f4f6f8;
        --sbc-panel: #ffffff;
        --sbc-ink: #17202a;
        --sbc-muted: #697586;
        --sbc-border: rgba(23, 32, 42, 0.11);
        --sbc-shadow: 0 18px 45px rgba(18, 25, 38, 0.10);
    }}

    .stApp {{
        font-family: "Poppins", "Segoe UI", sans-serif;
        background:
            radial-gradient(circle at 10% 0%, color-mix(in srgb, var(--sbc-team-primary) 42%, transparent) 0, transparent 38rem),
            radial-gradient(circle at 90% 2%, color-mix(in srgb, var(--sbc-team-secondary) 36%, transparent) 0, transparent 34rem),
            linear-gradient(180deg, color-mix(in srgb, var(--sbc-team-primary) 12%, #ffffff) 0%, rgba(244, 246, 248, 0.94) 34%, color-mix(in srgb, var(--sbc-team-secondary) 9%, #eef2f6) 100%);
        color: var(--sbc-ink);
    }}

    html[data-sbc-main-tab="team"] .stApp {{
        background:
            radial-gradient(circle at 10% 0%, color-mix(in srgb, var(--sbc-selected-primary) 42%, transparent) 0, transparent 38rem),
            radial-gradient(circle at 90% 2%, color-mix(in srgb, var(--sbc-selected-secondary) 36%, transparent) 0, transparent 34rem),
            linear-gradient(180deg, color-mix(in srgb, var(--sbc-selected-primary) 12%, #ffffff) 0%, rgba(244, 246, 248, 0.94) 34%, color-mix(in srgb, var(--sbc-selected-secondary) 9%, #eef2f6) 100%);
    }}

    .block-container,
    [data-testid="stMainBlockContainer"] {{
        box-sizing: border-box;
        width: 100%;
        max-width: min(1500px, 100%);
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 5.25rem;
        padding-bottom: 3rem;
    }}

    [data-testid="stMainBlockContainer"] > div {{
        max-width: 100%;
    }}

    header[data-testid="stHeader"] {{
        background: rgba(244, 246, 248, 0.82);
        backdrop-filter: blur(14px);
        border-bottom: 1px solid rgba(23, 32, 42, 0.06);
    }}

    header[data-testid="stHeader"] *,
    [data-testid="stToolbar"] *,
    [data-testid="stToolbar"] button,
    [data-testid="stToolbar"] a {{
        color: #111827 !important;
    }}

    [data-testid="stToolbar"] button,
    [data-testid="stToolbar"] [role="button"] {{
        background: transparent !important;
        box-shadow: none !important;
    }}

    [data-testid="stToolbar"] svg {{
        color: #111827 !important;
        filter: brightness(0) saturate(100%) !important;
    }}

    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        flex: 0 0 0 !important;
    }}

    .sbc-app-masthead {{
        margin-bottom: 0.75rem;
    }}

    .sbc-league-masthead {{
        display: grid;
        grid-template-columns: auto 1fr;
        align-items: center;
        gap: 1rem;
        padding: 0.95rem 1.1rem;
        border: 1px solid color-mix(in srgb, {LEAGUE_PRIMARY} 24%, rgba(23, 32, 42, 0.12));
        border-radius: 8px;
        background: linear-gradient(135deg, color-mix(in srgb, {LEAGUE_PRIMARY} 10%, #ffffff) 0%, color-mix(in srgb, {LEAGUE_SECONDARY} 9%, #ffffff) 100%);
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.075);
    }}

    .sbc-league-masthead img {{
        width: clamp(4.25rem, 9vw, 6.25rem);
        height: clamp(4.25rem, 9vw, 6.25rem);
        object-fit: contain;
        filter: drop-shadow(0 8px 16px rgba(18, 25, 38, 0.18));
    }}

    .sbc-league-masthead .sbc-app-eyebrow {{
        color: {LEAGUE_SECONDARY};
    }}

    .sbc-league-masthead .sbc-app-title {{
        color: {LEAGUE_PRIMARY};
        font-family: "{league_font_css}", "Poppins", sans-serif;
    }}

    .sbc-app-eyebrow {{
        color: var(--sbc-team-primary);
        font-size: 0.8rem;
        font-weight: 900;
        letter-spacing: 0.16em;
        line-height: 1;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
    }}

    .sbc-app-title {{
        color: var(--sbc-ink);
        font-size: clamp(2.15rem, 4.2vw, 4.05rem);
        font-weight: 950;
        letter-spacing: 0;
        line-height: 0.94;
        margin: 0;
    }}

    .sbc-app-subtitle {{
        max-width: 48rem;
        margin-top: 0.55rem;
        color: var(--sbc-muted);
        font-size: 1rem;
        font-weight: 700;
        line-height: 1.35;
    }}

    .sbc-picker-eyebrow {{
        color: var(--sbc-team-primary);
        font-size: 0.72rem;
        font-weight: 900;
        letter-spacing: 0.14em;
        line-height: 1;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
    }}

    .sbc-team-hero {{
        position: relative;
        overflow: visible;
        margin: 0.35rem 0 1.15rem;
        padding: 1.25rem 1.4rem;
        border: 1px solid rgba(255, 255, 255, 0.58);
        border-radius: 8px;
        background: var(--sbc-team-primary);
        box-shadow: var(--sbc-shadow);
        color: var(--sbc-team-secondary);
    }}

    .sbc-team-hero::after {{
        content: none;
    }}

    .sbc-team-hero-inner {{
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: minmax(7rem, 9.25rem) 1fr;
        gap: 1.35rem;
        align-items: center;
    }}

    .sbc-logo-frame {{
        width: 8.75rem;
        height: 8.75rem;
        display: grid;
        place-items: center;
        padding: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
    }}

    .sbc-logo-frame img {{
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        display: block;
        filter: drop-shadow(0 10px 18px rgba(0, 0, 0, 0.24));
    }}

    .sbc-team-typeface {{
        color: var(--sbc-team-secondary);
        font-family: var(--sbc-team-font);
        font-size: clamp(2.4rem, 5.2vw, 5.35rem);
        font-weight: 900;
        line-height: 1.18;
        max-width: 100%;
        white-space: nowrap;
        overflow: visible;
        text-overflow: ellipsis;
        padding-bottom: 0.08em;
        text-shadow: 0 2px 14px rgba(0, 0, 0, 0.20);
    }}

    .sbc-team-title {{
        display: none;
    }}

    .sbc-team-subtitle {{
        margin-top: 0.5rem;
        font-size: 1rem;
        font-weight: 800;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}

    label,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label,
    [data-testid="stSelectbox"] label,
    [data-testid="stMultiSelect"] label,
    [data-testid="stNumberInput"] label {{
        color: var(--sbc-ink) !important;
        font-weight: 800 !important;
    }}

    div[data-baseweb="select"] > div {{
        min-height: 2.85rem;
        border-radius: 8px !important;
        border: 1px solid rgba(23, 32, 42, 0.16) !important;
        background: #ffffff !important;
        box-shadow: 0 8px 22px rgba(18, 25, 38, 0.08);
        align-items: center !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }}

    div[data-baseweb="select"] > div:hover,
    div[data-baseweb="select"] > div:focus-within {{
        border-color: var(--sbc-team-primary) !important;
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--sbc-team-primary) 18%, transparent), 0 10px 26px rgba(18, 25, 38, 0.10);
    }}

    div[data-baseweb="select"] *,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] div {{
        font-weight: 800;
        color: var(--sbc-ink) !important;
        line-height: 1.2 !important;
    }}

    div[data-baseweb="select"] svg {{
        fill: var(--sbc-ink) !important;
        color: var(--sbc-ink) !important;
    }}

    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] input,
    [data-testid="stDateInput"] input {{
        color: var(--sbc-ink) !important;
        background: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid rgba(23, 32, 42, 0.16) !important;
        box-shadow: 0 8px 22px rgba(18, 25, 38, 0.08);
        min-height: 3.15rem;
    }}

    [data-testid="stNumberInput"] input:focus,
    [data-testid="stTextInput"] input:focus,
    [data-testid="stDateInput"] input:focus {{
        border-color: var(--sbc-team-primary) !important;
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--sbc-team-primary) 18%, transparent), 0 10px 26px rgba(18, 25, 38, 0.10);
    }}

    div[data-baseweb="popover"] {{
        border-radius: 8px !important;
        overflow: hidden;
        box-shadow: 0 18px 42px rgba(18, 25, 38, 0.18) !important;
    }}

    div[data-baseweb="menu"] {{
        background: #ffffff !important;
        color: var(--sbc-ink) !important;
    }}

    div[data-baseweb="option"],
    div[data-baseweb="option"] * {{
        color: var(--sbc-ink) !important;
        font-weight: 750 !important;
    }}

    div[data-baseweb="option"]:hover,
    div[data-baseweb="option"][aria-selected="true"] {{
        background: color-mix(in srgb, var(--sbc-team-primary) 12%, #ffffff) !important;
    }}

    [data-baseweb="tag"] {{
        background: color-mix(in srgb, var(--sbc-team-primary) 14%, #ffffff) !important;
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 26%, #ffffff) !important;
        border-radius: 7px !important;
        color: var(--sbc-ink) !important;
    }}

    [data-baseweb="tag"] span {{
        color: var(--sbc-ink) !important;
        font-weight: 800 !important;
    }}

    .sbc-cap-page-title {{
        margin: 0.45rem 0 1rem;
        padding-bottom: 0.65rem;
        border-bottom: 3px solid color-mix(in srgb, var(--sbc-team-primary) 56%, rgba(23, 32, 42, 0.10));
    }}

    .sbc-cap-eyebrow {{
        color: var(--sbc-team-primary);
        font-size: 0.98rem;
        font-weight: 950;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }}

    .sbc-cap-heading {{
        margin-top: 0.2rem;
        color: var(--sbc-ink);
        font-size: clamp(1.65rem, 3vw, 2.65rem);
        font-weight: 950;
        line-height: 1;
    }}

    .sbc-cap-subcopy {{
        margin-top: 0.45rem;
        color: var(--sbc-muted);
        font-size: 0.96rem;
        font-weight: 700;
    }}

    .sbc-section-label {{
        display: flex;
        align-items: center;
        gap: 0.55rem;
        margin: 1.1rem 0 0.55rem;
        color: var(--sbc-ink);
        font-size: 1.28rem;
        font-weight: 950;
        line-height: 1;
    }}

    .sbc-section-label::before {{
        content: "";
        width: 0.45rem;
        height: 1.25rem;
        border-radius: 3px;
        background: var(--sbc-team-primary);
    }}

    .sbc-mini-note,
    .sbc-empty-state {{
        border: 1px solid rgba(23, 32, 42, 0.10);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.78);
        color: var(--sbc-muted);
        font-size: 0.92rem;
        font-weight: 700;
        line-height: 1.35;
        padding: 0.85rem 0.95rem;
        box-shadow: 0 10px 28px rgba(18, 25, 38, 0.05);
    }}

    .sbc-legend {{
        border: 1px solid rgba(23, 32, 42, 0.10);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 12px 32px rgba(18, 25, 38, 0.07);
        padding: 0.72rem 0.95rem;
        margin-bottom: 0.65rem;
    }}

    .sbc-legend-title {{
        color: var(--sbc-ink);
        font-size: 0.9rem;
        font-weight: 950;
        margin-bottom: 0.65rem;
    }}

    .sbc-legend-row {{
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        color: var(--sbc-ink);
        font-size: 0.86rem;
        font-weight: 750;
        margin: 0.28rem 1.1rem 0.28rem 0;
    }}

    .sbc-legend-row span {{
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        margin-right: 0.8rem;
        white-space: nowrap;
    }}

    .sbc-legend-row i {{
        width: 1.25rem;
        height: 0.82rem;
        border: 1px solid rgba(23, 32, 42, 0.12);
        border-radius: 4px;
        display: inline-block;
        flex: 0 0 auto;
    }}

    .sbc-swatch {{
        width: 1.25rem;
        height: 0.82rem;
        border-radius: 4px;
        border: 1px solid rgba(23, 32, 42, 0.12);
        flex: 0 0 auto;
    }}

    .sbc-table-wrap {{
        width: 100%;
        max-width: 100%;
        overflow-x: auto;
        border: 1px solid rgba(23, 32, 42, 0.10);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 8px 20px rgba(18, 25, 38, 0.055);
        margin: 0.25rem 0 0.38rem;
    }}

    .sbc-cap-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.84rem;
        line-height: 1.22;
        color: var(--sbc-ink);
    }}

    .sbc-cap-table thead th {{
        position: sticky;
        top: 0;
        z-index: 1;
        background: #f7f9fc;
        color: var(--sbc-ink);
        border-bottom: 1px solid rgba(23, 32, 42, 0.12);
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.06em;
        padding: 0.62rem 0.7rem;
        text-align: center;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-cap-table tbody td {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.07);
        padding: 0.42rem 0.54rem;
        vertical-align: middle;
        font-weight: 650;
        white-space: nowrap;
        text-align: center;
    }}

    .sbc-cap-table tbody tr[style*="--row-team-color"] td {{
        background-color: color-mix(in srgb, var(--row-team-color) 5%, #ffffff);
    }}

    .sbc-cap-table tbody tr:nth-child(even) td {{
        background-color: rgba(247, 249, 252, 0.55);
    }}

    .sbc-cap-table tbody tr:nth-child(even)[style*="--row-team-color"] td {{
        background-color: color-mix(in srgb, var(--row-team-color) 7%, #ffffff);
    }}

    .sbc-cap-table tbody tr:hover td {{
        background-color: color-mix(in srgb, var(--sbc-team-primary) 8%, #ffffff);
    }}

    .sbc-cap-table tbody tr:last-child td {{
        border-bottom: none;
    }}

    .sbc-money-cell {{
        text-align: center;
        font-variant-numeric: tabular-nums;
        font-weight: 800 !important;
    }}

    .sbc-player-col,
    .sbc-player-cell {{
        text-align: left !important;
        min-width: 9.25rem;
    }}

    .sbc-year-col {{
        width: 7.25rem;
        min-width: 7.25rem;
        max-width: 7.25rem;
    }}

    .sbc-image-cell {{
        width: 3.9rem;
        min-width: 3.9rem;
        text-align: center;
    }}

    .sbc-table-img {{
        width: 3.2rem;
        height: 3.2rem;
        object-fit: cover;
        object-position: center 18%;
        border-radius: 50%;
        display: block;
        margin: 0 auto;
        background: #eef2f6;
        border: 2px solid #ffffff;
        box-shadow: 0 0 0 1px rgba(23, 32, 42, 0.14), 0 4px 10px rgba(18, 25, 38, 0.12);
    }}

    .sbc-team-logo-img {{
        width: 3.05rem;
        height: 3.05rem;
        object-fit: contain;
        display: block;
        margin: 0 auto;
        filter: drop-shadow(0 4px 8px rgba(18, 25, 38, 0.13));
    }}

    .sbc-draft-hero {{
        position: relative;
        overflow: hidden;
        margin: 0.35rem 0 0.95rem;
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 24%, rgba(255, 255, 255, 0.82));
        border-radius: 8px;
        background:
            linear-gradient(135deg, color-mix(in srgb, var(--sbc-team-primary) 88%, #111827 12%) 0%, color-mix(in srgb, var(--sbc-team-secondary) 70%, #111827 30%) 100%);
        color: var(--sbc-team-text);
        box-shadow: 0 22px 55px rgba(18, 25, 38, 0.18);
        padding: 1.15rem 1.25rem;
    }}

    .sbc-draft-hero::after {{
        content: "";
        position: absolute;
        inset: auto -4rem -7rem auto;
        width: 18rem;
        height: 18rem;
        border: 1.35rem solid rgba(255, 255, 255, 0.11);
        border-radius: 999px;
    }}

    .sbc-draft-hero-inner {{
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 1.05rem;
        align-items: center;
    }}

    .sbc-draft-logo {{
        width: 5.25rem;
        height: 5.25rem;
        object-fit: contain;
        filter: drop-shadow(0 10px 16px rgba(0, 0, 0, 0.28));
    }}

    .sbc-draft-eyebrow {{
        color: rgba(255, 255, 255, 0.82);
        font-size: 0.76rem;
        font-weight: 950;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }}

    .sbc-draft-heading {{
        margin-top: 0.18rem;
        color: #ffffff;
        font-family: var(--sbc-team-font);
        font-size: clamp(2rem, 4.5vw, 4rem);
        font-weight: 950;
        line-height: 1.08;
        padding-bottom: 0.06em;
        text-shadow: 0 2px 16px rgba(0, 0, 0, 0.24);
    }}

    .sbc-team-branded {{
        --sbc-team-primary: var(--sbc-selected-primary);
        --sbc-team-secondary: var(--sbc-selected-secondary);
        --sbc-team-text: var(--sbc-selected-text);
        --sbc-team-font: var(--sbc-selected-font);
    }}

    .sbc-league-hero {{
        --sbc-team-primary: {LEAGUE_PRIMARY};
        --sbc-team-secondary: {LEAGUE_SECONDARY};
        --sbc-team-text: #ffffff;
        --sbc-team-font: "{league_font_css}", "Poppins", sans-serif;
        border-color: color-mix(in srgb, {LEAGUE_PRIMARY} 24%, rgba(255, 255, 255, 0.82));
        background: linear-gradient(135deg, color-mix(in srgb, {LEAGUE_PRIMARY} 90%, #111827 10%) 0%, color-mix(in srgb, {LEAGUE_SECONDARY} 76%, #111827 24%) 100%);
    }}

    .sbc-league-hero .sbc-draft-heading {{
        font-family: "{league_font_css}", "Poppins", sans-serif;
        letter-spacing: 0;
    }}

    .sbc-draft-subcopy {{
        max-width: 52rem;
        color: rgba(255, 255, 255, 0.88);
        font-size: 0.96rem;
        font-weight: 750;
        line-height: 1.35;
    }}

    .sbc-draft-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 0.85rem 0 1rem;
    }}

    .sbc-draft-tile {{
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 28%, rgba(23, 32, 42, 0.10));
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.86);
        box-shadow: 0 12px 28px rgba(18, 25, 38, 0.075);
        padding: 0.86rem 0.9rem;
        min-height: 6.2rem;
    }}

    .sbc-draft-tile-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.65rem;
    }}

    .sbc-draft-tile-icon {{
        width: 2.35rem;
        height: 2.35rem;
        display: grid;
        place-items: center;
        border-radius: 8px;
        background: color-mix(in srgb, var(--sbc-team-primary) 14%, #ffffff);
        color: var(--sbc-team-primary);
        font-size: 1.15rem;
        font-weight: 950;
    }}

    .sbc-draft-tile-value {{
        color: var(--sbc-ink);
        font-size: 1.75rem;
        font-weight: 950;
        line-height: 1;
    }}

    .sbc-draft-tile-label {{
        margin-top: 0.72rem;
        color: var(--sbc-ink);
        font-size: 0.86rem;
        font-weight: 900;
        line-height: 1.15;
    }}

    .sbc-draft-tile-note {{
        margin-top: 0.25rem;
        color: var(--sbc-muted);
        font-size: 0.76rem;
        font-weight: 750;
        line-height: 1.25;
    }}

    .sbc-pick-panel {{
        overflow: hidden;
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 22%, rgba(23, 32, 42, 0.11));
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.08);
        margin: 0 0 0.9rem;
    }}

    .sbc-pick-panel-head {{
        display: grid;
        grid-template-columns: auto 1fr auto;
        gap: 0.8rem;
        align-items: center;
        border-bottom: 1px solid rgba(23, 32, 42, 0.08);
        background:
            linear-gradient(90deg, color-mix(in srgb, var(--sbc-team-primary) 12%, #ffffff) 0%, rgba(255, 255, 255, 0.88) 100%);
        padding: 0.78rem 0.9rem;
    }}

    .sbc-pick-icon {{
        width: 2.5rem;
        height: 2.5rem;
        display: grid;
        place-items: center;
        border-radius: 8px;
        background: var(--sbc-team-primary);
        color: var(--sbc-team-text);
        font-size: 1.18rem;
        font-weight: 950;
        box-shadow: 0 8px 18px color-mix(in srgb, var(--sbc-team-primary) 28%, transparent);
    }}

    .sbc-pick-title {{
        color: var(--sbc-ink);
        font-size: 1.22rem;
        font-weight: 950;
        line-height: 1.05;
    }}

    .sbc-pick-copy {{
        margin-top: 0.24rem;
        color: var(--sbc-muted);
        font-size: 0.78rem;
        font-weight: 750;
        line-height: 1.25;
    }}

    .sbc-pick-count {{
        min-width: 2.65rem;
        height: 2.25rem;
        display: grid;
        place-items: center;
        border-radius: 8px;
        background: #ffffff;
        border: 1px solid rgba(23, 32, 42, 0.10);
        color: var(--sbc-ink);
        font-size: 1.2rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
    }}

    .sbc-pick-table-wrap {{
        width: 100%;
        overflow-x: auto;
        background: #ffffff;
    }}

    .sbc-pick-table {{
        width: 100%;
        table-layout: fixed;
        border-collapse: separate;
        border-spacing: 0;
        color: var(--sbc-ink);
        font-size: 0.84rem;
        line-height: 1.25;
    }}

    .sbc-pick-table thead th {{
        background: #f7f9fc;
        border-bottom: 1px solid rgba(23, 32, 42, 0.11);
        color: var(--sbc-ink);
        font-size: 0.86rem;
        font-weight: 950;
        letter-spacing: 0.07em;
        padding: 0.62rem 0.68rem;
        text-align: center;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-pick-table tbody td {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.065);
        color: var(--sbc-ink);
        font-weight: 700;
        padding: 0.48rem 0.68rem;
        text-align: center;
        vertical-align: middle;
        white-space: nowrap;
    }}

    .sbc-pick-table tbody tr:nth-child(even) td {{
        background: rgba(247, 249, 252, 0.62);
    }}

    .sbc-pick-table tbody tr:hover td {{
        background: color-mix(in srgb, var(--sbc-team-primary) 8%, #ffffff);
    }}

    .sbc-pick-table tbody tr:last-child td {{
        border-bottom: none;
    }}

    .sbc-pick-year-row td {{
        background: color-mix(in srgb, var(--sbc-team-primary) 14%, #ffffff) !important;
        border-bottom: 1px solid color-mix(in srgb, var(--sbc-team-primary) 20%, rgba(23, 32, 42, 0.08)) !important;
        padding: 0.52rem 0.72rem !important;
        text-align: left !important;
    }}

    .sbc-pick-year-row span {{
        display: inline-flex;
        align-items: center;
        min-height: 1.65rem;
        border-radius: 999px;
        background: var(--sbc-team-primary);
        color: var(--sbc-team-text);
        font-size: 0.78rem;
        font-weight: 950;
        letter-spacing: 0.04em;
        padding: 0.18rem 0.75rem;
    }}

    .sbc-pick-logo-col {{
        width: 4.1rem;
        min-width: 4.1rem;
        max-width: 4.1rem;
        text-align: center !important;
    }}

    .sbc-pick-logo {{
        width: 2.35rem;
        height: 2.35rem;
        display: block;
        object-fit: contain;
        margin: 0 auto;
        filter: drop-shadow(0 4px 8px rgba(18, 25, 38, 0.13));
    }}


    .sbc-pick-slot-cell {{
        width: 12.75rem;
        min-width: 12.75rem;
        max-width: 12.75rem;
        text-align: left !important;
    }}

    .sbc-pick-slot-team {{
        color: var(--sbc-ink);
        display: inline-block;
        font-family: var(--slot-font), "Poppins", sans-serif;
        font-size: 1.02rem;
        font-weight: 950;
        line-height: 1.05;
        overflow-wrap: anywhere;
        text-align: left;
        text-shadow: none;
        white-space: nowrap;
    }}

    .sbc-pick-logo-cluster {{
        display: flex;
        align-items: center;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.35rem;
    }}

    .sbc-pick-logo-chip {{
        display: inline-grid;
        justify-items: center;
        align-items: center;
        gap: 0.18rem;
    }}

    .sbc-pick-logo-chip span {{
        color: var(--sbc-muted);
        font-size: 0.72rem;
        font-weight: 950;
        line-height: 1.05;
        text-align: center;
    }}

    .sbc-pick-year-cell {{
        font-size: 0.92rem;
        font-weight: 950 !important;
        font-variant-numeric: tabular-nums;
    }}

    .sbc-pick-round-col,
    .sbc-pick-round-cell {{
        width: 3.15rem;
        min-width: 3.15rem;
        max-width: 3.15rem;
        font-weight: 850 !important;
        text-align: center !important;
    }}

    .sbc-pick-contact-col,
    .sbc-pick-contact-cell {{
        width: 15.75rem;
        min-width: 15.75rem;
        max-width: 15.75rem;
        text-align: center !important;
        white-space: normal !important;
    }}

    .sbc-round-badge {{
        display: inline-grid;
        place-items: center;
        width: 2rem;
        height: 2rem;
        border-radius: 999px;
        background: color-mix(in srgb, var(--sbc-team-primary) 16%, #ffffff);
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 32%, rgba(23, 32, 42, 0.10));
        color: var(--sbc-ink);
        font-size: 0.86rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
    }}

    .sbc-pick-detail-col,
    .sbc-pick-detail-cell {{
        width: 34rem;
        min-width: 34rem;
        text-align: left !important;
        white-space: normal !important;
    }}

    .sbc-pick-empty {{
        padding: 0.9rem;
        color: var(--sbc-muted);
        font-size: 0.9rem;
        font-weight: 750;
        line-height: 1.35;
        background: #ffffff;
    }}

    .sbc-live-controls {{
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 24%, rgba(23, 32, 42, 0.11));
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.08);
        padding: 0.9rem 1rem 1rem;
        margin-bottom: 0.9rem;
    }}

    .sbc-live-control-title {{
        color: var(--sbc-ink);
        font-size: 0.95rem;
        font-weight: 950;
        line-height: 1.1;
        margin-bottom: 0.2rem;
    }}

    .sbc-live-control-copy {{
        color: var(--sbc-muted);
        font-size: 0.78rem;
        font-weight: 750;
        line-height: 1.3;
        margin-bottom: 0.75rem;
    }}

    .sbc-live-summary {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0 0 1rem;
    }}

    .sbc-live-pill {{
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 24%, rgba(23, 32, 42, 0.10));
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.88);
        box-shadow: 0 10px 24px rgba(18, 25, 38, 0.06);
        padding: 0.78rem 0.85rem;
    }}

    .sbc-live-pill-label {{
        color: var(--sbc-muted);
        font-size: 0.72rem;
        font-weight: 900;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }}

    .sbc-live-pill-value {{
        color: var(--sbc-ink);
        font-size: 1.45rem;
        font-weight: 950;
        line-height: 1;
        margin-top: 0.28rem;
        font-variant-numeric: tabular-nums;
    }}

    .sbc-live-card {{
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 22%, rgba(23, 32, 42, 0.11));
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.93);
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.08);
        padding: 0.85rem 0.9rem 0.95rem;
        margin-bottom: 0.95rem;
    }}

    .sbc-live-card-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        margin-bottom: 0.65rem;
    }}

    .sbc-live-card-title {{
        color: var(--sbc-ink);
        font-size: 1rem;
        font-weight: 950;
        line-height: 1.1;
    }}

    .sbc-live-card-kicker {{
        color: var(--sbc-team-primary);
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }}

    .sbc-live-badge {{
        border-radius: 999px;
        background: color-mix(in srgb, var(--sbc-team-primary) 14%, #ffffff);
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 28%, rgba(23, 32, 42, 0.10));
        color: var(--sbc-ink);
        font-size: 0.76rem;
        font-weight: 900;
        line-height: 1;
        padding: 0.38rem 0.65rem;
        white-space: nowrap;
    }}

    .sbc-live-board {{
        overflow: hidden;
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 24%, rgba(23, 32, 42, 0.11));
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 12px 28px rgba(18, 25, 38, 0.07);
        margin: 0 0 1rem;
    }}

    .sbc-live-board-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        min-height: 4.55rem;
        border-bottom: 1px solid rgba(23, 32, 42, 0.08);
        background:
            linear-gradient(90deg, color-mix(in srgb, var(--sbc-team-primary) 12%, #ffffff) 0%, rgba(255, 255, 255, 0.92) 100%);
        padding: 0.82rem 0.95rem;
    }}

    .sbc-live-board-grid {{
        display: grid;
        grid-template-columns: minmax(10rem, 1.2fr) repeat(var(--sbc-live-team-cols), minmax(6rem, 0.85fr));
        width: 100%;
    }}

    .sbc-live-team-spacer,
    .sbc-live-team-head {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.08);
        background: #f7f9fc;
        height: 5.65rem;
        min-height: 5.65rem;
    }}

    .sbc-live-team-head {{
        display: grid;
        justify-items: center;
        grid-template-rows: 2.35rem 2.1rem;
        align-items: center;
        gap: 0.32rem;
        border-left: 1px solid rgba(23, 32, 42, 0.07);
        color: var(--sbc-ink);
        font-size: 0.78rem;
        font-weight: 950;
        line-height: 1.05;
        padding: 0.56rem 0.5rem;
        text-align: center;
    }}

    .sbc-live-logo {{
        width: 2.35rem;
        height: 2.35rem;
        object-fit: contain;
        filter: drop-shadow(0 4px 8px rgba(18, 25, 38, 0.14));
    }}

    .sbc-live-team-head span {{
        display: -webkit-box;
        max-width: 100%;
        min-height: 2.1em;
        overflow: hidden;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        word-break: normal;
    }}

    .sbc-live-stat-row {{
        display: contents;
    }}

    .sbc-live-stat-name,
    .sbc-live-stat-value,
    .sbc-live-total-name,
    .sbc-live-total-value {{
        box-sizing: border-box;
        border-bottom: 1px solid rgba(23, 32, 42, 0.065);
        height: 3.55rem;
        min-height: 3.55rem;
        overflow: hidden;
        padding: 0.48rem 0.68rem;
    }}

    .sbc-live-stat-name,
    .sbc-live-total-name {{
        display: grid;
        align-content: center;
        background: rgba(247, 249, 252, 0.68);
        color: var(--sbc-ink);
    }}

    .sbc-live-stat-name span,
    .sbc-live-total-name span {{
        display: -webkit-box;
        overflow: hidden;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        font-size: 0.88rem;
        font-weight: 950;
        line-height: 1.05;
    }}

    .sbc-live-stat-name em,
    .sbc-live-total-name em {{
        margin-top: 0.18rem;
        color: var(--sbc-muted);
        font-size: 0.69rem;
        font-style: normal;
        font-weight: 850;
        letter-spacing: 0.04em;
        line-height: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-live-stat-value {{
        display: grid;
        place-items: center;
        align-content: center;
        border-left: 1px solid rgba(23, 32, 42, 0.06);
        color: var(--sbc-ink);
        font-size: 0.98rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
        text-align: center;
    }}

    .sbc-live-stat-value span {{
        display: block;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1;
        white-space: nowrap;
    }}

    .sbc-live-stat-value em {{
        margin-top: 0.22rem;
        color: #4b5563;
        font-size: 0.66rem;
        font-style: normal;
        font-weight: 900;
        letter-spacing: 0.04em;
        line-height: 1;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-live-total-name,
    .sbc-live-total-value {{
        background: #111827;
        color: #ffffff;
        border-bottom: none;
        height: 3.75rem;
        min-height: 3.75rem;
    }}

    .sbc-live-total-name em {{
        color: rgba(255, 255, 255, 0.68);
    }}

    .sbc-live-total-value {{
        display: grid;
        place-items: center;
        border-left: 1px solid rgba(255, 255, 255, 0.12);
        font-size: 1.18rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
    }}

    .sbc-live-total-leader {{
        background: var(--sbc-team-primary);
        color: var(--sbc-team-text);
        box-shadow: inset 0 0 0 2px color-mix(in srgb, var(--sbc-team-secondary) 52%, #ffffff);
    }}

    .sbc-live-total-tie {{
        background: #e6c85c;
        color: #3f3000;
        box-shadow: inset 0 0 0 2px rgba(63, 48, 0, 0.18);
    }}

    .sbc-live-total-value span {{
        line-height: 1;
    }}

    .sbc-live-total-value em {{
        margin-top: 0.18rem;
        font-size: 0.58rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.06em;
        line-height: 1;
        text-transform: uppercase;
    }}

    .sbc-live-stat-win {{
        background: color-mix(in srgb, #58a76b 22%, #ffffff);
        color: #163c21;
    }}

    .sbc-live-stat-tie {{
        background: color-mix(in srgb, #e6c85c 30%, #ffffff);
        color: #4d3a00;
    }}

    .sbc-live-stat-trail {{
        background: color-mix(in srgb, #d96b6b 15%, #ffffff);
        color: #582020;
    }}

    .sbc-live-stat-neutral {{
        background: #ffffff;
    }}

    .sbc-chart-shell {{
        border: 1px solid rgba(23, 32, 42, 0.10);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 10px 28px rgba(18, 25, 38, 0.06);
        padding: 0.9rem 1rem 1rem;
        margin-top: 0.1rem;
    }}

    .sbc-chart-head {{
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 0.75rem;
    }}

    .sbc-chart-title {{
        color: var(--sbc-ink);
        font-size: 1.05rem;
        font-weight: 950;
        line-height: 1.1;
    }}

    .sbc-chart-copy {{
        color: var(--sbc-muted);
        font-size: 0.78rem;
        font-weight: 750;
        line-height: 1.3;
        margin-top: 0.24rem;
    }}

    .sbc-schedule-table-wrap {{
        overflow: hidden;
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 22%, rgba(23, 32, 42, 0.12));
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 16px 38px rgba(18, 25, 38, 0.09);
        margin: 0.4rem 0 1.2rem;
    }}

    .sbc-schedule-list {{
        display: grid;
        gap: 0.55rem;
        margin: 0.4rem 0 1.2rem;
    }}

    .sbc-schedule-group-card {{
        margin-top: 0.35rem;
    }}

    .sbc-schedule-group-card span {{
        display: inline-flex;
        align-items: center;
        min-height: 1.65rem;
        border-radius: 999px;
        background: var(--sbc-team-primary);
        color: var(--sbc-team-text);
        font-size: 0.78rem;
        font-weight: 950;
        letter-spacing: 0.04em;
        padding: 0.18rem 0.75rem;
        text-transform: uppercase;
    }}

    .sbc-schedule-card {{
        display: grid;
        grid-template-columns: minmax(7.5rem, auto) minmax(0, 1fr) minmax(6rem, auto);
        gap: 0.75rem;
        align-items: center;
        border: 1px solid rgba(23,32,42,0.10);
        border-left: 0.42rem solid var(--sbc-opponent-color);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 10px 24px rgba(18,25,38,0.065);
        min-height: 4.25rem;
        padding: 0.62rem 0.75rem 0.62rem 0.55rem;
    }}

    .sbc-schedule-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }}

    .sbc-schedule-table th {{
        background: #111827;
        color: #ffffff;
        font-size: 0.86rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        padding: 0.78rem 0.85rem;
        text-align: left;
        text-transform: uppercase;
    }}

    .sbc-schedule-table th:nth-child(1) {{ width: 9.25rem; }}
    .sbc-schedule-table th:nth-child(3) {{ width: 8.5rem; text-align: center; }}

    .sbc-schedule-row {{
        border-left: 0.42rem solid var(--sbc-opponent-color);
    }}

    .sbc-schedule-row td {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.075);
        color: var(--sbc-ink);
        height: 4.25rem;
        padding: 0.68rem 0.85rem;
        vertical-align: middle;
    }}

    .sbc-schedule-row:last-child td {{ border-bottom: none; }}

    .sbc-schedule-group-row td {{
        background: color-mix(in srgb, var(--sbc-team-primary) 14%, #ffffff);
        border-bottom: 1px solid color-mix(in srgb, var(--sbc-team-primary) 20%, rgba(23, 32, 42, 0.08));
        color: var(--sbc-ink);
        padding: 0.52rem 0.72rem;
    }}

    .sbc-schedule-group-row span {{
        display: inline-flex;
        align-items: center;
        min-height: 1.65rem;
        border-radius: 999px;
        background: var(--sbc-team-primary);
        color: var(--sbc-team-text);
        font-size: 0.78rem;
        font-weight: 950;
        letter-spacing: 0.04em;
        padding: 0.18rem 0.75rem;
        text-transform: uppercase;
    }}

    .sbc-schedule-period span {{
        display: inline-grid;
        place-items: center;
        min-width: 7rem;
        height: 2.1rem;
        padding: 0 0.62rem;
        border-radius: 999px;
        background: color-mix(in srgb, var(--sbc-team-primary) 16%, #ffffff);
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 30%, rgba(23, 32, 42, 0.12));
        color: var(--sbc-ink);
        font-size: 0.78rem;
        font-weight: 950;
    }}

    .sbc-schedule-opponent {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        min-width: 0;
    }}

    .sbc-schedule-logo {{
        width: 2.35rem;
        height: 2.35rem;
        flex: 0 0 2.35rem;
        object-fit: contain;
        filter: drop-shadow(0 4px 8px rgba(18, 25, 38, 0.13));
    }}

    .sbc-schedule-opponent strong {{
        display: block;
        overflow: hidden;
        color: #111827;
        font-family: "Poppins", "Segoe UI", sans-serif;
        font-size: 0.98rem;
        font-weight: 950;
        line-height: 1.08;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-schedule-opponent em {{
        display: none;
        margin-top: 0.2rem;
        overflow: hidden;
        color: var(--sbc-muted);
        font-size: 0.7rem;
        font-style: normal;
        font-weight: 800;
        letter-spacing: 0.04em;
        text-overflow: ellipsis;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-schedule-score {{ text-align: center; }}

    .sbc-schedule-score strong {{
        display: block;
        color: var(--sbc-ink);
        font-size: 1rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
        line-height: 1;
    }}

    .sbc-schedule-score em {{
        display: inline-grid;
        place-items: center;
        min-width: 2rem;
        margin-top: 0.24rem;
        border-radius: 999px;
        background: #edf1f5;
        color: #344054;
        font-size: 0.62rem;
        font-style: normal;
        font-weight: 950;
        line-height: 1;
        padding: 0.25rem 0.42rem;
    }}

    .sbc-schedule-win .sbc-schedule-score em {{
        background: color-mix(in srgb, #58a76b 24%, #ffffff);
        color: #174221;
    }}

    .sbc-schedule-loss .sbc-schedule-score em {{
        background: color-mix(in srgb, #d96b6b 20%, #ffffff);
        color: #651f1f;
    }}

    .sbc-schedule-tie .sbc-schedule-score em {{
        background: color-mix(in srgb, #e6c85c 34%, #ffffff);
        color: #4d3a00;
    }}

    .sbc-scoreboard-wrap {{
        display: grid;
        gap: 1rem;
        margin: 0.45rem 0 1.2rem;
    }}

    .sbc-score-group {{
        overflow: hidden;
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 22%, rgba(23, 32, 42, 0.12));
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 16px 38px rgba(18, 25, 38, 0.09);
    }}

    .sbc-score-group-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        border-bottom: 1px solid rgba(23, 32, 42, 0.08);
        background:
            linear-gradient(90deg, color-mix(in srgb, var(--sbc-team-primary) 16%, #ffffff) 0%, #ffffff 100%);
        padding: 0.78rem 0.9rem;
    }}

    .sbc-score-group-head span {{
        color: var(--sbc-ink);
        font-size: 0.96rem;
        font-weight: 950;
        line-height: 1.1;
    }}

    .sbc-score-group-head em {{
        border-radius: 999px;
        background: var(--sbc-team-primary);
        color: var(--sbc-team-text);
        font-size: 0.68rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.06em;
        padding: 0.32rem 0.58rem;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-score-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.72rem;
        padding: 0.82rem;
    }}

    .sbc-score-card {{
        overflow: hidden;
        border: 1px solid rgba(23, 32, 42, 0.10);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 10px 24px rgba(18, 25, 38, 0.06);
    }}

    .sbc-score-card-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.7rem;
        min-height: 2.25rem;
        background: #111827;
        color: #ffffff;
        padding: 0.45rem 0.58rem;
    }}

    .sbc-score-card-top span,
    .sbc-score-card-top em {{
        overflow: hidden;
        font-size: 0.66rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.08em;
        line-height: 1;
        text-overflow: ellipsis;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-score-card-top em {{
        color: rgba(255, 255, 255, 0.72);
    }}

    .sbc-score-team {{
        display: grid;
        grid-template-columns: 2.45rem minmax(0, 1fr) auto;
        gap: 0.58rem;
        align-items: center;
        min-height: 4.25rem;
        border-left: 0.34rem solid var(--score-color);
        border-bottom: 1px solid rgba(23, 32, 42, 0.075);
        background:
            linear-gradient(90deg, color-mix(in srgb, var(--score-color) 9%, #ffffff) 0%, #ffffff 52%);
        padding: 0.58rem 0.68rem 0.58rem 0.54rem;
    }}

    .sbc-score-team:last-child {{
        border-bottom: none;
    }}

    .sbc-score-team img {{
        width: 2.35rem;
        height: 2.35rem;
        object-fit: contain;
        filter: drop-shadow(0 4px 8px rgba(18, 25, 38, 0.13));
    }}

    .sbc-score-team strong {{
        display: block;
        overflow: hidden;
        color: var(--sbc-ink);
        font-size: 0.86rem;
        font-weight: 950;
        line-height: 1.08;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-score-team em {{
        display: block;
        margin-top: 0.2rem;
        overflow: hidden;
        color: var(--sbc-muted);
        font-size: 0.66rem;
        font-style: normal;
        font-weight: 850;
        letter-spacing: 0.04em;
        line-height: 1;
        text-overflow: ellipsis;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-score-team b {{
        color: var(--sbc-ink);
        font-size: 1.4rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
        line-height: 1;
        text-align: right;
    }}

    .sbc-score-winner {{
        background:
            linear-gradient(90deg, color-mix(in srgb, var(--score-color) 22%, #ffffff) 0%, #ffffff 58%);
    }}

    .sbc-score-winner b {{
        color: var(--sbc-ink);
    }}

    div[data-testid="stButton"] > button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"] p,
    div.stButton > button[kind="primary"],
    div.stButton > button[kind="primary"] p {{
        color: #ffffff !important;
    }}

    div[data-testid="stRadio"] {{
        display: inline-flex;
        align-items: center;
        border: 1px solid rgba(23,32,42,0.18);
        border-radius: 8px;
        background: #f8fafc;
        box-shadow: 0 8px 18px rgba(18,25,38,0.06);
        margin-top: 0.85rem;
        padding: 0.4rem 0.55rem;
    }}

    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] p {{
        color: var(--sbc-ink) !important;
        font-size: 0.86rem !important;
        font-weight: 950 !important;
    }}

    div[data-testid="stRadio"] [role="radiogroup"] {{
        gap: 0.35rem;
    }}

    div[data-testid="stRadio"] [role="radio"] {{
        border: 1px solid rgba(23,32,42,0.16);
        border-radius: 999px;
        background: #ffffff;
        padding: 0.22rem 0.58rem;
    }}

    div[data-testid="stRadio"] [role="radio"][aria-checked="true"] {{
        background: {LEAGUE_PRIMARY};
        color: #ffffff !important;
    }}

    div[data-testid="stDialog"] div[role="dialog"] {{
        width: min(96vw, 1420px) !important;
        max-width: min(96vw, 1420px) !important;
        background: #ffffff !important;
        color: var(--sbc-ink) !important;
    }}

    div[data-testid="stDialog"] div[role="dialog"] h1,
    div[data-testid="stDialog"] div[role="dialog"] h2,
    div[data-testid="stDialog"] div[role="dialog"] h3,
    div[data-testid="stDialog"] div[role="dialog"] [data-testid="stMarkdownContainer"] p {{
        color: var(--sbc-ink) !important;
    }}

    div[data-testid="stDialog"] button[aria-label="Close"],
    div[data-testid="stDialog"] button[title="Close"],
    div[data-testid="stDialog"] button[kind="header"] {{
        color: var(--sbc-ink) !important;
        background: #e5e7eb !important;
        border: 1px solid rgba(23,32,42,0.16) !important;
        border-radius: 999px !important;
    }}

    div[data-testid="stDialog"] button[aria-label="Close"] svg,
    div[data-testid="stDialog"] button[title="Close"] svg,
    div[data-testid="stDialog"] button[kind="header"] svg {{
        color: var(--sbc-ink) !important;
        fill: var(--sbc-ink) !important;
        stroke: var(--sbc-ink) !important;
    }}

    div[data-testid="stDialog"] div[role="dialog"] section {{
        background: #ffffff;
    }}

    .sbc-box-dialog-hero {{
        overflow: hidden;
        border: 1px solid rgba(23, 32, 42, 0.10);
        border-radius: 8px;
        background: #ffffff;
        color: var(--sbc-ink);
        box-shadow: 0 16px 36px rgba(18, 25, 38, 0.10);
    }}

    .sbc-box-dialog-kicker {{
        background: #111827;
        color: rgba(255,255,255,0.76);
        font-size: 0.7rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        padding: 0.5rem 0.75rem;
        text-transform: uppercase;
    }}

    .sbc-box-dialog-title {{
        padding: 0.82rem 0.9rem 0;
        color: var(--sbc-ink);
        font-size: 1.15rem;
        font-weight: 950;
        line-height: 1.05;
    }}

    .sbc-box-dialog-matchup {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(8rem, auto) minmax(0, 1fr);
        gap: 1rem;
        align-items: center;
        padding: 0.85rem 1rem 1rem;
    }}

    .sbc-box-dialog-team {{
        display: grid;
        grid-template-columns: 4.2rem minmax(0, 1fr) auto;
        gap: 0.72rem;
        align-items: center;
        min-width: 0;
        border-radius: 8px;
        background:
            linear-gradient(135deg, color-mix(in srgb, var(--box-team) 94%, #000000), color-mix(in srgb, var(--box-team-secondary) 76%, #111827));
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.18), 0 12px 26px rgba(18,25,38,0.14);
        padding: 0.78rem 0.85rem;
    }}

    .sbc-box-dialog-team-home {{
        grid-template-columns: auto minmax(0, 1fr) 4.2rem;
        text-align: right;
    }}

    .sbc-box-dialog-team img {{
        width: 4rem;
        height: 4rem;
        object-fit: contain;
        filter: drop-shadow(0 8px 13px rgba(0,0,0,0.30));
    }}

    .sbc-box-dialog-team strong {{
        display: block;
        overflow: hidden;
        color: #ffffff;
        font-family: var(--box-team-font), "Poppins", "Segoe UI", sans-serif;
        font-size: clamp(1.05rem, 1.55vw, 1.55rem);
        font-weight: 950;
        line-height: 1;
        text-shadow: 0 2px 8px rgba(0,0,0,0.28);
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-box-dialog-team em {{
        display: block;
        margin-top: 0.34rem;
        color: rgba(255,255,255,0.88);
        font-size: 0.82rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}

    .sbc-box-dialog-team b {{
        color: #ffffff;
        font-size: clamp(2.15rem, 4vw, 3.45rem);
        font-weight: 950;
        line-height: 0.9;
        text-shadow: 0 3px 10px rgba(0,0,0,0.34);
    }}

    .sbc-box-dialog-score-win {{
        text-decoration: underline;
        text-decoration-color: rgba(255,255,255,0.72);
        text-decoration-thickness: 0.12em;
        text-underline-offset: 0.12em;
    }}

    .sbc-box-dialog-score {{
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        border: 1px solid rgba(23,32,42,0.10);
        background: #ffffff;
        color: var(--sbc-ink);
        font-variant-numeric: tabular-nums;
        padding: 0.62rem 0.9rem;
        text-align: center;
    }}

    .sbc-box-dialog-score i {{
        color: var(--sbc-muted);
        font-size: 0.72rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .sbc-box-panel {{
        overflow: hidden;
        border: 1px solid rgba(23, 32, 42, 0.10);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 12px 28px rgba(18, 25, 38, 0.06);
        margin-top: 0.8rem;
    }}

    .sbc-box-category-panel {{
        width: 100%;
        max-width: none;
        margin-left: 0;
        margin-right: 0;
        background: #ffffff;
    }}

    .sbc-box-panel-head,
    .sbc-box-team-head {{
        display: flex;
        align-items: center;
        gap: 0.55rem;
        border-bottom: 1px solid rgba(23, 32, 42, 0.08);
        background: #f8fafc;
        color: var(--sbc-ink);
        font-size: 0.86rem;
        font-weight: 950;
        padding: 0.54rem 0.7rem;
    }}

    .sbc-box-team-head {{
        min-height: 4.35rem;
        border-left: 0;
        background:
            linear-gradient(135deg, color-mix(in srgb, var(--box-team-secondary) 88%, #111827), color-mix(in srgb, var(--box-team) 68%, #111827));
        color: #ffffff;
        padding: 0.72rem 0.85rem;
    }}

    .sbc-box-team-head img,
    .sbc-box-category-table th img {{
        width: 2.65rem;
        height: 2.65rem;
        object-fit: contain;
    }}

    .sbc-box-team-head img {{
        width: 2.8rem;
        height: 2.8rem;
        filter: drop-shadow(0 8px 12px rgba(0,0,0,0.28));
    }}

    .sbc-box-team-head span {{
        overflow: hidden;
        color: #ffffff;
        font-family: var(--box-team-font), "Poppins", "Segoe UI", sans-serif;
        font-size: clamp(1.05rem, 1.8vw, 1.55rem);
        font-weight: 950;
        line-height: 1;
        text-shadow: 0 2px 8px rgba(0,0,0,0.28);
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-box-category-table,
    .sbc-box-player-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        color: var(--sbc-ink);
        font-variant-numeric: tabular-nums;
    }}

    .sbc-box-category-table {{
        table-layout: fixed;
    }}

    .sbc-box-category-table th:nth-child(1),
    .sbc-box-category-table td:nth-child(1),
    .sbc-box-category-table th:nth-child(3),
    .sbc-box-category-table td:nth-child(3) {{
        width: 42%;
    }}

    .sbc-box-category-table th:nth-child(2),
    .sbc-box-category-table td:nth-child(2) {{
        width: 16%;
    }}

    .sbc-box-category-table th {{
        text-align: center;
    }}

    .sbc-box-category-team-name {{
        display: inline-block;
        max-width: 100%;
        overflow: hidden;
        font-size: clamp(1.05rem, 1.8vw, 1.55rem);
        font-weight: 950;
        line-height: 1;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-box-category-team-a {{
        color: color-mix(in srgb, var(--cat-a) 82%, #111827);
        font-family: var(--cat-font-a), "Poppins", "Segoe UI", sans-serif;
    }}

    .sbc-box-category-team-b {{
        color: color-mix(in srgb, var(--cat-b) 82%, #111827);
        font-family: var(--cat-font-b), "Poppins", "Segoe UI", sans-serif;
    }}

    .sbc-box-category-team-header {{
        padding-top: 0.7rem !important;
        padding-bottom: 0.7rem !important;
    }}

    .sbc-box-category-team-header-a {{
        background: color-mix(in srgb, var(--cat-a-secondary) 42%, #ffffff) !important;
    }}

    .sbc-box-category-team-header-b {{
        background: color-mix(in srgb, var(--cat-b-secondary) 42%, #ffffff) !important;
    }}

    .sbc-box-category-table th,
    .sbc-box-player-table th {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.08);
        background: #f3f5f8;
        color: var(--sbc-muted);
        font-size: 0.66rem;
        font-weight: 950;
        letter-spacing: 0.06em;
        padding: 0.36rem 0.5rem;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-box-category-table td,
    .sbc-box-player-table td {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.06);
        padding: 0.38rem 0.5rem;
        vertical-align: middle;
    }}

    .sbc-box-category-table td {{
        background: #f3f5f8;
    }}

    .sbc-box-stat-cell strong {{
        display: block;
        color: var(--sbc-ink);
        font-size: 0.88rem;
        font-weight: 950;
        line-height: 1;
    }}

    .sbc-box-stat-cell em,
    .sbc-box-category-name em,
    .sbc-box-player-cell em {{
        display: block;
        margin-top: 0.18rem;
        color: var(--sbc-muted);
        font-size: 0.6rem;
        font-style: normal;
        font-weight: 850;
        line-height: 1;
        white-space: nowrap;
    }}

    .sbc-box-stat-win {{
        background: color-mix(in srgb, #58a76b 26%, #ffffff) !important;
        box-shadow: inset 0 0 0 1px color-mix(in srgb, #58a76b 44%, transparent);
    }}

    .sbc-box-stat-tie {{
        background: color-mix(in srgb, #facc15 24%, #ffffff) !important;
        box-shadow: inset 0 0 0 1px color-mix(in srgb, #d4a90b 58%, transparent);
    }}

    .sbc-box-category-name {{
        text-align: center;
        background: #f3f5f8 !important;
    }}

    .sbc-box-category-name strong {{
        display: block;
        color: var(--sbc-ink);
        font-size: 0.82rem;
        font-weight: 950;
        line-height: 1;
    }}

    .sbc-box-section-title {{
        margin: 0.9rem 0 0.45rem;
        color: var(--sbc-ink);
        font-size: 0.95rem;
        font-weight: 950;
    }}

    .sbc-box-player-grid {{
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 0.8rem;
        align-items: start;
    }}

    .sbc-box-table-scroll {{
        overflow-x: auto;
    }}

    .sbc-box-player-table {{
        min-width: 54rem;
    }}

    .sbc-box-player-table th:first-child,
    .sbc-box-player-table td:first-child {{
        position: sticky;
        left: 0;
        z-index: 1;
        background: #ffffff;
    }}

    .sbc-box-player-table tr.sbc-box-game-date-row td {{
        position: static;
        z-index: 2;
        background: color-mix(in srgb, var(--box-team) 10%, #ffffff);
        color: color-mix(in srgb, var(--box-team) 72%, #111827);
        font-size: 0.68rem;
        font-weight: 950;
        letter-spacing: 0.07em;
        padding: 0.38rem 0.6rem;
        text-transform: uppercase;
    }}

    .sbc-box-player-cell {{
        display: grid;
        grid-template-columns: 2.35rem minmax(8rem, 1fr);
        gap: 0.5rem;
        align-items: center;
        min-width: 12rem;
    }}

    .sbc-box-player-cell img {{
        width: 2.25rem;
        height: 2.25rem;
        border-radius: 999px;
        background: #eef2f7;
        object-fit: cover;
    }}

    .sbc-box-player-cell strong {{
        display: block;
        overflow: hidden;
        color: var(--sbc-ink);
        font-size: 0.78rem;
        font-weight: 950;
        line-height: 1.08;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-pbp-panel {{
        border-color: rgba(23, 32, 42, 0.10);
    }}

    .sbc-pbp-chart-key {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.75rem;
        border: 0;
        border-radius: 0;
        background: #ffffff;
        margin: 0 0 0.35rem;
        padding: 0.15rem 0 0.45rem;
    }}

    .sbc-pbp-chart-key span {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border-radius: 999px;
        background: color-mix(in srgb, var(--chart-team-color) 12%, #ffffff);
        color: color-mix(in srgb, var(--chart-team-color) 72%, #111827);
        font-size: 0.7rem;
        font-weight: 950;
        padding: 0.3rem 0.55rem;
    }}

    .sbc-pbp-chart-key img {{
        width: 1.35rem;
        height: 1.35rem;
        object-fit: contain;
    }}

    .sbc-pbp-chart-key .sbc-pbp-chart-mid {{
        background: color-mix(in srgb, #C9A227 22%, #ffffff);
        color: #6b4f00;
    }}

    .sbc-pbp-mini-chart-title {{
        margin: 0.85rem 0 0.35rem;
        color: var(--sbc-ink);
        font-size: 0.86rem;
        font-weight: 950;
    }}

    .sbc-pbp-table {{
        min-width: 60rem;
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        color: var(--sbc-ink);
        font-variant-numeric: tabular-nums;
    }}

    .sbc-pbp-table th {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.08);
        background: #f3f5f8;
        color: var(--sbc-muted);
        font-size: 0.66rem;
        font-weight: 950;
        letter-spacing: 0.06em;
        padding: 0.42rem 0.55rem;
        text-align: center;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-pbp-table td {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.06);
        background: #ffffff;
        font-size: 0.76rem;
        font-weight: 850;
        padding: 0.46rem 0.55rem;
        text-align: center;
        vertical-align: middle;
    }}

    .sbc-pbp-table th:nth-child(2),
    .sbc-pbp-table td:nth-child(2) {{
        text-align: center;
    }}

    .sbc-pbp-table td:first-child {{
        width: 9.5rem;
        color: var(--sbc-muted);
        white-space: nowrap;
    }}

    .sbc-pbp-table td:nth-child(2),
    .sbc-pbp-table td:nth-child(4),
    .sbc-pbp-table td:nth-child(5),
    .sbc-pbp-table td:nth-child(6) {{
        white-space: nowrap;
    }}

    .sbc-pbp-description {{
        min-width: 28rem;
        color: var(--sbc-ink);
        font-weight: 850;
        line-height: 1.25;
        text-align: left !important;
        white-space: normal !important;
    }}

    .sbc-pbp-lead-change-row td {{
        background: color-mix(in srgb, #facc15 26%, #ffffff);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.55), inset 0 -1px 0 color-mix(in srgb, #facc15 38%, rgba(23, 32, 42, 0.06));
    }}

    .sbc-pbp-tied-row td {{
        background: color-mix(in srgb, #93c5fd 18%, #ffffff);
    }}

    .sbc-pbp-total-cell {{
        font-weight: 950 !important;
    }}

    .sbc-pbp-updated-total {{
        outline: 2px solid color-mix(in srgb, var(--pbp-active-color) 70%, #ffffff);
        outline-offset: -3px;
        background: color-mix(in srgb, var(--pbp-active-color) 11%, #ffffff) !important;
        color: var(--sbc-ink);
    }}

    .sbc-pbp-team-head {{
        display: inline-grid;
        grid-template-columns: 1.5rem auto;
        gap: 0.35rem;
        align-items: center;
        justify-content: center;
        min-width: 3.25rem;
    }}

    .sbc-pbp-team-head img,
    .sbc-pbp-leader-logo img {{
        width: 1.45rem;
        height: 1.45rem;
        object-fit: contain;
        filter: drop-shadow(0 2px 4px rgba(18,25,38,0.12));
    }}

    .sbc-pbp-team-head strong {{
        color: var(--sbc-ink);
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0;
    }}

    .sbc-pbp-leader-logo {{
        display: inline-grid;
        place-items: center;
    }}

    .sbc-pbp-tie-text {{
        display: inline-grid;
        place-items: center;
        border-radius: 999px;
        background: color-mix(in srgb, #93c5fd 26%, #ffffff);
        color: #1e3a8a;
        font-size: 0.66rem;
        font-weight: 950;
        padding: 0.22rem 0.42rem;
        white-space: nowrap;
    }}

    .sbc-player-profile-hero {{
        display: grid;
        grid-template-columns: 18rem minmax(0, 1fr) minmax(14rem, 0.5fr);
        gap: 1.25rem;
        align-items: center;
        width: 100%;
        max-width: 90rem;
        overflow: hidden;
        border: 1px solid color-mix(in srgb, {LEAGUE_PRIMARY} 34%, rgba(23,32,42,0.12));
        border-radius: 8px;
        background:
            linear-gradient(135deg, color-mix(in srgb, {LEAGUE_PRIMARY} 14%, #ffffff), #ffffff 45%, color-mix(in srgb, {LEAGUE_SECONDARY} 12%, #ffffff));
        box-shadow: 0 20px 48px rgba(18,25,38,0.12);
        margin: 0.9rem auto 1rem;
        padding: 1.15rem;
    }}

    .sbc-player-profile-hero-no-accolades {{
        grid-template-columns: 18rem minmax(0, 1fr);
    }}

    .sbc-player-profile-hero-current {{
        border-color: color-mix(in srgb, var(--profile-current-team-color) 36%, rgba(23,32,42,0.12));
        background:
            linear-gradient(135deg, color-mix(in srgb, var(--profile-current-team-color) 18%, #ffffff), #ffffff 44%, color-mix(in srgb, var(--profile-current-team-secondary) 18%, #ffffff));
        box-shadow: 0 20px 48px color-mix(in srgb, var(--profile-current-team-color) 16%, rgba(18,25,38,0.10));
    }}

    .sbc-player-profile-photo {{
        display: grid;
        place-items: end center;
        overflow: hidden;
        width: 18rem;
        height: 18rem;
        border-radius: 8px;
        background:
            radial-gradient(circle at 50% 18%, color-mix(in srgb, {LEAGUE_SECONDARY} 30%, #ffffff), #eef2f7 64%);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.8), 0 12px 28px rgba(18,25,38,0.12);
    }}

    .sbc-player-profile-hero-current .sbc-player-profile-photo {{
        background:
            radial-gradient(circle at 50% 18%, color-mix(in srgb, var(--profile-current-team-secondary) 34%, #ffffff), color-mix(in srgb, var(--profile-current-team-color) 9%, #eef2f7) 64%);
    }}

    .sbc-player-profile-photo img {{
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }}

    .sbc-player-profile-kicker {{
        color: {LEAGUE_PRIMARY};
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .sbc-player-profile-hero-current .sbc-player-profile-kicker {{
        color: var(--profile-current-team-color);
    }}

    .sbc-player-profile-main h2 {{
        margin: 0.16rem 0 0.55rem;
        color: var(--sbc-ink);
        font-family: "{league_font_css}", "Poppins", sans-serif;
        font-size: clamp(2.35rem, 5vw, 4.4rem);
        font-weight: 950;
        line-height: 0.95;
    }}

    .sbc-player-profile-hero-current .sbc-player-profile-main h2 {{
        color: var(--profile-current-team-color);
        font-family: var(--profile-current-team-font), "Poppins", sans-serif;
        text-shadow: 0 1px 0 rgba(255,255,255,0.72);
    }}

    .sbc-player-profile-meta {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.45rem;
    }}

    .sbc-player-profile-main {{
        text-align: center;
    }}

    .sbc-player-profile-meta span,
    .sbc-player-profile-awards span {{
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        background: #f3f5f8;
        color: var(--sbc-ink);
        font-size: 0.72rem;
        font-weight: 900;
        padding: 0.25rem 0.58rem;
    }}

    .sbc-player-profile-hero-current .sbc-player-profile-meta span {{
        border: 1px solid color-mix(in srgb, var(--profile-current-team-color) 22%, rgba(23,32,42,0.10));
        background: color-mix(in srgb, var(--profile-current-team-color) 10%, #ffffff);
        color: color-mix(in srgb, var(--profile-current-team-color) 82%, #111827);
    }}

    .sbc-player-profile-awards {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: stretch;
        gap: 0.42rem;
        margin-top: 0.5rem;
    }}

    .sbc-player-profile-awards span {{
        justify-content: center;
        background: color-mix(in srgb, #c99720 18%, #ffffff);
        color: #111827;
        width: 100%;
    }}

    .sbc-player-profile-awards em {{
        color: var(--sbc-muted);
        font-size: 0.78rem;
        font-style: normal;
        font-weight: 800;
    }}

    .sbc-player-profile-accolades {{
        align-self: stretch;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border: 1px solid color-mix(in srgb, #c99720 28%, rgba(23,32,42,0.10));
        border-radius: 8px;
        background: linear-gradient(135deg, color-mix(in srgb, #c99720 14%, #ffffff), #ffffff);
        padding: 0.85rem;
    }}

    .sbc-player-profile-hero-current .sbc-player-profile-accolades {{
        border-color: color-mix(in srgb, var(--profile-current-team-secondary) 34%, rgba(23,32,42,0.10));
        background: linear-gradient(135deg, color-mix(in srgb, var(--profile-current-team-secondary) 14%, #ffffff), #ffffff);
    }}

    .sbc-player-profile-accolades-label {{
        color: #5a3b00;
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-align: center;
        text-transform: uppercase;
    }}

    .sbc-player-profile-hero-current .sbc-player-profile-accolades-label {{
        color: var(--profile-current-team-color);
    }}

    .sbc-player-profile-table {{
        width: 100%;
        min-width: 60rem;
        overflow: hidden;
        border: 1px solid rgba(23,32,42,0.10);
        border-radius: 8px;
        border-collapse: collapse;
        color: var(--sbc-ink);
        font-variant-numeric: tabular-nums;
    }}

    .sbc-player-profile-table th {{
        background: #111827;
        color: #ffffff;
        font-size: 0.62rem;
        font-weight: 950;
        letter-spacing: 0.05em;
        padding: 0.45rem 0.42rem;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-player-profile-table td {{
        border-bottom: 1px solid rgba(23,32,42,0.065);
        background: #ffffff;
        padding: 0.42rem;
        vertical-align: middle;
    }}

    .sbc-player-profile-table tr:nth-child(even) td {{
        background: #f8fafc;
    }}

    .sbc-player-profile-season,
    .sbc-player-profile-team {{
        white-space: nowrap;
    }}

    .sbc-player-profile-season em {{
        display: block;
        margin-top: 0.16rem;
        color: var(--sbc-muted);
        font-size: 0.58rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }}

    .sbc-player-profile-season-total {{
        background: color-mix(in srgb, {LEAGUE_PRIMARY} 8%, #ffffff) !important;
    }}

    .sbc-player-profile-team-mark {{
        display: inline-flex;
        align-items: center;
        gap: 0.42rem;
        min-width: 13rem;
        border-left: 0.32rem solid var(--profile-team-color);
        border-radius: 8px;
        background:
            linear-gradient(90deg, color-mix(in srgb, var(--profile-team-color) 14%, #ffffff), #ffffff 72%);
        padding: 0.32rem 0.5rem 0.32rem 0.42rem;
    }}

    .sbc-player-profile-team-mark img {{
        width: 1.9rem;
        height: 1.9rem;
        object-fit: contain;
        filter: drop-shadow(0 3px 6px rgba(18,25,38,0.14));
    }}

    .sbc-player-profile-team-mark strong {{
        overflow: hidden;
        color: var(--profile-team-color) !important;
        font-family: var(--profile-team-font), "Poppins", sans-serif !important;
        font-size: 0.86rem;
        font-weight: 950;
        line-height: 1;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-player-profile-team-total {{
        --profile-team-color: {LEAGUE_PRIMARY};
        --profile-team-secondary: {LEAGUE_SECONDARY};
        --profile-team-font: "{league_font_css}";
        min-width: 9rem;
        justify-content: flex-start;
        background: linear-gradient(90deg, #111827, #263244) !important;
        border-left-color: #111827;
    }}

    .sbc-player-profile-team-total strong {{
        color: #ffffff !important;
    }}

    .sbc-player-profile-team-total em {{
        color: rgba(255,255,255,0.66);
        font-size: 0.62rem;
        font-style: normal;
        font-weight: 850;
        text-transform: uppercase;
    }}

    @media (max-width: 980px) {{
        .sbc-player-profile-hero {{
            grid-template-columns: 1fr;
            justify-items: center;
        }}

        .sbc-player-profile-photo {{
            width: min(18rem, 82vw);
            height: min(18rem, 82vw);
        }}

        .sbc-player-profile-accolades {{
            width: 100%;
        }}
    }}

    .sbc-history-layout {{
        display: grid;
        grid-template-columns: minmax(18rem, 0.95fr) minmax(28rem, 1.65fr) minmax(18rem, 0.95fr);
        gap: 0.9rem;
        align-items: start;
        margin: 0.5rem 0 1.2rem;
    }}

    .sbc-history-bracket-panel {{
        overflow: hidden;
        border: 1px solid color-mix(in srgb, {LEAGUE_PRIMARY} 24%, rgba(23, 32, 42, 0.12));
        border-radius: 8px;
        background: rgba(255,255,255,0.96);
        box-shadow: 0 16px 38px rgba(18, 25, 38, 0.085);
    }}

    .sbc-history-bracket-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        background: linear-gradient(90deg, {LEAGUE_PRIMARY}, color-mix(in srgb, {LEAGUE_PRIMARY} 72%, {LEAGUE_SECONDARY}));
        color: #ffffff;
        padding: 0.75rem 0.85rem;
    }}

    .sbc-history-bracket-head span {{
        font-size: 1.02rem;
        font-weight: 950;
    }}

    .sbc-history-bracket-head em {{
        color: rgba(255,255,255,0.78);
        font-size: 0.68rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-history-bracket-scroll {{
        display: grid;
        grid-auto-flow: column;
        grid-auto-columns: minmax(13.5rem, 1fr);
        gap: 0.7rem;
        overflow-x: auto;
        padding: 0.75rem;
    }}

    .sbc-history-bracket-round {{
        display: grid;
        align-content: start;
        gap: 0.55rem;
        min-width: 0;
    }}

    .sbc-history-bracket-round-head {{
        display: flex;
        justify-content: space-between;
        gap: 0.5rem;
        min-height: 2.2rem;
        align-items: center;
        border-radius: 8px;
        background: color-mix(in srgb, {LEAGUE_PRIMARY} 9%, #ffffff);
        color: {LEAGUE_PRIMARY};
        padding: 0.45rem 0.55rem;
    }}

    .sbc-history-bracket-round-head span,
    .sbc-history-bracket-round-head em {{
        overflow: hidden;
        font-size: 0.68rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.05em;
        text-overflow: ellipsis;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-history-bracket-games {{
        display: grid;
        gap: 0.48rem;
    }}

    .sbc-history-game-card {{
        overflow: hidden;
        border: 1px solid rgba(23, 32, 42, 0.1);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 8px 18px rgba(18,25,38,0.055);
    }}

    .sbc-history-game-top {{
        display: flex;
        justify-content: space-between;
        gap: 0.5rem;
        background: #111827;
        color: #ffffff;
        padding: 0.38rem 0.5rem;
    }}

    .sbc-history-game-top span,
    .sbc-history-game-top em {{
        overflow: hidden;
        font-size: 0.58rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.06em;
        text-overflow: ellipsis;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-history-game-top em {{
        color: rgba(255,255,255,0.66);
    }}

    .sbc-history-game-team {{
        display: grid;
        grid-template-columns: 1.85rem minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.46rem;
        border-left: 0.28rem solid var(--history-team-color);
        border-bottom: 1px solid rgba(23,32,42,0.07);
        background: linear-gradient(90deg, color-mix(in srgb, var(--history-team-color) 8%, #ffffff), #ffffff 62%);
        min-height: 3.2rem;
        padding: 0.42rem 0.5rem 0.42rem 0.4rem;
    }}

    .sbc-history-game-team:last-child {{
        border-bottom: none;
    }}

    .sbc-history-game-winner {{
        background: linear-gradient(90deg, color-mix(in srgb, var(--history-team-color) 21%, #ffffff), #ffffff 64%);
    }}

    .sbc-history-kpi-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 0.85rem 0 1rem;
    }}

    .sbc-history-table-wrap {{
        overflow-x: auto;
        border: 1px solid rgba(23, 32, 42, 0.1);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.07);
        margin-bottom: 1rem;
    }}

    .sbc-history-overview-table {{
        width: 100%;
        min-width: 860px;
        border-collapse: collapse;
    }}

    .sbc-history-overview-table th {{
        background: linear-gradient(135deg, color-mix(in srgb, {LEAGUE_PRIMARY} 16%, #ffffff), color-mix(in srgb, {LEAGUE_SECONDARY} 10%, #ffffff));
        color: var(--sbc-ink);
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.06em;
        text-align: left;
        text-transform: uppercase;
        padding: 0.62rem 0.72rem;
        white-space: nowrap;
    }}

    .sbc-history-overview-table td {{
        border-top: 1px solid rgba(23, 32, 42, 0.08);
        color: #1f2937;
        font-size: 0.82rem;
        font-weight: 800;
        padding: 0.54rem 0.72rem;
        vertical-align: middle;
        white-space: nowrap;
    }}

    .sbc-history-overview-table tr:nth-child(even) td {{
        background: rgba(248, 250, 252, 0.72);
    }}

    .sbc-matchup-high-table {{
        overflow: hidden;
        border: 2px solid rgba(17,24,39,0.16) !important;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 14px 34px rgba(15,23,42,0.10);
    }}

    .sbc-matchup-high-table th {{
        background: #ffffff !important;
        border-bottom: 2px solid rgba(17,24,39,0.14);
        color: var(--sbc-ink) !important;
    }}

    .sbc-matchup-high-table td {{
        background: #ffffff !important;
    }}

    .sbc-matchup-high-table tr:nth-child(even) td {{
        background: #fbfcfe !important;
    }}

    .sbc-matchup-high-table td strong {{
        color: var(--sbc-ink);
    }}

    .sbc-matchup-high-table td em {{
        display: block;
        margin-top: 0.12rem;
        color: var(--sbc-muted);
        font-size: 0.68rem;
        font-style: normal;
        font-weight: 850;
    }}

    .sbc-ledger-table {{
        outline: 1px solid rgba(255,255,255,0.9);
        outline-offset: -5px;
    }}

    .sbc-ledger-table tr.sbc-ledger-active-row td {{
        background: color-mix(in srgb, var(--ledger-team-color) 18%, #ffffff) !important;
    }}

    .sbc-ledger-table tr.sbc-ledger-active-row:nth-child(even) td {{
        background: color-mix(in srgb, var(--ledger-team-color) 22%, #ffffff) !important;
    }}

    .sbc-ledger-table tr.sbc-ledger-active-row td:first-child {{
        border-left: 0.24rem solid var(--ledger-team-color);
    }}

    .sbc-ledger-table tr.sbc-ledger-active-row .sbc-history-player-cell strong {{
        color: color-mix(in srgb, var(--ledger-team-color) 82%, #111827) !important;
    }}

    .sbc-record-chase-table tr[style*="--record-team-color"] td {{
        background: color-mix(in srgb, var(--record-team-color) 7%, #ffffff) !important;
    }}

    .sbc-record-chase-table tr[style*="--record-team-color"] td:first-child {{
        border-left: 0.24rem solid var(--record-team-color);
    }}

    .sbc-history-player-cell {{
        display: inline-grid;
        grid-template-columns: 2rem minmax(8rem, 1fr);
        gap: 0.48rem;
        align-items: center;
        min-width: 11rem;
    }}

    .sbc-history-player-cell img {{
        width: 2rem;
        height: 2rem;
        border-radius: 999px;
        background: #eef2f7;
        object-fit: cover;
    }}

    .sbc-history-player-cell strong {{
        overflow: hidden;
        color: var(--sbc-ink);
        font-size: 0.82rem;
        font-weight: 950;
        line-height: 1.05;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-history-overview-table .sbc-draft-team-mark {{
        min-width: 11.5rem;
    }}

    .sbc-history-years-cell {{
        color: #111827 !important;
        font-size: 0.76rem !important;
        font-weight: 900 !important;
        line-height: 1.25;
        min-width: 7.25rem;
        white-space: normal !important;
    }}

    .sbc-history-overview-table .sbc-draft-team-wordmark {{
        font-family: var(--draft-team-font), "Poppins", "Segoe UI", sans-serif;
        font-size: 0.86rem;
    }}

    .sbc-h2h-read-key {{
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
        margin: -0.2rem 0 0.45rem;
    }}

    .sbc-h2h-read-key span {{
        border-radius: 999px;
        background: #111827;
        color: #ffffff;
        font-size: 0.64rem;
        font-weight: 950;
        letter-spacing: 0.06em;
        padding: 0.24rem 0.46rem;
        text-transform: uppercase;
    }}

    .sbc-h2h-read-key em {{
        color: var(--sbc-muted);
        font-size: 0.72rem;
        font-style: normal;
        font-weight: 850;
    }}

    .sbc-h2h-wrap {{
        overflow: visible;
        border: 1px solid rgba(23, 32, 42, 0.1);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.07);
        margin-bottom: 1rem;
    }}

    .sbc-h2h-table {{
        width: max-content;
        min-width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        table-layout: fixed;
    }}

    .sbc-h2h-table th,
    .sbc-h2h-table td {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.07);
        border-right: 1px solid rgba(23, 32, 42, 0.06);
        font-variant-numeric: tabular-nums;
    }}

    .sbc-h2h-corner {{
        position: sticky;
        top: 0;
        left: 0;
        z-index: 5;
        width: 4.15rem;
        min-width: 4.15rem;
        background: #111827;
        color: #ffffff;
        font-size: 0.62rem;
        font-weight: 950;
        letter-spacing: 0.06em;
        padding: 0.38rem 0.35rem;
        text-transform: uppercase;
    }}

    .sbc-h2h-logo-head {{
        width: 2.16rem;
        min-width: 2.16rem;
        height: 2.25rem;
        background: linear-gradient(135deg, color-mix(in srgb, {LEAGUE_PRIMARY} 13%, #ffffff), color-mix(in srgb, {LEAGUE_SECONDARY} 9%, #ffffff));
        padding: 0.22rem;
        text-align: center;
    }}

    .sbc-h2h-logo-head img {{
        width: 1.45rem;
        height: 1.45rem;
        object-fit: contain;
        filter: drop-shadow(0 3px 6px rgba(18, 25, 38, 0.14));
    }}

    .sbc-h2h-row-head {{
        position: sticky;
        left: 0;
        z-index: 3;
        display: grid;
        grid-template-columns: 1.35rem 1fr;
        align-items: center;
        gap: 0.22rem;
        width: 4.15rem;
        min-width: 4.15rem;
        background: #ffffff;
        padding: 0.26rem 0.3rem;
        text-align: left;
    }}

    .sbc-h2h-row-head img {{
        width: 1.22rem;
        height: 1.22rem;
        object-fit: contain;
    }}

    .sbc-h2h-row-head span {{
        overflow: hidden;
        color: var(--sbc-ink);
        font-size: 0.58rem;
        font-weight: 950;
        line-height: 1;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-h2h-table td {{
        width: 2.16rem;
        min-width: 2.16rem;
        color: #111827;
        font-size: 0.62rem;
        font-weight: 950;
        padding: 0.32rem 0.18rem;
        text-align: center;
    }}

    .sbc-h2h-table tr:nth-child(even) .sbc-h2h-row-head {{
        background: rgba(248, 250, 252, 0.92);
    }}

    .sbc-h2h-table td:not(.sbc-h2h-self):hover {{
        outline: 2px solid color-mix(in srgb, {LEAGUE_SECONDARY} 34%, transparent);
        outline-offset: -2px;
    }}

    .sbc-h2h-self {{
        background: #111827 !important;
        color: rgba(255, 255, 255, 0.72) !important;
    }}

    .sbc-history-stats-wrap {{
        overflow: visible;
    }}

    .sbc-history-stats-table {{
        width: 100%;
        min-width: 0;
        table-layout: fixed;
    }}

    .sbc-history-stats-table th {{
        padding: 0.42rem 0.24rem;
        text-align: right;
    }}

    .sbc-history-stats-table th:not(.sbc-history-stat-logo-head) {{
        font-size: 0.58rem;
        letter-spacing: 0.025em;
        text-align: center;
    }}

    .sbc-history-stats-table td {{
        padding: 0.32rem 0.18rem;
        text-align: center;
    }}

    .sbc-history-stats-table td span {{
        display: block;
        color: #111827;
        font-size: 0.67rem;
        font-weight: 950;
        line-height: 1;
    }}

    .sbc-history-stats-table td em {{
        display: block;
        color: var(--sbc-muted);
        font-size: 0.5rem;
        font-style: normal;
        font-weight: 900;
        line-height: 1;
        margin-top: 0.12rem;
    }}

    .sbc-history-stat-logo-head {{
        width: 2.7rem;
        text-align: center !important;
    }}

    .sbc-history-stat-team-logo {{
        width: 2.7rem;
        text-align: center !important;
    }}

    .sbc-history-stat-team-logo img {{
        width: 1.72rem;
        height: 1.72rem;
        object-fit: contain;
        filter: drop-shadow(0 4px 7px rgba(18,25,38,0.14));
    }}

    .sbc-history-game-team img {{
        width: 1.8rem;
        height: 1.8rem;
        object-fit: contain;
    }}

    .sbc-history-game-team strong {{
        overflow: hidden;
        color: var(--sbc-ink);
        font-size: 0.74rem;
        font-weight: 950;
        line-height: 1.08;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-history-game-team b {{
        color: var(--sbc-ink);
        font-size: 1.05rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
    }}

    .sbc-bracket-panel {{
        overflow: hidden;
        border: 1px solid color-mix(in srgb, {LEAGUE_PRIMARY} 28%, rgba(23, 32, 42, 0.12));
        border-radius: 8px;
        background:
            linear-gradient(135deg, color-mix(in srgb, {LEAGUE_PRIMARY} 8%, #ffffff), #ffffff 42%, color-mix(in srgb, {LEAGUE_SECONDARY} 7%, #ffffff));
        box-shadow: 0 18px 44px rgba(18,25,38,0.095);
        margin: 0.45rem 0 1.15rem;
    }}

    .sbc-bracket-head {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        background: linear-gradient(90deg, {LEAGUE_PRIMARY}, color-mix(in srgb, {LEAGUE_PRIMARY} 65%, {LEAGUE_SECONDARY}));
        color: #ffffff;
        padding: 0.85rem 1rem;
    }}

    .sbc-bracket-head span {{
        font-size: 1.15rem;
        font-weight: 950;
        line-height: 1.05;
    }}

    .sbc-bracket-head em {{
        color: rgba(255,255,255,0.74);
        font-size: 0.68rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-bracket-stage {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(11rem, 0.22fr) minmax(0, 1fr);
        gap: 0.9rem;
        align-items: center;
        padding: 0.9rem;
    }}

    .sbc-bracket-side {{
        display: grid;
        grid-auto-flow: column;
        grid-auto-columns: minmax(10.5rem, 1fr);
        gap: 0.9rem;
        align-items: center;
        overflow-x: auto;
        padding: 0.2rem 0.25rem 0.75rem;
    }}

    .sbc-bracket-side-right {{
        justify-content: end;
    }}

    .sbc-bracket-round {{
        position: relative;
        display: grid;
        align-content: center;
        gap: 0.85rem;
        min-width: 0;
    }}

    .sbc-bracket-side-left .sbc-bracket-round:not(:last-child)::after {{
        content: "";
        position: absolute;
        top: 50%;
        right: -0.7rem;
        width: 0.7rem;
        height: 2px;
        background: linear-gradient(90deg, color-mix(in srgb, {LEAGUE_PRIMARY} 55%, transparent), color-mix(in srgb, {LEAGUE_SECONDARY} 70%, transparent));
        transform: translateY(-50%);
    }}

    .sbc-bracket-side-right .sbc-bracket-round:not(:last-child)::before {{
        content: "";
        position: absolute;
        top: 50%;
        left: -0.7rem;
        width: 0.7rem;
        height: 2px;
        background: linear-gradient(270deg, color-mix(in srgb, {LEAGUE_PRIMARY} 55%, transparent), color-mix(in srgb, {LEAGUE_SECONDARY} 70%, transparent));
        transform: translateY(-50%);
    }}

    .sbc-bracket-round-head {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.55rem;
        min-height: 2.45rem;
        border-radius: 8px;
        background: rgba(17,24,39,0.92);
        color: #ffffff;
        padding: 0.5rem 0.65rem;
    }}

    .sbc-bracket-round-head span,
    .sbc-bracket-round-head em {{
        overflow: hidden;
        font-size: 0.68rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.06em;
        text-overflow: ellipsis;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-bracket-round-head em {{
        color: rgba(255,255,255,0.7);
    }}

    .sbc-bracket-games {{
        display: grid;
        gap: 0.7rem;
    }}

    .sbc-bracket-matchup {{
        position: relative;
        border: 1px solid rgba(23,32,42,0.11);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 10px 24px rgba(18,25,38,0.075);
    }}

    .sbc-bracket-matchup-empty {{
        visibility: hidden;
    }}

    .sbc-bracket-matchup::after {{
        content: "";
        position: absolute;
        top: 50%;
        right: -0.46rem;
        width: 0.46rem;
        height: 2px;
        background: color-mix(in srgb, var(--bracket-winner-color) 68%, rgba(23,32,42,0.12));
    }}

    .sbc-bracket-side-right .sbc-bracket-matchup::after {{
        right: auto;
        left: -0.46rem;
    }}

    .sbc-bracket-matchup-inner {{
        position: relative;
        z-index: 2;
        overflow: hidden;
        border-radius: 8px 8px 0 0;
    }}

    .sbc-bracket-team {{
        display: grid;
        grid-template-columns: 1.6rem 2rem minmax(0, 1fr);
        align-items: center;
        gap: 0.38rem;
        min-height: 3.05rem;
        border-left: 0.28rem solid var(--bracket-team-color);
        border-bottom: 1px solid rgba(23,32,42,0.07);
        background: linear-gradient(90deg, color-mix(in srgb, var(--bracket-team-color) 8%, #ffffff), #ffffff 64%);
        padding: 0.4rem 0.48rem 0.4rem 0.36rem;
    }}

    .sbc-bracket-team:last-child {{
        border-bottom: none;
    }}

    .sbc-bracket-team-winner {{
        background:
            linear-gradient(90deg, color-mix(in srgb, var(--bracket-team-color) 26%, #ffffff), #ffffff 62%),
            linear-gradient(135deg, color-mix(in srgb, var(--bracket-team-secondary) 12%, transparent), transparent);
    }}

    .sbc-bracket-seed {{
        display: grid;
        place-items: center;
        width: 1.38rem;
        height: 1.38rem;
        border-radius: 999px;
        background: var(--bracket-seed-color);
        border: 1px solid color-mix(in srgb, var(--bracket-seed-color) 72%, #ffffff);
        color: #ffffff;
        font-size: 0.64rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
    }}

    .sbc-bracket-team img {{
        width: 1.95rem;
        height: 1.95rem;
        object-fit: contain;
        filter: drop-shadow(0 6px 10px rgba(18,25,38,0.13));
    }}

    .sbc-bracket-team strong {{
        overflow: hidden;
        color: var(--sbc-ink);
        font-size: 0.82rem;
        font-weight: 950;
        line-height: 1.06;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-bracket-score {{
        color: #111827;
        font-size: 0.84rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
        line-height: 1;
        text-align: right;
    }}

    .sbc-bracket-champion {{
        display: grid;
        align-content: center;
        justify-items: center;
        gap: 0.55rem;
        min-height: 100%;
        border: 1px solid color-mix(in srgb, var(--champion-color) 34%, rgba(23,32,42,0.12));
        border-radius: 8px;
        background:
            linear-gradient(135deg, color-mix(in srgb, var(--champion-color) 22%, #ffffff), color-mix(in srgb, var(--champion-secondary) 14%, #ffffff));
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.65);
        padding: 1rem;
        text-align: center;
    }}

    .sbc-bracket-champion span {{
        border-radius: 999px;
        background: #111827;
        color: #ffffff;
        font-size: 0.68rem;
        font-weight: 950;
        letter-spacing: 0.07em;
        padding: 0.35rem 0.58rem;
        text-transform: uppercase;
    }}

    .sbc-bracket-champion img {{
        width: clamp(4.2rem, 8vw, 6.4rem);
        height: clamp(4.2rem, 8vw, 6.4rem);
        object-fit: contain;
        filter: drop-shadow(0 12px 20px rgba(18,25,38,0.18));
    }}

    .sbc-bracket-champion strong {{
        color: color-mix(in srgb, var(--champion-color) 78%, #111827);
        font-size: clamp(1rem, 1.45vw, 1.45rem);
        font-weight: 950;
        line-height: 1.02;
    }}

    @media (max-width: 980px) {{
        .sbc-bracket-stage {{
            grid-template-columns: 1fr;
        }}

        .sbc-bracket-side {{
            grid-auto-flow: row;
            grid-auto-columns: unset;
        }}

        .sbc-bracket-champion {{
            min-height: 12rem;
        }}
    }}

    .sbc-nba-bracket {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(12rem, 0.24fr) minmax(0, 1fr);
        gap: 0.65rem;
        align-items: stretch;
        min-height: 38rem;
        padding: 0.85rem 0.65rem;
    }}

    .sbc-nba-bracket-side {{
        display: grid;
        grid-template-columns: repeat(4, minmax(8.35rem, 1fr));
        grid-template-rows: auto 1fr;
        gap: 0.54rem;
        align-items: stretch;
        min-width: 0;
    }}

    .sbc-nba-bracket-center {{
        display: grid;
        gap: 0.85rem;
        align-content: start;
        justify-content: center;
        justify-items: center;
        min-width: 0;
        padding-top: 2.89rem;
    }}

    .sbc-nba-conference-title {{
        grid-column: 1 / -1;
        display: grid;
        place-items: center;
        min-height: 2.35rem;
        border-radius: 8px;
        background:
            linear-gradient(90deg, color-mix(in srgb, {LEAGUE_SECONDARY} 90%, #111827), color-mix(in srgb, {LEAGUE_PRIMARY} 86%, #111827));
        color: #ffffff;
        font-size: 1.08rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        line-height: 1;
        text-transform: uppercase;
        box-shadow: 0 12px 22px rgba(18,25,38,0.12);
    }}

    .sbc-nba-bracket-west .sbc-nba-conference-title {{
        background: {LEAGUE_SECONDARY};
    }}

    .sbc-nba-bracket-east .sbc-nba-conference-title {{
        background: {LEAGUE_PRIMARY};
    }}

    .sbc-nba-bracket .sbc-nba-bracket-column {{
        position: relative;
        display: grid;
        grid-template-rows: auto minmax(0, 1fr);
        gap: 0.55rem;
        min-width: 0;
    }}

    .sbc-nba-bracket .sbc-nba-bracket-column:not(:last-child)::after {{
        display: none;
    }}

    .sbc-nba-bracket-east .sbc-nba-bracket-column:not(:last-child)::after {{
        right: auto;
        left: -0.58rem;
    }}

    .sbc-nba-bracket-column-head {{
        display: grid;
        gap: 0.1rem;
        min-height: 2.2rem;
        align-content: center;
        border-radius: 6px;
        background: rgba(17,24,39,0.92);
        color: #ffffff;
        padding: 0.42rem 0.5rem;
        text-align: center;
    }}

    .sbc-nba-bracket-column-head span,
    .sbc-nba-bracket-column-head em {{
        overflow: hidden;
        font-size: 0.58rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.05em;
        line-height: 1;
        text-overflow: ellipsis;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-nba-bracket-column-head em {{
        color: rgba(255,255,255,0.68);
    }}

    .sbc-nba-bracket .sbc-bracket-games {{
        gap: 0.5rem;
        align-content: space-around;
        min-height: 30rem;
    }}

    .sbc-nba-bracket .sbc-bracket-matchup {{
        z-index: 1;
        box-shadow: 0 7px 16px rgba(18,25,38,0.07);
    }}

    .sbc-nba-bracket .sbc-bracket-matchup::after {{
        display: none;
    }}

    .sbc-nba-bracket-east .sbc-bracket-matchup::after {{
        right: auto;
        left: -0.52rem;
    }}

    .sbc-nba-bracket-center .sbc-bracket-matchup::after {{
        display: none;
    }}

    .sbc-nba-bracket-center .sbc-nba-bracket-column::after {{
        display: none;
    }}

    .sbc-nba-bracket .sbc-bracket-team,
    .sbc-ist-bracket-panel .sbc-bracket-team {{
        grid-template-columns: 1.35rem 1.72rem minmax(0, 1fr);
        gap: 0.3rem;
        min-height: 2.45rem;
        padding: 0.3rem 0.4rem 0.3rem 0.28rem;
    }}

    .sbc-nba-bracket .sbc-bracket-seed,
    .sbc-ist-bracket-panel .sbc-bracket-seed {{
        width: 1.16rem;
        height: 1.16rem;
        font-size: 0.58rem;
    }}

    .sbc-nba-bracket .sbc-bracket-team img,
    .sbc-ist-bracket-panel .sbc-bracket-team img {{
        width: 1.65rem;
        height: 1.65rem;
    }}

    .sbc-nba-bracket .sbc-bracket-team strong,
    .sbc-ist-bracket-panel .sbc-bracket-team strong {{
        font-size: 0.76rem;
        letter-spacing: 0.02em;
    }}

    .sbc-nba-bracket .sbc-bracket-team {{
        grid-template-columns: 1.35rem minmax(0, 1fr) 2.25rem;
        justify-items: center;
        min-height: 3.35rem;
    }}

    .sbc-nba-bracket .sbc-bracket-team img {{
        display: block;
        width: 2.28rem;
        height: 2.28rem;
    }}

    .sbc-nba-bracket .sbc-bracket-team strong {{
        display: none;
    }}

    .sbc-nba-bracket .sbc-bracket-score {{
        justify-self: end;
        padding-right: 0.08rem;
    }}

    .sbc-nba-bracket .sbc-bracket-champion {{
        justify-self: center;
        min-height: 15.5rem;
        width: 17rem;
        max-width: none;
    }}

    .sbc-nba-bracket-center .sbc-nba-bracket-column {{
        justify-self: center;
        width: 8.35rem;
    }}

    .sbc-nba-bracket-center .sbc-bracket-games {{
        width: 100%;
    }}

    .sbc-playin-group {{
        display: grid;
        gap: 0.28rem;
    }}

    .sbc-playin-group-head {{
        min-height: 2.2rem;
        display: grid;
        gap: 0.08rem;
        place-items: center;
        border-radius: 6px;
        background: #111827;
        color: #ffffff;
        font-size: 0.58rem;
        font-weight: 950;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-playin-group-head span,
    .sbc-playin-group-head em {{
        font-style: normal;
        line-height: 1;
    }}

    .sbc-playin-group-head em {{
        color: rgba(255,255,255,0.68);
        font-size: 0.54rem;
    }}

    .sbc-playin-group-games {{
        display: grid;
        gap: 0.42rem;
    }}

    .sbc-playin-spacer {{
        min-height: 2rem;
    }}

    .sbc-ist-bracket-stage {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(11rem, 0.2fr);
        gap: 0.8rem;
        align-items: stretch;
        padding: 0.9rem;
    }}

    .sbc-ist-bracket-flow {{
        display: grid;
        grid-auto-flow: column;
        grid-auto-columns: minmax(21rem, 1fr);
        gap: 0.8rem;
        align-items: stretch;
        overflow-x: auto;
        padding: 0.2rem 0.3rem 0.75rem 0.1rem;
    }}

    .sbc-ist-bracket-round {{
        position: relative;
        display: grid;
        grid-template-rows: auto 1fr;
        align-content: start;
        gap: 0.55rem;
    }}

    .sbc-ist-bracket-round .sbc-bracket-round-head {{
        display: grid;
        gap: 0.1rem;
        justify-content: stretch;
        align-content: center;
        text-align: center;
    }}

    .sbc-ist-bracket-round .sbc-bracket-round-head span,
    .sbc-ist-bracket-round .sbc-bracket-round-head em {{
        line-height: 1;
    }}

    .sbc-ist-bracket-round .sbc-bracket-round-head em {{
        font-size: 0.58rem;
    }}

    .sbc-ist-bracket-round .sbc-bracket-games {{
        align-content: start;
    }}

    .sbc-ist-bracket-panel .sbc-bracket-team {{
        grid-template-columns: 1.55rem 2.15rem minmax(0, 1fr) 2.4rem;
        min-height: 3rem;
    }}

    .sbc-ist-bracket-panel .sbc-bracket-team img {{
        width: 2.05rem;
        height: 2.05rem;
    }}

    .sbc-ist-bracket-panel .sbc-bracket-team strong {{
        font-size: 0.84rem;
    }}

    .sbc-ist-bracket-panel .sbc-bracket-score {{
        justify-self: end;
        padding-right: 0.05rem;
    }}

    .sbc-ist-bracket-panel .sbc-bracket-matchup::after {{
        display: none;
    }}

    .sbc-ist-bracket-round:not(:last-child)::after {{
        display: none;
    }}

    .sbc-ist-bracket-round:nth-child(2) .sbc-bracket-games {{
        gap: 7.1rem;
        padding-top: 3.35rem;
    }}

    .sbc-ist-bracket-round:nth-child(3) .sbc-bracket-games {{
        padding-top: 10rem;
    }}

    @media (max-width: 1150px) {{
        .sbc-nba-bracket {{
            grid-template-columns: 1fr;
        }}

        .sbc-nba-bracket-side {{
            grid-template-columns: repeat(2, minmax(9rem, 1fr));
        }}

        .sbc-ist-bracket-stage {{
            grid-template-columns: 1fr;
        }}
    }}

    .sbc-under-construction {{
        display: grid;
        grid-template-columns: auto 1fr;
        align-items: center;
        gap: 0.8rem;
        border: 1px solid color-mix(in srgb, {LEAGUE_SECONDARY} 24%, rgba(23, 32, 42, 0.12));
        border-left: 0.4rem solid {LEAGUE_SECONDARY};
        border-radius: 8px;
        background: color-mix(in srgb, {LEAGUE_SECONDARY} 7%, #ffffff);
        box-shadow: 0 12px 28px rgba(18,25,38,0.065);
        margin: 0.5rem 0 1rem;
        padding: 0.85rem 0.95rem;
    }}

    .sbc-under-icon {{
        display: grid;
        place-items: center;
        width: 2.4rem;
        height: 2.4rem;
        border-radius: 999px;
        background: {LEAGUE_SECONDARY};
        color: #ffffff;
        font-weight: 950;
        letter-spacing: 0.03em;
    }}

    .sbc-under-construction strong,
    .sbc-under-construction span {{
        display: block;
    }}

    .sbc-under-construction strong {{
        color: var(--sbc-ink);
        font-size: 0.98rem;
        font-weight: 950;
    }}

    .sbc-under-construction span {{
        color: var(--sbc-muted);
        font-size: 0.84rem;
        font-weight: 800;
    }}

    .sbc-standings-layout {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.9rem;
        margin: 0.45rem 0 1.1rem;
    }}

    .sbc-standings-panel {{
        overflow: hidden;
        --standings-accent: var(--sbc-team-primary);
        --standings-accent-2: var(--sbc-team-secondary);
        border: 1px solid color-mix(in srgb, var(--standings-accent) 30%, rgba(23, 32, 42, 0.12));
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.075);
    }}

    .sbc-standings-west {{
        --standings-accent: {LEAGUE_SECONDARY};
        --standings-accent-2: color-mix(in srgb, {LEAGUE_SECONDARY} 58%, #111827);
    }}

    .sbc-standings-east {{
        --standings-accent: {LEAGUE_PRIMARY};
        --standings-accent-2: color-mix(in srgb, {LEAGUE_PRIMARY} 70%, #111827);
    }}

    .sbc-standings-panel-wide {{
        margin: 0.25rem 0 1.1rem;
    }}

    .sbc-standings-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        border-bottom: 1px solid rgba(23, 32, 42, 0.08);
        background: linear-gradient(90deg, var(--standings-accent), var(--standings-accent-2));
        color: #ffffff;
        padding: 0.72rem 0.85rem;
    }}

    .sbc-standings-head span {{
        font-size: 1.1rem;
        font-weight: 950;
        line-height: 1.1;
    }}

    .sbc-standings-head em {{
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.66rem;
        font-style: normal;
        font-weight: 900;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-standings-table-wrap {{
        overflow-x: auto;
    }}

    .sbc-standings-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }}

    .sbc-standings-table th {{
        background: color-mix(in srgb, var(--standings-accent) 13%, #ffffff);
        border-bottom: 1px solid rgba(23, 32, 42, 0.1);
        color: color-mix(in srgb, var(--standings-accent) 80%, #111827);
        font-size: 0.84rem;
        font-weight: 950;
        letter-spacing: 0.07em;
        padding: 0.58rem 0.6rem;
        text-align: center;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-standings-table th:nth-child(1) {{ width: 3.4rem; }}
    .sbc-standings-table th:nth-child(2) {{ width: 14rem; text-align: left; }}

    .sbc-ist-standings-table th:nth-child(1) {{ width: 3.4rem; }}
    .sbc-ist-standings-table th:nth-child(2) {{ width: 13.5rem; text-align: left; }}
    .sbc-ist-standings-table th:nth-child(3),
    .sbc-ist-standings-table th:nth-child(4) {{ width: 5.2rem; }}

    .sbc-standings-table td {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.065);
        color: var(--sbc-ink);
        font-size: 0.78rem;
        font-weight: 800;
        height: 3.25rem;
        padding: 0.48rem 0.6rem;
        text-align: center;
        vertical-align: middle;
        white-space: nowrap;
    }}

    .sbc-standings-table tr:last-child td {{
        border-bottom: none;
    }}

    .sbc-standings-group-row td {{
        height: auto !important;
        background: linear-gradient(90deg, var(--standings-accent), var(--standings-accent-2)) !important;
        color: #ffffff !important;
        font-size: 0.82rem !important;
        font-weight: 950 !important;
        letter-spacing: 0.08em;
        padding: 0.52rem 0.68rem !important;
        text-align: left !important;
        text-transform: uppercase;
    }}

    .sbc-standings-playoff td {{
        background: color-mix(in srgb, var(--standings-accent) 17%, #ffffff);
    }}

    .sbc-standings-playin td {{
        background: color-mix(in srgb, #c7a731 19%, #ffffff);
    }}

    .sbc-standings-lottery td {{
        background: color-mix(in srgb, #c84d4d 13%, #ffffff);
    }}

    .sbc-standings-rank {{
        color: var(--sbc-ink);
        font-weight: 950 !important;
        font-variant-numeric: tabular-nums;
    }}

    .sbc-standings-rank span {{
        display: inline-grid;
        place-items: center;
        width: 2.15rem;
        height: 2.15rem;
        border-radius: 999px;
        background: var(--standings-accent);
        border: 1px solid color-mix(in srgb, var(--standings-accent) 70%, #ffffff);
        box-shadow: 0 4px 10px rgba(18, 25, 38, 0.08);
        color: #ffffff;
        font-weight: 950;
    }}

    .sbc-standings-team {{
        display: flex;
        align-items: center;
        gap: 0.52rem;
        min-width: 0;
        text-align: left !important;
    }}

    .sbc-standings-team img {{
        width: 2rem;
        height: 2rem;
        flex: 0 0 2rem;
        object-fit: contain;
        filter: drop-shadow(0 3px 7px rgba(18, 25, 38, 0.12));
    }}

    .sbc-standings-team strong {{
        overflow: hidden;
        color: var(--sbc-ink);
        font-size: 0.78rem;
        font-weight: 950;
        line-height: 1.05;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-overview-table-wrap,
    .sbc-draft-board {{
        overflow: hidden;
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 22%, rgba(23, 32, 42, 0.12));
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.075);
        margin: 0.45rem 0 1rem;
    }}

    .sbc-overview-table,
    .sbc-draft-board-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }}

    .sbc-overview-table th,
    .sbc-draft-board-table th {{
        background: #111827;
        color: #ffffff;
        font-size: 0.86rem;
        font-weight: 950;
        letter-spacing: 0.07em;
        padding: 0.66rem 0.65rem;
        text-align: center;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    .sbc-overview-table th:nth-child(1) {{ width: 3.4rem; }}
    .sbc-overview-table th:nth-child(2) {{ width: 7.2rem; text-align: left; }}
    .sbc-overview-table th:nth-child(3) {{ width: 4.35rem; }}
    .sbc-overview-table th:nth-child(4) {{ width: 8.1rem; }}
    .sbc-overview-table th:nth-child(5),
    .sbc-overview-table th:nth-child(6) {{ width: 7.2rem; }}
    .sbc-overview-table th:nth-child(7),
    .sbc-overview-table th:nth-child(8) {{ width: 6.6rem; }}
    .sbc-overview-table th:nth-child(9),
    .sbc-overview-table th:nth-child(10),
    .sbc-overview-table th:nth-child(11) {{ width: 6.1rem; }}
    .sbc-overview-table th:nth-child(12) {{ width: 7.9rem; }}
    .sbc-overview-table td,
    .sbc-draft-board-table td {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.07);
        color: var(--sbc-ink);
        font-size: 0.78rem;
        font-weight: 800;
        height: 3.65rem;
        padding: 0.5rem 0.65rem;
        text-align: center;
        vertical-align: middle;
    }}

    .sbc-overview-table tr:nth-child(even) td,
    .sbc-draft-board-table tr:nth-child(even) td {{
        background: rgba(247, 249, 252, 0.62);
    }}

    .sbc-overview-table td:nth-child(2) {{
        text-align: left;
        font-weight: 950;
    }}

    .sbc-overview-money {{
        color: var(--sbc-ink) !important;
        font-family: "Poppins", "Segoe UI", sans-serif;
        font-variant-numeric: tabular-nums;
        font-size: 0.8rem !important;
        font-weight: 850 !important;
        letter-spacing: 0;
    }}

    .sbc-money-good {{ color: #1f5f34 !important; }}
    .sbc-money-bad {{ color: #8d2424 !important; }}
    .sbc-overview-fee-pill {{
        display: inline-flex;
        margin-left: 0.35rem;
        padding: 0.05rem 0.35rem;
        border-radius: 999px;
        background: color-mix(in srgb, #8d2424 10%, #ffffff);
        color: #8d2424;
        font-size: 0.62rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        vertical-align: middle;
    }}
    .sbc-overview-important-money {{
        background: color-mix(in srgb, #c7a731 24%, #ffffff) !important;
        box-shadow: inset 0 0 0 2px rgba(199, 167, 49, 0.38);
    }}
    .sbc-overview-center {{ font-weight: 950 !important; }}

    .sbc-overview-logo-cell img {{
        width: 3.25rem;
        height: 3.25rem;
    }}

    .sbc-overview-team-name {{
        color: var(--overview-team-color);
        display: grid;
        gap: 0.14rem;
        line-height: 1.05;
    }}

    .sbc-overview-team-name strong {{
        display: block;
        font-family: var(--overview-team-font), "Poppins", sans-serif;
        font-size: 1rem;
        font-weight: 950;
    }}

    .sbc-overview-team-name em {{
        color: var(--sbc-muted);
        display: block;
        font-family: "Poppins", "Segoe UI", sans-serif;
        font-size: 0.68rem;
        font-style: normal;
        font-weight: 850;
        line-height: 1;
    }}

    .sbc-overview-active {{
        display: inline-grid;
        place-items: center;
        min-width: 2.35rem;
        height: 2.15rem;
        border-radius: 999px;
        border: 1px solid rgba(23, 32, 42, 0.12);
        font-size: 0.9rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
    }}

    .sbc-overview-active-ok {{
        background: color-mix(in srgb, #3f8f55 14%, #ffffff);
        color: #194926;
    }}

    .sbc-overview-active-warn {{
        background: color-mix(in srgb, #c97f25 22%, #ffffff);
        color: #6a3a08;
    }}

    .sbc-overview-active-danger {{
        background: color-mix(in srgb, #c84d4d 18%, #ffffff);
        color: #7c1f1f;
    }}

    .sbc-overview-hardcap {{
        font-size: 0.78rem !important;
        font-weight: 850 !important;
    }}

    .sbc-overview-hardcap-alert {{
        background: color-mix(in srgb, #c7a731 20%, #ffffff) !important;
        color: #5f4700 !important;
        font-weight: 950 !important;
    }}

    .sbc-hardcap-flag {{
        display: inline-grid;
        place-items: center;
        width: 1.2rem;
        height: 1.2rem;
        margin-right: 0.32rem;
        border-radius: 999px;
        background: #111827;
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 950;
        vertical-align: middle;
    }}

    .sbc-payout-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.78rem;
        margin: 0.45rem 0 1rem;
    }}

    .sbc-payout-card {{
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 24%, rgba(23, 32, 42, 0.11));
        border-top: 4px solid var(--sbc-team-primary);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 12px 28px rgba(18, 25, 38, 0.065);
        min-height: 7rem;
        padding: 0.82rem 0.88rem;
    }}

    .sbc-payout-label {{
        color: var(--sbc-muted);
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .sbc-payout-value {{
        color: var(--sbc-ink);
        font-size: 1.45rem;
        font-weight: 950;
        line-height: 1;
        margin-top: 0.42rem;
        font-variant-numeric: tabular-nums;
    }}

    .sbc-payout-note {{
        color: var(--sbc-muted);
        font-size: 0.73rem;
        font-weight: 750;
        line-height: 1.28;
        margin-top: 0.42rem;
    }}

    .sbc-draft-board-head {{
        display: grid;
        grid-template-columns: auto 1fr;
        align-items: center;
        gap: 0.72rem;
        border-bottom: 1px solid rgba(23, 32, 42, 0.08);
        background:
            linear-gradient(90deg, color-mix(in srgb, var(--sbc-team-primary) 16%, #ffffff) 0%, #ffffff 100%);
        padding: 0.78rem 0.88rem;
    }}

    .sbc-draft-board-head > span {{
        width: 2.35rem;
        height: 2.35rem;
        display: grid;
        place-items: center;
        border-radius: 8px;
        background: var(--sbc-team-primary);
        color: var(--sbc-team-text);
        font-weight: 950;
    }}

    .sbc-draft-board-head strong {{
        display: block;
        color: var(--sbc-ink);
        font-size: 1rem;
        font-weight: 950;
        line-height: 1.1;
    }}

    .sbc-draft-board-head em {{
        display: block;
        color: var(--sbc-muted);
        font-size: 0.76rem;
        font-style: normal;
        font-weight: 750;
        line-height: 1.25;
        margin-top: 0.18rem;
    }}

    .sbc-draft-board-wrap {{
        overflow-x: auto;
    }}

    .sbc-draft-board-table th:nth-child(1) {{ width: 4.2rem; }}
    .sbc-draft-board-table th:nth-child(2) {{ width: 13.5rem; }}
    .sbc-draft-board-table th:nth-child(3) {{ width: 12.5rem; }}
    .sbc-draft-board-table th:nth-child(4) {{ width: 14rem; }}
    .sbc-draft-board-table th:nth-child(5) {{ width: 10rem; }}

    .sbc-current-draft-board .sbc-draft-board-table th:nth-child(2) {{ width: 15.8rem; text-align: left; }}
    .sbc-current-draft-board .sbc-draft-board-table th:nth-child(3) {{ width: 12rem; text-align: left; }}
    .sbc-history-draft-board .sbc-draft-board-table th:nth-child(2) {{ width: 9.9rem; text-align: left; }}
    .sbc-history-draft-board .sbc-draft-board-table th:nth-child(3) {{ width: 14.4rem; }}
    .sbc-history-draft-board .sbc-draft-board-table th:nth-child(4) {{ width: 13.1rem; text-align: left; }}
    .sbc-history-draft-board .sbc-draft-board-table th:nth-child(2),
    .sbc-history-draft-board .sbc-draft-board-table th:nth-child(4) {{ text-align: left; }}

    .sbc-draft-pick-no span {{
        display: inline-grid;
        place-items: center;
        width: 2.25rem;
        height: 2.25rem;
        border-radius: 999px;
        background: color-mix(in srgb, var(--sbc-team-primary) 16%, #ffffff);
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 30%, rgba(23, 32, 42, 0.12));
        color: var(--sbc-ink);
        font-weight: 950;
    }}

    .sbc-draft-team-cell,
    .sbc-draft-player-cell {{
        text-align: center !important;
    }}

    .sbc-current-draft-board .sbc-draft-board-table td,
    .sbc-history-draft-board .sbc-draft-board-table td {{
        height: 4.2rem;
    }}

    .sbc-current-draft-board .sbc-draft-board-table tr[style*="--draft-row-color"] td,
    .sbc-history-draft-board .sbc-draft-board-table tr[style*="--draft-row-color"] td {{
        background-color: color-mix(in srgb, var(--draft-row-color) 5%, #ffffff);
    }}

    .sbc-current-draft-board .sbc-draft-board-table tr[style*="--draft-row-color"]:nth-child(even) td,
    .sbc-history-draft-board .sbc-draft-board-table tr[style*="--draft-row-color"]:nth-child(even) td {{
        background-color: color-mix(in srgb, var(--draft-row-color) 8%, #ffffff);
    }}

    .sbc-current-draft-board .sbc-draft-team-cell,
    .sbc-history-draft-board .sbc-draft-team-cell {{
        text-align: left !important;
    }}

    .sbc-draft-player-cell {{
        text-align: left !important;
        white-space: nowrap;
    }}

    .sbc-draft-slot-cell .sbc-pick-slot-team {{
        margin: 0;
    }}

    .sbc-draft-team-cell img {{
        width: 2.65rem;
        height: 2.65rem;
        object-fit: contain;
        vertical-align: middle;
        margin-right: 0.45rem;
        filter: drop-shadow(0 3px 7px rgba(18, 25, 38, 0.12));
    }}

    .sbc-draft-player-cell img {{
        width: 2.6rem;
        height: 2.6rem;
        object-fit: cover;
        object-position: center 18%;
        border-radius: 999px;
        vertical-align: middle;
        margin-right: 0.55rem;
        border: 2px solid #ffffff;
        box-shadow: 0 0 0 1px rgba(23, 32, 42, 0.14);
    }}

    .sbc-draft-team-cell strong,
    .sbc-draft-player-cell strong {{
        font-size: 0.82rem;
        font-weight: 950;
    }}

    .sbc-draft-team-wordmark {{
        color: color-mix(in srgb, var(--draft-team-secondary) 72%, #111827 28%);
        display: inline-block;
        font-family: var(--draft-team-font), "Poppins", "Segoe UI", sans-serif;
        font-size: 0.9rem;
        font-weight: 950;
        line-height: 1.12;
        text-align: left;
        white-space: nowrap;
    }}

    .sbc-draft-team-mark {{
        display: inline-grid;
        grid-template-columns: 2rem minmax(0, 1fr);
        align-items: center;
        gap: 0.48rem;
        max-width: 100%;
    }}

    .sbc-draft-team-mark img {{
        width: 1.7rem;
        height: 1.7rem;
        object-fit: contain;
        margin: 0;
        filter: drop-shadow(0 3px 6px rgba(18, 25, 38, 0.14));
    }}

    .sbc-draft-team-empty {{
        color: var(--sbc-muted);
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 900;
        line-height: 1.1;
    }}

    .sbc-draft-player-pending strong {{
        color: var(--sbc-ink);
        font-variant-numeric: tabular-nums;
    }}

    .sbc-retired-live-draft-room {{
        display: grid;
        grid-template-columns: minmax(18rem, 1fr) minmax(27rem, 1.25fr);
        gap: 1rem;
        align-items: center;
        margin: 0.85rem 0 1rem;
        padding: 1rem 1.1rem;
        border: 1px solid color-mix(in srgb, {LEAGUE_PRIMARY} 24%, rgba(23, 32, 42, 0.12));
        border-left: 0.45rem solid {LEAGUE_SECONDARY};
        border-radius: 8px;
        background: linear-gradient(135deg, #ffffff 0%, color-mix(in srgb, {LEAGUE_PRIMARY} 7%, #ffffff) 100%);
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.075);
    }}

    .sbc-live-draft-kicker {{
        color: {LEAGUE_SECONDARY};
        font-size: 0.76rem;
        font-weight: 950;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }}

    .sbc-live-draft-title {{
        color: {LEAGUE_PRIMARY};
        font-family: "{league_font_css}", "Poppins", sans-serif;
        font-size: clamp(1.55rem, 3vw, 2.55rem);
        font-weight: 950;
        line-height: 1.05;
    }}

    .sbc-live-draft-dates {{
        color: var(--sbc-muted);
        font-size: 0.9rem;
        font-weight: 800;
        margin-top: 0.25rem;
    }}

    .sbc-live-draft-cards {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.75rem;
    }}

    .sbc-live-draft-card {{
        display: grid;
        grid-template-columns: auto auto 1fr;
        gap: 0.75rem;
        align-items: center;
        border-radius: 8px;
        background: linear-gradient(135deg, color-mix(in srgb, var(--clock-team-color, {LEAGUE_PRIMARY}) 12%, #ffffff) 0%, color-mix(in srgb, var(--clock-team-secondary, {LEAGUE_SECONDARY}) 12%, #ffffff) 100%);
        border: 1px solid color-mix(in srgb, var(--clock-team-color, {LEAGUE_PRIMARY}) 28%, rgba(23, 32, 42, 0.12));
        border-left: 0.35rem solid var(--clock-team-color, {LEAGUE_PRIMARY});
        color: var(--sbc-ink);
        min-height: 5.35rem;
        padding: 0.78rem 0.9rem;
    }}

    .sbc-live-draft-pick-circle {{
        width: 3rem;
        height: 3rem;
        display: grid;
        place-items: center;
        border-radius: 999px;
        background: var(--clock-team-color, {LEAGUE_PRIMARY});
        color: #ffffff;
        font-size: 1.08rem;
        font-weight: 950;
        box-shadow: 0 8px 18px color-mix(in srgb, var(--clock-team-color, {LEAGUE_PRIMARY}) 25%, transparent);
    }}

    .sbc-live-draft-logo {{
        width: 3.2rem;
        height: 3.2rem;
        display: grid;
        place-items: center;
    }}

    .sbc-live-draft-logo img {{
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        filter: drop-shadow(0 5px 10px rgba(0, 0, 0, 0.28));
    }}

    .sbc-live-draft-card-copy {{
        display: grid;
        gap: 0.12rem;
        min-width: 0;
    }}

    .sbc-live-draft-card-copy span {{
        color: color-mix(in srgb, var(--clock-team-secondary, {LEAGUE_SECONDARY}) 68%, #111827 32%);
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.14em;
        text-transform: uppercase;
    }}

    .sbc-live-draft-card-copy strong {{
        color: var(--sbc-ink);
        font-size: 1rem;
        font-weight: 950;
        line-height: 1.15;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-live-draft-card-copy em {{
        color: var(--sbc-muted);
        font-size: 0.8rem;
        font-style: normal;
        font-weight: 800;
    }}

    .sbc-live-draft-empty {{
        color: var(--sbc-muted);
        font-weight: 900;
    }}

    .sbc-awards-section-head {{
        display: grid;
        gap: 0.18rem;
        margin: 1.2rem 0 0.75rem;
    }}

    .sbc-awards-section-head span {{
        color: var(--sbc-ink);
        font-family: "{league_font_css}", "Poppins", sans-serif;
        font-size: clamp(1.45rem, 2.7vw, 2.35rem);
        font-weight: 950;
        line-height: 1;
    }}

    .sbc-awards-section-head em {{
        color: var(--sbc-muted);
        font-size: 0.9rem;
        font-style: normal;
        font-weight: 800;
    }}

    .sbc-about-feature,
    .sbc-about-rule-card,
    .sbc-check-card {{
        --about-accent: {LEAGUE_PRIMARY};
        overflow: hidden;
        border: 1px solid color-mix(in srgb, var(--about-accent) 22%, rgba(23, 32, 42, 0.12));
        border-top: 4px solid var(--about-accent);
        border-radius: 8px;
        background: linear-gradient(135deg, #ffffff 0%, color-mix(in srgb, var(--about-accent) 6%, #ffffff) 100%);
        box-shadow: 0 16px 36px rgba(18, 25, 38, 0.08);
    }}

    .sbc-about-feature {{
        min-height: 10.6rem;
        padding: 0.95rem;
        margin-bottom: 0.85rem;
        display: grid;
        align-content: start;
        gap: 0.38rem;
    }}

    .sbc-about-feature-blue,
    .sbc-check-clear {{ --about-accent: {LEAGUE_PRIMARY}; }}

    .sbc-about-feature-green {{ --about-accent: {LEAGUE_SECONDARY}; }}
    .sbc-about-feature-gold {{ --about-accent: #b88914; }}
    .sbc-about-feature-red,
    .sbc-check-issue {{ --about-accent: #b91c1c; }}

    .sbc-about-stat {{
        width: fit-content;
        border-radius: 999px;
        background: var(--about-accent);
        color: #ffffff;
        font-size: 0.78rem;
        font-weight: 950;
        padding: 0.26rem 0.58rem;
    }}

    .sbc-about-feature-title,
    .sbc-about-rule-title,
    .sbc-check-title {{
        color: var(--sbc-ink);
        font-size: 1.02rem;
        font-weight: 950;
        line-height: 1.12;
    }}

    .sbc-about-feature-body,
    .sbc-check-copy {{
        color: var(--sbc-muted);
        font-size: 0.88rem;
        font-weight: 760;
        line-height: 1.42;
    }}

    .sbc-about-rule-card {{
        padding: 0.85rem 0.95rem;
        margin-bottom: 0.85rem;
    }}

    .sbc-about-rule-card ul {{
        margin: 0.58rem 0 0;
        padding-left: 1.05rem;
        color: var(--sbc-muted);
        font-size: 0.86rem;
        font-weight: 760;
        line-height: 1.42;
    }}

    .sbc-about-rule-card li + li {{
        margin-top: 0.28rem;
    }}

    .sbc-check-card {{
        margin-bottom: 0.65rem;
        padding: 0.85rem 0.95rem;
    }}

    .sbc-check-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.85rem;
    }}

    .sbc-check-badge {{
        flex: 0 0 auto;
        min-width: 4.7rem;
        border-radius: 999px;
        background: var(--about-accent);
        color: #ffffff;
        font-size: 0.78rem;
        font-weight: 950;
        text-align: center;
        padding: 0.32rem 0.6rem;
    }}

    .sbc-about-copy-card {{
        --about-accent: {LEAGUE_PRIMARY};
        margin-bottom: 0.95rem;
        padding: 1rem 1.08rem;
        border: 1px solid color-mix(in srgb, var(--about-accent) 22%, rgba(23, 32, 42, 0.12));
        border-left: 5px solid var(--about-accent);
        border-radius: 8px;
        background: linear-gradient(135deg, #ffffff 0%, color-mix(in srgb, var(--about-accent) 5%, #ffffff) 100%);
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.075);
    }}

    .sbc-about-copy-title {{
        color: var(--sbc-ink);
        font-size: 1.16rem;
        font-weight: 950;
        line-height: 1.08;
        margin-bottom: 0.58rem;
    }}

    .sbc-about-copy-body {{
        color: #263244;
        font-size: 0.95rem;
        font-weight: 650;
        line-height: 1.55;
    }}

    .sbc-about-copy-body p {{
        margin: 0 0 0.76rem;
    }}

    .sbc-about-copy-body p:last-child {{
        margin-bottom: 0;
    }}

    .sbc-about-copy-body ul {{
        margin: 0.55rem 0 0.72rem;
        padding-left: 1.1rem;
    }}

    .sbc-about-copy-body li {{
        margin: 0.22rem 0;
    }}

    .sbc-about-copy-body a {{
        color: var(--about-accent);
        font-weight: 900;
        text-decoration: none;
    }}

    .sbc-trade-hero {{
        position: relative;
        overflow: hidden;
        border-radius: 8px;
        margin-bottom: 1rem;
        background:
            linear-gradient(135deg, color-mix(in srgb, var(--trade-primary, {LEAGUE_PRIMARY}) 92%, #111827 8%), color-mix(in srgb, var(--trade-secondary, {LEAGUE_SECONDARY}) 72%, #111827 28%));
        box-shadow: 0 20px 48px rgba(18, 25, 38, 0.18);
    }}

    .sbc-trade-hero-bg {{
        position: absolute;
        inset: 0;
        background:
            linear-gradient(90deg, rgba(255,255,255,0.12) 0 1px, transparent 1px 100%),
            linear-gradient(0deg, rgba(255,255,255,0.1) 0 1px, transparent 1px 100%);
        background-size: 28px 28px;
        opacity: 0.34;
    }}

    .sbc-trade-hero-inner {{
        position: relative;
        display: grid;
        grid-template-columns: 6.2rem minmax(0, 1fr) auto;
        align-items: center;
        gap: 1rem;
        padding: 1.05rem 1.15rem;
    }}

    .sbc-trade-logo-frame {{
        display: grid;
        place-items: center;
        width: 5.7rem;
        height: 5.7rem;
        border-radius: 8px;
        background: rgba(255,255,255,0.92);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.7), 0 16px 28px rgba(0,0,0,0.18);
    }}

    .sbc-trade-logo-frame img {{
        max-width: 4.9rem;
        max-height: 4.9rem;
        object-fit: contain;
    }}

    .sbc-trade-eyebrow {{
        color: rgba(255,255,255,0.82);
        font-size: 0.76rem;
        font-weight: 950;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }}

    .sbc-trade-heading {{
        color: #ffffff;
        font-family: "{league_font_css}", "Poppins", sans-serif;
        font-size: clamp(2rem, 4.8vw, 4rem);
        font-weight: 950;
        line-height: 0.95;
        text-shadow: 0 10px 24px rgba(0,0,0,0.22);
    }}

    .sbc-trade-subcopy {{
        max-width: 54rem;
        color: rgba(255,255,255,0.9);
        font-size: 0.96rem;
        font-weight: 760;
        line-height: 1.35;
        margin-top: 0.28rem;
    }}

    .sbc-trade-hero-counts {{
        display: grid;
        grid-template-columns: repeat(2, minmax(5.2rem, 1fr));
        gap: 0.55rem;
    }}

    .sbc-trade-hero-counts span,
    .sbc-trade-summary-card,
    .sbc-trade-chip-card {{
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.2);
        background: rgba(255,255,255,0.92);
        box-shadow: 0 14px 30px rgba(18,25,38,0.1);
    }}

    .sbc-trade-hero-counts span {{
        display: grid;
        place-items: center;
        min-height: 4.4rem;
        padding: 0.55rem;
    }}

    .sbc-trade-hero-counts strong {{
        color: var(--trade-primary, {LEAGUE_PRIMARY});
        font-size: 1.45rem;
        font-weight: 950;
        line-height: 1;
    }}

    .sbc-trade-hero-counts em {{
        color: var(--sbc-muted);
        font-size: 0.72rem;
        font-style: normal;
        font-weight: 900;
        text-transform: uppercase;
    }}

    .sbc-trade-panel-head {{
        display: grid;
        grid-template-columns: auto 1fr;
        align-items: center;
        gap: 0.65rem;
        margin: 0.4rem 0 0.55rem;
        padding: 0.68rem 0.76rem;
        border-radius: 8px;
        border: 1px solid color-mix(in srgb, var(--trade-primary, {LEAGUE_PRIMARY}) 24%, rgba(23, 32, 42, 0.12));
        border-top: 4px solid var(--trade-primary, {LEAGUE_PRIMARY});
        background: linear-gradient(135deg, #ffffff 0%, color-mix(in srgb, var(--trade-primary, {LEAGUE_PRIMARY}) 8%, #ffffff) 100%);
    }}

    .sbc-trade-panel-green {{
        --trade-primary: #007a32;
    }}

    .sbc-trade-panel-gold {{
        --trade-primary: #9f6f00;
    }}

    .sbc-trade-panel-red {{
        --trade-primary: #b91c1c;
    }}

    .sbc-trade-panel-head img {{
        width: 2.35rem;
        height: 2.35rem;
        object-fit: contain;
    }}

    .sbc-trade-panel-head span {{
        display: block;
        color: var(--sbc-ink);
        font-family: "Poppins", sans-serif;
        font-size: 0.98rem;
        font-weight: 950;
        line-height: 1.1;
    }}

    .sbc-trade-panel-head em {{
        display: block;
        color: var(--sbc-muted);
        font-family: "Poppins", sans-serif;
        font-size: 0.78rem;
        font-style: normal;
        font-weight: 850;
    }}

    .sbc-trade-summary-card,
    .sbc-trade-chip-card {{
        --trade-card-accent: {LEAGUE_PRIMARY};
        padding: 0.78rem 0.85rem;
        margin-bottom: 0.75rem;
        border: 1px solid color-mix(in srgb, var(--trade-card-accent) 22%, rgba(23, 32, 42, 0.12));
        border-top: 4px solid var(--trade-card-accent);
        background: linear-gradient(135deg, #ffffff 0%, color-mix(in srgb, var(--trade-card-accent) 6%, #ffffff) 100%);
    }}

    .sbc-trade-summary-green {{ --trade-card-accent: {LEAGUE_SECONDARY}; }}
    .sbc-trade-summary-gold {{ --trade-card-accent: #b88914; }}
    .sbc-trade-summary-red {{ --trade-card-accent: #b91c1c; }}

    .sbc-trade-summary-card span,
    .sbc-trade-chip-title {{
        color: var(--sbc-muted);
        font-size: 0.73rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .sbc-trade-summary-card strong {{
        display: block;
        color: var(--sbc-ink);
        font-size: clamp(1.25rem, 2.2vw, 1.85rem);
        font-weight: 950;
        line-height: 1.05;
        margin-top: 0.14rem;
    }}

    .sbc-trade-summary-card em {{
        display: block;
        color: var(--sbc-muted);
        font-size: 0.78rem;
        font-style: normal;
        font-weight: 800;
        margin-top: 0.12rem;
    }}

    .sbc-trade-chip-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.38rem;
        margin-top: 0.48rem;
    }}

    .sbc-trade-chip,
    .sbc-trade-empty-chip {{
        display: inline-flex;
        align-items: center;
        min-height: 1.8rem;
        border-radius: 999px;
        padding: 0.32rem 0.55rem;
        font-size: 0.78rem;
        font-weight: 850;
        line-height: 1.1;
    }}

    .sbc-trade-chip {{
        background: color-mix(in srgb, var(--trade-card-accent) 14%, #ffffff);
        color: color-mix(in srgb, var(--trade-card-accent) 70%, #111827 30%);
        border: 1px solid color-mix(in srgb, var(--trade-card-accent) 22%, rgba(23, 32, 42, 0.1));
    }}

    .sbc-trade-empty-chip {{
        background: #f3f6fa;
        color: var(--sbc-muted);
        border: 1px dashed rgba(23, 32, 42, 0.18);
    }}

    div[data-testid="stForm"] {{
        border: 1px solid color-mix(in srgb, {LEAGUE_PRIMARY} 14%, rgba(23, 32, 42, 0.12));
        border-radius: 8px;
        background:
            linear-gradient(180deg, rgba(255,255,255,0.94), rgba(255,255,255,0.82)),
            color-mix(in srgb, {LEAGUE_SECONDARY} 4%, #ffffff);
        box-shadow: 0 18px 44px rgba(18, 25, 38, 0.09);
        padding: 1rem 1rem 0.95rem;
        font-family: "Poppins", sans-serif;
    }}

    div[data-testid="stForm"] label,
    div[data-testid="stForm"] [data-testid="stWidgetLabel"] p {{
        color: #111827 !important;
        font-family: "Poppins", sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 900 !important;
        letter-spacing: 0 !important;
        line-height: 1.1 !important;
        margin-bottom: 0.28rem !important;
    }}

    div[data-testid="stForm"] div[data-baseweb="select"] > div {{
        min-height: 3.35rem;
        align-items: center;
        border-color: rgba(23, 32, 42, 0.16) !important;
        border-radius: 8px !important;
        background: rgba(255, 255, 255, 0.92) !important;
        box-shadow: 0 7px 18px rgba(18, 25, 38, 0.045);
    }}

    div[data-testid="stForm"] div[data-baseweb="select"] > div:hover,
    div[data-testid="stForm"] div[data-baseweb="select"] > div:focus-within {{
        border-color: color-mix(in srgb, {LEAGUE_PRIMARY} 44%, rgba(23, 32, 42, 0.18)) !important;
        box-shadow: 0 0 0 3px color-mix(in srgb, {LEAGUE_PRIMARY} 10%, transparent), 0 9px 20px rgba(18, 25, 38, 0.055);
    }}

    div[data-testid="stForm"] div[data-baseweb="select"],
    div[data-testid="stForm"] div[data-baseweb="select"] * {{
        font-family: "Poppins", sans-serif !important;
    }}

    div[data-testid="stForm"] div[data-baseweb="select"] input {{
        min-height: 2rem;
        color: #111827 !important;
        font-family: "Poppins", sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 800 !important;
        line-height: 2rem;
    }}

    div[data-testid="stForm"] div[data-baseweb="select"] [data-baseweb="tag"] {{
        min-height: 1.7rem;
        align-items: center;
        border-radius: 999px;
        background: color-mix(in srgb, {LEAGUE_PRIMARY} 12%, #ffffff);
        color: {LEAGUE_PRIMARY};
        font-family: "Poppins", sans-serif;
        font-size: 0.78rem;
        font-weight: 900;
    }}

    div[data-testid="stForm"] div[data-baseweb="select"] [data-baseweb="select"] {{
        min-height: 3.35rem;
    }}

    div[data-testid="stForm"] div[data-baseweb="select"] [class*="placeholder"] {{
        color: transparent !important;
        font-family: "Poppins", sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 850 !important;
        line-height: 1.2 !important;
        white-space: normal;
    }}

    div[data-testid="stForm"] input[type="text"] {{
        min-height: 2.7rem;
        border-color: rgba(23, 32, 42, 0.18) !important;
        border-radius: 8px !important;
        background: rgba(255, 255, 255, 0.96) !important;
        color: #111827 !important;
        font-family: "Poppins", sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 850 !important;
        box-shadow: 0 7px 18px rgba(18, 25, 38, 0.045);
    }}

    div[data-testid="stForm"] input[type="text"]:focus {{
        border-color: color-mix(in srgb, {LEAGUE_PRIMARY} 44%, rgba(23, 32, 42, 0.18)) !important;
        box-shadow: 0 0 0 3px color-mix(in srgb, {LEAGUE_PRIMARY} 10%, transparent), 0 9px 20px rgba(18, 25, 38, 0.055) !important;
    }}

    div[data-testid="stForm"] input[type="text"]::placeholder {{
        color: rgba(17, 24, 39, 0.36) !important;
        font-weight: 800 !important;
    }}

    div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {{
        min-height: 2.75rem;
        padding: 0.62rem 1.25rem;
        border-radius: 8px;
        border: 1px solid color-mix(in srgb, var(--trade-primary, {LEAGUE_PRIMARY}) 82%, #000 18%);
        background: linear-gradient(135deg, var(--trade-primary, {LEAGUE_PRIMARY}), color-mix(in srgb, var(--trade-primary, {LEAGUE_PRIMARY}) 72%, #111827 28%));
        color: #ffffff;
        font-family: "Poppins", sans-serif;
        font-size: 0.86rem;
        font-weight: 900;
        box-shadow: 0 12px 24px rgba(18, 25, 38, 0.16);
    }}

    div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {{
        border-color: var(--trade-secondary, {LEAGUE_SECONDARY});
        transform: translateY(-1px);
        filter: brightness(1.03);
    }}

    .sbc-trade-ledger {{
        overflow: hidden;
        margin: 0.9rem 0 1rem;
        border-radius: 8px;
        border: 1px solid color-mix(in srgb, var(--trade-ledger-primary, var(--sbc-team-primary)) 20%, rgba(23, 32, 42, 0.12));
        background: #ffffff;
        box-shadow: 0 18px 42px rgba(18,25,38,0.09);
    }}

    .sbc-trade-ledger-head {{
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.82rem 0.95rem;
        border-bottom: 1px solid rgba(23, 32, 42, 0.08);
        background: linear-gradient(135deg, color-mix(in srgb, var(--trade-ledger-primary, var(--sbc-team-primary)) 11%, #ffffff), color-mix(in srgb, var(--trade-ledger-secondary, var(--sbc-team-secondary)) 9%, #ffffff));
    }}

    .sbc-trade-ledger-head span {{
        color: var(--sbc-ink);
        font-size: 1.15rem;
        font-weight: 950;
        line-height: 1;
    }}

    .sbc-trade-ledger-head em {{
        color: var(--sbc-muted);
        font-size: 0.8rem;
        font-style: normal;
        font-weight: 850;
    }}

    .sbc-trade-ledger-wrap {{
        overflow-x: auto;
    }}

    .sbc-trade-ledger table {{
        width: 100%;
        border-collapse: collapse;
        min-width: 56rem;
    }}

    .sbc-trade-ledger th {{
        padding: 0.58rem 0.7rem;
        background: #f7f9fc;
        color: var(--sbc-muted);
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-align: left;
        text-transform: uppercase;
    }}

    .sbc-trade-ledger td {{
        padding: 0.55rem 0.7rem;
        border-top: 1px solid rgba(23, 32, 42, 0.07);
        color: var(--sbc-ink);
        font-size: 0.84rem;
        font-weight: 780;
        vertical-align: middle;
    }}

    .sbc-trade-ledger-out {{
        background: color-mix(in srgb, var(--trade-ledger-primary, var(--sbc-team-primary)) 5%, #ffffff);
    }}

    .sbc-trade-ledger-in {{
        background: color-mix(in srgb, {LEAGUE_SECONDARY} 5%, #ffffff);
    }}

    .sbc-trade-ledger-math {{
        background: #f8fafc;
    }}

    .sbc-trade-side-pill {{
        display: inline-flex;
        min-width: 5.7rem;
        justify-content: center;
        border-radius: 999px;
        background: var(--trade-ledger-primary, var(--sbc-team-primary));
        color: var(--trade-ledger-text, var(--sbc-team-text));
        font-size: 0.72rem;
        font-weight: 950;
        padding: 0.26rem 0.5rem;
    }}

    .sbc-trade-ledger-in .sbc-trade-side-pill {{
        background: #007a32;
        color: #ffffff;
    }}

    .sbc-trade-ledger-math .sbc-trade-side-pill {{
        background: #111827;
        color: #ffffff;
    }}

    .sbc-trade-player,
    .sbc-trade-ledger-team {{
        display: inline-grid;
        grid-template-columns: auto 1fr;
        align-items: center;
        gap: 0.5rem;
        min-width: 0;
    }}

    .sbc-trade-player-img {{
        width: 2.15rem;
        height: 2.15rem;
        border-radius: 999px;
        object-fit: cover;
        object-position: center 18%;
        background: #111827;
        border: 2px solid #ffffff;
        box-shadow: 0 0 0 1px rgba(23, 32, 42, 0.14);
    }}

    .sbc-trade-ledger-team img {{
        width: 1.9rem;
        height: 1.9rem;
        object-fit: contain;
    }}

    .sbc-trade-ledger-team strong {{
        color: color-mix(in srgb, var(--trade-ledger-team) 72%, #111827 28%);
        font-family: var(--trade-ledger-font), "Poppins", sans-serif;
        font-size: 0.94rem;
        font-weight: 950;
        line-height: 1.05;
    }}

    .sbc-trade-ledger-money {{
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
    }}

    .sbc-trade-ledger-muted {{
        color: var(--sbc-muted);
        font-size: 0.8rem;
        font-weight: 800;
    }}

    .sbc-trade-board-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.85rem;
        padding: 0.9rem;
    }}

    .sbc-trade-board-panel {{
        overflow: hidden;
        border-radius: 8px;
        border: 1px solid rgba(23, 32, 42, 0.1);
        background: #ffffff;
    }}

    .sbc-trade-board-out {{
        border-top: 4px solid var(--trade-ledger-primary, var(--sbc-team-primary));
    }}

    .sbc-trade-board-in {{
        border-top: 4px solid #007a32;
    }}

    .sbc-trade-board-title {{
        padding: 0.68rem 0.75rem;
        color: var(--sbc-ink);
        font-size: 1.05rem;
        font-weight: 950;
        background: #f8fafc;
        border-bottom: 1px solid rgba(23, 32, 42, 0.07);
    }}

    .sbc-trade-board-headrow,
    .sbc-trade-board-row {{
        display: grid;
        grid-template-columns: 5.5rem minmax(11rem, 1.5fr) minmax(8rem, 1fr) 6.5rem;
        align-items: center;
        gap: 0.55rem;
    }}

    .sbc-trade-board-headrow {{
        padding: 0.5rem 0.68rem;
        background: #f3f6fa;
        color: var(--sbc-muted);
        font-size: 0.68rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .sbc-trade-board-row {{
        min-height: 3.25rem;
        padding: 0.5rem 0.68rem;
        border-top: 1px solid rgba(23, 32, 42, 0.07);
    }}

    .sbc-trade-board-out .sbc-trade-board-row {{
        background: color-mix(in srgb, var(--trade-ledger-primary, var(--sbc-team-primary)) 4%, #ffffff);
    }}

    .sbc-trade-board-in .sbc-trade-board-row {{
        background: color-mix(in srgb, #007a32 4%, #ffffff);
    }}

    .sbc-trade-board-type {{
        color: var(--sbc-muted);
        font-size: 0.74rem;
        font-weight: 950;
        text-transform: uppercase;
    }}

    .sbc-trade-board-asset {{
        min-width: 0;
        color: var(--sbc-ink);
        font-size: 0.88rem;
        font-weight: 900;
        line-height: 1.12;
    }}

    .sbc-trade-board-asset em {{
        display: block;
        color: var(--sbc-muted);
        font-size: 0.72rem;
        font-style: normal;
        font-weight: 760;
        margin-top: 0.12rem;
    }}

    .sbc-trade-board-money {{
        color: var(--sbc-ink);
        font-size: 0.84rem;
        font-variant-numeric: tabular-nums;
        font-weight: 950;
        text-align: right;
    }}

    .sbc-trade-board-empty {{
        padding: 1rem;
        color: var(--sbc-muted);
        font-size: 0.86rem;
        font-weight: 850;
    }}

    .sbc-trade-math-strip {{
        display: grid;
        grid-template-columns: repeat(8, minmax(0, 1fr));
        gap: 0.6rem;
        padding: 0 0.9rem 0.85rem;
    }}

    .sbc-trade-math-strip span {{
        display: grid;
        gap: 0.12rem;
        border-radius: 8px;
        background: #f8fafc;
        border: 1px solid rgba(23, 32, 42, 0.08);
        padding: 0.68rem 0.75rem;
    }}

    .sbc-trade-math-strip strong {{
        color: var(--sbc-ink);
        font-size: 0.9rem;
        font-weight: 950;
        font-variant-numeric: tabular-nums;
        line-height: 1.15;
        overflow-wrap: anywhere;
    }}

    .sbc-trade-math-strip em {{
        color: var(--sbc-muted);
        font-size: 0.7rem;
        font-style: normal;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .sbc-trade-math-strip .sbc-trade-apron-clear {{
        border-color: rgba(0, 122, 50, 0.24);
        background: linear-gradient(135deg, rgba(0, 122, 50, 0.12), #ffffff);
    }}

    .sbc-trade-math-strip .sbc-trade-apron-watch {{
        border-color: rgba(159, 111, 0, 0.28);
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.18), #ffffff);
    }}

    .sbc-trade-math-strip .sbc-trade-apron-block {{
        border-color: rgba(185, 28, 28, 0.28);
        background: linear-gradient(135deg, rgba(185, 28, 28, 0.13), #ffffff);
    }}

    .sbc-trade-narrative {{
        margin: 0 0.9rem 0.95rem;
        border-radius: 8px;
        border-left: 5px solid var(--trade-ledger-primary, var(--sbc-team-primary));
        background: linear-gradient(135deg, color-mix(in srgb, var(--trade-ledger-primary, var(--sbc-team-primary)) 8%, #ffffff), #ffffff);
        color: #1f2937;
        font-size: 0.98rem;
        font-weight: 780;
        line-height: 1.45;
        padding: 0.85rem 0.95rem;
    }}

    .sbc-trade-rule-card {{
        display: grid;
        grid-template-columns: 5.2rem 1fr;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 0.62rem;
        border-radius: 8px;
        border: 1px solid color-mix(in srgb, var(--rule-color) 24%, rgba(23, 32, 42, 0.1));
        border-left: 5px solid var(--rule-color);
        background: linear-gradient(135deg, color-mix(in srgb, var(--rule-color) 8%, #ffffff), #ffffff);
        box-shadow: 0 10px 24px rgba(18, 25, 38, 0.055);
        padding: 0.72rem 0.82rem;
    }}

    .sbc-trade-rule-clear {{ --rule-color: #007a32; }}
    .sbc-trade-rule-watch {{ --rule-color: #9f6f00; }}
    .sbc-trade-rule-block {{ --rule-color: #b91c1c; }}

    .sbc-trade-rule-status {{
        display: grid;
        place-items: center;
        min-height: 2.1rem;
        border-radius: 999px;
        background: var(--rule-color);
        color: #ffffff;
        font-size: 0.68rem;
        font-weight: 950;
        letter-spacing: 0.08em;
    }}

    .sbc-trade-rule-card strong {{
        display: block;
        color: var(--sbc-ink);
        font-size: 0.94rem;
        font-weight: 950;
        line-height: 1.08;
    }}

    .sbc-trade-rule-card span {{
        display: block;
        color: var(--sbc-muted);
        font-size: 0.82rem;
        font-weight: 760;
        line-height: 1.32;
        margin-top: 0.12rem;
    }}

    .sbc-award-card,
    .sbc-award-team-card {{
        overflow: hidden;
        margin-bottom: 0.85rem;
        min-height: 100%;
        border: 1px solid color-mix(in srgb, var(--award-accent, {LEAGUE_PRIMARY}) 26%, rgba(23, 32, 42, 0.12));
        border-top: 4px solid var(--award-accent, {LEAGUE_PRIMARY});
        border-radius: 8px;
        background: linear-gradient(135deg, #ffffff 0%, color-mix(in srgb, var(--award-accent, {LEAGUE_PRIMARY}) 7%, #ffffff) 100%);
        box-shadow: 0 16px 36px rgba(18, 25, 38, 0.085);
    }}

    .sbc-award-card-blue {{ --award-accent: {LEAGUE_PRIMARY}; }}
    .sbc-award-card-green {{ --award-accent: {LEAGUE_SECONDARY}; }}
    .sbc-award-card-red {{ --award-accent: #b91c1c; }}
    .sbc-award-card-gold {{ --award-accent: #c99720; }}
    .sbc-award-card-purple {{ --award-accent: #7c3aed; }}

    .sbc-award-card-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.7rem;
        padding: 0.72rem 0.85rem;
        background: color-mix(in srgb, var(--award-accent, {LEAGUE_PRIMARY}) 13%, #ffffff);
        border-bottom: 1px solid color-mix(in srgb, var(--award-accent, {LEAGUE_PRIMARY}) 18%, rgba(23, 32, 42, 0.08));
    }}

    .sbc-award-card-top span {{
        color: var(--sbc-ink);
        font-size: 0.92rem;
        font-weight: 950;
        line-height: 1.1;
    }}

    .sbc-award-card-top em {{
        display: inline-grid;
        place-items: center;
        min-width: 3.1rem;
        border-radius: 999px;
        background: var(--award-accent, {LEAGUE_PRIMARY});
        color: #ffffff;
        font-size: 0.76rem;
        font-style: normal;
        font-weight: 950;
        padding: 0.28rem 0.5rem;
    }}

    .sbc-award-player-grid {{
        display: grid;
        gap: 0.55rem;
        padding: 0.78rem;
    }}

    .sbc-award-player-grid-compact {{
        grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
    }}

    .sbc-award-player {{
        display: grid;
        grid-template-columns: 3.2rem 1fr;
        align-items: center;
        gap: 0.65rem;
        min-width: 0;
        border-radius: 8px;
        background: linear-gradient(135deg, color-mix(in srgb, var(--award-row-color, var(--award-accent, {LEAGUE_PRIMARY})) 9%, #ffffff), color-mix(in srgb, var(--award-row-secondary, var(--award-accent, {LEAGUE_PRIMARY})) 5%, #ffffff));
        border: 1px solid color-mix(in srgb, var(--award-row-color, var(--award-accent, {LEAGUE_PRIMARY})) 20%, rgba(23, 32, 42, 0.08));
        border-left: 4px solid var(--award-row-color, var(--award-accent, {LEAGUE_PRIMARY}));
        padding: 0.48rem;
    }}

    .sbc-award-player-compact {{
        grid-template-columns: 2.6rem 1fr;
    }}

    .sbc-award-headshot {{
        width: 3.2rem;
        height: 3.2rem;
        border-radius: 999px;
        object-fit: cover;
        object-position: center 18%;
        background: #111827;
        border: 2px solid #ffffff;
        box-shadow: 0 0 0 1px rgba(23, 32, 42, 0.16);
    }}

    .sbc-award-player-compact .sbc-award-headshot {{
        width: 2.6rem;
        height: 2.6rem;
    }}

    .sbc-award-player strong {{
        display: block;
        color: var(--sbc-ink);
        font-family: var(--award-row-font), "Poppins", sans-serif;
        font-size: 0.9rem;
        font-weight: 950;
        line-height: 1.1;
    }}

    .sbc-award-week {{
        display: inline-block;
        color: var(--award-accent, {LEAGUE_PRIMARY});
        font-size: 0.68rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .sbc-award-mini-logo {{
        width: 1.55rem;
        height: 1.55rem;
        object-fit: contain;
        margin-top: 0.18rem;
        filter: drop-shadow(0 2px 4px rgba(18,25,38,0.12));
    }}

    .sbc-award-wordmark-wrap {{
        display: grid;
        place-items: center;
        min-height: 7.6rem;
        padding: 1rem;
        background: linear-gradient(135deg, color-mix(in srgb, var(--award-team-color, {LEAGUE_PRIMARY}) 13%, #ffffff), color-mix(in srgb, var(--award-team-secondary, {LEAGUE_SECONDARY}) 13%, #ffffff));
    }}

    .sbc-award-team-feature .sbc-award-wordmark-wrap {{
        min-height: 10rem;
    }}

    .sbc-award-wordmark {{
        max-width: min(100%, 18rem);
        max-height: 8rem;
        object-fit: contain;
        filter: drop-shadow(0 10px 18px rgba(18,25,38,0.16));
    }}

    .sbc-award-team-spotlight {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.72rem;
        text-align: center;
    }}

    .sbc-award-team-spotlight-stacked {{
        display: grid;
        justify-items: center;
        gap: 0.44rem;
        width: 100%;
    }}

    .sbc-award-team-spotlight img {{
        width: 4.5rem;
        height: 4.5rem;
        object-fit: contain;
        filter: drop-shadow(0 12px 20px rgba(18,25,38,0.16));
    }}

    .sbc-award-team-spotlight-stacked img {{
        width: 4.75rem;
        height: 4.75rem;
    }}

    .sbc-award-team-feature .sbc-award-team-spotlight {{
        display: grid;
    }}

    .sbc-award-team-feature .sbc-award-team-spotlight img {{
        width: min(7.5rem, 56%);
        height: 7.5rem;
    }}

    .sbc-award-team-spotlight strong {{
        color: color-mix(in srgb, var(--award-team-color, {LEAGUE_PRIMARY}) 78%, #111827 22%);
        font-family: var(--award-team-font), "Poppins", sans-serif;
        font-size: clamp(1.2rem, 2.6vw, 2.1rem);
        font-weight: 950;
        line-height: 1;
    }}

    .sbc-award-team-spotlight-stacked strong {{
        max-width: 100%;
        font-size: 1rem;
        line-height: 1.05;
        text-wrap: balance;
    }}

    .sbc-award-team-footer {{
        padding: 0.75rem 0.85rem;
    }}

    .sbc-award-team-mark {{
        display: inline-grid;
        grid-template-columns: 2.25rem 1fr;
        align-items: center;
        gap: 0.55rem;
    }}

    .sbc-award-team-mark img {{
        width: 2.25rem;
        height: 2.25rem;
        object-fit: contain;
    }}

    .sbc-award-team-mark strong {{
        color: color-mix(in srgb, var(--award-team-color, {LEAGUE_PRIMARY}) 70%, #111827 30%);
        font-size: 0.94rem;
        font-weight: 950;
        line-height: 1.1;
    }}

    .sbc-award-empty,
    .sbc-award-team-missing {{
        color: var(--sbc-muted);
        font-size: 0.84rem;
        font-weight: 850;
        padding: 0.75rem;
    }}

    .sbc-draft-detail {{
        color: var(--sbc-muted) !important;
        font-size: 0.74rem !important;
        font-weight: 750 !important;
        text-align: left !important;
        white-space: normal;
    }}

    .sbc-draft-time {{
        color: var(--sbc-team-primary) !important;
        font-weight: 950 !important;
        font-variant-numeric: tabular-nums;
    }}

    h1, h2, h3 {{
        color: var(--sbc-ink);
        letter-spacing: 0;
    }}

    h2, h3 {{
        font-weight: 850;
    }}

    hr {{
        margin: 1.15rem 0;
        border-color: rgba(23, 32, 42, 0.08);
    }}

    button[data-baseweb="tab"] {{
        height: 3rem;
        padding: 0 1rem;
        border-radius: 8px 8px 0 0;
        color: var(--sbc-muted);
        font-weight: 800;
        border-bottom: 2px solid transparent;
    }}

    button[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--sbc-ink);
        background: #ffffff;
        border-bottom-color: var(--sbc-team-primary);
    }}

    div[role="radiogroup"] label,
    div[role="radiogroup"] label *,
    div[role="radiogroup"] p,
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] label *,
    [data-testid="stRadio"] p,
    .stButton > button,
    .stButton > button *,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stFormSubmitButton"] button * {{
        color: #111827 !important;
        fill: #111827 !important;
    }}

    [data-testid="stRadio"] > div {{
        gap: 0.42rem;
    }}

    div[role="radiogroup"] label,
    [data-testid="stRadio"] label {{
        min-height: 2.38rem;
        border-radius: 999px;
        border: 1px solid color-mix(in srgb, {LEAGUE_PRIMARY} 16%, rgba(23, 32, 42, 0.14));
        background: linear-gradient(135deg, #ffffff, color-mix(in srgb, {LEAGUE_SECONDARY} 5%, #ffffff));
        box-shadow: 0 8px 18px rgba(18, 25, 38, 0.045);
        padding: 0.18rem 0.72rem;
        transition: border-color 140ms ease, background 140ms ease, box-shadow 140ms ease, transform 140ms ease;
    }}

    div[role="radiogroup"] label:hover,
    [data-testid="stRadio"] label:hover {{
        border-color: color-mix(in srgb, {LEAGUE_SECONDARY} 52%, {LEAGUE_PRIMARY});
        background: linear-gradient(135deg, color-mix(in srgb, {LEAGUE_PRIMARY} 8%, #ffffff), color-mix(in srgb, {LEAGUE_SECONDARY} 10%, #ffffff));
        box-shadow: 0 10px 22px rgba(18, 25, 38, 0.075);
        transform: translateY(-1px);
    }}

    div[role="radiogroup"] label:has(input:checked),
    [data-testid="stRadio"] label:has(input:checked),
    div[role="radiogroup"] label:has([aria-checked="true"]),
    [data-testid="stRadio"] label:has([aria-checked="true"]) {{
        border-color: color-mix(in srgb, {LEAGUE_PRIMARY} 54%, {LEAGUE_SECONDARY});
        background: linear-gradient(135deg, color-mix(in srgb, {LEAGUE_PRIMARY} 28%, #ffffff), color-mix(in srgb, {LEAGUE_SECONDARY} 24%, #ffffff));
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.54), 0 12px 26px rgba(18, 25, 38, 0.11);
    }}

    div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p,
    [data-testid="stRadio"] label [data-testid="stMarkdownContainer"] p {{
        font-weight: 900 !important;
    }}

    div[role="radiogroup"] input[type="radio"],
    [data-testid="stRadio"] input[type="radio"] {{
        accent-color: {LEAGUE_PRIMARY};
    }}

    div[role="radiogroup"] label:has(input:checked) input[type="radio"],
    [data-testid="stRadio"] label:has(input:checked) input[type="radio"] {{
        accent-color: {LEAGUE_SECONDARY};
    }}

    [data-testid="stRadio"] label:has(input:checked) *,
    [data-testid="stRadio"] label:has([aria-checked="true"]) * {{
        color: #ffffff !important;
        fill: #ffffff !important;
    }}

    .stButton > button[kind="primary"],
    .stButton > button[kind="primary"] *,
    [data-testid="stButton"] > button[kind="primary"],
    [data-testid="stButton"] > button[kind="primary"] * {{
        color: #ffffff !important;
        fill: #ffffff !important;
    }}

    [data-testid="stMetric"] {{
        background: var(--sbc-panel);
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 20%, var(--sbc-border));
        border-top: 4px solid var(--sbc-team-primary);
        border-radius: 8px;
        box-shadow: 0 10px 30px rgba(18, 25, 38, 0.06);
        padding: 0.65rem 0.75rem;
        min-height: 6.75rem;
    }}

    [data-testid="stMetricLabel"] p {{
        color: var(--sbc-muted);
        font-size: 0.78rem;
        font-weight: 850;
        line-height: 1.1;
    }}

    [data-testid="stMetric"] [data-testid="stTooltipIcon"],
    [data-testid="stMetric"] button,
    [data-testid="stMetric"] svg {{
        color: var(--sbc-team-primary) !important;
        fill: var(--sbc-team-primary) !important;
        opacity: 1 !important;
    }}

    [data-testid="stMetric"] [data-testid="stTooltipIcon"]:hover,
    [data-testid="stMetric"] button:hover,
    [data-testid="stMetric"] button:hover svg {{
        color: var(--sbc-team-secondary) !important;
        fill: var(--sbc-team-secondary) !important;
    }}

    [data-testid="stMetricValue"] {{
        color: var(--sbc-ink);
        font-size: clamp(1.05rem, 1.45vw, 1.55rem);
        font-weight: 900;
        line-height: 1.05;
        overflow-wrap: anywhere;
    }}

    [data-testid="stMetricDelta"] {{
        font-size: 0.78rem;
        font-weight: 800;
        line-height: 1.1;
    }}

    .sbc-player-count-metric {{
        background: var(--sbc-panel);
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 20%, var(--sbc-border));
        border-top: 4px solid var(--sbc-team-primary);
        border-radius: 8px;
        box-shadow: 0 10px 30px rgba(18, 25, 38, 0.06);
        padding: 0.65rem 0.75rem;
        min-height: 6.75rem;
    }}

    .sbc-player-count-label {{
        color: var(--sbc-muted);
        font-size: 0.78rem;
        font-weight: 850;
        line-height: 1.1;
        margin-bottom: 0.35rem;
    }}

    .sbc-player-count-value {{
        color: var(--sbc-ink);
        font-size: clamp(1.05rem, 1.45vw, 1.55rem);
        font-weight: 900;
        line-height: 1.05;
        margin-bottom: 0.55rem;
    }}

    .sbc-player-count-pill {{
        display: inline-flex;
        align-items: center;
        min-height: 1.45rem;
        border-radius: 999px;
        background: #e5e7eb;
        color: #111827 !important;
        border: 1px solid #cbd5e1;
        padding: 0.12rem 0.55rem;
        font-size: 0.78rem;
        font-weight: 850;
        line-height: 1.1;
    }}

    [data-testid="stDataFrame"] {{
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--sbc-border);
        box-shadow: 0 12px 32px rgba(18, 25, 38, 0.07);
    }}

    div[data-testid="stForm"] {{
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 14%, rgba(23, 32, 42, 0.12));
        border-radius: 8px;
        background:
            linear-gradient(180deg, rgba(255,255,255,0.94), rgba(255,255,255,0.82)),
            color-mix(in srgb, var(--sbc-team-secondary) 4%, #ffffff);
        box-shadow: 0 18px 44px rgba(18, 25, 38, 0.09);
        padding: 1rem 1rem 0.95rem;
        font-family: "Poppins", sans-serif;
    }}

    .stButton > button,
    [data-testid="stFormSubmitButton"] button {{
        min-height: 2.65rem;
        padding: 0.58rem 1.18rem;
        border-radius: 8px;
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 82%, #000 18%);
        background: linear-gradient(135deg, var(--sbc-team-primary), color-mix(in srgb, var(--sbc-team-primary) 76%, #111827 24%));
        color: #111827;
        font-family: "Poppins", sans-serif;
        font-size: 0.86rem;
        font-weight: 900;
        box-shadow: 0 12px 24px rgba(18, 25, 38, 0.16);
    }}

    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] button:hover {{
        border-color: var(--sbc-team-secondary);
        transform: translateY(-1px);
        filter: brightness(1.03);
    }}

    .stAlert {{
        border-radius: 8px;
    }}

    img {{
        image-rendering: auto;
    }}

    @media (max-width: 850px) {{
        .block-container,
        [data-testid="stMainBlockContainer"] {{
            padding-top: 5.6rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }}

        .sbc-team-hero-inner {{
            grid-template-columns: 4.8rem 1fr;
        }}

        .sbc-logo-frame {{
            width: 5.5rem;
            height: 5.5rem;
        }}

        .sbc-team-title {{
            font-size: 0.72rem;
        }}

        .sbc-team-typeface {{
            font-size: clamp(1.85rem, 8vw, 3.15rem);
        }}

        .sbc-draft-hero-inner {{
            grid-template-columns: 4.4rem 1fr;
            gap: 0.85rem;
        }}

        .sbc-draft-logo {{
            width: 4.4rem;
            height: 4.4rem;
        }}

        .sbc-draft-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}

        .sbc-live-summary {{
            grid-template-columns: 1fr;
        }}

        .sbc-chart-head {{
            align-items: start;
            flex-direction: column;
        }}

        .sbc-live-board {{
            overflow-x: auto;
        }}

        .sbc-live-board-grid {{
            min-width: 34rem;
        }}

        .sbc-pick-panel-head {{
            grid-template-columns: auto 1fr;
        }}

        .sbc-pick-count {{
            grid-column: 1 / -1;
            justify-self: start;
        }}

        .sbc-score-grid,
        .sbc-standings-layout,
        .sbc-payout-grid {{
            grid-template-columns: 1fr;
        }}
    }}

    @media (max-width: 560px) {{
        .sbc-draft-grid {{
            grid-template-columns: 1fr;
        }}

        .sbc-draft-heading {{
            font-size: clamp(1.7rem, 10vw, 2.55rem);
        }}

        .sbc-draft-subcopy {{
            font-size: 0.86rem;
        }}
    }}

    /* Legacy sidebar selectors kept harmless in case Streamlit injects shell nodes. */
    section[data-testid="stSidebar"] {{
        background-color: var(--sbc-team-primary);
    }}
    </style>""",
    unsafe_allow_html=True)

render_html(f"""
    <div class="sbc-app-masthead sbc-league-masthead">
        <img src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
        <div>
            <div class="sbc-app-eyebrow">Sports Business Classroom Fantasy Basketball League</div>
            <div class="sbc-app-title">SBC League Office</div>
        </div>
    </div>
    """)

if selected_team_changed and SelectedTeam == "Honolulu":
    st.balloons()
if selected_team_changed and SelectedTeam == "Manchester":
    st.snow()
main_page = st.radio(
    "SBC Office",
    ["Team Hub", "League Hub", "Trade Machine", "Free Agency", "About", "Data Checks"],
    index=0,
    format_func=nav_label(MAIN_NAV_LABELS),
    key="sbc_main_page",
    horizontal=True,
    label_visibility="collapsed",
)
st.markdown(
    f"<script>document.documentElement.dataset.sbcMainTab = '{'team' if main_page == 'Team Hub' else 'league'}';</script>",
    unsafe_allow_html=True,
)
selected_team_page = None
selected_league_page = None
selected_history_page = None
selected_free_agency_page = None
LeagueHistoryYear = current_year
if main_page == "Free Agency":
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">{current_year-1}-{str(current_year)[-2:]} League Office</div>
                    <div class="sbc-draft-heading">Free Agency</div>
                    <div class="sbc-draft-subcopy">A commissioner workbench for bid intake, active offers, team timing, cap context, and exception status.</div>
                </div>
            </div>
        </div>
        """)

    selected_free_agency_page = st.radio(
        "Free Agency View",
        ["League View", "My Bids", "Commish View"],
        format_func=nav_label(FREE_AGENCY_NAV_LABELS),
        horizontal=True,
        key="sbc_free_agency_page",
        label_visibility="collapsed",
    )
    fa_league_view = load_free_agency_league_view()
    if selected_free_agency_page == "League View":
        render_html(f"""
            <style>
                .sbc-fa-league-note {{
                    margin: 0 0 0.85rem;
                    padding: 0.7rem 0.85rem;
                    border: 1px solid color-mix(in srgb, {LEAGUE_SECONDARY} 24%, rgba(23, 32, 42, 0.12));
                    border-left: 0.32rem solid {LEAGUE_SECONDARY};
                    border-radius: 8px;
                    background: color-mix(in srgb, {LEAGUE_SECONDARY} 7%, #ffffff);
                    color: var(--sbc-ink);
                    font-size: 0.92rem;
                    font-weight: 800;
                }}
                .sbc-fa-league-note a {{
                    color: {LEAGUE_PRIMARY};
                    font-weight: 950;
                    text-decoration: none;
                    border-bottom: 1px solid currentColor;
                }}
            </style>
            <div class="sbc-fa-league-note">
                Ready to make an offer? Submit free agency bids through the
                <a href="{FREE_AGENCY_SURVEY_URL}" target="_blank" rel="noopener noreferrer">SBCFBL Free Agency Survey</a>.
            </div>
        """)
        render_html('<div class="sbc-section-label">Free Agency Board</div>')
        render_free_agency_league_table(fa_league_view)

    if selected_free_agency_page == "My Bids":
        team_key = st.text_input("Team code", type="password", key="sbc_free_agency_team_bid_key")
        my_team = free_agency_team_from_code(team_key.strip())
        if my_team not in team_info:
            render_html('<div class="sbc-empty-state">Enter your team code to view your submitted free agency bids.</div>')
        else:
            fa_bids = load_free_agency_bids()
            available_players = []
            if isinstance(fa_league_view, pd.DataFrame) and "Player" in fa_league_view.columns:
                available_players = fa_league_view["Player"].tolist()
            signed_players = free_agency_signed_players(fa_league_view)
            fa_active_bids, fa_excluded_bids = free_agency_bid_audit(fa_bids, signed_players=signed_players, available_players=available_players, league_view=fa_league_view)
            render_free_agency_my_bids(my_team, fa_bids, fa_active_bids, fa_excluded_bids, fa_league_view)

    if selected_free_agency_page == "Commish View":
        commish_key = st.text_input("Commissioner key", type="password", key="sbc_free_agency_commish_key")
        if commish_key.strip() != FREE_AGENCY_PASSWORD:
            render_html('<div class="sbc-empty-state">Enter the commissioner key to view free agency controls.</div>')
        else:
            fa_bids = load_free_agency_bids()
            fa_bid_players = load_free_agency_bid_players()
            signed_text = st.text_area(
                "Signed players to exclude",
                placeholder="One player per line. This is temporary until the signing tracker is wired in.",
                key="sbc_free_agency_signed_players",
            )
            signed_players = [line.strip() for line in signed_text.splitlines() if line.strip()]
            signed_players.extend(free_agency_signed_players(fa_league_view))
            available_players = []
            if isinstance(fa_league_view, pd.DataFrame) and "Player" in fa_league_view.columns:
                available_players = fa_league_view["Player"].tolist()
            fa_active_bids, fa_excluded_bids = free_agency_bid_audit(fa_bids, signed_players=signed_players, available_players=available_players, league_view=fa_league_view)
            render_free_agency_commish_desk(fa_active_bids, fa_excluded_bids, fa_league_view, all_bids=fa_bids, bid_players=fa_bid_players)

if main_page == "Team Hub":
    picker_col, _ = st.columns([1.15, 3.85], vertical_alignment="bottom")
    with picker_col:
        st.selectbox("Choose your team", Teams, key="_sbc_selected_team")

    selected_team_page = st.radio(
        "Team Hub View",
        ["Cap", "Picks", "Live", "Schedule", "History"],
        format_func=nav_label(TEAM_NAV_LABELS),
        horizontal=True,
        key="sbc_team_page",
        label_visibility="collapsed",
    )

if main_page == "League Hub":
    selected_league_page = st.radio(
        "League Hub View",
        ["Overview", "Scoreboard", "Standings", "Players", "Draft Picks", "History"],
        format_func=nav_label(LEAGUE_NAV_LABELS),
        horizontal=True,
        key="sbc_league_page",
        label_visibility="collapsed",
    )

    if selected_league_page == "History":
        league_history_year_options = schedule_year_options_for_history()
        default_league_history_year = current_year if current_year in league_history_year_options else league_history_year_options[-1]
        LeagueHistoryYear = st.selectbox(
            "History Year",
            options=league_history_year_options,
            index=league_history_year_options.index(default_league_history_year),
            key="league_history_year",
        )
        selected_history_page = st.radio(
            "League History View",
            ["Overview", "Scoreboard", "Playoff Bracket", "In-Season Tournament", "Player Stats", "All-Time Stats", "Awards", "Draft History"],
            format_func=nav_label(HISTORY_NAV_LABELS),
            horizontal=True,
            key="sbc_history_page",
            label_visibility="collapsed",
        )

if main_page == "Team Hub" and selected_team_page == "Cap":
    _legacy_tab1 = r'''
    st.subheader(f"{SelectedTeam} Cap Sheet for {current_year-1}-{str(current_year)[-2:]} Season")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label = "Salary Cap", value = current_salary_cap, delta = "6.669%", delta_color = "normal", help = "Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border = True, format = "dollar")
    
    with col2:
        st.metric(label = "Luxury Tax", value = current_luxury_tax, delta = "6.669%", delta_color = "normal", help = "Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border = True, format = "dollar")
    
    with col3:
        st.metric(label = "Apron #1", value = current_apron_1, delta = "6.669%", delta_color = "normal", help = "Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border = True, format = "dollar")
    
    with col4:
        st.metric(label = "Apron #2", value = current_apron_2, delta = "6.669%", delta_color = "normal", help = "Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade–related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border = True, format = "dollar")

    col1, col2 = st.columns([1, 4])

    with col1:
        st.divider()

        st.markdown("""
            **Cap Sheet Legend:** \n
            <span style="background-color:#FCE5CD;padding:6px 20px;border-radius:5px;">&nbsp;</span> Guaranteed \n 
            <span style="background-color:#F4CCCC;padding:6px 20px;border-radius:5px;">&nbsp;</span> Non-Guaranteed \n
            <span style="background-color:#CFE2F3;padding:6px 20px;border-radius:5px;">&nbsp;</span> Team Option \n
            <span style="background-color:#D9D2E9;padding:6px 20px;border-radius:5px;">&nbsp;</span> Unrestricted \n
            <span style="background-color:#CFFFFF;padding:6px 20px;border-radius:5px;">&nbsp;</span> Restricted \n
            <span style="background-color:#D9D9D9;padding:6px 20px;border-radius:5px;">&nbsp;</span> Dead
            """, unsafe_allow_html=True)

        st.metric(label = "Players", value = active_player_n(df, SelectedTeam), delta = inactive_player_n(df, SelectedTeam), delta_color = "off", help = "The first number shows active roster players (up to 14, plus up to 3 IR). Teams must carry at least 12 active players, or face penalties after 14 days. The second number represents non-active players, including overseas players, draft rights, retired, and waived players and there is no limit. To qualify as overseas, a drafted player must have spent their entire SBC career abroad, with status locking on opening night.", border = True, format = "plain", delta_arrow = "off")
    
        st.metric(label = "Cap Total", value = get_cap_total(df, exceptions, SelectedTeam), delta = get_cap_total(df, exceptions, SelectedTeam)-current_salary_cap, delta_color = "inverse", help = "The first number shows total team salary, including all active and inactive player salaries, cap holds for unrenounced free agents, incomplete roster charges, and all exceptions (Mid-Level, Bi-Annual, Disabled Player, and Trade). The second number shows how much room remains relative to the Salary Cap.", border = True, format = "dollar")
    
        st.metric(label = "Tax Total", value = get_tax_total(df, SelectedTeam), delta = get_tax_total(df, SelectedTeam)-current_luxury_tax, delta_color = "inverse", help = "The first number shows total team salary against the luxury tax, including all active and inactive player salaries and incomplete roster charges. Unlike the real NBA, rookie and second-year undrafted fees are not included. The second number shows remaining space relative to the Luxury Tax.", border = True, format = "dollar")
    
        st.metric(label = "Apron Space", value = team_hard_cap(base_cap, SelectedTeam), delta = team_hard_cap_n(df, SelectedTeam, base_cap), help = "The first value indicates whether the team is uncapped, capped at the first apron, or capped at the second apron while the second value shows how far the team is from the applicable cap ", border = True, format = "dollar")
    
        st.metric(label = "Entry Fee", value = base_fee(df, SelectedTeam, base_cap), delta = luxury_fee(df, SelectedTeam, base_cap), delta_color = "inverse", help = "The SBCFBL uses a 3,000,000‑1 scale. The first number is the base entry fee, calculated from the Tax Total plus a $3.00 In-Season Tournament fee. The second number shows the Luxury Tax penalty for the season, scaled as a payable fee.", border = True, format = "dollar")
    
        st.metric(label = "Balance", value = net_fee(df, SelectedTeam, base_cap), delta = amount_paid(base_cap, SelectedTeam), delta_color = "normal", help = "The first number shows current total owed for the season, including base payment, In-Season Tournament fee, tax penalties, winnings, and tax payouts. The second number shows how much has been paid so far.", border = True, format = "dollar")

    with col2:

        st.subheader("Active Players")
        active_player_df = active_players(df, pics, SelectedTeam)
        active_player_df = (active_player_df.style
            .apply(lambda row: style_salaries(row, type_colors), axis=1)  
            .format({c: "${:,.0f}" for c in active_player_df.columns if re.match(r"\d{4}", c)}))
        st.dataframe(active_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order + ["Bird Rights"], column_config={" ": st.column_config.ImageColumn(" ")})

        overseas_player_df = overseas_players(df, pics, SelectedTeam)
        if overseas_player_df.shape[0] > 0:
            st.subheader("Overseas Players")
            overseas_player_df = (overseas_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in overseas_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(overseas_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order + ["Bird Rights"], column_config={" ": st.column_config.ImageColumn(" ")})
        
        dead_player_df = dead_players(df, pics, SelectedTeam)
        if dead_player_df.shape[0] > 0:
            st.subheader("Dead Players")
            dead_player_df = (dead_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in dead_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(dead_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order, column_config={" ": st.column_config.ImageColumn(" ")})

    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

    with col1:
        st.subheader("Exceptions")
        exception_df = exception_table(exceptions, SelectedTeam)
        exception_df = (exception_df.style
            .format({"Amount": "${:,.0f}"}))
        st.dataframe(exception_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—")

    with col2:
        free_agent_player_df = free_agent_players(df, pics, SelectedTeam)
        if free_agent_player_df.shape[0] > 0:
            st.subheader("Upcoming Free Agents")
            free_agent_player_df = (free_agent_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in free_agent_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(free_agent_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + [str(current_year+ year_offset), "Bird Rights"], column_config={" ": st.column_config.ImageColumn(" ")})

    with col3:
        restricted_df = trade_restrictions(df, pics, SelectedTeam)
        if restricted_df.shape[0] > 0:
            st.subheader("Trade Restrictions")
            st.dataframe(restricted_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={" ": st.column_config.ImageColumn(" ")})

    with col4:
        draft_retired_player_df = draft_retired_players(df, pics, SelectedTeam)
        if draft_retired_player_df.shape[0] > 0:
            st.subheader("Draft Rights & Retired")
            draft_retired_player_df = (draft_retired_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in draft_retired_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(draft_retired_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=(" ", "Player"), column_config={" ": st.column_config.ImageColumn(" ")})

    '''

    season_label = f"{current_year-1}-{str(current_year)[-2:]}"
    cap_total = get_cap_total(df, exceptions, SelectedTeam)
    tax_total = get_tax_total(df, SelectedTeam)
    cap_space_delta = current_salary_cap - cap_total
    tax_space_delta = current_luxury_tax - tax_total
    apron_space_delta = team_hard_cap_n(df, SelectedTeam, base_cap)
    if apron_space_delta is not None:
        apron_space_delta = -apron_space_delta
    active_count = active_player_n(df, SelectedTeam)
    inactive_count = inactive_player_n(df, SelectedTeam)

    render_html(f"""
        <div class="sbc-draft-hero sbc-team-branded">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{team_logo_html}" alt="{team_name_html} logo">
                <div>
                    <div class="sbc-draft-eyebrow">{season_label} Season Cap Office</div>
                    <div class="sbc-draft-heading">{team_name_html} {nickname_html} Cap</div>
                    <div class="sbc-draft-subcopy">Roster construction, cap position, tax exposure, exceptions, free agents, and rights inventory.</div>
                </div>
            </div>
        </div>
        """)

    render_html('<div class="sbc-section-label">League Thresholds</div>')
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Salary Cap", value=current_salary_cap, delta="6.669%", delta_color="normal", help="Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border=True, format="dollar")
    with col2:
        st.metric(label="Luxury Tax", value=current_luxury_tax, delta="6.669%", delta_color="normal", help="Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border=True, format="dollar")
    with col3:
        st.metric(label="Apron #1", value=current_apron_1, delta="6.669%", delta_color="normal", help="Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border=True, format="dollar")
    with col4:
        st.metric(label="Apron #2", value=current_apron_2, delta="6.669%", delta_color="normal", help="Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade-related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border=True, format="dollar")

    render_html('<div class="sbc-section-label">Team Snapshot</div>')
    snap1, snap2, snap3 = st.columns([1, 1, 2])
    with snap1:
        st.metric(label="Cap Total", value=cap_total, delta=cap_space_delta, delta_color="normal", help="The first number shows total team salary, including all active and inactive player salaries, cap holds for unrenounced free agents, incomplete roster charges, and all exceptions (Mid-Level, Bi-Annual, Disabled Player, and Trade). The second number shows how much room remains relative to the Salary Cap; green is under, red is over.", border=True, format="dollar")
    with snap2:
        st.metric(label="Tax Total", value=tax_total, delta=tax_space_delta, delta_color="normal", help="The first number shows total team salary against the luxury tax, including all active and inactive player salaries and incomplete roster charges. Unlike the real NBA, rookie and second-year undrafted fees are not included. The second number shows remaining space relative to the Luxury Tax; green is under, red is over.", border=True, format="dollar")
    with snap3:
        st.metric(label="Apron Space", value=team_hard_cap(base_cap, SelectedTeam), delta=apron_space_delta, delta_color="normal", help="The first value indicates whether the team is uncapped, capped at the first apron, or capped at the second apron while the second value shows space from the applicable cap; green is under, red is over.", border=True, format="dollar")

    snap4, snap5, snap6 = st.columns(3)
    with snap4:
        render_html(f"""
            <div class="sbc-player-count-metric" title="The first number shows active roster players (up to 14, plus up to 3 IR). Teams must carry at least 12 active players, or face penalties after 14 days. The second number represents non-active players, including overseas players, draft rights, retired, and waived players and there is no limit. To qualify as overseas, a drafted player must have spent their entire SBC career abroad, with status locking on opening night.">
                <div class="sbc-player-count-label">Players</div>
                <div class="sbc-player-count-value">{active_count}</div>
                <div class="sbc-player-count-pill">{inactive_count}</div>
            </div>
            """)
    with snap5:
        st.metric(label="Entry Fee", value=base_fee(df, SelectedTeam, base_cap), delta=luxury_fee(df, SelectedTeam, base_cap), delta_color="inverse", help="The SBCFBL uses a 3,000,000-1 scale. The first number is the base entry fee, calculated from the Tax Total plus a $3.00 In-Season Tournament fee. The second number shows the Luxury Tax penalty for the season, scaled as a payable fee.", border=True, format="dollar2")
    with snap6:
        st.metric(label="Balance", value=net_fee(df, SelectedTeam, base_cap), delta=amount_paid(base_cap, SelectedTeam), delta_color="normal", help="The first number shows current total owed for the season, including base payment, In-Season Tournament fee, tax penalties, winnings, and tax payouts. The second number shows how much has been paid so far.", border=True, format="dollar2")

    render_html('<div class="sbc-section-label">Team Rosters</div>')
    render_html("""
        <div class="sbc-legend">
            <div class="sbc-legend-title">Contract Status</div>
            <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#FCE5CD;"></span>Guaranteed</div>
            <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#F4CCCC;"></span>Non-Guaranteed</div>
            <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#CFE2F3;"></span>Team Option</div>
            <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#D9D2E9;"></span>Unrestricted</div>
            <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#CFFFFF;"></span>Restricted</div>
            <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#D9D9D9;"></span>Dead</div>
        </div>
        """)
    render_html('<div class="sbc-cap-eyebrow">Active Players</div>')
    active_player_df = active_players(df, pics, SelectedTeam)
    render_cap_table(active_player_df, columns=[" ", "Player"] + columns_order + ["Bird Rights"], image_columns=[" "], row_team=SelectedTeam)

    overseas_player_df = overseas_players(df, pics, SelectedTeam)
    render_html('<div class="sbc-cap-eyebrow">Overseas Players</div>')
    if overseas_player_df.shape[0] > 0:
        render_cap_table(overseas_player_df, columns=[" ", "Player"] + columns_order + ["Bird Rights"], image_columns=[" "], row_team=SelectedTeam)
    else:
        render_html('<div class="sbc-empty-state">No overseas players are currently listed for this team.</div>')

    dead_player_df = dead_players(df, pics, SelectedTeam)
    render_html('<div class="sbc-cap-eyebrow">Dead Players</div>')
    if dead_player_df.shape[0] > 0:
        dead_player_df["Bird Rights"] = ""
        render_cap_table(dead_player_df, columns=[" ", "Player"] + columns_order + ["Bird Rights"], image_columns=[" "], row_team=SelectedTeam)
    else:
        render_html('<div class="sbc-empty-state">No dead salary is currently listed for this team.</div>')

    render_html('<div class="sbc-section-label">Contract And Asset Details</div>')
    exception_col, context_col = st.columns([1.7, 1])
    with exception_col:
        render_html('<div class="sbc-cap-eyebrow">Exceptions</div>')
        exception_df = exception_table(exceptions, SelectedTeam)
        render_cap_table(exception_df, columns=["Exception", "Amount", "Expiration Date"], money_columns=["Amount"], contract_colors=False)
    with context_col:
        render_html('<div class="sbc-cap-eyebrow">Asset Summary</div>')
        free_agent_count = free_agent_players(df, pics, SelectedTeam).shape[0]
        restricted_count = trade_restrictions(df, pics, SelectedTeam).shape[0]
        rights_count = draft_retired_players(df, pics, SelectedTeam).shape[0]
        render_html(f"""
            <div class="sbc-mini-note">
                <strong>{free_agent_count}</strong> upcoming free agents<br>
                <strong>{restricted_count}</strong> current trade restrictions<br>
                <strong>{rights_count}</strong> draft-rights or retired assets
            </div>
            """)

    asset1, asset2, asset3 = st.columns([1.05, 1.15, 0.9])
    with asset1:
        render_html('<div class="sbc-cap-eyebrow">Upcoming Free Agents</div>')
        free_agent_player_df = free_agent_players(df, pics, SelectedTeam)
        if free_agent_player_df.shape[0] > 0:
            render_cap_table(free_agent_player_df, columns=[" ", "Player"] + [str(current_year+ year_offset), "Bird Rights"], image_columns=[" "], row_team=SelectedTeam)
        else:
            render_html('<div class="sbc-empty-state">No upcoming free agents are currently listed for this team.</div>')

    with asset2:
        render_html('<div class="sbc-cap-eyebrow">Trade Restrictions</div>')
        restricted_df = trade_restrictions(df, pics, SelectedTeam)
        if restricted_df.shape[0] > 0:
            render_cap_table(restricted_df, columns=[" ", "Player", "Trade Restriction"], image_columns=[" "], contract_colors=False, row_team=SelectedTeam)
        else:
            render_html('<div class="sbc-empty-state">No trade restrictions are currently listed for this team.</div>')

    with asset3:
        render_html('<div class="sbc-cap-eyebrow">Draft Rights & Retired</div>')
        draft_retired_player_df = draft_retired_players(df, pics, SelectedTeam)
        if draft_retired_player_df.shape[0] > 0:
            render_cap_table(draft_retired_player_df, columns=[" ", "Player"], image_columns=[" "], row_team=SelectedTeam)
        else:
            render_html('<div class="sbc-empty-state">No draft-rights or retired players are currently listed for this team.</div>')

if main_page == "Team Hub" and selected_team_page == "Picks":
    # Custom draft-room layout replaces the legacy dataframe stack below.
    
    full_team_picks = full_draft_picks(dp, SelectedTeam)
    if False and full_team_picks.shape[0] > 0:
        st.header("Fully Owned Picks")
        st.dataframe(full_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})
    
    swap_team_picks = swap_draft_picks(dp, SelectedTeam)
    if False and swap_team_picks.shape[0] > 0:
        st.header("Swapped Draft Picks")
        st.dataframe(swap_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

    split_team_picks = split_draft_picks(dp, SelectedTeam)
    if False and split_team_picks.shape[0] > 0:
        st.header("Split Draft Picks")
        st.dataframe(split_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small")})

    locked_team_picks = locked_draft_picks(dp, SelectedTeam)
    if False and locked_team_picks.shape[0] > 0:
        st.header("Locked Draft Picks")
        st.dataframe(locked_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

    original_team_picks = original_draft_picks(dp, SelectedTeam)
    if False and original_team_picks.shape[0] > 0:
        st.header("Traded Away Draft Picks")
        st.dataframe(original_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

    touched_team_picks = touched_draft_picks(dp, SelectedTeam)

    shared_pick_frames = []
    if swap_team_picks.shape[0] > 0:
        swap_display = swap_team_picks.copy()
        swap_display["Type"] = "Swap"
        shared_pick_frames.append(swap_display)
    if split_team_picks.shape[0] > 0:
        split_display = split_team_picks.copy()
        split_display["Type"] = "Shared"
        shared_pick_frames.append(split_display)
    shared_team_picks = pd.concat(shared_pick_frames, ignore_index=True) if shared_pick_frames else pd.DataFrame()

    total_pick_count = full_team_picks.shape[0] + shared_team_picks.shape[0] + locked_team_picks.shape[0] + original_team_picks.shape[0]
    first_round_count = sum(
        pick_df[pick_df["Round"].astype(str).str.contains("1st", na=False)].shape[0]
        for pick_df in [full_team_picks, shared_team_picks, locked_team_picks]
        if "Round" in pick_df.columns
    )

    render_html(f"""
        <div class="sbc-draft-hero sbc-team-branded">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{team_logo_html}" alt="{team_name_html} logo">
                <div>
                    <div class="sbc-draft-eyebrow">{current_year}-{str(current_year + 6)[-2:]} Draft Room</div>
                    <div class="sbc-draft-heading">{team_name_html} {nickname_html} Picks</div>
                    <div class="sbc-draft-subcopy">A clean view of owned assets, shared-control picks, locked picks, and outbound picks now controlled elsewhere.</div>
                </div>
            </div>
        </div>
        <div class="sbc-draft-grid">
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">✓</div><div class="sbc-draft-tile-value">{full_team_picks.shape[0]}</div></div>
                <div class="sbc-draft-tile-label">Full Control</div>
                <div class="sbc-draft-tile-note">Owned outright and currently tradeable unless another rule applies.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">⇄</div><div class="sbc-draft-tile-value">{shared_team_picks.shape[0]}</div></div>
                <div class="sbc-draft-tile-label">Swaps & Shared</div>
                <div class="sbc-draft-tile-note">Assets with swap language, split rights, or shared control.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">⌖</div><div class="sbc-draft-tile-value">{locked_team_picks.shape[0]}</div></div>
                <div class="sbc-draft-tile-label">Locked</div>
                <div class="sbc-draft-tile-note">Picks held by the team but currently blocked from being traded.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">↗</div><div class="sbc-draft-tile-value">{original_team_picks.shape[0]}</div></div>
                <div class="sbc-draft-tile-label">Traded Away</div>
                <div class="sbc-draft-tile-note">Original team slots that now belong to another franchise.</div>
            </div>
        </div>
        <div class="sbc-mini-note"><strong>{total_pick_count}</strong> total pick records shown here, including <strong>{first_round_count}</strong> controlled or restricted first-round records.</div>
        """)

    render_pick_table(
        full_team_picks,
        "Full Control Picks",
        "✓",
        "Picks the team controls outright.",
        "No fully controlled picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "Contacted", "Explanation"],
        image_columns=[],
        status="hold")

    render_pick_table(
        shared_team_picks,
        "Swaps & Shared Control",
        "⇄",
        "Picks with swap language, shared ownership, or split-control terms.",
        "No swapped or shared-control picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "Contacted", "Explanation"],
        image_columns=[],
        status="swap")

    render_pick_table(
        locked_team_picks,
        "Locked Picks",
        "⌖",
        "Picks the team has, but is not allowed to trade right now.",
        "No locked picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "Contacted", "Explanation"],
        image_columns=[],
        status="locked")

    render_pick_table(
        original_team_picks,
        "Traded Away Picks",
        "↗",
        "Original team picks that now sit with another owner.",
        "No traded-away picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "CurrentTeam", "Contacted", "Explanation"],
        image_columns=["CurrentTeam"],
        status="away")

    render_first_round_control_grid(
        dp,
        [SelectedTeam],
        "First-Round Control",
        "Seven-year snapshot of whether this team has a no-doubt first-round pick, swap-based first, split/shared rights, or no listed first.",
        compact=True,
    )

    if False and touched_team_picks.shape[0] > 0:
        st.header("Touched Draft Picks")
        st.dataframe(touched_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})


if main_page == "Team Hub" and selected_team_page == "Live":
    live_rosters = all_time_rosters.copy() if all_time_rosters is not None else pd.DataFrame()
    if live_rosters.empty:
        live_rosters = load_optional_data("All-time rosters", get_all_time_rosters)
    live_rosters = ensure_columns(live_rosters, ["id", "position", "status", "team_name", "period", "year"])

    render_html(f"""
        <div class="sbc-draft-hero sbc-team-branded">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{team_logo_html}" alt="{team_name_html} logo">
                <div>
                    <div class="sbc-draft-eyebrow">Live Matchup Center</div>
                    <div class="sbc-draft-heading">{team_name_html} {nickname_html} Live</div>
                    <div class="sbc-draft-subcopy">Period scoreboards, matchup category battles, and the team trend line for the selected season.</div>
                </div>
            </div>
        </div>
        """)

    render_html("""
        <div class="sbc-live-controls">
            <div class="sbc-live-control-title">Matchup Window</div>
            <div class="sbc-live-control-copy">Choose the season and matchup period to refresh the scoreboards and trend chart.</div>
        </div>
        """)

    control1, control2 = st.columns([1, 1])
    with control1:
        year_options = list(range(2021, current_year+1))
        SelectedYear = st.selectbox("Year", options=year_options, index=year_options.index(current_year))
    with control2:
        period_options = schedule_period_options(all_time_schedule, SelectedYear)
        SelectedPeriod = st.selectbox("Period", options=period_options, index=current_period_index(period_options), format_func=period_select_label(SelectedYear))
    RegOpponents = get_opponents(all_time_schedule, SelectedTeam, SelectedYear, SelectedPeriod, "Regular Season")
    PIOpponents = get_opponents(all_time_schedule, SelectedTeam, SelectedYear, SelectedPeriod, "Play-In")
    PlayOpponents = get_opponents(all_time_schedule, SelectedTeam, SelectedYear, SelectedPeriod, "Playoffs")
    ISTOpponents = get_opponents(all_time_schedule, SelectedTeam, SelectedYear, SelectedPeriod, "In-Season Tournament")
    matchup_sections = (
        [("Regular Season", opponent) for opponent in RegOpponents]
        + [("In-Season Tournament", opponent) for opponent in ISTOpponents]
        + [("Play-In", opponent) for opponent in PIOpponents]
        + [("Playoffs", opponent) for opponent in PlayOpponents])
    matchup_count = len(matchup_sections)

    with st.spinner("Updating live center..."):
        live_stats_df = get_matchup_stats(SelectedYear, SelectedPeriod)

    live_schedule_source = all_time_schedule.copy()
    live_schedule_source["_live_year"] = pd.to_numeric(live_schedule_source["Year"], errors="coerce")
    live_schedule_source["_live_period"] = pd.to_numeric(live_schedule_source["Period"], errors="coerce")
    live_year_value = int(SelectedYear)
    live_period_value = int(SelectedPeriod)
    live_schedule_rows = live_schedule_source[
        (live_schedule_source["_live_year"] == live_year_value)
        & (live_schedule_source["_live_period"] == live_period_value)
        & ((live_schedule_source["TeamA"] == SelectedTeam) | (live_schedule_source["TeamB"] == SelectedTeam))
    ].copy()
    live_player_aggregate = False
    if live_schedule_rows.shape[0] > 0:
        render_html('<div class="sbc-section-label">Player Box Score</div>')
        live_player_aggregate = render_selected_team_player_boxscore(
            live_schedule_rows,
            SelectedTeam,
            live_rosters,
            key_prefix=f"live_players_{SelectedYear}_{SelectedPeriod}") or False

    render_html('<div class="sbc-section-label">Matchup Scoreboards</div>')
    if matchup_count == 0:
        selected_payload = live_row_payload(live_stats_df, SelectedTeam)
        render_live_stat_board(
            f"{SelectedTeam} {period_date_label(SelectedYear, SelectedPeriod, f'P{SelectedPeriod}')} Stat Profile",
            "No scheduled matchup",
            [selected_payload] if selected_payload else [],
            SelectedTeam,
            SelectedTeam)
    else:
        for idx, (matchup_type, opponent) in enumerate(matchup_sections):
            selected_payload = live_row_payload(live_stats_df, SelectedTeam)
            opponent_payload = live_row_payload(live_stats_df, opponent)
            matchup_rows = [payload for payload in [selected_payload, opponent_payload] if payload]
            matchup_home = SelectedTeam
            schedule_match = live_schedule_source[
                (live_schedule_source["_live_year"] == live_year_value)
                & (live_schedule_source["_live_period"] == live_period_value)
                & (live_schedule_source["Type"] == matchup_type)
                & (
                    ((live_schedule_source["TeamA"] == SelectedTeam) & (live_schedule_source["TeamB"] == opponent))
                    | ((live_schedule_source["TeamA"] == opponent) & (live_schedule_source["TeamB"] == SelectedTeam))
                )
            ]
            if schedule_match.shape[0] > 0:
                matchup_home = schedule_match.iloc[0]["TeamA"]
            if schedule_match.shape[0] > 0:
                matchup_payload = schedule_match.iloc[0].to_dict()
                render_matchup_boxscore(matchup_payload, live_rosters, key_prefix=f"live_{idx}", show_players=False)
                render_team_player_boxscore_for_matchup(matchup_payload, opponent, live_rosters, aggregate=live_player_aggregate)
            else:
                render_live_stat_board(
                    f"{SelectedTeam} vs {opponent}",
                    f"{matchup_type} - {period_date_label(SelectedYear, SelectedPeriod, f'P{SelectedPeriod}')}",
                    matchup_rows,
                    SelectedTeam,
                    matchup_home)

    render_html('<div class="sbc-section-label">Season Trend</div>')
    SelectedCategory = st.selectbox("Trend Category", options=list(stat_to_scipId.keys()), index=list(stat_to_scipId.keys()).index("PTS"))
    render_html(f"""
        <div class="sbc-chart-head">
            <div>
                <div class="sbc-chart-title">{escape(str(SelectedCategory))} by Matchup Period</div>
                <div class="sbc-chart-copy">{team_name_html}, this period's opponents, and the league median. Larger dots mark the selected period.</div>
            </div>
            <div class="sbc-live-badge">{SelectedYear}</div>
        </div>
        """)
    chart_opponents = [opponent for _, opponent in matchup_sections]
    season_line_chart_data = build_live_line_chart(all_time_team_stats, SelectedTeam, SelectedCategory, SelectedYear, SelectedPeriod, chart_opponents, bg_color, text_color2)
    if season_line_chart_data is None:
        render_html('<div class="sbc-empty-state">No season trend data is available for this selection.</div>')
    else:
        st.altair_chart(season_line_chart_data, use_container_width=True)

if main_page == "Team Hub" and selected_team_page == "Schedule":
    schedule_years = sorted(all_time_schedule["Year"].dropna().astype(int).unique().tolist())
    if not schedule_years:
        schedule_years = [current_year]
    default_schedule_year = current_year if current_year in schedule_years else schedule_years[-1]
    if "_sbc_schedule_year" not in st.session_state or st.session_state["_sbc_schedule_year"] not in schedule_years:
        st.session_state["_sbc_schedule_year"] = default_schedule_year
    SelectedScheduleYear = st.session_state["_sbc_schedule_year"]
    schedule_raw = all_time_schedule[
        (all_time_schedule["Year"] == SelectedScheduleYear)
        & ((all_time_schedule["TeamA"] == SelectedTeam) | (all_time_schedule["TeamB"] == SelectedTeam))
    ].copy()
    schedule_record = schedule_regular_record(schedule_raw, SelectedTeam)
    render_html(f"""
        <div class="sbc-draft-hero sbc-team-branded">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{team_logo_html}" alt="{team_name_html} logo">
                <div>
                    <div class="sbc-draft-eyebrow">{SelectedScheduleYear} Travel Desk / Regular Season {escape(schedule_record)}</div>
                    <div class="sbc-draft-heading">{team_name_html} {nickname_html} Schedule</div>
                    <div class="sbc-draft-subcopy">Opponent flow, home-road balance, matchup types, results, and travel load by season.</div>
                </div>
            </div>
        </div>
        """)
    render_html("""
        <div class="sbc-live-controls">
            <div class="sbc-live-control-title">Schedule Window</div>
            <div class="sbc-live-control-copy">Choose the season to refresh the schedule table, travel totals, and map.</div>
        </div>
        """)
    SelectedScheduleYear = st.selectbox("Schedule Year", options=schedule_years, key="_sbc_schedule_year")
    schedule_raw = all_time_schedule[
        (all_time_schedule["Year"] == SelectedScheduleYear)
        & ((all_time_schedule["TeamA"] == SelectedTeam) | (all_time_schedule["TeamB"] == SelectedTeam))
    ].copy()
    render_html('<div class="sbc-section-label">Schedule</div>')
    render_schedule_table(schedule_raw, SelectedTeam, rosters_df=all_time_rosters, show_boxscores=True)
    total_miles, num_flights = calculate_team_travel_summary(SelectedTeam, SelectedScheduleYear, all_time_schedule)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Miles", value=f"{int(total_miles):,} mi", help="Total miles traveled this season including road trips and returns home.", border=True)
    with col2:
        st.metric(label="Total Flights", value=num_flights, help="Number of flights taken this season (legs with distance > 0).", border=True)
    render_team_travel_map(schedule_raw, SelectedTeam, SelectedScheduleYear)

if main_page == "Team Hub" and selected_team_page == "History":
    team_history_view = st.segmented_control(
        "Team history section", ["Franchise History", "Branding"],
        default="Franchise History", key="team_history_section", label_visibility="collapsed",
    )
    if team_history_view == "Branding":
        render_team_branding(SelectedTeam)

if main_page == "Team Hub" and selected_team_page == "History" and team_history_view == "Franchise History":
    matchup_archive = load_sbc_player_matchup_stats_archive()
    team_archive = matchup_archive[matchup_archive["sbc_team_key"].astype(str) == str(SelectedTeam)].copy() if not matchup_archive.empty and "sbc_team_key" in matchup_archive.columns else pd.DataFrame()
    render_html(f"""
        <div class="sbc-draft-hero sbc-team-branded">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{team_logo_html}" alt="{team_name_html} logo">
                <div>
                    <div class="sbc-draft-eyebrow">Franchise Archive</div>
                    <div class="sbc-draft-heading">{team_name_html} {nickname_html} All-Time Stats</div>
                    <div class="sbc-draft-subcopy">Player production counted only while active for this franchise in SBCFBL matchup windows.</div>
                </div>
            </div>
        </div>
    """)
    if team_archive.empty:
        render_html('<div class="sbc-empty-state">No player matchup archive is available for this team yet. Run build_sbc_player_matchup_stats.py to refresh it.</div>')
    else:
        seasons = sorted(pd.to_numeric(team_archive["sbc_year"], errors="coerce").dropna().astype(int).unique().tolist())
        season_options = ["Career"] + [season_label_from_year(year) for year in seasons]
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            team_scope = st.selectbox("Season", season_options, key="team_history_all_time_scope")
        with col2:
            team_type = st.selectbox("Stat Type", ["Regular Season", "Playoffs", "Play-In", "In-Season Tournament"], key="team_history_all_time_type_v2")
        with col3:
            team_basis = st.selectbox("Stat Basis", ["Total", "Per NBA Game", "Per SBCFBL Matchup"], key="team_history_all_time_basis")
        with col4:
            leader_stat = st.selectbox("Sort / Leaderboard Stat", HISTORY_LEADERBOARD_STATS, index=HISTORY_LEADERBOARD_STATS.index("PTS"), key="team_history_matchup_stat")
        filtered_team_archive = team_archive.copy()
        if team_scope != "Career":
            selected_year = seasons[season_options.index(team_scope) - 1]
            filtered_team_archive = filtered_team_archive[pd.to_numeric(filtered_team_archive["sbc_year"], errors="coerce") == selected_year].copy()
        filtered_team_archive = filtered_team_archive[filtered_team_archive["sbc_matchup_type"].astype(str) == team_type].copy()
        basis_key = {"Total": "total", "Per NBA Game": "per_nba", "Per SBCFBL Matchup": "per_sbc"}[team_basis]
        render_html('<div class="sbc-awards-section-head"><span>Player Ledger</span><em>Sorted by points, with percentages recalculated from summed makes and attempts.</em></div>')
        selected_team_active_player_keys = current_active_player_keys_for_team(df, SelectedTeam)
        render_all_time_player_aggregate_table(
            aggregate_matchup_player_rows(filtered_team_archive, basis=basis_key),
            "No player stats match this team history filter.",
            limit=75,
            show_team=False,
            show_seasons=(team_scope == "Career"),
            sort_stat=leader_stat,
            current_contracts=df,
            highlight_team=SelectedTeam,
            highlight_player_keys=selected_team_active_player_keys,
        )
        render_html('<div class="sbc-awards-section-head"><span>Franchise Single-Matchup Leaders</span><em>Best individual matchup performances for the selected stat.</em></div>')
        player_filter = st.text_input("Filter players", key="team_history_player_filter", placeholder="Type a player name...")
        leaderboard_archive = filtered_team_archive.copy()
        if player_filter.strip():
            leaderboard_archive = leaderboard_archive[leaderboard_archive["fantrax_name"].astype(str).str.contains(player_filter.strip(), case=False, na=False)].copy()
        render_matchup_leaderboard(leaderboard_archive, leader_stat, "No single-matchup leaders match this filter.", limit=25, show_team=False)

if main_page == "League Hub" and selected_league_page == "Scoreboard":
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">League Scoreboard</div>
                    <div class="sbc-draft-heading">SBC Scoreboard</div>
                    <div class="sbc-draft-subcopy">Every matchup in the selected window, with scores grouped by competition type.</div>
                </div>
            </div>
        </div>
        """)
    SelectedYear2 = current_year
    period_options2 = schedule_period_options(all_time_schedule, SelectedYear2)
    SelectedPeriod2 = st.selectbox("Select Period", options=period_options2, index=current_period_index(period_options2), key="league_current_scoreboard_period", format_func=period_select_label(SelectedYear2))

    scoreboard_schedule = all_time_schedule[
        (all_time_schedule["Year"] == SelectedYear2)
        & (all_time_schedule["Period"] == SelectedPeriod2)
    ]
    if scoreboard_schedule.empty:
        live_stats_total_scores = pd.DataFrame()
    else:
        with st.spinner("Updating matchups..."):
            live_stats_df2 = get_matchup_stats(SelectedYear2, SelectedPeriod2)
            live_stats_total_scores = get_weekly_scores_df(SelectedYear2, SelectedPeriod2, all_time_schedule, live_stats_df2, standings)

    render_html('<div class="sbc-section-label">All Scores</div>')
    render_scoreboard_cards(live_stats_total_scores)

if main_page == "League Hub" and selected_league_page == "History" and selected_history_page == "Overview":
    render_league_history_overview()

if main_page == "League Hub" and selected_league_page == "History" and selected_history_page == "Scoreboard":
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">League History</div>
                    <div class="sbc-draft-heading">Historical Scoreboard</div>
                    <div class="sbc-draft-subcopy">Look up any saved matchup window across regular season, Cup, play-in, and playoff records.</div>
                </div>
            </div>
        </div>
    """)
    HistoryScoreYear = LeagueHistoryYear
    history_period_options = schedule_period_options(all_time_schedule, HistoryScoreYear)
    HistoryScorePeriod = st.selectbox("History Period", options=history_period_options, index=current_period_index(history_period_options), key="league_history_scoreboard_period", format_func=period_select_label(HistoryScoreYear))
    history_schedule = all_time_schedule[
        (all_time_schedule["Year"] == HistoryScoreYear)
        & (all_time_schedule["Period"] == HistoryScorePeriod)
    ]
    if history_schedule.empty:
        history_scores = pd.DataFrame()
    else:
        with st.spinner("Loading historical matchups..."):
            history_live_stats = get_matchup_stats(HistoryScoreYear, HistoryScorePeriod)
            history_scores = get_weekly_scores_df(HistoryScoreYear, HistoryScorePeriod, all_time_schedule, history_live_stats, standings)
    render_html('<div class="sbc-section-label">Historical Scores</div>')
    render_scoreboard_cards(history_scores)

if main_page == "League Hub" and selected_league_page == "History" and selected_history_page == "Playoff Bracket":
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">League History</div>
                    <div class="sbc-draft-heading">Playoff Bracket</div>
                    <div class="sbc-draft-subcopy">Final conference standings around an NBA-style play-in and playoff bracket built from saved game results.</div>
                </div>
            </div>
        </div>
    """)
    PlayoffHistoryYear = LeagueHistoryYear
    playoff_period = latest_period_for_year(PlayoffHistoryYear)
    playoff_games = all_time_schedule[
        (all_time_schedule["Year"] == PlayoffHistoryYear)
        & (all_time_schedule["Type"].astype(str).isin(["Play-In", "Playoffs"]))
    ].copy()
    playoff_seed_lookup = bracket_seed_lookup(standings, PlayoffHistoryYear, playoff_period)
    render_html('<div class="sbc-section-label">Playoff Bracket</div>')
    render_playoff_bracket(playoff_games, f"{PlayoffHistoryYear} Playoffs", "No play-in or playoff games are available for this year.", seed_lookup=playoff_seed_lookup)
    render_html('<div class="sbc-section-label">Final Standings Snapshot</div>')
    west_col, east_col = st.columns(2)
    with west_col:
        render_conference_standings(standings, PlayoffHistoryYear, playoff_period, "West")
    with east_col:
        render_conference_standings(standings, PlayoffHistoryYear, playoff_period, "East")

if main_page == "League Hub" and selected_league_page == "History" and selected_history_page == "In-Season Tournament":
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">League History</div>
                    <div class="sbc-draft-heading">In-Season Tournament</div>
                    <div class="sbc-draft-subcopy">Cup group tables on the wings with knockout games in the middle.</div>
                </div>
            </div>
        </div>
    """)
    ISTHistoryYear = LeagueHistoryYear
    ist_period = latest_period_for_year(ISTHistoryYear)
    ist_games = all_time_schedule[
        (all_time_schedule["Year"] == ISTHistoryYear)
        & (all_time_schedule["Type"].astype(str) == "In-Season Tournament")
        & (~all_time_schedule["Round"].astype(str).str.contains("Group", case=False, na=False))
    ].copy()
    ist_seed_lookup = ist_bracket_seed_lookup(ISTHistoryYear, ist_period)
    render_html('<div class="sbc-section-label">Cup Bracket</div>')
    render_ist_bracket(ist_games, f"{ISTHistoryYear} SBCFBL Cup", "No Cup knockout games are available for this year.", seed_lookup=ist_seed_lookup)
    render_html('<div class="sbc-section-label">Cup Group Standings</div>')
    west_col, east_col = st.columns(2)
    with west_col:
        render_ist_conference_history_panel(ISTHistoryYear, ist_period, "West")
    with east_col:
        render_ist_conference_history_panel(ISTHistoryYear, ist_period, "East")

if main_page == "League Hub" and selected_league_page == "History" and selected_history_page == "Player Stats":
    player_options = player_stats_options(all_time_rosters)
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">League History</div>
                    <div class="sbc-draft-heading">Player Stats</div>
                    <div class="sbc-draft-subcopy">Career pages for every player who has ever been active in an SBCFBL lineup, counting only games while started in this league.</div>
                </div>
            </div>
        </div>
    """)
    if player_options.empty:
        render_html('<div class="sbc-empty-state">No active-start player history is available yet.</div>')
    else:
        player_name_to_id = (
            player_options.drop_duplicates("display_name")
            .set_index("display_name")["fantrax_id"]
            .to_dict()
        )
        selected_player_name = st.selectbox(
            "Player",
            options=sorted(player_name_to_id.keys(), key=lambda value: str(value).lower()),
            key="history_player_stats_player",
        )
        selected_player_id = player_name_to_id.get(selected_player_name)
        selected_meta = player_options[player_options["fantrax_id"] == selected_player_id].iloc[0]
        espn_player_id = selected_meta.get("espn_player_id", "")
        contract = current_player_contract(selected_player_name, df)
        current_salary = contract.get("salary", "")
        active_roster = bool(contract.get("active_roster"))
        salary_text = contract.get("summary") or (format_money(current_salary) if not is_blank_value(current_salary) else "No active contract listed")
        team_key = contract.get("team_key", "")
        awards_table = player_awards_table_for_name(selected_player_name, award_history)
        player_rows = selected_player_matchup_rows(selected_player_id, all_time_rosters, all_time_schedule)
        career_team_values = []
        if not player_rows.empty:
            team_col = "sbc_team_key" if "sbc_team_key" in player_rows.columns else "sbc_team"
            if team_col in player_rows.columns:
                career_team_values = [
                    resolve_team_key(value)
                    for value in player_rows[team_col].dropna().astype(str).unique().tolist()
                    if resolve_team_key(value) in team_info
                ]
        career_team_values = sorted(set(career_team_values))
        profile_team_key = team_key if active_roster and team_key in team_info else (career_team_values[0] if len(career_team_values) == 1 else "")
        team_text = live_team_full_name(team_key) if active_roster and team_key in team_info else "Not currently rostered"
        has_accolades = awards_table is not None and not awards_table.empty
        profile_classes = ["sbc-player-profile-hero"]
        if profile_team_key in team_info:
            profile_classes.append("sbc-player-profile-hero-current")
        if not has_accolades:
            profile_classes.append("sbc-player-profile-hero-no-accolades")
        profile_class = " ".join(profile_classes)
        if profile_team_key in team_info:
            profile_visuals = team_visuals(profile_team_key)
            profile_style = (
                f' style="--profile-current-team-color:{escape(str(profile_visuals["primary"]), quote=True)};'
                f'--profile-current-team-secondary:{escape(str(profile_visuals["secondary"]), quote=True)};'
                f'--profile-current-team-font:{escape(str(profile_visuals["font"]), quote=True)};'
                f'--profile-current-team-text:{escape(str(profile_visuals["text"]), quote=True)};"'
            )
        else:
            profile_style = ""
        active_years = sorted(pd.to_numeric(player_rows.get("sbc_year", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).unique().tolist()) if not player_rows.empty else []
        season_text = player_season_count_text(active_years, active_roster=active_roster)
        headshot = espn_headshot_url(espn_player_id)
        award_html = award_summary_chips(awards_table) if has_accolades else ""
        accolades_html = f"""
                <div class="sbc-player-profile-accolades">
                    <div class="sbc-player-profile-accolades-label">Accolades</div>
                    <div class="sbc-player-profile-awards">{award_html}</div>
                </div>
        """ if has_accolades else ""
        render_html(f"""
            <section class="{profile_class}"{profile_style}>
                <div class="sbc-player-profile-photo">
                    <img src="{headshot}" alt="{escape(selected_player_name, quote=True)} headshot">
                </div>
                <div class="sbc-player-profile-main">
                    <div class="sbc-player-profile-kicker">SBCFBL Player Profile</div>
                    <h2>{escape(selected_player_name)}</h2>
                    <div class="sbc-player-profile-meta">
                        <span>{escape(team_text)}</span>
                        <span>{escape(salary_text)}</span>
                        <span>{escape(season_text)}</span>
                    </div>
                </div>
                {accolades_html}
            </section>
        """)
        stat_mode = st.radio(
            "Stat Type",
            options=["Regular Season", "Playoffs", "Play-In", "In-Season Tournament"],
            horizontal=True,
            key="history_player_stats_type",
        )
        pace_mode = st.radio(
            "Stat Basis",
            options=["Per NBA Game", "Per SBCFBL Matchup", "Total"],
            horizontal=True,
            key="history_player_stats_basis",
        )
        stat_type_lookup = {
            "Regular Season": ("Regular Season Stats", "Regular Season", "No regular season games matched this player while active."),
            "Playoffs": ("Playoff Stats", "Playoffs", "No playoff games matched this player while active."),
            "Play-In": ("Play-In Stats", "Play-In", "No play-in games matched this player while active."),
            "In-Season Tournament": ("In-Season Tournament Stats", "In-Season Tournament", "No in-season tournament games matched this player while active."),
        }
        title, type_value, empty_text = stat_type_lookup[stat_mode]
        type_column = "sbc_matchup_type" if "sbc_matchup_type" in player_rows.columns else "Type"
        section_rows = player_rows[player_rows[type_column].astype(str) == type_value] if not player_rows.empty else pd.DataFrame()
        basis_key = {"Per NBA Game": "per_nba", "Per SBCFBL Matchup": "per_sbc", "Total": "total"}[pace_mode]
        basis_note = {
            "per_nba": "Per NBA game played.",
            "per_sbc": "Per SBCFBL matchup; GP is NBA games played per matchup.",
            "total": "Raw totals.",
        }[basis_key]
        render_html(f'<div class="sbc-awards-section-head"><span>{escape(title)}</span><em>{escape(basis_note)} Only NBA games on dates this player was ACTIVE in an SBCFBL matchup.</em></div>')
        season_rows = aggregate_player_season_rows(section_rows, basis=basis_key)
        render_player_stats_table(season_rows, empty_text)
        render_html('<div class="sbc-awards-section-head"><span>Matchup Leaders</span><em>Best single SBCFBL matchup performance by category.</em></div>')
        render_player_matchup_highs(section_rows, "No matchup highs are available for this player and stat type.")
        render_award_detail_ledger(awards_table)

if main_page == "League Hub" and selected_league_page == "History" and selected_history_page == "All-Time Stats":
    matchup_archive = load_sbc_player_matchup_stats_archive()
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">League History</div>
                    <div class="sbc-draft-heading">All-Time Stats</div>
                    <div class="sbc-draft-subcopy">Single-matchup player records from the SBCFBL matchup archive.</div>
                </div>
            </div>
        </div>
    """)
    if matchup_archive.empty:
        render_html('<div class="sbc-empty-state">No player matchup archive is available yet. Run build_sbc_player_matchup_stats.py to refresh it.</div>')
    else:
        seasons = sorted(pd.to_numeric(matchup_archive["sbc_year"], errors="coerce").dropna().astype(int).unique().tolist())
        season_options = ["Career"] + [season_label_from_year(year) for year in seasons]
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            league_stat = st.selectbox("Category", HISTORY_LEADERBOARD_STATS, index=HISTORY_LEADERBOARD_STATS.index("PTS"), key="league_history_all_time_stat")
        with col2:
            league_scope = st.selectbox("Season", season_options, key="league_history_all_time_scope")
        with col3:
            league_type = st.selectbox("Stat Type", ["Regular Season", "Playoffs", "Play-In", "In-Season Tournament"], key="league_history_all_time_type_v2")
        with col4:
            league_mode = st.selectbox("View", ["Single Game", "SBCFBL Matchup Average", "Total"], key="league_history_all_time_mode")
        filtered_archive = matchup_archive.copy()
        if league_scope != "Career":
            selected_year = seasons[season_options.index(league_scope) - 1]
            filtered_archive = filtered_archive[pd.to_numeric(filtered_archive["sbc_year"], errors="coerce") == selected_year].copy()
        filtered_archive = filtered_archive[filtered_archive["sbc_matchup_type"].astype(str) == league_type].copy()
        if league_mode == "Single Game":
            render_html(f'<div class="sbc-awards-section-head"><span>{escape(history_stat_label(league_stat))} Single-Matchup Leaders</span><em>One row is one player in one SBCFBL matchup period.</em></div>')
            render_matchup_leaderboard(filtered_archive, league_stat, "No single-matchup leaders match this filter.", limit=50, show_team=True)
        elif league_mode == "SBCFBL Matchup Average":
            render_html('<div class="sbc-awards-section-head"><span>Matchup Average Leaders</span><em>Player averages per SBCFBL matchup in the selected scope.</em></div>')
            render_all_time_player_aggregate_table(
                aggregate_matchup_player_rows(filtered_archive, basis="per_sbc", group_by_team=False),
                "No matchup average leaders match this filter.",
                limit=50,
                show_team=False,
                show_seasons=(league_scope == "Career"),
                sort_stat=league_stat,
            )
        else:
            render_html('<div class="sbc-awards-section-head"><span>Total Leaders</span><em>Player totals in the selected scope.</em></div>')
            render_all_time_player_aggregate_table(
                aggregate_matchup_player_rows(filtered_archive, basis="total", group_by_team=False),
                "No total leaders match this filter.",
                limit=50,
                show_team=False,
                show_seasons=(league_scope == "Career"),
                sort_stat=league_stat,
            )

if main_page == "League Hub" and selected_league_page == "Standings":
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">League Table</div>
                    <div class="sbc-draft-heading">SBC Standings</div>
                    <div class="sbc-draft-subcopy">Conference position, win percentage, games back, and conference/division record through the selected period.</div>
                </div>
            </div>
        </div>
        """)
    StandingsYear = st.selectbox("Standings Year", options=list(range(2021, current_year+1)), index=list(range(2021, current_year+1)).index(current_year))
    standings_period_options = schedule_period_options(all_time_schedule, StandingsYear)
    StandingsPeriod = st.selectbox("Standings Period", options=standings_period_options, index=current_period_index(standings_period_options), format_func=period_select_label(StandingsYear))
    render_html('<div class="sbc-section-label">Standings Snapshot</div>')
    west_col, east_col = st.columns(2)
    with west_col:
        render_conference_standings(standings, StandingsYear, StandingsPeriod, "West")
    with east_col:
        render_conference_standings(standings, StandingsYear, StandingsPeriod, "East")
    render_ist_standings(standings, StandingsYear, StandingsPeriod)

if main_page == "League Hub" and selected_league_page == "Players":

    active_all_df = safe_table_call(active_players_all, df, pics)
    inactive_all_df = safe_table_call(inactive_players_all, df, pics)
    dead_players_df = safe_table_call(dead_players_all, df, pics)
    all_free_agents_df = safe_table_call(all_free_agents, df, pics)
    draft_all_df = safe_table_call(draft_rights_all, df, pics)
    retired_all_df = safe_table_call(retired_all, df, pics)
    trade_restrictins_all_df = safe_table_call(trade_restrictions_all, df, pics)

    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">{current_year-1}-{str(current_year)[-2:]} League Player Office</div>
                    <div class="sbc-draft-heading">League Players</div>
                    <div class="sbc-draft-subcopy">Every roster, stash, dead salary, rights asset, upcoming free agent, and trade restriction in one league-wide view.</div>
                </div>
            </div>
        </div>
        <div class="sbc-draft-grid">
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">👥</div><div class="sbc-draft-tile-value">{active_all_df.shape[0]}</div></div>
                <div class="sbc-draft-tile-label">Active Players</div>
                <div class="sbc-draft-tile-note">Players currently occupying active roster slots across the league.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">🌍</div><div class="sbc-draft-tile-value">{inactive_all_df.shape[0]}</div></div>
                <div class="sbc-draft-tile-label">Overseas Players</div>
                <div class="sbc-draft-tile-note">Non-active players with guaranteed or unguaranteed salary records.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">⏳</div><div class="sbc-draft-tile-value">{all_free_agents_df.shape[0]}</div></div>
                <div class="sbc-draft-tile-label">Upcoming Free Agents</div>
                <div class="sbc-draft-tile-note">Players reaching restricted or unrestricted free agency in the next class.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">🚧</div><div class="sbc-draft-tile-value">{trade_restrictins_all_df.shape[0]}</div></div>
                <div class="sbc-draft-tile-label">Trade Restrictions</div>
                <div class="sbc-draft-tile-note">Current league-wide player movement restrictions.</div>
            </div>
        </div>
        """)

    render_html('<div class="sbc-section-label">Cap Sheet Legend</div>')
    render_html("""
        <div class="sbc-legend-row">
            <span><i style="background:#FCE5CD;"></i>Guaranteed</span>
            <span><i style="background:#F4CCCC;"></i>Non-Guaranteed</span>
            <span><i style="background:#CFE2F3;"></i>Team Option</span>
            <span><i style="background:#D9D2E9;"></i>Unrestricted</span>
            <span><i style="background:#CFFFFF;"></i>Restricted</span>
            <span><i style="background:#D9D9D9;"></i>Dead</span>
        </div>
        """)

    render_html('<div class="sbc-section-label">League Rosters</div>')
    render_html('<div class="sbc-cap-eyebrow">Active Players</div>')
    render_cap_table(active_all_df, columns=["Team_logo", " ", "Player"] + columns_order + ["Bird Rights"], image_columns=["Team_logo", " "])

    render_html('<div class="sbc-cap-eyebrow">Overseas Players</div>')
    render_cap_table(inactive_all_df, columns=["Team_logo", " ", "Player"] + columns_order + ["Bird Rights"], image_columns=["Team_logo", " "])

    render_html('<div class="sbc-cap-eyebrow">Dead Players</div>')
    render_cap_table(dead_players_df, columns=["Team_logo", " ", "Player"] + columns_order + ["Bird Rights"], image_columns=["Team_logo", " "])

    render_html('<div class="sbc-section-label">Contract And Asset Details</div>')
    asset1, asset2 = st.columns([1.1, 0.9])
    with asset1:
        render_html('<div class="sbc-cap-eyebrow">Upcoming Free Agents</div>')
        render_cap_table(all_free_agents_df, columns=["Team_logo", " ", "Player"] + [str(current_year + year_offset), "Bird Rights"], image_columns=["Team_logo", " "])
    with asset2:
        render_html('<div class="sbc-cap-eyebrow">Trade Restrictions</div>')
        render_cap_table(trade_restrictins_all_df, columns=["Team_logo", " ", "Player", "Trade Restriction"], image_columns=["Team_logo", " "], contract_colors=False)

    asset3, asset4 = st.columns(2)
    with asset3:
        render_html('<div class="sbc-cap-eyebrow">Draft Rights</div>')
        render_cap_table(draft_all_df, columns=["Team_logo", " ", "Player"] + columns_order, image_columns=["Team_logo", " "])
    with asset4:
        render_html('<div class="sbc-cap-eyebrow">Retired Rights</div>')
        render_cap_table(retired_all_df, columns=["Team_logo", " ", "Player"] + columns_order, image_columns=["Team_logo", " "])

    _legacy_tab6 = r'''
    col1, col2 = st.columns([1,7])

    with col1:

        st.markdown("""
            **Cap Sheet Legend:** \n
            <span style="background-color:#FCE5CD;padding:6px 20px;border-radius:5px;">&nbsp;</span> Guaranteed \n 
            <span style="background-color:#F4CCCC;padding:6px 20px;border-radius:5px;">&nbsp;</span> Non-Guaranteed \n
            <span style="background-color:#CFE2F3;padding:6px 20px;border-radius:5px;">&nbsp;</span> Team Option \n
            <span style="background-color:#D9D2E9;padding:6px 20px;border-radius:5px;">&nbsp;</span> Unrestricted \n
            <span style="background-color:#CFFFFF;padding:6px 20px;border-radius:5px;">&nbsp;</span> Restricted \n
            <span style="background-color:#D9D9D9;padding:6px 20px;border-radius:5px;">&nbsp;</span> Dead
            """, unsafe_allow_html=True)

    with col2:
        active_all_df = active_players_all(df, pics)
        if active_all_df.shape[0] > 0:
            st.subheader("Active Players")
            active_all_df = (active_all_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in active_all_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(active_all_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + columns_order + ["Bird Rights"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

        inactive_all_df = inactive_players_all(df, pics)
        if inactive_all_df.shape[0] > 0:
            st.subheader("Overseas Players")
            inactive_all_df = (inactive_all_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in inactive_all_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(inactive_all_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + columns_order + ["Bird Rights"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

        dead_players_df = dead_players_all(df, pics)
        if dead_players_df.shape[0] > 0:
            st.subheader("Dead Players")
            dead_players_df = (dead_players_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in dead_players_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(dead_players_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + columns_order, column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

    col1, col2, col3, col4 = st.columns([3,2,2,3])

    with col1:
        all_free_agents_df = all_free_agents(df, pics)
        if all_free_agents_df.shape[0] > 0:
            st.subheader("Upcoming Free Agents")
            all_free_agents_df = (all_free_agents_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in all_free_agents_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(all_free_agents_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + [str(current_year+ year_offset), "Bird Rights"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

    with col2:
        draft_all_df = draft_rights_all(df, pics)
        if draft_all_df.shape[0] > 0:
            st.subheader("Draft Rights")
            draft_all_df = (draft_all_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in draft_all_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(draft_all_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

    with col3:
        retired_all_df = retired_all(df, pics)
        if retired_all_df.shape[0] > 0:
            st.subheader("Retired Rights")
            retired_all_df = (retired_all_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in retired_all_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(retired_all_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

    with col4:
        trade_restrictins_all_df = trade_restrictions_all(df, pics)
        if trade_restrictins_all_df.shape[0] > 0:
            st.subheader("Trade Restrictions")
            trade_restrictins_all_df = (trade_restrictins_all_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                .format({c: "${:,.0f}" for c in trade_restrictins_all_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(trade_restrictins_all_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player", "Trade Restriction"], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

    '''
if main_page == "League Hub" and selected_league_page == "Draft Picks":
    all_full_team_picks = safe_table_call(all_full_draft_picks, dp)
    all_swap_team_picks = safe_table_call(all_swap_draft_picks, dp)
    all_split_team_picks = safe_table_call(all_split_draft_picks, dp)
    all_locked_team_picks = safe_table_call(all_locked_draft_picks, dp)
    all_shared_pick_count = all_swap_team_picks.shape[0] + all_split_team_picks.shape[0]
    all_pick_count = all_full_team_picks.shape[0] + all_shared_pick_count + all_locked_team_picks.shape[0]
    all_first_round_count = sum(
        pick_df[pick_df["Round"].astype(str).str.contains("1st", na=False)].shape[0]
        for pick_df in [all_full_team_picks, all_swap_team_picks, all_split_team_picks, all_locked_team_picks]
        if "Round" in pick_df.columns
    )

    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">{current_year}-{str(current_year + 6)[-2:]} League Draft Inventory</div>
                    <div class="sbc-draft-heading">League Draft Picks</div>
                    <div class="sbc-draft-subcopy">A complete league-wide inventory of controlled picks, swap language, shared ownership, and locked draft assets.</div>
                </div>
            </div>
        </div>
        <div class="sbc-draft-grid">
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">✓</div><div class="sbc-draft-tile-value">{all_full_team_picks.shape[0]}</div></div>
                <div class="sbc-draft-tile-label">Full Control</div>
                <div class="sbc-draft-tile-note">Picks controlled outright by their current owner.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">⇄</div><div class="sbc-draft-tile-value">{all_shared_pick_count}</div></div>
                <div class="sbc-draft-tile-label">Swaps & Shared</div>
                <div class="sbc-draft-tile-note">Pick swaps and assets with split or shared control language.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">⌖</div><div class="sbc-draft-tile-value">{all_locked_team_picks.shape[0]}</div></div>
                <div class="sbc-draft-tile-label">Locked</div>
                <div class="sbc-draft-tile-note">Picks currently blocked from being traded.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">1</div><div class="sbc-draft-tile-value">{all_first_round_count}</div></div>
                <div class="sbc-draft-tile-label">First-Round Records</div>
                <div class="sbc-draft-tile-note">Round-one records across controlled, shared, and locked inventory.</div>
            </div>
        </div>
        <div class="sbc-mini-note"><strong>{all_pick_count}</strong> total league pick records shown across all active draft-control categories.</div>
        """)

    render_pick_table(
        all_full_team_picks,
        "Fully Owned Picks",
        "✓",
        "Every pick currently controlled outright by its owner.",
        "No fully owned picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "CurrentTeam", "Contacted", "Explanation"],
        image_columns=["CurrentTeam"],
        status="full"
    )

    render_pick_table(
        all_swap_team_picks,
        "Swapped Draft Picks",
        "⇄",
        "Pick records with swap language attached.",
        "No swapped picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "CurrentTeam", "Contacted", "Explanation"],
        image_columns=["CurrentTeam"],
        status="swap"
    )

    render_pick_table(
        all_split_team_picks,
        "Split Draft Picks",
        "◐",
        "Picks with shared or split-control ownership language.",
        "No split picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "Potential Owners", "Contacted", "Explanation"],
        image_columns=[],
        status="split"
    )

    render_pick_table(
        all_locked_team_picks,
        "Locked Draft Picks",
        "⌖",
        "Picks held by teams but currently restricted from trade.",
        "No locked picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "CurrentTeam", "Contacted", "Explanation"],
        image_columns=["CurrentTeam"],
        status="locked"
    )

    render_league_first_round_control_matrix(dp)

    _legacy_tab7 = r'''
    all_full_team_picks = all_full_draft_picks(dp)
    st.header("Fully Owned Picks")
    st.dataframe(all_full_team_picks, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})
    
    all_swap_team_picks = all_swap_draft_picks(dp)
    st.header("Swapped Draft Picks")
    st.dataframe(all_swap_team_picks, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

    all_split_team_picks = all_split_draft_picks(dp)
    st.header("Split Draft Picks")
    st.dataframe(all_split_team_picks, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small")})

    all_locked_team_picks = all_locked_draft_picks(dp)
    st.header("Locked Draft Picks")
    st.dataframe(all_locked_team_picks, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

    '''
if main_page == "League Hub" and selected_league_page == "Overview":
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">{current_year-1}-{str(current_year)[-2:]} League Office</div>
                    <div class="sbc-draft-heading">League Overview</div>
                    <div class="sbc-draft-subcopy">Cap thresholds, organization balances, payout structure, and league-wide financial positioning.</div>
                </div>
            </div>
        </div>
        """)

    overview_df = overall_cap_table(df, exceptions, base_cap)
    tax_team_count = (overview_df["Luxury Fee"] > 0).sum() if "Luxury Fee" in overview_df.columns else 0
    apron_1_team_count = (overview_df["Apron 1 Space"] < 0).sum() if "Apron 1 Space" in overview_df.columns else 0
    apron_2_team_count = (overview_df["Apron 2 Space"] < 0).sum() if "Apron 2 Space" in overview_df.columns else 0

    render_html(f"""
        <div class="sbc-draft-grid">
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">$</div><div class="sbc-draft-tile-value">{format_money(current_salary_cap)}</div></div>
                <div class="sbc-draft-tile-label">Salary Cap</div>
                <div class="sbc-draft-tile-note">Primary roster-building threshold for the current league year.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">Tax</div><div class="sbc-draft-tile-value">{format_money(current_luxury_tax)}</div></div>
                <div class="sbc-draft-tile-label">Luxury Tax</div>
                <div class="sbc-draft-tile-note">{tax_team_count} organizations currently project a luxury fee.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">A1</div><div class="sbc-draft-tile-value">{format_money(current_apron_1)}</div></div>
                <div class="sbc-draft-tile-label">Apron #1</div>
                <div class="sbc-draft-tile-note">{apron_1_team_count} organizations currently sit above the first apron.</div>
            </div>
            <div class="sbc-draft-tile">
                <div class="sbc-draft-tile-top"><div class="sbc-draft-tile-icon">A2</div><div class="sbc-draft-tile-value">{format_money(current_apron_2)}</div></div>
                <div class="sbc-draft-tile-label">Apron #2</div>
                <div class="sbc-draft-tile-note">{apron_2_team_count} organizations currently sit above the second apron.</div>
            </div>
        </div>
        """)

    render_html('<div class="sbc-section-label">Organization Ledger</div>')
    render_overview_table(overview_df)

    render_html('<div class="sbc-section-label">League Payouts</div>')
    render_payout_cards([
        ("Champion", unit_payout(df, exceptions, base_cap) * 12, "SBCFBL champion base-pool payout."),
        ("Runner-Up", unit_payout(df, exceptions, base_cap) * 4, "Finals runner-up base-pool payout."),
        ("Conference Finalist", unit_payout(df, exceptions, base_cap) * 2, "Paid to each conference runner-up."),
        ("Conference Semifinalist", unit_payout(df, exceptions, base_cap), "Paid to each semifinal loser."),
        ("Charity Champion", tax_payout_champ(df, exceptions, base_cap), "Champion-directed charity payout from luxury fees."),
        ("Tax Payback", tax_payout_split(df, exceptions, base_cap), "Split among non-tax organizations."),
        ("IST Champion", 75, "Flat payout for the SBCFBL Cup champion."),
        ("IST Runner Up", 15, "Flat payout for the SBCFBL Cup runner-up."),
    ])
    _legacy_tab8 = r'''
    render_html('<div class="sbc-section-label">League Thresholds</div>')
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label = "Salary Cap", value = current_salary_cap, delta = "6.669%", delta_color = "normal", help = "Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border = True, format = "dollar")
    
    with col2:
        st.metric(label = "Luxury Tax", value = current_luxury_tax, delta = "6.669%", delta_color = "normal", help = "Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border = True, format = "dollar")
    
    with col3:
        st.metric(label = "Apron #1", value = current_apron_1, delta = "6.669%", delta_color = "normal", help = "Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border = True, format = "dollar")
    
    with col4:
        st.metric(label = "Apron #2", value = current_apron_2, delta = "6.669%", delta_color = "normal", help = "Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade–related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border = True, format = "dollar")

    render_html('<div class="sbc-section-label">Organization Ledger</div>')
    overall_cap_df = overall_cap_table(df, exceptions, base_cap)
    styled_overall_cap_df = (overall_cap_df.style
        .apply(lambda row: style_overall_cap(row), axis=1)
        .format({c: "${:,.2f}" for c in overall_cap_df.columns if c in ["Base Fee", "Luxury Fee", "Balance", "Amount Paid", "Cap Space", "Tax Space", "Apron 1 Space", "Apron 2 Space"]}))
    st.dataframe(styled_overall_cap_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn(label="", width="small")})

    render_html('<div class="sbc-section-label">Base Pool Payouts</div>')
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label = "Champion Payout", value = unit_payout(df, exceptions, base_cap)*12, help = "Awarded to the SBCFBL Champion. Prize equals ½ of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    with col2:
        st.metric(label = "Runner-Up Payout", value = unit_payout(df, exceptions, base_cap)*4, help = "Awarded to the SBCFBL Runner-up. Prize equals 1⁄6 of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    with col3:
        st.metric(label = "Conference Finalists", value = unit_payout(df, exceptions, base_cap)*2, help = "Awarded to each Conference Runner-up (2 total). Prize equals 1⁄12 of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    with col4:
        st.metric(label = "Conference Semifinalists", value = unit_payout(df, exceptions, base_cap)*1, help = "Awarded to each Conference Semifinal loser (4 total). Prize equals 1⁄24 of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    render_html('<div class="sbc-section-label">Tax And Cup Payouts</div>')
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label = "Charity Champion", value = tax_payout_champ(df, exceptions, base_cap), help = "Awarded to the SBCFBL Champion to donate to a charity of their choice. Amount equals ½ of the luxury fee pool after all SBCFBL expenses.", border = True, format = "dollar")

    with col2:
        st.metric(label = "Tax Payback", value = tax_payout_split(df, exceptions, base_cap), help = "Awarded to non-tax teams for finishing outside the tax. Amount equals ½ of the luxury fee pool after all SBCFBL expenses, split evenly among non-tax teams.", border = True, format = "dollar")

    with col3:
        st.metric(label = "IST Champion", value = 75, help = "Awarded to the SBCFBL Cup Champion. Prize is a flat $75.", border = True, format = "dollar")

    with col4:
        st.metric(label = "IST Runner Up", value = 15, help = "Awarded to the SBCFBL Cup Runner-up. Prize is a flat $15.", border = True, format = "dollar")

    '''
if main_page == "Trade Machine":
    if "_sbc_trade_team" not in st.session_state:
        st.session_state["_sbc_trade_team"] = SelectedTeam if SelectedTeam in Teams else "Vegas"
    TradeTeam = st.selectbox(
        "Trade Machine Team",
        options=Teams,
        index=Teams.index(st.session_state.get("_sbc_trade_team", "Vegas")) if st.session_state.get("_sbc_trade_team", "Vegas") in Teams else Teams.index("Vegas"),
        key="_sbc_trade_team",
    )
    trade_visuals = team_visuals(TradeTeam)
    render_trade_hero(TradeTeam)

    with st.form("team_selection_form"):
        render_trade_panel_header("Build The Deal", f"{live_team_full_name(TradeTeam)} transaction worksheet", TradeTeam)
        col1, col2 = st.columns(2)
    
        with col1:
            render_trade_panel_header("Outgoing Package", "Assets leaving your organization", TradeTeam, "blue")
            SelectedPlayersOut = st.multiselect("Outgoing Players:", trade_active_player_options(df, TradeTeam, incoming=False), placeholder="")
            st_player_out, st_salary_out = st.columns([0.6, 0.4])
            with st_player_out:
                SelectedSignTradeOut = st.selectbox("Outgoing S&T Free Agent:", [""] + trade_sign_and_trade_options(df, TradeTeam, incoming=False), key="trade_st_out_player")
            with st_salary_out:
                SignTradeOutSalary = st.number_input("Signing Salary:", min_value=0, step=100000, format="%d", key="trade_st_out_salary")
            SignTradeOutSalaries = trade_single_salary_map(SelectedSignTradeOut, SignTradeOutSalary)
            SelectedPicksOut = st.multiselect("Outgoing Picks:", tradeable_picks_out(dp, TradeTeam), placeholder="")
            SelectedExceptionOut = st.multiselect("Exceptions Used:", tradeable_exceptions_out(exceptions, TradeTeam), placeholder="")
            CashOutText = st.text_input("Cash Out:", placeholder="$0")
            CashOut = parse_money_input(CashOutText)

        with col2:
            render_trade_panel_header("Incoming Package", "Assets your organization receives", tone="green")
            SelectedPlayersIn = st.multiselect("Incoming Players:", trade_active_player_options(df, TradeTeam, incoming=True), placeholder="")
            st_player_in, st_salary_in = st.columns([0.6, 0.4])
            with st_player_in:
                SelectedSignTradeIn = st.selectbox("Incoming S&T Free Agent:", [""] + trade_sign_and_trade_options(df, TradeTeam, incoming=True), key="trade_st_in_player")
            with st_salary_in:
                SignTradeInSalary = st.number_input("Signing Salary:", min_value=0, step=100000, format="%d", key="trade_st_in_salary")
            SignTradeInSalaries = trade_single_salary_map(SelectedSignTradeIn, SignTradeInSalary)
            SelectedPicksIn = st.multiselect("Incoming Picks:", tradeable_picks_in(dp, TradeTeam), placeholder="")
            SelectedExceptionIn = st.multiselect("Exceptions Used:", tradeable_exceptions_in(exceptions, TradeTeam), placeholder="")
            CashInText = st.text_input("Cash In:", placeholder="$0")
            CashIn = parse_money_input(CashInText)

        submitted = st.form_submit_button("Review Deal")

    sign_trade_out_salary = trade_salary_total(SignTradeOutSalaries)
    sign_trade_in_salary = trade_salary_total(SignTradeInSalaries)
    trade_has_assets = bool(SelectedPicksIn or SelectedPicksOut or SelectedPlayersIn or SelectedPlayersOut or SelectedSignTradeIn or SelectedSignTradeOut or SelectedExceptionIn or SelectedExceptionOut or CashIn or CashOut)

    if submitted and trade_has_assets:
        outgoing_salary = current_year_salary_for_players(df, SelectedPlayersOut) + sign_trade_out_salary
        incoming_salary = current_year_salary_for_players(df, SelectedPlayersIn) + sign_trade_in_salary
        salary_delta = incoming_salary - outgoing_salary
        current_type_col = "Type" + str(current_year)
        active_status = (df["Type"] == "Active Players") & ~df[current_type_col].isin(["Unrestricted", "Restricted", "Dead"])
        active_out = df[(df["Player"].isin(SelectedPlayersOut)) & active_status].shape[0]
        active_in = df[(df["Player"].isin(SelectedPlayersIn)) & active_status].shape[0]
        roster_before = active_player_n(df, TradeTeam)
        roster_after = roster_before - active_out + active_in + len([value for value in SignTradeInSalaries.values() if value])
        cap_total_before = get_cap_total(df, exceptions, TradeTeam)
        cap_total_after = cap_total_before - current_year_salary_for_players(df, SelectedPlayersOut) + current_year_salary_for_players(df, SelectedPlayersIn) + sign_trade_in_salary
        players_trade_out = players_out_table(df, pics, SelectedPlayersOut)
        players_traded_in = players_in_table(df, pics, SelectedPlayersIn)
        stepien_review = trade_stepien_review(dp, TradeTeam, SelectedPicksIn, SelectedPicksOut)
        apron_review = trade_apron_review(TradeTeam, SelectedPlayersIn, SelectedPlayersOut, SelectedExceptionOut, CashOut, sign_trade_in_salary, sign_trade_out_salary)
        render_trade_asset_ledger(
            TradeTeam,
            players_trade_out,
            players_traded_in,
            SelectedPicksOut,
            SelectedPicksIn,
            SelectedExceptionOut,
            SelectedExceptionIn,
            CashOut,
            CashIn,
            incoming_salary,
            outgoing_salary,
            salary_delta,
            cap_total_after,
            roster_after,
            stepien_review,
            apron_review,
            SignTradeOutSalaries,
            SignTradeInSalaries,
        )

        render_html("""
            <div class="sbc-awards-section-head">
                <span>Rule Desk</span>
                <em>Roster and apron checks using the existing SBCFBL trade logic.</em>
            </div>
        """)
        render_trade_rule_checks(TradeTeam, SelectedPlayersIn, SelectedPlayersOut, SelectedExceptionOut, CashOut, apron_review, stepien_review, sign_trade_in_salary, sign_trade_out_salary, len([value for value in SignTradeInSalaries.values() if value]))
    elif submitted:
        render_trade_panel_header("No Deal Submitted", "Select at least one player, pick, exception, or cash field to run the machine.", TradeTeam, "gold")

if main_page == "League Hub" and selected_league_page == "History" and selected_history_page == "Draft History":
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">Historical Draft Room</div>
                    <div class="sbc-draft-heading">SBC Drafts</div>
                    <div class="sbc-draft-subcopy">Draft boards by year, round, pick order, drafted organization, current organization, and player headshot.</div>
                </div>
            </div>
        </div>
        """)

    draft_year = LeagueHistoryYear
    c1, c2 = st.columns(2)
    with c1:
        render_draft_history_table(
            safe_table_call(past_draft, df, pics, dh, draft_year, "1st Round"),
            f"{draft_year} Round 1",
            "First-round selections and current team context.")
    with c2:
        render_draft_history_table(
            safe_table_call(past_draft, df, pics, dh, draft_year, "2nd Round"),
            f"{draft_year} Round 2",
            "Second-round selections and current team context.")
    _legacy_tab10 = r'''
    tab2026, tab2025, tab2024, tab2023, tab2022, tab2021, tablottery = st.tabs(["2026 Draft", "2025 Draft", "2024 Draft", "2023 Draft", "2022 Draft", "2021 Draft", "Lottery"])

    with tab2026:
        st.title("2026 SBCFBL Draft")
        col1, col2 = st.columns([1,1])

        with col1:
            st.subheader("Round 1: Saturday, June 27th")
            draft_1R = past_draft(df, pics, dh, 2026, "1st Round")
            st.dataframe(draft_1R, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

        with col2:
            st.subheader("Round 2: Sunday, June 28th")
            draft_2R = past_draft(df, pics, dh, 2026, "2nd Round")
            st.dataframe(draft_2R, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with tab2025:
        st.title("2025 SBCFBL Draft")
        col1, col2 = st.columns([1,1])

        with col1:
            st.subheader("Round 1: Saturday, June 28th")
            draft_1R_2025 = past_draft(df, pics, dh, 2025, "1st Round")
            st.dataframe(draft_1R_2025, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

        with col2:
            st.subheader("Round 2: Sunday, June 29th")
            draft_2R_2025 = past_draft(df, pics, dh, 2025, "2nd Round")
            st.dataframe(draft_2R_2025, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with tab2024:
        st.title("2024 SBCFBL Draft")
        col1, col2 = st.columns([1,1])

        with col1:
            st.subheader("Round 1: Saturday, June 29th")
            draft_1R_2024 = past_draft(df, pics, dh, 2024, "1st Round")
            st.dataframe(draft_1R_2024, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

        with col2:
            st.subheader("Round 2: Sunday, June 30th")
            draft_2R_2024 = past_draft(df, pics, dh, 2024, "2nd Round")
            st.dataframe(draft_2R_2024, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with tab2023:
        st.title("2023 SBCFBL Draft")
        col1, col2 = st.columns([1,1])

        with col1:
            st.subheader("Round 1: Saturday, June 24th")
            draft_1R_2023 = past_draft(df, pics, dh, 2023, "1st Round")
            st.dataframe(draft_1R_2023, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

        with col2:
            st.subheader("Round 2: Sunday, June 25th")
            draft_2R_2023 = past_draft(df, pics, dh, 2023, "2nd Round")
            st.dataframe(draft_2R_2023, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with tab2022:
        st.title("2022 SBCFBL Draft")
        col1, col2 = st.columns([1,1])

        with col1:
            st.subheader("Round 1: Saturday, June 25th")
            draft_1R_2022 = past_draft(df, pics, dh, 2022, "1st Round")
            st.dataframe(draft_1R_2022, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

        with col2:
            st.subheader("Round 2: Sunday, June 25th")
            draft_2R_2022 = past_draft(df, pics, dh, 2022, "2nd Round")
            st.dataframe(draft_2R_2022, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with tab2021:
        st.title("2021 SBCFBL Draft")
        col1, col2 = st.columns([1,1])

        with col1:
            st.subheader("Round 1: Saturday, July 31st")
            draft_1R_2021 = past_draft(df, pics, dh, 2021, "1st Round")
            st.dataframe(draft_1R_2021, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

        with col2:
            st.subheader("Round 2: Sunday, August 1st")
            draft_2R_2021 = past_draft(df, pics, dh, 2021, "2nd Round")
            st.dataframe(draft_2R_2021, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Drafted Team": st.column_config.ImageColumn(width="small"), "Current Team": st.column_config.ImageColumn(width="small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
    
    with tablottery:
        col1, col2, col3, col4 = st.columns(4)

        options = [None] + list(range(1, 15))

        with col1:
            ball1 = st.selectbox("Ball 1", options)
        with col2:
            ball2 = st.selectbox("Ball 2", options)
        with col3:
            ball3 = st.selectbox("Ball 3", options)
        with col4:
            ball4 = st.selectbox("Ball 4", options)        
        try:
            base_table = lottery_table(standings)
        except Exception:
            render_html('<div class="sbc-empty-state">Lottery data is not available right now.</div>')
            base_table = pd.DataFrame(columns=["Lowest Ball", "Lower Ball", "Higher Ball", "Highest Ball", "Ownership"])

        ball_cols = ["Lowest Ball", "Lower Ball", "Higher Ball", "Highest Ball"]

        filtered_table = base_table.copy()

        selected_balls = [ball1, ball2, ball3, ball4]

        for ball in selected_balls:
            if ball:
                filtered_table = filtered_table[
                    filtered_table[ball_cols].isin([ball]).any(axis=1)]
        counts = (
            filtered_table["Ownership"]
            .value_counts()
            .rename_axis("Team")
            .reset_index(name="Count")
        )

        # Get all teams from original table
        all_teams = base_table["Ownership"].unique()
        import pandas as pd
        summary = (
            pd.DataFrame({"Team": all_teams})
            .merge(counts, on="Team", how="left")
            .fillna(0)
        )

        summary["Count"] = summary["Count"].astype(int)
        
        # Sort by count descending
        summary = summary.sort_values("Count", ascending=False)
        col5, col6 = st.columns([4, 1])        
        with col5:
            st.dataframe(filtered_table, width="stretch", height="content", row_height=50, hide_index=True)
        with col6:
            st.dataframe(summary, width="stretch", hide_index=True)


    '''


def award_year_filter(table, year):
    if table is None or table.empty or "Year" not in table.columns:
        return pd.DataFrame()
    work = table.copy()
    work["_award_year"] = pd.to_numeric(work["Year"], errors="coerce")
    return work[work["_award_year"] == year].copy()


def team_award_winner(award_table, year, award):
    work = award_year_filter(award_table, year)
    if work.empty or not {"Award", "Winner"}.issubset(work.columns):
        return "Not Awarded"
    row = work[work["Award"].astype(str) == award]
    if row.empty:
        return "Not Awarded"
    return clean_pick_display(row.iloc[0]["Winner"])


def award_player_key(value):
    return player_name_match_key(value)


def month_number_from_label(value):
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    return months.get(str(value).strip().lower())


def award_calendar_rows(year):
    if period_calendar is None or period_calendar.empty or not {"Year", "Period", "Date"}.issubset(period_calendar.columns):
        return pd.DataFrame()
    calendar = period_calendar.copy()
    calendar["_award_year"] = pd.to_numeric(calendar["Year"], errors="coerce")
    calendar["_period"] = pd.to_numeric(calendar["Period"], errors="coerce")
    calendar["_date"] = pd.to_datetime(calendar["Date"], errors="coerce")
    return calendar[(calendar["_award_year"] == year) & calendar["_date"].notna()].copy()


def period_for_award_date(year, target_date):
    calendar = award_calendar_rows(year)
    if calendar.empty or pd.isna(target_date):
        return None
    eligible = calendar[calendar["_date"] <= pd.Timestamp(target_date)].copy()
    if eligible.empty:
        eligible = calendar.copy()
    period_value = eligible.sort_values("_date").iloc[-1].get("_period")
    return int(period_value) if pd.notna(period_value) else None


def regular_season_final_period(year):
    calendar = award_calendar_rows(year)
    if calendar.empty:
        return None
    regular = calendar[calendar.get("Season", "").astype(str).str.lower().eq("regular")].copy() if "Season" in calendar.columns else calendar
    if regular.empty:
        regular = calendar
    period_value = regular.sort_values("_date").iloc[-1].get("_period")
    return int(period_value) if pd.notna(period_value) else None


def final_calendar_period(year):
    calendar = award_calendar_rows(year)
    if calendar.empty:
        return None
    period_value = calendar.sort_values("_date").iloc[-1].get("_period")
    return int(period_value) if pd.notna(period_value) else None


def month_end_period(year, month_label):
    month_num = month_number_from_label(month_label)
    if not month_num:
        return None
    calendar = award_calendar_rows(year)
    if calendar.empty:
        return None
    month_rows = calendar[calendar["_date"].dt.month == month_num].copy()
    if month_rows.empty:
        return None
    period_value = month_rows.sort_values("_date").iloc[-1].get("_period")
    return int(period_value) if pd.notna(period_value) else None


def week_award_period(week_label):
    match = re.search(r"\d+", str(week_label))
    return int(match.group(0)) if match else None


def award_snapshot_period(year, award, mode="single", week_label=""):
    if mode == "allstar" or award in {"ASG MVP", "West All-Star", "East All-Star"}:
        return period_for_award_date(year, pd.Timestamp(year=year, month=2, day=1))
    if mode == "short":
        if str(week_label).lower().startswith("week"):
            return week_award_period(week_label)
        return month_end_period(year, week_label)
    season_long_awards = {
        "MVP",
        "Clutch",
        "DPOY",
        "MIP",
        "ROY",
        "6MOY",
        "All-SBC 1st Team",
        "All-SBC 2nd Team",
        "All-SBC 3rd Team",
        "All-Defense 1st Team",
        "All-Defense 2nd Team",
        "All-Rookie 1st Team",
        "All-Rookie 2nd Team",
    }
    if award in season_long_awards:
        return regular_season_final_period(year)
    return final_calendar_period(year)


def full_team_name_to_key(value):
    team_key = resolve_team_key(clean_pick_display(value))
    return team_key if team_key in team_info else ""


def logo_for_team_key(team_key):
    return team_logo_for_name(team_key) if team_key in team_info else ""


def award_roster_team_for_player(fantrax_id, year, period_value):
    if is_blank_value(fantrax_id) or all_time_rosters is None or all_time_rosters.empty or period_value is None:
        return ""
    rosters = all_time_rosters.copy()
    year_col = "Year" if "Year" in rosters.columns else "year"
    if not {"id", "period", "team_name", year_col}.issubset(rosters.columns):
        return ""
    rosters["_award_year"] = pd.to_numeric(rosters[year_col], errors="coerce")
    rosters["_award_period"] = pd.to_numeric(rosters["period"], errors="coerce")
    rows = rosters[
        (rosters["id"].astype(str) == str(fantrax_id))
        & (rosters["_award_year"] == year)
        & (rosters["_award_period"] <= period_value)
    ].copy()
    if rows.empty:
        return ""
    rows = rows.sort_values("_award_period")
    exact = rows[rows["_award_period"] == period_value]
    if not exact.empty:
        rows = exact
    return full_team_name_to_key(rows.iloc[-1].get("team_name", ""))


def award_base_rows(year, award, mode="single"):
    if award_history is None or award_history.empty or not {"Award", "Year", "Winner"}.issubset(award_history.columns):
        return pd.DataFrame(columns=["Award", "Year", "Winner", "Week"])
    work = award_year_filter(award_history, year)
    if work.empty:
        return pd.DataFrame(columns=["Award", "Year", "Winner", "Week"])
    work = work.copy()
    if mode == "short":
        work["Week"] = work["Award"].astype(str).str.extract(r"(Week \d+|January|February|March|April|May|June|July|August|September|October|November|December)")[0]
        work["Award_clean"] = work["Award"].astype(str).apply(lambda value: " ".join([value.split()[0], value.split()[-1]]) if value.split() else "")
        work = work[work["Award_clean"] == award].copy()
    else:
        work = work[work["Award"].astype(str) == award].copy()
        work["Week"] = ""
    work = work[~work["Winner"].astype(str).str.strip().isin(["", "Not Awarded"])].copy()
    return work


def award_team_override(year, award):
    if award == "Champion":
        return team_award_winner(team_award_history, year, "Champion")
    if award == "Cup Winner":
        return team_award_winner(team_award_history, year, "Cup Winner")
    return ""


def player_award_table(year, award, mode="single"):
    rows = award_base_rows(year, award, mode)
    if rows.empty:
        return pd.DataFrame(columns=["Week", "logo", "Winner", "Picture_Online"])
    players = ft_players.copy() if ft_players is not None else pd.DataFrame()
    pictures = pics.copy() if pics is not None else pd.DataFrame()
    if "name" in players.columns:
        players["_player_key"] = players["name"].apply(award_player_key)
    else:
        players["_player_key"] = ""
    if "Player" in pictures.columns:
        pictures["_player_key"] = pictures["Player"].apply(award_player_key)
    else:
        pictures["_player_key"] = ""
    rows["_player_key"] = rows["Winner"].apply(award_player_key)
    if {"_player_key", "fantraxId"}.issubset(players.columns):
        rows = rows.merge(players[["_player_key", "fantraxId"]], on="_player_key", how="left")
    else:
        rows["fantraxId"] = ""
    if {"_player_key", "Picture_Online"}.issubset(pictures.columns):
        rows = rows.merge(pictures[["_player_key", "Picture_Online"]], on="_player_key", how="left")
    else:
        rows["Picture_Online"] = ""
    forced_team = award_team_override(year, award)
    logos = []
    for _, row in rows.iterrows():
        team_key = forced_team if forced_team in team_info else ""
        if not team_key:
            snapshot_period = award_snapshot_period(year, award, mode, row.get("Week", ""))
            team_key = award_roster_team_for_player(row.get("fantraxId", ""), year, snapshot_period)
        logos.append(logo_for_team_key(team_key))
    rows["logo"] = logos
    if mode == "short":
        categories = ["November", "December", "January", "February", "March"] + [f"Week {i}" for i in range(1, 39)]
        rows["Week"] = pd.Categorical(rows["Week"], categories=categories, ordered=True)
        rows = rows.sort_values("Week")
    else:
        rows = rows.sort_values("Winner")
    return rows[["Week", "logo", "Winner", "Picture_Online"]] if mode == "short" else rows[["logo", "Winner", "Picture_Online"]]


def render_award_player_rows(data, compact=False):
    if data is None or data.empty:
        return '<div class="sbc-award-empty">Not awarded yet</div>'
    cards = []
    for _, row in data.iterrows():
        name = clean_pick_display(row.get("Winner", ""))
        picture = row.get("Picture_Online", "")
        logo = row.get("logo", "")
        week = clean_pick_display(row.get("Week", ""))
        award_team = team_from_logo(logo)
        team_style = ""
        if award_team:
            visuals = team_visuals(award_team)
            team_style = (
                f' style="--award-row-color:{escape(str(visuals["primary"]), quote=True)};'
                f'--award-row-secondary:{escape(str(visuals["secondary"]), quote=True)};'
                f'--award-row-font:{escape(str(visuals["font"]), quote=True)};"'
            )
        week_html = "" if is_blank_value(week) or str(week).strip() in ["-", "—", "â€”"] else f'<span class="sbc-award-week">{escape(str(week))}</span>'
        logo_html = f'<img class="sbc-award-mini-logo" src="{escape(str(logo), quote=True)}" alt="Team logo" referrerpolicy="no-referrer">' if not is_blank_value(logo) else ""
        img_html = f'<img class="sbc-award-headshot" src="{escape(str(picture), quote=True)}" alt="{escape(str(name), quote=True)}">' if not is_blank_value(picture) else '<div class="sbc-award-headshot sbc-award-headshot-empty"></div>'
        cards.append(f"""
            <div class="sbc-award-player {'sbc-award-player-compact' if compact else ''}"{team_style}>
                {img_html}
                <div>
                    {week_html}
                    <strong>{escape(str(name))}</strong>
                    {logo_html}
                </div>
            </div>
        """)
    return "".join(cards)


def render_player_award(title, award, year, mode="single", tone="blue", compact=False):
    data = player_award_table(year, award, mode)
    render_html(f"""
        <section class="sbc-award-card sbc-award-card-{tone}">
            <div class="sbc-award-card-top">
                <span>{escape(title)}</span>
                <em>{escape(str(year))}</em>
            </div>
            <div class="sbc-award-player-grid {'sbc-award-player-grid-compact' if compact else ''}">
                {render_award_player_rows(data, compact=compact)}
            </div>
        </section>
    """)


def render_team_award_card(title, award, year, tone="blue", feature=False, stacked=False):
    winner = team_award_winner(team_award_history, year, award)
    if winner in team_info:
        visuals = team_visuals(winner)
        spotlight_class = "sbc-award-team-spotlight sbc-award-team-spotlight-stacked" if stacked else "sbc-award-team-spotlight"
        team_content = f"""
            <div class="{spotlight_class}">
                <img src="{escape(str(visuals["logo"]), quote=True)}" alt="{escape(live_team_full_name(winner), quote=True)} logo" referrerpolicy="no-referrer">
                <strong style="--award-team-font:{escape(str(visuals["font"]), quote=True)};">{escape(live_team_full_name(winner))}</strong>
            </div>
        """
        color = team_color_for_name(winner)
        secondary = team_secondary_for_name(winner)
    else:
        team_content = f'<span class="sbc-award-team-missing">{escape(str(winner))}</span>'
        color = LEAGUE_PRIMARY
        secondary = LEAGUE_SECONDARY
    render_html(f"""
        <section class="sbc-award-team-card sbc-award-card-{tone} {'sbc-award-team-feature' if feature else ''}" style="--award-team-color:{escape(str(color), quote=True)};--award-team-secondary:{escape(str(secondary), quote=True)};">
            <div class="sbc-award-card-top">
                <span>{escape(title)}</span>
                <em>{escape(str(year))}</em>
            </div>
            <div class="sbc-award-wordmark-wrap">{team_content}</div>
        </section>
    """)


def render_awards_section(title, subtitle, columns):
    render_html(f"""
        <div class="sbc-awards-section-head">
            <span>{escape(title)}</span>
            <em>{escape(subtitle)}</em>
        </div>
    """)
    return st.columns(columns)


def render_about_feature(title, body, stat=None, accent="blue"):
    stat_html = f'<div class="sbc-about-stat">{escape(str(stat))}</div>' if stat else ""
    render_html(f"""
        <section class="sbc-about-feature sbc-about-feature-{accent}">
            {stat_html}
            <div class="sbc-about-feature-title">{escape(title)}</div>
            <div class="sbc-about-feature-body">{escape(body)}</div>
        </section>
    """)


def render_about_rule_card(title, items, accent="blue"):
    rows = "".join(f"<li>{escape(str(item))}</li>" for item in items)
    render_html(f"""
        <section class="sbc-about-rule-card sbc-about-feature-{accent}">
            <div class="sbc-about-rule-title">{escape(title)}</div>
            <ul>{rows}</ul>
        </section>
    """)


def render_check_card(title, description, check_df):
    count = 0 if check_df is None else check_df.shape[0]
    status = "clear" if count == 0 else "issue"
    status_text = "Clear" if count == 0 else f"{count} issues"
    render_html(f"""
        <section class="sbc-check-card sbc-check-{status}">
            <div class="sbc-check-top">
                <div>
                    <div class="sbc-check-title">{escape(title)}</div>
                    <div class="sbc-check-copy">{escape(description)}</div>
                </div>
                <div class="sbc-check-badge">{escape(status_text)}</div>
            </div>
        </section>
    """)
    if count > 0:
        with st.expander(f"Review {title}", expanded=False):
            st.dataframe(check_df, width="stretch", hide_index=True)


if main_page == "League Hub" and selected_league_page == "History" and selected_history_page == "Awards":
    AwardYears = LeagueHistoryYear
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">{AwardYears} Trophy Case</div>
                    <div class="sbc-draft-heading">SBCFBL Awards</div>
                    <div class="sbc-draft-subcopy">Champions, postseason heroes, award winners, all-league teams, all-stars, and monthly honors in one polished gallery.</div>
                </div>
            </div>
        </div>
    """)

    col1, col2 = render_awards_section("Crown Jewels", "League champion, Cup champion, and signature postseason stars.", [1, 1])
    with col1:
        render_team_award_card("SBCFBL Champion", "Champion", AwardYears, "gold", feature=True)
        render_player_award("Finals MVP", "Finals MVP", AwardYears, tone="gold")
        render_player_award("Championship Roster", "Champion", AwardYears, tone="gold", compact=True)
    with col2:
        render_team_award_card("SBCFBL Cup Winner", "Cup Winner", AwardYears, "gold", feature=True)
        render_player_award("Cup MVP", "Cup MVP", AwardYears, tone="gold")
        render_player_award("Cup-Winning Roster", "Cup Winner", AwardYears, tone="gold", compact=True)

    west_col, east_col = render_awards_section("Conference & Division Crowns", "The paths through each side of the bracket.", [1, 1])
    with west_col:
        render_team_award_card("Western Conference Champion", "WC Champion", AwardYears, "green")
        render_player_award("Western Conference MVP", "WCF MVP", AwardYears, tone="green")
        div_cols = st.columns(3)
        with div_cols[0]:
            render_team_award_card("Pacific Champion", "Pacific Champion", AwardYears, "green", stacked=True)
        with div_cols[1]:
            render_team_award_card("Northwest Champion", "Northwest Champion", AwardYears, "green", stacked=True)
        with div_cols[2]:
            render_team_award_card("Southwest Champion", "Southwest Champion", AwardYears, "green", stacked=True)
    with east_col:
        render_team_award_card("Eastern Conference Champion", "EC Champion", AwardYears, "blue")
        render_player_award("Eastern Conference MVP", "ECF MVP", AwardYears, tone="blue")
        div_cols = st.columns(3)
        with div_cols[0]:
            render_team_award_card("Central Champion", "Central Champion", AwardYears, "blue", stacked=True)
        with div_cols[1]:
            render_team_award_card("Atlantic Champion", "Atlantic Champion", AwardYears, "blue", stacked=True)
        with div_cols[2]:
            render_team_award_card("Southeast Champion", "Southeast Champion", AwardYears, "blue", stacked=True)

    cols = render_awards_section("Individual Hardware", "The season's headliners and category kings.", [1, 1, 1])
    individual_awards = [
        ("Most Valuable Player", "MVP", "purple"),
        ("Clutch Player of the Year", "Clutch", "purple"),
        ("Defensive Player of the Year", "DPOY", "purple"),
        ("Most Improved Player", "MIP", "purple"),
        ("Rookie of the Year", "ROY", "purple"),
        ("Sixth Man of the Year", "6MOY", "purple"),
    ]
    for idx, (title, award, tone) in enumerate(individual_awards):
        with cols[idx % 3]:
            render_player_award(title, award, AwardYears, tone=tone)

    team_cols = render_awards_section("All-League Teams", "The best five-man groups from the season.", [1, 1, 1])
    for col, (title, award, tone) in zip(team_cols, [("All-SBC First Team", "All-SBC 1st Team", "purple"), ("All-SBC Second Team", "All-SBC 2nd Team", "purple"), ("All-SBC Third Team", "All-SBC 3rd Team", "purple")]):
        with col:
            render_player_award(title, award, AwardYears, tone=tone, compact=True)

    col1, col2 = render_awards_section("Defense, Rookies & All-Star Stage", "Special teams, regular season crown, and showcase stars.", [1, 1])
    with col1:
        render_player_award("All-Defense First Team", "All-Defense 1st Team", AwardYears, tone="purple", compact=True)
        render_player_award("All-Rookie First Team", "All-Rookie 1st Team", AwardYears, tone="purple", compact=True)
        render_team_award_card("Regular Season Champion", "RS Champion", AwardYears, "gold")
        render_player_award("Western Conference All-Stars", "West All-Star", AwardYears, mode="allstar", tone="green", compact=True)
    with col2:
        render_player_award("All-Defense Second Team", "All-Defense 2nd Team", AwardYears, tone="purple", compact=True)
        render_player_award("All-Rookie Second Team", "All-Rookie 2nd Team", AwardYears, tone="purple", compact=True)
        render_player_award("All-Star Game MVP", "ASG MVP", AwardYears, tone="gold")
        render_player_award("Eastern Conference All-Stars", "East All-Star", AwardYears, mode="allstar", tone="blue", compact=True)

    col1, col2 = render_awards_section("Monthly & Weekly Honors", "A full season of recurring winners without the spreadsheet slog.", [1, 1])
    with col1:
        render_player_award("West Player of the Month", "West POM", AwardYears, mode="short", tone="green", compact=True)
        render_player_award("West Rookie of the Month", "West ROM", AwardYears, mode="short", tone="green", compact=True)
        render_player_award("West Player of the Week", "West POW", AwardYears, mode="short", tone="green", compact=True)
    with col2:
        render_player_award("East Player of the Month", "East POM", AwardYears, mode="short", tone="blue", compact=True)
        render_player_award("East Rookie of the Month", "East ROM", AwardYears, mode="short", tone="blue", compact=True)
        render_player_award("East Player of the Week", "East POW", AwardYears, mode="short", tone="blue", compact=True)
    _legacy_tab11 = r'''
    st.title("2025 SBCFBL Awards")

    col1, col2 = st.columns([1,1])

    with col1:
        st.subheader("SBCFBL Champion")
        Champion = get_team_award(team_award_history, AwardYears, "Champion")
        st.image(Champion)
        st.subheader("SBCFBL Finals Most Valuable Player")
        FinalsMVP = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "Finals MVP")
        st.dataframe(FinalsMVP, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("List of SBCFBL Champions")
        PChampion = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "Champion")
        PChampion = PChampion.drop(columns=["logo"])
        st.dataframe(PChampion, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with col2:
        st.subheader("SBCFBL Cup Winner")
        CupChamp = get_team_award(team_award_history, AwardYears, "Cup Winner")
        st.image(CupChamp)
        st.subheader("SBCFBL Cup Most Valuable Player")
        CupMVP = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "Cup MVP")
        st.dataframe(CupMVP, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("List of SBCFBL Cup Winners")
        CupPlayers = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "Cup Winner")
        CupPlayers = CupPlayers.drop(columns=["logo"])
        st.dataframe(CupPlayers, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    col1, col2 = st.columns([1,1])

    with col1:
        st.subheader("Western Conference Champion")
        WChampion = get_team_award(team_award_history, AwardYears, "WC Champion")
        st.image(WChampion)
        st.subheader("SBCFBL Western Conference Most Valuable Player")
        WFinalsMVP = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "WCF MVP")
        st.dataframe(WFinalsMVP, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Pacific Division Champion")
        PacChampion = get_team_award(team_award_history, AwardYears, "Pacific Champion")
        st.image(PacChampion)
        st.subheader("Northwest Division Champion")
        NWChampion = get_team_award(team_award_history, AwardYears, "Northwest Champion")
        st.image(NWChampion)
        st.subheader("Southwest Division Champion")
        SWChampion = get_team_award(team_award_history, AwardYears, "Southwest Champion")
        st.image(SWChampion)

    with col2:
        st.subheader("Eastern Conference Champion")
        EChampion = get_team_award(team_award_history, AwardYears, "EC Champion")
        st.image(EChampion)
        st.subheader("SBCFBL Eastern Conference Most Valuable Player")
        EFinalsMVP = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "ECF MVP")
        st.dataframe(EFinalsMVP, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Central Division Champion")
        CChampion = get_team_award(team_award_history, AwardYears, "Central Champion")
        st.image(CChampion)
        st.subheader("Atlantic Division Champion")
        AChampion = get_team_award(team_award_history, AwardYears, "Atlantic Champion")
        st.image(AChampion)
        st.subheader("Southeast Division Champion")
        SEChampion = get_team_award(team_award_history, AwardYears, "Southeast Champion")
        st.image(SEChampion)


    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.subheader("Most Valuable Player")
        MVP = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "MVP")
        st.dataframe(MVP, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Clutch Player of the Year")
        Clutch = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "Clutch")
        st.dataframe(Clutch, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with col2:
        st.subheader("Defensive Player of the Year")
        DPOY = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "DPOY")
        st.dataframe(DPOY, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Most Improved Player")
        MIP = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "MIP")
        st.dataframe(MIP, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with col3:
        st.subheader("Rookie of the Year")
        ROY = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "ROY")
        st.dataframe(ROY, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Sixth Man of the Year")
        MOY6 = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "6MOY")
        st.dataframe(MOY6, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    col1, col2, col3 = st.columns([1,1,1])

    with col1:
        st.subheader("All-SBC First Team")
        ASBC1 = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "All-SBC 1st Team")
        st.dataframe(ASBC1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with col2:
        st.subheader("All-SBC Second Team")
        ASBC2 = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "All-SBC 2nd Team")
        st.dataframe(ASBC2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with col3:
        st.subheader("All-SBC Third Team")
        ASBC3 = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "All-SBC 3rd Team")
        st.dataframe(ASBC3, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    col1, col2 = st.columns([1,1])

    with col1:
        st.subheader("All-Defense First Team")
        AD1 = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "All-Defense 1st Team")
        st.dataframe(AD1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("All-Rookie First Team")
        AR1 = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "All-Rookie 1st Team")
        st.dataframe(AR1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Regular Season Champion")
        RSChampion = get_team_award(team_award_history, AwardYears, "RS Champion")
        st.image(RSChampion)
        st.subheader("Western Conference All-Stars")
        ASW = get_all_stars_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "West All-Star")
        st.dataframe(ASW, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Western Conference Player of the Month")
        WCPOM = get_short_term_awards(award_history, ft_players, all_time_rosters, pics, AwardYears, "West POM")
        st.dataframe(WCPOM, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Western Conference Rookie of the Month")
        WCROM = get_short_term_awards(award_history, ft_players, all_time_rosters, pics, AwardYears, "West ROM")
        st.dataframe(WCROM, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Western Conference Player of the Week")
        WCPOW = get_short_term_awards(award_history, ft_players, all_time_rosters, pics, AwardYears, "West POW")
        st.dataframe(WCPOW, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    with col2:
        st.subheader("All-Defense Second Team")
        AD2 = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "All-Defense 2nd Team")
        st.dataframe(AD2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("All-Rookie Second Team")
        AR2 = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "All-Rookie 2nd Team")
        st.dataframe(AR2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("All-Star Game MVP")
        ASGMVP = get_single_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "ASG MVP")
        st.dataframe(ASGMVP, width = "stretch", height = "content", row_height = 69, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Eastern Conference All-Stars")
        ASE = get_all_stars_award(award_history, ft_players, all_time_rosters, pics, AwardYears, "East All-Star")
        st.dataframe(ASE, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Eastern Conference Player of the Month")
        ECPOM = get_short_term_awards(award_history, ft_players, all_time_rosters, pics, AwardYears, "East POM")
        st.dataframe(ECPOM, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Eastern Conference Rookie of the Month")
        ECROM = get_short_term_awards(award_history, ft_players, all_time_rosters, pics, AwardYears, "East ROM")
        st.dataframe(ECROM, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})
        st.subheader("Eastern Conference Player of the Week")
        ECPOW = get_short_term_awards(award_history, ft_players, all_time_rosters, pics, AwardYears, "East POW")
        st.dataframe(ECPOW, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"logo": st.column_config.ImageColumn(label = "Team", width = "small"), "Picture_Online": st.column_config.ImageColumn(label = "", width = "small")})

    '''

if main_page == "About":
    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">Rules / Origin / Operating Model</div>
                    <div class="sbc-draft-heading">About SBCFBL</div>
                    <div class="sbc-draft-subcopy">A front-office fantasy basketball league built around NBA-style roster building, cap strategy, scheduled drafts, custom organizations, and real competitive stakes.</div>
                </div>
            </div>
        </div>
    """)

    render_html("""
        <div class="sbc-awards-section-head">
            <span>League Guide</span>
            <em>The original SBCFBL overview, preserved with the full written detail.</em>
        </div>
    """)

    render_about_copy_card("SBCFBL Introduction", """
        <p>The <strong>Sports Business Classroom Fantasy Basketball League (SBCFBL)</strong> was established in Fall 2020 by alumni of the Sports Business Classroom 2019 and 2020 cohorts. The SBCFBL was inspired by guidance from Seth Partnow, who encouraged students pursuing careers in the NBA to gain hands-on experience by managing every aspect of a simulated professional team.</p>
        <p>The SBCFBL was created and developed from the ground up by <a href="https://x.com/McCadeP8">McCade Pearson</a>. Over the past six years, SBCFBL has been intentionally designed to closely mirror the structure, rules, and financial mechanics outlined in the NBA's official <a href="https://imgix.cosmicjs.com/25da5eb0-15eb-11ee-b5b3-fbd321202bdf-Final-2023-NBA-Collective-Bargaining-Agreement-6-28-23.pdf">Collective Bargaining Agreement (CBA)</a>.</p>
        <p>Since its launch, SBCFBL has helped more than half a dozen participants secure roles with NBA teams and has raised over $10,000 for charitable causes, serving as both a professional development platform and a vehicle for positive community impact.</p>
    """, "blue")

    about_cols = st.columns(2)
    with about_cols[0]:
        render_about_copy_card("SBCFBL Pre-Launch", """
            <p>During the SBCFBL's formation, McCade Pearson led the development of all franchise identities. This process included the creation of 30 distinct and original brands, each with a unique location, area-appropriate team name, and customized color scheme. In 2022, this branding effort was further expanded to include original team logos for every franchise.</p>
            <p>All 30 organizations are based in the United States or Vancouver. To date, the only franchise to undergo rebranding is the San Diego Wave, following the introduction of an NWSL expansion team with the same name.</p>
        """, "green")
    with about_cols[1]:
        render_about_copy_card("SBCFBL Initial Roster Construction", """
            <p>To initialize rosters, SBCFBL conducted a 30-team slow blind auction over the course of multiple 'days'. Each organization began with a clean salary cap sheet, along with access to the full Mid-Level Exception (MLE) and Bi-Annual Exception (BAE) in Year 1 to facilitate roster construction and competitive balance.</p>
            <p>To ensure a realistic distribution of contract lengths across the SBCFBL, contract values were permitted to differ from real-world figures, while contract durations were aligned with each player's actual NBA contract length at the time. Following a series of randomized draws and strategic bidding rounds, all 30 team rosters were completed and the SBCFBL officially launched.</p>
        """, "gold")

    render_about_copy_card("SBCFBL Scoring System", """
        <p>The SBCFBL scoring system is modeled after the structure of the United States Electoral College. Rather than states, the SBCFBL allocates weighted values to traditional basketball performance categories that most strongly correlate with winning NBA games-beyond points alone.</p>
        <p>Each category contributes a fixed number of "votes," with higher-impact metrics carrying greater weight.</p>
        <ul>
            <li><strong>Points</strong>: 61</li>
            <li><strong>Assists</strong>: 41</li>
            <li><strong>True Shooting Percentage</strong>: 41</li>
            <li><strong>Blocks</strong>: 31</li>
            <li><strong>Defensive Rebounds</strong>: 31</li>
            <li><strong>Offensive Rebounds</strong>: 31</li>
            <li><strong>Plus-Minus</strong>: 31</li>
            <li><strong>Steals</strong>: 31</li>
            <li><strong>Three-Point Percentage</strong>: 31</li>
            <li><strong>Two-Point Percentage</strong>: 31</li>
            <li><strong>Free Throw Percentage</strong>: 21</li>
            <li><strong>Turnovers*</strong>: -21</li>
            <li><strong>Minutes Played</strong>: 11</li>
        </ul>
        <p>In total, <strong>413 points</strong> are available in each matchup, with <strong>207 points required to win</strong>. The inclusion of an additional digit in each category allows a tie to be resolved by awarding the win to the team that captures the most individual categories. In the rare event of a 206.5-206.5 tie, the win is awarded to the home team.</p>
        <p>To be eligible to win the four efficiency categories, teams must meet the following minimum thresholds: <strong>10 field goal attempts (FGA)</strong>, <strong>10 three-point attempts (3PA)</strong>, and <strong>5 free throw attempts (FTA)</strong>.</p>
        <p>This nontraditional scoring system expands strategic flexibility and encourages sophisticated analytical decision-making, creating a more dynamic and engaging competitive environment than standard fantasy formats.</p>
        <p><em>*For Turnovers, the team with the lower total is awarded the category.</em></p>
    """, "blue")

    about_cols = st.columns(2)
    with about_cols[0]:
        render_about_copy_card("SBCFBL Roster Construction", """
            <p>To balance the need for a waiver wire, the SBCFBL employs unique roster rules. Each organization must maintain a <strong>minimum of 12 players</strong> and may carry <strong>up to 14 players</strong> during the season. Instead of two-way contracts, each organization has access to <strong>three IR slots</strong>. During the offseason, rosters may expand to a straight <strong>17 players</strong>.</p>
            <p>The SBCFBL also accommodates <strong>overseas players</strong>. To qualify, a player must be drafted by the SBCFBL and assigned 'overseas' during the summer prior to the season, locking in their status on opening night. These players may remain overseas for the duration of their rookie contract. This system allows organizations to retain second-round draft picks in situations where a standard roster would not have space for them.</p>
            <p>On a day-to-day basis, each SBCFBL organization maintains roster spots for the following positions:</p>
            <ul><li><strong>Point Guard (PG)</strong></li><li><strong>Shooting Guard (SG)</strong></li><li><strong>Small Forward (SF)</strong></li><li><strong>Power Forward (PF)</strong></li><li><strong>Center (C)</strong></li><li><strong>Three Flex (FLX)</strong></li><li><strong>Six Bench</strong></li></ul>
            <p>Player position eligibility is determined by <strong>Fantrax</strong> each season. Organizations may request the addition of a new position for a player within <strong>two weeks after the season begins</strong>. The commissioner reviews these requests using independent sources and makes the final decision.</p>
        """, "green")
    with about_cols[1]:
        render_about_copy_card("SBCFBL Season Structure", """
            <p>The SBCFBL consists of 30 organizations organized into six divisions across two conferences. The regular season schedule is designed to emulate the length and intensity of the NBA. Following minor adjustments due to COVID-shortened seasons, the SBCFBL now plays a <strong>72-game schedule</strong>, consisting of a <strong>triple round-robin for 42 intraconference games</strong> and a <strong>double round-robin for 30 interconference games</strong> per organization, spread over <strong>36 periods</strong>. Each period features two games per organization played over a 3-4 day stretch.</p>
            <p>The playoffs closely mirror the NBA's format, beginning with <strong>two rounds of three-day play-in games</strong>, followed by <strong>four rounds of seven-day playoff series</strong>, ultimately producing a single, undisputed SBCFBL champion who hoists the Larry Coon Trophy.</p>
            <p>With the addition of the NBA Cup in 2023, the SBCFBL added a cup as well. organizations play four games in the five periods leading up to a quarterfinal, semfinal, and championship matchup that takes place over the NBA Cup Final. While NBA Cup Final games obviously don't count, they do in only our SBCFBL Cup Championship for entertainment purposes. None of the SBCFBL Cup games count towards our regular season standings due to the complexity of folding them into the regular season schedule.</p>
        """, "gold")

    render_about_copy_card("SBCFBL Financial Structure", """
        <p>The SBCFBL initially launched using a <strong>2,000,000:1 scale</strong> relative to the NBA, meaning a player with a $10,000,000 salary would cost an owner $5 in the league. As the NBA salary cap increased, the league adjusted to a <strong>3,000,000:1 scale</strong> for the 2025-26 season to keep entry fees accessible while maintaining realistic roster management. Currently the formula used to determine the ratio for the year is to take the NBA's Salary Cap, divide by 60,000,000 and raise the quotient to the nearest integer before multiplying by 1,000,000. The league also enforces a <strong>luxury tax</strong> consistent with the NBA's structure.</p>
        <p>Entry fees collected for each organization's base roster are pooled into a league fund. These funds are first allocated to cover operational expenses, including <strong>Fantrax fees</strong> and the purchase of the <strong>Larry Coon Trophy</strong>. After these costs, remaining funds are distributed to successful organizations as follows:</p>
        <ul><li><strong>Champion</strong>: 1/2 of the remaining pool</li><li><strong>Runner-up</strong>: 1/6 of the remaining pool</li><li><strong>Conference Finalists (2 organizations)</strong>: 1/12 each of the remaining poool</li><li><strong>Conference Semifinalists (4 organizations)</strong>: 1/24 each each of the remaining pool</li></ul>
        <p>In addition to entry fees, the SBCFBL collects <strong>luxury tax payments</strong>. During the league's first five years, the full luxury tax pool was awarded to the league champion to donate to a charity of their choice. This approach both supported charitable causes and limited organizations' ability to recoup luxury tax payments to fund additional championships.</p>
        <p>As of the 2025-26 season, <strong>50% of the luxury tax pool continues to be allocated to charitable causes</strong>, while the remaining 50% is redistributed evenly among organizations that did not exceed the luxury tax threshold.</p>
        <p><strong>SBCFBL Cup</strong> carries an entry fee of <strong>$3</strong> per organization. The winner of the Cup receives <strong>$75</strong>, while the runner-up is awarded <strong>$15</strong>.</p>
    """, "blue")

    about_cols = st.columns(2)
    with about_cols[0]:
        render_about_copy_card("SBCFBL Free Agency", """
            <p>The SBCFBL Free Agency moratorium spans <strong>seven "days"</strong>, each lasting 48 hours, concluding on <strong>July 1, 3, 5, 7, 9, 11, and 13</strong>. During this period, organizations place bids through a <strong>Qualtrics survey</strong>, with a maximum of <strong>20 bids per organization per day</strong>.</p>
            <p>After each day, <strong>signings are announced</strong>, along with an updated list of free agents showing the number of bids received and the current highest bid for each player.</p>
            <p>Players are released in <strong>three tiers</strong> based on their previous season's salary. A player signs after either receiving <strong>five bids</strong> or having at least one bid for <strong>two consecutive days</strong> (signing on the third day). Players sign for the <strong>highest year-one salary bid</strong>, and organizations determine contract length <strong>as part of their bid</strong>, not after securing the signing.</p>
            <p>All offseason contracts in the SBCFBL are <strong>fully guaranteed</strong>. <strong>Player options</strong> are not permitted, as allowing them would require every signing to include one. Similarly, <strong>team options</strong> are disallowed outside of rookie contracts, ensuring clarity and consistency in all agreements.</p>
            <p>Any players with remaining bids sign on the <strong>seventh day</strong>, marking the end of the moratorium.</p>
            <p><strong>Restricted free agent signings</strong> have just under one day for the incumbent organization to match a bid. <strong>Sign-and-trade deals</strong> are permitted, provided the transaction is agreed upon by the conclusion of the moratorium.</p>
            <p>In the event of multiple organizations submitting identical bids for a player, the incumbent organization has a <strong>50% chance</strong> to retain the player, while the remaining organizations split the other 50%. For <strong>supermax-eligible players</strong>, if the incumbent organization matches the supermax amount, they have a <strong>75% chance</strong> to retain the player.</p>
            <p>This 48-hour bidding process continues throughout free agency, but activity generally slows significantly after the moratorium concludes. Once the SBCFBL season begins, <strong>contracts become non-guaranteed</strong>, and organizations may only execute signings on the <strong>first day of a matchup</strong>.</p>
        """, "green")
    with about_cols[1]:
        render_about_copy_card("SBCFBL Draft", """
            <p>The SBCFBL Draft follows the same structure as the NBA Draft, including <strong>lottery procedures and tiebreakers</strong>. Rather than using a traditional countdown timer for each pick, the draft operates on <strong>scheduled timeslots</strong>. For example, the <strong>first overall pick</strong> always occurs between <strong>10:00 a.m. and 10:30 a.m. EDT</strong> on the Saturday following the NBA Draft, with the <strong>second pick</strong> due at <strong>11:00 a.m. EDT</strong>, and so on.</p>
            <p>If all organizations submit their picks early, the next organization may proceed immediately. Should a team <strong>miss their designated timeslot</strong>, multiple organizations may be placed <strong>on the clock simultaneously</strong>. Any organization that is <strong>over two hours late</strong> will have their pick <strong>autodrafted</strong>, typically receiving the highest remaining NBA draft pick (e.g., the first pick would be autodrafted at 12:30 p.m. EDT, likely selecting the 5th overall player).</p>
            <p>The <strong>second round</strong> follows the same timeslot framework on <strong>Sunday</strong>, maintaining consistency and pace throughout the draft.</p>
        """, "gold")

    about_cols = st.columns(2)
    with about_cols[0]:
        render_about_copy_card("SBCFBL Trade Deadline", """
            <p>The SBCFBL Trade Deadline occurs 24 hours after the NBA Trade Deadline, typically on Friday at 3:00 PM EST. As with all trades, a trade must be formally presented and agreed upon in a "call" (i.e., a private Discord group chat) involving all parties. On trade deadline day, the group chat between the involved parties and McCade must be initiated before the official deadline.</p>
            <p>At 3:00 PM, McCade will begin processing trades. Teams may continue negotiations and finalize details up until McCade addresses the trade call. If any issues arise, the trade will be placed at the back of the queue, and corrections can be made until McCade returns to it.</p>
            <p>The trade market officially closes once McCade has updated all trades, which may occur within minutes or several hours.</p>
        """, "red")
    with about_cols[1]:
        render_about_copy_card("SBCFBL Other Information", """
            <p>All other SBCFBL operations adhere as closely as possible to the <strong>NBA Collective Bargaining Agreement (CBA)</strong>, including, but not limited to, <strong>salary cap rules, trade regulations, exceptions, and deadlines</strong>. Most SBCFBL deadlines are set on a <strong>24-hour delay</strong> relative to the NBA, including the <strong>waive-and-stretch deadline, player guarantee date, offseason signing and trade restrictions,</strong> and the <strong>trade deadline</strong>.</p>
            <p>This document is intended as a <strong>quick-reference guide</strong> and is not an exhaustive rulebook. Its purpose is to provide key information and highlight why the SBCFBL is considered <strong>the premier fantasy basketball experience</strong>.</p>
        """, "blue")

    _legacy_tab12 = r'''
    st.subheader("SBCFBL Introduction")
    st.markdown("""
    The **Sports Business Classroom Fantasy Basketball League (SBCFBL)** was established in Fall 2020 by alumni of the Sports Business Classroom 2019 and 2020 cohorts. The SBCFBL was inspired by guidance from Seth Partnow, who encouraged students pursuing careers in the NBA to gain hands-on experience by managing every aspect of a simulated professional team.

    The SBCFBL was created and developed from the ground up by [McCade Pearson](https://x.com/McCadeP8). Over the past six years, SBCFBL has been intentionally designed to closely mirror the structure, rules, and financial mechanics outlined in the NBA’s official [Collective Bargaining Agreement (CBA)](https://imgix.cosmicjs.com/25da5eb0-15eb-11ee-b5b3-fbd321202bdf-Final-2023-NBA-Collective-Bargaining-Agreement-6-28-23.pdf).

    Since its launch, SBCFBL has helped more than half a dozen participants secure roles with NBA teams and has raised over $10,000 for charitable causes, serving as both a professional development platform and a vehicle for positive community impact.
    """)

    st.divider()
    st.subheader("SBCFBL Pre-Launch")
    st.markdown("""
    During the SBCFBL's formation, McCade Pearson led the development of all franchise identities. This process included the creation of 30 distinct and original brands, each with a unique location, area-appropriate team name, and customized color scheme. In 2022, this branding effort was further expanded to include original team logos for every franchise.

    All 30 organizations are based in the United States or Vancouver. To date, the only franchise to undergo rebranding is the San Diego Wave, following the introduction of an NWSL expansion team with the same name.
    """)

    st.divider()
    st.subheader("SBCFBL Initial Roster Construction")
    st.markdown("""
    To initialize rosters, SBCFBL conducted a 30-team slow blind auction over the course of multiple 'days'. Each organization began with a clean salary cap sheet, along with access to the full Mid-Level Exception (MLE) and Bi-Annual Exception (BAE) in Year 1 to facilitate roster construction and competitive balance.

    To ensure a realistic distribution of contract lengths across the SBCFBL, contract values were permitted to differ from real-world figures, while contract durations were aligned with each player’s actual NBA contract length at the time. Following a series of randomized draws and strategic bidding rounds, all 30 team rosters were completed and the SBCFBL officially launched.
    """)

    st.divider()
    st.subheader("SBCFBL Scoring System")
    st.markdown("""
    The SBCFBL scoring system is modeled after the structure of the United States Electoral College. Rather than states, the SBCFBL allocates weighted values to traditional basketball performance categories that most strongly correlate with winning NBA games—beyond points alone.

    Each category contributes a fixed number of “votes,” with higher-impact metrics carrying greater weight.
    - **Points**: 61  
    - **Assists**: 41  
    - **True Shooting Percentage**: 41  
    - **Blocks**: 31  
    - **Defensive Rebounds**: 31  
    - **Offensive Rebounds**: 31  
    - **Plus-Minus**: 31  
    - **Steals**: 31  
    - **Three-Point Percentage**: 31  
    - **Two-Point Percentage**: 31  
    - **Free Throw Percentage**: 21  
    - **Turnovers***: -21
    - **Minutes Played**: 11  

    In total, **413 points** are available in each matchup, with **207 points required to win**. The inclusion of an additional digit in each category allows a tie to be resolved by awarding the win to the team that captures the most individual categories. In the rare event of a 206.5–206.5 tie, the win is awarded to the home team.

    To be eligible to win the four efficiency categories, teams must meet the following minimum thresholds: **10 field goal attempts (FGA)**, **10 three-point attempts (3PA)**, and **5 free throw attempts (FTA)**.

    This nontraditional scoring system expands strategic flexibility and encourages sophisticated analytical decision-making, creating a more dynamic and engaging competitive environment than standard fantasy formats.

    \**For Turnovers, the team with the lower total is awarded the category.*
    """)

    st.divider()
    st.subheader("SBCFBL Roster Construction")
    st.markdown("""
    To balance the need for a waiver wire, the SBCFBL employs unique roster rules. Each organization must maintain a **minimum of 12 players** and may carry **up to 14 players** during the season. Instead of two-way contracts, each organization has access to **three IR slots**. During the offseason, rosters may expand to a straight **17 players**.  

    The SBCFBL also accommodates **overseas players**. To qualify, a player must be drafted by the SBCFBL and assigned 'overseas' during the summer prior to the season, locking in their status on opening night. These players may remain overseas for the duration of their rookie contract. This system allows organizations to retain second-round draft picks in situations where a standard roster would not have space for them.

    On a day-to-day basis, each SBCFBL organization maintains roster spots for the following positions:

    - **Point Guard (PG)**  
    - **Shooting Guard (SG)**  
    - **Small Forward (SF)**  
    - **Power Forward (PF)**  
    - **Center (C)**  
    - **Three Flex (FLX)** 
    - **Six Bench**

    Player position eligibility is determined by **Fantrax** each season. Organizations may request the addition of a new position for a player within **two weeks after the season begins**. The commissioner reviews these requests using independent sources and makes the final decision.
    """)

    st.divider()
    st.subheader("SBCFBL Season Structure")
    st.markdown("""
    The SBCFBL consists of 30 organizations organized into six divisions across two conferences. The regular season schedule is designed to emulate the length and intensity of the NBA. Following minor adjustments due to COVID-shortened seasons, the SBCFBL now plays a **72-game schedule**, consisting of a **triple round-robin for 42 intraconference games** and a **double round-robin for 30 interconference games** per organization, spread over **36 periods**. Each period features two games per organization played over a 3–4 day stretch.

    The playoffs closely mirror the NBA’s format, beginning with **two rounds of three-day play-in games**, followed by **four rounds of seven-day playoff series**, ultimately producing a single, undisputed SBCFBL champion who hoists the Larry Coon Trophy.

    With the addition of the NBA Cup in 2023, the SBCFBL added a cup as well. organizations play four games in the five periods leading up to a quarterfinal, semfinal, and championship matchup that takes place over the NBA Cup Final. While NBA Cup Final games obviously don't count, they do in only our SBCFBL Cup Championship for entertainment purposes. None of the SBCFBL Cup games count towards our regular season standings due to the complexity of folding them into the regular season schedule. 
    """)

    st.divider()
    st.subheader("SBCFBL Financial Structure")
    st.markdown("""
    The SBCFBL initially launched using a **2,000,000:1 scale** relative to the NBA, meaning a player with a \$10,000,000 salary would cost an owner $5 in the league. As the NBA salary cap increased, the league adjusted to a **3,000,000:1 scale** for the 2025–26 season to keep entry fees accessible while maintaining realistic roster management. Currently the formula used to determine the ratio for the year is to take the NBA's Salary Cap, divide by 60,000,000 and raise the quotient to the nearest integer before multiplying by 1,000,000. The league also enforces a **luxury tax** consistent with the NBA’s structure.

    Entry fees collected for each organization’s base roster are pooled into a league fund. These funds are first allocated to cover operational expenses, including **Fantrax fees** and the purchase of the **Larry Coon Trophy**. After these costs, remaining funds are distributed to successful organizations as follows:

    - **Champion**: 1/2 of the remaining pool  
    - **Runner-up**: 1/6 of the remaining pool  
    - **Conference Finalists (2 organizations)**: 1/12 each of the remaining poool
    - **Conference Semifinalists (4 organizations)**: 1/24 each each of the remaining pool

    In addition to entry fees, the SBCFBL collects **luxury tax payments**. During the league’s first five years, the full luxury tax pool was awarded to the league champion to donate to a charity of their choice. This approach both supported charitable causes and limited organizations’ ability to recoup luxury tax payments to fund additional championships.  

    As of the 2025–26 season, **50\% of the luxury tax pool continues to be allocated to charitable causes**, while the remaining 50\% is redistributed evenly among organizations that did not exceed the luxury tax threshold.

     **SBCFBL Cup** carries an entry fee of **\$3** per organization. The winner of the Cup receives **\$75**, while the runner-up is awarded **\$15**.
    """)

    st.divider()
    st.subheader("SBCFBL Free Agency")
    st.markdown("""
    The SBCFBL Free Agency moratorium spans **seven “days”**, each lasting 48 hours, concluding on **July 1, 3, 5, 7, 9, 11, and 13**. During this period, organizations place bids through a **Qualtrics survey**, with a maximum of **20 bids per organization per day**.

    After each day, **signings are announced**, along with an updated list of free agents showing the number of bids received and the current highest bid for each player.  

    Players are released in **three tiers** based on their previous season’s salary. A player signs after either receiving **five bids** or having at least one bid for **two consecutive days** (signing on the third day). Players sign for the **highest year-one salary bid**, and organizations determine contract length **as part of their bid**, not after securing the signing.  

    All offseason contracts in the SBCFBL are **fully guaranteed**. **Player options** are not permitted, as allowing them would require every signing to include one. Similarly, **team options** are disallowed outside of rookie contracts, ensuring clarity and consistency in all agreements.
    
    Any players with remaining bids sign on the **seventh day**, marking the end of the moratorium.

    **Restricted free agent signings** have just under one day for the incumbent organization to match a bid. **Sign-and-trade deals** are permitted, provided the transaction is agreed upon by the conclusion of the moratorium.

    In the event of multiple organizations submitting identical bids for a player, the incumbent organization has a **50\% chance** to retain the player, while the remaining organizations split the other 50%. For **supermax-eligible players**, if the incumbent organization matches the supermax amount, they have a **75\% chance** to retain the player.

    This 48-hour bidding process continues throughout free agency, but activity generally slows significantly after the moratorium concludes. Once the SBCFBL season begins, **contracts become non-guaranteed**, and organizations may only execute signings on the **first day of a matchup**.
    """)

    st.divider()
    st.subheader("SBCFBL Draft")
    st.markdown("""
    The SBCFBL Draft follows the same structure as the NBA Draft, including **lottery procedures and tiebreakers**. Rather than using a traditional countdown timer for each pick, the draft operates on **scheduled timeslots**. For example, the **first overall pick** always occurs between **10:00 a.m. and 10:30 a.m. EDT** on the Saturday following the NBA Draft, with the **second pick** due at **11:00 a.m. EDT**, and so on.

    If all organizations submit their picks early, the next organization may proceed immediately. Should a team **miss their designated timeslot**, multiple organizations may be placed **on the clock simultaneously**. Any organization that is **over two hours late** will have their pick **autodrafted**, typically receiving the highest remaining NBA draft pick (e.g., the first pick would be autodrafted at 12:30 p.m. EDT, likely selecting the 5th overall player).

    The **second round** follows the same timeslot framework on **Sunday**, maintaining consistency and pace throughout the draft.
    """)

    st.divider()
    st.subheader("SBCFBL Trade Deadline")
    st.markdown("""
    The SBCFBL Trade Deadline occurs 24 hours after the NBA Trade Deadline, typically on Friday at 3:00 PM EST. As with all trades, a trade must be formally presented and agreed upon in a “call” (i.e., a private Discord group chat) involving all parties. On trade deadline day, the group chat between the involved parties and McCade must be initiated before the official deadline.

    At 3:00 PM, McCade will begin processing trades. Teams may continue negotiations and finalize details up until McCade addresses the trade call. If any issues arise, the trade will be placed at the back of the queue, and corrections can be made until McCade returns to it.

    The trade market officially closes once McCade has updated all trades, which may occur within minutes or several hours.
    """)

    st.divider()
    st.subheader("SBCFBL Other Information")
    st.markdown("""
    All other SBCFBL operations adhere as closely as possible to the **NBA Collective Bargaining Agreement (CBA)**, including, but not limited to, **salary cap rules, trade regulations, exceptions, and deadlines**. Most SBCFBL deadlines are set on a **24-hour delay** relative to the NBA, including the **waive-and-stretch deadline, player guarantee date, offseason signing and trade restrictions,** and the **trade deadline**.

    This document is intended as a **quick-reference guide** and is not an exhaustive rulebook. Its purpose is to provide key information and highlight why the SBCFBL is considered **the premier fantasy basketball experience**.
    """)
    '''

if main_page == "Data Checks":
    picture_check = data_picture_check(df, pics)
    roster_n_check = data_roster_check(df)
    missing_salary_check = data_missing_salary_check(df)
    hard_cap_check_df = hard_cap_check(df, base_cap)
    stepien_check_df = stepien_data_check(dp)
    missing_fantrax = fantrax_players_check(df, ft_players, ft_roster)
    cap_sheet_to_fantrax_df = fantrax_roster_check(df, ft_players, ft_roster)
    positional_check_df = fantrax_positional_check(df, ft_players, ft_roster)

    check_items = [
        ("Pictures", "Players missing image links or mapped headshots.", picture_check),
        ("Roster Count", "Organizations outside expected roster-size rules.", roster_n_check),
        ("Missing Salary Info", "Cap sheet rows missing salary or contract fields.", missing_salary_check),
        ("Hard Cap Broken", "Teams that appear to be over a hard-cap limit.", hard_cap_check_df),
        ("Stepien Rule Broken", "Draft assets that may violate Stepien protections.", stepien_check_df),
        ("Cap Sheet To Fantrax Translation", "Players that do not translate cleanly into Fantrax player data.", missing_fantrax),
        ("Cap Sheet To Fantrax Roster", "Roster mismatches between the cap sheet and Fantrax.", cap_sheet_to_fantrax_df),
        ("Fantrax Positional Check", "Position eligibility mismatches that need manual review.", positional_check_df),
    ]
    issue_count = sum(0 if table is None else table.shape[0] for _, _, table in check_items)
    clear_count = sum(1 for _, _, table in check_items if table is None or table.shape[0] == 0)

    render_html(f"""
        <div class="sbc-draft-hero sbc-league-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{league_logo_html}" alt="SBC Fantasy Basketball League logo">
                <div>
                    <div class="sbc-draft-eyebrow">Integrity Desk</div>
                    <div class="sbc-draft-heading">Data Checks</div>
                    <div class="sbc-draft-subcopy">A clean command center for roster, salary, draft, image, and Fantrax validation issues before they become real app problems.</div>
                </div>
            </div>
        </div>
    """)

    status_cols = st.columns(3)
    with status_cols[0]:
        render_about_feature("Checks Run", "Automated validations across the league data model.", len(check_items), "blue")
    with status_cols[1]:
        render_about_feature("Checks Clear", "Validation groups with no current rows to review.", clear_count, "green")
    with status_cols[2]:
        render_about_feature("Open Issues", "Total rows currently returned by the data checks.", issue_count, "red" if issue_count else "green")

    render_html("""
        <div class="sbc-awards-section-head">
            <span>Review Queue</span>
            <em>Cards stay compact when clean and open into the source table when a check returns rows.</em>
        </div>
    """)
    for idx in range(0, len(check_items), 2):
        cols = st.columns(2)
        for col, (title, description, table) in zip(cols, check_items[idx:idx + 2]):
            with col:
                render_check_card(title, description, table)
