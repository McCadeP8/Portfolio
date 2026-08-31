from __future__ import annotations

import csv
import math
import re
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SFB_ROOT = ROOT.parent / "SFB_Prep"
RANKINGS = ROOT / "output" / "csv" / "Smack_Talkers_2026_Personal_Rankings_With_Tiers.csv"
FIRST_DOWNS = SFB_ROOT / "sfb_projection_cheat_sheet.csv"
OUTPUT = ROOT / "output" / "first-down-value-one-pager.png"

W, H = 1800, 2400
BG = "#09111f"
PANEL = "#111d30"
PANEL_2 = "#0d1728"
TEXT = "#f3f7fb"
MUTED = "#9fb0c6"
LINE = "#26364b"
GREEN = "#42d39b"
GREEN_SOFT = "#173d35"
RED = "#ff7585"
RED_SOFT = "#45232e"
GOLD = "#f4c95d"
BLUE = "#61a8ff"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size=size)


F_TITLE = font(62, True)
F_SUBTITLE = font(25)
F_PANEL = font(32, True)
F_GROUP = font(22, True)
F_HEADER = font(18, True)
F_ROW = font(20)
F_ROW_BOLD = font(20, True)
F_SMALL = font(17)
F_SMALL_BOLD = font(17, True)
F_IMPACT = font(25, True)


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    tokens = re.sub(r"[^a-z0-9 ]", " ", normalized).split()
    return "".join(token for token in tokens if token not in {"jr", "sr", "ii", "iii", "iv"})


def load_players() -> list[dict]:
    with FIRST_DOWNS.open(encoding="utf-8-sig", newline="") as handle:
        first_down_rows = list(csv.DictReader(handle))
    first_down_map = {normalize_name(row["player"]): row for row in first_down_rows}

    players: list[dict] = []
    with RANKINGS.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["Pos"] not in {"QB", "RB", "WR", "TE"}:
                continue
            fd_row = first_down_map.get(normalize_name(row["Player"]))
            if not fd_row:
                continue
            projected_points = float(row["Proj"])
            first_downs = float(fd_row["projected_first_downs"] or 0)
            bonus = 0.5 * first_downs
            players.append(
                {
                    "player": row["Player"],
                    "pos": row["Pos"],
                    "points": projected_points,
                    "first_downs": first_downs,
                    "bonus": bonus,
                    "adjusted": projected_points + bonus,
                    "lift": 100 * bonus / projected_points if projected_points else 0,
                }
            )

    for position in ("QB", "RB", "WR", "TE"):
        pool = [player for player in players if player["pos"] == position]
        before = sorted(pool, key=lambda player: player["points"], reverse=True)
        after = sorted(pool, key=lambda player: player["adjusted"], reverse=True)
        before_rank = {player["player"]: rank for rank, player in enumerate(before, 1)}
        after_rank = {player["player"]: rank for rank, player in enumerate(after, 1)}
        for player in pool:
            player["before_rank"] = before_rank[player["player"]]
            player["after_rank"] = after_rank[player["player"]]
            player["rank_change"] = player["before_rank"] - player["after_rank"]
    return players


def ranked_lists(players: list[dict], position: str, count: int) -> tuple[list[dict], list[dict]]:
    pool = [player for player in players if player["pos"] == position]
    # The requested value change is purely the percentage of a player's original
    # projection supplied by first-down scoring.
    risers = sorted(pool, key=lambda player: player["lift"], reverse=True)[:count]
    riser_names = {player["player"] for player in risers}
    fallers = sorted(
        [player for player in pool if player["player"] not in riser_names],
        key=lambda player: player["lift"],
    )[:count]
    return risers, fallers


def round_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, radius: int = 24) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, base: ImageFont.FreeTypeFont) -> str:
    if draw.textbbox((0, 0), text, font=base)[2] <= max_width:
        return text
    clipped = text
    while clipped and draw.textbbox((0, 0), clipped + "…", font=base)[2] > max_width:
        clipped = clipped[:-1]
    return clipped + "…"


def draw_player_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    risers: list[dict],
    fallers: list[dict],
) -> None:
    x0, y0, x1, y1 = box
    round_rect(draw, box, PANEL)
    draw.text((x0 + 28, y0 + 20), title, fill=TEXT, font=F_PANEL)
    draw.text((x1 - 28, y0 + 31), "base pts  |  +1D pts  |  lift", fill=MUTED, font=F_SMALL, anchor="ra")
    cursor_y = y0 + 72
    row_count = len(risers) + len(fallers)
    available = y1 - cursor_y - 20
    row_h = max(30, min(39, math.floor((available - 82) / row_count)))

    def group(label: str, color: str, soft: str, rows: list[dict], direction: str) -> None:
        nonlocal cursor_y
        draw.rounded_rectangle((x0 + 22, cursor_y, x1 - 22, cursor_y + 34), radius=12, fill=soft)
        draw.text((x0 + 36, cursor_y + 5), label, fill=color, font=F_GROUP)
        cursor_y += 42
        for index, player in enumerate(rows, 1):
            if index % 2 == 0:
                draw.rectangle((x0 + 22, cursor_y, x1 - 22, cursor_y + row_h), fill=PANEL_2)
            draw.text((x0 + 32, cursor_y + 5), f"{index:>2}", fill=MUTED, font=F_ROW)
            player_name = fit_text(draw, player["player"], 330, F_ROW_BOLD)
            draw.text((x0 + 76, cursor_y + 5), player_name, fill=TEXT, font=F_ROW_BOLD)
            draw.text((x1 - 285, cursor_y + 5), f"{player['points']:.1f}", fill=MUTED, font=F_ROW, anchor="ra")
            draw.text((x1 - 145, cursor_y + 5), f"+{player['bonus']:.1f}", fill=TEXT, font=F_ROW, anchor="ra")
            draw.text((x1 - 34, cursor_y + 5), f"{player['lift']:.1f}%", fill=color, font=F_ROW_BOLD, anchor="ra")
            cursor_y += row_h
        cursor_y += 10

    group(f"HIGHEST 1D LIFT — TOP {len(risers)}", GREEN, GREEN_SOFT, risers, "up")
    group(f"LOWEST 1D LIFT — BOTTOM {len(fallers)}", RED, RED_SOFT, fallers, "down")


def draw_position_impact(draw: ImageDraw.ImageDraw, players: list[dict], box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    round_rect(draw, box, PANEL)
    draw.text((x0 + 28, y0 + 20), "WHO GAINS RELATIVE TO THE OTHER POSITIONS?", fill=TEXT, font=F_PANEL)
    draw.text(
        (x0 + 28, y0 + 65),
        "Typical 12-team 1QB starters · average percentage lift from first downs",
        fill=MUTED,
        font=F_SMALL,
    )

    starter_counts = {"RB": 24, "WR": 36, "TE": 12, "QB": 12}
    stats = []
    for position in ("RB", "WR", "TE", "QB"):
        pool = sorted(
            [player for player in players if player["pos"] == position],
            key=lambda player: player["points"],
            reverse=True,
        )[: starter_counts[position]]
        average_bonus = sum(player["bonus"] for player in pool) / len(pool)
        average_lift = sum(player["lift"] for player in pool) / len(pool)
        stats.append((position, average_lift, average_bonus / 17))

    max_lift = max(item[1] for item in stats)
    chart_x = x0 + 55
    chart_y = y0 + 112
    label_w = 70
    bar_w = 545
    row_h = 54
    colors = {"RB": GREEN, "WR": BLUE, "TE": GOLD, "QB": RED}
    for index, (position, lift, per_game) in enumerate(stats):
        y = chart_y + index * row_h
        draw.text((chart_x, y + 7), position, fill=TEXT, font=F_IMPACT)
        draw.rounded_rectangle((chart_x + label_w, y + 9, chart_x + label_w + bar_w, y + 34), radius=12, fill=LINE)
        filled = int(bar_w * lift / max_lift)
        draw.rounded_rectangle((chart_x + label_w, y + 9, chart_x + label_w + filled, y + 34), radius=12, fill=colors[position])
        draw.text(
            (chart_x + label_w + bar_w + 25, y + 5),
            f"{lift:.1f}% lift  (+{per_game:.2f}/game)",
            fill=TEXT,
            font=F_ROW_BOLD,
        )

    note_x = x0 + 980
    draw.text((note_x, y0 + 112), "DRAFT-ROOM TRANSLATION", fill=GOLD, font=F_GROUP)
    bullets = [
        ("RB ↑↑", "Largest percentage lift; volume backs gain against the field."),
        ("WR ↑", "Second-largest lift; chain movers beat low-volume deep threats."),
        ("TE ↔", "Moderate lift, but little new positional separation."),
        ("QB ↓", "Smallest lift by far; rushing QBs are the exceptions."),
    ]
    for index, (lead, body) in enumerate(bullets):
        y = y0 + 154 + index * 52
        draw.text((note_x, y), lead, fill=colors.get(lead[:2], TEXT), font=F_SMALL_BOLD)
        draw.text((note_x + 95, y), body, fill=TEXT, font=F_SMALL)


def main() -> None:
    players = load_players()
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)

    draw.text((70, 54), "0.5 POINT PER FIRST DOWN", fill=TEXT, font=F_TITLE)
    draw.text((70, 127), "2026 percentage lift — rushing + receiving first downs only", fill=BLUE, font=F_SUBTITLE)
    draw.text(
        (1730, 82),
        "LIFT = FIRST-DOWN BONUS ÷ BASE PROJECTION\nExample: 100 points → 110 points = 10% lift",
        fill=MUTED,
        font=F_SMALL,
        anchor="ra",
        spacing=7,
    )
    draw.line((70, 183, 1730, 183), fill=LINE, width=2)

    rb_up, rb_down = ranked_lists(players, "RB", 10)
    wr_up, wr_down = ranked_lists(players, "WR", 10)
    qb_up, qb_down = ranked_lists(players, "QB", 5)
    te_up, te_down = ranked_lists(players, "TE", 5)

    draw_player_panel(draw, (70, 215, 880, 1265), "RUNNING BACKS", rb_up, rb_down)
    draw_player_panel(draw, (920, 215, 1730, 1265), "WIDE RECEIVERS", wr_up, wr_down)
    draw_player_panel(draw, (70, 1300, 880, 1815), "QUARTERBACKS", qb_up, qb_down)
    draw_player_panel(draw, (920, 1300, 1730, 1815), "TIGHT ENDS", te_up, te_down)
    draw_position_impact(draw, players, (70, 1850, 1730, 2300))

    footer = (
        "Method: calculate (0.5 × projected rushing/receiving first downs) ÷ original projected points, "
        "then sort strictly by that percentage within each position. Bottom means lowest percentage lift, not fewer points.\n"
        "Sources: Smack Talkers rankings 8/21/26 · SFB first-down model 6/26/26. Passing first downs excluded."
    )
    draw.text((70, 2323), footer, fill=MUTED, font=F_SMALL, spacing=6)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
