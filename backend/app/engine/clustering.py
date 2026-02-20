import logging
from collections import defaultdict

import numpy as np
from sklearn.cluster import AgglomerativeClustering, DBSCAN

logger = logging.getLogger(__name__)


def find_exact_duplicates(
    report_ids: list[str], content_hashes: list[str | None]
) -> list[list[int]]:
    """Group reports by content hash to find exact duplicates.

    Returns list of index groups, each group having 2+ members.
    """
    hash_groups: dict[str, list[int]] = defaultdict(list)
    for i, h in enumerate(content_hashes):
        if h:
            hash_groups[h].append(i)

    return [indices for indices in hash_groups.values() if len(indices) > 1]


def find_near_duplicates(
    similarity_matrix: np.ndarray, threshold: float = 0.75
) -> list[list[int]]:
    """Find near-duplicate clusters using agglomerative clustering.

    Uses the similarity matrix and a distance threshold.
    """
    n = similarity_matrix.shape[0]
    if n < 2:
        return []

    # Convert similarity to distance
    distance_matrix = 1.0 - similarity_matrix
    np.fill_diagonal(distance_matrix, 0)

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1.0 - threshold,
        metric="precomputed",
        linkage="average",
    )
    labels = clustering.fit_predict(distance_matrix)

    groups: dict[int, list[int]] = defaultdict(list)
    for i, label in enumerate(labels):
        groups[label].append(i)

    return [indices for indices in groups.values() if len(indices) > 1]


def find_report_families(
    similarity_matrix: np.ndarray,
    min_similarity: float = 0.4,
    min_samples: int = 2,
) -> list[list[int]]:
    """Find broader report families using DBSCAN on the similarity graph.

    Lower threshold captures reports that are related but not duplicates.
    """
    n = similarity_matrix.shape[0]
    if n < 2:
        return []

    distance_matrix = 1.0 - similarity_matrix
    np.fill_diagonal(distance_matrix, 0)

    clustering = DBSCAN(
        eps=1.0 - min_similarity,
        min_samples=min_samples,
        metric="precomputed",
    )
    labels = clustering.fit_predict(distance_matrix)

    groups: dict[int, list[int]] = defaultdict(list)
    for i, label in enumerate(labels):
        if label != -1:  # Ignore noise points
            groups[label].append(i)

    return [indices for indices in groups.values() if len(indices) > 1]


def select_primary_report(report_indices: list[int], access_counts: list[int]) -> int:
    """Select the primary (canonical) report in a cluster based on usage.

    Returns the index of the most-accessed report.
    """
    best_idx = report_indices[0]
    best_count = access_counts[report_indices[0]] if report_indices[0] < len(access_counts) else 0

    for idx in report_indices[1:]:
        count = access_counts[idx] if idx < len(access_counts) else 0
        if count > best_count:
            best_count = count
            best_idx = idx

    return best_idx
