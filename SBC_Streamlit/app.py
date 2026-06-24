#import os
#os.chdir("SBC_Streamlit")

import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import altair as alt
import re as re
from html import escape
from textwrap import dedent
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

Teams = sorted(team_info.keys())

_, top_col2 = st.columns([5, 2], vertical_alignment="bottom")
with top_col2:
    render_html('<div class="sbc-picker-eyebrow">Team View</div>')
    SelectedTeam = st.selectbox("Choose your team", Teams, index=Teams.index("Vegas"))

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

def render_cap_table(data, columns=None, image_columns=None, money_columns=None, contract_colors=True):
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

def render_cap_table(data, columns=None, image_columns=None, money_columns=None, contract_colors=True):
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
        header_cells.append(f"<th{class_attr}>{escape(str(col))}</th>")

    body_rows = []
    for _, row in table_df.iterrows():
        cells = []
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
                value_html = f'<img class="sbc-table-img" src="{url}" alt="" referrerpolicy="no-referrer">'
                cell_classes.extend(["sbc-image-cell", "sbc-image-col"])
            else:
                display = "—" if value == "" else value
                value_html = escape(str(display))
                if col == "Player":
                    cell_classes.append("sbc-player-cell")

            class_attr = f' class="{" ".join(cell_classes)}"' if cell_classes else ""
            cells.append(f"<td{class_attr}{style}>{value_html}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    render_html(f"""
        <div class="sbc-table-wrap">
            <table class="sbc-cap-table">
                <thead><tr>{''.join(header_cells)}</tr></thead>
                <tbody>{''.join(body_rows)}</tbody>
            </table>
        </div>
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
        if col == "Contacted":
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
                url = escape(str(value), quote=True)
                value_html = f'<img class="sbc-pick-logo" src="{url}" alt="" referrerpolicy="no-referrer">'
                cell_classes.extend(["sbc-pick-logo-cell", "sbc-pick-logo-col"])
            else:
                display = clean_pick_display(value)
                value_html = escape(str(display))
                if col == "Explanation":
                    cell_classes.append("sbc-pick-detail-cell")
                if col == "Contacted":
                    cell_classes.append("sbc-pick-contact-cell")
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


def render_live_stat_board(title, kicker, rows, selected_team):
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


def schedule_result(team_score, opponent_score):
    if is_blank_value(team_score) or is_blank_value(opponent_score):
        return "TBD"
    if float(team_score) > float(opponent_score):
        return "W"
    if float(team_score) < float(opponent_score):
        return "L"
    return "T"


def render_schedule_table(schedule_df, selected_team):
    if schedule_df is None or schedule_df.shape[0] == 0:
        render_html('<div class="sbc-empty-state">No schedule records are available for this selection.</div>')
        return

    type_order = {"Regular Season": 0, "In-Season Tournament": 1, "Play-In": 2, "Playoffs": 3}
    table_df = schedule_df.copy()
    table_df["TypeOrder"] = table_df["Type"].map(type_order).fillna(9)
    table_df = table_df.sort_values(["Period", "TypeOrder", "Game_ID"])

    body_rows = []
    for _, row in table_df.iterrows():
        is_home = row.get("TeamA") == selected_team
        opponent = row.get("TeamB") if is_home else row.get("TeamA")
        opponent_info = team_info.get(opponent, {})
        logo = opponent_info.get("logo", "")
        logo_html = f'<img class="sbc-schedule-logo" src="{escape(str(logo), quote=True)}" alt="{escape(str(opponent), quote=True)} logo">' if logo else ""
        location_text = "Home" if is_home else "Away"
        venue_mark = "vs" if is_home else "@"
        team_score = row.get("TeamAScore") if is_home else row.get("TeamBScore")
        opponent_score = row.get("TeamBScore") if is_home else row.get("TeamAScore")
        result = schedule_result(team_score, opponent_score)
        result_class = {"W": "win", "L": "loss", "T": "tie"}.get(result, "tbd")
        score_text = "TBD" if result == "TBD" else f"{float(team_score):g}-{float(opponent_score):g}"
        type_text = clean_pick_display(row.get("Type", ""))
        round_text = clean_pick_display(row.get("Round", ""))
        context_bits = [bit for bit in [type_text, round_text if round_text != type_text else ""] if bit and bit != "-"]
        context_text = " / ".join(context_bits)
        body_rows.append(dedent(f"""
        <tr class="sbc-schedule-row sbc-schedule-{result_class}">
            <td class="sbc-schedule-period"><span>P{escape(str(row.get("Period", "")))}</span></td>
            <td class="sbc-schedule-opponent">
                {logo_html}
                <div>
                    <strong>{escape(str(venue_mark))} {escape(str(opponent))}</strong>
                    <em>{escape(location_text)} / {escape(context_text)}</em>
                </div>
            </td>
            <td class="sbc-schedule-type"><span>{escape(type_text)}</span></td>
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
                    <th>Type</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>{''.join(body_rows)}</tbody>
        </table>
    </div>
    """)

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Amatic+SC:wght@700&family=Arvo:wght@400;700&family=Audiowide&family=Baloo+2:wght@700;800&family=Bebas+Neue&family=Cabin+Sketch:wght@700&family=Comfortaa:wght@700&family=Creepster&family=Dancing+Script:wght@700&family=Fjalla+One&family=IM+Fell+English&family=Indie+Flower&family=Lobster&family=Neucha&family=Oswald:wght@700&family=Pacifico&family=Parisienne&family=Pathway+Gothic+One&family=Permanent+Marker&family=Playfair+Display:wght@800&family=Poppins:wght@400;600;700;800;900&family=Quicksand:wght@700&family=Roboto+Slab:wght@800&family=Rye&family=Satisfy&family=Shadows+Into+Light&family=Tangerine:wght@700&family=Teko:wght@700&family=Ubuntu:wght@700&display=swap');

    :root {{
        --sbc-team-primary: {bg_color};
        --sbc-team-secondary: {text_color2};
        --sbc-team-text: {text_color};
        --sbc-team-font: "{team_font_css}", "Poppins", sans-serif;
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
        margin-bottom: 0.3rem;
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
        font-size: 0.76rem;
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
        font-size: 1.08rem;
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

    .sbc-cap-table tbody tr:nth-child(even) td {{
        background-color: rgba(247, 249, 252, 0.55);
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
        width: 3rem;
        min-width: 3rem;
        text-align: center;
    }}

    .sbc-table-img {{
        width: 2.45rem;
        height: 2.45rem;
        object-fit: cover;
        border-radius: 50%;
        display: block;
        margin: 0 auto;
        background: #eef2f6;
        border: 2px solid #ffffff;
        box-shadow: 0 0 0 1px rgba(23, 32, 42, 0.14), 0 4px 10px rgba(18, 25, 38, 0.12);
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
        font-size: 1.02rem;
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
        font-size: 0.7rem;
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
        width: 3.15rem;
        min-width: 3.15rem;
        max-width: 3.15rem;
        text-align: center !important;
    }}

    .sbc-pick-logo {{
        width: 1.85rem;
        height: 1.85rem;
        display: block;
        object-fit: contain;
        margin: 0 auto;
        filter: drop-shadow(0 4px 8px rgba(18, 25, 38, 0.13));
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
        width: 13.75rem;
        min-width: 13.75rem;
        max-width: 13.75rem;
        text-align: left !important;
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
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.08em;
        padding: 0.78rem 0.85rem;
        text-align: left;
        text-transform: uppercase;
    }}

    .sbc-schedule-table th:nth-child(1) {{ width: 5.5rem; }}
    .sbc-schedule-table th:nth-child(3) {{ width: 10rem; }}
    .sbc-schedule-table th:nth-child(4) {{ width: 8.5rem; text-align: center; }}

    .sbc-schedule-row {{
        border-left: 0.42rem solid color-mix(in srgb, var(--sbc-team-primary) 60%, #ffffff);
    }}

    .sbc-schedule-row td {{
        border-bottom: 1px solid rgba(23, 32, 42, 0.075);
        color: var(--sbc-ink);
        padding: 0.68rem 0.85rem;
        vertical-align: middle;
    }}

    .sbc-schedule-row:last-child td {{ border-bottom: none; }}
    .sbc-schedule-win {{ border-left-color: #58a76b; }}
    .sbc-schedule-loss {{ border-left-color: #d96b6b; }}
    .sbc-schedule-tie {{ border-left-color: #e6c85c; }}

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
        color: var(--sbc-ink);
        font-size: 0.94rem;
        font-weight: 950;
        line-height: 1.05;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .sbc-schedule-opponent em {{
        display: block;
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

    .sbc-schedule-type span {{
        display: inline-flex;
        max-width: 100%;
        border-radius: 999px;
        background: #f3f6f9;
        border: 1px solid rgba(23, 32, 42, 0.09);
        color: #344054;
        font-size: 0.72rem;
        font-weight: 900;
        line-height: 1;
        overflow: hidden;
        padding: 0.42rem 0.58rem;
        text-overflow: ellipsis;
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

if SelectedTeam == "Honolulu":
    st.balloons()
if SelectedTeam == "Manchester":
    st.snow()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13 = st.tabs([
    f"💰 {SelectedTeam} Cap",
    f"🏀 {SelectedTeam} Picks",
    f"📊 {SelectedTeam} Live",
    f"🗓️ {SelectedTeam} Schedule",
    "🏟️ Scoreboard",
    "👥 Players",
    "🎯 Draft Picks",
    "🏆 Overview",
    "🔁 Trade Machine",
    "📚 Drafts",
    "⭐ Awards",
    "📖 About",
    "✅ Data Checks"])

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
        <div class="sbc-draft-hero">
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
    render_cap_table(active_player_df, columns=[" ", "Player"] + columns_order + ["Bird Rights"], image_columns=[" "])

    overseas_player_df = overseas_players(df, pics, SelectedTeam)
    render_html('<div class="sbc-cap-eyebrow">Overseas Players</div>')
    if overseas_player_df.shape[0] > 0:
        render_cap_table(overseas_player_df, columns=[" ", "Player"] + columns_order + ["Bird Rights"], image_columns=[" "])
    else:
        render_html('<div class="sbc-empty-state">No overseas players are currently listed for this team.</div>')

    dead_player_df = dead_players(df, pics, SelectedTeam)
    render_html('<div class="sbc-cap-eyebrow">Dead Players</div>')
    if dead_player_df.shape[0] > 0:
        dead_player_df["Bird Rights"] = ""
        render_cap_table(dead_player_df, columns=[" ", "Player"] + columns_order + ["Bird Rights"], image_columns=[" "])
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
            render_cap_table(free_agent_player_df, columns=[" ", "Player"] + [str(current_year+ year_offset)], image_columns=[" "])
        else:
            render_html('<div class="sbc-empty-state">No upcoming free agents are currently listed for this team.</div>')

    with asset2:
        render_html('<div class="sbc-cap-eyebrow">Trade Restrictions</div>')
        restricted_df = trade_restrictions(df, pics, SelectedTeam)
        if restricted_df.shape[0] > 0:
            render_cap_table(restricted_df, columns=[" ", "Player", "Trade Restriction"], image_columns=[" "], contract_colors=False)
        else:
            render_html('<div class="sbc-empty-state">No trade restrictions are currently listed for this team.</div>')

    with asset3:
        render_html('<div class="sbc-cap-eyebrow">Draft Rights & Retired</div>')
        draft_retired_player_df = draft_retired_players(df, pics, SelectedTeam)
        if draft_retired_player_df.shape[0] > 0:
            render_cap_table(draft_retired_player_df, columns=[" ", "Player"], image_columns=[" "])
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
        <div class="sbc-draft-hero">
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
        image_columns=["OGTeam"],
        status="hold")

    render_pick_table(
        shared_team_picks,
        "Swaps & Shared Control",
        "⇄",
        "Picks with swap language, shared ownership, or split-control terms.",
        "No swapped or shared-control picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "Contacted", "Explanation"],
        image_columns=["OGTeam"],
        status="swap")

    render_pick_table(
        locked_team_picks,
        "Locked Picks",
        "⌖",
        "Picks the team has, but is not allowed to trade right now.",
        "No locked picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "Contacted", "Explanation"],
        image_columns=["OGTeam"],
        status="locked")

    render_pick_table(
        original_team_picks,
        "Traded Away Picks",
        "↗",
        "Original team picks that now sit with another owner.",
        "No traded-away picks are currently listed.",
        columns=["Year", "Round", "OGTeam", "CurrentTeam", "Contacted", "Explanation"],
        image_columns=["OGTeam", "CurrentTeam"],
        status="away")
    if False and touched_team_picks.shape[0] > 0:
        st.header("Touched Draft Picks")
        st.dataframe(touched_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})


with tab3:
    render_html(f"""
        <div class="sbc-draft-hero">
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
        max_period_raw = all_time_schedule[all_time_schedule["Year"] == SelectedYear]["Period"].max()
        max_period = int(max_period_raw) if not pd.isna(max_period_raw) else 1
        current_period_value = current_matchup if isinstance(current_matchup, int) else max_period
        period_options = list(range(1, max_period+1))
        SelectedPeriod = st.selectbox("Period", options=period_options, index=period_options.index(min(current_period_value, max_period)))
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
            SelectedTeam)
    else:
        matchup_cols = st.columns(min(3, matchup_count))
        for idx, (matchup_type, opponent) in enumerate(matchup_sections):
            with matchup_cols[idx % len(matchup_cols)]:
                selected_payload = live_row_payload(live_stats_df, SelectedTeam)
                opponent_payload = live_row_payload(live_stats_df, opponent)
                matchup_rows = [payload for payload in [selected_payload, opponent_payload] if payload]
                render_live_stat_board(
                    f"{SelectedTeam} vs {opponent}",
                    f"{matchup_type} - Period {SelectedPeriod}",
                    matchup_rows,
                    SelectedTeam)

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
    default_schedule_year = current_year if current_year in schedule_years else schedule_years[-1]
    render_html(f"""
        <div class="sbc-draft-hero">
            <div class="sbc-draft-hero-inner">
                <img class="sbc-draft-logo" src="{team_logo_html}" alt="{team_name_html} logo">
                <div>
                    <div class="sbc-draft-eyebrow">Travel Desk</div>
                    <div class="sbc-draft-heading">{team_name_html} {nickname_html} Schedule</div>
                    <div class="sbc-draft-subcopy">Opponent flow, home-road balance, matchup types, results, and travel load by season.</div>
                </div>
            </div>
        </div>
        """)
    SelectedScheduleYear = st.selectbox(
        "Schedule Year",
        options=schedule_years,
        index=schedule_years.index(default_schedule_year))
    schedule_raw = all_time_schedule[
        (all_time_schedule["Year"] == SelectedScheduleYear)
        & ((all_time_schedule["TeamA"] == SelectedTeam) | (all_time_schedule["TeamB"] == SelectedTeam))
    ].copy()
    render_html('<div class="sbc-section-label">Schedule</div>')
    render_schedule_table(schedule_raw, SelectedTeam)
    total_miles, num_flights = get_team_mileage(SelectedTeam, SelectedScheduleYear, all_time_schedule)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Miles", value=f"{int(total_miles):,} mi", help="Total miles traveled this season including road trips and returns home.", border=True)
    with col2:
        st.metric(label="Total Flights", value=num_flights, help="Number of flights taken this season (legs with distance > 0).", border=True)
    st_folium(plot_team_flights(SelectedTeam, SelectedScheduleYear, all_time_schedule), width="100%", height=480, returned_objects=[])

with tab5:
    st.subheader("League Scoreboard")

    SelectedYear2 = st.selectbox("Select Year", options=list(range(2021, current_year+1)), index=list(range(2021, current_year+1)).index(current_year))
    max_period2 = all_time_schedule[all_time_schedule["Year"] == SelectedYear2]["Period"].max()
    SelectedPeriod2 = st.selectbox("Select Period", options=list(range(1, max_period2+1)), index=list(range(1, max_period2+1)).index(min(current_matchup, max_period2)))

    with st.spinner("Updating matchups..."):
        live_stats_df2 = get_matchup_stats(SelectedYear2, SelectedPeriod2)
        live_stats_total_scores = get_weekly_scores_df(SelectedYear2, SelectedPeriod2, all_time_schedule, live_stats_df2, standings)

    def render_section(title, type_filter, n_cols):
        filtered = live_stats_total_scores[live_stats_total_scores["Type"] == type_filter]
        if filtered.empty:
            return
        st.subheader(title)
        cols = st.columns(n_cols)
        for i, (_, row) in enumerate(filtered.iterrows()):
            with cols[i % n_cols]:
                render_scorebug(row)

    render_section("Regular Season Matchups", "Regular Season", 6)
    render_section("In-Season Tournament Matchups", "In-Season Tournament", 6)
    render_section("Play-In Tournament Matchups", "Play-In", 4)
    render_section("Playoff Matchups", "Playoffs", 4)

    col1, col2 = st.columns([1,1])
    with col1:
        st.subheader("Western Conference Standings")
        WestStandings = get_standings_table(standings, SelectedPeriod2, SelectedYear2, "West")
        st.dataframe(WestStandings, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn(label="", width="small")})

    with col2:
        st.subheader("Easten Conference Standings")
        EastStandings = get_standings_table(standings, SelectedPeriod2, SelectedYear2, "East")
        st.dataframe(EastStandings, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn(label="", width="small")})
    
    st.write("Tiebreakers not currently implemented, so teams with identical records are sorted alphabetically within the standings.")

with tab6:

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

with tab7:
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

with tab8:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label = "Salary Cap", value = current_salary_cap, delta = "10.0%", delta_color = "normal", help = "Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border = True, format = "dollar")
    
    with col2:
        st.metric(label = "Luxury Tax", value = current_luxury_tax, delta = "10.0%", delta_color = "normal", help = "Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border = True, format = "dollar")
    
    with col3:
        st.metric(label = "Apron #1", value = current_apron_1, delta = "10.0%", delta_color = "normal", help = "Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border = True, format = "dollar")
    
    with col4:
        st.metric(label = "Apron #2", value = current_apron_2, delta = "10.0%", delta_color = "normal", help = "Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade–related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border = True, format = "dollar")

    overall_cap_df = overall_cap_table(df, exceptions, base_cap)
    styled_overall_cap_df = (overall_cap_df.style
        .apply(lambda row: style_overall_cap(row), axis=1)
        .format({c: "${:,.2f}" for c in overall_cap_df.columns if c in ["Base Fee", "Luxury Fee", "Balance", "Amount Paid", "Cap Space", "Tax Space", "Apron 1 Space", "Apron 2 Space"]}))
    st.dataframe(styled_overall_cap_df, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn(label="", width="small")})

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label = "Champion Payout", value = unit_payout(df, exceptions, base_cap)*12, help = "Awarded to the SBCFBL Champion. Prize equals ½ of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    with col2:
        st.metric(label = "Runner-Up Payout", value = unit_payout(df, exceptions, base_cap)*4, help = "Awarded to the SBCFBL Runner-up. Prize equals 1⁄6 of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    with col3:
        st.metric(label = "Conference Finalists", value = unit_payout(df, exceptions, base_cap)*2, help = "Awarded to each Conference Runner-up (2 total). Prize equals 1⁄12 of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    with col4:
        st.metric(label = "Conference Semifinalists", value = unit_payout(df, exceptions, base_cap)*1, help = "Awarded to each Conference Semifinal loser (4 total). Prize equals 1⁄24 of the base fee pool after Fantrax, Larry Coon Trophy, and IST fees.", border = True, format = "dollar")

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label = "Charity Champion", value = tax_payout_champ(df, exceptions, base_cap), help = "Awarded to the SBCFBL Champion to donate to a charity of their choice. Amount equals ½ of the luxury fee pool after all SBCFBL expenses.", border = True, format = "dollar")

    with col2:
        st.metric(label = "Tax Payback", value = tax_payout_split(df, exceptions, base_cap), help = "Awarded to non-tax teams for finishing outside the tax. Amount equals ½ of the luxury fee pool after all SBCFBL expenses, split evenly among non-tax teams.", border = True, format = "dollar")

    with col3:
        st.metric(label = "IST Champion", value = 75, help = "Awarded to the SBCFBL Cup Champion. Prize is a flat $75.", border = True, format = "dollar")

    with col4:
        st.metric(label = "IST Runner Up", value = 15, help = "Awarded to the SBCFBL Cup Runner-up. Prize is a flat $15.", border = True, format = "dollar")

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
        base_table = lottery_table(standings)

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
        
        if all(ball is not None for ball in [ball1, ball2, ball3, ball4]):
            st.balloons()
        # Sort by count descending
        summary = summary.sort_values("Count", ascending=False)
        col5, col6 = st.columns([4, 1])        
        with col5:
            st.dataframe(filtered_table, width="stretch", height="content", row_height=50, hide_index=True)
        with col6:
            st.dataframe(summary, width="stretch", hide_index=True)



with tab11:
    AwardYears = st.selectbox("Select Award Year", options=list(range(2021, current_year+1)), index=list(range(2021, current_year+1)).index(current_year))
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

with tab12:
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

with tab13:

    picture_check = data_picture_check(df, pics)
    if picture_check.shape[0] > 0:
        st.header("Pictures")
        st.dataframe(picture_check)

    roster_n_check = data_roster_check(df)
    #if roster_n_check.shape[0] > 0:
    #    st.header("Roster Count")
    #    st.dataframe(roster_n_check)

    missing_salary_check = data_missing_salary_check(df)
    if missing_salary_check.shape[0] > 0:
        st.header("Missing Salary Info")
        st.dataframe(missing_salary_check)

    hard_cap_check_df = hard_cap_check(df, base_cap)
    if hard_cap_check_df.shape[0] > 0:
        st.header("Hard Cap Broken")        
        st.dataframe(hard_cap_check_df)

    stepien_check = stepien_data_check(dp)
    if stepien_check.shape[0] > 0:
        st.header("Stepien Rule Broken")
        st.dataframe(stepien_check)

    missing_fantrax = fantrax_players_check(df, ft_players, ft_roster)
    if missing_fantrax.shape[0] > 0:
        st.header("Cap Sheet to Fantrax Translation")
        st.dataframe(missing_fantrax)

    cap_sheet_to_fantrax_df = fantrax_roster_check(df, ft_players, ft_roster)
    if cap_sheet_to_fantrax_df.shape[0] > 0:
        st.header("Cap Sheet to Fantrax Roster")
        st.dataframe(cap_sheet_to_fantrax_df)

    positoinal_check_df = fantrax_positional_check(df, ft_players, ft_roster)
    if positoinal_check_df.shape[0] > 0:
        st.header("Fantrax Positional Check")
        st.dataframe(positoinal_check_df)
