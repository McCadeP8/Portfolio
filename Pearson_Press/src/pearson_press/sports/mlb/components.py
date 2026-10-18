"""Compact, one-column MLB newspaper components."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape

from reportlab.lib.colors import black
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


@dataclass(frozen=True)
class MLBBatterLine:
    name: str
    ab: str
    runs: str
    hits: str
    rbi: str
    walks: str
    strikeouts: str
    substitute: bool = False


@dataclass(frozen=True)
class MLBPitcherLine:
    name: str
    innings: str
    hits: str
    runs: str
    earned_runs: str
    walks: str
    strikeouts: str
    pitches_strikes: str
    decision: str = ""


@dataclass(frozen=True)
class MLBTeamBox:
    location: str
    nickname: str
    abbreviation: str
    score: int
    record: str
    innings: tuple[str, ...]
    hits: int
    errors: int
    batters: tuple[MLBBatterLine, ...]
    batting_totals: tuple[str, str, str, str, str, str]
    doubles: tuple[str, ...]
    triples: tuple[str, ...]
    home_runs: tuple[str, ...]
    stolen_bases: tuple[str, ...]
    error_players: tuple[str, ...]
    pitchers: tuple[MLBPitcherLine, ...]
    lob: int
    double_plays: int


@dataclass(frozen=True)
class MLBSimpleBoxScore:
    away: MLBTeamBox
    home: MLBTeamBox
    venue: str
    city: str
    state: str
    umpires: tuple[str, ...]
    attendance: int

    @property
    def innings_played(self) -> int:
        return max(len(self.away.innings), len(self.home.innings), 9)

    @property
    def headline(self) -> str:
        winner, loser = sorted((self.away, self.home), key=lambda team: team.score, reverse=True)
        suffix = f" ({self.innings_played})" if self.innings_played > 9 else ""
        return f"{winner.nickname} {winner.score}, {loser.nickname} {loser.score}{suffix}"


@dataclass(frozen=True)
class MLBStandingRow:
    division_code: str
    seed: int
    team: str
    record: str
    pct: str
    games_behind: str
    home: str
    away: str
    runs_scored: str
    runs_allowed: str
    streak: str
    last_ten: str
    clinch: str = ""

    @property
    def team_label(self) -> str:
        return f"{self.clinch}-{self.team}" if self.clinch else self.team

    @property
    def rank_label(self) -> str:
        if self.seed <= 3:
            return self.division_code
        return str(self.seed) if self.seed <= 6 else ""


def draw_mlb_standings_league(
    pdf: Canvas,
    title: str,
    rows: Sequence[MLBStandingRow],
    x: float,
    top: float,
    width: float,
    *,
    row_height: float = 17.2,
    regular_font: str = "PP-Narrow",
    bold_font: str = "PP-Narrow-Bold",
) -> float:
    """Draw a complete 15-team league in one newspaper column."""

    registered = pdfmetrics.getRegisteredFontNames()
    regular = regular_font if regular_font in registered else "Helvetica"
    bold = bold_font if bold_font in registered else "Helvetica-Bold"
    left = x + 2.0
    usable = width - 4.0
    widths = (0.05, 0.19, 0.125, 0.09, 0.07, 0.105, 0.105, 0.065, 0.065, 0.065, 0.07)
    scale = usable / sum(widths)
    edges = []
    edge = left
    for fraction in widths:
        edge += fraction * scale
        edges.append(edge)

    pdf.setFont(bold, 7.0)
    pdf.drawString(left, top, title.upper())
    top -= 5.0
    pdf.setLineWidth(0.48)
    pdf.line(left, top, x + width - 2.0, top)
    top -= 5.3

    headings = ("RK", "TEAM", "W-L", "PCT", "GB", "HOME", "AWAY", "RS", "RA", "STRK", "L10")
    pdf.setFont(bold, 2.95)
    previous = left
    for index, (right, heading) in enumerate(zip(edges, headings, strict=True)):
        if index == 1:
            pdf.drawString(previous + 0.8, top, heading)
        else:
            pdf.drawRightString(right, top, heading)
        previous = right
    top -= 2.5
    pdf.setLineWidth(0.2)
    pdf.line(left, top, x + width - 2.0, top)
    top -= 5.0

    for index, row in enumerate(rows):
        values = (
            row.rank_label, row.team_label, row.record, row.pct, row.games_behind,
            row.home, row.away, row.runs_scored, row.runs_allowed, row.streak, row.last_ten,
        )
        pdf.setFont(regular, 3.45)
        previous = left
        for column, (right, value) in enumerate(zip(edges, values, strict=True)):
            if column == 1:
                _fit_name(pdf, value, previous + 0.8, top, right - previous - 1.2, regular, 3.45)
            else:
                pdf.setFont(regular, 3.45)
                pdf.drawRightString(right, top, value)
            previous = right
        top -= row_height
        if index < len(rows) - 1:
            pdf.setLineWidth(0.8 if index == 5 else 0.12)
            pdf.line(left, top + row_height / 2 - 0.2, x + width - 2.0, top + row_height / 2 - 0.2)
    return top


def _surname(name: str) -> str:
    parts = name.split()
    suffixes = {"Jr.", "Sr.", "II", "III", "IV"}
    if len(parts) > 2 and parts[-1] in suffixes:
        return f"{parts[-2]} {parts[-1]}"
    return parts[-1]


def _paragraph(
    pdf: Canvas,
    text: str,
    x: float,
    top: float,
    width: float,
    *,
    font: str,
    size: float = 4.05,
    leading: float = 4.7,
) -> float:
    style = ParagraphStyle(
        "mlb-compact",
        fontName=font,
        fontSize=size,
        leading=leading,
        alignment=TA_LEFT,
        textColor=black,
        spaceBefore=0,
        spaceAfter=0,
    )
    paragraph = Paragraph(text, style)
    _, height = paragraph.wrap(width, 200)
    paragraph.drawOn(pdf, x, top - height)
    return top - height


def _fit_name(pdf: Canvas, text: str, x: float, y: float, width: float, font: str, size: float) -> None:
    fitted = size
    while fitted > 3.2 and pdf.stringWidth(text, font, fitted) > width:
        fitted -= 0.15
    pdf.setFont(font, fitted)
    pdf.drawString(x, y, text)


def _draw_batting_team(
    pdf: Canvas,
    team: MLBTeamBox,
    x: float,
    top: float,
    width: float,
    *,
    row_height: float,
    regular: str,
    bold: str,
) -> float:
    pdf.setFont(bold, 5.1)
    pdf.drawString(x, top, f"{team.location.upper()} ({team.record})")
    top -= 5.2

    name_width = width * 0.48
    value_width = (width - name_width) / 6
    edges = [x + name_width + value_width * (index + 1) for index in range(6)]
    pdf.setFont(bold, 3.3)
    pdf.drawString(x, top, "BATTER")
    for edge, heading in zip(edges, ("AB", "R", "H", "RBI", "BB", "K"), strict=True):
        pdf.drawRightString(edge, top, heading)
    top -= 4.2  # batter lines sit snug under their headings

    for batter in team.batters:
        label = f"a-{_surname(batter.name)}" if batter.substitute else _surname(batter.name)
        _fit_name(pdf, label, x, top, name_width - 2.0, regular, 4.25)
        pdf.setFont(regular, 4.25)
        values = (batter.ab, batter.runs, batter.hits, batter.rbi, batter.walks, batter.strikeouts)
        for edge, value in zip(edges, values, strict=True):
            pdf.drawRightString(edge, top, value)
        top -= row_height

    pdf.setLineWidth(0.22)
    pdf.line(x, top + row_height - 1.3, x + width, top + row_height - 1.3)
    top -= 0.9  # the total drops a touch below its rule
    pdf.setFont(bold, 4.15)
    pdf.drawString(x, top, "TOTAL")
    for edge, value in zip(edges, team.batting_totals, strict=True):
        pdf.drawRightString(edge, top, value)
    top -= 1.6  # the extra-base line follows the total with no blank line

    def listed(values: Sequence[str]) -> str:
        return ", ".join(values) if values else "None"

    details = (
        f"<b>2B</b> {escape(listed(team.doubles))}; <b>3B</b> {escape(listed(team.triples))}; "
        f"<b>HR</b> {escape(listed(team.home_runs))}; <b>SB</b> {escape(listed(team.stolen_bases))}; "
        f"<b>E</b> {escape(listed(team.error_players))}"
    )
    top = _paragraph(pdf, details, x, top, width, font=regular, size=3.85, leading=4.45)
    # A hairline closes the team before the next team or the pitching starts.
    pdf.setLineWidth(0.22)
    pdf.line(x, top - 1.2, x + width, top - 1.2)
    return top - 2.4


def _draw_section_heading(pdf: Canvas, title: str, x: float, top: float, width: float, bold: str) -> float:
    """Draw a ruled section heading and return the baseline of the rule."""

    pdf.setFont(bold, 5.3)
    pdf.drawString(x, top, title)
    pdf.setLineWidth(0.3)
    pdf.line(x, top - 2.0, x + width, top - 2.0)
    return top - 2.0


def _register_narrow_family(regular: str, bold: str) -> None:
    """Let <b> inside paragraphs switch to the narrow bold face."""

    if regular != "Helvetica":
        pdfmetrics.registerFontFamily(regular, normal=regular, bold=bold, italic=regular, boldItalic=bold)


def _draw_innings_value(
    pdf: Canvas,
    value: str,
    right: float,
    baseline: float,
    regular: str,
    size: float,
) -> None:
    """Render ESPN's .1/.2 outs as small newspaper-style 1/3 and 2/3 fractions."""

    whole, dot, outs = value.partition(".")
    if not dot or outs not in {"1", "2"}:
        pdf.setFont(regular, size)
        pdf.drawRightString(right, baseline, value.rstrip(".0") or "0")
        return
    fraction = "1/3" if outs == "1" else "2/3"
    fraction_size = size * 0.66
    fraction_width = pdf.stringWidth(fraction, regular, fraction_size)
    pdf.setFont(regular, fraction_size)
    pdf.drawRightString(right, baseline + size * 0.27, fraction)
    if whole != "0":
        pdf.setFont(regular, size)
        pdf.drawRightString(right - fraction_width - 0.6, baseline, whole)


def _draw_pitching_team(
    pdf: Canvas,
    team: MLBTeamBox,
    x: float,
    top: float,
    width: float,
    *,
    row_height: float,
    regular: str,
    bold: str,
) -> float:
    pdf.setFont(bold, 5.1)
    pdf.drawString(x, top, team.location.upper())
    top -= 5.2
    name_width = width * 0.40
    fractions = (0.105, 0.07, 0.07, 0.07, 0.07, 0.07, 0.145)
    usable = width - name_width
    scale = usable / sum(fractions)
    edges = []
    edge = x + name_width
    for fraction in fractions:
        edge += fraction * scale
        edges.append(edge)

    pdf.setFont(bold, 3.15)
    pdf.drawString(x, top, "PITCHER")
    for edge, heading in zip(edges, ("IP", "H", "R", "ER", "BB", "K", "PT-ST"), strict=True):
        pdf.drawRightString(edge, top, heading)
    top -= 4.3
    for pitcher in team.pitchers:
        label = _surname(pitcher.name)
        if pitcher.decision:
            label += f" ({pitcher.decision})"
        _fit_name(pdf, label, x, top, name_width - 1.5, regular, 4.0)
        values = (
            pitcher.innings, pitcher.hits, pitcher.runs, pitcher.earned_runs,
            pitcher.walks, pitcher.strikeouts, pitcher.pitches_strikes,
        )
        _draw_innings_value(pdf, values[0], edges[0], top, regular, 4.0)
        pdf.setFont(regular, 4.0)
        for edge, value in zip(edges[1:], values[1:], strict=True):
            pdf.drawRightString(edge, top, value)
        top -= row_height
    return top - 0.8


def _draw_line_score(
    pdf: Canvas,
    game: MLBSimpleBoxScore,
    x: float,
    top: float,
    width: float,
    *,
    regular: str,
    bold: str,
) -> float:
    top = _draw_section_heading(pdf, "LINE SCORE", x, top, width, bold)
    top -= 4.6

    innings = game.innings_played
    name_width = width * 0.25
    group_gap = 2.2
    group_breaks = sum(1 for inning in range(1, innings) if inning % 3 == 0)
    value_width = (width - name_width - group_gap * group_breaks) / (innings + 3)
    edges = []
    edge = x + name_width
    for index in range(innings + 3):
        if index < innings and index > 0 and index % 3 == 0:
            edge += group_gap
        edge += value_width
        edges.append(edge)

    headings = tuple(str(index) for index in range(1, innings + 1)) + ("R", "H", "E")
    header_size = 2.85 if innings > 9 else 3.25
    pdf.setFont(bold, header_size)
    for edge, heading in zip(edges, headings, strict=True):
        pdf.drawRightString(edge, top, heading)
    top -= 4.6

    for team, is_home in ((game.away, False), (game.home, True)):
        pdf.setFont(regular, 3.9)
        pdf.drawString(x, top, team.location)
        values = list(team.innings)
        while len(values) < innings:
            values.append("x" if is_home and team.score > game.away.score and len(values) == innings - 1 else "-")
        values.extend((str(team.score), str(team.hits), str(team.errors)))
        value_size = 3.1 if innings > 9 else 3.55
        pdf.setFont(regular, value_size)
        for edge, value in zip(edges, values, strict=True):
            pdf.drawRightString(edge, top, value)
        top -= 5.0
    return top


def draw_mlb_simple_box_score(
    pdf: Canvas,
    game: MLBSimpleBoxScore,
    x: float,
    top: float,
    width: float,
    *,
    batting_row_height: float = 4.8,
    pitching_row_height: float = 4.8,
    section_gap: float = 0.6,
    regular_font: str = "PP-Narrow",
    bold_font: str = "PP-Narrow-Bold",
) -> float:
    """Draw a complete MLB simple box in one newspaper column."""

    registered = pdfmetrics.getRegisteredFontNames()
    regular = regular_font if regular_font in registered else "Helvetica"
    bold = bold_font if bold_font in registered else "Helvetica-Bold"
    left = x + 2.0
    usable = width - 4.0

    pdf.setFont("Helvetica-Bold", 7.1)
    pdf.drawCentredString(x + width / 2, top - 7.0, game.headline)
    top -= 10.6
    pdf.setLineWidth(0.6)
    pdf.line(left, top, x + width - 2.0, top)
    top -= 5.7 + section_gap
    _register_narrow_family(regular, bold)

    # Batting and pitching share one structure: a ruled section heading, then
    # an unruled team label over each team's table.
    top = _draw_section_heading(pdf, "BATTING", left, top, usable, bold)
    top -= 5.0
    for index, team in enumerate((game.away, game.home)):
        top = _draw_batting_team(
            pdf, team, left, top, usable,
            row_height=batting_row_height, regular=regular, bold=bold,
        )
        top -= (3.6 if index == 0 else 2.8) + section_gap

    top = _draw_section_heading(pdf, "PITCHING", left, top - 2.0, usable, bold)
    top -= 4.5 + section_gap
    for team in (game.away, game.home):
        top = _draw_pitching_team(
            pdf, team, left, top, usable,
            row_height=pitching_row_height, regular=regular, bold=bold,
        )
        top -= 1.2 + section_gap

    top = _draw_section_heading(pdf, "TEAM STATS", left, top - 2.0, usable, bold)
    top -= 1.6
    for team in (game.away, game.home):
        text = f"<b>{escape(team.abbreviation)}:</b> LOB {team.lob}, DP Turned {team.double_plays}"
        top = _paragraph(pdf, text, left, top, usable, font=regular, size=4.05, leading=4.7)
        top -= 0.5

    top -= 5.0 + section_gap
    top = _draw_line_score(pdf, game, left, top, usable, regular=regular, bold=bold)
    top -= 1.4 + section_gap
    pdf.setLineWidth(0.28)
    pdf.line(left, top, x + width - 2.0, top)
    top -= 4.3
    top = _paragraph(
        pdf, escape(f"{game.venue}, {game.city}, {game.state}"),
        left, top, usable, font=regular, size=4.05, leading=4.7,
    )
    top -= 0.5
    top = _paragraph(
        pdf, f"<b>Umpires:</b> {escape(', '.join(game.umpires))}",
        left, top, usable, font=regular, size=3.85, leading=4.45,
    )
    top -= 0.5
    return _paragraph(
        pdf, f"<b>Attendance:</b> {game.attendance:,}",
        left, top, usable, font=regular, size=4.05, leading=4.7,
    )


__all__ = (
    "MLBBatterLine",
    "MLBPitcherLine",
    "MLBSimpleBoxScore",
    "MLBStandingRow",
    "MLBTeamBox",
    "draw_mlb_simple_box_score",
    "draw_mlb_standings_league",
)
