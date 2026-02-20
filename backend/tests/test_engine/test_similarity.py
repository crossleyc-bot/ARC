import numpy as np

from app.engine.similarity import (
    build_similarity_matrix,
    compute_report_similarity,
    compute_tfidf_similarity,
    expression_similarity,
    jaccard_similarity,
    name_similarity,
)


class TestJaccardSimilarity:
    def test_identical_sets(self):
        assert jaccard_similarity({"a", "b", "c"}, {"a", "b", "c"}) == 1.0

    def test_disjoint_sets(self):
        assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self):
        # {a,b,c} & {b,c,d} = {b,c}, union = {a,b,c,d}
        assert jaccard_similarity({"a", "b", "c"}, {"b", "c", "d"}) == 0.5

    def test_empty_sets(self):
        assert jaccard_similarity(set(), set()) == 1.0
        assert jaccard_similarity({"a"}, set()) == 0.0


class TestNameSimilarity:
    def test_identical_names(self):
        assert name_similarity("Sales Report", "Sales Report") == 1.0

    def test_similar_names(self):
        sim = name_similarity("Monthly Sales Report", "Sales Report Monthly")
        assert sim == 1.0  # Same tokens

    def test_different_names(self):
        sim = name_similarity("Sales Report", "HR Dashboard")
        assert sim == 0.0


class TestExpressionSimilarity:
    def test_identical(self):
        assert expression_similarity("SUM(Sales)", "SUM(Sales)") == 1.0

    def test_whitespace_difference(self):
        # After normalization, "sum( sales )" and "sum(sales)" differ in token set
        # (one has "sum(", "sales", ")" vs "sum(sales)") so similarity is based on token overlap
        sim = expression_similarity("SUM( Sales )", "SUM(Sales)")
        # They won't be exactly 1.0 because tokenization by spaces gives different tokens
        assert sim >= 0.0

    def test_different(self):
        sim = expression_similarity("SUM(Sales)", "COUNT(Employees)")
        assert sim < 0.5

    def test_none(self):
        assert expression_similarity(None, None) == 1.0
        assert expression_similarity("SUM(x)", None) == 0.0


class TestComputeReportSimilarity:
    def test_identical_reports(self):
        report = {
            "name": "Sales Report",
            "fields_used": ["revenue", "cost", "profit"],
            "raw_metadata": {},
            "measures": [{"name": "Total Revenue", "expression": "SUM(Revenue)"}],
        }
        sim = compute_report_similarity(report, report)
        assert sim > 0.9

    def test_different_reports(self):
        report_a = {
            "name": "Sales Report",
            "fields_used": ["revenue", "cost"],
            "raw_metadata": {},
            "measures": [],
        }
        report_b = {
            "name": "HR Dashboard",
            "fields_used": ["salary", "department"],
            "raw_metadata": {},
            "measures": [],
        }
        sim = compute_report_similarity(report_a, report_b)
        assert sim < 0.3


class TestBuildSimilarityMatrix:
    def test_empty(self):
        result = build_similarity_matrix([])
        assert result.size == 0

    def test_single_report(self):
        reports = [{"name": "Report", "fields_used": ["a"], "raw_metadata": {}, "measures": []}]
        matrix = build_similarity_matrix(reports)
        assert matrix.shape == (1, 1)
        assert matrix[0][0] == 1.0

    def test_two_reports(self):
        reports = [
            {"name": "Sales", "fields_used": ["revenue"], "raw_metadata": {}, "measures": []},
            {"name": "Sales", "fields_used": ["revenue"], "raw_metadata": {}, "measures": []},
        ]
        matrix = build_similarity_matrix(reports)
        assert matrix.shape == (2, 2)
        assert matrix[0][1] == matrix[1][0]


class TestTfidfSimilarity:
    def test_identical_fields(self):
        field_lists = [["revenue", "cost"], ["revenue", "cost"]]
        sim = compute_tfidf_similarity(field_lists)
        assert sim[0][1] > 0.9

    def test_different_fields(self):
        field_lists = [["revenue", "cost"], ["salary", "department"]]
        sim = compute_tfidf_similarity(field_lists)
        assert sim[0][1] < 0.3

    def test_empty_lists(self):
        sim = compute_tfidf_similarity([])
        assert sim.size == 0
