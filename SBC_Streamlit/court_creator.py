r"""Standalone Streamlit editor for all 30 SBC branded courts.

Run with: .\.venv\Scripts\python.exe -m streamlit run court_creator.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ft2font import FT2Font
import numpy as np
import pandas as pd
import requests
import streamlit as st

from court_engine import CourtConfig, draw_branded_court, figure_bytes, plot_shots
from data import team_info


APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "court_team_configs.csv"
LOGO_DIR = APP_DIR / "assets" / "court_logos"
FONT_DIR = APP_DIR / ".streamlit_cache" / "court_fonts"
TEAMS = sorted(team_info)

HARDWOODS = {
    "Light maple": ("#E4C58B", "#B88F55"),
    "Natural maple": ("#D9B77E", "#9B7745"),
    "Honey maple": ("#CF9F5B", "#8D6030"),
    "Golden oak": ("#C58D4A", "#80552D"),
    "Warm beech": ("#D2AA72", "#93683D"),
    "Classic parquet": ("#CDA96F", "#8B663A"),
    "Dark walnut": ("#8A603D", "#51351F"),
    "Gray wash": ("#B9B2A6", "#797269"),
}

GOOGLE_FONTS = [
    "Alfa Slab One", "Amatic SC", "Arvo", "Audiowide", "Baloo 2", "Bebas Neue",
    "Bungee", "Cabin Sketch", "Comfortaa", "Creepster", "Dancing Script", "Fjalla One",
    "IM Fell English", "Indie Flower", "Lobster", "Neucha", "Oswald", "Pacifico",
    "Parisienne", "Pathway Gothic One", "Permanent Marker", "Playfair Display", "Poppins",
    "Quicksand", "Roboto Slab", "Rye", "Satisfy", "Shadows Into Light", "Tangerine",
    "Teko", "Ubuntu",
]

TEAM_FONTS = {
    "Albuquerque": "Amatic SC", "Anaheim": "Baloo 2", "Anchorage": "Fjalla One",
    "Austin": "Creepster", "Baltimore": "Lobster", "Birmingham": "Rye", "Boise": "Neucha",
    "Buffalo": "Teko", "Cincinnati": "Satisfy", "Columbus": "Arvo", "Des Moines": "Cabin Sketch",
    "El Paso": "Pathway Gothic One", "Honolulu": "Dancing Script", "Jacksonville": "Pacifico",
    "Kentucky": "Playfair Display", "Lansing": "Ubuntu", "Lincoln": "Bebas Neue",
    "Little Rock": "Alfa Slab One", "Manchester": "Quicksand", "Nashville": "Tangerine",
    "Pittsburgh": "Roboto Slab", "Providence": "IM Fell English", "San Diego": "Comfortaa",
    "San Jose": "Indie Flower", "Seattle": "Poppins", "St. Louis": "Oswald",
    "Tampa Bay": "Parisienne", "Tulsa": "Permanent Marker", "Vancouver": "Shadows Into Light",
    "Vegas": "Audiowide",
}


def default_row(team: str) -> dict:
    config = CourtConfig(team=team, baseline_text=team.upper(), font_family=TEAM_FONTS.get(team, "Poppins"))
    return config.to_dict() | {
        "hardwood": "Natural maple",
        "wood_grain": "Natural maple",
        "logo_path": "",
        "league_logo_path": "",
    }


def read_config_table() -> pd.DataFrame:
    if CONFIG_PATH.exists():
        table = pd.read_csv(CONFIG_PATH).fillna("")
    else:
        table = pd.DataFrame([default_row(team) for team in TEAMS])
    missing = [team for team in TEAMS if team not in set(table.get("team", []))]
    if missing:
        table = pd.concat([table, pd.DataFrame([default_row(team) for team in missing])], ignore_index=True)
    for key, value in default_row(TEAMS[0]).items():
        if key not in table.columns:
            table[key] = value
    return table[table["team"].isin(TEAMS)].sort_values("team").reset_index(drop=True)


def bool_value(value) -> bool:
    return value if isinstance(value, bool) else str(value).lower() in {"true", "1", "yes"}


@st.cache_resource(show_spinner=False)
def google_font_path(font_family: str) -> str:
    """Fetch and cache a Google Font file usable by Matplotlib."""
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-z0-9]+", "_", font_family.lower()).strip("_")
    existing = list(FONT_DIR.glob(f"{safe_name}.*"))
    for cached_path in existing:
        try:
            FT2Font(str(cached_path))
            return str(cached_path)
        except (RuntimeError, OSError):
            cached_path.unlink(missing_ok=True)

    # Every selected family offers a regular/base face. Some decorative fonts
    # do not publish a true 700 face, which made the prior bold-only URL fail.
    css_url = f"https://fonts.googleapis.com/css2?family={font_family.replace(' ', '+')}"
    last_error = None
    for _ in range(3):
        try:
            response = requests.get(css_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            response.raise_for_status()
            urls = re.findall(r"url\((https://[^)]+)\)", response.text)
            if not urls:
                raise ValueError("Google Fonts returned no downloadable font file")
            font_response = requests.get(urls[-1], headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            font_response.raise_for_status()
            content_type = font_response.headers.get("content-type", "")
            suffix = ".woff2" if "woff2" in content_type else ".ttf"
            path = FONT_DIR / f"{safe_name}{suffix}"
            path.write_bytes(font_response.content)
            FT2Font(str(path))
            return str(path)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Could not load {font_family}: {last_error}")


def color_control(label: str, value: str, key: str) -> str:
    return st.color_picker(label, value=value, key=key)


def palette_color(
    label: str,
    saved_value: str,
    selected_hardwood: str,
    team_color_1: str,
    team_color_2: str,
    key: str,
) -> str:
    """Select a team color, neutral, custom color, or named wood tone."""
    saved_value = str(saved_value or "")
    palette = {
        "Team Color 1": team_color_1,
        "Team Color 2": team_color_2,
        "White": "#FFFFFF",
        "Black": "#000000",
    }
    matching_wood = next((name for name, (wood, _) in HARDWOODS.items() if wood.lower() == saved_value.lower()), None)
    if not saved_value or matching_wood:
        selected = "Choose Wood"
    else:
        selected = next((name for name, color in palette.items() if color.lower() == saved_value.lower()), "Custom")
    options = ["Choose Wood", "Team Color 1", "Team Color 2", "White", "Black", "Custom"]
    choice = st.selectbox(label, options, index=options.index(selected), key=f"{key}_choice")
    if choice == "Choose Wood":
        initial_wood = matching_wood or selected_hardwood
        wood_choice = st.selectbox(
            f"{label} wood",
            list(HARDWOODS),
            index=list(HARDWOODS).index(initial_wood),
            key=f"{key}_wood",
        )
        return HARDWOODS[wood_choice][0]
    if choice == "Custom":
        return st.color_picker(f"{label} custom color", value=saved_value or HARDWOODS[selected_hardwood][0], key=f"{key}_custom")
    return palette[choice]


def brand_palette_color(label: str, saved_value: str, team_color_1: str, team_color_2: str, key: str) -> str:
    """Palette for non-wood branding elements such as lines and wordmarks."""
    saved_value = str(saved_value or "")
    palette = {
        "Team Color 1": team_color_1,
        "Team Color 2": team_color_2,
        "White": "#FFFFFF",
        "Black": "#000000",
    }
    selected = next((name for name, color in palette.items() if color.lower() == saved_value.lower()), "Custom")
    options = ["Team Color 1", "Team Color 2", "White", "Black", "Custom"]
    choice = st.selectbox(label, options, index=options.index(selected), key=f"{key}_choice")
    if choice == "Custom":
        return st.color_picker(f"{label} custom color", value=saved_value or team_color_1, key=f"{key}_custom")
    return palette[choice]


st.set_page_config(page_title="SBC Court Creator", page_icon="🏀", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    :root { color-scheme: light; }
    .stApp, [data-testid="stAppViewContainer"] { background:#f5f7fb; color:#111827; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background:#ffffff !important; }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color:#111827 !important; }
    [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] > div { background:#ffffff !important; color:#111827 !important; }
    [data-testid="stSidebar"] input::placeholder { color:#6b7280 !important; }
    [data-testid="stSidebar"] hr { border-color:#d1d5db; }
    .block-container { max-width:1450px; padding-top:2rem; }
    .court-kicker { color:#2563eb; font-size:.78rem; font-weight:900; letter-spacing:.16em; text-transform:uppercase; }
    .court-title { color:#111827; font-size:clamp(2rem,4vw,3.6rem); font-weight:950; line-height:1; margin:.25rem 0 .45rem; }
    .court-copy { color:#64748b; font-size:1rem; font-weight:600; max-width:58rem; margin-bottom:1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

table = read_config_table()
st.markdown('<div class="court-kicker">SBC Design Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="court-title">Court Creator</div>', unsafe_allow_html=True)
st.markdown('<div class="court-copy">Choose a team, tune its court, save the row, and move directly to the next franchise.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Court controls")
    team = st.selectbox("Team/configuration name", TEAMS, index=0)
    saved = table.loc[table["team"] == team].iloc[0].to_dict()
    key_prefix = re.sub(r"[^a-z0-9]", "_", team.lower())
    team_color_1 = str(team_info[team]["bg"])
    team_color_2 = str(team_info[team]["bg2"])

    with st.expander("Team and words", expanded=True):
        legacy_text = str(saved.get("baseline_text", team.upper()))
        baseline_text_bottom = st.text_input("Text under basket 1 (left/bottom)", value=str(saved.get("baseline_text_bottom") or legacy_text), key=f"{key_prefix}_baseline_1")
        baseline_text_top = st.text_input("Text under basket 2 (right/top)", value=str(saved.get("baseline_text_top") or legacy_text), key=f"{key_prefix}_baseline_2")
        sideline_text = st.text_input("Sideline text", value=str(saved["sideline_text"]), key=f"{key_prefix}_sideline")
        text_color = brand_palette_color("Text color", saved["text_color"], team_color_1, team_color_2, f"{key_prefix}_text_color")
        text_size = st.slider("Text size", 8, 32, int(float(saved["text_size"])), key=f"{key_prefix}_text_size")
        default_font = str(saved.get("font_family", TEAM_FONTS.get(team, "Poppins")))
        font_team = next((font_team for font_team, family in TEAM_FONTS.items() if family == default_font), team)
        font_team = st.selectbox("Team font", TEAMS, index=TEAMS.index(font_team), key=f"{key_prefix}_font_team", help="Each team name represents its assigned Google Font.")
        font_family = TEAM_FONTS[font_team]

    with st.expander("Floor", expanded=True):
        hardwood = st.selectbox("Hardwood", list(HARDWOODS), index=list(HARDWOODS).index(saved.get("hardwood", "Natural maple")) if saved.get("hardwood") in HARDWOODS else 1, key=f"{key_prefix}_hardwood")
        hardwood_color, default_grain = HARDWOODS[hardwood]
        court_color = hardwood_color
        out_of_bounds_color = brand_palette_color("Out of bounds", saved["out_of_bounds_color"], team_color_1, team_color_2, f"{key_prefix}_oob")
        line_color = brand_palette_color("Court lines", saved["line_color"], team_color_1, team_color_2, f"{key_prefix}_lines")
        floor_pattern = st.radio("Floor pattern", ["parquet", "planks"], index=0 if saved.get("floor_pattern", "parquet") == "parquet" else 1, horizontal=True, key=f"{key_prefix}_pattern")
        saved_grain = str(saved.get("wood_grain") or "Natural maple")
        if saved_grain not in HARDWOODS:
            saved_plank_color = str(saved.get("plank_color") or "").lower()
            saved_grain = next((name for name, (_, grain) in HARDWOODS.items() if grain.lower() == saved_plank_color), "Natural maple")
        wood_grain = st.selectbox("Wood grain", list(HARDWOODS), index=list(HARDWOODS).index(saved_grain), key=f"{key_prefix}_grain")
        plank_color = HARDWOODS[wood_grain][1]
        plank_opacity = st.slider("Wood grain strength", 0.0, 0.35, float(saved["plank_opacity"]), 0.01, key=f"{key_prefix}_grain_alpha")

    with st.expander("Eight court color zones", expanded=True):
        st.caption(f"Team Color 1: {team_color_1} · Team Color 2: {team_color_2}")
        palette_args = (hardwood, team_color_1, team_color_2)
        inner_center_circle_color = palette_color("1. Inner half-court circle", saved["inner_center_circle_color"], *palette_args, f"{key_prefix}_z1")
        outer_center_circle_color = palette_color("2. Outer half-court circle", saved["outer_center_circle_color"], *palette_args, f"{key_prefix}_z2")
        outside_three_color = palette_color("3. Outside three-point line", saved["outside_three_color"], *palette_args, f"{key_prefix}_z3")
        inside_three_color = palette_color("4. Inside three-point line", saved["inside_three_color"], *palette_args, f"{key_prefix}_z4")
        free_throw_outer_half_color = palette_color("5. Half-circle above free throw", saved["free_throw_outer_half_color"], *palette_args, f"{key_prefix}_z5")
        free_throw_inner_half_color = palette_color("6. Half-circle inside paint", saved["free_throw_inner_half_color"], *palette_args, f"{key_prefix}_z6")
        core_paint_color = palette_color("7. Core paint", saved["core_paint_color"], *palette_args, f"{key_prefix}_z7")
        paint_stripe_color = palette_color("8. Paint stripes", saved["paint_stripe_color"], *palette_args, f"{key_prefix}_z8")

    with st.expander("Center-court logo", expanded=True):
        logo_options = ["None"] + TEAMS
        saved_logo_team = str(saved.get("center_logo_team") or team)
        center_logo_team = st.selectbox("Center-court team logo", logo_options, index=logo_options.index(saved_logo_team) if saved_logo_team in logo_options else logo_options.index(team), key=f"{key_prefix}_center_logo_team")
        logo_scale = st.slider("Logo scale", 0.10, 1.80, float(saved["logo_scale"]), 0.05, key=f"{key_prefix}_logo_scale")
        logo_opacity = st.slider("Logo opacity", 0.10, 1.00, float(saved["logo_opacity"]), 0.05, key=f"{key_prefix}_logo_opacity")
        logo_x = st.number_input("Logo horizontal position", min_value=0.0, max_value=50.0, value=float(saved["logo_x"]), step=0.5, key=f"{key_prefix}_logo_x")
        logo_y = st.number_input("Logo vertical position", min_value=0.0, max_value=94.0, value=float(saved["logo_y"]), step=0.5, key=f"{key_prefix}_logo_y")

    with st.expander("League logo"):
        uploaded_league_logo = st.file_uploader("Upload league logo", type=["png", "jpg", "jpeg", "webp"], key="sbc_league_logo")
        league_logo_scale = st.slider("League logo size", 0.10, 1.20, float(saved.get("league_logo_scale", 0.45)), 0.05, key=f"{key_prefix}_league_scale")
        league_logo_opacity = st.slider("League logo opacity", 0.10, 1.00, float(saved.get("league_logo_opacity", 1.0)), 0.05, key=f"{key_prefix}_league_opacity")
        st.caption("The league logo is centered along the bottom sideline in horizontal view.")

    with st.expander("Canvas and export"):
        orientation = st.radio("Orientation", ["horizontal", "vertical"], horizontal=True)
        view = st.radio("Court view", ["full", "half"], horizontal=True)
        outer_margin = st.slider("Outer border", 0.0, 8.0, float(saved["outer_margin"]), 0.5, key=f"{key_prefix}_margin")
        export_format = st.selectbox("Download format", ["png", "svg"])
        export_dpi = st.select_slider("PNG quality", options=[100, 150, 200, 300, 400], value=200)
        transparent = st.toggle("Transparent canvas", False)

font_path = ""
font_warning = ""
try:
    font_path = google_font_path(font_family)
except Exception as exc:
    font_warning = f"Google Font unavailable; showing the local fallback. {exc}"

config = CourtConfig(
    team=team, court_color=court_color, out_of_bounds_color=out_of_bounds_color,
    line_color=line_color, inner_center_circle_color=inner_center_circle_color,
    outer_center_circle_color=outer_center_circle_color, outside_three_color=outside_three_color,
    inside_three_color=inside_three_color, free_throw_outer_half_color=free_throw_outer_half_color,
    free_throw_inner_half_color=free_throw_inner_half_color, core_paint_color=core_paint_color,
    paint_stripe_color=paint_stripe_color, line_width=1.2, boundary_width=1.2,
    baseline_text=baseline_text_bottom, baseline_text_bottom=baseline_text_bottom,
    baseline_text_top=baseline_text_top, sideline_text=sideline_text, text_color=text_color,
    text_size=float(text_size), font_family=font_family, font_path=font_path,
    logo_scale=logo_scale, logo_rotation=90.0, logo_opacity=logo_opacity,
    logo_x=logo_x, logo_y=logo_y, center_logo_team="" if center_logo_team == "None" else center_logo_team,
    league_logo_scale=league_logo_scale, league_logo_opacity=league_logo_opacity,
    show_center_circle=True, show_lane_marks=True,
    wood_planks=True, plank_color=plank_color, plank_opacity=plank_opacity,
    floor_pattern=floor_pattern, outer_margin=outer_margin,
)

logo_source = team_info[center_logo_team]["logo"] if center_logo_team in team_info else None
saved_league_path = Path(str(saved.get("league_logo_path", ""))) if saved.get("league_logo_path") else None
if saved_league_path and not saved_league_path.is_absolute():
    saved_league_path = APP_DIR / saved_league_path
if not saved_league_path or not saved_league_path.exists():
    league_candidates = list(LOGO_DIR.glob("league_logo.*")) if LOGO_DIR.exists() else []
    saved_league_path = league_candidates[0] if league_candidates else None
league_logo_source = uploaded_league_logo.getvalue() if uploaded_league_logo else saved_league_path

preview_tab, shot_tab, config_tab = st.tabs(["Court preview", "Shot-chart test", "All team configurations"])
with preview_tab:
    if font_warning:
        st.warning(font_warning)
    fig, _ = draw_branded_court(config, logo=logo_source, league_logo=league_logo_source, orientation=orientation, view=view)
    st.pyplot(fig, use_container_width=True)
    export = figure_bytes(fig, export_format, dpi=export_dpi, transparent=transparent)
    plt.close(fig)
    safe_name = "_".join(team.lower().split())
    save_col, image_col, json_col = st.columns(3)
    with save_col:
        if st.button(f"Save {team}", type="primary", use_container_width=True):
            league_logo_path_value = str(saved.get("league_logo_path", ""))
            if uploaded_league_logo:
                LOGO_DIR.mkdir(parents=True, exist_ok=True)
                suffix = Path(uploaded_league_logo.name).suffix.lower() or ".png"
                logo_file = LOGO_DIR / f"league_logo{suffix}"
                logo_file.write_bytes(uploaded_league_logo.getvalue())
                league_logo_path_value = str(logo_file.relative_to(APP_DIR)).replace("\\", "/")
                table["league_logo_path"] = league_logo_path_value
            new_row = config.to_dict() | {"hardwood": hardwood, "wood_grain": wood_grain, "logo_path": "", "league_logo_path": league_logo_path_value}
            table.loc[table["team"] == team, list(new_row)] = list(new_row.values())
            table.to_csv(CONFIG_PATH, index=False)
            st.success(f"Saved {team} to {CONFIG_PATH.name}")
    with image_col:
        st.download_button(f"Download {export_format.upper()}", export, file_name=f"{safe_name}_court.{export_format}", mime="image/png" if export_format == "png" else "image/svg+xml", use_container_width=True)
    with json_col:
        st.download_button("Download configuration", json.dumps(config.to_dict(), indent=2), file_name=f"{safe_name}_court.json", mime="application/json", use_container_width=True)

with shot_tab:
    st.caption("Sample shots use the same regulation coordinates consumed by the reusable plotting function.")
    rng = np.random.default_rng(23)
    sample_x = np.clip(rng.normal(25, 12, 42), 1, 49)
    sample_y = np.clip(rng.gamma(2.2, 7.0, 42), 1, 46) if view == "half" else np.clip(rng.normal(47, 29, 42), 1, 93)
    shot_fig, shot_ax = draw_branded_court(config, logo=logo_source, league_logo=league_logo_source, orientation=orientation, view=view)
    plot_shots(shot_ax, sample_x, sample_y, orientation=orientation, made=rng.random(42) < 0.48)
    st.pyplot(shot_fig, use_container_width=True)
    plt.close(shot_fig)

with config_tab:
    st.subheader("30-team saved configuration")
    st.caption(f"Persistent file: {CONFIG_PATH.name} · {len(table)} teams")
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button("Download all team configurations", table.to_csv(index=False), file_name="court_team_configs.csv", mime="text/csv")
