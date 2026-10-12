import numpy as np
import pandas as pd

from fantasy_basketball.player_archetypes import ARCHETYPES, _kmeans, _ward_clusters


def test_ward_clusters_separate_distant_groups():
    features = np.array([[0.0, 0.0], [0.1, 0.1], [10.0, 10.0], [10.1, 10.1]])
    labels = _ward_clusters(features, cluster_count=2)
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert labels[0] != labels[2]


def test_eight_named_archetypes_are_unique():
    assert len(ARCHETYPES) == 8
    assert len(set(ARCHETYPES.values())) == 8


def test_kmeans_separates_obvious_specialist_shapes():
    features = np.array([
        [5.0, 0.0], [4.8, 0.1], [0.0, 5.0], [0.1, 4.8],
    ])
    labels, centers = _kmeans(features, cluster_count=2)
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert labels[0] != labels[2]
    assert centers.shape == (2, 2)
