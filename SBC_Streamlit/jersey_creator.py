r"""Standalone Streamlit editor for 90 SBC uniform configurations.

Run with: .\.venv\Scripts\python.exe -m streamlit run jersey_creator.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ft2font import FT2Font
import pandas as pd
import requests
import streamlit as st

from data import team_info
from jersey_engine import JerseyConfig, draw_uniform, figure_bytes


APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "jersey_team_configs.csv"
FONT_DIR = APP_DIR / ".streamlit_cache" / "jersey_fonts"
TEAMS = sorted(team_info)
EDITIONS = ["Association", "Icon", "Statement"]

# Keep the editor permissive for intentionally oversized jersey typography.
# Matplotlib accepts font sizes well beyond the jersey silhouette, which is
# useful for cropped, edge-to-edge, and other experimental treatments.
TEXT_FONT_SIZE_MAX = 300.0
NUMBER_FONT_SIZE_MAX = 500.0

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
FONT_OPTIONS = TEAMS + ["SBC League", "Basic Sans", "Basic Serif", "Basic Mono", "Basic Athletic"]
BASIC_FONTS = {
    "SBC League": "Bungee",
    "Basic Sans": "DejaVu Sans",
    "Basic Serif": "DejaVu Serif",
    "Basic Mono": "DejaVu Sans Mono",
    "Basic Athletic": "DejaVu Sans",
}

JERSEY_STRIPES = ["None", "Side panels", "Double side", "Chest band", "Sash", "Pinstripes", "Waist fade"]
SHORTS_STRIPES = ["None", "Side panels", "Double side", "Hem band", "Chevron", "Pinstripes"]
COLLARS = ["V-neck", "Crew", "Wishbone"]


def edition_defaults(team: str, edition: str) -> JerseyConfig:
    info = team_info[team]
    primary = str(info["bg"])
    secondary = str(info["bg2"])
    nickname = str(info.get("nickname", team))
    if edition == "Association":
        base, trim, accent, text = "#FFFFFF", secondary, primary, secondary
        wordmark_text, number_text, player_text = secondary, secondary, secondary
        stripe, shorts_stripe, collar, wordmark = "Side panels", "Side panels", "Crew", nickname
        font_label, font_family = "SBC League", "Bungee"
        logo_x, logo_y, logo_scale, front_number_x, front_number_y = 12.0, 15.0, .70, 0.0, 45.0
        outline, show_league = "#000000", False
        wordmark_size, number_size, name_size, back_number_size = 35.0, 90.0, 50.0, 110.0
        wordmark_x, wordmark_y, back_name_x, back_name_y = 0.0, 29.0, 0.0, 18.0
        back_number_x, back_number_y = 0.0, 37.5
    elif edition == "Icon":
        base, trim, accent, text = primary, secondary, "#FFFFFF", "#FFFFFF"
        wordmark_text, number_text, player_text = "#FFFFFF", "#FFFFFF", "#FFFFFF"
        stripe, shorts_stripe, collar, wordmark = "Double side", "Double side", "Crew", team
        font_label, font_family = team, TEAM_FONTS[team]
        logo_x, logo_y, logo_scale, front_number_x, front_number_y = 12.0, 15.0, .70, 0.0, 45.0
        outline, show_league = trim, True
        wordmark_size, number_size, name_size, back_number_size = 35.0, 60.0, 36.0, 80.0
        wordmark_x, wordmark_y, back_name_x, back_name_y = 0.0, 29.0, 0.0, 18.0
        back_number_x, back_number_y = 0.0, 43.0
    else:
        base, trim, accent, text = primary, "#000000", "#FFFFFF", "#FFFFFF"
        wordmark_text, number_text, player_text = "#FFFFFF", "#000000", "#000000"
        stripe, shorts_stripe, collar, wordmark = "None", "None", "Crew", ""
        font_label, font_family = team, TEAM_FONTS[team]
        logo_x, logo_y, logo_scale, front_number_x, front_number_y = 0.0, 40.0, 3.0, 12.0, 20.0
        outline, show_league = secondary, False
        wordmark_size, number_size, name_size, back_number_size = 35.0, 50.0, 50.0, 110.0
        wordmark_x, wordmark_y, back_name_x, back_name_y = 0.0, 29.0, 0.0, 18.0
        back_number_x, back_number_y = 0.0, 37.5
    return JerseyConfig(
        team=team, edition=edition, jersey_color=base, shorts_color=base,
        trim_color=trim, accent_color=accent, wordmark_color=wordmark_text,
        number_color=number_text, number_outline_color=outline, player_name_color=player_text,
        stripe_style=stripe, shorts_stripe_style=shorts_stripe,
        collar_style=collar, wordmark=wordmark.upper(),
        wordmark_font=font_label, font_family=font_family,
        logo_team=team, jersey_logo_x=logo_x, jersey_logo_y=logo_y,
        jersey_logo_scale=logo_scale, front_number_x=front_number_x,
        front_number_y=front_number_y, number="00" if team == "Pittsburgh" else "27", trim_width=3.4,
        number_outline_width=4.0, front_wordmark_size=wordmark_size,
        front_wordmark_x=wordmark_x, front_wordmark_y=wordmark_y,
        front_number_size=number_size, back_name_size=name_size,
        back_name_x=back_name_x, back_name_y=back_name_y,
        back_number_size=back_number_size, back_number_x=back_number_x,
        back_number_y=back_number_y, show_jersey_logo=True,
        show_league_mark=show_league,
    )


def default_table() -> pd.DataFrame:
    return pd.DataFrame([
        edition_defaults(team, edition).to_dict()
        for team in TEAMS for edition in EDITIONS
    ])


def read_config_table() -> pd.DataFrame:
    if CONFIG_PATH.exists():
        # "None" is a real design option for stripes, not a missing value.
        # Numbers are stored as text so valid leading-zero values such as 00
        # survive every load/edit/save cycle.
        table = pd.read_csv(
            CONFIG_PATH,
            keep_default_na=False,
            dtype={"number": str},
        ).fillna("")
    else:
        table = default_table()
    # Older reads converted the literal "None" stripe choice to a blank. Both
    # render identically, but normalize it so widgets and future saves are valid.
    for stripe_column in ("stripe_style", "shorts_stripe_style"):
        if stripe_column in table:
            table.loc[table[stripe_column].astype(str).str.strip().eq(""), stripe_column] = "None"
    existing = set(zip(table.get("team", []), table.get("edition", [])))
    missing = [edition_defaults(team, edition).to_dict() for team in TEAMS for edition in EDITIONS if (team, edition) not in existing]
    if missing:
        table = pd.concat([table, pd.DataFrame(missing)], ignore_index=True)

    # One-time edition-identity migration. The marker remains in the CSV so
    # later manual work is never overwritten by this template setup.
    if "template_version" not in table.columns or not (pd.to_numeric(table["template_version"], errors="coerce").fillna(0) >= 4).all():
        for team in TEAMS:
            for edition in EDITIONS:
                defaults = edition_defaults(team, edition)
                mask = (table["team"] == team) & (table["edition"] == edition)
                identity_fields = {
                    "jersey_color": defaults.jersey_color,
                    "shorts_color": defaults.shorts_color,
                    "wordmark": defaults.wordmark,
                    "wordmark_font": defaults.wordmark_font,
                    "font_family": defaults.font_family,
                    "logo_team": defaults.logo_team,
                    "show_jersey_logo": defaults.show_jersey_logo,
                    "jersey_logo_x": defaults.jersey_logo_x,
                    "jersey_logo_y": defaults.jersey_logo_y,
                    "jersey_logo_scale": defaults.jersey_logo_scale,
                    "front_number_x": defaults.front_number_x,
                    "front_number_y": defaults.front_number_y,
                    "number": defaults.number,
                    "collar_style": defaults.collar_style,
                    "trim_width": defaults.trim_width,
                    "number_outline_width": defaults.number_outline_width,
                    "front_wordmark_size": defaults.front_wordmark_size,
                    "front_number_size": defaults.front_number_size,
                    "back_name_size": defaults.back_name_size,
                    "back_number_size": defaults.back_number_size,
                }
                for column, value in identity_fields.items():
                    table.loc[mask, column] = value
        table["template_version"] = 4
        table.to_csv(CONFIG_PATH, index=False)

    # Association v5 preset: update only the 30 Association rows. Icon and
    # Statement designs—including any manual work—remain untouched.
    if "template_version" not in table.columns or not (pd.to_numeric(table["template_version"], errors="coerce").fillna(0) >= 5).all():
        for team in TEAMS:
            defaults = edition_defaults(team, "Association")
            mask = (table["team"] == team) & (table["edition"] == "Association")
            for column, value in defaults.to_dict().items():
                if column != "font_path":
                    table.loc[mask, column] = value
        table["template_version"] = 5
        table.to_csv(CONFIG_PATH, index=False)

    # Statement v6 preset: update only the 30 Statement rows.
    if "template_version" not in table.columns or not (pd.to_numeric(table["template_version"], errors="coerce").fillna(0) >= 6).all():
        for team in TEAMS:
            defaults = edition_defaults(team, "Statement")
            mask = (table["team"] == team) & (table["edition"] == "Statement")
            for column, value in defaults.to_dict().items():
                if column != "font_path":
                    table.loc[mask, column] = value
        table["template_version"] = 6
        table.to_csv(CONFIG_PATH, index=False)
    sample = edition_defaults(TEAMS[0], EDITIONS[0]).to_dict()
    for column, value in sample.items():
        if column not in table:
            table[column] = value
    order = {edition: index for index, edition in enumerate(EDITIONS)}
    table = table[table["team"].isin(TEAMS) & table["edition"].isin(EDITIONS)].copy()
    table["_edition_order"] = table["edition"].map(order)
    return table.sort_values(["team", "_edition_order"]).drop(columns="_edition_order").reset_index(drop=True)


def bool_value(value) -> bool:
    return value if isinstance(value, bool) else str(value).lower() in {"true", "1", "yes"}


def option_index(options: list[str], saved, fallback: str) -> int:
    """Return a safe widget index for legacy or malformed saved values."""
    value = str(saved).strip()
    return options.index(value) if value in options else options.index(fallback)


@st.cache_resource(show_spinner=False)
def google_font_path(font_family: str) -> str:
    if font_family.startswith("DejaVu"):
        return ""
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-z0-9]+", "_", font_family.lower()).strip("_")
    for path in FONT_DIR.glob(f"{safe_name}.*"):
        try:
            FT2Font(str(path))
            return str(path)
        except (RuntimeError, OSError):
            path.unlink(missing_ok=True)
    css_url = f"https://fonts.googleapis.com/css2?family={font_family.replace(' ', '+')}"
    error = None
    for _ in range(3):
        try:
            css = requests.get(css_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            css.raise_for_status()
            urls = re.findall(r"url\((https://[^)]+)\)", css.text)
            if not urls:
                raise ValueError("No font URL returned")
            font_response = requests.get(urls[-1], headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            font_response.raise_for_status()
            suffix = ".woff2" if "woff2" in font_response.headers.get("content-type", "") else ".ttf"
            path = FONT_DIR / f"{safe_name}{suffix}"
            path.write_bytes(font_response.content)
            FT2Font(str(path))
            return str(path)
        except Exception as exc:
            error = exc
    raise RuntimeError(f"Could not load {font_family}: {error}")


def palette_control(label: str, saved: str, team: str, key: str, allow_transparent: bool = False) -> str:
    primary, secondary = str(team_info[team]["bg"]), str(team_info[team]["bg2"])
    palette = {"Team Color 1": primary, "Team Color 2": secondary, "White": "#FFFFFF", "Black": "#000000"}
    if allow_transparent:
        palette["None"] = "none"
    selected = next((name for name, value in palette.items() if value.lower() == str(saved).lower()), "Custom")
    options = list(palette) + ["Custom"]
    choice = st.selectbox(label, options, index=options.index(selected), key=f"{key}_choice")
    if choice == "Custom":
        return st.color_picker(f"{label} custom", value=str(saved) if str(saved).startswith("#") else primary, key=f"{key}_custom")
    return palette[choice]


st.set_page_config(page_title="SBC Jersey Creator", page_icon="👕", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root { color-scheme:light; }
.stApp,[data-testid="stAppViewContainer"] { background:#f5f7fb; color:#111827; }
[data-testid="stSidebar"],[data-testid="stSidebar"]>div { background:#fff !important; }
[data-testid="stSidebar"] *,[data-testid="stSidebar"] label,[data-testid="stSidebar"] p { color:#111827 !important; }
[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea,[data-testid="stSidebar"] [data-baseweb="select"]>div { background:#fff !important; color:#111827 !important; }
.block-container { max-width:1500px; padding-top:2rem; }
.uniform-kicker { color:#7c3aed; font-size:.78rem; font-weight:900; letter-spacing:.16em; text-transform:uppercase; }
.uniform-title { color:#111827; font-size:clamp(2rem,4vw,3.6rem); font-weight:950; line-height:1; margin:.25rem 0 .45rem; }
.uniform-copy { color:#64748b; font-size:1rem; font-weight:600; max-width:60rem; margin-bottom:1rem; }
</style>
""", unsafe_allow_html=True)

table = read_config_table()
st.markdown('<div class="uniform-kicker">SBC Design Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="uniform-title">Jersey Creator</div>', unsafe_allow_html=True)
st.markdown('<div class="uniform-copy">Build Association, Icon, and Statement uniforms from a focused set of repeatable league design choices.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Uniform controls")
    team = st.selectbox("Team", TEAMS)
    edition = st.segmented_control("Edition", EDITIONS, default="Association")
    if edition not in EDITIONS:
        edition = "Association"
    saved = table[(table["team"] == team) & (table["edition"] == edition)].iloc[0].to_dict()
    prefix = re.sub(r"[^a-z0-9]+", "_", f"{team}_{edition}".lower())

    with st.expander("Identity", expanded=True):
        wordmark = st.text_input("Front wordmark", value=str(saved["wordmark"]), key=f"{prefix}_wordmark")
        number = st.text_input("Preview number", value=str(saved["number"]), max_chars=2, key=f"{prefix}_number")
        player_name = st.text_input("Preview player name", value=str(saved["player_name"]), max_chars=14, key=f"{prefix}_name")
        saved_font_label = str(saved.get("wordmark_font") or team)
        font_label = st.selectbox("Uniform font", FONT_OPTIONS, index=FONT_OPTIONS.index(saved_font_label) if saved_font_label in FONT_OPTIONS else FONT_OPTIONS.index(team), key=f"{prefix}_font")
        font_family = TEAM_FONTS[font_label] if font_label in TEAM_FONTS else BASIC_FONTS[font_label]

    with st.expander("Uniform palette", expanded=True):
        st.caption(f"Team Color 1: {team_info[team]['bg']} · Team Color 2: {team_info[team]['bg2']}")
        jersey_color = palette_control("Jersey base", saved["jersey_color"], team, f"{prefix}_jersey")
        trim_color = palette_control("Trim", saved["trim_color"], team, f"{prefix}_trim")
        accent_color = palette_control("Stripe/accent", saved["accent_color"], team, f"{prefix}_accent")
        wordmark_color = palette_control("Wordmark", saved["wordmark_color"], team, f"{prefix}_wordmark_color")
        number_color = palette_control("Number", saved["number_color"], team, f"{prefix}_number_color")
        number_outline_color = palette_control("Number outline", saved["number_outline_color"], team, f"{prefix}_outline")
        player_name_color = palette_control("Player name", saved["player_name_color"], team, f"{prefix}_name_color")

    with st.expander("Jersey construction", expanded=True):
        collar_style = st.selectbox("Collar", COLLARS, index=option_index(COLLARS, saved.get("collar_style"), "Crew"), key=f"{prefix}_collar")
        stripe_style = st.selectbox("Jersey stripe", JERSEY_STRIPES, index=option_index(JERSEY_STRIPES, saved.get("stripe_style"), "None"), key=f"{prefix}_stripe")
        trim_width = st.select_slider("Trim weight", options=[1.2, 1.7, 2.2, 2.8, 3.4], value=float(saved["trim_width"]), key=f"{prefix}_trim_width")
        number_outline_width = st.select_slider("Number outline", options=[0.0, 1.0, 2.0, 3.0, 4.0], value=float(saved["number_outline_width"]), key=f"{prefix}_outline_width")

    with st.expander("Front text placement", expanded=True):
        front_wordmark_size = st.number_input("Wordmark font size", 15.0, TEXT_FONT_SIZE_MAX, float(saved.get("front_wordmark_size", 35)), 1.0, key=f"{prefix}_front_wordmark_size")
        front_wordmark_x = st.number_input("Wordmark horizontal position", -20.0, 20.0, float(saved.get("front_wordmark_x", 0)), .5, key=f"{prefix}_front_wordmark_x")
        front_wordmark_y = st.number_input("Wordmark vertical position", 8.0, 65.0, float(saved.get("front_wordmark_y", 29)), .5, key=f"{prefix}_front_wordmark_y")
        front_number_size = st.number_input("Front number font size", 30.0, NUMBER_FONT_SIZE_MAX, float(saved.get("front_number_size", 60)), 1.0, key=f"{prefix}_front_number_size")
        front_number_x = st.number_input("Front number horizontal position", -20.0, 20.0, float(saved.get("front_number_x", 8)), .5, key=f"{prefix}_front_number_x")
        front_number_y = st.number_input("Front number vertical position", 15.0, 68.0, float(saved.get("front_number_y", 45)), .5, key=f"{prefix}_front_number_y")

    with st.expander("Back text placement", expanded=True):
        back_name_size = st.number_input("Player-name font size", 15.0, TEXT_FONT_SIZE_MAX, float(saved.get("back_name_size", 36)), 1.0, key=f"{prefix}_back_name_size")
        back_name_x = st.number_input("Player-name horizontal position", -20.0, 20.0, float(saved.get("back_name_x", 0)), .5, key=f"{prefix}_back_name_x")
        back_name_y = st.number_input("Player-name vertical position", 8.0, 55.0, float(saved.get("back_name_y", 18)), .5, key=f"{prefix}_back_name_y")
        back_number_size = st.number_input("Back number font size", 40.0, NUMBER_FONT_SIZE_MAX, float(saved.get("back_number_size", 80)), 1.0, key=f"{prefix}_back_number_size")
        back_number_x = st.number_input("Back number horizontal position", -20.0, 20.0, float(saved.get("back_number_x", 0)), .5, key=f"{prefix}_back_number_x")
        back_number_y = st.number_input("Back number vertical position", 18.0, 68.0, float(saved.get("back_number_y", 43)), .5, key=f"{prefix}_back_number_y")

    with st.expander("Jersey logo and export", expanded=True):
        logo_options = ["None"] + TEAMS
        saved_logo = str(saved.get("logo_team") or team)
        logo_team = st.selectbox("Jersey logo", logo_options, index=logo_options.index(saved_logo) if saved_logo in logo_options else logo_options.index(team), key=f"{prefix}_logo")
        show_jersey_logo = st.toggle("Show jersey logo", bool_value(saved.get("show_jersey_logo", True)), key=f"{prefix}_show_logo")
        jersey_logo_scale = st.number_input("Jersey logo size", .05, 5.00, float(saved.get("jersey_logo_scale", .70)), .05, key=f"{prefix}_logo_scale")
        jersey_logo_x = st.number_input("Jersey logo horizontal position", -20.0, 20.0, float(saved.get("jersey_logo_x", 12)), .5, key=f"{prefix}_logo_x")
        jersey_logo_y = st.number_input("Jersey logo vertical position", -40.0, 120.0, float(saved.get("jersey_logo_y", 15)), .5, key=f"{prefix}_logo_y")
        show_league_mark = st.toggle("Show SBC chest mark", bool_value(saved["show_league_mark"]), key=f"{prefix}_league")
        export_format = st.selectbox("Download format", ["png", "svg"])
        transparent = st.toggle("Transparent background", False)

font_path, font_warning = "", ""
try:
    font_path = google_font_path(font_family)
except Exception as exc:
    font_warning = f"Selected font unavailable; showing a local fallback. {exc}"

config = JerseyConfig(
    team=team, edition=edition, jersey_color=jersey_color, shorts_color=jersey_color,
    trim_color=trim_color, accent_color=accent_color, wordmark_color=wordmark_color,
    number_color=number_color, number_outline_color=number_outline_color,
    player_name_color=player_name_color, stripe_style=stripe_style,
    shorts_stripe_style=str(saved.get("shorts_stripe_style", "None")), collar_style=collar_style,
    wordmark=wordmark, wordmark_font=font_label, font_family=font_family,
    font_path=font_path, number=number, player_name=player_name,
    number_outline_width=number_outline_width, trim_width=trim_width,
    logo_team="" if logo_team == "None" else logo_team,
    show_shorts_logo=False, show_league_mark=show_league_mark,
    front_wordmark_x=front_wordmark_x, front_wordmark_y=front_wordmark_y,
    front_wordmark_size=front_wordmark_size, front_number_x=front_number_x,
    front_number_y=front_number_y, front_number_size=front_number_size,
    back_name_x=back_name_x, back_name_y=back_name_y, back_name_size=back_name_size,
    back_number_x=back_number_x, back_number_y=back_number_y, back_number_size=back_number_size,
    jersey_logo_x=jersey_logo_x, jersey_logo_y=jersey_logo_y,
    jersey_logo_scale=jersey_logo_scale, show_jersey_logo=show_jersey_logo,
)
logo_source = team_info[logo_team]["logo"] if logo_team in team_info else None

preview_tab, gallery_tab, data_tab = st.tabs(["Uniform preview", "Edition gallery", "90-row configuration"])
with preview_tab:
    if font_warning:
        st.warning(font_warning)
    fig, _ = draw_uniform(config, logo=logo_source)
    st.pyplot(fig, use_container_width=True)
    download = figure_bytes(fig, export_format, transparent=transparent)
    plt.close(fig)
    safe_name = "_".join(f"{team}_{edition}".lower().split())
    save_col, image_col, json_col = st.columns(3)
    with save_col:
        if st.button(f"Save {team} {edition}", type="primary", use_container_width=True):
            row = config.to_dict()
            table.loc[(table["team"] == team) & (table["edition"] == edition), list(row)] = list(row.values())
            table.to_csv(CONFIG_PATH, index=False)
            st.success(f"Saved {team} {edition}")
    with image_col:
        st.download_button(f"Download {export_format.upper()}", download, file_name=f"{safe_name}.{export_format}", mime="image/png" if export_format == "png" else "image/svg+xml", use_container_width=True)
    with json_col:
        st.download_button("Download configuration", json.dumps(config.to_dict(), indent=2), file_name=f"{safe_name}.json", mime="application/json", use_container_width=True)

with gallery_tab:
    st.caption(f"All three editions. {edition} reflects your live controls; the other two show their saved designs.")
    columns = st.columns(3)
    for column, gallery_edition in zip(columns, EDITIONS):
        if gallery_edition == edition:
            gallery_config = config
            gallery_logo = logo_source
        else:
            row = table[(table["team"] == team) & (table["edition"] == gallery_edition)].iloc[0].to_dict()
            gallery_config = JerseyConfig.from_mapping(row)
            gallery_logo_team = str(row.get("logo_team") or team)
            gallery_logo = team_info[gallery_logo_team]["logo"] if gallery_logo_team in team_info else None
        gallery_fig, _ = draw_uniform(gallery_config, logo=gallery_logo, view="front")
        with column:
            st.subheader(gallery_edition)
            st.pyplot(gallery_fig, use_container_width=True)
        plt.close(gallery_fig)

with data_tab:
    st.subheader("League uniform configuration")
    st.caption(f"{len(table)} saved rows · 30 teams × 3 editions")
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button("Download all uniform configurations", table.to_csv(index=False), file_name="jersey_team_configs.csv", mime="text/csv")
