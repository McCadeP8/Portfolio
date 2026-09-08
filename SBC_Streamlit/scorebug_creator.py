"""Interactive SBCFBL fantasy basketball scorebug creator.

Run with:
    streamlit run scorebug_creator.py

The renderer is intentionally independent from Streamlit so it can later be fed
by live matchup data, a webhook, or a batch export job.
"""

from __future__ import annotations

import hashlib
import math
import re
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Literal, Mapping

import imageio_ffmpeg
import requests
import streamlit as st
from matplotlib import font_manager
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont

from data import team_info


CATEGORY_ORDER = (
    "MP",
    "TS%",
    "2P%",
    "3P%",
    "FT%",
    "PTS",
    "OREB",
    "DREB",
    "AST",
    "STL",
    "BLK",
    "TOV",
    "+/-",
)

# SBCFBL's category voting weights. Ties split the available points.
CATEGORY_WEIGHTS = {
    "MP": 11,
    "TS%": 41,
    "2P%": 31,
    "3P%": 31,
    "FT%": 21,
    "PTS": 61,
    "OREB": 31,
    "DREB": 31,
    "AST": 41,
    "STL": 31,
    "BLK": 31,
    "TOV": 21,
    "+/-": 31,
}

CATEGORY_PILL_LABELS = {
    "MP": "MIN",
    "TS%": "TS%",
    "2P%": "2P%",
    "3P%": "3P%",
    "FT%": "FT%",
    "PTS": "PTS",
    "OREB": "OR",
    "DREB": "DR",
    "AST": "AST",
    "STL": "STL",
    "BLK": "BLK",
    "TOV": "TOV",
    "+/-": "+/-",
}

DEFAULT_CATEGORY_WINNERS: dict[str, Winner] = dict(
    zip(
        CATEGORY_ORDER,
        ("B", "A", "B", "A", "B", "TIE", "B", "B", "A", "A", "A", "A", "B"),
    )
)

LOGO_CACHE_DIR = Path(__file__).resolve().parent / "assets" / "scorebug_logos"
ANIMATION_HOLD_BEFORE = 0.65
ANIMATION_TRANSITION = 1.50
ANIMATION_HOLD_AFTER = 1.05
SBC_BLUE = "#09438E"
SBC_GREEN = "#009C3D"

Winner = Literal["A", "B", "TIE"]


@dataclass(frozen=True)
class TeamDisplay:
    city: str
    nickname: str
    color: str
    secondary_color: str
    text_color: str
    logo: str
    record: str = "0-0"
    rank: int | None = None

    @property
    def short_name(self) -> str:
        return self.nickname or self.city


@dataclass(frozen=True)
class ScorebugData:
    team_a: TeamDisplay
    team_b: TeamDisplay
    categories: Mapping[str, Winner]
    score_a: float
    score_b: float
    matchup_progress: int = 50
    label: str = "SBCFBL MATCHUP"
    status: str = "FINAL"


def team_display(team: str, record: str, rank: int | None) -> TeamDisplay:
    info = team_info.get(team, {})
    return TeamDisplay(
        city=team,
        nickname=str(info.get("nickname", team)),
        color=str(info.get("bg", "#334155")),
        secondary_color=str(info.get("bg2", "#64748b")),
        text_color=str(info.get("text", "white")),
        logo=str(info.get("logo", "")),
        record=record.strip() or "—",
        rank=rank,
    )


def calculate_score(categories: Mapping[str, Winner]) -> tuple[float, float]:
    """Calculate weighted SBCFBL scores from the 13 category winners."""
    score_a = 0.0
    score_b = 0.0
    for category in CATEGORY_ORDER:
        points = CATEGORY_WEIGHTS[category]
        winner = categories.get(category, "TIE")
        if winner == "A":
            score_a += points
        elif winner == "B":
            score_b += points
        else:
            score_a += points / 2
            score_b += points / 2
    return score_a, score_b


@lru_cache(maxsize=32)
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    props = font_manager.FontProperties(
        family="DejaVu Sans",
        weight="bold" if bold else "normal",
    )
    return ImageFont.truetype(font_manager.findfont(props), size=size)


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    start_size: int,
    minimum_size: int,
) -> ImageFont.FreeTypeFont:
    for size in range(start_size, minimum_size - 1, -1):
        candidate = _font(size, True)
        box = draw.textbbox((0, 0), text, font=candidate)
        if box[2] - box[0] <= max_width:
            return candidate
    return _font(minimum_size, True)


def _rgb(color: str, fallback: str = "#334155") -> tuple[int, int, int]:
    try:
        return ImageColor.getrgb(color)
    except (TypeError, ValueError):
        return ImageColor.getrgb(fallback)


def _contrast(color: str) -> str:
    red, green, blue = _rgb(color)
    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
    return "#101828" if luminance > 0.62 else "#ffffff"


def _mix(color_a: str, color_b: str, amount: float) -> tuple[int, int, int]:
    first = _rgb(color_a)
    second = _rgb(color_b)
    amount = max(0.0, min(1.0, amount))
    return tuple(round(a + (b - a) * amount) for a, b in zip(first, second))


def _gradient_panel(
    image: Image.Image,
    box: tuple[int, int, int, int],
    start: tuple[int, int, int],
    end: tuple[int, int, int],
) -> None:
    """Paint a crisp horizontal RGBA gradient into a rectangular panel."""
    left, top, right, bottom = box
    panel_width = max(1, right - left)
    panel_height = max(1, bottom - top)
    gradient = Image.new("RGBA", (panel_width, panel_height))
    pixels = gradient.load()
    for x in range(panel_width):
        blend = x / max(1, panel_width - 1)
        color = tuple(round(a + (b - a) * blend) for a, b in zip(start, end))
        for y in range(panel_height):
            pixels[x, y] = (*color, 255)
    image.alpha_composite(gradient, (left, top))


@lru_cache(maxsize=64)
def _load_logo(source: str, max_size: int) -> Image.Image | None:
    if not source:
        return None
    try:
        if source.startswith(("https://", "http://")):
            cache_name = hashlib.sha256(source.encode("utf-8")).hexdigest()[:20] + ".img"
            cache_path = LOGO_CACHE_DIR / cache_name
            if cache_path.exists():
                content = cache_path.read_bytes()
            else:
                response = requests.get(
                    source,
                    timeout=8,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; SBCFBL-scorebug/1.0)"},
                )
                response.raise_for_status()
                content = response.content
                LOGO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(content)
        else:
            content = Path(source).read_bytes()
        logo = Image.open(BytesIO(content)).convert("RGBA")
        logo.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return logo
    except (OSError, ValueError, requests.RequestException):
        return None


def _draw_logo(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    team: TeamDisplay,
    center: tuple[int, int],
    size: int = 82,
) -> None:
    logo = _load_logo(team.logo, size)
    if logo is not None:
        canvas.alpha_composite(
            logo,
            (center[0] - logo.width // 2, center[1] - logo.height // 2),
        )
        return

    radius = size // 2
    draw.ellipse(
        (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
        fill=_rgb(team.secondary_color),
        outline="#ffffff",
        width=3,
    )
    initials = "".join(word[0] for word in team.short_name.split()[:2]).upper()
    draw.text(center, initials or team.city[:2].upper(), font=_font(24, True), fill=_contrast(team.secondary_color), anchor="mm")


def _score_text(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def _standing_text(team: TeamDisplay) -> str:
    if team.rank is None:
        return team.record
    suffix = "th" if 10 <= team.rank % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(team.rank % 10, "th")
    return f"{team.rank}{suffix}  •  {team.record}"


def _paint_category_pill(
    image: Image.Image,
    box: tuple[int, int, int, int],
    category: str,
    winner: Winner,
    team_a_color: str,
    team_b_color: str,
) -> None:
    draw = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    radius = max(5, (y2 - y1) // 2)
    if winner == "A":
        draw.rounded_rectangle(box, radius=radius, fill=_rgb(team_a_color), outline=(255, 255, 255, 125), width=1)
        text_color = _contrast(team_a_color)
    elif winner == "B":
        draw.rounded_rectangle(box, radius=radius, fill=_rgb(team_b_color), outline=(255, 255, 255, 125), width=1)
        text_color = _contrast(team_b_color)
    else:
        draw.rounded_rectangle(box, radius=radius, fill="#334155", outline=(255, 255, 255, 125), width=1)
        midpoint = (x1 + x2) // 2
        inset = max(1, min(2, (y2 - y1) // 5))
        draw.rounded_rectangle((x1 + inset, y1 + inset, midpoint, y2 - inset), radius=radius - inset, fill=_rgb(team_a_color))
        draw.rounded_rectangle((midpoint, y1 + inset, x2 - inset, y2 - inset), radius=radius - inset, fill=_rgb(team_b_color))
        text_color = "#ffffff"
    draw.text(
        ((x1 + x2) // 2, (y1 + y2) // 2),
        CATEGORY_PILL_LABELS[category],
        font=_font(9, True),
        fill=text_color,
        anchor="mm",
        stroke_width=1 if winner == "TIE" else 0,
        stroke_fill="#0f172a",
    )


def _paint_gold_pill(image: Image.Image, box: tuple[int, int, int, int], category: str) -> None:
    draw = ImageDraw.Draw(image)
    radius = max(5, (box[3] - box[1]) // 2)
    draw.rounded_rectangle(box, radius=radius, fill="#fbbf24", outline="#fff7cc", width=2)
    draw.text(
        ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2),
        CATEGORY_PILL_LABELS[category],
        font=_font(9, True),
        fill="#1f2937",
        anchor="mm",
    )


def _smoothstep(start: float, end: float, value: float) -> float:
    if end <= start:
        return float(value >= end)
    amount = max(0.0, min(1.0, (value - start) / (end - start)))
    return amount * amount * (3 - 2 * amount)


def _alpha_text(
    image: Image.Image,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    color: str,
    alpha: int,
    *,
    anchor: str = "mm",
    stroke_width: int = 0,
    stroke_fill: str = "#0f172a",
) -> None:
    if alpha <= 0:
        return
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    layer_draw.text(
        position,
        text,
        font=font,
        fill=(*_rgb(color), min(255, alpha)),
        anchor=anchor,
        stroke_width=stroke_width,
        stroke_fill=(*_rgb(stroke_fill), min(255, alpha)),
    )
    image.alpha_composite(layer)


def render_scorebug(
    data: ScorebugData,
    scale: int = 2,
    *,
    animation_changes: Mapping[str, tuple[Winner, Winner]] | None = None,
    animation_scores: tuple[tuple[float, float], tuple[float, float]] | None = None,
    animation_progress: float = 1.0,
) -> Image.Image:
    """Render a transparent, tightly cropped scorebug PNG."""
    width, height = 940, 172
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((18, 15, width - 18, 145), radius=22, fill=(0, 0, 0, 185))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    image.alpha_composite(shadow)
    draw = ImageDraw.Draw(image)

    left, right = 18, width - 18
    top, team_bottom = 9, 125
    center_left, center_right = 382, 558

    # A compact three-part broadcast bar: team, matchup clock, team.
    draw.rounded_rectangle((left, top, right, team_bottom), radius=19, fill="#0f172a")
    _gradient_panel(
        image,
        (left, top, center_left, team_bottom),
        _mix(data.team_a.color, "#020617", 0.34),
        _mix(data.team_a.color, data.team_a.secondary_color, 0.20),
    )
    _gradient_panel(
        image,
        (center_right, top, right, team_bottom),
        _mix(data.team_b.color, data.team_b.secondary_color, 0.20),
        _mix(data.team_b.color, "#020617", 0.34),
    )
    draw.polygon(((center_left - 21, top), (center_left + 8, top), (center_left - 16, team_bottom), (center_left - 45, team_bottom)), fill=_rgb(data.team_a.secondary_color))
    draw.polygon(((center_right - 8, top), (center_right + 21, top), (center_right + 45, team_bottom), (center_right + 16, team_bottom)), fill=_rgb(data.team_b.secondary_color))
    _gradient_panel(
        image,
        (center_left, top, center_right, team_bottom),
        _mix(SBC_BLUE, "#020617", 0.46),
        _mix(SBC_BLUE, SBC_GREEN, 0.22),
    )
    draw = ImageDraw.Draw(image)
    draw.rectangle((center_left, top, center_right, top + 4), fill=SBC_GREEN)
    draw.line((center_left, top + 1, center_left, team_bottom - 1), fill=SBC_GREEN, width=2)
    draw.line((center_right, top + 1, center_right, team_bottom - 1), fill=SBC_BLUE, width=2)

    _draw_logo(image, draw, data.team_a, (66, 67), 76)
    _draw_logo(image, draw, data.team_b, (width - 66, 67), 76)

    name_a = data.team_a.short_name.upper()
    name_b = data.team_b.short_name.upper()
    font_a = _fit_font(draw, name_a, 160, 25, 15)
    font_b = _fit_font(draw, name_b, 160, 25, 15)
    text_a = _contrast(data.team_a.color)
    text_b = _contrast(data.team_b.color)
    draw.text((110, 53), name_a, font=font_a, fill=text_a, anchor="lm")
    draw.text((110, 85), _standing_text(data.team_a), font=_font(14, True), fill=text_a, anchor="lm")
    draw.text((width - 110, 53), name_b, font=font_b, fill=text_b, anchor="rm")
    draw.text((width - 110, 85), _standing_text(data.team_b), font=_font(14, True), fill=text_b, anchor="rm")

    # Large scores stay inside their team panels, like a conventional TV scorebug.
    score_a_box = (276, 27, 366, 106)
    score_b_box = (width - 366, 27, width - 276, 106)
    draw.rounded_rectangle(score_a_box, radius=13, fill=_mix(data.team_a.color, "#020617", 0.53), outline=(255, 255, 255, 75), width=1)
    draw.rounded_rectangle(score_b_box, radius=13, fill=_mix(data.team_b.color, "#020617", 0.53), outline=(255, 255, 255, 75), width=1)
    if animation_scores:
        before_scores, after_scores = animation_scores
        score_progress = max(0.0, min(1.0, animation_progress))
        old_phase = _smoothstep(0.12, 0.50, score_progress)
        new_phase = _smoothstep(0.46, 0.84, score_progress)
        delta_in = _smoothstep(0.17, 0.34, score_progress)
        delta_out = 1 - _smoothstep(0.82, 0.98, score_progress)
        for x_position, old_value, new_value in (
            (321, before_scores[0], after_scores[0]),
            (width - 321, before_scores[1], after_scores[1]),
        ):
            old_text = _score_text(old_value)
            new_text = _score_text(new_value)
            old_font = _fit_font(draw, old_text, 78, 43, 25)
            new_font = _fit_font(draw, new_text, 78, 43, 25)
            _alpha_text(image, (x_position, round(62 - 20 * old_phase)), old_text, old_font, "#ffffff", round(255 * (1 - old_phase)))
            _alpha_text(image, (x_position, round(80 - 18 * new_phase)), new_text, new_font, "#ffffff", round(255 * new_phase))
            delta = new_value - old_value
            if abs(delta) > 0.001:
                delta_text = f"{'+' if delta > 0 else '−'}{_score_text(abs(delta))}"
                delta_color = "#4ade80" if delta > 0 else "#fb7185"
                delta_font = _fit_font(draw, delta_text, 76, 20, 13)
                _alpha_text(
                    image,
                    (x_position, 96),
                    delta_text,
                    delta_font,
                    delta_color,
                    round(255 * delta_in * delta_out),
                    stroke_width=1,
                )
    else:
        score_a_text = _score_text(data.score_a)
        score_b_text = _score_text(data.score_b)
        score_a_font = _fit_font(draw, score_a_text, 78, 43, 25)
        score_b_font = _fit_font(draw, score_b_text, 78, 43, 25)
        draw.text((321, 66), score_a_text, font=score_a_font, fill="#ffffff", anchor="mm")
        draw.text((width - 321, 66), score_b_text, font=score_b_font, fill="#ffffff", anchor="mm")

    # The center behaves like a fantasy-game clock: black loading over white.
    progress = max(0, min(100, int(data.matchup_progress)))
    draw.text((width // 2, 31), "MATCHUP PROGRESS", font=_font(10, True), fill="#ffffff", anchor="mm")
    track = (407, 48, 533, 76)
    draw.rounded_rectangle(track, radius=14, fill="#ffffff", outline=SBC_GREEN, width=2)
    fill_width = round((track[2] - track[0]) * progress / 100)
    if fill_width:
        fill_right = max(track[0] + 14, min(track[2], track[0] + fill_width))
        fill_mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(fill_mask).rounded_rectangle(track, radius=14, fill=255)
        black_fill = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ImageDraw.Draw(black_fill).rectangle((track[0], track[1], fill_right, track[3]), fill="#050505")
        image.alpha_composite(Image.composite(black_fill, Image.new("RGBA", image.size), fill_mask))
        draw = ImageDraw.Draw(image)
    percentage_color = "#ffffff" if progress >= 50 else "#050505"
    draw.text((width // 2, 62), f"{progress}%", font=_font(14, True), fill=percentage_color, anchor="mm")
    progress_status = "MATCHUP COMPLETE" if progress >= 100 else "IN PROGRESS"
    draw.rounded_rectangle((413, 85, 527, 111), radius=13, fill=SBC_GREEN)
    draw.text((width // 2, 98), progress_status, font=_font(10, True), fill="#ffffff", anchor="mm")

    # Thirteen compact capsules encode category ownership without adding clutter.
    pill_top, pill_bottom = 137, 157
    gap = 7
    usable_width = 650
    pill_width = (usable_width - gap * (len(CATEGORY_ORDER) - 1)) / len(CATEGORY_ORDER)
    x = (width - usable_width) / 2
    for category in CATEGORY_ORDER:
        winner = data.categories.get(category, "TIE")
        x1, x2 = int(x), int(x + pill_width)
        change = (animation_changes or {}).get(category)
        if change:
            animation_from, animation_to = change
            progress = max(0.0, min(1.0, animation_progress))
            pulse = math.sin(math.pi * min(1.0, progress / 0.88))
            animated_box = (
                round(x1 - 4 * pulse),
                round(pill_top - 7 * pulse),
                round(x2 + 4 * pulse),
                round(pill_bottom + 7 * pulse),
            )
            glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
            ImageDraw.Draw(glow).rounded_rectangle(animated_box, radius=14, fill=(251, 191, 36, round(220 * pulse)))
            image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(9)))
            source_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
            gold_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
            target_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
            _paint_category_pill(source_layer, animated_box, category, animation_from, data.team_a.color, data.team_b.color)
            _paint_gold_pill(gold_layer, animated_box, category)
            _paint_category_pill(target_layer, animated_box, category, animation_to, data.team_a.color, data.team_b.color)
            if progress < 0.34:
                animated_pill = Image.blend(source_layer, gold_layer, _smoothstep(0.0, 0.34, progress))
            elif progress < 0.62:
                animated_pill = gold_layer
            else:
                animated_pill = Image.blend(gold_layer, target_layer, _smoothstep(0.62, 1.0, progress))
            image.alpha_composite(animated_pill)
        else:
            _paint_category_pill(image, (x1, pill_top, x2, pill_bottom), category, winner, data.team_a.color, data.team_b.color)
        x += pill_width + gap

    if scale != 1:
        image = image.resize((width * scale, height * scale), Image.Resampling.LANCZOS)
    return image


def image_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _gif_frame(image: Image.Image) -> Image.Image:
    """Convert RGBA to a GIF palette while reserving one transparent color."""
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    transparent = alpha.point(lambda value: 255 if value < 24 else 0)
    frame = rgba.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
    frame.paste(255, mask=transparent)
    frame.info["transparency"] = 255
    return frame


def _render_transition_frames(
    before: ScorebugData,
    changes: Mapping[str, Winner],
    *,
    fps: int = 20,
) -> list[Image.Image]:
    """Render RGBA frames for one or more category and score changes."""
    if not changes:
        raise ValueError("Select at least one category to animate.")
    transitions: dict[str, tuple[Winner, Winner]] = {}
    for category, target in changes.items():
        if category not in CATEGORY_ORDER:
            raise ValueError(f"Unknown category: {category}")
        source = before.categories.get(category, "TIE")
        if source == target:
            raise ValueError(f"{category} must change to a different result.")
        transitions[category] = (source, target)

    after_categories = dict(before.categories)
    after_categories.update(changes)
    after_score_a, after_score_b = calculate_score(after_categories)
    hold_before = round(fps * ANIMATION_HOLD_BEFORE)
    transition_frames = round(fps * ANIMATION_TRANSITION)
    hold_after = round(fps * ANIMATION_HOLD_AFTER)
    frames: list[Image.Image] = []

    for index in range(hold_before + transition_frames + hold_after):
        if index < hold_before:
            progress = 0.0
        elif index >= hold_before + transition_frames:
            progress = 1.0
        else:
            raw = (index - hold_before) / max(1, transition_frames - 1)
            progress = raw * raw * (3 - 2 * raw)
        frame_data = ScorebugData(
            team_a=before.team_a,
            team_b=before.team_b,
            categories=before.categories if progress < 1 else after_categories,
            score_a=before.score_a if progress < 1 else after_score_a,
            score_b=before.score_b if progress < 1 else after_score_b,
            matchup_progress=before.matchup_progress,
            label=before.label,
            status=before.status,
        )
        frame = render_scorebug(
            frame_data,
            scale=2,
            animation_changes=transitions,
            animation_scores=((before.score_a, before.score_b), (after_score_a, after_score_b)),
            animation_progress=progress,
        )
        frames.append(frame)

    return frames


def render_transition_gif(
    before: ScorebugData,
    changes: Mapping[str, Winner],
    *,
    fps: int = 20,
) -> bytes:
    """Animate one or more category changes as a downloadable GIF."""
    frames = [_gif_frame(frame) for frame in _render_transition_frames(before, changes, fps=fps)]

    output = BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / fps),
        loop=0,
        disposal=2,
        transparency=255,
        optimize=False,
    )
    return output.getvalue()


def _changed_scorebug(before: ScorebugData, changes: Mapping[str, Winner]) -> ScorebugData:
    categories = dict(before.categories)
    categories.update(changes)
    score_a, score_b = calculate_score(categories)
    return ScorebugData(
        team_a=before.team_a,
        team_b=before.team_b,
        categories=categories,
        score_a=score_a,
        score_b=score_b,
        matchup_progress=before.matchup_progress,
        label=before.label,
        status=before.status,
    )


def _probe_video(path: Path) -> tuple[float, int, int]:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    completed = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    details = completed.stderr
    duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", details)
    video_line = next((line for line in details.splitlines() if "Video:" in line), "")
    size_match = re.search(r"(?<!\d)(\d{2,5})x(\d{2,5})(?!\d)", video_line)
    if not duration_match or not size_match:
        raise ValueError("The uploaded MP4's duration or dimensions could not be read.")
    hours, minutes, seconds = duration_match.groups()
    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return duration, int(size_match.group(1)), int(size_match.group(2))


def render_video_with_scorebug(
    video_bytes: bytes,
    before: ScorebugData,
    changes: Mapping[str, Winner],
    *,
    change_at: float = 0.75,
    overlay_scale: float = 0.52,
) -> bytes:
    """Burn the scorebug into an MP4 and trigger its animation partway through."""
    if not video_bytes:
        raise ValueError("Upload an MP4 before rendering.")
    if not changes:
        raise ValueError("Select at least one category change before rendering.")

    with tempfile.TemporaryDirectory(prefix="sbc_scorebug_") as directory:
        work = Path(directory)
        input_path = work / "input.mp4"
        before_path = work / "before.png"
        transition_pattern = work / "transition_%04d.png"
        after_path = work / "after.png"
        output_path = work / "scorebug_highlight.mp4"
        input_path.write_bytes(video_bytes)

        duration, video_width, video_height = _probe_video(input_path)
        if duration <= 0:
            raise ValueError("The uploaded video has no playable duration.")
        trigger_time = duration * max(0.0, min(1.0, change_at))
        gif_start = max(0.0, trigger_time - ANIMATION_HOLD_BEFORE)
        # Once the animated score settles, switch to the final static overlay.
        # This avoids a transparent tail when the highlight ends mid-animation.
        gif_end = min(duration, gif_start + ANIMATION_HOLD_BEFORE + ANIMATION_TRANSITION)

        before_path.write_bytes(image_bytes(render_scorebug(before)))
        for frame_index, frame in enumerate(_render_transition_frames(before, changes)):
            frame.save(work / f"transition_{frame_index:04d}.png", format="PNG", compress_level=1)
        after_path.write_bytes(image_bytes(render_scorebug(_changed_scorebug(before, changes))))

        overlay_scale = max(0.25, min(0.90, float(overlay_scale)))
        overlay_width = min(1880, max(240, round(video_width * overlay_scale)))
        overlay_height = round(344 * overlay_width / 1880)
        overlay_x = max(0, (video_width - overlay_width) // 2)
        overlay_y = max(0, video_height - overlay_height - max(18, round(video_height * 0.035)))
        filter_graph = (
            f"[1:v]scale={overlay_width}:-1[before];"
            f"[2:v]scale={overlay_width}:-1[transition];"
            f"[3:v]scale={overlay_width}:-1[after];"
            f"[0:v][before]overlay={overlay_x}:{overlay_y}:enable=lt(t\\,{gif_start:.3f}):eof_action=pass[v1];"
            f"[v1][transition]overlay={overlay_x}:{overlay_y}:enable=between(t\\,{gif_start:.3f}\\,{gif_end:.3f}):eof_action=pass[v2];"
            f"[v2][after]overlay={overlay_x}:{overlay_y}:enable=gte(t\\,{gif_end:.3f}):eof_action=pass[vout]"
        )
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        command = [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-loop",
            "1",
            "-i",
            str(before_path),
            "-itsoffset",
            f"{gif_start:.3f}",
            "-framerate",
            "20",
            "-i",
            str(transition_pattern),
            "-loop",
            "1",
            "-i",
            str(after_path),
            "-filter_complex",
            filter_graph,
            "-map",
            "[vout]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-t",
            f"{duration:.3f}",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if completed.returncode != 0 or not output_path.exists():
            final_error = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "Unknown FFmpeg error"
            raise RuntimeError(f"Video rendering failed: {final_error}")
        return output_path.read_bytes()


def render_app() -> None:
    st.set_page_config(page_title="SBCFBL Scorebug Studio", page_icon="🏀", layout="wide")
    st.title("SBCFBL Scorebug Studio")
    st.caption("Build a transparent fantasy scorebug for highlight clips.")

    teams = sorted(team_info)
    default_a = teams.index("Vegas") if "Vegas" in teams else 0
    default_b = teams.index("Boise") if "Boise" in teams else min(1, len(teams) - 1)

    setup, result = st.columns([0.82, 1.18], gap="large")
    with setup:
        st.subheader("Matchup")
        left_col, right_col = st.columns(2)
        with left_col:
            team_a_name = st.selectbox("Team A", teams, index=default_a)
            rank_a = st.number_input("Team A rank", min_value=1, max_value=len(teams), value=5)
            record_a = st.text_input("Team A record", value="36-24")
        with right_col:
            team_b_name = st.selectbox("Team B", teams, index=default_b)
            rank_b = st.number_input("Team B rank", min_value=1, max_value=len(teams), value=2)
            record_b = st.text_input("Team B record", value="46-14")

        matchup_progress = st.slider(
            "Matchup clock",
            min_value=0,
            max_value=100,
            value=65,
            format="%d%% complete",
        )

        st.subheader("13-category result")
        st.caption("The score is calculated from the league's weighted category values.")
        st.caption(f"A = {team_info[team_a_name].get('nickname', team_a_name)}  •  B = {team_info[team_b_name].get('nickname', team_b_name)}")
        categories: dict[str, Winner] = {}
        option_labels = {"A": "A", "Tie": "TIE", "B": "B"}
        default_options = {"A": "A", "TIE": "Tie", "B": "B"}
        for row_start in range(0, len(CATEGORY_ORDER), 2):
            row = st.columns(2)
            for column, category in zip(row, CATEGORY_ORDER[row_start : row_start + 2]):
                with column:
                    selection = st.segmented_control(
                        category,
                        options=list(option_labels),
                        default=default_options[DEFAULT_CATEGORY_WINNERS[category]],
                        key=f"scorebug_{category}",
                    )
                    categories[category] = option_labels.get(selection, "TIE")  # type: ignore[assignment]

        st.subheader("Animate a change")
        animation_categories = st.multiselect(
            "Categories to flip",
            CATEGORY_ORDER,
            default=["PTS"],
            help="Every selected category changes at the same moment.",
        )
        target_names = {
            "A": f"Team A — {team_info[team_a_name].get('nickname', team_a_name)}",
            "B": f"Team B — {team_info[team_b_name].get('nickname', team_b_name)}",
            "TIE": "Tie",
        }
        animation_changes: dict[str, Winner] = {}
        target_columns = st.columns(2)
        for index, animation_category in enumerate(animation_categories):
            current_winner = categories[animation_category]
            allowed_targets: list[Winner] = [winner for winner in ("A", "TIE", "B") if winner != current_winner]  # type: ignore[misc]
            default_target = "TIE" if current_winner != "TIE" else "A"
            with target_columns[index % 2]:
                animation_changes[animation_category] = st.selectbox(
                    f"{animation_category}: {target_names[current_winner]} →",
                    allowed_targets,
                    index=allowed_targets.index(default_target),
                    format_func=lambda winner: target_names[winner],
                    key=f"animation_target_{animation_category}",
                )

    auto_score_a, auto_score_b = calculate_score(categories)
    display = ScorebugData(
        team_a=team_display(team_a_name, record_a, int(rank_a)),
        team_b=team_display(team_b_name, record_b, int(rank_b)),
        categories=categories,
        score_a=auto_score_a,
        score_b=auto_score_b,
        matchup_progress=matchup_progress,
        status="FINAL" if matchup_progress == 100 else "IN PROGRESS",
    )
    rendered = render_scorebug(display)
    png = image_bytes(rendered)

    with result:
        st.subheader("Preview")
        st.image(png, use_container_width=True)
        st.caption(f"Transparent PNG • {rendered.width} × {rendered.height}px • score { _score_text(auto_score_a) }–{ _score_text(auto_score_b) }")
        filename = f"{team_a_name.lower().replace(' ', '-')}-vs-{team_b_name.lower().replace(' ', '-')}-scorebug.png"
        st.download_button(
            "Download transparent PNG",
            data=png,
            file_name=filename,
            mime="image/png",
            type="primary",
            use_container_width=True,
        )
        animation_signature = (
            team_a_name,
            team_b_name,
            record_a,
            record_b,
            rank_a,
            rank_b,
            matchup_progress,
            tuple(categories.items()),
            tuple(animation_changes.items()),
        )
        if st.button("Generate animated GIF", use_container_width=True, disabled=not animation_changes):
            with st.spinner("Animating the category and score change…"):
                st.session_state["scorebug_animation"] = render_transition_gif(
                    display,
                    animation_changes,
                )
                st.session_state["scorebug_animation_signature"] = animation_signature

        animation = st.session_state.get("scorebug_animation")
        if animation and st.session_state.get("scorebug_animation_signature") == animation_signature:
            st.subheader("Animated before and after")
            st.image(animation, use_container_width=True)
            animation_filename = f"{team_a_name.lower().replace(' ', '-')}-vs-{team_b_name.lower().replace(' ', '-')}-changes.gif"
            st.download_button(
                "Download animated GIF",
                data=animation,
                file_name=animation_filename,
                mime="image/gif",
                use_container_width=True,
            )

        st.divider()
        st.subheader("Add to a highlight")
        video_scorebug_size = st.slider(
            "Video scorebug size",
            min_value=35,
            max_value=75,
            value=52,
            format="%d%% of video width",
        )
        uploaded_video = st.file_uploader(
            "Upload MP4",
            type=["mp4"],
            help="The scorebug is centered near the bottom and changes 75% of the way through.",
        )
        if uploaded_video is not None:
            source_video = uploaded_video.getvalue()
            st.video(source_video)
            video_signature = (
                hashlib.sha256(source_video).hexdigest()[:16],
                animation_signature,
                video_scorebug_size,
            )
            if st.button(
                "Create new MP4",
                type="primary",
                use_container_width=True,
                disabled=not animation_changes,
            ):
                try:
                    with st.spinner("Rendering the scorebug into your video…"):
                        st.session_state["scorebug_video"] = render_video_with_scorebug(
                            source_video,
                            display,
                            animation_changes,
                            change_at=0.75,
                            overlay_scale=video_scorebug_size / 100,
                        )
                        st.session_state["scorebug_video_signature"] = video_signature
                except (OSError, RuntimeError, ValueError) as error:
                    st.error(str(error))

            rendered_video = st.session_state.get("scorebug_video")
            if rendered_video and st.session_state.get("scorebug_video_signature") == video_signature:
                st.subheader("Finished highlight")
                st.video(rendered_video)
                video_filename = f"{Path(uploaded_video.name).stem}-with-scorebug.mp4"
                st.download_button(
                    "Download finished MP4",
                    data=rendered_video,
                    file_name=video_filename,
                    mime="video/mp4",
                    use_container_width=True,
                )
        st.info("Drop the PNG or GIF above the highlight track in your editor. Both are tightly cropped with a transparent background, so they can sit at the top or bottom of any 16:9 clip.")


if __name__ == "__main__":
    render_app()
