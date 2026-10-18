"""Print components for NBA pages."""

from __future__ import annotations

from collections import Counter
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
class PlayerLine:
    """The fields needed by the Pearson Press simple NBA box score."""

    name: str
    fg: str
    three_pt: str
    points: int
    rebounds: int
    assists: int
    steals: int = 0
    blocks: int = 0
    free_throws: str = "0-0"
    turnovers: int = 0


@dataclass(frozen=True)
class TeamBox:
    """One team's compact box-score data."""

    location: str
    nickname: str
    abbreviation: str
    score: int
    record: str
    players: tuple[PlayerLine, ...]
    totals: PlayerLine
    quarter_scores: tuple[int, ...]
    team_stats: Mapping[str, int]
    display_name: str | None = None
    rank: int | None = None


@dataclass(frozen=True)
class SimpleBoxScore:
    """A finished game, normalized for the four-across print component."""

    away: TeamBox
    home: TeamBox
    venue: str
    city: str
    state: str
    officials: tuple[str, ...]
    attendance: int
    regulation_periods: int = 4

    @property
    def period_count(self) -> int:
        return max(len(self.away.quarter_scores), len(self.home.quarter_scores))

    @property
    def headline(self) -> str:
        winner, loser = sorted((self.away, self.home), key=lambda team: team.score, reverse=True)
        overtime = ""
        overtime_count = self.period_count - self.regulation_periods
        if overtime_count == 1:
            overtime = " (OT)"
        elif overtime_count > 1:
            overtime = f" ({overtime_count}OT)"

        def label(team: TeamBox) -> str:
            name = team.display_name or team.nickname
            return f"No. {team.rank} {name}" if team.rank is not None and team.rank <= 25 else name

        return f"{label(winner)} {winner.score}, {label(loser)} {loser.score}{overtime}"


@dataclass(frozen=True)
class StandingRow:
    """One compact conference-standings row."""

    rank: int
    team: str
    record: str
    pct: str
    games_behind: str
    home: str
    away: str
    conference: str
    division: str
    streak: str
    last_ten: str
    clinch: str = ""

    @property
    def rank_label(self) -> str:
        return str(self.rank) if 1 <= self.rank <= 10 else ""

    @property
    def team_label(self) -> str:
        return f"{self.clinch}-{self.team}" if self.clinch else self.team


def _split_made_attempted(value: str) -> tuple[int, int]:
    made, attempted = value.split("-", maxsplit=1)
    return int(made), int(attempted)


def _surname(full_name: str) -> str:
    parts = full_name.split()
    if len(parts) == 1:
        return parts[0]
    suffixes = {"Jr.", "Sr.", "II", "III", "IV"}
    if parts[-1] in suffixes and len(parts) >= 3:
        return f"{parts[-2]} {parts[-1]}"
    return parts[-1]


def player_labels(players: Sequence[PlayerLine]) -> dict[str, str]:
    """Use surnames unless two players share one, then add a first initial."""

    surnames = [_surname(player.name) for player in players]
    duplicates = Counter(surnames)
    labels: dict[str, str] = {}
    for player, surname in zip(players, surnames, strict=True):
        labels[player.name] = (
            f"{player.name[0]}. {surname}" if duplicates[surname] > 1 else surname
        )
    return labels


def _true_shooting_pct(team: TeamBox) -> float:
    """Return standard team TS%: PTS / (2 * (FGA + 0.44 * FTA))."""

    _, field_goal_attempts = _split_made_attempted(team.totals.fg)
    _, free_throw_attempts = _split_made_attempted(team.totals.free_throws)
    denominator = 2 * (field_goal_attempts + 0.44 * free_throw_attempts)
    return 100 * team.score / denominator if denominator else 0.0


def _free_throw_rate(team: TeamBox) -> float:
    """Return standard free-throw rate: FTA / FGA."""

    _, field_goal_attempts = _split_made_attempted(team.totals.fg)
    _, free_throw_attempts = _split_made_attempted(team.totals.free_throws)
    return free_throw_attempts / field_goal_attempts if field_goal_attempts else 0.0


def _offensive_rating(team: TeamBox) -> float:
    """Return points per 100 possessions using a compact box-score estimate."""

    _, field_goal_attempts = _split_made_attempted(team.totals.fg)
    _, free_throw_attempts = _split_made_attempted(team.totals.free_throws)
    possessions = (
        field_goal_attempts
        - team.team_stats["offensive_rebounds"]
        + team.totals.turnovers
        + 0.44 * free_throw_attempts
    )
    return 100 * team.score / possessions if possessions else 0.0


def _draw_paragraph(pdf, text, x, top, width, *, font_size=4.85, leading=5.8):
    style = ParagraphStyle(
        "compact-box-score",
        fontName="Helvetica",
        fontSize=font_size,
        leading=leading,
        alignment=TA_LEFT,
        textColor=black,
        spaceAfter=0,
        spaceBefore=0,
        allowWidows=0,
        allowOrphans=0,
    )
    paragraph = Paragraph(text, style)
    _, height = paragraph.wrap(width, 200)
    paragraph.drawOn(pdf, x, top - height)
    return top - height


def _draw_team_table(
    pdf: Canvas,
    team: TeamBox,
    x: float,
    top: float,
    width: float,
    player_row_height: float,
) -> float:
    pad = 2.2
    left = x + pad
    usable = width - (2 * pad)
    # Narrower name/shooting columns give the five one-to-two digit stat
    # columns enough room that their bold headings never touch.
    name_width = usable * 0.30
    shooting_width = usable * 0.13
    small_width = (usable - name_width - 2 * shooting_width) / 5
    column_widths = (shooting_width, shooting_width, *([small_width] * 5))
    right_edges = []
    edge = left + name_width
    for column_width in column_widths:
        edge += column_width
        right_edges.append(edge)
    labels = player_labels(team.players)

    pdf.setFillGray(0)
    pdf.setFont("Helvetica-Bold", 6.25)
    pdf.drawString(left, top - 6.2, f"{team.location.upper()} ({team.record})")
    top -= 8.4
    pdf.setLineWidth(0.3)
    pdf.line(left, top, x + width - pad, top)
    top -= 4.9
    pdf.setFont("Helvetica-Bold", 4.35)
    pdf.drawString(left, top, "PLAYER")
    for edge, heading in zip(
        right_edges,
        ("FG", "3P", "PTS", "REB", "AST", "STL", "BLK"),
        strict=True,
    ):
        pdf.drawRightString(edge, top, heading)
    top -= 2.2
    pdf.setLineWidth(0.18)
    pdf.line(left, top, x + width - pad, top)
    top -= 5.0

    for player in team.players:
        pdf.setFont("Helvetica", 4.95)
        pdf.drawString(left, top, labels[player.name])
        values = (
            player.fg.replace("-", "/"),
            player.three_pt.replace("-", "/"),
            player.points,
            player.rebounds,
            player.assists,
            player.steals,
            player.blocks,
        )
        for edge, value in zip(right_edges, values, strict=True):
            pdf.drawRightString(edge, top, str(value))
        top -= player_row_height

    top -= 1.0
    pdf.setLineWidth(0.22)
    pdf.line(left, top + 2.3, x + width - pad, top + 2.3)
    pdf.setFont("Helvetica-Bold", 4.95)
    pdf.drawString(left, top - 2.4, "TOTAL")
    values = (
        team.totals.fg.replace("-", "/"),
        team.totals.three_pt.replace("-", "/"),
        team.totals.points,
        team.totals.rebounds,
        team.totals.assists,
        team.totals.steals,
        team.totals.blocks,
    )
    for edge, value in zip(right_edges, values, strict=True):
        pdf.drawRightString(edge, top - 2.4, str(value))
    # Preserve a clear team break after the total row. This is deliberately
    # larger than ordinary row leading so the next header cannot read as part
    # of the totals table.
    return top - 9.0


def _team_stats(team: TeamBox) -> str:
    stats = team.team_stats
    return (
        f"<b>{escape(team.location)}:</b> OReb {stats['offensive_rebounds']}, "
        f"DReb {stats['defensive_rebounds']}, STL {team.totals.steals}, "
        f"BLK {team.totals.blocks}, FT {team.totals.free_throws.replace('-', '/')}, "
        f"TOV {team.totals.turnovers}, Pts off TOV {stats['turnover_points']}, "
        f"Fast Break {stats['fast_break_points']}, PIP {stats['points_in_paint']}, "
        f"Fouls {stats['fouls']}, TS% {_true_shooting_pct(team):.1f}, "
        f"FTr {f'{_free_throw_rate(team):.3f}'.lstrip('0')}, "
        f"ORtg {_offensive_rating(team):.1f}"
    )


def _draw_section_heading(pdf: Canvas, title: str, left: float, top: float, right: float) -> float:
    """Draw a ruled section heading; callers put any extra air above it, not below."""

    pdf.setFont("Helvetica-Bold", 5.0)
    pdf.drawString(left, top, title)
    pdf.setLineWidth(0.22)
    pdf.line(left, top - 2.1, right, top - 2.1)
    return top


def _draw_quarters(pdf: Canvas, game: SimpleBoxScore, x: float, top: float, width: float) -> float:
    pad = 2.2
    left = x + pad
    usable = width - (2 * pad)
    has_overtime = game.period_count > game.regulation_periods
    displayed_periods = game.regulation_periods + int(has_overtime)
    columns = displayed_periods + 2
    name_width = usable * 0.32
    number_width = (usable - name_width) / (columns - 1)
    right_edges = [left + name_width + number_width * (index + 1) for index in range(columns - 1)]

    section_title = "SCORING BY HALF" if game.regulation_periods == 2 else "SCORING BY QUARTER"
    top = _draw_section_heading(pdf, section_title, left, top, left + usable)
    top -= 6.6
    pdf.setFont("Helvetica-Bold", 4.35)
    if game.regulation_periods == 2:
        headings = ["1H", "2H"]
    else:
        headings = [f"Q{number}" for number in range(1, game.regulation_periods + 1)]
    if has_overtime:
        headings.append("OT")
    headings.append("T")
    for edge, heading in zip(right_edges, headings, strict=True):
        pdf.drawRightString(edge, top, heading)
    top -= 5.6
    for team in (game.away, game.home):
        pdf.setFont("Helvetica", 4.9)
        pdf.drawString(left, top, team.location)
        values = list(team.quarter_scores[:game.regulation_periods])
        if has_overtime:
            values.append(sum(team.quarter_scores[game.regulation_periods:]))
        values.append(team.score)
        for edge, value in zip(right_edges, values, strict=True):
            pdf.drawRightString(edge, top, str(value))
        top -= 6.4
    return top


def draw_standings_conference(
    pdf: Canvas,
    title: str,
    rows: Sequence[StandingRow],
    x: float,
    top: float,
    width: float,
    *,
    regular_font: str = "PP-Narrow",
    bold_font: str = "PP-Narrow-Bold",
    title_font_size: float = 7.1,
    heading_font_size: float = 3.65,
    body_font_size: float = 4.15,
    row_height: float = 8.7,
    row_rule_span: tuple[float, float] | None = None,
) -> float:
    """Draw one 15-team NBA conference table in a newspaper column."""

    registered = pdfmetrics.getRegisteredFontNames()
    regular = regular_font if regular_font in registered else "Helvetica"
    bold = bold_font if bold_font in registered else "Helvetica-Bold"
    pad = 2.0
    left = x + pad
    usable = width - 2 * pad
    fractions = (0.05, 0.21, 0.10, 0.09, 0.06, 0.09, 0.09, 0.09, 0.08, 0.07, 0.07)
    right_edges = []
    edge = left
    for fraction in fractions:
        edge += usable * fraction
        right_edges.append(edge)

    pdf.setFont(bold, title_font_size)
    pdf.drawString(left, top - title_font_size, title)
    top -= title_font_size + 3.2
    pdf.setLineWidth(0.45)
    pdf.line(left, top, x + width - pad, top)
    top -= 5.0

    headings = ("RK", "TEAM", "W-L", "%", "GB", "HOME", "AWAY", "CONF", "DIV", "STRK", "L10")
    pdf.setFont(bold, heading_font_size)
    previous_edge = left
    for index, (right_edge, heading) in enumerate(zip(right_edges, headings, strict=True)):
        if index == 1:
            pdf.drawString(previous_edge + 1.25, top, heading)
        else:
            pdf.drawRightString(right_edge, top, heading)
        previous_edge = right_edge
    top -= 2.5
    pdf.setLineWidth(0.2)
    pdf.line(left, top, x + width - pad, top)
    top -= 5.6

    for index, row in enumerate(rows):
        values = (
            row.rank_label,
            row.team_label,
            row.record,
            row.pct,
            row.games_behind,
            row.home,
            row.away,
            row.conference,
            row.division,
            row.streak,
            row.last_ten,
        )
        pdf.setFont(regular, body_font_size)
        previous_edge = left
        for column, (right_edge, value) in enumerate(zip(right_edges, values, strict=True)):
            if column == 1:
                pdf.drawString(previous_edge + 1.25, top, value)
            else:
                pdf.drawRightString(right_edge, top, value)
            previous_edge = right_edge
        top -= row_height
        if row_rule_span is not None and index < len(rows) - 1:
            # Draw synchronized rules from the west table across the gutter and
            # through the east table. The 10/11 cutoff is intentionally heavy.
            pdf.setLineWidth(0.85 if index == 9 else 0.16)
            pdf.line(
                row_rule_span[0],
                top + row_height / 2,
                row_rule_span[1],
                top + row_height / 2,
            )
    return top


def draw_simple_box_score(
    pdf: Canvas,
    game: SimpleBoxScore,
    x: float,
    top: float,
    width: float,
    *,
    show_outline: bool = False,
    extra_spacing: float = 0.0,
    player_row_height: float = 6.15,
) -> float:
    """Draw a complete NBA box score and return its bottom y coordinate."""

    if width < 132:
        raise ValueError("Simple NBA box score needs at least 132 points of width")
    start_top = top
    if show_outline:
        pdf.setStrokeGray(0.72)
        pdf.setLineWidth(0.35)
        pdf.rect(x, 28, width, start_top - 28, stroke=1, fill=0)
        pdf.setStrokeGray(0)

    pad = 2.2
    pdf.setFillGray(0)
    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawCentredString(x + width / 2, top - 7.2, game.headline)
    top -= 11.1
    pdf.setLineWidth(0.65)
    pdf.line(x + pad, top, x + width - pad, top)
    top -= 3.2 + extra_spacing
    top = _draw_team_table(pdf, game.away, x, top, width, player_row_height)
    top -= 0.5 + extra_spacing
    top = _draw_team_table(pdf, game.home, x, top, width, player_row_height)
    top -= 2.8 + extra_spacing
    top = _draw_quarters(pdf, game, x, top, width)
    top -= 2.6 + 2 * extra_spacing
    top = _draw_section_heading(pdf, "TEAM STATS", x + pad, top, x + width - pad)
    top -= 3.2
    for team in (game.away, game.home):
        top = _draw_paragraph(pdf, _team_stats(team), x + pad, top, width - 2 * pad)
        top -= 2.0

    top -= 2.0 + extra_spacing
    pdf.setLineWidth(0.28)
    pdf.line(x + pad, top, x + width - pad, top)
    top -= 4.3
    location = f"{game.venue}, {game.city}, {game.state}"
    top = _draw_paragraph(pdf, escape(location), x + pad, top, width - 2 * pad, font_size=4.55)
    top -= 1.0
    if game.officials:
        top = _draw_paragraph(pdf, f"<b>Officials:</b> {escape(', '.join(game.officials))}", x + pad, top, width - 2 * pad, font_size=4.55)
        top -= 1.0
    return _draw_paragraph(pdf, f"<b>Attendance:</b> {game.attendance:,}", x + pad, top, width - 2 * pad, font_size=4.55)
