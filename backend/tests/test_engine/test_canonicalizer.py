from app.engine.canonicalizer import (
    generate_rationalization_actions,
    propose_canonical_dataset,
)


class TestProposeCanonicalDataset:
    def test_basic_proposal(self):
        reports = [
            {"id": "r1", "name": "Sales Q1", "fields_used": ["revenue", "cost", "date"], "raw_metadata": {}, "access_count": 100},
            {"id": "r2", "name": "Sales Q2", "fields_used": ["revenue", "profit", "date"], "raw_metadata": {}, "access_count": 50},
        ]
        measures = [
            {"name": "Total Revenue", "expression": "SUM(Revenue)", "data_type": "decimal", "access_count": 100},
            {"name": "Total Revenue", "expression": "SUM(Revenue)", "data_type": "decimal", "access_count": 50},
        ]
        proposal = propose_canonical_dataset(reports, measures, "Sales Cluster")
        assert proposal.name == "Canonical - Sales Cluster"
        assert len(proposal.dimensions) > 0  # Should have shared dimensions
        assert len(proposal.gap_analyses) == 2

    def test_empty_cluster(self):
        proposal = propose_canonical_dataset([], [], "Empty")
        assert proposal.name == "Empty"
        assert "Empty cluster" in proposal.description

    def test_gap_analysis_scores(self):
        reports = [
            {"id": "r1", "name": "Full Report", "fields_used": ["a", "b", "c", "d"], "raw_metadata": {}, "access_count": 100},
            {"id": "r2", "name": "Partial Report", "fields_used": ["a", "b"], "raw_metadata": {}, "access_count": 10},
        ]
        proposal = propose_canonical_dataset(reports, [], "Test")
        # Full report should have higher compatibility
        gap_r1 = next(g for g in proposal.gap_analyses if g["report_id"] == "r1")
        gap_r2 = next(g for g in proposal.gap_analyses if g["report_id"] == "r2")
        assert gap_r1["compatibility_score"] >= gap_r2["compatibility_score"]


class TestGenerateRationalizationActions:
    def test_exact_duplicate_retirement(self):
        reports = [
            {"id": "r1", "name": "Report A", "access_count": 100},
            {"id": "r2", "name": "Report A Copy", "access_count": 10},
        ]
        actions = generate_rationalization_actions(
            reports,
            exact_duplicate_groups=[[0, 1]],
            near_duplicate_groups=[],
            family_groups=[],
        )
        retire_actions = [a for a in actions if a.action == "retire"]
        assert len(retire_actions) == 1
        assert retire_actions[0].report_id == "r2"

    def test_near_duplicate_merge(self):
        reports = [
            {"id": "r1", "name": "Report A", "access_count": 100},
            {"id": "r2", "name": "Report A v2", "access_count": 50},
        ]
        actions = generate_rationalization_actions(
            reports,
            exact_duplicate_groups=[],
            near_duplicate_groups=[[0, 1]],
            family_groups=[],
        )
        merge_actions = [a for a in actions if a.action == "merge"]
        assert len(merge_actions) == 1

    def test_unique_reports_kept(self):
        reports = [
            {"id": "r1", "name": "Unique Report", "access_count": 50},
        ]
        actions = generate_rationalization_actions(
            reports,
            exact_duplicate_groups=[],
            near_duplicate_groups=[],
            family_groups=[],
        )
        assert len(actions) == 1
        assert actions[0].action == "keep"

    def test_priority_ordering(self):
        reports = [
            {"id": "r1", "name": "Primary", "access_count": 100},
            {"id": "r2", "name": "Duplicate", "access_count": 10},
            {"id": "r3", "name": "Near Dup", "access_count": 30},
            {"id": "r4", "name": "Unique", "access_count": 50},
        ]
        actions = generate_rationalization_actions(
            reports,
            exact_duplicate_groups=[[0, 1]],
            near_duplicate_groups=[[0, 2]],
            family_groups=[],
        )
        # Actions should be sorted by priority
        priorities = [a.priority for a in actions]
        assert priorities == sorted(priorities)
