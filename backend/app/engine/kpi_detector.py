import logging
from collections import defaultdict
from dataclasses import dataclass, field

from app.engine.normalizer import normalize_expression, normalize_name

logger = logging.getLogger(__name__)


@dataclass
class KPIConflictResult:
    measure_name: str
    conflicting_definitions: list[dict] = field(default_factory=list)
    severity: str = "info"  # critical, warning, info


def detect_kpi_conflicts(
    measures: list[dict],
) -> list[KPIConflictResult]:
    """Detect KPI definition conflicts across measures.

    Groups measures by normalized name, then compares expressions
    within each group to find conflicts.

    Args:
        measures: List of dicts with keys: name, expression, dataset_name, report_name, access_count
    """
    # Group by normalized name
    name_groups: dict[str, list[dict]] = defaultdict(list)
    for m in measures:
        norm = normalize_name(m.get("name", ""))
        if norm:
            name_groups[norm].append(m)

    conflicts = []

    for norm_name, group in name_groups.items():
        if len(group) < 2:
            continue

        # Check if expressions differ within the group
        expressions = {}
        for m in group:
            expr = normalize_expression(m.get("expression"))
            if expr not in expressions:
                expressions[expr] = []
            expressions[expr].append(m)

        if len(expressions) < 2:
            # All expressions are the same — no conflict
            continue

        # There is a conflict
        conflicting_defs = []
        for expr, members in expressions.items():
            conflicting_defs.append(
                {
                    "expression": expr or "(no expression)",
                    "count": len(members),
                    "sources": [
                        {
                            "dataset": m.get("dataset_name", ""),
                            "report": m.get("report_name", ""),
                            "access_count": m.get("access_count", 0),
                        }
                        for m in members
                    ],
                }
            )

        # Score severity based on usage and divergence
        total_access = sum(m.get("access_count", 0) for m in group)
        expr_count = len(expressions)

        if total_access > 100 and expr_count > 2:
            severity = "critical"
        elif total_access > 50 or expr_count > 2:
            severity = "warning"
        else:
            severity = "info"

        conflicts.append(
            KPIConflictResult(
                measure_name=group[0].get("name", norm_name),
                conflicting_definitions=conflicting_defs,
                severity=severity,
            )
        )

    # Sort by severity
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    conflicts.sort(key=lambda c: severity_order.get(c.severity, 3))

    return conflicts
