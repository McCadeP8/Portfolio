#!/usr/bin/env python3
"""Create a one-page portrait Utah Jazz + Mammoth season schedule poster."""

from __future__ import annotations

import argparse
import calendar
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


JAZZ_HOME = HexColor("#330072")
JAZZ_AWAY = HexColor("#010101")
MAMMOTH_HOME = HexColor("#69B3E7")
MAMMOTH_AWAY = HexColor("#964C18")

PAPER = HexColor("#F3F0E8")
INK = HexColor("#17171A")
MUTED = HexColor("#6D6B68")
GRID = HexColor("#D9D5CC")
EMPTY = HexColor("#FBFAF6")
WEEKEND = HexColor("#F6F3EC")
WHITE = HexColor("#FFFFFF")

LOGO_URLS = {
    "jazz": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/utah.png&h=600&w=600",
    "mammoth": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/uta.png&h=600&w=600",
}


@dataclass(frozen=True)
class Game:
    day: date
    league: str
    opponent: str
    away: bool

    @property
    def team(self) -> str:
        return "Jazz" if self.league == "NBA" else "Mammoth"

    @property
    def color(self):
        if self.league == "NBA":
            return JAZZ_AWAY if self.away else JAZZ_HOME
        return MAMMOTH_AWAY if self.away else MAMMOTH_HOME

    @property
    def text_color(self):
        return INK if self.league == "NHL" and not self.away else WHITE

    @property
    def matchup(self) -> str:
        return f"a{self.opponent}" if self.away else f"v{self.opponent}"


def register_fonts() -> tuple[str, str, str]:
    candidates = [
        (
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
            Path(r"C:\Windows\Fonts\segoeuib.ttf"),
            Path(r"C:\Windows\Fonts\segoeuisl.ttf"),
        ),
        (
            Path(r"C:\Windows\Fonts\arial.ttf"),
            Path(r"C:\Windows\Fonts\arialbd.ttf"),
            Path(r"C:\Windows\Fonts\ariali.ttf"),
        ),
    ]
    for regular, bold, italic in candidates:
        if regular.exists() and bold.exists() and italic.exists():
            pdfmetrics.registerFont(TTFont("PosterSans", str(regular)))
            pdfmetrics.registerFont(TTFont("PosterSans-Bold", str(bold)))
            pdfmetrics.registerFont(TTFont("PosterSans-Italic", str(italic)))
            return "PosterSans", "PosterSans-Bold", "PosterSans-Italic"
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


FONT, BOLD, ITALIC = register_fonts()


def load_games(csv_path: Path) -> dict[date, list[Game]]:
    by_day: dict[date, list[Game]] = defaultdict(list)
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            day = datetime.strptime(row["Date"].strip(), "%m/%d/%Y").date()
            raw = row["Game"].strip()
            # The CSV uses a lowercase "a" prefix for away games. Keep this
            # case-sensitive so home opponents such as ANA and ATL stay home.
            away = raw.startswith("a")
            opponent = raw[1:] if away else raw
            league = row["League"].strip().upper()
            if league not in {"NBA", "NHL"}:
                raise ValueError(f"Unexpected league {league!r} on {day}")
            by_day[day].append(Game(day, league, opponent.upper(), away))

    all_games = [game for games in by_day.values() for game in games]
    allowed_counts = {"NBA": {82}, "NHL": {82, 84}}
    actual = {league: sum(g.league == league for g in all_games) for league in allowed_counts}
    invalid = {
        league: count
        for league, count in actual.items()
        if count not in allowed_counts[league]
    }
    if invalid:
        raise ValueError(
            f"Unexpected schedule lengths {actual}; expected NBA=82 and NHL=82 or 84"
        )
    if any(len(games) > 2 for games in by_day.values()):
        raise ValueError("Calendar layout supports at most two games on one date")
    for games in by_day.values():
        games.sort(key=lambda game: 0 if game.league == "NBA" else 1)
    return by_day


def season_info(games: dict[date, list[Game]]) -> tuple[int, str]:
    """Return the fall start year and display label inferred from schedule dates."""
    season_years = {day.year if day.month >= 7 else day.year - 1 for day in games}
    if len(season_years) != 1:
        raise ValueError(f"Schedule dates cross season boundaries: {sorted(season_years)}")
    start_year = season_years.pop()
    return start_year, f"{start_year}-{str(start_year + 1)[-2:]}"


def get_logo(kind: str, logo_dir: Path | None) -> ImageReader:
    filename = f"utah_{kind}_logo.png"
    if logo_dir:
        local = logo_dir / filename
        if local.exists():
            return ImageReader(str(local))
    req = Request(LOGO_URLS[kind], headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as response:
        return ImageReader(BytesIO(response.read()))


def rounded_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, radius: float = 10) -> None:
    c.setFillColor(Color(0, 0, 0, alpha=0.09))
    c.roundRect(x + 3, y - 3, w, h, radius, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=0)


def draw_header(
    c: canvas.Canvas,
    width: float,
    height: float,
    jazz_logo: ImageReader,
    mammoth_logo: ImageReader,
    season_label: str,
) -> None:
    c.setFillColor(INK)
    c.rect(0, height - 118, width, 118, fill=1, stroke=0)
    c.setFillColor(JAZZ_HOME)
    c.rect(0, height - 8, width / 2, 8, fill=1, stroke=0)
    c.setFillColor(MAMMOTH_HOME)
    c.rect(width / 2, height - 8, width / 2, 8, fill=1, stroke=0)

    logo_size = 74
    center = width / 2
    c.drawImage(jazz_logo, center - 325, height - 103, logo_size, logo_size, preserveAspectRatio=True, mask="auto")
    c.drawImage(mammoth_logo, center + 251, height - 103, logo_size, logo_size, preserveAspectRatio=True, mask="auto")

    c.setFillColor(WHITE)
    c.setFont(BOLD, 32)
    c.drawCentredString(center, height - 50, "UTAH BASKETBALL + HOCKEY")
    c.setFillColor(HexColor("#C9C6BE"))
    c.setFont(FONT, 14)
    c.drawCentredString(center, height - 76, "JAZZ  /  MAMMOTH")
    c.setFont(BOLD, 13)
    c.setFillColor(HexColor("#ECE9E1"))
    c.drawCentredString(center, height - 98, f"{season_label} REGULAR SEASON")


def draw_game_half(c: canvas.Canvas, game: Game, x: float, y: float, w: float, h: float, day_num: int | None) -> None:
    c.setFillColor(game.color)
    c.rect(x, y, w, h, fill=1, stroke=0)
    pad = 6
    c.setFillColor(game.text_color)
    if day_num is not None:
        c.setFont(BOLD, 9.2)
        c.drawRightString(x + w - pad, y + h - 11, str(day_num))
    c.setFont(BOLD, 14.0 if h > 34 else 10.8)
    c.drawCentredString(x + w / 2, y + h / 2 - 4, game.matchup)


def draw_day_cell(c: canvas.Canvas, x: float, y: float, w: float, h: float, day_num: int, games: list[Game], weekend: bool) -> None:
    if not games:
        c.setFillColor(WEEKEND if weekend else EMPTY)
        c.rect(x, y, w, h, fill=1, stroke=0)
        c.setFillColor(MUTED)
        c.setFont(BOLD, 9.2)
        c.drawRightString(x + w - 5, y + h - 11, str(day_num))
    elif len(games) == 1:
        draw_game_half(c, games[0], x, y, w, h, day_num)
    else:
        half = h / 2
        # Jazz always occupies the upper half; Mammoth the lower half.
        for index, game in enumerate(games):
            gy = y + half if index == 0 else y
            draw_game_half(c, game, x, gy, w, half, day_num if index == 0 else None)
        c.setStrokeColor(Color(1, 1, 1, alpha=0.65))
        c.setLineWidth(0.7)
        c.line(x, y + half, x + w, y + half)

    c.setStrokeColor(GRID)
    c.setLineWidth(0.45)
    c.rect(x, y, w, h, fill=0, stroke=1)


def draw_combined_day_cell(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    first_day: int,
    first_games: list[Game],
    second_day: int,
    second_games: list[Game],
) -> None:
    """Draw two calendar dates in one conventional split cell."""
    half = h / 2
    for index, (day_num, daily_games) in enumerate(
        ((first_day, first_games), (second_day, second_games))
    ):
        gy = y + half if index == 0 else y
        if len(daily_games) == 1:
            draw_game_half(c, daily_games[0], x, gy, w, half, day_num)
        elif len(daily_games) == 2:
            # In an already stacked 24/31 calendar cell, put same-date Jazz
            # and Mammoth games side by side so the text remains legible.
            game_half = w / 2
            for game_index, game in enumerate(daily_games):
                game_x = x + game_index * game_half
                c.setFillColor(game.color)
                c.rect(game_x, gy, game_half, half, fill=1, stroke=0)
                c.setFillColor(game.text_color)
                c.setFont(BOLD, 8.2)
                c.drawCentredString(game_x + game_half / 2, gy + 3, game.matchup)
            # One neutral date badge applies to both side-by-side games.
            badge_w = 13
            badge_h = 9
            c.setFillColor(PAPER)
            c.roundRect(x + w - badge_w - 2, gy + half - badge_h - 2, badge_w, badge_h, 2, fill=1, stroke=0)
            c.setFillColor(INK)
            c.setFont(BOLD, 6.8)
            c.drawCentredString(x + w - badge_w / 2 - 2, gy + half - badge_h, str(day_num))
            c.setStrokeColor(Color(1, 1, 1, alpha=0.72))
            c.setLineWidth(0.6)
            c.line(x + game_half, gy, x + game_half, gy + half)
        else:
            c.setFillColor(WEEKEND)
            c.rect(x, gy, w, half, fill=1, stroke=0)
            c.setFillColor(MUTED)
            c.setFont(BOLD, 9.2)
            c.drawRightString(x + w - 6, gy + half - 11, str(day_num))
    c.setStrokeColor(Color(1, 1, 1, alpha=0.72))
    c.setLineWidth(0.8)
    c.line(x, y + half, x + w, y + half)
    c.setStrokeColor(GRID)
    c.setLineWidth(0.45)
    c.rect(x, y, w, h, fill=0, stroke=1)


def draw_month(
    c: canvas.Canvas,
    year: int,
    month: int,
    games: dict[date, list[Game]],
    x: float,
    y: float,
    w: float,
    h: float,
    visible_weeks: int = 6,
    max_day: int | None = None,
    combined_days: tuple[int, int] | None = None,
) -> None:
    rounded_card(c, x, y, w, h)
    inner_x = x + 10
    inner_y = y + 10
    inner_w = w - 20
    inner_h = h - 20
    title_h = 34
    weekday_h = 18
    grid_h = inner_h - title_h - weekday_h
    cell_w = inner_w / 7
    cell_h = grid_h / visible_weeks

    c.setFillColor(INK)
    c.setFont(BOLD, 20)
    c.drawString(inner_x, inner_y + inner_h - 23, calendar.month_name[month].upper())
    c.setFillColor(MUTED)
    c.setFont(BOLD, 9.5)
    c.drawRightString(inner_x + inner_w, inner_y + inner_h - 20, str(year))
    line_y = inner_y + inner_h - title_h + 1
    c.setFillColor(JAZZ_HOME)
    c.rect(inner_x, line_y, inner_w / 2, 3, fill=1, stroke=0)
    c.setFillColor(MAMMOTH_HOME)
    c.rect(inner_x + inner_w / 2, line_y, inner_w / 2, 3, fill=1, stroke=0)

    weekdays = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    c.setFont(BOLD, 8.5)
    for col, label in enumerate(weekdays):
        c.setFillColor(MUTED if col not in {0, 6} else HexColor("#4A4947"))
        c.drawCentredString(inner_x + (col + 0.5) * cell_w, line_y - 12, label)

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)
    while len(weeks) < visible_weeks:
        weeks.append([0] * 7)
    grid_top = inner_y + grid_h
    for row, week in enumerate(weeks[:visible_weeks]):
        cy = grid_top - (row + 1) * cell_h
        for col, day_num in enumerate(week):
            cx = inner_x + col * cell_w
            if combined_days and day_num == combined_days[0]:
                first_day, second_day = combined_days
                draw_combined_day_cell(
                    c,
                    cx,
                    cy,
                    cell_w,
                    cell_h,
                    first_day,
                    games.get(date(year, month, first_day), []),
                    second_day,
                    games.get(date(year, month, second_day), []),
                )
            elif day_num and (max_day is None or day_num <= max_day):
                the_day = date(year, month, day_num)
                draw_day_cell(c, cx, cy, cell_w, cell_h, day_num, games.get(the_day, []), col in {0, 6})
            else:
                c.setFillColor(PAPER)
                c.rect(cx, cy, cell_w, cell_h, fill=1, stroke=0)


def swatch(c: canvas.Canvas, x: float, y: float, color, text_color, label: str, detail: str) -> None:
    c.setFillColor(color)
    c.roundRect(x, y, 102, 34, 6, fill=1, stroke=0)
    c.setFillColor(text_color)
    c.setFont(BOLD, 9)
    c.drawString(x + 8, y + 19, label)
    c.setFont(FONT, 8)
    c.drawString(x + 8, y + 8, detail)


def draw_legend(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    jazz_logo: ImageReader,
    mammoth_logo: ImageReader,
    games: dict[date, list[Game]],
) -> None:
    rounded_card(c, x, y, w, h)
    pad = 18
    c.setFillColor(INK)
    c.setFont(BOLD, 20)
    c.drawString(x + pad, y + h - 33, "SEASON KEY")
    c.setFillColor(MUTED)
    c.setFont(FONT, 9.5)
    all_games = [game for daily_games in games.values() for game in daily_games]
    shared_dates = sum(
        {game.league for game in daily_games} == {"NBA", "NHL"}
        for daily_games in games.values()
    )
    start_year, _ = season_info(games)
    display_start = date(start_year, 10, 1)
    display_end = date(start_year + 1, 4, 11)
    occupied_dates = {
        game_day for game_day in games if display_start <= game_day <= display_end
    }
    empty_days = (display_end - display_start).days + 1 - len(occupied_dates)
    c.drawRightString(
        x + w - pad,
        y + h - 30,
        f"{len(all_games)} GAMES  /  {shared_dates} SHARED DATES  /  {empty_days} EMPTY DAYS",
    )

    rule_y = y + h - 46
    c.setFillColor(JAZZ_HOME)
    c.rect(x + pad, rule_y, (w - 2 * pad) / 2, 3, fill=1, stroke=0)
    c.setFillColor(MAMMOTH_HOME)
    c.rect(x + pad + (w - 2 * pad) / 2, rule_y, (w - 2 * pad) / 2, 3, fill=1, stroke=0)

    # Compact two-column team summary keeps the shortened fourth row useful.
    team_y = y + h - 105
    team_col_w = (w - 2 * pad) / 2
    c.drawImage(jazz_logo, x + 22, team_y, 48, 48, preserveAspectRatio=True, mask="auto")
    c.setFillColor(INK)
    c.setFont(BOLD, 15.5)
    c.drawString(x + 78, team_y + 30, "UTAH JAZZ")
    c.setFont(FONT, 9.5)
    c.setFillColor(MUTED)
    jazz_home = sum(game.league == "NBA" and not game.away for game in all_games)
    jazz_road = sum(game.league == "NBA" and game.away for game in all_games)
    c.drawString(x + 78, team_y + 14, f"NBA  /  {jazz_home} HOME  /  {jazz_road} ROAD")

    mammoth_x = x + pad + team_col_w
    c.drawImage(mammoth_logo, mammoth_x + 4, team_y, 48, 48, preserveAspectRatio=True, mask="auto")
    c.setFillColor(INK)
    c.setFont(BOLD, 15.5)
    c.drawString(mammoth_x + 60, team_y + 30, "UTAH MAMMOTH")
    c.setFont(FONT, 9.5)
    c.setFillColor(MUTED)
    mammoth_home = sum(game.league == "NHL" and not game.away for game in all_games)
    mammoth_road = sum(game.league == "NHL" and game.away for game in all_games)
    c.drawString(mammoth_x + 60, team_y + 14, f"NHL  /  {mammoth_home} HOME  /  {mammoth_road} ROAD")

    swatch_y = y + 24
    gap = 8
    total_w = 4 * 102 + 3 * gap
    start_x = x + (w - total_w) / 2
    swatch(c, start_x, swatch_y, JAZZ_HOME, WHITE, "JAZZ HOME", "vABC")
    swatch(c, start_x + 102 + gap, swatch_y, JAZZ_AWAY, WHITE, "JAZZ ROAD", "aABC")
    swatch(c, start_x + 2 * (102 + gap), swatch_y, MAMMOTH_HOME, INK, "MAMMOTH HOME", "vABC")
    swatch(c, start_x + 3 * (102 + gap), swatch_y, MAMMOTH_AWAY, WHITE, "MAMMOTH ROAD", "aABC")


def build(csv_path: Path, output_path: Path | None, logo_dir: Path | None) -> Path:
    games = load_games(csv_path)
    start_year, season_label = season_info(games)
    if output_path is None:
        output_path = csv_path.with_name(f"Utah_Jazz_Mammoth_{season_label}_Calendar.pdf")
    jazz_logo = get_logo("jazz", logo_dir)
    mammoth_logo = get_logo("mammoth", logo_dir)

    # Five-row months plus the shortened April/key row make a compact social image.
    page_size = (18 * 72, 18.625 * 72)
    width, height = page_size
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=page_size, pageCompression=1)
    c.setTitle(f"{season_label} Utah Jazz and Utah Mammoth Schedule")
    c.setAuthor("Utah Basketball + Hockey Calendar")
    c.setSubject("Combined regular-season schedule")
    c.setFillColor(PAPER)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    draw_header(c, width, height, jazz_logo, mammoth_logo, season_label)

    margin_x = 28
    gap_x = 16
    gap_y = 14
    footer_h = 25
    header_bottom = height - 118
    calendar_top = header_bottom - 18
    card_w = (width - 2 * margin_x - gap_x) / 2
    bottom_h = 190
    card_h = (calendar_top - footer_h - 3 * gap_y - bottom_h) / 3

    months = [(start_year, month) for month in (10, 11, 12)] + [
        (start_year + 1, month) for month in (1, 2, 3, 4)
    ]
    for index, (year, month) in enumerate(months):
        row = index // 2
        col = index % 2
        x = margin_x + col * (card_w + gap_x)
        if row < 3:
            y = calendar_top - (row + 1) * card_h - row * gap_y
            combined = (24, 31) if month == 1 else None
            draw_month(
                c,
                year,
                month,
                games,
                x,
                y,
                card_w,
                card_h,
                visible_weeks=5,
                combined_days=combined,
            )
        else:
            y = footer_h
            draw_month(c, year, month, games, x, y, card_w, bottom_h, visible_weeks=3, max_day=11)

    legend_x = margin_x + card_w + gap_x
    legend_y = footer_h
    draw_legend(c, legend_x, legend_y, card_w, bottom_h, jazz_logo, mammoth_logo, games)

    c.setFillColor(MUTED)
    c.setFont(FONT, 8)
    c.drawString(margin_x, 10, "Schedule data: UHTSchedule.csv  /  Team abbreviations follow source data")
    c.drawRightString(width - margin_x, 10, "Times not listed  /  Schedule subject to change")
    c.showPage()
    c.save()
    return output_path


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=script_dir / "UHTSchedule.csv")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output PDF path; defaults to a season-specific filename beside the CSV",
    )
    parser.add_argument("--logo-dir", type=Path, default=script_dir)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output = build(args.csv, args.output, args.logo_dir)
    print(output.resolve())
