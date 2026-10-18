"""Print components for compact Pearson Press NHL pages."""

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
class GoalEvent:
    period: int
    time: str
    scorer: str
    goal_number: int
    assists: tuple[str, ...]
    away_score: int
    home_score: int
    strength: str = ""


@dataclass(frozen=True)
class GoalieLine:
    name: str
    even_strength_saves: int
    power_play_saves: int
    short_handed_saves: int
    shots_against: int
    save_pct: str
    time_on_ice: str

    @property
    def strength_saves(self) -> str:
        """Even-strength, power-play and shorthanded saves, then the total: '16-2-0-18'."""

        parts = (self.even_strength_saves, self.power_play_saves, self.short_handed_saves)
        try:
            total = sum(int(part) for part in parts)
        except (TypeError, ValueError):
            return "-".join(str(part) for part in parts)
        return f"{parts[0]}-{parts[1]}-{parts[2]}-{total}"


@dataclass(frozen=True)
class NHLTeamBox:
    location: str
    nickname: str
    abbreviation: str
    score: int
    goalie: GoalieLine
    penalty_minutes: tuple[tuple[str, int], ...]
    team_stats: Mapping[str, str | int]
    period_scores: tuple[int, ...]
    headline_name: str | None = None


@dataclass(frozen=True)
class NHLSimpleBoxScore:
    away: NHLTeamBox
    home: NHLTeamBox
    goals: tuple[GoalEvent, ...]
    venue: str
    city: str
    state: str
    officials: tuple[str, ...]
    attendance: int
    overtime_periods: int = 0
    shootout: bool = False

    @property
    def headline(self) -> str:
        winner, loser = sorted((self.away, self.home), key=lambda team: team.score, reverse=True)
        suffix = ""
        if self.shootout:
            suffix = " (SO)"
        elif self.overtime_periods == 1:
            suffix = " (OT)"
        elif self.overtime_periods > 1:
            suffix = f" ({self.overtime_periods}OT)"
        return (
            f"{winner.headline_name or winner.nickname} {winner.score}, "
            f"{loser.headline_name or loser.nickname} {loser.score}{suffix}"
        )


@dataclass(frozen=True)
class NHLStandingRow:
    rank: str
    team: str
    record: str
    points: str
    regulation_wins: str
    regulation_overtime_wins: str
    home: str
    away: str
    goals_for: str
    goals_against: str
    last_ten: str
    streak: str
    clinch: str = ""

    @property
    def team_label(self) -> str:
        return f"{self.clinch}-{self.team}" if self.clinch else self.team


def _paragraph(
    pdf: Canvas,
    text: str,
    x: float,
    top: float,
    width: float,
    *,
    font_size: float = 4.45,
    leading: float = 5.05,
) -> float:
    style = ParagraphStyle(
        "nhl-compact",
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


def _fit_text(pdf: Canvas, text: str, x: float, baseline: float, width: float, font: str, size: float) -> None:
    while size > 3.2 and pdf.stringWidth(text, font, size) > width:
        size -= 0.1
    pdf.setFont(font, size)
    pdf.drawString(x, baseline, text)


def _draw_heading(pdf: Canvas, title: str, left: float, right: float, top: float, spacing: float) -> float:
    """Draw a ruled section heading; air belongs above headings, not below."""

    top -= 1.6 * spacing
    pdf.setFont("Helvetica-Bold", 5.0)
    pdf.drawString(left, top, title)
    pdf.setLineWidth(0.22)
    pdf.line(left, top - 2.0, right, top - 2.0)
    return top


def _draw_scoring_summary(
    pdf: Canvas,
    game: NHLSimpleBoxScore,
    x: float,
    top: float,
    width: float,
    spacing: float,
) -> float:
    pad = 2.2
    left = x + pad
    right = x + width - pad
    top = _draw_heading(pdf, "SCORING SUMMARY", left, right, top, spacing)
    top -= 6.6 * spacing

    for period in sorted({goal.period for goal in game.goals}):
        goals = [goal for goal in game.goals if goal.period == period]
        label = f"{period}{'ST' if period == 1 else 'ND' if period == 2 else 'RD' if period == 3 else 'TH'} PERIOD"
        if period > 3:
            label = "OVERTIME"
        pdf.setFont("Helvetica-Bold", 4.55)
        pdf.drawString(left, top, label)
        pdf.drawRightString(right - 14.0, top, game.away.abbreviation)
        pdf.drawRightString(right, top, game.home.abbreviation)
        top -= 5.4 * spacing

        for goal in goals:
            strength = f" ({goal.strength})" if goal.strength else ""
            scorer = f"{goal.scorer} ({goal.goal_number}){strength}"
            pdf.setFont("Helvetica", 4.65)
            pdf.drawString(left, top, goal.time)
            _fit_text(pdf, scorer, left + 19.0, top, width - 53.0, "Helvetica-Bold", 4.65)
            # Running score sits under each team's column heading.
            pdf.setFont("Helvetica-Bold", 4.55)
            pdf.drawRightString(right - 14.0, top, str(goal.away_score))
            pdf.drawRightString(right, top, str(goal.home_score))
            top -= 2.6 * spacing  # assists tuck up under their own scorer
            assist_text = "Assists: " + (", ".join(goal.assists) if goal.assists else "Unassisted")
            top = _paragraph(
                pdf, escape(assist_text), left + 19.0, top + 0.8,
                width - 21.2, font_size=4.0, leading=4.35 * spacing,
            )
            top -= 4.4 * spacing  # room so the next bold scorer clears these assists
        top -= 0.8 * spacing
    return top


def _draw_goalies(pdf: Canvas, game: NHLSimpleBoxScore, x: float, top: float, width: float, spacing: float) -> float:
    pad = 2.2
    left = x + pad
    right = x + width - pad
    name_edge = left + (width - 2 * pad) * 0.36
    edges = (
        name_edge + (right - name_edge) * 0.36,
        name_edge + (right - name_edge) * 0.52,
        name_edge + (right - name_edge) * 0.74,
        right,
    )
    top = _draw_heading(pdf, "GOALTENDING", left, right, top, spacing)
    top -= 7.0 * spacing
    for index, team in enumerate((game.away, game.home)):
        # Each team gets its own labelled table, matching the NBA box score.
        if index:
            top -= 1.6 * spacing
        pdf.setFont("Helvetica-Bold", 4.6)
        pdf.drawString(left, top, team.location.upper())
        top -= 5.0 * spacing
        pdf.setFont("Helvetica-Bold", 3.9)
        pdf.drawString(left, top, "PLAYER")
        for edge, label in zip(edges, ("ES-PP-SH-TOT", "SA", "SV%", "TOI"), strict=True):
            pdf.drawRightString(edge, top, label)
        pdf.setLineWidth(0.18)
        pdf.line(left, top - 1.6 * spacing, right, top - 1.6 * spacing)
        top -= 5.6 * spacing
        goalie = team.goalie
        _fit_text(pdf, goalie.name, left, top, name_edge - left - 1.5, "Helvetica", 4.4)
        values = (goalie.strength_saves, goalie.shots_against, goalie.save_pct, goalie.time_on_ice)
        pdf.setFont("Helvetica", 4.35)
        for edge, value in zip(edges, values, strict=True):
            pdf.drawRightString(edge, top, str(value))
        top -= 5.1 * spacing
    return top


def _draw_penalties(pdf: Canvas, game: NHLSimpleBoxScore, x: float, top: float, width: float, spacing: float) -> float:
    pad = 2.2
    top = _draw_heading(pdf, "PENALTY MINUTES", x + pad, x + width - pad, top, spacing)
    top -= 3.2 * spacing
    for team in (game.away, game.home):
        players = ", ".join(f"{name} {minutes}" for name, minutes in team.penalty_minutes) or "None"
        top = _paragraph(
            pdf, f"<b>{team.abbreviation}:</b> {escape(players)}",
            x + pad, top, width - 2 * pad, font_size=4.15, leading=4.65 * spacing,
        )
        top -= 0.8 * spacing
    return top


def _display_periods(game: NHLSimpleBoxScore, team: NHLTeamBox) -> tuple[list[str], list[int]]:
    headings = ["1P", "2P", "3P"]
    scores = list(team.period_scores[:3])
    if game.overtime_periods or game.shootout:
        headings.append("OT")
        if game.shootout:
            scores.append(max(0, team.score - sum(scores)))
        else:
            scores.append(sum(team.period_scores[3:]))
    headings.append("T")
    scores.append(team.score)
    return headings, scores


def _draw_period_scores(pdf: Canvas, game: NHLSimpleBoxScore, x: float, top: float, width: float, spacing: float) -> float:
    pad = 2.2
    left = x + pad
    right = x + width - pad
    headings, _ = _display_periods(game, game.away)
    name_width = (width - 2 * pad) * 0.42
    number_width = (right - (left + name_width)) / len(headings)
    edges = [left + name_width + number_width * (index + 1) for index in range(len(headings))]
    top = _draw_heading(pdf, "SCORING BY PERIOD", left, right, top, spacing)
    top -= 6.6 * spacing
    pdf.setFont("Helvetica-Bold", 4.0)
    for edge, heading in zip(edges, headings, strict=True):
        pdf.drawRightString(edge, top, heading)
    top -= 5.0 * spacing
    for team in (game.away, game.home):
        _, scores = _display_periods(game, team)
        pdf.setFont("Helvetica", 4.4)
        pdf.drawString(left, top, team.location)
        for edge, score in zip(edges, scores, strict=True):
            pdf.drawRightString(edge, top, str(score))
        top -= 5.1 * spacing
    return top


def _draw_team_stats(pdf: Canvas, game: NHLSimpleBoxScore, x: float, top: float, width: float, spacing: float) -> float:
    pad = 2.2
    top = _draw_heading(pdf, "TEAM STATS", x + pad, x + width - pad, top, spacing)
    top -= 3.2 * spacing
    for team in (game.away, game.home):
        stats = team.team_stats
        text = (
            f"<b>{escape(team.abbreviation)}:</b> Shots {stats['shots']}, Hits {stats['hits']}, "
            f"FOW {stats['faceoffs_won']}, PP {stats['power_play']}, Blocks {stats['blocked_shots']}, "
            f"Takeaways {stats['takeaways']}, Giveaways {stats['giveaways']}"
        )
        top = _paragraph(pdf, text, x + pad, top, width - 2 * pad, font_size=4.15, leading=4.65 * spacing)
        top -= 0.8 * spacing
    return top


def draw_nhl_simple_box_score(
    pdf: Canvas,
    game: NHLSimpleBoxScore,
    x: float,
    top: float,
    width: float,
    *,
    spacing_factor: float = 1.0,
) -> float:
    """Draw one one-column NHL box and return its bottom coordinate."""
    if width < 132:
        raise ValueError("Simple NHL box score needs at least 132 points of width")
    spacing = max(0.72, spacing_factor)
    pad = 2.2
    pdf.setFillGray(0)
    pdf.setFont("Helvetica-Bold", 7.1)
    pdf.drawCentredString(x + width / 2, top - 7.0, game.headline)
    top -= 10.5 * spacing
    pdf.setLineWidth(0.65)
    pdf.line(x + pad, top, x + width - pad, top)
    top -= 4.0 * spacing

    top = _draw_scoring_summary(pdf, game, x, top, width, spacing)
    top -= 1.2 * spacing
    top = _draw_goalies(pdf, game, x, top, width, spacing)
    top -= 3.0 * spacing
    top = _draw_penalties(pdf, game, x, top, width, spacing)
    top -= 4.0 * spacing
    top = _draw_period_scores(pdf, game, x, top, width, spacing)
    top -= 0.4 * spacing
    top = _draw_team_stats(pdf, game, x, top, width, spacing)
    top -= 1.2 * spacing
    pdf.setLineWidth(0.28)
    pdf.line(x + pad, top, x + width - pad, top)
    top -= 4.2 * spacing
    top = _paragraph(
        pdf, escape(f"{game.venue}, {game.city}, {game.state}"),
        x + pad, top, width - 2 * pad, font_size=4.25, leading=4.7 * spacing,
    )
    top -= 0.6 * spacing
    if game.officials:
        top = _paragraph(
            pdf, f"<b>Officials:</b> {escape(', '.join(game.officials))}",
            x + pad, top, width - 2 * pad, font_size=4.05, leading=4.55 * spacing,
        )
        top -= 0.6 * spacing
    return _paragraph(
        pdf, f"<b>Attendance:</b> {game.attendance:,}",
        x + pad, top, width - 2 * pad, font_size=4.1, leading=4.55 * spacing,
    )


def draw_nhl_standings_conference(
    pdf: Canvas,
    title: str,
    rows: Sequence[NHLStandingRow],
    x: float,
    top: float,
    width: float,
    *,
    row_rule_span: tuple[float, float] | None = None,
    title_font_size: float = 7.2,
    heading_font_size: float = 3.55,
    body_font_size: float = 4.15,
    row_height: float = 7.7,
) -> float:
    """Draw one conference in NHL playoff order."""
    registered = pdfmetrics.getRegisteredFontNames()
    regular = "PP-Narrow" if "PP-Narrow" in registered else "Helvetica"
    bold = "PP-Narrow-Bold" if "PP-Narrow-Bold" in registered else "Helvetica-Bold"
    pad = 2.0
    left = x + pad
    usable = width - 2 * pad
    fractions = (0.055, 0.185, 0.105, 0.06, 0.055, 0.065, 0.105, 0.105, 0.055, 0.055, 0.09, 0.065)
    edges = []
    edge = left
    for fraction in fractions:
        edge += usable * fraction
        edges.append(edge)

    pdf.setFont(bold, title_font_size)
    pdf.drawString(left, top - title_font_size, title)
    top -= title_font_size + 3.2
    pdf.setLineWidth(0.45)
    pdf.line(left, top, x + width - pad, top)
    top -= 5.0
    headings = ("RK", "TEAM", "W-L-OTL", "PTS", "RW", "ROW", "HOME", "AWAY", "GF", "GA", "L10", "STRK")
    pdf.setFont(bold, heading_font_size)
    previous = left
    for index, (right, heading) in enumerate(zip(edges, headings, strict=True)):
        if index == 1:
            pdf.drawString(previous + 1.0, top, heading)
        else:
            pdf.drawRightString(right, top, heading)
        previous = right
    top -= 2.5
    pdf.setLineWidth(0.2)
    pdf.line(left, top, x + width - pad, top)
    top -= 5.3

    for index, row in enumerate(rows):
        values = (
            row.rank, row.team_label, row.record, row.points, row.regulation_wins,
            row.regulation_overtime_wins, row.home, row.away, row.goals_for,
            row.goals_against, row.last_ten, row.streak,
        )
        pdf.setFont(regular, body_font_size)
        previous = left
        for column, (right, value) in enumerate(zip(edges, values, strict=True)):
            if column == 1:
                _fit_text(pdf, value, previous + 1.0, top, right - previous - 1.5, regular, body_font_size)
            else:
                pdf.drawRightString(right, top, value)
            previous = right
        top -= row_height
        if row_rule_span is not None and index < len(rows) - 1:
            pdf.setLineWidth(0.85 if index == 7 else 0.13)
            pdf.line(row_rule_span[0], top + 3.5, row_rule_span[1], top + 3.5)
    return top
