from app.engine.kpi_detector import detect_kpi_conflicts


class TestDetectKPIConflicts:
    def test_no_conflicts(self):
        measures = [
            {"name": "Revenue", "expression": "SUM(Sales.Amount)", "access_count": 10},
            {"name": "Cost", "expression": "SUM(Costs.Amount)", "access_count": 10},
        ]
        conflicts = detect_kpi_conflicts(measures)
        assert len(conflicts) == 0

    def test_same_name_same_expression(self):
        measures = [
            {"name": "Revenue", "expression": "SUM(Sales.Amount)", "access_count": 10},
            {"name": "Revenue", "expression": "SUM(Sales.Amount)", "access_count": 20},
        ]
        conflicts = detect_kpi_conflicts(measures)
        assert len(conflicts) == 0

    def test_same_name_different_expression(self):
        measures = [
            {"name": "Revenue", "expression": "SUM(Sales.Amount)", "access_count": 10},
            {"name": "Revenue", "expression": "SUM(Orders.Total)", "access_count": 20},
        ]
        conflicts = detect_kpi_conflicts(measures)
        assert len(conflicts) == 1
        assert conflicts[0].measure_name == "Revenue"
        assert len(conflicts[0].conflicting_definitions) == 2

    def test_severity_scoring(self):
        measures = [
            {"name": "Revenue", "expression": "SUM(A)", "access_count": 200},
            {"name": "Revenue", "expression": "SUM(B)", "access_count": 200},
            {"name": "Revenue", "expression": "SUM(C)", "access_count": 200},
        ]
        conflicts = detect_kpi_conflicts(measures)
        assert len(conflicts) == 1
        assert conflicts[0].severity == "critical"

    def test_case_insensitive_matching(self):
        measures = [
            {"name": "total_revenue", "expression": "SUM(A)", "access_count": 0},
            {"name": "Total Revenue", "expression": "SUM(B)", "access_count": 0},
        ]
        conflicts = detect_kpi_conflicts(measures)
        assert len(conflicts) == 1

    def test_multiple_conflicts(self):
        measures = [
            {"name": "Revenue", "expression": "SUM(A)", "access_count": 0},
            {"name": "Revenue", "expression": "SUM(B)", "access_count": 0},
            {"name": "Profit", "expression": "X - Y", "access_count": 0},
            {"name": "Profit", "expression": "A - B", "access_count": 0},
        ]
        conflicts = detect_kpi_conflicts(measures)
        assert len(conflicts) == 2
