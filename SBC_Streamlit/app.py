#import os
#os.chdir("SBC_Streamlit")

import streamlit as st
from streamlit_folium import st_folium
import re as re
from html import escape
from functions import get_data, get_pictures, active_players, style_salaries, overseas_players, free_agent_players, dead_players, draft_retired_players, active_player_n, inactive_player_n, get_exceptions, exception_table, get_cap_total, get_tax_total, get_base_cap, team_hard_cap, team_hard_cap_n, base_fee, amount_paid, net_fee, luxury_fee, trade_restrictions, active_players_all, inactive_players_all, dead_players_all, draft_rights_all, retired_all, all_free_agents, trade_restrictions_all, overall_cap_table, unit_payout, tax_payout_champ, tax_payout_split, style_overall_cap, get_draft_picks, full_draft_picks, swap_draft_picks, split_draft_picks, locked_draft_picks, original_draft_picks, touched_draft_picks, all_full_draft_picks, all_swap_draft_picks, all_split_draft_picks, all_locked_draft_picks, data_picture_check, data_roster_check, tradeable_players_in, tradeable_players_out, tradeable_picks_in, tradeable_picks_out, players_out_table, players_in_table, picks_out_table, picks_in_table, net_players_check, no_cash, tpe_st_check, under_100_percent_check, no_bae_mle_check, stepien_check, tradeable_exceptions_in, tradeable_exceptions_out, exceptions_in_table, exceptions_out_table, data_missing_salary_check, hard_cap_check, stepien_data_check, get_fantrax_roster, get_fantrax_players, fantrax_players_check, fantrax_roster_check, fantrax_positional_check, current_draft, get_standings, get_draft_history, past_draft, lottery_table, get_matchup_stats, format_live_stats_df, team_stats_line_chart, current_matchup_period, team_with_ranks, matchup_scoreboard, get_all_time_schedule, get_opponents, get_all_time_team_stats, get_all_time_rosters, get_award_history, get_single_award, get_team_award_history, get_team_award, get_all_stars_award, get_short_term_awards, render_scorebug, get_weekly_scores_df, get_standings_table, get_team_schedule, plot_team_flights, get_team_mileage
# no_aggregation_check, salary_trade_check, tpe_check, bae_mle_check, player_agg_check, create_tpe_check, new_trade_rest_check, old_team_check, team_with_ranks
from data import team_info, type_colors, current_salary_cap, current_luxury_tax, current_apron_1, current_apron_2, current_year, columns_order, year_offset, max_cash, period, stat_to_scipId

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

df = get_data()
pics = get_pictures()
exceptions = get_exceptions()
base_cap = get_base_cap()
dp = get_draft_picks()
ft_roster = get_fantrax_roster(current_year, period)
ft_players = get_fantrax_players()
standings = get_standings()
dh = get_draft_history()
all_time_team_stats = get_all_time_team_stats()
all_time_rosters = get_all_time_rosters()
all_time_schedule = get_all_time_schedule()
current_matchup = current_matchup_period()
award_history = get_award_history()
team_award_history = get_team_award_history()

Teams = sorted(team_info.keys())

top_col1, top_col2 = st.columns([5, 2], vertical_alignment="bottom")
with top_col1:
    st.markdown(
        """
        <div class="sbc-app-masthead">
            <div class="sbc-app-eyebrow">Welcome to the league office</div>
            <div class="sbc-app-title">SBC Fantasy Basketball League</div>
            <div class="sbc-app-subtitle">Cap sheets, live scores, draft assets, awards, and league history in one place.</div>
        </div>
        """,
        unsafe_allow_html=True)
with top_col2:
    st.markdown('<div class="sbc-picker-eyebrow">Team View</div>', unsafe_allow_html=True)
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
            linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(244, 246, 248, 0.97) 34%, #eef2f6 100%);
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
    [data-testid="stToolbar"] a,
    [data-testid="stToolbar"] svg {{
        color: #111827 !important;
        fill: #111827 !important;
        stroke: #111827 !important;
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
        overflow: hidden;
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
        line-height: 1;
        max-width: 100%;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
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
        border-bottom: 1px solid rgba(23, 32, 42, 0.10);
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
        padding: 0.95rem;
    }}

    .sbc-legend-title {{
        color: var(--sbc-ink);
        font-size: 0.9rem;
        font-weight: 950;
        margin-bottom: 0.65rem;
    }}

    .sbc-legend-row {{
        display: flex;
        align-items: center;
        gap: 0.55rem;
        color: var(--sbc-ink);
        font-size: 0.86rem;
        font-weight: 750;
        margin: 0.42rem 0;
    }}

    .sbc-swatch {{
        width: 1.25rem;
        height: 0.82rem;
        border-radius: 4px;
        border: 1px solid rgba(23, 32, 42, 0.12);
        flex: 0 0 auto;
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
        border: 1px solid var(--sbc-border);
        border-radius: 8px;
        box-shadow: 0 10px 30px rgba(18, 25, 38, 0.06);
    }}

    [data-testid="stMetricLabel"] p {{
        color: var(--sbc-muted);
        font-weight: 800;
    }}

    [data-testid="stMetricValue"] {{
        color: var(--sbc-ink);
        font-weight: 900;
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
    }}

    /* Legacy sidebar selectors kept harmless in case Streamlit injects shell nodes. */
    section[data-testid="stSidebar"] {{
        background-color: var(--sbc-team-primary);
    }}
    </style>""",
    unsafe_allow_html=True)

st.markdown(
    f"""
    <section class="sbc-team-hero">
        <div class="sbc-team-hero-inner">
            <div class="sbc-logo-frame">
                <img src="{team_logo_html}" alt="{team_name_html} logo" referrerpolicy="no-referrer">
            </div>
            <div>
                <div class="sbc-team-typeface">{team_name_html} {nickname_html}</div>
                <div class="sbc-team-subtitle">Cap Sheet and League Hub</div>
            </div>
        </div>
    </section>
    """,
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
    r'''
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

    st.markdown(
        f"""
        <div class="sbc-cap-page-title">
            <div class="sbc-cap-eyebrow">{season_label} Season</div>
            <div class="sbc-cap-heading">{team_name_html} {nickname_html} Cap Sheet</div>
            <div class="sbc-cap-subcopy">Roster construction, cap position, tax exposure, exceptions, free agents, and rights inventory.</div>
        </div>
        """,
        unsafe_allow_html=True)

    st.markdown('<div class="sbc-section-label">League Thresholds</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Salary Cap", value=current_salary_cap, delta="10.0%", delta_color="normal", help="Teams can pay player salaries up to this amount with no exceptions applied, and must maintain a payroll of at least 90% of this figure over the season.", border=True, format="dollar")
    with col2:
        st.metric(label="Luxury Tax", value=current_luxury_tax, delta="10.0%", delta_color="normal", help="Teams exceeding this threshold incur a financial penalty, which increases with the amount over the limit and becomes significantly harsher for repeat offenders over multiple seasons.", border=True, format="dollar")
    with col3:
        st.metric(label="Apron #1", value=current_apron_1, delta="10.0%", delta_color="normal", help="Teams above this level face strict roster limits, including bans on sign-and-trades, restricted use of exceptions, limits on salary matching in trades, and loss of certain traded-player exceptions; doing so hard-caps the team at this level for the entire season.", border=True, format="dollar")
    with col4:
        st.metric(label="Apron #2", value=current_apron_2, delta="10.0%", delta_color="normal", help="Teams above this threshold cannot use the mid-level exception, combine player salaries in trades, include cash in trades, or use sign-and-trade-related mechanisms to acquire players; doing so hard-caps the team at this level for the entire season. Additionally there are draft pick penalties if over the second apron for an extended period of time.", border=True, format="dollar")

    st.markdown('<div class="sbc-section-label">Team Snapshot</div>', unsafe_allow_html=True)
    snap1, snap2, snap3, snap4, snap5, snap6 = st.columns(6)
    with snap1:
        st.metric(label="Players", value=active_count, delta=inactive_count, delta_color="off", help="The first number shows active roster players (up to 14, plus up to 3 IR). Teams must carry at least 12 active players, or face penalties after 14 days. The second number represents non-active players, including overseas players, draft rights, retired, and waived players and there is no limit. To qualify as overseas, a drafted player must have spent their entire SBC career abroad, with status locking on opening night.", border=True, format="plain", delta_arrow="off")
    with snap2:
        st.metric(label="Cap Total", value=cap_total, delta=cap_total-current_salary_cap, delta_color="inverse", help="The first number shows total team salary, including all active and inactive player salaries, cap holds for unrenounced free agents, incomplete roster charges, and all exceptions (Mid-Level, Bi-Annual, Disabled Player, and Trade). The second number shows how much room remains relative to the Salary Cap.", border=True, format="dollar")
    with snap3:
        st.metric(label="Tax Total", value=tax_total, delta=tax_total-current_luxury_tax, delta_color="inverse", help="The first number shows total team salary against the luxury tax, including all active and inactive player salaries and incomplete roster charges. Unlike the real NBA, rookie and second-year undrafted fees are not included. The second number shows remaining space relative to the Luxury Tax.", border=True, format="dollar")
    with snap4:
        st.metric(label="Apron Space", value=team_hard_cap(base_cap, SelectedTeam), delta=team_hard_cap_n(df, SelectedTeam, base_cap), help="The first value indicates whether the team is uncapped, capped at the first apron, or capped at the second apron while the second value shows how far the team is from the applicable cap.", border=True, format="dollar")
    with snap5:
        st.metric(label="Entry Fee", value=base_fee(df, SelectedTeam, base_cap), delta=luxury_fee(df, SelectedTeam, base_cap), delta_color="inverse", help="The SBCFBL uses a 3,000,000-1 scale. The first number is the base entry fee, calculated from the Tax Total plus a $3.00 In-Season Tournament fee. The second number shows the Luxury Tax penalty for the season, scaled as a payable fee.", border=True, format="dollar")
    with snap6:
        st.metric(label="Balance", value=net_fee(df, SelectedTeam, base_cap), delta=amount_paid(base_cap, SelectedTeam), delta_color="normal", help="The first number shows current total owed for the season, including base payment, In-Season Tournament fee, tax penalties, winnings, and tax payouts. The second number shows how much has been paid so far.", border=True, format="dollar")

    roster_left, roster_right = st.columns([1.1, 3.2])
    with roster_left:
        st.markdown('<div class="sbc-section-label">Legend</div>', unsafe_allow_html=True)
        st.markdown("""
            <div class="sbc-legend">
                <div class="sbc-legend-title">Contract Status</div>
                <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#FCE5CD;"></span>Guaranteed</div>
                <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#F4CCCC;"></span>Non-Guaranteed</div>
                <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#CFE2F3;"></span>Team Option</div>
                <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#D9D2E9;"></span>Unrestricted</div>
                <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#CFFFFF;"></span>Restricted</div>
                <div class="sbc-legend-row"><span class="sbc-swatch" style="background:#D9D9D9;"></span>Dead</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('<div class="sbc-section-label">Roster Notes</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="sbc-mini-note">
                {SelectedTeam} currently carries <strong>{active_count}</strong> active players and <strong>{inactive_count}</strong> non-active roster assets.
            </div>
            """,
            unsafe_allow_html=True)

    with roster_right:
        st.markdown('<div class="sbc-section-label">Team Rosters</div>', unsafe_allow_html=True)
        st.markdown('<div class="sbc-cap-eyebrow">Active Players</div>', unsafe_allow_html=True)
        active_player_df = active_players(df, pics, SelectedTeam)
        active_player_df = (active_player_df.style
            .apply(lambda row: style_salaries(row, type_colors), axis=1)
            .format({c: "${:,.0f}" for c in active_player_df.columns if re.match(r"\d{4}", c)}))
        st.dataframe(active_player_df, width="stretch", height="content", row_height=50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order + ["Bird Rights"], column_config={" ": st.column_config.ImageColumn(" ")})

        overseas_player_df = overseas_players(df, pics, SelectedTeam)
        st.markdown('<div class="sbc-cap-eyebrow">Overseas Players</div>', unsafe_allow_html=True)
        if overseas_player_df.shape[0] > 0:
            overseas_player_df = (overseas_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)
                .format({c: "${:,.0f}" for c in overseas_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(overseas_player_df, width="stretch", height="content", row_height=50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order + ["Bird Rights"], column_config={" ": st.column_config.ImageColumn(" ")})
        else:
            st.markdown('<div class="sbc-empty-state">No overseas players are currently listed for this team.</div>', unsafe_allow_html=True)

        dead_player_df = dead_players(df, pics, SelectedTeam)
        st.markdown('<div class="sbc-cap-eyebrow">Dead Players</div>', unsafe_allow_html=True)
        if dead_player_df.shape[0] > 0:
            dead_player_df = (dead_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)
                .format({c: "${:,.0f}" for c in dead_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(dead_player_df, width="stretch", height="content", row_height=50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + columns_order, column_config={" ": st.column_config.ImageColumn(" ")})
        else:
            st.markdown('<div class="sbc-empty-state">No dead salary is currently listed for this team.</div>', unsafe_allow_html=True)

    st.markdown('<div class="sbc-section-label">Contract And Asset Details</div>', unsafe_allow_html=True)
    detail1, detail2 = st.columns([1.15, 1])
    with detail1:
        st.markdown('<div class="sbc-cap-eyebrow">Exceptions</div>', unsafe_allow_html=True)
        exception_df = exception_table(exceptions, SelectedTeam)
        exception_df = (exception_df.style
            .format({"Amount": "${:,.0f}"}))
        st.dataframe(exception_df, width="stretch", height="content", row_height=50, hide_index=True, placeholder="—")

        st.markdown('<div class="sbc-cap-eyebrow">Upcoming Free Agents</div>', unsafe_allow_html=True)
        free_agent_player_df = free_agent_players(df, pics, SelectedTeam)
        if free_agent_player_df.shape[0] > 0:
            free_agent_player_df = (free_agent_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)
                .format({c: "${:,.0f}" for c in free_agent_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(free_agent_player_df, width="stretch", height="content", row_height=50, hide_index=True, placeholder="—", column_order=[" ", "Player"] + [str(current_year+ year_offset)], column_config={" ": st.column_config.ImageColumn(" ")})
        else:
            st.markdown('<div class="sbc-empty-state">No upcoming free agents are currently listed for this team.</div>', unsafe_allow_html=True)

    with detail2:
        st.markdown('<div class="sbc-cap-eyebrow">Trade Restrictions</div>', unsafe_allow_html=True)
        restricted_df = trade_restrictions(df, pics, SelectedTeam)
        if restricted_df.shape[0] > 0:
            st.dataframe(restricted_df, width="stretch", height="content", row_height=50, hide_index=True, placeholder="—", column_config={" ": st.column_config.ImageColumn(" ")})
        else:
            st.markdown('<div class="sbc-empty-state">No trade restrictions are currently listed for this team.</div>', unsafe_allow_html=True)

        st.markdown('<div class="sbc-cap-eyebrow">Draft Rights & Retired</div>', unsafe_allow_html=True)
        draft_retired_player_df = draft_retired_players(df, pics, SelectedTeam)
        if draft_retired_player_df.shape[0] > 0:
            draft_retired_player_df = (draft_retired_player_df.style
                .apply(lambda row: style_salaries(row, type_colors), axis=1)
                .format({c: "${:,.0f}" for c in draft_retired_player_df.columns if re.match(r"\d{4}", c)}))
            st.dataframe(draft_retired_player_df, width="stretch", height="content", row_height=50, hide_index=True, placeholder="—", column_order=(" ", "Player"), column_config={" ": st.column_config.ImageColumn(" ")})
        else:
            st.markdown('<div class="sbc-empty-state">No draft-rights or retired players are currently listed for this team.</div>', unsafe_allow_html=True)

with tab2:
    st.subheader(f"{SelectedTeam} Future Draft Picks")
    
    full_team_picks = full_draft_picks(dp, SelectedTeam)
    if full_team_picks.shape[0] > 0:
        st.header("Fully Owned Picks")
        st.dataframe(full_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})
    
    swap_team_picks = swap_draft_picks(dp, SelectedTeam)
    if swap_team_picks.shape[0] > 0:
        st.header("Swapped Draft Picks")
        st.dataframe(swap_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

    split_team_picks = split_draft_picks(dp, SelectedTeam)
    if split_team_picks.shape[0] > 0:
        st.header("Split Draft Picks")
        st.dataframe(split_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small")})

    locked_team_picks = locked_draft_picks(dp, SelectedTeam)
    if locked_team_picks.shape[0] > 0:
        st.header("Locked Draft Picks")
        st.dataframe(locked_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

    original_team_picks = original_draft_picks(dp, SelectedTeam)
    if original_team_picks.shape[0] > 0:
        st.header("Traded Away Draft Picks")
        st.dataframe(original_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})

    touched_team_picks = touched_draft_picks(dp, SelectedTeam)
    if touched_team_picks.shape[0] > 0:
        st.header("Touched Draft Picks")
        st.dataframe(touched_team_picks, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"OGTeam": st.column_config.ImageColumn(label="Slot", width="small"), "CurrentTeam": st.column_config.ImageColumn(label="Owner", width="small")})


with tab3:
    col1, col2 = st.columns([1, 9])

    with col1:
        SelectedYear = st.selectbox("Year", options=list(range(2021, current_year+1)), index=list(range(2021, current_year+1)).index(current_year))
        max_period = all_time_schedule[all_time_schedule["Year"] == SelectedYear]["Period"].max()
        SelectedPeriod = st.selectbox("Period", options=list(range(1, max_period+1)), index=list(range(1, max_period+1)).index(min(current_matchup, max_period)))

    with col2:
        with st.spinner("Updating matchups..."):
            live_stats_df = get_matchup_stats(SelectedYear, SelectedPeriod)
        live_stats_df_team = team_with_ranks(live_stats_df, SelectedTeam, SelectedYear, SelectedPeriod)
        live_stats_df_formatted = format_live_stats_df(live_stats_df_team)
        st.subheader(f"Stats for {SelectedTeam} in Matchup Period {SelectedPeriod} in {SelectedYear}")
        st.dataframe(live_stats_df_formatted, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Team": st.column_config.ImageColumn(label="Team", width="small")})
        RegOpponents = get_opponents(all_time_schedule, SelectedTeam, SelectedYear, SelectedPeriod, "Regular Season")
        PIOpponents = get_opponents(all_time_schedule, SelectedTeam, SelectedYear, SelectedPeriod, "Play-In")
        PlayOpponents = get_opponents(all_time_schedule, SelectedTeam, SelectedYear, SelectedPeriod, "Playoffs")
        ISTOpponents = get_opponents(all_time_schedule, SelectedTeam, SelectedYear, SelectedPeriod, "In-Season Tournament")
        if len(RegOpponents) > 0:
            st.subheader("Regular Season Matchup(s)")
            scoreboard1 = matchup_scoreboard(live_stats_df, SelectedTeam, SelectedYear, SelectedPeriod, RegOpponents[0])
            st.dataframe(scoreboard1, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Team": st.column_config.ImageColumn(label="Team", width="small")})
        if len(RegOpponents) > 1:
            scoreboard2 = matchup_scoreboard(live_stats_df, SelectedTeam, SelectedYear, SelectedPeriod, RegOpponents[1])
            st.dataframe(scoreboard2, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Team": st.column_config.ImageColumn(label="Team", width="small")})
        if len(PIOpponents) > 0:
            st.subheader("Play-In Matchup")
            scoreboard3 = matchup_scoreboard(live_stats_df, SelectedTeam, SelectedYear, SelectedPeriod, PIOpponents[0])
            st.dataframe(scoreboard3, width ="stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Team": st.column_config.ImageColumn(label="Team", width="small")})
        if len(PlayOpponents) > 0:
            st.subheader("Playoff Matchup")
            scoreboard4 = matchup_scoreboard(live_stats_df, SelectedTeam, SelectedYear, SelectedPeriod, PlayOpponents[0])
            st.dataframe(scoreboard4, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Team": st.column_config.ImageColumn(label="Team", width="small")})
        if len(ISTOpponents) > 0:
            st.subheader("In-Season Tournament Matchup")
            scoreboard5 = matchup_scoreboard(live_stats_df, SelectedTeam, SelectedYear, SelectedPeriod, ISTOpponents[0])
            st.dataframe(scoreboard5, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Team": st.column_config.ImageColumn(label="Team", width="small")})
        SelectedCategory = st.selectbox("Category", options=list(stat_to_scipId.keys()), index=list(stat_to_scipId.keys()).index("PTS"))
        season_line_chart_data = team_stats_line_chart(all_time_team_stats, SelectedTeam, SelectedCategory, SelectedYear, SelectedPeriod)
        st.altair_chart(season_line_chart_data, use_container_width=True)

with tab4:
    st.subheader(f"{SelectedTeam} {current_year-1}-{str(current_year)[-2:]} Schedule")
    TeamSchedule = get_team_schedule(all_time_schedule, SelectedTeam, current_year)
    st.dataframe(TeamSchedule, width = "stretch", height = "content", row_height = 50, hide_index=True, placeholder="—", column_config={"Logo": st.column_config.ImageColumn(label="Opp", width="small")})
    total_miles, num_flights = get_team_mileage(SelectedTeam, current_year, all_time_schedule)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Miles", value=f"{int(total_miles):,} mi", help="Total miles traveled this season including road trips and returns home.", border=True)
    with col2:
        st.metric(label="Total Flights", value=num_flights, help="Number of flights taken this season (legs with distance > 0).", border=True)
    st_folium(plot_team_flights(SelectedTeam, current_year, all_time_schedule), width="100%", height=480, returned_objects=[])

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
