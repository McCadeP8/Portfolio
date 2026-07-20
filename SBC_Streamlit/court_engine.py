"""Reusable NBA court drawing and branding utilities.

The drawing functions deliberately have no Streamlit dependency.  They can be
used by the court creator, the main app, batch export scripts, or shot charts.
Coordinates are measured in feet on a 50 x 94 NBA court, with (0, 0) at the
lower-left corner.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Mapping
from urllib.request import Request, urlopen

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Arc, Circle, PathPatch, Rectangle, Wedge
from matplotlib.path import Path as MplPath
import numpy as np
from PIL import Image


COURT_WIDTH = 50.0
COURT_LENGTH = 94.0
HOOP_DISTANCE = 5.25
THREE_POINT_RADIUS = 23.75
CORNER_THREE_X = 3.0
CORNER_THREE_END = 14.0
LANE_WIDTH = 16.0
FREE_THROW_DISTANCE = 19.0
FREE_THROW_RADIUS = 6.0
RESTRICTED_RADIUS = 4.0


@dataclass(slots=True)
class CourtConfig:
    """Serializable visual settings for one branded court."""

    team: str = "SBC"
    court_color: str = "#D9B77E"
    out_of_bounds_color: str = "#14213D"
    line_color: str = "#FFFFFF"
    inner_center_circle_color: str = "#D9B77E"
    outer_center_circle_color: str = "#D9B77E"
    outside_three_color: str = "#D9B77E"
    inside_three_color: str = "#D9B77E"
    free_throw_outer_half_color: str = "#D9B77E"
    free_throw_inner_half_color: str = "#1F4E79"
    core_paint_color: str = "#1F4E79"
    paint_stripe_color: str = "#1F4E79"
    line_width: float = 1.2
    boundary_width: float = 1.2
    baseline_text: str = "SBC BASKETBALL"
    baseline_text_bottom: str = ""
    baseline_text_top: str = ""
    sideline_text: str = ""
    text_color: str = "#FFFFFF"
    text_size: float = 18.0
    font_family: str = "DejaVu Sans"
    font_path: str = ""
    logo_scale: float = 0.65
    logo_rotation: float = 0.0
    logo_opacity: float = 1.0
    logo_x: float = 25.0
    logo_y: float = 47.0
    center_logo_team: str = ""
    league_logo_scale: float = 0.45
    league_logo_opacity: float = 1.0
    show_center_circle: bool = True
    show_lane_marks: bool = True
    wood_planks: bool = True
    plank_color: str = "#9B7745"
    plank_opacity: float = 0.14
    floor_pattern: str = "parquet"
    outer_margin: float = 4.0

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "CourtConfig":
        valid = {field.name for field in fields(cls)}
        return cls(**{key: value for key, value in values.items() if key in valid})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read_logo(logo: Any) -> np.ndarray | None:
    if logo is None:
        return None
    if isinstance(logo, np.ndarray):
        return logo
    if isinstance(logo, (str, Path)):
        if str(logo).startswith(("http://", "https://")):
            try:
                request = Request(str(logo), headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(request, timeout=15) as response:
                    return np.asarray(Image.open(BytesIO(response.read())).convert("RGBA"))
            except Exception:
                return None
        path = Path(logo)
        return mpimg.imread(path) if path.exists() else None
    if isinstance(logo, bytes):
        return np.asarray(Image.open(BytesIO(logo)).convert("RGBA"))
    if isinstance(logo, (BytesIO, BinaryIO)) or hasattr(logo, "read"):
        if hasattr(logo, "seek"):
            logo.seek(0)
        return mpimg.imread(logo)
    return None


def _zone_color(value: str, hardwood: str) -> str:
    return value if isinstance(value, str) and value.strip() else hardwood


def _add_floor(ax: Axes, config: CourtConfig) -> None:
    margin = config.outer_margin
    ax.add_patch(
        Rectangle(
            (-margin, -margin),
            COURT_WIDTH + margin * 2,
            COURT_LENGTH + margin * 2,
            facecolor=config.out_of_bounds_color,
            edgecolor="none",
            zorder=0,
        )
    )
    ax.add_patch(
        Rectangle(
            (0, 0), COURT_WIDTH, COURT_LENGTH,
            facecolor=_zone_color(config.outside_three_color, config.court_color),
            edgecolor=config.line_color,
            linewidth=config.boundary_width,
            zorder=1,
        )
    )
    if config.wood_planks:
        if config.floor_pattern == "parquet":
            # Alternating 4 x 4 foot blocks suggest traditional parquet while
            # remaining subtle enough to support shot markers.
            block = 4.0
            rows = int(np.ceil(COURT_LENGTH / block))
            cols = int(np.ceil(COURT_WIDTH / block))
            for row in range(rows):
                for col in range(cols):
                    if (row + col) % 2:
                        ax.add_patch(Rectangle(
                            (col * block, row * block),
                            min(block, COURT_WIDTH - col * block),
                            min(block, COURT_LENGTH - row * block),
                            facecolor=config.plank_color, edgecolor="none",
                            alpha=config.plank_opacity, zorder=1.15,
                        ))
            for y in np.arange(block, COURT_LENGTH, block):
                ax.plot([0, COURT_WIDTH], [y, y], color=config.plank_color, alpha=config.plank_opacity * 0.7, linewidth=0.35, zorder=1.2)
            for x in np.arange(block, COURT_WIDTH, block):
                ax.plot([x, x], [0, COURT_LENGTH], color=config.plank_color, alpha=config.plank_opacity * 0.7, linewidth=0.35, zorder=1.2)
        else:
            for y in np.arange(2.0, COURT_LENGTH, 2.0):
                ax.plot([0, COURT_WIDTH], [y, y], color=config.plank_color, alpha=config.plank_opacity, linewidth=0.45, zorder=1.1)


def _three_point_interior_path(baseline: float, top: bool) -> MplPath:
    """Closed polygon for the area between baseline and the three-point arc."""
    hoop_y = baseline + (-1 if top else 1) * HOOP_DISTANCE
    if top:
        angles = np.linspace(np.deg2rad(202.4), np.deg2rad(337.6), 160)
        start = (CORNER_THREE_X, baseline)
        corner_a = (CORNER_THREE_X, baseline - CORNER_THREE_END)
        corner_b = (COURT_WIDTH - CORNER_THREE_X, baseline - CORNER_THREE_END)
        finish = (COURT_WIDTH - CORNER_THREE_X, baseline)
    else:
        angles = np.linspace(np.deg2rad(157.6), np.deg2rad(22.4), 160)
        start = (CORNER_THREE_X, baseline)
        corner_a = (CORNER_THREE_X, baseline + CORNER_THREE_END)
        corner_b = (COURT_WIDTH - CORNER_THREE_X, baseline + CORNER_THREE_END)
        finish = (COURT_WIDTH - CORNER_THREE_X, baseline)
    arc = [(25 + THREE_POINT_RADIUS * np.cos(a), hoop_y + THREE_POINT_RADIUS * np.sin(a)) for a in angles]
    vertices = [start, corner_a, *arc, corner_b, finish, start]
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(vertices) - 2) + [MplPath.CLOSEPOLY]
    return MplPath(vertices, codes)


def _draw_half(ax: Axes, config: CourtConfig, top: bool = False) -> None:
    direction = -1.0 if top else 1.0
    baseline = COURT_LENGTH if top else 0.0
    hoop_y = baseline + direction * HOOP_DISTANCE
    lane_y = baseline + direction * FREE_THROW_DISTANCE
    line = config.line_color
    lw = config.line_width

    lane_bottom = min(baseline, lane_y)
    inside_three = _zone_color(config.inside_three_color, config.court_color)
    ax.add_patch(PathPatch(_three_point_interior_path(baseline, top), facecolor=inside_three, edgecolor="none", zorder=1.5))

    # Regulation lane is 16 feet wide. The historic 12-foot lane is retained
    # as a separately brandable core with two-foot bands on either side.
    ax.add_patch(Rectangle(((COURT_WIDTH - LANE_WIDTH) / 2, lane_bottom), LANE_WIDTH, FREE_THROW_DISTANCE, facecolor=_zone_color(config.paint_stripe_color, config.court_color), edgecolor=line, linewidth=lw, zorder=2))
    core_width = 12.0
    ax.add_patch(Rectangle(((COURT_WIDTH - core_width) / 2, lane_bottom), core_width, FREE_THROW_DISTANCE, facecolor=_zone_color(config.core_paint_color, config.court_color), edgecolor=line, linewidth=lw, zorder=2.1))

    # Separately colored halves of the free-throw circle.
    if top:
        ax.add_patch(Wedge((25, lane_y), FREE_THROW_RADIUS, 180, 360, facecolor=_zone_color(config.free_throw_outer_half_color, config.court_color), edgecolor="none", zorder=2.2))
        ax.add_patch(Wedge((25, lane_y), FREE_THROW_RADIUS, 0, 180, facecolor=_zone_color(config.free_throw_inner_half_color, config.court_color), edgecolor="none", zorder=2.2))
    else:
        ax.add_patch(Wedge((25, lane_y), FREE_THROW_RADIUS, 0, 180, facecolor=_zone_color(config.free_throw_outer_half_color, config.court_color), edgecolor="none", zorder=2.2))
        ax.add_patch(Wedge((25, lane_y), FREE_THROW_RADIUS, 180, 360, facecolor=_zone_color(config.free_throw_inner_half_color, config.court_color), edgecolor="none", zorder=2.2))
    restricted_theta = (0, 180) if not top else (180, 360)
    ax.add_patch(
        Arc(
            (COURT_WIDTH / 2, hoop_y),
            RESTRICTED_RADIUS * 2,
            RESTRICTED_RADIUS * 2,
            theta1=restricted_theta[0],
            theta2=restricted_theta[1],
            color=line,
            linewidth=lw,
            zorder=4,
        )
    )

    # Backboard and rim.
    board_y = baseline + direction * 4.0
    ax.plot([22, 28], [board_y, board_y], color="#000000", linewidth=lw * 1.5, zorder=5)
    ax.add_patch(Circle((COURT_WIDTH / 2, hoop_y), 0.75, facecolor="#D71920", edgecolor="#D71920", linewidth=lw, zorder=5))
    ax.add_patch(Circle((COURT_WIDTH / 2, hoop_y), 0.54, facecolor="#FFFFFF", edgecolor="none", zorder=5.1))

    # Corner threes and arc. NBA arc meets the corner lines at 14 feet.
    end_y = baseline + direction * CORNER_THREE_END
    ax.plot([CORNER_THREE_X, CORNER_THREE_X], [baseline, end_y], color=line, linewidth=lw, zorder=4)
    ax.plot(
        [COURT_WIDTH - CORNER_THREE_X, COURT_WIDTH - CORNER_THREE_X],
        [baseline, end_y], color=line, linewidth=lw, zorder=4,
    )
    if top:
        theta1, theta2 = 202.4, 337.6
    else:
        theta1, theta2 = 22.4, 157.6
    ax.add_patch(
        Arc(
            (COURT_WIDTH / 2, hoop_y),
            THREE_POINT_RADIUS * 2,
            THREE_POINT_RADIUS * 2,
            theta1=theta1,
            theta2=theta2,
            color=line,
            linewidth=lw,
            zorder=4,
        )
    )

    # Solid half of the free-throw circle faces center court; dashed half faces baseline.
    solid_angles = (0, 180) if not top else (180, 360)
    dashed_angles = (180, 360) if not top else (0, 180)
    ax.add_patch(
        Arc(
            (COURT_WIDTH / 2, lane_y), 12, 12,
            theta1=solid_angles[0], theta2=solid_angles[1],
            color=line, linewidth=lw, zorder=4,
        )
    )
    ax.add_patch(
        Arc(
            (COURT_WIDTH / 2, lane_y), 12, 12,
            theta1=dashed_angles[0], theta2=dashed_angles[1],
            color=line, linewidth=lw, linestyle=(0, (3, 3)), zorder=4,
        )
    )
    # Semicircle fills sit above the lane rectangles, so redraw the regulation
    # 16-foot free-throw line last to keep it continuous and visible.
    ax.plot(
        [(COURT_WIDTH - LANE_WIDTH) / 2, (COURT_WIDTH + LANE_WIDTH) / 2],
        [lane_y, lane_y],
        color=line,
        linewidth=lw,
        zorder=4.5,
    )

    if config.show_lane_marks:
        for offset in (7.0, 8.33, 11.5, 14.67):
            y = baseline + direction * offset
            ax.plot([16.5, 17], [y, y], color=line, linewidth=lw, zorder=4)
            ax.plot([33, 33.5], [y, y], color=line, linewidth=lw, zorder=4)


def _add_branding(ax: Axes, config: CourtConfig, logo: Any = None) -> None:
    from matplotlib.font_manager import FontProperties

    font = FontProperties(fname=config.font_path) if config.font_path and Path(config.font_path).exists() else FontProperties(family=config.font_family)
    logo_data = _read_logo(logo)
    if logo_data is not None:
        aspect = logo_data.shape[1] / max(logo_data.shape[0], 1)
        height = 16.0 * config.logo_scale
        width = height * aspect
        image = ax.imshow(
            logo_data,
            extent=(
                config.logo_x - width / 2,
                config.logo_x + width / 2,
                config.logo_y - height / 2,
                config.logo_y + height / 2,
            ),
            alpha=config.logo_opacity,
            zorder=20,
            interpolation="lanczos",
        )
        if config.logo_rotation:
            from matplotlib.transforms import Affine2D

            transform = Affine2D().rotate_deg_around(
                config.logo_x, config.logo_y, config.logo_rotation
            ) + ax.transData
            image.set_transform(transform)

    bottom_text = (config.baseline_text_bottom or config.baseline_text).strip()
    top_text = (config.baseline_text_top or config.baseline_text).strip()
    for wordmark, y, rotation in ((bottom_text, -1.9, 180), (top_text, 95.9, 0)):
        if not wordmark:
            continue
        ax.text(
                COURT_WIDTH / 2, y, wordmark,
                color=config.text_color,
                fontsize=config.text_size,
                fontweight="bold",
                fontproperties=font,
                ha="center", va="center", rotation=rotation,
                zorder=6,
        )
    if config.sideline_text.strip():
        ax.text(
            -2.0, COURT_LENGTH / 2, config.sideline_text.strip(),
            color=config.text_color,
            fontsize=max(config.text_size * 0.72, 7),
            fontweight="bold",
            fontproperties=font,
            ha="center", va="center", rotation=90, zorder=6,
        )


def draw_branded_court(
    config: CourtConfig | Mapping[str, Any] | None = None,
    *,
    logo: Any = None,
    league_logo: Any = None,
    orientation: str = "vertical",
    view: str = "full",
    figsize: tuple[float, float] | None = None,
    dpi: int = 150,
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Draw a branded regulation court and return ``(figure, axes)``.

    Callers can add shots directly to the returned axes using court coordinates.
    ``orientation='horizontal'`` changes presentation only; data coordinates are
    rotated so callers should use :func:`plot_shots` when orientation may vary.
    """

    if config is None:
        config = CourtConfig()
    elif not isinstance(config, CourtConfig):
        config = CourtConfig.from_mapping(config)

    orientation = orientation.lower()
    view = view.lower()
    if orientation not in {"vertical", "horizontal"}:
        raise ValueError("orientation must be 'vertical' or 'horizontal'")
    if view not in {"full", "half"}:
        raise ValueError("view must be 'full' or 'half'")

    if figsize is None:
        if view == "half":
            figsize = (8.5, 7.2) if orientation == "vertical" else (11.5, 6.2)
        else:
            figsize = (7.2, 12.4) if orientation == "vertical" else (13.5, 7.3)
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    else:
        fig = ax.figure

    _add_floor(ax, config)
    _draw_half(ax, config, top=False)
    if view == "full":
        _draw_half(ax, config, top=True)
        ax.plot([0, COURT_WIDTH], [47, 47], color=config.line_color, linewidth=config.line_width, zorder=4)
        if config.show_center_circle:
            ax.add_patch(Circle((25, 47), 6, facecolor=_zone_color(config.outer_center_circle_color, config.court_color), edgecolor=config.line_color, linewidth=config.line_width, zorder=2.5))
            ax.add_patch(Circle((25, 47), 2, facecolor=_zone_color(config.inner_center_circle_color, config.court_color), edgecolor=config.line_color, linewidth=config.line_width, zorder=4))
        _add_branding(ax, config, logo)

    margin = config.outer_margin
    y_max = 50.0 if view == "half" else COURT_LENGTH + margin
    ax.set_xlim(-margin, COURT_WIDTH + margin)
    ax.set_ylim(-margin, y_max)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(config.out_of_bounds_color)

    if orientation == "horizontal":
        ax.set_xlim(-margin, y_max)
        ax.set_ylim(-(COURT_WIDTH + margin), margin)
        transform = plt.matplotlib.transforms.Affine2D().rotate_deg(-90)
        for artist in list(ax.patches) + list(ax.lines):
            artist.set_transform(transform + ax.transData)
        # Preserve the center logo's own rotation before rotating the complete
        # court. Previously the court transform replaced this setting, leaving
        # horizontal-court logos sideways.
        from matplotlib.transforms import Affine2D

        for court_logo in ax.images:
            logo_transform = (
                Affine2D()
                .rotate_deg_around(config.logo_x, config.logo_y, config.logo_rotation)
                .rotate_deg(-90)
            )
            court_logo.set_transform(logo_transform + ax.transData)
        # Text needs both its anchor and glyph orientation rotated. Applying an
        # artist transform alone rotates glyphs around an unrotated anchor.
        for label in ax.texts:
            text_x, text_y = label.get_position()
            label.set_position((text_y, -text_x))
            label.set_rotation(float(label.get_rotation()) - 90)

    league_logo_data = _read_logo(league_logo)
    if league_logo_data is not None and view == "full":
        aspect = league_logo_data.shape[1] / max(league_logo_data.shape[0], 1)
        logo_height = max(1.2, 7.0 * config.league_logo_scale)
        logo_width = logo_height * aspect
        if orientation == "horizontal":
            center_x, center_y = 47.0, -(COURT_WIDTH + margin / 2)
        else:
            center_x, center_y = 25.0, -margin / 2
        ax.imshow(
            league_logo_data,
            extent=(center_x - logo_width / 2, center_x + logo_width / 2, center_y - logo_height / 2, center_y + logo_height / 2),
            alpha=config.league_logo_opacity,
            zorder=12,
            interpolation="lanczos",
        )

    fig.tight_layout(pad=0)
    return fig, ax


def plot_shots(
    ax: Axes,
    x: Any,
    y: Any,
    *,
    orientation: str = "vertical",
    made: Any = None,
    made_color: str = "#22C55E",
    missed_color: str = "#EF4444",
    size: float = 34,
    alpha: float = 0.88,
) -> None:
    """Overlay shots measured in the same 50 x 94 foot coordinate system."""

    x_values = np.asarray(x, dtype=float)
    y_values = np.asarray(y, dtype=float)
    if orientation.lower() == "horizontal":
        plot_x, plot_y = y_values, -x_values
    else:
        plot_x, plot_y = x_values, y_values
    if made is None:
        colors: Any = made_color
    else:
        made_values = np.asarray(made, dtype=bool)
        colors = np.where(made_values, made_color, missed_color)
    ax.scatter(plot_x, plot_y, c=colors, s=size, alpha=alpha, edgecolors="white", linewidths=0.55, zorder=10)


def figure_bytes(fig: Figure, file_format: str = "png", dpi: int = 200, transparent: bool = False) -> bytes:
    """Serialize a Matplotlib figure for Streamlit downloads or batch export."""

    output = BytesIO()
    fig.savefig(output, format=file_format, dpi=dpi, bbox_inches="tight", pad_inches=0, transparent=transparent)
    output.seek(0)
    return output.getvalue()
