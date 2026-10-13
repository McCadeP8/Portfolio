"""Build the first six-page Pearson Press US Letter prototype."""

from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs" / "pearson-press-prototype-v1.pdf"

PAGE_W, PAGE_H = letter
MARGIN = 34
CONTENT_W = PAGE_W - 2 * MARGIN
BLACK = 0
DARK = 0.18
MID = 0.45
LIGHT = 0.88
PALE = 0.95


def gray(c: canvas.Canvas, value: float, *, stroke: bool = False) -> None:
    if stroke:
        c.setStrokeGray(value)
    else:
        c.setFillGray(value)


def rule(c: canvas.Canvas, x1: float, y: float, x2: float, width: float = 0.7) -> None:
    gray(c, BLACK, stroke=True)
    c.setLineWidth(width)
    c.line(x1, y, x2, y)


def label(c: canvas.Canvas, text: str, x: float, y: float, size: float = 7) -> None:
    gray(c, BLACK)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x, y, text.upper())


def fit_line(c: canvas.Canvas, text: str, x: float, y: float, max_width: float,
             font: str, size: float, minimum: float = 8) -> float:
    current = size
    while current > minimum and stringWidth(text, font, current) > max_width:
        current -= 0.25
    c.setFont(font, current)
    c.drawString(x, y, text)
    return current


def wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    *,
    font: str = "Times-Roman",
    size: float = 9,
    leading: float = 11,
    max_lines: int | None = None,
) -> float:
    words_per_line = max(12, int(width / (size * 0.48)))
    lines = wrap(text, width=words_per_line, break_long_words=False)
    if max_lines is not None:
        lines = lines[:max_lines]
    c.setFont(font, size)
    gray(c, BLACK)
    for line_text in lines:
        c.drawString(x, y, line_text)
        y -= leading
    return y


def section_bar(c: canvas.Canvas, title: str, x: float, y: float, width: float,
                *, inverted: bool = True) -> float:
    if inverted:
        gray(c, BLACK)
        c.rect(x, y - 15, width, 17, fill=1, stroke=0)
        gray(c, 1)
    else:
        gray(c, LIGHT)
        c.rect(x, y - 15, width, 17, fill=1, stroke=0)
        gray(c, BLACK)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 6, y - 10, title.upper())
    gray(c, BLACK)
    return y - 21


def masthead(c: canvas.Canvas, page_number: int, section: str) -> None:
    if page_number == 1:
        gray(c, BLACK)
        c.setFont("Times-Bold", 34)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 55, "PEARSON PRESS")
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(
            PAGE_W / 2,
            PAGE_H - 69,
            "TUESDAY, OCTOBER 13, 2026  |  PROTOTYPE EDITION  |  NO. 001  |  $0.00",
        )
        rule(c, MARGIN, PAGE_H - 76, PAGE_W - MARGIN, 1.8)
        rule(c, MARGIN, PAGE_H - 80, PAGE_W - MARGIN, 0.45)
        return

    c.setFont("Times-Bold", 16)
    c.drawString(MARGIN, PAGE_H - 42, "PEARSON PRESS")
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 40, section.upper())
    rule(c, MARGIN, PAGE_H - 49, PAGE_W - MARGIN, 1.2)


def footer(c: canvas.Canvas, page_number: int) -> None:
    rule(c, MARGIN, 27, PAGE_W - MARGIN, 0.45)
    c.setFont("Helvetica", 6.5)
    gray(c, DARK)
    c.drawString(MARGIN, 16, "PEARSON PRESS  |  BLACK-AND-WHITE LETTER PROTOTYPE")
    c.drawRightString(PAGE_W - MARGIN, 16, str(page_number))


def sample_badge(c: canvas.Canvas, x: float, y: float) -> None:
    gray(c, BLACK)
    c.roundRect(x, y - 11, 74, 14, 3, fill=1, stroke=0)
    gray(c, 1)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(x + 37, y - 7, "SAMPLE DATA")
    gray(c, BLACK)


def draw_small_score(c: canvas.Canvas, x: float, y: float, width: float, league: str,
                     away: str, away_score: str, home: str, home_score: str,
                     note: str) -> None:
    gray(c, 1)
    gray(c, BLACK, stroke=True)
    c.setLineWidth(0.6)
    c.rect(x, y - 74, width, 74, fill=1, stroke=1)
    gray(c, BLACK)
    c.rect(x, y - 15, width, 15, fill=1, stroke=0)
    gray(c, 1)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 6, y - 10, league)
    c.drawRightString(x + width - 6, y - 10, "FINAL")
    gray(c, BLACK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 7, y - 32, away)
    c.drawRightString(x + width - 8, y - 32, away_score)
    c.drawString(x + 7, y - 49, home)
    c.drawRightString(x + width - 8, y - 49, home_score)
    c.setFont("Helvetica-Oblique", 6.5)
    gray(c, MID)
    c.drawString(x + 7, y - 65, note)


def draw_table(c: canvas.Canvas, x: float, y: float, widths: list[float],
               rows: list[list[str]], *, header: bool = True,
               row_height: float = 16, font_size: float = 7.2) -> float:
    total = sum(widths)
    for index, row in enumerate(rows):
        top = y - index * row_height
        if index == 0 and header:
            gray(c, BLACK)
            c.rect(x, top - row_height + 2, total, row_height, fill=1, stroke=0)
            gray(c, 1)
            font = "Helvetica-Bold"
        else:
            if index % 2 == 0:
                gray(c, PALE)
                c.rect(x, top - row_height + 2, total, row_height, fill=1, stroke=0)
            gray(c, BLACK)
            font = "Helvetica-Bold" if index > 0 and row[0].startswith("*") else "Helvetica"
        cursor = x
        c.setFont(font, font_size)
        for col, cell in enumerate(row):
            value = cell.lstrip("*")
            if col == 0:
                c.drawString(cursor + 4, top - row_height + 6, value)
            else:
                c.drawRightString(cursor + widths[col] - 4, top - row_height + 6, value)
            cursor += widths[col]
        gray(c, LIGHT, stroke=True)
        c.setLineWidth(0.25)
        c.line(x, top - row_height + 2, x + total, top - row_height + 2)
    return y - len(rows) * row_height


def page_one(c: canvas.Canvas) -> None:
    masthead(c, 1, "Front Page")
    sample_badge(c, MARGIN, PAGE_H - 92)
    c.setFont("Helvetica-Bold", 7)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 99, "6 PAGES  |  PRINTED FOR ONE READER")

    c.setFont("Times-Bold", 31)
    c.drawString(MARGIN, 654, "A NEW MORNING")
    c.drawString(MARGIN, 621, "FOR PEARSON PRESS")
    c.setFont("Times-Italic", 12)
    gray(c, DARK)
    c.drawString(MARGIN, 601, "A personal newspaper finds its voice, one page at a time")
    rule(c, MARGIN, 589, PAGE_W - MARGIN, 0.8)

    left_w = 330
    c.setFont("Helvetica-Bold", 8)
    gray(c, BLACK)
    c.drawString(MARGIN, 572, "BY THE PEARSON PRESS DESIGN DESK")
    story = (
        "This first prototype establishes the daily paper's shape: six portrait pages, "
        "three duplex sheets, strong typography, compact data, and no dependence on color. "
        "The finished system will decide what matters overnight, write from verified facts, "
        "balance every page, and place a fresh edition in the print queue before morning."
    )
    y = wrapped_text(c, story, MARGIN, 555, left_w, size=10, leading=13)
    y -= 7
    story2 = (
        "Nothing here is locked. Headlines, page roles, column density, tables, and recurring "
        "features are all deliberately visible so they can be judged on paper. The goal is not "
        "to imitate a website. It is to create a calm, finite reading experience built around "
        "the teams, leagues, sources, and subjects selected in each publication profile."
    )
    wrapped_text(c, story2, MARGIN, y, left_w, size=9, leading=11.5)

    visual_x = 386
    gray(c, PALE)
    c.rect(visual_x, 424, 192, 155, fill=1, stroke=0)
    gray(c, BLACK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(visual_x + 13, 557, "THE DAILY EDITION")
    c.setFont("Times-Bold", 65)
    c.drawString(visual_x + 13, 487, "06")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(visual_x + 116, 526, "PAGES")
    c.drawString(visual_x + 116, 509, "3 SHEETS")
    c.drawString(visual_x + 116, 492, "2 SIDES")
    rule(c, visual_x + 13, 472, visual_x + 179, 0.5)
    c.setFont("Helvetica", 7)
    c.drawString(visual_x + 13, 457, "LETTER  /  PORTRAIT  /  MONOCHROME")
    c.drawString(visual_x + 13, 443, "AUTOMATED  /  PERSONAL  /  ARCHIVED")

    y0 = 393
    col_gap = 13
    col_w = (CONTENT_W - 2 * col_gap) / 3
    blocks = [
        (
            "INSIDE TODAY",
            "P2  Scoreboard and schedule\nP3  Featured box score\nP4  Standings and trends\nP5  News desk\nP6  Back page",
        ),
        (
            "THE EDITOR'S PROMISE",
            "Useful before exhaustive.\nOriginal before copied.\nReadable before clever.\nPersonal before generic.\nCorrect before fast.",
        ),
        (
            "SUNDAY",
            "The weekend paper expands to 10-12 pages with weekly reviews, projections, long-form features, history, and puzzles.",
        ),
    ]
    for i, (heading, body) in enumerate(blocks):
        x = MARGIN + i * (col_w + col_gap)
        section_bar(c, heading, x, y0, col_w)
        yy = y0 - 31
        for paragraph in body.split("\n"):
            yy = wrapped_text(c, paragraph, x + 1, yy, col_w - 3, size=8.5, leading=11)
        if i < 2:
            rule_x = x + col_w + col_gap / 2
            gray(c, LIGHT, stroke=True)
            c.line(rule_x, 267, rule_x, 393)

    section_bar(c, "Morning Briefing", MARGIN, 242, CONTENT_W)
    briefing = [
        ("SPORT", "Active seasons control the space, while favorite teams remain guaranteed."),
        ("NEWS", "Multiple reports become one concise, attributed briefing instead of repeated headlines."),
        ("PRINT", "Every page is checked for clipping, missing sources, gray contrast, and duplex parity."),
    ]
    bx = MARGIN
    for title, body in briefing:
        label(c, title, bx, 207)
        wrapped_text(c, body, bx, 193, 165, size=8.2, leading=10, max_lines=4)
        bx += 181

    gray(c, PALE)
    c.rect(MARGIN, 62, CONTENT_W, 74, fill=1, stroke=0)
    c.setFont("Times-Bold", 17)
    gray(c, BLACK)
    c.drawString(MARGIN + 14, 108, "Today's question")
    c.setFont("Times-Italic", 12)
    c.drawString(MARGIN + 14, 84, "What should earn a permanent place in your morning paper?")
    c.setFont("Helvetica", 7)
    c.drawRightString(PAGE_W - MARGIN - 14, 70, "DESIGN NOTE 01")
    footer(c, 1)
    c.showPage()


def page_two(c: canvas.Canvas) -> None:
    masthead(c, 2, "Scoreboard")
    sample_badge(c, PAGE_W - MARGIN - 74, PAGE_H - 62)
    c.setFont("Times-Bold", 27)
    c.drawString(MARGIN, 711, "The Scoreboard")
    c.setFont("Times-Italic", 10)
    c.drawString(MARGIN, 694, "Results, schedules, and the games that deserve another look")
    rule(c, MARGIN, 684, PAGE_W - MARGIN, 0.8)

    card_w = (CONTENT_W - 16) / 3
    draw_small_score(c, MARGIN, 666, card_w, "NBA", "DEN", "112", "OKC", "106", "Murray 29 pts")
    draw_small_score(c, MARGIN + card_w + 8, 666, card_w, "NHL", "COL", "4", "DAL", "2", "Georgiev 31 saves")
    draw_small_score(c, MARGIN + 2 * (card_w + 8), 666, card_w, "NFL", "SEA", "24", "DEN", "27", "FG as time expired")

    y = section_bar(c, "Yesterday - All Results", MARGIN, 570, 350)
    results = [
        ["League", "Away", "Home", "Status"],
        ["NBA", "DEN 112", "OKC 106", "Final"],
        ["NBA", "PHX 101", "LAL 109", "Final"],
        ["NHL", "COL 4", "DAL 2", "Final"],
        ["NHL", "MIN 1", "WPG 3", "Final"],
        ["NFL", "SEA 24", "DEN 27", "Final"],
        ["NCAAF", "STATE 31", "TECH 28", "Final"],
    ]
    draw_table(c, MARGIN, y, [55, 88, 88, 119], results, row_height=18)

    sx = 400
    y2 = section_bar(c, "Tonight's Short List", sx, 570, 178)
    games = [
        ("6:00 PM", "BOS at NYK", "NBA"),
        ("7:00 PM", "TOR at COL", "NHL"),
        ("8:30 PM", "GSW at DEN", "NBA"),
        ("9:00 PM", "Top 25 recap", "NCAAM"),
    ]
    for time, game, league in games:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(sx + 2, y2 - 5, time)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(sx + 2, y2 - 20, game)
        c.setFont("Helvetica", 6.5)
        c.drawRightString(sx + 174, y2 - 20, league)
        rule(c, sx, y2 - 29, sx + 178, 0.3)
        y2 -= 47

    y3 = section_bar(c, "What The Editor Would Feature", MARGIN, 386, CONTENT_W)
    c.setFont("Times-Bold", 19)
    c.drawString(MARGIN, y3 - 15, "A finish, a milestone, and a game with consequences")
    wrapped_text(
        c,
        "The selection engine should not reward every final score equally. It should elevate close finishes, favorite teams, records, rivalry games, playoff leverage, and performances that change the shape of a season. This module is where the daily paper becomes editorial rather than encyclopedic.",
        MARGIN,
        y3 - 39,
        CONTENT_W,
        size=9.2,
        leading=12,
        max_lines=4,
    )

    col_w = (CONTENT_W - 14) / 2
    y4 = section_bar(c, "Tomorrow", MARGIN, 284, col_w)
    tomorrow = [
        ["Time", "Matchup", "Why it matters"],
        ["5:30", "BOS at NYK", "East race"],
        ["6:00", "TOR at COL", "Home streak"],
        ["7:00", "GSW at DEN", "Featured"],
        ["8:15", "KC at LV", "Division"],
    ]
    draw_table(c, MARGIN, y4, [44, 98, 122], tomorrow, row_height=19)

    x2 = MARGIN + col_w + 14
    y5 = section_bar(c, "Data Status", x2, 284, col_w)
    statuses = [
        ("Official feeds", "READY"),
        ("Late games", "2 OPEN"),
        ("Injury reports", "UPDATED"),
        ("Source conflicts", "NONE"),
        ("Edition cutoff", "4:00 AM"),
    ]
    for index, (name, status) in enumerate(statuses):
        yy = y5 - index * 25
        c.setFont("Helvetica", 8)
        c.drawString(x2 + 4, yy - 4, name)
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(x2 + col_w - 4, yy - 4, status)
        rule(c, x2, yy - 12, x2 + col_w, 0.25)
    footer(c, 2)
    c.showPage()


def page_three(c: canvas.Canvas) -> None:
    masthead(c, 3, "Featured Box Score")
    sample_badge(c, PAGE_W - MARGIN - 74, PAGE_H - 62)
    c.setFont("Times-Bold", 27)
    c.drawString(MARGIN, 711, "The Featured Game")
    c.setFont("Times-Italic", 10)
    c.drawString(MARGIN, 694, "A long box score should answer the question before the reader asks it")
    rule(c, MARGIN, 684, PAGE_W - MARGIN, 0.8)

    gray(c, PALE)
    c.rect(MARGIN, 594, CONTENT_W, 70, fill=1, stroke=0)
    gray(c, BLACK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN + 12, 646, "NBA  |  FINAL")
    c.setFont("Times-Bold", 23)
    c.drawString(MARGIN + 12, 614, "DENVER 112")
    c.drawRightString(PAGE_W - MARGIN - 12, 614, "OKLAHOMA CITY 106")
    c.setFont("Helvetica", 7)
    c.drawString(MARGIN + 12, 600, "Ball Arena  |  Attendance 19,302  |  2:14  |  Lead changes 14")

    y = section_bar(c, "Scoring By Quarter", MARGIN, 574, CONTENT_W)
    quarters = [
        ["Team", "1", "2", "3", "4", "Total"],
        ["OKC", "25", "29", "24", "28", "106"],
        ["*DEN", "31", "24", "30", "27", "112"],
    ]
    draw_table(c, MARGIN, y, [188, 66, 66, 66, 66, 58], quarters, row_height=19, font_size=8)

    y2 = section_bar(c, "Denver", MARGIN, 484, CONTENT_W)
    den = [
        ["Player", "MIN", "FG", "3PT", "FT", "REB", "AST", "PTS"],
        ["N. Jokic", "37", "11-18", "1-3", "5-6", "14", "11", "28"],
        ["J. Murray", "35", "10-19", "4-8", "5-5", "4", "7", "29"],
        ["A. Gordon", "31", "6-9", "1-2", "2-3", "7", "3", "15"],
        ["M. Porter", "30", "5-12", "3-7", "0-0", "8", "1", "13"],
        ["Bench", "87", "10-24", "3-10", "4-6", "17", "8", "27"],
    ]
    draw_table(c, MARGIN, y2, [124, 45, 61, 55, 50, 52, 52, 55], den, row_height=18)

    y3 = section_bar(c, "Oklahoma City", MARGIN, 343, CONTENT_W)
    okc = [
        ["Player", "MIN", "FG", "3PT", "FT", "REB", "AST", "PTS"],
        ["S. Gilgeous-Alexander", "38", "12-21", "2-5", "7-8", "5", "6", "33"],
        ["J. Williams", "34", "8-16", "2-6", "2-2", "6", "4", "20"],
        ["C. Holmgren", "32", "6-13", "1-4", "3-4", "10", "2", "16"],
        ["L. Dort", "29", "4-11", "2-7", "0-0", "4", "2", "10"],
        ["Bench", "82", "10-28", "3-12", "4-5", "16", "7", "27"],
    ]
    draw_table(c, MARGIN, y3, [124, 45, 61, 55, 50, 52, 52, 55], okc, row_height=18)

    col_w = (CONTENT_W - 14) / 2
    y4 = section_bar(c, "Team Comparison", MARGIN, 200, col_w)
    compare = [
        ["Metric", "OKC", "DEN"],
        ["Field goal %", "47.2", "51.8"],
        ["Three-point %", "32.4", "38.5"],
        ["Rebounds", "41", "50"],
        ["Turnovers", "11", "13"],
    ]
    draw_table(c, MARGIN, y4, [130, 67, 67], compare, row_height=17)

    x2 = MARGIN + col_w + 14
    y5 = section_bar(c, "How It Turned", x2, 200, col_w)
    wrapped_text(
        c,
        "Denver won the final six minutes 18-9, turning second-chance points into the decisive margin. The featured recap would be generated from verified play-by-play and the statistical shape of the game.",
        x2 + 2,
        y5 - 4,
        col_w - 4,
        size=8.4,
        leading=10.5,
        max_lines=7,
    )
    footer(c, 3)
    c.showPage()


def draw_bar(c: canvas.Canvas, x: float, y: float, width: float, value: float,
             maximum: float, label_text: str, value_text: str) -> None:
    c.setFont("Helvetica", 7)
    gray(c, BLACK)
    c.drawString(x, y + 3, label_text)
    c.drawRightString(x + width, y + 3, value_text)
    gray(c, LIGHT)
    c.rect(x, y - 7, width, 6, fill=1, stroke=0)
    gray(c, BLACK)
    c.rect(x, y - 7, width * value / maximum, 6, fill=1, stroke=0)


def page_four(c: canvas.Canvas) -> None:
    masthead(c, 4, "Standings & Trends")
    sample_badge(c, PAGE_W - MARGIN - 74, PAGE_H - 62)
    c.setFont("Times-Bold", 27)
    c.drawString(MARGIN, 711, "Standings & Trends")
    c.setFont("Times-Italic", 10)
    c.drawString(MARGIN, 694, "The season at a glance, with enough context to make the numbers useful")
    rule(c, MARGIN, 684, PAGE_W - MARGIN, 0.8)

    col_w = (CONTENT_W - 14) / 2
    y = section_bar(c, "NBA West", MARGIN, 666, col_w)
    west = [
        ["Team", "W", "L", "Pct", "GB"],
        ["*Denver", "48", "21", ".696", "-"],
        ["Oklahoma City", "47", "22", ".681", "1.0"],
        ["Minnesota", "45", "24", ".652", "3.0"],
        ["Phoenix", "41", "28", ".594", "7.0"],
        ["Dallas", "40", "29", ".580", "8.0"],
        ["New Orleans", "39", "30", ".565", "9.0"],
        ["Sacramento", "38", "31", ".551", "10.0"],
    ]
    draw_table(c, MARGIN, y, [116, 37, 37, 42, 32], west, row_height=18)

    x2 = MARGIN + col_w + 14
    y2 = section_bar(c, "NHL Central", x2, 666, col_w)
    central = [
        ["Team", "GP", "W", "L", "PTS"],
        ["*Colorado", "72", "45", "21", "96"],
        ["Dallas", "72", "43", "22", "94"],
        ["Winnipeg", "71", "42", "21", "92"],
        ["Nashville", "72", "40", "25", "87"],
        ["Minnesota", "72", "34", "29", "77"],
        ["St. Louis", "71", "33", "30", "74"],
        ["Arizona", "72", "29", "36", "65"],
    ]
    draw_table(c, x2, y2, [116, 37, 37, 37, 37], central, row_height=18)

    y3 = section_bar(c, "Five Numbers To Know", MARGIN, 476, CONTENT_W)
    stats = [
        ("1", "48-21", "Denver's sample record and the anchor for today's standings page."),
        ("2", "+7.4", "Net rating across the most recent ten games."),
        ("3", "31", "Shots stopped in Colorado's featured win."),
        ("4", "14", "Lead changes in the game of the night."),
        ("5", "3", "Double-sided sheets in the finished daily paper."),
    ]
    stat_y = y3 - 4
    for num, stat, desc in stats:
        c.setFont("Times-Bold", 18)
        c.drawString(MARGIN + 4, stat_y - 12, num)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(MARGIN + 34, stat_y - 10, stat)
        c.setFont("Helvetica", 7.6)
        c.drawString(MARGIN + 94, stat_y - 9, desc)
        rule(c, MARGIN, stat_y - 21, PAGE_W - MARGIN, 0.25)
        stat_y -= 35

    y4 = section_bar(c, "Form Guide - Last 10", MARGIN, 269, col_w)
    draw_bar(c, MARGIN + 4, y4 - 7, col_w - 8, 8, 10, "Denver", "8-2")
    draw_bar(c, MARGIN + 4, y4 - 34, col_w - 8, 7, 10, "Oklahoma City", "7-3")
    draw_bar(c, MARGIN + 4, y4 - 61, col_w - 8, 6, 10, "Minnesota", "6-4")
    draw_bar(c, MARGIN + 4, y4 - 88, col_w - 8, 5, 10, "Phoenix", "5-5")

    y5 = section_bar(c, "Playoff Pressure", x2, 269, col_w)
    wrapped_text(
        c,
        "Standings should reveal movement, not merely rank. The final module can flag clinching scenarios, elimination numbers, games back, recent form, strength of schedule, and changes since yesterday's edition.",
        x2 + 2,
        y5 - 5,
        col_w - 4,
        size=8.5,
        leading=11,
        max_lines=8,
    )
    footer(c, 4)
    c.showPage()


def page_five(c: canvas.Canvas) -> None:
    masthead(c, 5, "News Desk")
    sample_badge(c, PAGE_W - MARGIN - 74, PAGE_H - 62)
    c.setFont("Times-Bold", 27)
    c.drawString(MARGIN, 711, "The News Desk")
    c.setFont("Times-Italic", 10)
    c.drawString(MARGIN, 694, "A finite briefing assembled from the sources selected in your profile")
    rule(c, MARGIN, 684, PAGE_W - MARGIN, 0.8)

    left_w = 340
    c.setFont("Times-Bold", 25)
    c.drawString(MARGIN, 645, "One event, one clear briefing")
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(MARGIN, 625, "THE PEARSON PRESS NEWSROOM")
    paragraphs = [
        "A useful morning paper should reduce repetition. When several enabled publishers cover the same event, Pearson Press will cluster their reporting, preserve each source, compare factual claims, and produce one original summary.",
        "The profile decides which publishers may contribute. The editorial engine then weighs freshness, authority, personal relevance, geographic importance, and whether the story has materially changed since the prior edition.",
        "This prototype reserves one page for general sports and world news. On a quiet day, it may hold short briefs. On a consequential day, one story can take the lead while the rest move into a narrow digest.",
    ]
    yy = 608
    for paragraph in paragraphs:
        yy = wrapped_text(c, paragraph, MARGIN, yy, left_w, size=9.1, leading=12)
        yy -= 9

    x2 = 395
    y2 = section_bar(c, "World Briefs", x2, 654, 183)
    briefs = [
        ("LEAD", "Major development receives a verified, multi-source summary."),
        ("ECONOMY", "A compact indicator and a sentence explaining why it matters."),
        ("SCIENCE", "Research news appears with clear uncertainty and attribution."),
        ("CULTURE", "One worthwhile item, selected for interest rather than volume."),
    ]
    for tag, body in briefs:
        label(c, tag, x2 + 2, y2 - 2)
        y2 = wrapped_text(c, body, x2 + 2, y2 - 16, 178, size=7.8, leading=9.5)
        y2 -= 12
        rule(c, x2, y2 + 5, x2 + 183, 0.25)

    y3 = section_bar(c, "Source Mix", MARGIN, 357, CONTENT_W)
    providers = [
        ["Provider", "Role", "Profile", "Status"],
        ["Official league feeds", "Scores and statistics", "ON", "Ready"],
        ["ESPN", "Sports reporting", "OPTIONAL", "Review"],
        ["Fox News", "World and national", "OPTIONAL", "Review"],
        ["Local weather", "Morning forecast", "ON", "Ready"],
        ["Additional providers", "Future capabilities", "OFF", "Available"],
    ]
    draw_table(c, MARGIN, y3, [145, 175, 85, 105], providers, row_height=20, font_size=7.5)

    col_w = (CONTENT_W - 14) / 2
    y4 = section_bar(c, "Editorial Guardrails", MARGIN, 204, col_w)
    guards = [
        "Facts trace back to human-readable sources.",
        "No article text is copied into the edition.",
        "Conflicting claims are flagged, not blended.",
        "Opinion and reporting remain visibly distinct.",
    ]
    for idx, item in enumerate(guards, start=1):
        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN + 4, y4 - idx * 22 + 10, f"{idx:02d}")
        c.setFont("Helvetica", 7.5)
        c.drawString(MARGIN + 28, y4 - idx * 22 + 10, item)

    x3 = MARGIN + col_w + 14
    y5 = section_bar(c, "Weather", x3, 204, col_w)
    c.setFont("Times-Bold", 32)
    c.drawString(x3 + 4, y5 - 39, "54 / 31")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x3 + 144, y5 - 22, "CLEAR START")
    c.drawString(x3 + 144, y5 - 38, "WIND W 8")
    c.setFont("Helvetica", 7)
    c.drawString(x3 + 4, y5 - 65, "A compact forecast belongs on page one; details can live here.")
    footer(c, 5)
    c.showPage()


def page_six(c: canvas.Canvas) -> None:
    masthead(c, 6, "Back Page")
    sample_badge(c, PAGE_W - MARGIN - 74, PAGE_H - 62)
    gray(c, BLACK)
    c.rect(MARGIN, 572, CONTENT_W, 132, fill=1, stroke=0)
    gray(c, 1)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN + 16, 677, "THE BACK PAGE")
    c.setFont("Times-Bold", 31)
    c.drawString(MARGIN + 16, 634, "Tomorrow starts tonight")
    c.setFont("Times-Italic", 12)
    c.drawString(MARGIN + 16, 607, "The viewing guide, one last number, and room to have some fun")
    c.setFont("Helvetica", 7)
    c.drawRightString(PAGE_W - MARGIN - 16, 585, "END OF PROTOTYPE EDITION")

    col_w = (CONTENT_W - 14) / 2
    y = section_bar(c, "Tomorrow At A Glance", MARGIN, 547, col_w)
    schedule = [
        ["Time", "Event", "Desk"],
        ["5:30", "BOS at NYK", "NBA"],
        ["6:00", "TOR at COL", "NHL"],
        ["7:00", "GSW at DEN", "NBA"],
        ["8:15", "KC at LV", "NFL"],
        ["All day", "News monitor", "World"],
    ]
    draw_table(c, MARGIN, y, [50, 140, 74], schedule, row_height=20)

    x2 = MARGIN + col_w + 14
    y2 = section_bar(c, "On This Day", x2, 547, col_w)
    c.setFont("Times-Bold", 42)
    c.drawString(x2 + 2, y2 - 45, "13")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x2 + 79, y2 - 20, "OCTOBER")
    c.setFont("Helvetica", 8)
    wrapped_text(
        c,
        "A historical sports note can rotate here, sourced from the archive and checked before publication.",
        x2 + 79,
        y2 - 38,
        col_w - 83,
        size=8,
        leading=10,
        max_lines=5,
    )

    y3 = section_bar(c, "The Six-Word Puzzle", MARGIN, 392, CONTENT_W)
    words = ["PRESS", "SCORE", "STORY", "STATS", "DAILY", "PRINT"]
    grid_x = MARGIN + 6
    grid_y = y3 - 13
    cell = 24
    letters = [
        "PRESSQDAILYV",
        "XSTORYLMNOPR",
        "SCOREABCDSTU",
        "QWERTYSTATSZ",
        "PRINTFGHIJKL",
        "MORNINGPAPER",
    ]
    for row, row_text in enumerate(letters):
        for col, char in enumerate(row_text):
            xx = grid_x + col * cell
            yy = grid_y - row * cell
            gray(c, LIGHT, stroke=True)
            c.rect(xx, yy - cell, cell, cell, fill=0, stroke=1)
            gray(c, BLACK)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(xx + cell / 2, yy - 16, char)
    list_x = 360
    c.setFont("Times-Bold", 15)
    c.drawString(list_x, grid_y - 7, "Find six words")
    c.setFont("Helvetica", 9)
    for idx, word in enumerate(words):
        c.drawString(list_x + (idx % 2) * 90, grid_y - 31 - (idx // 2) * 24, word)
    wrapped_text(
        c,
        "Sunday editions can reserve more room for a crossword, trivia, rankings, history, and a full week-ahead planner.",
        list_x,
        grid_y - 112,
        210,
        size=8,
        leading=10,
        max_lines=5,
    )

    gray(c, PALE)
    c.rect(MARGIN, 60, CONTENT_W, 79, fill=1, stroke=0)
    gray(c, BLACK)
    c.setFont("Times-Bold", 18)
    c.drawString(MARGIN + 14, 111, "The prototype is the conversation starter.")
    c.setFont("Times-Italic", 10)
    c.drawString(MARGIN + 14, 88, "Circle what works. Cross out what does not. The next issue gets better.")
    c.setFont("Helvetica-Bold", 7)
    c.drawRightString(PAGE_W - MARGIN - 14, 70, "PEARSON PRESS  /  ISSUE 001")
    footer(c, 6)
    c.showPage()


def build() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(OUTPUT), pagesize=letter, pageCompression=1)
    pdf.setTitle("Pearson Press Prototype V1")
    pdf.setAuthor("Pearson Press")
    pdf.setSubject("Six-page black-and-white US Letter newspaper prototype")
    for page in (page_one, page_two, page_three, page_four, page_five, page_six):
        page(pdf)
    pdf.save()
    return OUTPUT


if __name__ == "__main__":
    print(build())
