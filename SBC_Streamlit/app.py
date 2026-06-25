#import os
#os.chdir("SBC_Streamlit")

import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium
import pandas as pd
import altair as alt
import re as re
import json
import math
from datetime import datetime, date, time
from html import escape
from textwrap import dedent
from zoneinfo import ZoneInfo
from functions import get_data, get_pictures, active_players, style_salaries, overseas_players, free_agent_players, dead_players, draft_retired_players, active_player_n, inactive_player_n, get_exceptions, exception_table, get_cap_total, get_tax_total, get_base_cap, team_hard_cap, team_hard_cap_n, base_fee, amount_paid, net_fee, luxury_fee, trade_restrictions, active_players_all, inactive_players_all, dead_players_all, draft_rights_all, retired_all, all_free_agents, trade_restrictions_all, overall_cap_table, unit_payout, tax_payout_champ, tax_payout_split, style_overall_cap, get_draft_picks, full_draft_picks, swap_draft_picks, split_draft_picks, locked_draft_picks, original_draft_picks, touched_draft_picks, all_full_draft_picks, all_swap_draft_picks, all_split_draft_picks, all_locked_draft_picks, data_picture_check, data_roster_check, tradeable_players_in, tradeable_players_out, tradeable_picks_in, tradeable_picks_out, players_out_table, players_in_table, picks_out_table, picks_in_table, net_players_check, no_cash, tpe_st_check, under_100_percent_check, no_bae_mle_check, stepien_check, tradeable_exceptions_in, tradeable_exceptions_out, exceptions_in_table, exceptions_out_table, data_missing_salary_check, hard_cap_check, stepien_data_check, get_fantrax_roster, get_fantrax_players, fantrax_players_check, fantrax_roster_check, fantrax_positional_check, current_draft, get_standings, get_draft_history, past_draft, lottery_table, get_matchup_stats, format_live_stats_df, team_stats_line_chart, current_matchup_period, team_with_ranks, matchup_scoreboard, get_all_time_schedule, get_opponents, get_all_time_team_stats, get_all_time_rosters, get_award_history, get_single_award, get_team_award_history, get_team_award, get_all_stars_award, get_short_term_awards, render_scorebug, get_weekly_scores_df, get_standings_table, get_team_schedule, plot_team_flights, get_team_mileage
# no_aggregation_check, salary_trade_check, tpe_check, bae_mle_check, player_agg_check, create_tpe_check, new_trade_rest_check, old_team_check, team_with_ranks
from data import team_info, type_colors, current_salary_cap, current_luxury_tax, current_apron_1, current_apron_2, current_year, columns_order, year_offset, max_cash, period, stat_to_scipId

def render_html(markup):
    markup = dedent(str(markup)).strip()
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)

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


def load_optional_data(label, loader):
    try:
        return loader()
    except Exception as exc:
        st.warning(f"{label} could not be loaded right now: {exc}")
        return pd.DataFrame()


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


def current_period_index(options):
    try:
        current_value = int(current_matchup)
    except (TypeError, ValueError):
        current_value = options[-1]
    return options.index(min(current_value, options[-1]))


df = load_required_data("Cap sheet data", get_data)
pics = load_required_data("Player pictures", get_pictures)
exceptions = load_required_data("Exceptions", get_exceptions)
base_cap = load_required_data("Base cap", get_base_cap)
dp = load_required_data("Draft picks", get_draft_picks)
ft_roster = load_optional_data("Fantrax rosters", lambda: get_fantrax_roster(current_year, period))
ft_players = load_optional_data("Fantrax players", get_fantrax_players)
standings = load_optional_data("Standings", get_standings)
dh = load_optional_data("Draft history", get_draft_history)
all_time_team_stats = load_optional_data("All-time team stats", get_all_time_team_stats)
all_time_rosters = load_optional_data("All-time rosters", get_all_time_rosters)
all_time_schedule = load_optional_data("All-time schedule", get_all_time_schedule)
current_matchup = load_optional_data("Current matchup period", current_matchup_period)
award_history = load_optional_data("Award history", get_award_history)
team_award_history = load_optional_data("Team award history", get_team_award_history)

all_time_schedule = ensure_columns(all_time_schedule, ["Year", "Period", "Type", "Round", "TeamA", "TeamB", "TeamAScore", "TeamBScore", "Game_ID"])
standings = ensure_columns(standings, ["Year", "Period", "Team", "Record", "ConfRecord", "DivRecord", "GSRecord", "Playoff Seed", "IST Seed"])
ft_players = ensure_columns(ft_players, ["name", "fantraxId"])
all_time_rosters = ensure_columns(all_time_rosters, ["Year", "period", "id", "team_name"])
award_history = ensure_columns(award_history, ["Award", "Year", "Winner"])
team_award_history = ensure_columns(team_award_history, ["Award", "Year", "Winner"])

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
            elif col in image_columns and str(value).strip():
                url = escape(str(value), quote=True)
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
    if value is None or value == "":
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
            elif col in image_columns and str(value).strip():
                url = escape(str(value), quote=True)
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
                important = (col == "Apron 1 Space" and hard_cap == "First Apron") or (col == "Apron 2 Space" and hard_cap == "Second Apron")
                formatted = f"${numeric:,.2f}" if col in cents_cols else format_money(value)
                important_class = " sbc-overview-important-money" if important else ""
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
        card_html.append(f"""
            <div class="sbc-payout-card">
                <div class="sbc-payout-label">{escape(str(label))}</div>
                <div class="sbc-payout-value">{escape(str(format_money(value)))}</div>
                <div class="sbc-payout-note">{escape(str(note))}</div>
            </div>
        """)
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
        row_color = team_color_for_name(slot_team) if slot_team in team_info else ""
        row_style = f' style="--draft-row-color:{escape(str(row_color), quote=True)};"' if row_color else ""
        rows.append(f"""
            <tr{row_style}>
                <td class="sbc-draft-pick-no"><span>{escape(str(row.get("Pick", "")))}</span></td>
                <td class="sbc-draft-team-cell sbc-draft-slot-cell">{render_draft_team_wordmark(slot_team, include_nickname=True)}</td>
                <td class="sbc-draft-player-cell sbc-draft-player-pending">
                    <img src="{DRAFT_SILHOUETTE}" alt="">
                    <strong>{escape(str(row.get("Time Due (ET)", "")))} (ET)</strong>
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


def current_draft_from_history(draft_history, round_name):
    expected = ["Pick", "Slot", "Team", "Time Due (ET)"]
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
    table["Slot"] = table["Team"].astype(str).str.strip()
    table["Team"] = table["Slot"]
    return table[["Pick", "Slot", "Team", "Time Due (ET)"]]


def draft_clock_picks(round_df, draft_date):
    if round_df is None or round_df.empty:
        return None, None, "Board not loaded"
    now_et = datetime.now(ZoneInfo("America/New_York"))
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
    clean_df = round_df.reset_index(drop=True)
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


def render_draft_clock_card(row, label, draft_date):
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


def render_live_draft_room_header(round_1_df, round_2_df):
    round_1_date = date(2026, 6, 27)
    round_2_date = date(2026, 6, 28)
    now_et = datetime.now(ZoneInfo("America/New_York"))
    active_df = round_2_df if now_et.date() >= round_2_date else round_1_df
    active_date = round_2_date if now_et.date() >= round_2_date else round_1_date
    active_row, deck_row, status = draft_clock_picks(active_df, active_date)
    render_html(f"""
        <section class="sbc-live-draft-room">
            <div>
                <div class="sbc-live-draft-kicker">Live Draft Room</div>
                <div class="sbc-live-draft-title">2026 SBCFBL Draft</div>
                <div class="sbc-live-draft-dates">Round 1: Saturday, June 27th / Round 2: Sunday, June 28th</div>
            </div>
            <div class="sbc-live-draft-cards">
                {render_draft_clock_card(active_row, status, active_date)}
                {render_draft_clock_card(deck_row, "On deck", active_date)}
            </div>
        </section>
        """)


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
    if selected_category in ["TS%", "2PT%", "3PT%", "FT%"]:
        plot_df["PlotValue"] = plot_df[selected_category] * 100
        value_format = ".1f"
    else:
        plot_df["PlotValue"] = plot_df[selected_category]
        value_format = ".2f"
    team_points = plot_df[plot_df["Series"] == selected_team].copy()
    selected_period_df = pd.DataFrame({"Period": [selected_period]})
    color_domain = ["League Median"] + opponents + [selected_team]
    color_range = ["#9ca3af"] + [live_chart_color(opponent, "#a3aab5") for opponent in opponents] + [team_color]

    base = alt.Chart(plot_df).encode(
        x=alt.X(
            "Period:O",
            title="Matchup Period",
            axis=alt.Axis(labelAngle=0, labelFontSize=11, titleFontSize=12, titlePadding=10, grid=False)),
        y=alt.Y(
            "PlotValue:Q",
            title=selected_category,
            scale=alt.Scale(zero=False),
            axis=alt.Axis(labelFontSize=11, titleFontSize=12, titlePadding=10, gridOpacity=0.24)),
        tooltip=[
            alt.Tooltip("Series:N", title="Series"),
            alt.Tooltip("Period:O", title="Period"),
            alt.Tooltip("PlotValue:Q", title=selected_category, format=value_format)])

    selected_band = (
        alt.Chart(selected_period_df)
        .mark_rect(color=team_color, opacity=0.10)
        .encode(x=alt.X("Period:O", title=None)))
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
            size=alt.condition(alt.datum.Period == selected_period, alt.value(150), alt.value(54)),
            strokeWidth=alt.condition(alt.datum.Period == selected_period, alt.value(2.4), alt.value(1.2))))
    points = (
        alt.Chart(team_points)
        .mark_circle(size=115, stroke="#ffffff", strokeWidth=1.8)
        .encode(
            x="Period:O",
            y="PlotValue:Q",
            color=alt.value(team_color),
            tooltip=[
                alt.Tooltip("Period:O", title="Period"),
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


def render_schedule_table(schedule_df, selected_team):
    if schedule_df is None or schedule_df.shape[0] == 0:
        render_html('<div class="sbc-empty-state">No schedule records are available for this selection.</div>')
        return

    type_order = {"Regular Season": 0, "In-Season Tournament": 1, "Play-In": 2, "Playoffs": 3}
    table_df = schedule_df.copy()
    table_df["TypeOrder"] = table_df["Type"].map(type_order).fillna(9)
    table_df = table_df.sort_values(["TypeOrder", "Period", "Game_ID"])

    body_rows = []
    current_type = None
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
            body_rows.append(f'<tr class="sbc-schedule-group-row"><td colspan="3"><span>{escape(type_text)}</span></td></tr>')
        body_rows.append(dedent(f"""
        <tr class="sbc-schedule-row sbc-schedule-{result_class}" style="--sbc-opponent-color:{escape(str(opponent_color), quote=True)};">
            <td class="sbc-schedule-period"><span>P{escape(str(row.get("Period", "")))}</span></td>
            <td class="sbc-schedule-opponent">
                {logo_html}
                <div>
                    <strong>{escape(str(venue_mark))} {escape(str(opponent))}</strong>
                </div>
            </td>
            <td class="sbc-schedule-score"><strong>{escape(score_text)}</strong><em>{escape(result)}</em></td>
        </tr>
        """))

    render_html(f"""
    <div class="sbc-schedule-table-wrap">
        <table class="sbc-schedule-table">
            <thead>
                <tr>
                    <th>Period</th>
                    <th>Opponent</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>{''.join(body_rows)}</tbody>
        </table>
    </div>
    """)


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
                    "note": f"P{row.get('Period')}: {selected_team} to {destination_team}",
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
        non_winners = []
        for table in conference_groups.values():
            if table.shape[0] > 1:
                non_winners.append(table.iloc[1:].copy())
        if non_winners:
            wildcard_pool = pd.concat(non_winners, ignore_index=True)
            ranked_wildcards = []
            for _, group in wildcard_pool.sort_values(["WinPctRaw", "wins", "PointDiff", "Team"], ascending=[False, False, False, True]).groupby(["wins", "losses"], sort=False):
                tied = group["Team"].astype(str).tolist()
                common_games = tied_team_games(played_games, tied)
                group = group.copy()
                group["_h2h"] = group["Team"].map(lambda team: record_pct_for_games(str(team), common_games))
                ranked_wildcards.append(group.sort_values(["_h2h", "PointDiff", "Team"], ascending=[False, False, True]))
            wildcard = pd.concat(ranked_wildcards, ignore_index=True).iloc[0]["Team"]
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
    groups = []
    for type_name in ["Regular Season", "In-Season Tournament", "Play-In", "Playoffs"]:
        group_df = scores_df[scores_df["Type"].astype(str) == type_name].copy()
        if group_df.empty:
            continue
        group_df = group_df.sort_values(["Round", "TeamB_Nickname", "TeamA_Nickname"], na_position="last")
        cards = []
        for _, row in group_df.iterrows():
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
            cards.append(f"""
                <article class="sbc-score-card">
                    <div class="sbc-score-card-top">
                        <span>{escape(str(round_label))}</span>
                        <em>P{escape(str(row.get("Period", "")))}</em>
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
        groups.append(f"""
            <section class="sbc-score-group">
                <div class="sbc-score-group-head">
                    <span>{escape(type_labels.get(type_name, type_name))}</span>
                    <em>{group_df.shape[0]} matchup{'s' if group_df.shape[0] != 1 else ''}</em>
                </div>
                <div class="sbc-score-grid">{''.join(cards)}</div>
            </section>
        """)

    render_html(f'<div class="sbc-scoreboard-wrap">{"".join(groups)}</div>')


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
        <section class="sbc-standings-panel">
            <div class="sbc-standings-head">
                <span>{escape(conference)} Conference</span>
                <em>Through Period {escape(str(selected_period))}</em>
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
            <section class="sbc-standings-panel">
                <div class="sbc-standings-head">
                    <span>{conference} Groups</span>
                    <em>Through Period {escape(str(selected_period))}</em>
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

    .block-container {{
        max-width: 1500px;
        padding-top: 5.25rem;
        padding-bottom: 3rem;
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

    [data-testid="stSidebar"] {{
        display: none;
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

    .sbc-schedule-table th:nth-child(1) {{ width: 5.5rem; }}
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
        width: 3.1rem;
        height: 2.1rem;
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

    .sbc-standings-layout {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.9rem;
        margin: 0.45rem 0 1.1rem;
    }}

    .sbc-standings-panel {{
        overflow: hidden;
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 22%, rgba(23, 32, 42, 0.12));
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 14px 34px rgba(18, 25, 38, 0.075);
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
        background: #111827;
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
        background: #f7f9fc;
        border-bottom: 1px solid rgba(23, 32, 42, 0.1);
        color: var(--sbc-ink);
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
        background: #111827 !important;
        color: #ffffff !important;
        font-size: 0.82rem !important;
        font-weight: 950 !important;
        letter-spacing: 0.08em;
        padding: 0.52rem 0.68rem !important;
        text-align: left !important;
        text-transform: uppercase;
    }}

    .sbc-standings-playoff td {{
        background: color-mix(in srgb, #3f8f55 16%, #ffffff);
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
        background: #ffffff;
        border: 1px solid rgba(23, 32, 42, 0.14);
        box-shadow: 0 4px 10px rgba(18, 25, 38, 0.08);
        color: var(--sbc-ink);
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
        font-family: "Poppins", "Segoe UI", sans-serif;
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

    .sbc-live-draft-room {{
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

    .sbc-award-card,
    .sbc-award-team-card {{
        overflow: hidden;
        margin-bottom: 0.85rem;
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
        background: rgba(255,255,255,0.78);
        border: 1px solid rgba(23, 32, 42, 0.08);
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
        min-height: 7rem;
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

    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] * {{
        color: #4b5563 !important;
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

    [data-testid="stDataFrame"] {{
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--sbc-border);
        box-shadow: 0 12px 32px rgba(18, 25, 38, 0.07);
    }}

    div[data-testid="stForm"] {{
        border: 1px solid var(--sbc-border);
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 12px 32px rgba(18, 25, 38, 0.07);
        padding: 1rem;
    }}

    .stButton > button,
    [data-testid="stFormSubmitButton"] button {{
        border-radius: 8px;
        border: 1px solid color-mix(in srgb, var(--sbc-team-primary) 82%, #000 18%);
        background: var(--sbc-team-primary);
        color: var(--sbc-team-text);
        font-weight: 850;
        box-shadow: 0 10px 26px rgba(18, 25, 38, 0.12);
    }}

    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] button:hover {{
        border-color: var(--sbc-team-secondary);
        filter: brightness(1.03);
    }}

    .stAlert {{
        border-radius: 8px;
    }}

    img {{
        image-rendering: auto;
    }}

    @media (max-width: 850px) {{
        .block-container {{
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

team_hub_tab, league_hub_tab, tab9, tab10, tab11, tab12, tab13 = st.tabs([
    "🏢 Team Hub",
    "🏟️ League Hub",
    "🔁 Trade Machine",
    "📚 Drafts",
    "⭐ Awards",
    "📖 About",
    "✅ Data Checks"])

components.html("""
<script>
try {
  const doc = window.parent.document;
  function syncSbcMainTab() {
    const tabs = Array.from(doc.querySelectorAll('[role="tab"]'));
    const teamTab = tabs.find(tab => (tab.textContent || '').includes('Team Hub'));
    const isTeam = teamTab && teamTab.getAttribute('aria-selected') === 'true';
    doc.documentElement.dataset.sbcMainTab = isTeam ? 'team' : 'league';
  }
  syncSbcMainTab();
  new MutationObserver(syncSbcMainTab).observe(doc.body, {
    subtree: true,
    attributes: true,
    attributeFilter: ['aria-selected']
  });
} catch (error) {
  // Keep the league-branded fallback if parent DOM access is unavailable.
}
</script>
""", height=0)

components.html("""
<script>
try {
  const doc = window.parent.document;
  function formatCountdown(ms) {
    if (ms <= 0) return 'Due now';
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')} left til pick`;
  }
  function syncDraftCountdowns() {
    doc.querySelectorAll('.sbc-countdown[data-target]').forEach((node) => {
      const target = new Date(node.dataset.target);
      if (!Number.isNaN(target.getTime())) {
        node.textContent = formatCountdown(target.getTime() - Date.now());
      }
    });
  }
  syncDraftCountdowns();
  setInterval(syncDraftCountdowns, 1000);
} catch (error) {}
</script>
""", height=0)

with team_hub_tab:
    picker_col, _ = st.columns([1.15, 3.85], vertical_alignment="bottom")
    with picker_col:
        render_html('<div class="sbc-picker-eyebrow">Team View</div>')
        st.selectbox("Choose your team", Teams, key="_sbc_selected_team")

    tab1, tab2, tab3, tab4 = st.tabs([
        f"💰 {SelectedTeam} Cap",
        f"🏀 {SelectedTeam} Picks",
        f"📊 {SelectedTeam} Live",
        f"🗓️ {SelectedTeam} Schedule"])

with league_hub_tab:
    tab8, tab5, standings_tab, tab6, tab7 = st.tabs([
        "🏆 Overview",
        "🏟️ Scoreboard",
        "📈 Standings",
        "👥 Players",
        "🎯 Draft Picks"])

with tab1:
    _legacy_tab1 = r'''
    st.subheader(f"{SelectedTeam} Cap Sheet for {current_year-1}-{str(current_year)[-2:]} Season")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label = "Salary Cap", value = current_salary_cap, delta = "10.0%", delta_color = "normal", help = "Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border = True, format = "dollar")
    
    with col2:
        st.metric(label = "Luxury Tax", value = current_luxury_tax, delta = "10.0%", delta_color = "normal", help = "Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border = True, format = "dollar")
    
    with col3:
        st.metric(label = "Apron #1", value = current_apron_1, delta = "10.0%", delta_color = "normal", help = "Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border = True, format = "dollar")
    
    with col4:
        st.metric(label = "Apron #2", value = current_apron_2, delta = "10.0%", delta_color = "normal", help = "Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade–related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border = True, format = "dollar")

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
            st.dataframe(free_agent_player_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + [str(current_year+ year_offset)], column_config={" ": st.column_config.ImageColumn(" ")})

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
        st.metric(label="Salary Cap", value=current_salary_cap, delta="10.0%", delta_color="normal", help="Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border=True, format="dollar")
    with col2:
        st.metric(label="Luxury Tax", value=current_luxury_tax, delta="10.0%", delta_color="normal", help="Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border=True, format="dollar")
    with col3:
        st.metric(label="Apron #1", value=current_apron_1, delta="10.0%", delta_color="normal", help="Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border=True, format="dollar")
    with col4:
        st.metric(label="Apron #2", value=current_apron_2, delta="10.0%", delta_color="normal", help="Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade-related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border=True, format="dollar")

    render_html('<div class="sbc-section-label">Team Snapshot</div>')
    snap1, snap2, snap3 = st.columns([1, 1, 2])
    with snap1:
        st.metric(label="Cap Total", value=cap_total, delta=cap_total-current_salary_cap, delta_color="inverse", help="The first number shows total team salary, including all active and inactive player salaries, cap holds for unrenounced free agents, incomplete roster charges, and all exceptions (Mid-Level, Bi-Annual, Disabled Player, and Trade). The second number shows how much room remains relative to the Salary Cap.", border=True, format="dollar")
    with snap2:
        st.metric(label="Tax Total", value=tax_total, delta=tax_total-current_luxury_tax, delta_color="inverse", help="The first number shows total team salary against the luxury tax, including all active and inactive player salaries and incomplete roster charges. Unlike the real NBA, rookie and second-year undrafted fees are not included. The second number shows remaining space relative to the Luxury Tax.", border=True, format="dollar")
    with snap3:
        st.metric(label="Apron Space", value=team_hard_cap(base_cap, SelectedTeam), delta=team_hard_cap_n(df, SelectedTeam, base_cap), help="The first value indicates whether the team is uncapped, capped at the first apron, or capped at the second apron while the second value shows how far the team is from the applicable cap.", border=True, format="dollar")

    snap4, snap5, snap6 = st.columns(3)
    with snap4:
        st.metric(label="Players", value=active_count, delta=inactive_count, delta_color="off", help="The first number shows active roster players (up to 14, plus up to 3 IR). Teams must carry at least 12 active players, or face penalties after 14 days. The second number represents non-active players, including overseas players, draft rights, retired, and waived players and there is no limit. To qualify as overseas, a drafted player must have spent their entire SBC career abroad, with status locking on opening night.", border=True, format="plain", delta_arrow="off")
    with snap5:
        st.metric(label="Entry Fee", value=base_fee(df, SelectedTeam, base_cap), delta=luxury_fee(df, SelectedTeam, base_cap), delta_color="inverse", help="The SBCFBL uses a 3,000,000-1 scale. The first number is the base entry fee, calculated from the Tax Total plus a $3.00 In-Season Tournament fee. The second number shows the Luxury Tax penalty for the season, scaled as a payable fee.", border=True, format="dollar")
    with snap6:
        st.metric(label="Balance", value=net_fee(df, SelectedTeam, base_cap), delta=amount_paid(base_cap, SelectedTeam), delta_color="normal", help="The first number shows current total owed for the season, including base payment, In-Season Tournament fee, tax penalties, winnings, and tax payouts. The second number shows how much has been paid so far.", border=True, format="dollar")

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
            render_cap_table(free_agent_player_df, columns=[" ", "Player"] + [str(current_year+ year_offset)], image_columns=[" "], row_team=SelectedTeam)
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

with tab2:
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
    if False and touched_team_picks.shape[0] > 0:
        st.header("Touched Draft Picks")
        st.dataframe(touched_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})


with tab3:
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
        SelectedPeriod = st.selectbox("Period", options=period_options, index=current_period_index(period_options))
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

    render_html('<div class="sbc-section-label">Matchup Scoreboards</div>')
    if matchup_count == 0:
        selected_payload = live_row_payload(live_stats_df, SelectedTeam)
        render_live_stat_board(
            f"{SelectedTeam} Period {SelectedPeriod} Stat Profile",
            "No scheduled matchup",
            [selected_payload] if selected_payload else [],
            SelectedTeam,
            SelectedTeam)
    else:
        matchup_cols = st.columns(min(3, matchup_count))
        for idx, (matchup_type, opponent) in enumerate(matchup_sections):
            with matchup_cols[idx % len(matchup_cols)]:
                selected_payload = live_row_payload(live_stats_df, SelectedTeam)
                opponent_payload = live_row_payload(live_stats_df, opponent)
                matchup_rows = [payload for payload in [selected_payload, opponent_payload] if payload]
                matchup_home = SelectedTeam
                schedule_match = all_time_schedule[
                    (all_time_schedule["Year"] == SelectedYear)
                    & (all_time_schedule["Period"] == SelectedPeriod)
                    & (all_time_schedule["Type"] == matchup_type)
                    & (
                        ((all_time_schedule["TeamA"] == SelectedTeam) & (all_time_schedule["TeamB"] == opponent))
                        | ((all_time_schedule["TeamA"] == opponent) & (all_time_schedule["TeamB"] == SelectedTeam))
                    )
                ]
                if schedule_match.shape[0] > 0:
                    matchup_home = schedule_match.iloc[0]["TeamA"]
                render_live_stat_board(
                    f"{SelectedTeam} vs {opponent}",
                    f"{matchup_type} - Period {SelectedPeriod}",
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

with tab4:
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
    render_schedule_table(schedule_raw, SelectedTeam)
    total_miles, num_flights = calculate_team_travel_summary(SelectedTeam, SelectedScheduleYear, all_time_schedule)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Miles", value=f"{int(total_miles):,} mi", help="Total miles traveled this season including road trips and returns home.", border=True)
    with col2:
        st.metric(label="Total Flights", value=num_flights, help="Number of flights taken this season (legs with distance > 0).", border=True)
    render_team_travel_map(schedule_raw, SelectedTeam, SelectedScheduleYear)

with tab5:
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
    SelectedYear2 = st.selectbox("Select Year", options=list(range(2021, current_year+1)), index=list(range(2021, current_year+1)).index(current_year))
    period_options2 = schedule_period_options(all_time_schedule, SelectedYear2)
    SelectedPeriod2 = st.selectbox("Select Period", options=period_options2, index=current_period_index(period_options2))

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

with standings_tab:
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
    StandingsPeriod = st.selectbox("Standings Period", options=standings_period_options, index=current_period_index(standings_period_options))
    render_html('<div class="sbc-section-label">Standings Snapshot</div>')
    west_col, east_col = st.columns(2)
    with west_col:
        render_conference_standings(standings, StandingsYear, StandingsPeriod, "West")
    with east_col:
        render_conference_standings(standings, StandingsYear, StandingsPeriod, "East")
    render_ist_standings(standings, StandingsYear, StandingsPeriod)

with tab6:

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
    render_cap_table(dead_players_df, columns=["Team_logo", " ", "Player"] + columns_order, image_columns=["Team_logo", " "])

    render_html('<div class="sbc-section-label">Contract And Asset Details</div>')
    asset1, asset2 = st.columns([1.1, 0.9])
    with asset1:
        render_html('<div class="sbc-cap-eyebrow">Upcoming Free Agents</div>')
        render_cap_table(all_free_agents_df, columns=["Team_logo", " ", "Player"] + [str(current_year + year_offset)], image_columns=["Team_logo", " "])
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
            st.dataframe(all_free_agents_df, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + [str(current_year+ year_offset)], column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

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
with tab7:
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
with tab8:
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
        st.metric(label = "Salary Cap", value = current_salary_cap, delta = "10.0%", delta_color = "normal", help = "Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border = True, format = "dollar")
    
    with col2:
        st.metric(label = "Luxury Tax", value = current_luxury_tax, delta = "10.0%", delta_color = "normal", help = "Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border = True, format = "dollar")
    
    with col3:
        st.metric(label = "Apron #1", value = current_apron_1, delta = "10.0%", delta_color = "normal", help = "Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border = True, format = "dollar")
    
    with col4:
        st.metric(label = "Apron #2", value = current_apron_2, delta = "10.0%", delta_color = "normal", help = "Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade–related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border = True, format = "dollar")

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
with tab9:

    with st.form("team_selection_form"):
    
        col1, col2 = st.columns(2)
    
        with col1:
            SelectedPlayersOut = st.multiselect("Outgoing Players:", tradeable_players_out(df, SelectedTeam))
            SelectedPicksOut = st.multiselect("Outgoing Picks:", tradeable_picks_out(dp, SelectedTeam))
            SelectedExceptionOut = st.multiselect("Exceptions Used:", tradeable_exceptions_out(exceptions, SelectedTeam))
            CashOut = st.number_input(label="Cash Out:", min_value = 110000, max_value= max_cash, placeholder = "None", value = None)

        with col2:
            SelectedPlayersIn = st.multiselect("Incoming Players:", tradeable_players_in(df, SelectedTeam))
            SelectedPicksIn = st.multiselect("Incoming Picks:", tradeable_picks_in(dp, SelectedTeam))
            SelectedExceptionIn = st.multiselect("Exceptions Used:", tradeable_exceptions_in(exceptions, SelectedTeam))
            CashIn = st.number_input(label="Cash In:", min_value=110000, max_value=max_cash, placeholder = "None", value = None)

        submitted = st.form_submit_button("Submit")

    if submitted and (SelectedPicksIn or SelectedPicksOut or SelectedPlayersIn or SelectedPlayersOut):

        col1, col2 = st.columns(2)

        with col1:
            players_trade_out = players_out_table(df, pics, SelectedPlayersOut)
            if players_trade_out.shape[0] > 0:
                st.subheader("Players Going Out")
                players_trade_out = (players_trade_out.style
                    .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                    .format({c: "${:,.0f}" for c in players_trade_out.columns if re.match(r"\d{4}", c)}))
                st.dataframe(players_trade_out, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order, column_config={" ": st.column_config.ImageColumn(" ")})

            picks_trade_out = picks_out_table(dp, SelectedPicksOut)
            if picks_trade_out.shape[0] > 0:
                st.subheader("Picks Going Out")
                st.dataframe(picks_trade_out, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

            experiations_out = exceptions_out_table(exceptions, SelectedExceptionOut)
            if experiations_out.shape[0] > 0:
                st.subheader("Exceptions Being Used")
                st.dataframe(experiations_out, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

        with col2:
            players_traded_in = players_in_table(df, pics, SelectedPlayersIn)
            if players_traded_in.shape[0] > 0:
                st.subheader("Players Coming In")
                players_traded_in = (players_traded_in.style
                    .apply(lambda row: style_salaries(row, type_colors), axis=1)  
                    .format({c: "${:,.0f}" for c in players_traded_in.columns if re.match(r"\d{4}", c)}))
                st.dataframe(players_traded_in, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_order=["Team_logo", " ", "Player"] + columns_order, column_config={" ": st.column_config.ImageColumn(label="", width="small"), "Team_logo": st.column_config.ImageColumn(label="", width="small")})

            picks_trade_in = picks_in_table(dp, SelectedPicksIn)
            if picks_trade_in.shape[0] > 0:
                st.subheader("Picks Coming In")
                st.dataframe(picks_trade_in, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

            experiations_in = exceptions_in_table(exceptions, SelectedExceptionIn)
            if experiations_in.shape[0] > 0:
                st.subheader("Exceptions Being Used")
                st.dataframe(experiations_in, width = "stretch", row_height = 50, hide_index=True, placeholder="—", column_config={"Team": st.column_config.ImageColumn(label="Team", width="small")})


        st.subheader("Roster Limit")
        net_players_check(df, SelectedTeam, SelectedPlayersIn, SelectedPlayersOut)
        st.subheader("Salary Limit")
        #salary_trade_check()
        #tpe_check()
        #bae_mle_check()
        #player_agg_check()
        #create_tpe_check()
        #new_trade_rest_check()
        #old_team_check()
        st.subheader("Second Apron Checks")
        no_cash(df, SelectedPlayersIn, SelectedPlayersOut, SelectedTeam, base_cap, CashOut)
        tpe_st_check(df, SelectedPlayersIn, SelectedPlayersOut, SelectedTeam, base_cap, SelectedExceptionOut)
        #no_aggregation_check()
        st.subheader("First Apron Checks")
        no_bae_mle_check(df, SelectedPlayersIn, SelectedPlayersOut, SelectedTeam, base_cap, SelectedExceptionOut)
        under_100_percent_check(df, SelectedPlayersIn, SelectedPlayersOut, SelectedTeam, base_cap, SelectedExceptionOut)
        st.subheader("Draft Pick Check")
        #stepien_check()

with tab10:
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

    draft_years = []
    for year in [current_year, 2025, 2024, 2023, 2022, 2021]:
        if year not in draft_years:
            draft_years.append(year)
    draft_year_tabs = st.tabs([str(year) for year in draft_years])
    for draft_tab, draft_year in zip(draft_year_tabs, draft_years):
        with draft_tab:
            if draft_year == current_year:
                current_round_1 = current_draft_from_history(dh, "1st Round")
                current_round_2 = current_draft_from_history(dh, "2nd Round")
                render_live_draft_room_header(current_round_1, current_round_2)
                c1, c2 = st.columns(2)
                with c1:
                    render_current_draft_table(
                        current_round_1,
                        f"{draft_year} Round 1",
                        "1",
                        "Saturday, June 27th.")
                with c2:
                    render_current_draft_table(
                        current_round_2,
                        f"{draft_year} Round 2",
                        "2",
                        "Sunday, June 28th.")
            else:
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


def player_award_table(year, award, mode="single"):
    if mode == "allstar":
        return safe_table_call(get_all_stars_award, award_history, ft_players, all_time_rosters, pics, year, award)
    if mode == "short":
        return safe_table_call(get_short_term_awards, award_history, ft_players, all_time_rosters, pics, year, award)
    return safe_table_call(get_single_award, award_history, ft_players, all_time_rosters, pics, year, award)


def render_award_player_rows(data, compact=False):
    if data is None or data.empty:
        return '<div class="sbc-award-empty">Not awarded yet</div>'
    cards = []
    for _, row in data.iterrows():
        name = clean_pick_display(row.get("Winner", ""))
        picture = row.get("Picture_Online", "")
        logo = row.get("logo", "")
        week = clean_pick_display(row.get("Week", ""))
        week_html = f'<span class="sbc-award-week">{escape(str(week))}</span>' if week != "â€”" else ""
        logo_html = f'<img class="sbc-award-mini-logo" src="{escape(str(logo), quote=True)}" alt="Team logo" referrerpolicy="no-referrer">' if not is_blank_value(logo) else ""
        img_html = f'<img class="sbc-award-headshot" src="{escape(str(picture), quote=True)}" alt="{escape(str(name), quote=True)}">' if not is_blank_value(picture) else '<div class="sbc-award-headshot sbc-award-headshot-empty"></div>'
        cards.append(f"""
            <div class="sbc-award-player {'sbc-award-player-compact' if compact else ''}">
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


def render_team_award_card(title, award, year, tone="blue", feature=False):
    winner = team_award_winner(team_award_history, year, award)
    if winner in team_info:
        wordmark = team_info[winner].get("wordmark", "")
        mark = team_logo_name_mark(winner)
        color = team_color_for_name(winner)
        secondary = team_secondary_for_name(winner)
    else:
        wordmark = "https://pbs.twimg.com/media/HCRpyEUaQAAPORi?format=png&name=medium"
        mark = f'<span class="sbc-award-team-missing">{escape(str(winner))}</span>'
        color = LEAGUE_PRIMARY
        secondary = LEAGUE_SECONDARY
    render_html(f"""
        <section class="sbc-award-team-card sbc-award-card-{tone} {'sbc-award-team-feature' if feature else ''}" style="--award-team-color:{escape(str(color), quote=True)};--award-team-secondary:{escape(str(secondary), quote=True)};">
            <div class="sbc-award-card-top">
                <span>{escape(title)}</span>
                <em>{escape(str(year))}</em>
            </div>
            <div class="sbc-award-wordmark-wrap">
                <img class="sbc-award-wordmark" src="{escape(str(wordmark), quote=True)}" alt="{escape(str(winner), quote=True)} wordmark" referrerpolicy="no-referrer">
            </div>
            <div class="sbc-award-team-footer">{mark}</div>
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


with tab11:
    award_year_options = list(range(2021, current_year+1))
    AwardYears = st.selectbox("Select Award Year", options=award_year_options, index=award_year_options.index(current_year))
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
        render_team_award_card("SBCFBL Cup Winner", "Cup Winner", AwardYears, "green", feature=True)
        render_player_award("Cup MVP", "Cup MVP", AwardYears, tone="green")
        render_player_award("Cup-Winning Roster", "Cup Winner", AwardYears, tone="green", compact=True)

    west_col, east_col = render_awards_section("Conference & Division Crowns", "The paths through each side of the bracket.", [1, 1])
    with west_col:
        render_team_award_card("Western Conference Champion", "WC Champion", AwardYears, "blue")
        render_player_award("Western Conference MVP", "WCF MVP", AwardYears, tone="blue")
        div_cols = st.columns(3)
        with div_cols[0]:
            render_team_award_card("Pacific Champion", "Pacific Champion", AwardYears, "blue")
        with div_cols[1]:
            render_team_award_card("Northwest Champion", "Northwest Champion", AwardYears, "blue")
        with div_cols[2]:
            render_team_award_card("Southwest Champion", "Southwest Champion", AwardYears, "blue")
    with east_col:
        render_team_award_card("Eastern Conference Champion", "EC Champion", AwardYears, "red")
        render_player_award("Eastern Conference MVP", "ECF MVP", AwardYears, tone="red")
        div_cols = st.columns(3)
        with div_cols[0]:
            render_team_award_card("Central Champion", "Central Champion", AwardYears, "red")
        with div_cols[1]:
            render_team_award_card("Atlantic Champion", "Atlantic Champion", AwardYears, "red")
        with div_cols[2]:
            render_team_award_card("Southeast Champion", "Southeast Champion", AwardYears, "red")

    cols = render_awards_section("Individual Hardware", "The season's headliners and category kings.", [1, 1, 1])
    individual_awards = [
        ("Most Valuable Player", "MVP", "gold"),
        ("Clutch Player of the Year", "Clutch", "blue"),
        ("Defensive Player of the Year", "DPOY", "green"),
        ("Most Improved Player", "MIP", "blue"),
        ("Rookie of the Year", "ROY", "red"),
        ("Sixth Man of the Year", "6MOY", "green"),
    ]
    for idx, (title, award, tone) in enumerate(individual_awards):
        with cols[idx % 3]:
            render_player_award(title, award, AwardYears, tone=tone)

    team_cols = render_awards_section("All-League Teams", "The best five-man groups from the season.", [1, 1, 1])
    for col, (title, award, tone) in zip(team_cols, [("All-SBC First Team", "All-SBC 1st Team", "gold"), ("All-SBC Second Team", "All-SBC 2nd Team", "blue"), ("All-SBC Third Team", "All-SBC 3rd Team", "green")]):
        with col:
            render_player_award(title, award, AwardYears, tone=tone, compact=True)

    col1, col2 = render_awards_section("Defense, Rookies & All-Star Stage", "Special teams, regular season crown, and showcase stars.", [1, 1])
    with col1:
        render_player_award("All-Defense First Team", "All-Defense 1st Team", AwardYears, tone="green", compact=True)
        render_player_award("All-Rookie First Team", "All-Rookie 1st Team", AwardYears, tone="red", compact=True)
        render_team_award_card("Regular Season Champion", "RS Champion", AwardYears, "gold")
        render_player_award("Western Conference All-Stars", "West All-Star", AwardYears, mode="allstar", tone="blue", compact=True)
    with col2:
        render_player_award("All-Defense Second Team", "All-Defense 2nd Team", AwardYears, tone="green", compact=True)
        render_player_award("All-Rookie Second Team", "All-Rookie 2nd Team", AwardYears, tone="red", compact=True)
        render_player_award("All-Star Game MVP", "ASG MVP", AwardYears, tone="gold")
        render_player_award("Eastern Conference All-Stars", "East All-Star", AwardYears, mode="allstar", tone="red", compact=True)

    col1, col2 = render_awards_section("Monthly & Weekly Honors", "A full season of recurring winners without the spreadsheet slog.", [1, 1])
    with col1:
        render_player_award("West Player of the Month", "West POM", AwardYears, mode="short", tone="blue", compact=True)
        render_player_award("West Rookie of the Month", "West ROM", AwardYears, mode="short", tone="blue", compact=True)
        render_player_award("West Player of the Week", "West POW", AwardYears, mode="short", tone="blue", compact=True)
    with col2:
        render_player_award("East Player of the Month", "East POM", AwardYears, mode="short", tone="red", compact=True)
        render_player_award("East Rookie of the Month", "East ROM", AwardYears, mode="short", tone="red", compact=True)
        render_player_award("East Player of the Week", "East POW", AwardYears, mode="short", tone="red", compact=True)

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

with tab12:
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

    about_cols = st.columns(3)
    with about_cols[0]:
        render_about_feature(
            "Built For Front Office Reps",
            "Founded by Sports Business Classroom alumni, SBCFBL turns the NBA rulebook into a living team-building environment.",
            "2020",
            "blue",
        )
    with about_cols[1]:
        render_about_feature(
            "Thirty Original Organizations",
            "Every franchise has its own location, nickname, colors, logo, font, cap sheet, draft assets, and operating identity.",
            "30 Teams",
            "green",
        )
    with about_cols[2]:
        render_about_feature(
            "Real Stakes, Real Strategy",
            "League fees, luxury tax, prizes, charitable giving, roster rules, exceptions, deadlines, and trades all matter.",
            "$10K+ Raised",
            "gold",
        )

    render_html("""
        <div class="sbc-awards-section-head">
            <span>How The League Works</span>
            <em>The high-level rules commissioners, owners, and new members need fastest.</em>
        </div>
    """)
    rule_cols = st.columns(3)
    with rule_cols[0]:
        render_about_rule_card(
            "Roster Construction",
            [
                "12-player in-season minimum with a 14-player standard maximum.",
                "17-player offseason limit and three IR slots instead of two-way contracts.",
                "Overseas rights preserve drafted players through rookie-contract windows.",
            ],
            "blue",
        )
    with rule_cols[1]:
        render_about_rule_card(
            "Schedule And Playoffs",
            [
                "72-game regular season over 36 matchup periods.",
                "Triple round-robin inside conference and double round-robin outside it.",
                "Play-in rounds lead into four seven-day playoff series.",
            ],
            "green",
        )
    with rule_cols[2]:
        render_about_rule_card(
            "Scoring Model",
            [
                "413 available matchup points across NBA-style categories.",
                "207 points wins the matchup; category count resolves most ties.",
                "Efficiency categories require minimum attempt thresholds.",
            ],
            "gold",
        )

    finance_cols = st.columns(3)
    with finance_cols[0]:
        render_about_rule_card(
            "Cap And Fees",
            [
                "Scaled NBA salary cap economics keep rosters realistic and entry fees manageable.",
                "Luxury tax mirrors the NBA structure and affects both cost and competitive posture.",
                "Base roster funds support operations first, then prize distributions.",
            ],
            "blue",
        )
    with finance_cols[1]:
        render_about_rule_card(
            "Free Agency",
            [
                "Seven 48-hour moratorium days with Qualtrics bidding.",
                "Players sign through bid thresholds, consecutive interest, or final-day resolution.",
                "Restricted free agency, sign-and-trades, and offseason guarantees are built in.",
            ],
            "green",
        )
    with finance_cols[2]:
        render_about_rule_card(
            "Draft And Trades",
            [
                "The draft follows NBA structure, lottery logic, and scheduled timeslots.",
                "Late picks can trigger simultaneous clocks and eventual autodraft handling.",
                "Trade deadline timing follows the NBA deadline with a 24-hour SBCFBL delay.",
            ],
            "red",
        )

    render_html("""
        <div class="sbc-awards-section-head">
            <span>Why It Exists</span>
            <em>A serious sandbox for learning the tiny decisions that shape a basketball organization.</em>
        </div>
    """)
    purpose_cols = st.columns([1, 1])
    with purpose_cols[0]:
        render_about_feature(
            "Professional Development",
            "The league gives members meaningful practice with CBA mechanics, roster constraints, trade construction, draft planning, and long-term asset management.",
            "NBA-Style",
            "blue",
        )
    with purpose_cols[1]:
        render_about_feature(
            "Community Impact",
            "SBCFBL has paired competitive team building with charitable giving and a growing alumni network of members pursuing basketball roles.",
            "Community",
            "green",
        )

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

with tab13:
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
