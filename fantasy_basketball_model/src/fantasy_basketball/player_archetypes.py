from __future__ import annotations

from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd

from .overall_model import ALL_CATEGORIES


ARCHETYPES = {
    "do_it_all_superstar": "Do-It-All Superstar",
    "star_to_build_around": "Star To Build Around",
    "role_player": "Role Player",
    "specialist": "Specialist",
    "minute_filler": "Minute Filler",
    "negative_player": "Negative Player",
    "bench_warmer": "Bench Warmer",
    "sleeper": "Sleeper",
}

SPECIALIST_TYPES = [
    "Shooting Specialist",
    "Scoring Specialist",
    "Playmaking Specialist",
    "Defensive Specialist",
    "Interior Specialist",
]


def _percentile(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.rank(method="average", pct=True).fillna(0.0).clip(0, 1)


def _scale_to_100(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").fillna(0).clip(lower=0)
    upper = numeric.max()
    if upper <= 1e-12:
        return pd.Series(0.0, index=values.index)
    return (100 * numeric / upper).clip(0, 100)


def _ward_clusters(features: np.ndarray, cluster_count: int = 12) -> np.ndarray:
    """Cut a dependency-free Ward agglomerative hierarchy at cluster_count groups."""
    n = len(features)
    if n == 0:
        return np.array([], dtype=int)
    cluster_count = max(1, min(int(cluster_count), n))
    capacity = 2 * n
    distance = np.full((capacity, capacity), np.inf, dtype=float)
    initial = np.square(features[:, None, :] - features[None, :, :]).sum(axis=2)
    distance[:n, :n] = initial
    np.fill_diagonal(distance, np.inf)
    sizes = np.zeros(capacity, dtype=float)
    sizes[:n] = 1.0
    members: dict[int, list[int]] = {index: [index] for index in range(n)}
    active = set(range(n))
    next_index = n

    while len(active) > cluster_count:
        flat_index = int(np.argmin(distance))
        left, right = np.unravel_index(flat_index, distance.shape)
        if left == right or left not in active or right not in active:
            raise RuntimeError("Ward hierarchy reached an invalid merge state")
        if right < left:
            left, right = right, left
        merged_size = sizes[left] + sizes[right]
        others = np.array(sorted(active - {left, right}), dtype=int)
        if len(others):
            updated = (
                (sizes[others] + sizes[left]) * distance[others, left]
                + (sizes[others] + sizes[right]) * distance[others, right]
                - sizes[others] * distance[left, right]
            ) / (sizes[others] + merged_size)
            updated = np.maximum(updated, 0)
            distance[next_index, others] = updated
            distance[others, next_index] = updated
        distance[left, :] = np.inf
        distance[:, left] = np.inf
        distance[right, :] = np.inf
        distance[:, right] = np.inf
        sizes[next_index] = merged_size
        members[next_index] = members.pop(left) + members.pop(right)
        active.remove(left)
        active.remove(right)
        active.add(next_index)
        next_index += 1

    labels = np.zeros(n, dtype=int)
    for label, cluster_index in enumerate(sorted(active), start=1):
        labels[members[cluster_index]] = label
    return labels


def _kmeans(features: np.ndarray, cluster_count: int = 5, max_iterations: int = 100) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic farthest-first K-means used only to subtype specialists."""
    n = len(features)
    cluster_count = max(1, min(int(cluster_count), n))
    first = int(np.argmax(np.square(features).sum(axis=1)))
    centers = [features[first].copy()]
    while len(centers) < cluster_count:
        distance = np.min(
            np.stack([np.square(features - center).sum(axis=1) for center in centers]), axis=0
        )
        centers.append(features[int(np.argmax(distance))].copy())
    centers = np.stack(centers)
    labels = np.full(n, -1, dtype=int)
    for _ in range(max_iterations):
        distance = np.square(features[:, None, :] - centers[None, :, :]).sum(axis=2)
        updated_labels = np.argmin(distance, axis=1)
        if np.array_equal(labels, updated_labels):
            break
        labels = updated_labels
        for cluster in range(cluster_count):
            members = features[labels == cluster]
            if len(members):
                centers[cluster] = members.mean(axis=0)
            else:
                nearest = distance[np.arange(n), labels]
                centers[cluster] = features[int(np.argmax(nearest))]
    return labels, centers


def _specialist_subtypes(skill: pd.DataFrame, specialist_scores: pd.Series) -> pd.Series:
    domains = pd.DataFrame(
        {
            "Shooting Specialist": skill[["rating_TS%", "rating_2PT%", "rating_3PT%", "rating_FT%"]].mean(axis=1),
            "Scoring Specialist": skill[["rating_MP", "rating_PTS"]].mean(axis=1),
            "Playmaking Specialist": skill[["rating_AST", "rating_TOV"]].mean(axis=1),
            "Defensive Specialist": skill[["rating_STL", "rating_BLK", "rating_+/-"]].mean(axis=1),
            "Interior Specialist": skill[["rating_OREB", "rating_DREB", "rating_2PT%", "rating_BLK"]].mean(axis=1),
        },
        index=skill.index,
    )
    # Remove general talent level so K-means discovers the shape of specialization.
    shaped = domains.sub(domains.mean(axis=1), axis=0)
    training = specialist_scores.ge(50)
    if training.sum() < 25:
        training = specialist_scores.rank(pct=True).ge(0.75)
    train = shaped.loc[training]
    means = train.mean(axis=0)
    scales = train.std(axis=0).replace(0, 1)
    train_standardized = train.sub(means).div(scales).to_numpy()
    _, centers = _kmeans(train_standardized, cluster_count=5)

    # Give every cluster a unique basketball meaning by maximizing the five
    # centroid-to-domain matches across all 5! possible assignments.
    best_assignment = max(
        permutations(range(5)),
        key=lambda assignment: sum(centers[cluster, domain] for cluster, domain in enumerate(assignment)),
    )
    standardized = shaped.sub(means).div(scales).to_numpy()
    distance = np.square(standardized[:, None, :] - centers[None, :, :]).sum(axis=2)
    clusters = np.argmin(distance, axis=1)
    labels = [SPECIALIST_TYPES[best_assignment[cluster]] for cluster in clusters]
    return pd.Series(labels, index=skill.index)


def _hierarchical_similarity(frame: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    matrix = features.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    means = np.nanmean(matrix, axis=0)
    matrix = np.where(np.isnan(matrix), means, matrix)
    scales = np.nanstd(matrix, axis=0)
    scales[scales < 1e-9] = 1.0
    standardized = (matrix - means) / scales
    feature_weights = np.array([
        0.45 if str(column).startswith("total_") else 0.75 if str(column).startswith("per36_") else 1.0
        for column in features.columns
    ])
    standardized *= feature_weights
    labels = _ward_clusters(standardized, cluster_count=12)

    # A two-dimensional PCA projection is saved strictly for visualization. Ward
    # clustering and nearest-neighbor distances continue to use the complete
    # weighted feature matrix above; the map is only a readable view of it.
    centered = standardized - standardized.mean(axis=0)
    u, singular_values, _ = np.linalg.svd(centered, full_matrices=False)
    coordinates = u[:, :2] * singular_values[:2]
    if coordinates.shape[1] < 2:
        coordinates = np.column_stack([coordinates[:, 0], np.zeros(len(coordinates))])

    # Number clusters by descending mean overall rating so the IDs are deterministic.
    overall = pd.to_numeric(frame["overall_rating"], errors="coerce").to_numpy()
    order = sorted(np.unique(labels), key=lambda value: -np.nanmean(overall[labels == value]))
    relabel = {old: new for new, old in enumerate(order, start=1)}
    labels = np.array([relabel[value] for value in labels], dtype=int)

    squared = np.square(standardized[:, None, :] - standardized[None, :, :]).sum(axis=2)
    distances = np.sqrt(squared)
    np.fill_diagonal(distances, np.inf)
    names = frame["player_name"].fillna("").astype(str).to_numpy()
    similar_players: list[str] = []
    similarity_scores: list[float] = []
    for index in range(len(frame)):
        same_cluster = np.where(labels == labels[index])[0]
        same_cluster = same_cluster[same_cluster != index]
        pool = same_cluster if len(same_cluster) >= 3 else np.arange(len(frame))
        pool = pool[pool != index]
        nearest = pool[np.argsort(distances[index, pool])[:5]]
        similar_players.append(" | ".join(names[nearest]))
        nearest_distance = distances[index, nearest[0]] if len(nearest) else np.nan
        similarity_scores.append(100 * np.exp(-nearest_distance / np.sqrt(features.shape[1])))
    return pd.DataFrame(
        {
            "hierarchical_cluster": labels,
            "similar_players": similar_players,
            "closest_similarity": similarity_scores,
            "map_x": coordinates[:, 0],
            "map_y": coordinates[:, 1],
        },
        index=frame.index,
    )


def build_player_archetypes(
    players: pd.DataFrame,
    ratings: pd.DataFrame,
    category_weights: pd.DataFrame,
) -> pd.DataFrame:
    identity = [
        "fantrax_player_id", "player_name", "fantasy_team_id", "fantasy_team_name",
        "roster_status", "nba_team", "eligible_positions", "games", "minutes",
    ]
    production_columns = [
        "points", "offensive_rebounds", "defensive_rebounds", "assists", "steals",
        "blocks", "turnovers", "plus_minus", "fg_a", "two_a", "three_a", "ft_a",
        "ts_pct", "two_pct", "three_pct", "ft_pct",
    ]
    frame = players[[*identity, *production_columns]].copy()
    frame["fantrax_player_id"] = frame["fantrax_player_id"].astype(str)
    ratings = ratings.copy()
    ratings["fantrax_player_id"] = ratings["fantrax_player_id"].astype(str)
    rating_columns = [f"rating_{category}" for category in ALL_CATEGORIES]
    probability_columns = [f"probability_rating_{category}" for category in ALL_CATEGORIES]
    frame = frame.merge(
        ratings[["fantrax_player_id", "overall_rating", *rating_columns, *probability_columns]],
        on="fantrax_player_id", how="left", validate="one_to_one",
    )
    projected = frame["overall_rating"].notna()
    result = frame[identity].copy()
    result["overall_rating"] = pd.to_numeric(frame["overall_rating"], errors="coerce")
    for key in ARCHETYPES:
        result[f"score_{key}"] = np.nan
    result["primary_archetype"] = "Unrated"
    result["secondary_archetype"] = ""
    result["specialist_subtype"] = ""
    result["archetype_label"] = "Unrated"
    result["hierarchical_cluster"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    result["similar_players"] = ""
    result["closest_similarity"] = np.nan
    result["map_x"] = np.nan
    result["map_y"] = np.nan
    if not projected.any():
        return result

    work = frame.loc[projected].copy().reset_index().rename(columns={"index": "source_index"})
    skill = work[rating_columns].apply(pd.to_numeric, errors="coerce").clip(0, 10) / 10
    talent = _percentile(work["overall_rating"])
    opportunity = _percentile(pd.to_numeric(work["minutes"], errors="coerce"))
    availability = _percentile(pd.to_numeric(work["games"], errors="coerce"))
    breadth = (skill.ge(0.60).sum(axis=1) / len(rating_columns)).clip(0, 1)
    elite_breadth = (skill.ge(0.72).sum(axis=1) / 8).clip(0, 1)
    specialist_strengths = skill.ge(0.65).sum(axis=1)
    peak = np.sort(skill.to_numpy(), axis=1)[:, -3:].mean(axis=1)
    floor = np.sort(skill.to_numpy(), axis=1)[:, :4].mean(axis=1)
    positive = (skill - 0.5).clip(lower=0)
    top_three_positive = np.sort(positive.to_numpy(), axis=1)[:, -3:].sum(axis=1)
    concentration = pd.Series(
        np.divide(top_three_positive, positive.sum(axis=1), out=np.zeros(len(work)), where=positive.sum(axis=1).to_numpy() > 0),
        index=work.index,
    )

    weights = category_weights.set_index("category")["weight"].reindex(ALL_CATEGORIES).astype(float)
    probabilities = work[probability_columns].apply(pd.to_numeric, errors="coerce") / 10
    probabilities.columns = ALL_CATEGORIES
    impact_points = probabilities.sub(0.5).mul(weights, axis=1).sum(axis=1)
    minutes = pd.to_numeric(work["minutes"], errors="coerce").clip(lower=8)
    rate_quality = _percentile(impact_points / minutes)
    counting_volume = skill[[f"rating_{category}" for category in ["MP", "PTS", "OREB", "DREB", "AST", "STL", "BLK"]]].mean(axis=1)
    risk_columns = [f"rating_{category}" for category in ["TS%", "2PT%", "3PT%", "FT%", "TOV", "+/-"]]
    risk_skill = skill[risk_columns]
    downside = ((0.5 - risk_skill).clip(lower=0) / 0.5).mean(axis=1).clip(0, 1)
    no_downside = (1 - downside).clip(0, 1)
    balance = (1 - skill.std(axis=1) / 0.35).clip(0, 1)
    middle_talent = (1 - (talent - 0.58).abs() / 0.58).clip(0, 1)

    raw = pd.DataFrame(index=work.index)
    raw["do_it_all_superstar"] = (
        talent.pow(0.36) * breadth.pow(0.25) * pd.Series(floor, index=work.index).pow(0.19)
        * opportunity.pow(0.12) * no_downside.pow(0.08)
    )
    raw["star_to_build_around"] = (
        talent.pow(0.45) * pd.Series(elite_breadth, index=work.index).pow(0.27)
        * pd.Series(peak, index=work.index).pow(0.18) * opportunity.pow(0.10)
    )
    specialist_band = (1 - (specialist_strengths - 2.5).abs() / 4).clip(0, 1)
    specialist_peak = ((pd.Series(peak, index=work.index) - 0.55) / 0.35).clip(0, 1)
    raw["specialist"] = (
        specialist_peak.pow(0.38) * concentration.pow(0.34)
        * specialist_band.pow(0.20) * talent.clip(lower=0.10).pow(0.08)
    )
    raw["role_player"] = (
        middle_talent.pow(0.32) * balance.clip(lower=0.05).pow(0.25)
        * opportunity.pow(0.23) * no_downside.pow(0.20)
    )
    raw["minute_filler"] = (
        opportunity.pow(0.48) * (1 - rate_quality).pow(0.32)
        * pd.Series(counting_volume, index=work.index).pow(0.20)
    )
    raw["negative_player"] = (
        opportunity.pow(0.32) * downside.pow(0.38) * (1 - talent).pow(0.30)
    )
    raw["bench_warmer"] = (
        (1 - opportunity).pow(0.42) * (1 - rate_quality).pow(0.30) * (1 - talent).pow(0.28)
    )
    raw["sleeper"] = (
        (1 - opportunity).pow(0.42) * rate_quality.pow(0.33)
        * pd.Series(peak, index=work.index).pow(0.15) * availability.pow(0.10)
    )

    scores = pd.DataFrame({key: _scale_to_100(raw[key]) for key in ARCHETYPES}, index=work.index)
    specialist_subtype = _specialist_subtypes(skill, scores["specialist"])
    score_array = scores.to_numpy()
    superstar_index = list(ARCHETYPES).index("do_it_all_superstar")
    superstar_count = min(10, max(5, round(len(work) * 0.0175)))
    superstar_members = np.zeros(len(work), dtype=bool)
    broad_candidates = np.where(skill.ge(0.60).sum(axis=1).to_numpy() >= 7)[0]
    if len(broad_candidates) >= superstar_count:
        candidate_talent = pd.to_numeric(work.loc[broad_candidates, "overall_rating"], errors="coerce").to_numpy()
        chosen = broad_candidates[np.argsort(-candidate_talent)[:superstar_count]]
    else:
        chosen = np.argsort(-raw["do_it_all_superstar"].to_numpy())[:superstar_count]
    superstar_members[chosen] = True
    label_scores = score_array.copy()
    label_scores[~superstar_members, superstar_index] = -np.inf
    order = np.argsort(-label_scores, axis=1)
    names = list(ARCHETYPES.values())
    primary = [names[index] for index in order[:, 0]]
    secondary = [names[index] for index in order[:, 1]]
    primary_score = score_array[np.arange(len(work)), order[:, 0]]
    secondary_score = score_array[np.arange(len(work)), order[:, 1]]
    has_secondary = (secondary_score >= 60) & (secondary_score >= 0.86 * primary_score)
    has_secondary[superstar_members] = False
    primary = np.where(superstar_members, ARCHETYPES["do_it_all_superstar"], primary).tolist()
    secondary = np.where(superstar_members, "", secondary).tolist()
    labels = [
        f"{first} / {second}" if dual else first
        for first, second, dual in zip(primary, secondary, has_secondary)
    ]

    # Ward similarity deliberately blends actual projected totals with per-36 skill shape.
    # Totals capture fantasy opportunity; per-36 rates keep high-minute accumulation from
    # masquerading as the same player type as genuine rate production.
    total_minutes = (
        pd.to_numeric(work["games"], errors="coerce")
        * pd.to_numeric(work["minutes"], errors="coerce")
    ).replace(0, np.nan)
    counting_stats = [
        "points", "offensive_rebounds", "defensive_rebounds", "assists", "steals",
        "blocks", "turnovers", "plus_minus",
    ]
    hierarchy_features = work[rating_columns].apply(pd.to_numeric, errors="coerce").copy()
    for column in counting_stats:
        totals = pd.to_numeric(work[column], errors="coerce")
        hierarchy_features[f"total_{column}"] = totals
        hierarchy_features[f"per36_{column}"] = totals.div(total_minutes).mul(36)
    hierarchy_features["total_minutes"] = total_minutes
    for column in ["fg_a", "two_a", "three_a", "ft_a"]:
        hierarchy_features[f"total_{column}"] = pd.to_numeric(work[column], errors="coerce")
    hierarchy = _hierarchical_similarity(work, hierarchy_features)
    target_index = work["source_index"].to_numpy()
    for key in ARCHETYPES:
        result.loc[target_index, f"score_{key}"] = scores[key].round(1).to_numpy()
    result.loc[target_index, "primary_archetype"] = primary
    result.loc[target_index, "secondary_archetype"] = np.where(has_secondary, secondary, "")
    result.loc[target_index, "specialist_subtype"] = specialist_subtype.to_numpy()
    result.loc[target_index, "archetype_label"] = labels
    result.loc[target_index, "hierarchical_cluster"] = hierarchy["hierarchical_cluster"].to_numpy()
    result.loc[target_index, "similar_players"] = hierarchy["similar_players"].to_numpy()
    result.loc[target_index, "closest_similarity"] = hierarchy["closest_similarity"].round(1).to_numpy()
    result.loc[target_index, "map_x"] = hierarchy["map_x"].round(6).to_numpy()
    result.loc[target_index, "map_y"] = hierarchy["map_y"].round(6).to_numpy()
    return result


def write_player_archetypes(processed_dir: Path, categories_path: Path) -> dict[str, int]:
    players = pd.read_csv(processed_dir / "canonical_player_projections.csv", dtype={"fantrax_player_id": str})
    ratings = pd.read_csv(processed_dir / "player_value_ratings.csv", dtype={"fantrax_player_id": str})
    categories = pd.read_csv(categories_path)
    result = build_player_archetypes(players, ratings, categories)
    result.to_csv(processed_dir / "player_archetypes.csv", index=False)
    projected = result[result["archetype_label"].ne("Unrated")]
    summary_source = projected.sort_values(
        ["hierarchical_cluster", "overall_rating"], ascending=[True, False]
    )
    summary = (
        summary_source.groupby("hierarchical_cluster", dropna=False)
        .agg(
            players=("fantrax_player_id", "size"),
            most_common_archetype=("primary_archetype", lambda values: values.mode().iloc[0]),
            example_players=("player_name", lambda values: " | ".join(values.head(4))),
        )
        .reset_index()
    )
    summary.to_csv(processed_dir / "hierarchical_cluster_summary.csv", index=False)
    return {
        "players": len(result),
        "rated_players": len(projected),
        "archetypes_observed": projected["archetype_label"].nunique(),
        "hierarchical_clusters": projected["hierarchical_cluster"].nunique(),
    }
