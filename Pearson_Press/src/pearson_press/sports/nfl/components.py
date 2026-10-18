"""Compact, one-column NFL newspaper components."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import escape

from reportlab.lib.colors import black
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


@dataclass(frozen=True)
class NFLPlayerLine:
    name: str
    values: tuple[str, ...]


@dataclass(frozen=True)
class NFLTeamBox:
    location: str
    nickname: str
    abbreviation: str
    score: int
    record: str
    quarter_scores: tuple[int, ...]
    passing: tuple[NFLPlayerLine, ...]
    rushing: tuple[NFLPlayerLine, ...]
    receiving: tuple[NFLPlayerLine, ...]
    kicking: tuple[NFLPlayerLine, ...]
    sacks: tuple[str, ...]
    interceptions: tuple[str, ...]
    kick_returns: tuple[str, ...]
    punt_returns: tuple[str, ...]
    other_touchdowns: tuple[str, ...]
    team_stats: Mapping[str, str]
    display_name: str | None = None
    rank: int | None = None
    # Distances in yards, e.g. ("Smack 38",) or ("Smack 38, 45",).
    field_goals_made: tuple[str, ...] = ()
    field_goals_missed: tuple[str, ...] = ()


@dataclass(frozen=True)
class NFLSimpleBoxScore:
    away: NFLTeamBox
    home: NFLTeamBox
    venue: str
    city: str
    state: str
    officials: tuple[str, ...]
    attendance: int

    @property
    def headline(self) -> str:
        winner, loser = sorted((self.away, self.home), key=lambda team: team.score, reverse=True)

        def label(team: NFLTeamBox) -> str:
            name = team.display_name or team.nickname
            return f"No. {team.rank} {name}" if team.rank is not None and team.rank <= 25 else name

        overtime = max(len(self.away.quarter_scores), len(self.home.quarter_scores)) - 4
        suffix = " (OT)" if overtime == 1 else f" ({overtime}OT)" if overtime > 1 else ""
        return f"{label(winner)} {winner.score}, {label(loser)} {loser.score}{suffix}"


@dataclass(frozen=True)
class NFLStandingRow:
    seed: int
    division_code: str
    team: str
    record: str
    pct: str
    games_behind: str
    home: str
    away: str
    conference: str
    division: str
    streak: str
    sos: str
    sov: str
    clinch: str = ""

    @property
    def rank_label(self) -> str:
        if self.seed <= 4:
            return self.division_code
        return str(self.seed) if self.seed <= 7 else ""

    @property
    def team_label(self) -> str:
        return f"{self.clinch}-{self.team}" if self.clinch else self.team


def draw_nfl_standings_conference(
    pdf: Canvas,
    title: str,
    rows: Sequence[NFLStandingRow],
    x: float,
    top: float,
    width: float,
    *,
    row_rule_span: tuple[float, float] | None = None,
    regular_font: str = "PP-Narrow",
    bold_font: str = "PP-Narrow-Bold",
    row_height: float = 9.15,
    last_headings: tuple[str, str] = ("PF", "PA"),
) -> float:
    """Draw one 16-team NFL playoff-order table in one newspaper column.

    The last two columns carry ``sos``/``sov`` values; live editions fill them
    with points for and against, so their headings are configurable.
    """

    registered = pdfmetrics.getRegisteredFontNames()
    regular = regular_font if regular_font in registered else "Helvetica"
    bold = bold_font if bold_font in registered else "Helvetica-Bold"
    pad = 2.0
    left = x + pad
    usable = width - 2 * pad
    fractions = (0.05, 0.185, 0.095, 0.105, 0.05, 0.085, 0.085, 0.085, 0.075, 0.065, 0.06, 0.06)
    edges = []
    edge = left
    for fraction in fractions:
        edge += usable * fraction
        edges.append(edge)

    pdf.setFont(bold, 7.2)
    pdf.drawString(left, top - 6.9, title)
    top -= 10.1
    pdf.setLineWidth(0.45)
    pdf.line(left, top, x + width - pad, top)
    top -= 4.8

    headings = ("RK", "TEAM", "W-L-T", "PCT", "GB", "HOME", "AWAY", "CONF", "DIV", "STRK", *last_headings)
    pdf.setFont(bold, 3.15)
    previous = left
    for index, (right, heading) in enumerate(zip(edges, headings, strict=True)):
        if index == 1:
            pdf.drawString(previous + 1.0, top, heading)
        else:
            pdf.drawRightString(right, top, heading)
        previous = right
    top -= 2.4
    pdf.setLineWidth(0.2)
    pdf.line(left, top, x + width - pad, top)
    top -= 5.1

    for index, row in enumerate(rows):
        values = (
            row.rank_label, row.team_label, row.record, row.pct, row.games_behind,
            row.home, row.away, row.conference, row.division, row.streak, row.sos, row.sov,
        )
        pdf.setFont(regular, 3.95)
        previous = left
        for column, (right, value) in enumerate(zip(edges, values, strict=True)):
            if column == 1:
                pdf.drawString(previous + 1.0, top, value)
            else:
                pdf.drawRightString(right, top, value)
            previous = right
        top -= row_height
        if row_rule_span is not None and index < len(rows) - 1:
            pdf.setLineWidth(0.85 if index == 6 else 0.14)
            pdf.line(row_rule_span[0], top + row_height / 2, row_rule_span[1], top + row_height / 2)
    return top


def _surname(name: str) -> str:
    parts = name.split()
    suffixes = {"Jr.", "Sr.", "II", "III", "IV"}
    if len(parts) > 2 and parts[-1] in suffixes:
        return f"{parts[-2]} {parts[-1]}"
    return parts[-1]


def _paragraph(pdf, text: str, x: float, top: float, width: float, *, size=4.35, leading=5.05):
    style = ParagraphStyle(
        "nfl-compact",
        fontName="Helvetica",
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


def _draw_category(
    pdf: Canvas,
    title: str,
    teams: Sequence[NFLTeamBox],
    attribute: str,
    headings: Sequence[str],
    x: float,
    top: float,
    width: float,
    *,
    row_height: float,
    regular_font: str,
    bold_font: str,
) -> float:
    pdf.setFont(bold_font, 5.1)
    pdf.drawString(x, top, title.upper())
    pdf.setLineWidth(0.25)
    pdf.line(x, top - 2.1, x + width, top - 2.1)
    top -= 6.4

    team_width = 13.0
    name_width = width * (0.34 if len(headings) >= 5 else 0.39)
    value_width = (width - team_width - name_width) / len(headings)
    edges = [x + team_width + name_width + value_width * (index + 1) for index in range(len(headings))]
    pdf.setFont(bold_font, 3.4)
    pdf.drawString(x, top, "TM")
    pdf.drawString(x + team_width, top, "PLAYER")
    for edge, heading in zip(edges, headings, strict=True):
        pdf.drawRightString(edge, top, heading)
    # Grow the header-to-first-row gap with stretched rows so the first
    # player never looks glued to the column headings.
    top -= 4.5 + max(0.0, row_height - 4.95)

    pdf.setFont(regular_font, 4.35)
    for team in teams:
        lines = getattr(team, attribute)
        for index, line in enumerate(lines):
            pdf.drawString(x, top, team.abbreviation if index == 0 else "")
            pdf.drawString(x + team_width, top, _surname(line.name))
            for edge, value in zip(edges, line.values, strict=True):
                pdf.drawRightString(edge, top, value)
            top -= row_height
        if len(lines) > 1:
            # A team total only when more than one player is listed.
            pdf.setFont(bold_font, 4.35)
            pdf.drawString(x + team_width, top, "Total")
            for edge, value in zip(edges, _column_totals(headings, lines), strict=True):
                pdf.drawRightString(edge, top, value)
            pdf.setFont(regular_font, 4.35)
            top -= row_height
    return top - 1.1


def _column_totals(headings: Sequence[str], lines: Sequence[NFLPlayerLine]) -> list[str]:
    """Sum each stat column: 'C/A' adds both halves, LONG takes the longest."""

    totals = []
    for column, heading in enumerate(headings):
        values = [str(line.values[column]) for line in lines if column < len(line.values)]
        try:
            if heading == "LONG":
                totals.append(str(max(int(v) for v in values)))
            elif all("/" in v for v in values):
                made = sum(int(v.split("/")[0]) for v in values)
                tried = sum(int(v.split("/")[1]) for v in values)
                totals.append(f"{made}/{tried}")
            else:
                totals.append(str(sum(int(v) for v in values)))
        except ValueError:
            totals.append("")
    return totals


def _draw_heading(pdf: Canvas, title: str, x: float, top: float, width: float, bold: str) -> float:
    """Draw a ruled section heading tight to its content, matching player categories."""

    top -= HEADING_SPACE_ABOVE
    pdf.setFont(bold, 5.1)
    pdf.drawString(x, top, title)
    pdf.setLineWidth(0.25)
    pdf.line(x, top - 2.1, x + width, top - 2.1)
    return top


# Extra air above the stand-alone headings so each one reads as belonging to
# the block beneath it rather than to the block above.
HEADING_SPACE_ABOVE = 2.6


def _draw_scoring(pdf: Canvas, game: NFLSimpleBoxScore, x: float, top: float, width: float, bold: str):
    top = _draw_heading(pdf, "SCORING BY QUARTER", x, top, width, bold)
    top -= 6.4
    overtime = max(len(game.away.quarter_scores), len(game.home.quarter_scores)) > 4
    headings = ("Q1", "Q2", "Q3", "Q4", *(("OT",) if overtime else ()), "T")
    name_width = width * 0.42
    value_width = (width - name_width) / len(headings)
    edges = [x + name_width + value_width * (index + 1) for index in range(len(headings))]
    pdf.setFont(bold, 3.55)
    for edge, heading in zip(edges, headings, strict=True):
        pdf.drawRightString(edge, top, heading)
    top -= 4.6
    for team in (game.away, game.home):
        pdf.setFont("Helvetica", 4.45)
        pdf.drawString(x, top, team.location)
        quarters = list(team.quarter_scores[:4]) + [0] * (4 - len(team.quarter_scores[:4]))
        if overtime:
            quarters.append(sum(team.quarter_scores[4:]))
        for edge, value in zip(edges, (*quarters, team.score), strict=True):
            pdf.drawRightString(edge, top, str(value))
        top -= 5.25
    return top


def _player_stats(team: NFLTeamBox) -> str:
    return (
        f"<b>{escape(team.abbreviation)}:</b> Sacks {escape(', '.join(team.sacks) or 'None')}; "
        f"INT {escape(', '.join(team.interceptions) or 'None')}; "
        f"KR {escape(', '.join(team.kick_returns) or 'None')}; "
        f"PR {escape(', '.join(team.punt_returns) or 'None')}; "
        f"FG {escape(', '.join(team.field_goals_made) or 'None')}; "
        f"Missed FG {escape(', '.join(team.field_goals_missed) or 'None')}; "
        f"Other TD {escape(', '.join(team.other_touchdowns) or 'None')}"
    )


def _team_stats(team: NFLTeamBox) -> str:
    stats = team.team_stats
    # College feeds leave plays, drives, sacks and red zone empty: drop them rather than print zeros.
    tracked = str(stats.get("plays", "0")).strip() not in {"", "0", "None"}
    parts = [f"1st {stats['first_downs']}"]
    if tracked:
        parts += [f"Plays {stats['plays']}", f"Drives {stats['drives']}", f"Sacks Allowed {stats['sacks']}",
                  f"RZ {stats['red_zone']}"]
    parts += [f"3rd {stats['third_down']}", f"4th {stats['fourth_down']}", f"Pen {stats['penalties']}",
              f"TO {stats['turnovers']}", f"FL {stats['fumbles_lost']}", f"TOP {stats['possession']}"]
    return f"<b>{escape(team.abbreviation)}:</b> " + ", ".join(parts)


def draw_nfl_simple_box_score(
    pdf: Canvas,
    game: NFLSimpleBoxScore,
    x: float,
    top: float,
    width: float,
    *,
    player_row_height: float = 4.95,
    section_gap: float = 0.5,
    regular_font: str = "PP-Narrow",
    bold_font: str = "PP-Narrow-Bold",
) -> float:
    """Draw a complete NFL simple box in one newspaper column."""

    registered = pdfmetrics.getRegisteredFontNames()
    regular = regular_font if regular_font in registered else "Helvetica"
    bold = bold_font if bold_font in registered else "Helvetica-Bold"
    pad = 2.0
    left = x + pad
    usable = width - 2 * pad

    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawCentredString(x + width / 2, top - 7.1, game.headline)
    top -= 10.8
    pdf.setLineWidth(0.6)
    pdf.line(left, top, x + width - pad, top)
    top -= 6.0 + section_gap

    teams = (game.away, game.home)
    top = _draw_category(
        pdf, "Passing", teams, "passing", ("C/A", "YDS", "TD", "INT"),
        left, top, usable, row_height=player_row_height, regular_font=regular, bold_font=bold,
    )
    top -= section_gap
    top = _draw_category(
        pdf, "Rushing", teams, "rushing", ("CAR", "YDS", "TD", "LONG"),
        left, top, usable, row_height=player_row_height, regular_font=regular, bold_font=bold,
    )
    top -= section_gap
    top = _draw_category(
        pdf, "Receiving", teams, "receiving", ("REC", "YDS", "TD", "TGT", "LONG"),
        left, top, usable, row_height=player_row_height, regular_font=regular, bold_font=bold,
    )
    top -= section_gap
    top = _draw_category(
        pdf, "Kicking", teams, "kicking", ("FG", "XP", "PTS"),
        left, top, usable, row_height=player_row_height, regular_font=regular, bold_font=bold,
    )

    top -= section_gap
    top = _draw_scoring(pdf, game, left, top, usable, bold)
    top -= section_gap
    top = _draw_heading(pdf, "PLAYER STATS", left, top, usable, bold)
    top -= 3.0
    for team in teams:
        top = _paragraph(pdf, _player_stats(team), left, top, usable)
        top -= 1.1

    # Paragraph tops sit at the cap line, so add a baseline's worth of air
    # before the next heading to match the spacing above table headings.
    top -= 4.0 + section_gap
    top = _draw_heading(pdf, "TEAM STATS", left, top, usable, bold)
    top -= 3.0
    for team in teams:
        top = _paragraph(pdf, _team_stats(team), left, top, usable)
        top -= 1.3

    # Separate the prose-like team summary from the factual footer so the
    # venue, officiating crew, and attendance never feel glued to it.
    top -= 2.4 + section_gap
    pdf.setLineWidth(0.28)
    pdf.line(left, top, x + width - pad, top)
    top -= 5.2
    top = _paragraph(pdf, escape(f"{game.venue}, {game.city}, {game.state}"), left, top, usable, size=4.15, leading=4.8)
    top -= 1.0
    if game.officials:
        top = _paragraph(pdf, f"<b>Officials:</b> {escape(', '.join(game.officials))}", left, top, usable, size=4.05, leading=4.7)
        top -= 1.0
    return _paragraph(pdf, f"<b>Attendance:</b> {game.attendance:,}", left, top, usable, size=4.15, leading=4.8)
