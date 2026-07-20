"""Reusable vector-style basketball uniform renderer.

The engine has no Streamlit dependency. It can power the standalone creator,
batch exports, roster graphics, or future matchup presentations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping
from urllib.request import Request, urlopen

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Arc, Circle, PathPatch, Polygon, Rectangle
from matplotlib.path import Path as MplPath
import matplotlib.patheffects as path_effects
import numpy as np
from PIL import Image


@dataclass(slots=True)
class JerseyConfig:
    team: str = "SBC"
    edition: str = "Association"
    jersey_color: str = "#FFFFFF"
    shorts_color: str = "#FFFFFF"
    trim_color: str = "#111827"
    accent_color: str = "#2563EB"
    wordmark_color: str = "#111827"
    number_color: str = "#111827"
    number_outline_color: str = "#FFFFFF"
    player_name_color: str = "#111827"
    stripe_style: str = "Side panels"
    shorts_stripe_style: str = "Side panels"
    collar_style: str = "Crew"
    wordmark: str = "SBC"
    wordmark_font: str = "SBC League"
    font_family: str = "Bungee"
    font_path: str = ""
    number: str = "27"
    player_name: str = "PLAYER"
    number_outline_width: float = 4.0
    trim_width: float = 3.4
    logo_team: str = ""
    shorts_logo_scale: float = 0.75
    show_shorts_logo: bool = True
    show_league_mark: bool = True
    front_wordmark_x: float = 0.0
    front_wordmark_y: float = 29.0
    front_wordmark_size: float = 35.0
    front_number_x: float = 0.0
    front_number_y: float = 45.0
    front_number_size: float = 60.0
    back_name_x: float = 0.0
    back_name_y: float = 18.0
    back_name_size: float = 36.0
    back_number_x: float = 0.0
    back_number_y: float = 43.0
    back_number_size: float = 80.0
    jersey_logo_x: float = 12.0
    jersey_logo_y: float = 15.0
    jersey_logo_scale: float = 0.70
    show_jersey_logo: bool = True

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "JerseyConfig":
        valid = {field.name for field in fields(cls)}
        return cls(**{key: value for key, value in values.items() if key in valid})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read_image(image: Any) -> np.ndarray | None:
    if image is None:
        return None
    try:
        if isinstance(image, np.ndarray):
            return image
        if isinstance(image, bytes):
            return np.asarray(Image.open(BytesIO(image)).convert("RGBA"))
        if isinstance(image, (str, Path)):
            if str(image).startswith(("http://", "https://")):
                request = Request(str(image), headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(request, timeout=15) as response:
                    return np.asarray(Image.open(BytesIO(response.read())).convert("RGBA"))
            path = Path(image)
            if path.exists():
                return np.asarray(Image.open(path).convert("RGBA"))
    except Exception:
        return None
    return None


def _jersey_path(cx: float, top: float, scale: float = 1.0) -> MplPath:
    # Manufacturer-style basketball jersey flat based on a long, straight game
    # cut: narrow neck straps, deep armholes, straight side seams, curved hem.
    vertices = [
        (-6.5, 0), (-12, -1), (-24, 4),
        (-22, 11), (-20.5, 19), (-23, 27),
        (-24, 31), (-24, 38), (-24, 43),
        (-24, 69),
        (-15, 76), (15, 76), (24, 69),
        (24, 43),
        (24, 38), (24, 31), (23, 27),
        (20.5, 19), (22, 11), (24, 4),
        (12, -1), (6.5, 0),
        (5.5, 5), (3, 10), (0, 11),
        (-3, 10), (-5.5, 5), (-6.5, 0),
        (-6.5, 0),
    ]
    codes = [
        MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.LINETO,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.LINETO,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.LINETO, MplPath.LINETO,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    scaled = [(cx + x * scale, top + y * scale) for x, y in vertices]
    return MplPath(scaled, codes)


def _shorts_shapes(cx: float, top: float, scale: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    # Loose, knee-length basketball shorts with a dropped crotch and side vent.
    left = np.array([[-21, 0], [0, 0], [-2, 29], [-7, 38], [-25, 35], [-26, 8]], dtype=float)
    right = np.array([[0, 0], [21, 0], [26, 8], [25, 35], [7, 38], [2, 29]], dtype=float)
    for shape in (left, right):
        shape[:, 0] = cx + shape[:, 0] * scale
        shape[:, 1] = top + shape[:, 1] * scale
    return left, right


def _font(config: JerseyConfig):
    from matplotlib.font_manager import FontProperties

    if config.font_path and Path(config.font_path).exists():
        return FontProperties(fname=config.font_path)
    return FontProperties(family=config.font_family)


def _outlined_text(ax: Axes, x: float, y: float, text: str, color: str, outline: str, width: float, **kwargs):
    artist = ax.text(x, y, text, color=color, **kwargs)
    if width > 0:
        artist.set_path_effects([path_effects.withStroke(linewidth=width, foreground=outline), path_effects.Normal()])
    return artist


def _jersey_stripes(ax: Axes, config: JerseyConfig, cx: float, top: float, jersey_clip: PathPatch, scale: float):
    style = config.stripe_style
    z = 3
    if style == "None":
        return
    if style == "Side panels":
        for sign in (-1, 1):
            panel = Polygon([
                (cx + sign * 20 * scale, top + 22 * scale),
                (cx + sign * 24 * scale, top + 27 * scale),
                (cx + sign * 24 * scale, top + 70 * scale),
                (cx + sign * 18 * scale, top + 73 * scale),
            ], facecolor=config.accent_color, edgecolor="none", zorder=z)
            panel.set_clip_path(jersey_clip)
            ax.add_patch(panel)
    elif style == "Double side":
        for sign in (-1, 1):
            for offset, color in ((15, config.accent_color), (11.5, config.trim_color)):
                ax.plot([cx + sign * offset * scale] * 2, [top + 25 * scale, top + 72 * scale], color=color, linewidth=4.2 * scale, zorder=z, clip_path=jersey_clip)
    elif style == "Chest band":
        ax.add_patch(Rectangle((cx - 24 * scale, top + 27 * scale), 48 * scale, 8 * scale, facecolor=config.accent_color, edgecolor="none", zorder=z, clip_path=jersey_clip))
        ax.plot([cx - 24 * scale, cx + 24 * scale], [top + 35 * scale] * 2, color=config.trim_color, linewidth=2.3 * scale, zorder=z + .1, clip_path=jersey_clip)
    elif style == "Sash":
        sash = Polygon([(cx - 23 * scale, top + 12 * scale), (cx - 17 * scale, top + 8 * scale), (cx + 22 * scale, top + 69 * scale), (cx + 15 * scale, top + 74 * scale)], facecolor=config.accent_color, edgecolor="none", zorder=z)
        sash.set_clip_path(jersey_clip)
        ax.add_patch(sash)
    elif style == "Pinstripes":
        for x in np.arange(cx - 20 * scale, cx + 21 * scale, 5 * scale):
            ax.plot([x, x], [top + 4 * scale, top + 75 * scale], color=config.accent_color, linewidth=.8, alpha=.8, zorder=z, clip_path=jersey_clip)
    elif style == "Waist fade":
        for index in range(7):
            alpha = .12 + index * .09
            ax.add_patch(Rectangle((cx - 20 * scale, top + (44 + index * 3) * scale), 40 * scale, 3.1 * scale, facecolor=config.accent_color, edgecolor="none", alpha=alpha, zorder=z, clip_path=jersey_clip))


def _draw_jersey(ax: Axes, config: JerseyConfig, cx: float, top: float, back: bool, logo: Any = None, scale: float = 1.0):
    font = _font(config)
    path = _jersey_path(cx, top, scale)
    jersey = PathPatch(path, facecolor=config.jersey_color, edgecolor=config.trim_color, linewidth=config.trim_width, joinstyle="round", zorder=2)
    ax.add_patch(jersey)
    _jersey_stripes(ax, config, cx, top, jersey, scale)

    # The silhouette already contains the cutaway armholes. Collar treatments
    # reinforce the neckline without adding sleeve-like arcs.
    canvas = ax.get_facecolor()
    if config.collar_style == "V-neck":
        ax.plot([cx - 6.5 * scale, cx, cx + 6.5 * scale], [top + .5 * scale, top + 9 * scale, top + .5 * scale], color=config.trim_color, linewidth=config.trim_width * 1.35, zorder=6)
    elif config.collar_style == "Crew":
        ax.add_patch(Arc((cx, top + 1 * scale), 13 * scale, 16 * scale, theta1=0, theta2=180, color=config.trim_color, linewidth=config.trim_width * 1.4, zorder=6))
    else:  # Wishbone
        ax.plot([cx - 6.5 * scale, cx, cx + 6.5 * scale], [top + .5 * scale, top + 7.5 * scale, top + .5 * scale], color=config.accent_color, linewidth=config.trim_width * 2.4, zorder=5.8)
        ax.plot([cx - 6.5 * scale, cx, cx + 6.5 * scale], [top + .5 * scale, top + 7.5 * scale, top + .5 * scale], color=config.trim_color, linewidth=config.trim_width, zorder=6)

    if back:
        _outlined_text(ax, cx + config.back_name_x * scale, top + config.back_name_y * scale, config.player_name.upper(), config.player_name_color, config.number_outline_color, config.number_outline_width, fontsize=config.back_name_size * scale, fontweight="bold", fontproperties=font, ha="center", va="center", zorder=21)
        _outlined_text(ax, cx + config.back_number_x * scale, top + config.back_number_y * scale, config.number, config.number_color, config.number_outline_color, config.number_outline_width, fontsize=config.back_number_size * scale, fontweight="bold", fontproperties=font, ha="center", va="center", zorder=21)
    else:
        _outlined_text(ax, cx + config.front_wordmark_x * scale, top + config.front_wordmark_y * scale, config.wordmark.upper(), config.wordmark_color, config.number_outline_color, config.number_outline_width, fontsize=config.front_wordmark_size * scale, fontweight="bold", fontproperties=font, ha="center", va="center", zorder=21)
        _outlined_text(ax, cx + config.front_number_x * scale, top + config.front_number_y * scale, config.number, config.number_color, config.number_outline_color, config.number_outline_width, fontsize=config.front_number_size * scale, fontweight="bold", fontproperties=font, ha="center", va="center", zorder=21)
        if config.show_league_mark:
            ax.text(cx, top + 13 * scale, "SBC", color=config.accent_color, fontsize=4.8 * scale, fontweight="bold", ha="center", va="center", zorder=21)
        logo_data = _read_image(logo)
        if config.show_jersey_logo and logo_data is not None:
            # The canvas has an inverted y-axis; compensate so logos stay upright.
            logo_data = np.flipud(logo_data)
            height = 12 * scale * config.jersey_logo_scale
            width = height * logo_data.shape[1] / max(logo_data.shape[0], 1)
            logo_x = cx + config.jersey_logo_x * scale
            logo_y = top + config.jersey_logo_y * scale
            ax.imshow(logo_data, extent=(logo_x - width / 2, logo_x + width / 2, logo_y - height / 2, logo_y + height / 2), interpolation="lanczos", zorder=22)


def _draw_shorts(ax: Axes, config: JerseyConfig, cx: float, top: float, logo: Any, scale: float = 1.0):
    left, right = _shorts_shapes(cx, top, scale)
    for shape in (left, right):
        ax.add_patch(Polygon(shape, facecolor=config.shorts_color, edgecolor=config.trim_color, linewidth=config.trim_width, joinstyle="round", zorder=2))
    ax.add_patch(Rectangle((cx - 20 * scale, top), 40 * scale, 5 * scale, facecolor=config.trim_color, edgecolor="none", zorder=4))

    style = config.shorts_stripe_style
    if style == "Side panels":
        ax.add_patch(Polygon([(cx - 25 * scale, top + 7 * scale), (cx - 20 * scale, top + 5 * scale), (cx - 18 * scale, top + 33 * scale), (cx - 24 * scale, top + 34 * scale)], facecolor=config.accent_color, edgecolor="none", zorder=4))
        ax.add_patch(Polygon([(cx + 25 * scale, top + 7 * scale), (cx + 20 * scale, top + 5 * scale), (cx + 18 * scale, top + 33 * scale), (cx + 24 * scale, top + 34 * scale)], facecolor=config.accent_color, edgecolor="none", zorder=4))
    elif style == "Double side":
        for sign in (-1, 1):
            ax.plot([cx + sign * 21 * scale, cx + sign * 21 * scale], [top + 6 * scale, top + 33 * scale], color=config.accent_color, linewidth=4 * scale, zorder=4)
            ax.plot([cx + sign * 18 * scale, cx + sign * 18 * scale], [top + 6 * scale, top + 32 * scale], color=config.trim_color, linewidth=1.8 * scale, zorder=4)
    elif style == "Hem band":
        for shape in (left, right):
            y = top + 31 * scale
            ax.plot([shape[:, 0].min() + 2 * scale, shape[:, 0].max() - 2 * scale], [y, y], color=config.accent_color, linewidth=4 * scale, zorder=4)
    elif style == "Chevron":
        ax.plot([cx - 23 * scale, cx, cx + 23 * scale], [top + 25 * scale, top + 34 * scale, top + 25 * scale], color=config.accent_color, linewidth=4 * scale, zorder=4)
    elif style == "Pinstripes":
        for x in np.arange(cx - 20 * scale, cx + 21 * scale, 5 * scale):
            ax.plot([x, x], [top + 5 * scale, top + 32 * scale], color=config.accent_color, linewidth=.8, alpha=.8, zorder=4)

    logo_data = _read_image(logo)
    if config.show_shorts_logo and logo_data is not None:
        h = 9 * scale * config.shorts_logo_scale
        w = h * logo_data.shape[1] / max(logo_data.shape[0], 1)
        center_x, center_y = cx - 13 * scale, top + 13 * scale
        ax.imshow(logo_data, extent=(center_x - w / 2, center_x + w / 2, center_y - h / 2, center_y + h / 2), interpolation="lanczos", zorder=10)


def draw_uniform(
    config: JerseyConfig | Mapping[str, Any] | None = None,
    *,
    logo: Any = None,
    view: str = "front_and_back",
    dpi: int = 150,
    background: str = "#EEF2F7",
    show_view_label: bool = True,
) -> tuple[Figure, Axes]:
    """Draw front/back jerseys with shorts and return ``(figure, axes)``."""
    if config is None:
        config = JerseyConfig()
    elif not isinstance(config, JerseyConfig):
        config = JerseyConfig.from_mapping(config)
    if view not in {"front", "back", "front_and_back"}:
        raise ValueError("view must be front, back, or front_and_back")

    figsize = (12, 8) if view == "front_and_back" else (7, 8)
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_facecolor(background)
    fig.patch.set_facecolor(background)
    centers = [50] if view != "front_and_back" else [31, 89]
    backs = [view == "back"] if view != "front_and_back" else [False, True]
    for center, back in zip(centers, backs):
        _draw_jersey(ax, config, center, 5, back=back, logo=logo, scale=.92)
        if show_view_label:
            ax.text(center, 83, "BACK" if back else "FRONT", color="#64748B", fontsize=8, fontweight="bold", ha="center")
    ax.set_xlim(0, 120 if view == "front_and_back" else 100)
    ax.set_ylim(88, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout(pad=.5)
    return fig, ax


def figure_bytes(fig: Figure, file_format: str = "png", dpi: int = 220, transparent: bool = False) -> bytes:
    output = BytesIO()
    fig.savefig(output, format=file_format, dpi=dpi, bbox_inches="tight", pad_inches=.05, transparent=transparent)
    output.seek(0)
    return output.getvalue()
