"""Original black-and-white data graphics drawn from ESPN play data.

Print rules (no color, no hover): one y-axis per chart, thin marks, identity by
direct label and marker shape (filled vs. open), never by tone alone.
"""

from __future__ import annotations

from typing import Any

from reportlab.pdfgen.canvas import Canvas

from pearson_press.edition.blocks import Block
from pearson_press.publication.fonts import face

INK = 0.0
GRID = 0.78


def _caption(pdf: Canvas, title: str, note: str, x: float, top: float, width: float) -> float:
    pdf.setFillGray(INK)
    pdf.setFont(face("PP-Narrow-Bold"), 5.8)
    pdf.drawString(x, top - 5.8, title.upper())
    pdf.setFont(face("PP-Narrow"), 4.8)
    pdf.drawString(x, top - 12.0, note)
    return top - 16.0


def _source(pdf: Canvas, x: float, y: float) -> float:
    pdf.setFont("Times-Italic", 4.4)
    pdf.drawString(x, y - 4.6, "Pearson Press graphic | Data: ESPN")
    return y - 7.0


# --------------------------------------------------------------------------
# Win probability: one line, one axis (home team's chance to win, 0-100%)


def win_probability_block(summary: dict[str, Any], away: str, home: str, title: str, *, span: int = 1) -> Block | None:
    points = [float(p.get("homeWinPercentage", 0.5)) for p in summary.get("winprobability", [])]
    if len(points) < 8:
        return None

    def draw(pdf, x, top, width, s):
        left = x + 2.0
        usable = width - 4.0
        y = _caption(pdf, title, f"{home}'s chance to win, play by play", left, top, usable)
        plot_h = 58.0 + 30.0 * s
        label_w = 14.0
        px, pw = left + label_w, usable - label_w
        base = y - plot_h
        # Recessive grid: 0 / 50 / 100 with the 50% line dashed.
        for value in (0.0, 0.5, 1.0):
            gy = base + value * plot_h
            pdf.setStrokeGray(GRID)
            pdf.setLineWidth(0.3)
            if value == 0.5:
                pdf.setDash(1.5, 1.5)
            pdf.line(px, gy, px + pw, gy)
            pdf.setDash()
            pdf.setFillGray(0.35)
            pdf.setFont(face("PP-Narrow"), 4.2)
            pdf.drawRightString(px - 2.0, gy - 1.4, f"{int(value * 100)}%")
        # Direct team labels at the two poles of the axis.
        pdf.setFillGray(INK)
        pdf.setFont(face("PP-Narrow-Bold"), 4.6)
        pdf.drawString(px + 2.0, base + plot_h - 6.0, f"{home.upper()} WIN")
        pdf.drawString(px + 2.0, base + 2.5, f"{away.upper()} WIN")
        # The line (2px-equivalent at print scale).
        path = pdf.beginPath()
        step = pw / (len(points) - 1)
        for index, value in enumerate(points):
            point = (px + index * step, base + value * plot_h)
            path.moveTo(*point) if index == 0 else path.lineTo(*point)
        pdf.setStrokeGray(INK)
        pdf.setLineWidth(1.0)
        pdf.drawPath(path, stroke=1, fill=0)
        # Mark and label only the final value.
        end_x, end_y = px + pw, base + points[-1] * plot_h
        pdf.circle(end_x, end_y, 1.6, stroke=0, fill=1)
        pdf.setFont(face("PP-Narrow"), 4.2)
        pdf.drawRightString(px + pw, base - 6.0, "Final")
        pdf.drawString(px, base - 6.0, "Start")
        return _source(pdf, left, base - 7.0)

    return Block(f"winprob {title}", "graphic", span, draw, 0.0, 0.0, 1.0, priority=40)


# --------------------------------------------------------------------------
# NHL shot map: every shot on goal and goal, each team attacking one end


def _rink(pdf: Canvas, x: float, y: float, w: float, h: float) -> None:
    radius = h * 0.32
    pdf.setStrokeGray(INK)
    pdf.setLineWidth(0.6)
    pdf.roundRect(x, y, w, h, radius, stroke=1, fill=0)
    pdf.setStrokeGray(GRID)
    pdf.setLineWidth(0.4)
    pdf.line(x + w / 2, y, x + w / 2, y + h)  # center line
    for blue in (0.375, 0.625):  # blue lines at +/-25 ft of 200
        pdf.line(x + w * blue, y, x + w * blue, y + h)
    for goal in (0.055, 0.945):  # goal lines at 89 ft
        pdf.line(x + w * goal, y + h * 0.08, x + w * goal, y + h * 0.92)
    pdf.circle(x + w / 2, y + h / 2, h * 0.18, stroke=1, fill=0)


def shot_map_block(summary: dict[str, Any], away: dict[str, str], home: dict[str, str], title: str,
                   *, span: int = 1) -> Block | None:
    """``away``/``home``: {"id", "abbreviation"}. Away attacks left, home attacks right."""

    shots = []
    for play in summary.get("plays", []):
        kind = play.get("type", {}).get("text", "")
        team = str(play.get("team", {}).get("id", ""))
        coord = play.get("coordinate") or {}
        if kind not in {"Shot", "Goal"} or team not in {away["id"], home["id"]} or "x" not in coord:
            continue
        sx, sy = float(coord["x"]), float(coord["y"])
        attacking_right = team == home["id"]
        if (sx < 0) == attacking_right:  # mirror so each team keeps one end
            sx, sy = -sx, -sy
        shots.append((team, kind == "Goal", sx, sy))
    if len(shots) < 10:
        return None

    def draw(pdf, x, top, width, s):
        left = x + 2.0
        usable = width - 4.0
        counts = {team: sum(1 for t, *_ in shots if t == team) for team in (away["id"], home["id"])}
        goals = {team: sum(1 for t, g, *_ in shots if t == team and g) for team in (away["id"], home["id"])}
        y = _caption(pdf, title, "Shots on goal (open) and goals (filled)", left, top, usable)
        rink_h = usable * 85 / 200
        base = y - rink_h - 1.0
        _rink(pdf, left, base, usable, rink_h)
        for team, goal, sx, sy in sorted(shots, key=lambda item: item[1]):  # goals drawn on top
            mx = left + (sx + 100) / 200 * usable
            my = base + (sy + 42.5) / 85 * rink_h
            pdf.setStrokeGray(INK)
            pdf.setLineWidth(0.45)
            size = 1.9 if goal else 1.5
            if team == away["id"]:
                pdf.circle(mx, my, size, stroke=1, fill=1 if goal else 0)
            else:
                pdf.rect(mx - size, my - size, size * 2, size * 2, stroke=1, fill=1 if goal else 0)
        # Direct labels under each end name the shooter and the marker shape.
        pdf.setFont(face("PP-Narrow-Bold"), 4.7)
        label_y = base - 6.5
        pdf.circle(left + 2.0, label_y + 1.5, 1.6, stroke=1, fill=0)
        pdf.drawString(left + 5.5, label_y,
                       f"{away['abbreviation']} attacking: {counts[away['id']]} SOG, {goals[away['id']]} G")
        text = f"{home['abbreviation']} attacking: {counts[home['id']]} SOG, {goals[home['id']]} G"
        tw = pdf.stringWidth(text, face("PP-Narrow-Bold"), 4.7)
        pdf.rect(left + usable - tw - 7.0, label_y, 3.2, 3.2, stroke=1, fill=0)
        pdf.drawRightString(left + usable, label_y, text)
        return _source(pdf, left, label_y - 2.0)

    return Block(f"shotmap {title}", "graphic", span, draw, 0.0, 0.0, 0.0, priority=40)


# --------------------------------------------------------------------------
# Postseason bracket: earlier rounds feed the current ones


def bracket_block(series_list: list[Any], title: str = "Road to the World Series") -> Block | None:
    """Vertical bracket per league: two division series feed the LCS box."""

    by_league: dict[str, dict[str, list[Any]]] = {}
    world_series = None
    for series in series_list:
        name = series.round_name
        if "World Series" in name:
            world_series = series
            continue
        league = name[:2]
        if league not in {"AL", "NL"}:
            continue
        stage = "CS" if name.endswith("CS") else "DS" if name.endswith("DS") else ""
        if stage:
            by_league.setdefault(league, {}).setdefault(stage, []).append(series)
    if not by_league:
        return None

    def label(series: Any) -> tuple[str, str]:
        (a, b), (wa, wb) = series.teams, series.wins
        if series.is_over:
            winner, loser = (a, b) if wa > wb else (b, a)
            return f"{winner.name} def. {loser.name}", f"{max(wa, wb)}-{min(wa, wb)}"
        return f"{a.name} vs. {b.name}", series.summary.replace("leads series", "leads").replace("Series ", "")

    def box(pdf, x, y, w, series, *, bold=False):
        h = 15.0
        pdf.setLineWidth(0.8 if bold else 0.45)
        pdf.rect(x, y - h, w, h, stroke=1, fill=0)
        top_line, bottom_line = label(series)
        pdf.setFont(face("PP-Narrow-Bold" if bold else "PP-Narrow"), 4.9)
        pdf.drawString(x + 2.5, y - 6.2, top_line)
        pdf.setFont(face("PP-Narrow"), 4.4)
        pdf.drawString(x + 2.5, y - 12.2, bottom_line)
        return y - h / 2

    def draw(pdf, x, top, width, s):
        left = x + 2.0
        usable = width - 4.0
        y = _caption(pdf, title, "Division series feed each league championship series", left, top, usable)
        half = usable * 0.52
        cs_x = left + usable - half
        for league in ("AL", "NL"):
            rounds = by_league.get(league)
            if not rounds:
                continue
            pdf.setFont(face("PP-Narrow-Bold"), 5.2)
            pdf.drawString(left, y - 6.0, "AMERICAN LEAGUE" if league == "AL" else "NATIONAL LEAGUE")
            y -= 9.0
            mids = []
            for index, series in enumerate(rounds.get("DS", [])[:2]):
                mids.append(box(pdf, left, y - index * (19.0 + 4 * s), half - 8.0, series))
            if rounds.get("CS"):
                cs_mid = (sum(mids) / len(mids)) if mids else y - 8.0
                pdf.setLineWidth(0.45)
                for mid in mids:  # connectors: out, down/up, in
                    pdf.line(left + half - 8.0, mid, left + half - 4.0, mid)
                    pdf.line(left + half - 4.0, mid, left + half - 4.0, cs_mid)
                pdf.line(left + half - 4.0, cs_mid, cs_x, cs_mid)
                box(pdf, cs_x, cs_mid + 7.5, half, rounds["CS"][0], bold=True)
            y -= 2 * (19.0 + 4 * s) + 4.0
        pdf.setFont(face("PP-Narrow-Bold"), 5.2)
        pdf.drawString(left, y - 6.0, "WORLD SERIES")
        y -= 9.0
        if world_series is not None:
            box(pdf, left, y, usable, world_series, bold=True)
        else:
            pdf.setDash(1.2, 1.2)
            pdf.setLineWidth(0.45)
            pdf.rect(left, y - 15.0, usable, 15.0, stroke=1, fill=0)
            pdf.setDash()
            pdf.setFont(face("PP-Narrow"), 4.9)
            pdf.drawString(left + 2.5, y - 9.5, "AL champion vs. NL champion")
        y -= 15.0
        return _source(pdf, left, y - 2.0)

    return Block(f"bracket {title}", "graphic", 1, draw, 0.0, 0.0, 2.0, priority=45)


# --------------------------------------------------------------------------
# Ranked bars: one measure, one axis, every bar directly labeled


def ranked_bars_block(title: str, note: str, rows: list[tuple[str, float, str]], *,
                      diverging: bool = False, extra: list[str] | None = None,
                      heads: tuple[str, str] | None = None) -> Block | None:
    """``rows``: (label, value, value text). Diverging bars split at zero:
    solid for positive, open for negative, so sign never depends on tone."""

    if len(rows) < 4:
        return None

    def draw(pdf, x, top, width, s):
        left = x + 2.0
        usable = width - 4.0
        y = _caption(pdf, title, note, left, top, usable)
        label_w, value_w = 46.0, 16.0 + (20.0 if extra else 0.0)
        plot_x = left + label_w
        plot_w = usable - label_w - value_w
        biggest = max(abs(value) for _, value, _ in rows) or 1.0
        zero = plot_x + (plot_w / 2 if diverging else 0.0)
        scale = (plot_w / 2 if diverging else plot_w) / biggest
        row_h = 5.6 + s
        if heads:
            pdf.setFont(face("PP-Narrow-Bold"), 4.2)
            pdf.drawRightString(left + usable - (20.0 if extra else 0.0), y - 4.0, heads[0])
            if extra:
                pdf.drawRightString(left + usable, y - 4.0, heads[1])
            y -= 5.0
        if diverging:
            pdf.setStrokeGray(GRID)
            pdf.setLineWidth(0.3)
            pdf.line(zero, y + 1.0, zero, y - row_h * len(rows))
        for index, (name, value, shown) in enumerate(rows):
            ry = y - (index + 1) * row_h
            pdf.setFillGray(INK)
            pdf.setFont(face("PP-Narrow"), 4.6)
            pdf.drawString(left, ry + 1.2, name)
            bar = value * scale
            pdf.setStrokeGray(INK)
            pdf.setLineWidth(0.4)
            pdf.rect(min(zero, zero + bar), ry + 0.8, abs(bar), row_h - 1.8,
                     stroke=1, fill=0 if value < 0 else 1)
            pdf.setFillGray(INK)
            if extra:
                pdf.drawRightString(left + usable - 20.0, ry + 1.2, shown)
                pdf.drawRightString(left + usable, ry + 1.2, extra[index])
            else:
                pdf.drawRightString(left + usable, ry + 1.2, shown)
        return _source(pdf, left, y - row_h * len(rows) - 2.0)

    return Block(f"bars {title}", "graphic", 1, draw, 0.0, 0.0, 1.2, priority=42)
