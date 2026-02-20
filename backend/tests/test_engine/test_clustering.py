import numpy as np

from app.engine.clustering import (
    find_exact_duplicates,
    find_near_duplicates,
    find_report_families,
    select_primary_report,
)


class TestFindExactDuplicates:
    def test_no_duplicates(self):
        groups = find_exact_duplicates(["r1", "r2", "r3"], ["h1", "h2", "h3"])
        assert groups == []

    def test_one_duplicate_pair(self):
        groups = find_exact_duplicates(["r1", "r2", "r3"], ["h1", "h1", "h2"])
        assert len(groups) == 1
        assert set(groups[0]) == {0, 1}

    def test_multiple_groups(self):
        groups = find_exact_duplicates(
            ["r1", "r2", "r3", "r4"],
            ["h1", "h1", "h2", "h2"],
        )
        assert len(groups) == 2

    def test_none_hashes_ignored(self):
        groups = find_exact_duplicates(["r1", "r2"], [None, None])
        assert groups == []


class TestFindNearDuplicates:
    def test_high_similarity(self):
        # 2x2 matrix where reports are very similar
        matrix = np.array([[1.0, 0.9], [0.9, 1.0]])
        groups = find_near_duplicates(matrix, threshold=0.75)
        assert len(groups) == 1
        assert set(groups[0]) == {0, 1}

    def test_low_similarity(self):
        matrix = np.array([[1.0, 0.1], [0.1, 1.0]])
        groups = find_near_duplicates(matrix, threshold=0.75)
        assert groups == []

    def test_single_report(self):
        matrix = np.array([[1.0]])
        groups = find_near_duplicates(matrix, threshold=0.75)
        assert groups == []


class TestFindReportFamilies:
    def test_family_detection(self):
        # 3 reports that are moderately similar
        matrix = np.array([
            [1.0, 0.6, 0.5],
            [0.6, 1.0, 0.55],
            [0.5, 0.55, 1.0],
        ])
        groups = find_report_families(matrix, min_similarity=0.4, min_samples=2)
        # Should find at least one family
        assert len(groups) >= 1

    def test_no_families(self):
        # 3 very different reports
        matrix = np.array([
            [1.0, 0.05, 0.05],
            [0.05, 1.0, 0.05],
            [0.05, 0.05, 1.0],
        ])
        groups = find_report_families(matrix, min_similarity=0.4, min_samples=2)
        assert groups == []


class TestSelectPrimaryReport:
    def test_selects_highest_usage(self):
        indices = [0, 1, 2]
        access_counts = [10, 100, 50]
        assert select_primary_report(indices, access_counts) == 1

    def test_single_report(self):
        assert select_primary_report([0], [5]) == 0
