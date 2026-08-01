"""Deterministic game-uniform rotation and color-clash protection."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Callable, Mapping


IMPORTANT_GAME_WORDS = (
    "playoff", "play-in", "final", "championship", "tournament",
    "cup", "semifinal", "quarterfinal", "knockout",
)


def game_identity(matchup: Mapping[str, Any], road_team: str, home_team: str) -> str:
    parts = [
        matchup.get("Game_ID", matchup.get("GameID", "")),
        matchup.get("Year", ""), matchup.get("Period", ""),
        matchup.get("Round", ""), matchup.get("Type", ""),
        road_team, home_team,
    ]
    return "|".join(str(part).strip() for part in parts)


def is_important_game(matchup: Mapping[str, Any]) -> bool:
    label = " ".join(str(matchup.get(field, "")) for field in ("Type", "Round", "Competition", "Stage")).lower()
    return any(word in label for word in IMPORTANT_GAME_WORDS)


def stable_fraction(key: str) -> float:
    value = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
    return value / float(2**64 - 1)


def planned_edition(matchup: Mapping[str, Any], team: str, role: str) -> str:
    """Choose a stable edition; weighted rates combine to roughly 20% Statement."""
    probability = 0.22 if is_important_game(matchup) else 0.20
    identity = game_identity(matchup, str(matchup.get("TeamA", "")), str(matchup.get("TeamB", "")))
    if stable_fraction(f"statement|{identity}|{team}|{role}") < probability:
        return "Statement"
    return "Icon" if role == "road" else "Association"


def _hex_rgb(value: Any) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"#?([0-9a-fA-F]{6})", str(value or "").strip())
    if not match:
        return None
    raw = match.group(1)
    return tuple(int(raw[index:index + 2], 16) for index in (0, 2, 4))


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for value in rgb:
        channel = value / 255
        channels.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def uniform_separation(road: Any, home: Any) -> float:
    """Score visual separation using base color first and supporting colors second."""
    road_colors = [_hex_rgb(getattr(road, field, "")) for field in ("jersey_color", "accent_color", "number_color")]
    home_colors = [_hex_rgb(getattr(home, field, "")) for field in ("jersey_color", "accent_color", "number_color")]
    if road_colors[0] is None or home_colors[0] is None:
        return 1000.0
    base_distance = math.dist(road_colors[0], home_colors[0])
    luminance_gap = abs(_relative_luminance(road_colors[0]) - _relative_luminance(home_colors[0]))
    supporting = [
        math.dist(a, b) for a, b in zip(road_colors[1:], home_colors[1:])
        if a is not None and b is not None
    ]
    supporting_distance = sum(supporting) / len(supporting) if supporting else base_distance
    return base_distance + 150 * luminance_gap + 0.15 * supporting_distance


def uniforms_clash(road: Any, home: Any) -> bool:
    return uniform_separation(road, home) < 105.0


def select_game_uniforms(
    matchup: Mapping[str, Any],
    road_team: str,
    home_team: str,
    config_loader: Callable[[str, str], Any],
) -> tuple[str, str, bool]:
    """Return road edition, home edition, and whether clash protection intervened."""
    assigned_road = str(matchup.get("RoadJersey", "") or "").strip()
    assigned_home = str(matchup.get("HomeJersey", "") or "").strip()
    if assigned_road and assigned_home:
        adjusted = str(matchup.get("JerseyClashAdjusted", "")).strip().lower() in {"1", "true", "yes"}
        return assigned_road, assigned_home, adjusted
    road_edition = planned_edition(matchup, road_team, "road")
    home_edition = planned_edition(matchup, home_team, "home")
    home_config = config_loader(home_team, home_edition)
    road_config = config_loader(road_team, road_edition)
    if not uniforms_clash(road_config, home_config):
        return road_edition, home_edition, False

    alternatives = [edition for edition in ("Icon", "Statement", "Association") if edition != road_edition]
    scored = [
        (uniform_separation(config_loader(road_team, edition), home_config), edition)
        for edition in alternatives
    ]
    best_score, best_edition = max(scored, key=lambda item: item[0])
    if best_score > uniform_separation(road_config, home_config):
        return best_edition, home_edition, True
    return road_edition, home_edition, False
