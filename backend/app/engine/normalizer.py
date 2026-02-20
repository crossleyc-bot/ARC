import hashlib
import json
import re


def normalize_name(name: str) -> str:
    """Normalize a measure/field name for comparison.

    Lowercases, strips whitespace, removes underscores/hyphens,
    collapses multiple spaces.
    """
    name = name.lower().strip()
    name = re.sub(r"[_\-]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name


def compute_content_hash(report_metadata: dict) -> str:
    """Compute a deterministic hash of report content for exact duplicate detection.

    Uses a subset of metadata fields that represent the report's actual content,
    excluding volatile fields like last_accessed or access_count.
    """
    content_fields = {
        "name": report_metadata.get("name", ""),
        "fields_used": sorted(report_metadata.get("fields_used", [])),
        "report_type": report_metadata.get("report_type", ""),
    }

    # Include raw structural metadata if available
    raw = report_metadata.get("raw_metadata", {})
    if "dataset_id" in raw:
        content_fields["dataset_id"] = raw["dataset_id"]
    if "tables" in raw:
        content_fields["tables"] = raw["tables"]

    serialized = json.dumps(content_fields, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def normalize_expression(expression: str | None) -> str:
    """Normalize a DAX or SQL expression for comparison.

    Strips whitespace, lowercases, removes comments.
    """
    if not expression:
        return ""
    expr = expression.lower().strip()
    # Remove single-line comments
    expr = re.sub(r"--.*$", "", expr, flags=re.MULTILINE)
    # Remove block comments
    expr = re.sub(r"/\*.*?\*/", "", expr, flags=re.DOTALL)
    # Normalize whitespace
    expr = re.sub(r"\s+", " ", expr)
    return expr.strip()


def extract_field_set(report_metadata: dict) -> set[str]:
    """Extract the set of normalized field names used by a report."""
    fields = set()

    for f in report_metadata.get("fields_used", []):
        fields.add(normalize_name(f))

    # Also extract from tables/columns in raw metadata
    raw = report_metadata.get("raw_metadata", {})
    for table in raw.get("tables", []):
        if isinstance(table, dict):
            for col in table.get("columns", []):
                if isinstance(col, dict):
                    col_name = col.get("name", "")
                    if col_name:
                        fields.add(normalize_name(col_name))

    return fields
