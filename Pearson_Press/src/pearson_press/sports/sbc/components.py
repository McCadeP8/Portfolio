"""SBC box scores: the one-column matchup box and the reader's two-headed Blackjack box.

Scoring is shown in the paper's compact form: each category is worth its league
weight without the trailing 1 (PTS 6, AST 4, TS% 4, ... MP 1), and the TOTAL
row shows categories won. Official score = 10 x points + categories, so
38 points with 12 categories is the league's 392.

Beside each value, an arrow points at the side that won the category; "=" marks
a tie and "X" a side that did not qualify (no attempts). The reader's two-headed
box marks only the Blackjack's category wins, with a check.
"""

from __future__ import annotations

from datetime import date
from html import escape

from reportlab.pdfgen.canvas import Canvas

from pearson_press.edition.blocks import Block, paragraph
from pearson_press.publication.fonts import face
from pearson_press.sports.sbc.model import CATEGORIES, FAVORITE, SbcMatchup, SbcTeamBox

ATTEMPTS = {"TS%": ("2PTA", "3PTA", "FTA"), "2PT%": ("2PTA",), "3PT%": ("3PTA",), "FT%": ("FTA",)}
SPLITS = {"2PT%": ("2PTM", "2PTA"), "3PT%": ("3PTM", "3PTA"), "FT%": ("FTM", "FTA")}
NARROW, BOLD = "PP-Narrow", "PP-Narrow-Bold"


def qualified(box: SbcTeamBox, category: str) -> bool:
    if category not in ATTEMPTS:
        return True
    return any(box.totals.get(key, 0) for key in ATTEMPTS[category])


def value_text(category: str, box: SbcTeamBox) -> str:
    """One format for every percentage: the rate first, the actuals after in parentheses."""

    t = box.totals
    value = t.get(category, 0.0)
    if category in SPLITS:
        made, tried = SPLITS[category]
        return f"{value * 100:.1f}% ({int(t.get(made, 0))}/{int(t.get(tried, 0))})"
    if category == "TS%":
        attempts = t.get("2PTA", 0) + t.get("3PTA", 0) + 0.44 * t.get("FTA", 0)
        return f"{value * 100:.1f}% ({attempts:.0f})"
    if category == "+/-":
        return f"{int(value):+d}" if value else "0"
    return f"{int(round(value))}"


def _team_head(box: SbcTeamBox) -> str:
    return f"{box.abbr} ({box.record})" if box.record else box.abbr


def _num(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def _dates(start: date, end: date) -> str:
    months = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
    if start.month == end.month:
        return f"{months[start.month - 1]} {start.day}-{end.day}"
    return f"{months[start.month - 1]} {start.day}-{months[end.month - 1]} {end.day}"


def marker(pdf: Canvas, x: float, y: float, kind: str) -> None:
    """A winner arrow ('left'/'right'), '=' for a tie, 'X' for no qualifier, centered at x."""

    pdf.setFillGray(0)
    if kind in {"left", "right"}:
        w, h = 2.6, 2.8
        tip, back = (x - w / 2, x + w / 2) if kind == "left" else (x + w / 2, x - w / 2)
        path = pdf.beginPath()
        path.moveTo(tip, y + h / 2)
        path.lineTo(back, y + h)
        path.lineTo(back, y)
        path.close()
        pdf.drawPath(path, stroke=0, fill=1)
    elif kind == "check":
        pdf.setStrokeGray(0)
        pdf.setLineWidth(0.7)
        path = pdf.beginPath()
        path.moveTo(x - 1.5, y + 1.5)
        path.lineTo(x - 0.4, y + 0.3)
        path.lineTo(x + 1.7, y + 3.2)
        pdf.drawPath(path, stroke=1, fill=0)
    elif kind in {"=", "X"}:
        pdf.setFont(face(BOLD), 4.6)
        pdf.drawCentredString(x, y, kind)


def _markers(matchup: SbcMatchup, category: str, left: SbcTeamBox, right: SbcTeamBox) -> tuple[str, str]:
    """Markers beside the left and right values for one category."""

    winner = matchup.category_winner(category)
    marks = ["X" if not qualified(left, category) else "", "X" if not qualified(right, category) else ""]
    if winner == "tie":
        return marks[0] or "=", marks[1] or "="
    if winner == matchup.side(left.key):
        return marks[0] or "left", marks[1]
    return marks[0], marks[1] or "right"


def team_stats(pdf: Canvas, boxes: list[SbcTeamBox], x: float, top: float, width: float) -> float:
    """TEAM STATS: games played (with total), then the team's leader in PTS, REB, AST, STL, BLK."""

    pdf.setFillGray(0)
    pdf.setFont(face(BOLD), 4.6)
    pdf.drawString(x, top - 4.6, "TEAM STATS")
    pdf.setLineWidth(0.25)
    pdf.line(x, top - 5.8, x + width, top - 5.8)
    y = top - 6.8
    for box in boxes:
        groups: dict[int, list[str]] = {}
        for name, games in box.games:
            groups.setdefault(games, []).append(name)
        listed = "; ".join(f"{', '.join(names)} {count}" for count, names in sorted(groups.items(), reverse=True))
        total = sum(games for _, games in box.games)
        parts = [f"GP {total} ({listed})" if total else "GP 0"]
        if box.leaders:
            parts.append("Top: " + ", ".join(f"{who} {stat}" for stat, who in box.leaders.items()))
        y = paragraph(pdf, f"<b>{escape(box.abbr)}:</b> {escape('; '.join(parts))}", x, y, width,
                      font="Times-Roman", size=4.7, leading=5.2) - 0.4
    return y


# --------------------------------------------------------------------------
# One matchup, one column


def sbc_box_block(matchup: SbcMatchup, *, priority: int = 50) -> Block:
    away, home = matchup.away, matchup.home
    a_pts, h_pts, a_cats, h_cats = matchup.short_score()

    def draw(pdf, x, top, width, s):
        left, usable = x + 2.0, width - 4.0
        center = left + usable / 2
        label_w = 16.0
        value_w = (usable - label_w) / 2 - 7.5
        y = top
        pdf.setFillGray(0)
        pdf.setFont("Times-Bold", 8.2)
        pdf.drawCentredString(center, y - 7.4, matchup.short_headline)
        y -= 9.4
        pdf.setLineWidth(0.4)
        pdf.line(left, y, left + usable, y)
        pdf.setFont(face(BOLD), 4.9)
        pdf.drawRightString(left + value_w, y - 5.0, _team_head(away))
        pdf.drawString(left + usable - value_w, y - 5.0, _team_head(home))
        kind = "" if matchup.kind == "Regular Season" else f"{matchup.round} · "
        pdf.setFont(face(NARROW), 4.2)
        pdf.drawCentredString(center, y - 4.9, f"{kind}{_dates(matchup.start, matchup.end)}")
        y -= 6.4
        pdf.setLineWidth(0.25)
        pdf.line(left, y, left + usable, y)
        y -= 1.4  # a little air above the first category
        row = 4.35 + 0.6 * s
        for category, label in CATEGORIES:
            base = y - row + 1.0
            mark_left, mark_right = _markers(matchup, category, away, home)
            pdf.setFont(face(NARROW), 4.6)
            pdf.drawRightString(left + value_w, base, value_text(category, away))
            pdf.drawString(left + usable - value_w, base, value_text(category, home))
            pdf.drawCentredString(center, base, label)
            marker(pdf, center - label_w / 2 - 3.0, base, mark_left)
            marker(pdf, center + label_w / 2 + 3.0, base, mark_right)
            y -= row
        pdf.setLineWidth(0.4)
        pdf.line(left, y, left + usable, y)
        pdf.setFont(face(BOLD), 5.0)
        pdf.drawRightString(left + value_w, y - 5.4, _num(a_cats))
        pdf.drawString(left + usable - value_w, y - 5.4, _num(h_cats))
        pdf.setFont(face(NARROW), 4.3)
        pdf.drawCentredString(center, y - 5.3, "TOTAL")
        y -= 7.6
        return team_stats(pdf, [away, home], left, y, usable) - 1.5

    return Block(f"sbc box {matchup.game_id}", "box", 1, draw, -0.6, 0.0, 2.0, priority=priority)


# --------------------------------------------------------------------------
# The reader's matchups: one two-headed box, Blackjack in the middle


def _mine_first(matchup: SbcMatchup, key: str) -> tuple[float, float, float, float]:
    a_pts, h_pts, a_cats, h_cats = matchup.short_score()
    if matchup.side(key) == "away":
        return a_pts, h_pts, a_cats, h_cats
    return h_pts, a_pts, h_cats, a_cats


def reader_box_block(matchups: list[SbcMatchup], key: str = FAVORITE, *,
                     live_days: tuple[int, int] | None = None) -> Block:
    """Opponent A | Blackjack | Opponent B across two columns, Blackjack's stats printed once.

    Each arrow points toward whoever won that category in that matchup. With a
    single opponent it is simply a wide box: Opponent | Blackjack.
    """

    heads = matchups[:2]
    first = heads[0]
    me = first.away if first.away.key == key else first.home
    opponents = [m.opponent(key) for m in heads]
    order = [opponents[0], me] + opponents[1:]

    def draw(pdf, x, top, width, s):
        left, usable = x + 2.0, width - 4.0
        label_w, gap = 30.0, 10.0
        value_w = (usable - label_w - gap * (len(order) - 1)) / len(order)
        starts = [left + label_w + i * (value_w + gap) for i in range(len(order))]
        centers = [start + value_w / 2 for start in starts]
        y = top
        pdf.setFillGray(0)
        results = []
        for matchup in heads:
            mine, theirs, *_ = _mine_first(matchup, key)
            if live_days:
                verdict = "Up" if mine > theirs else "Down" if mine < theirs else "Tied"
            else:
                verdict = "W" if mine > theirs else "L" if mine < theirs else "T"
            results.append(f"{verdict} {_num(mine)}-{_num(theirs)} vs. {matchup.opponent(key).nickname}")
        pdf.setFont("Times-Bold", 9.4)
        pdf.drawCentredString(left + usable / 2, y - 8.4, f"{me.nickname}: " + "   ·   ".join(results))
        y -= 11.0
        pdf.setLineWidth(0.5)
        pdf.line(left, y, left + usable, y)
        pdf.setFont(face(NARROW), 4.3)
        kind = "" if first.kind == "Regular Season" else f"{first.round}, "
        when = f"Day {live_days[0]} of {live_days[1]}" if live_days else _dates(first.start, first.end)
        pdf.drawString(left, y - 5.3, f"{kind}{when}")
        pdf.setFont(face(BOLD), 5.3)
        for center, box in zip(centers, order, strict=True):
            pdf.drawCentredString(center, y - 5.4, _team_head(box))
        y -= 7.0
        pdf.setLineWidth(0.25)
        pdf.line(left, y, left + usable, y)
        y -= 1.4
        row = 5.1 + 0.6 * s
        for category, label in CATEGORIES:
            base = y - row + 1.2
            pdf.setFont(face(BOLD), 4.8)
            pdf.drawString(left, base, label)
            pdf.setFont(face(NARROW), 5.0)
            for center, box in zip(centers, order, strict=True):
                pdf.drawCentredString(center, base, value_text(category, box))
            # A check in each gap when the Blackjack won that category in that matchup; = for a tie.
            for index, matchup in enumerate(heads):
                won = matchup.category_winner(category)
                mark = "check" if won == matchup.side(key) else "=" if won == "tie" else ""
                marker(pdf, starts[1 + index] - gap / 2, base, mark)
            y -= row
        pdf.setLineWidth(0.4)
        pdf.line(left, y, left + usable, y)
        pdf.setFont(face(BOLD), 5.3)
        pdf.drawString(left, y - 5.7, "TOTAL")
        mine_totals, shown = [], {}
        for matchup in heads:
            _, _, my_cats, their_cats = _mine_first(matchup, key)
            shown[matchup.opponent(key).key] = _num(their_cats)
            mine_totals.append(_num(my_cats))
        for center, box in zip(centers, order, strict=True):
            text = " · ".join(mine_totals) if box.key == key else shown[box.key]
            pdf.drawCentredString(center, y - 5.7, text)
        y -= 8.6
        return team_stats(pdf, order, left, y, usable) - 1.5

    return Block("sbc reader box", "box", 2, draw, -0.5, 0.0, 1.5, priority=96)
