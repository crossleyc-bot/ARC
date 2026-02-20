from app.engine.normalizer import (
    compute_content_hash,
    extract_field_set,
    normalize_expression,
    normalize_name,
)


class TestNormalizeName:
    def test_basic_normalization(self):
        assert normalize_name("Revenue_YTD") == "revenue ytd"
        assert normalize_name("  Total-Sales  ") == "total sales"
        assert normalize_name("NET_PROFIT_MARGIN") == "net profit margin"

    def test_case_insensitive(self):
        assert normalize_name("Revenue") == normalize_name("revenue")
        assert normalize_name("TOTAL SALES") == normalize_name("total sales")

    def test_special_chars(self):
        assert normalize_name("profit_margin") == normalize_name("profit-margin")
        # Double underscore becomes double space then collapsed to single
        assert normalize_name("total__sales") == "total sales"


class TestNormalizeExpression:
    def test_empty(self):
        assert normalize_expression(None) == ""
        assert normalize_expression("") == ""

    def test_whitespace(self):
        result = normalize_expression("SUM(  Sales  )")
        assert result == "sum( sales )"

    def test_removes_comments(self):
        expr = """
        SUM(Sales) -- this is total sales
        + SUM(Returns)
        """
        result = normalize_expression(expr)
        assert "--" not in result
        assert "sum(sales)" in result

    def test_block_comments(self):
        expr = "SUM(Sales) /* total */ + SUM(Returns)"
        result = normalize_expression(expr)
        assert "/*" not in result
        assert "*/" not in result


class TestComputeContentHash:
    def test_same_content_same_hash(self):
        meta1 = {"name": "Sales Report", "fields_used": ["revenue", "cost"], "report_type": "dashboard"}
        meta2 = {"name": "Sales Report", "fields_used": ["cost", "revenue"], "report_type": "dashboard"}
        assert compute_content_hash(meta1) == compute_content_hash(meta2)

    def test_different_content_different_hash(self):
        meta1 = {"name": "Sales Report", "fields_used": ["revenue"], "report_type": "dashboard"}
        meta2 = {"name": "HR Report", "fields_used": ["salary"], "report_type": "dashboard"}
        assert compute_content_hash(meta1) != compute_content_hash(meta2)


class TestExtractFieldSet:
    def test_from_fields_used(self):
        meta = {"fields_used": ["Revenue", "Cost", "Profit"]}
        fields = extract_field_set(meta)
        assert "revenue" in fields
        assert "cost" in fields
        assert "profit" in fields

    def test_from_raw_metadata_tables(self):
        meta = {
            "fields_used": [],
            "raw_metadata": {
                "tables": [
                    {"name": "Sales", "columns": [{"name": "Amount"}, {"name": "Date"}]}
                ]
            },
        }
        fields = extract_field_set(meta)
        assert "amount" in fields
        assert "date" in fields

    def test_empty_metadata(self):
        assert extract_field_set({}) == set()
