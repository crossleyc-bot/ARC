import logging
from collections import Counter
from dataclasses import dataclass, field

from app.engine.normalizer import extract_field_set, normalize_name

logger = logging.getLogger(__name__)


@dataclass
class CanonicalDatasetProposal:
    name: str
    description: str
    grain: str | None = None
    dimensions: list[str] = field(default_factory=list)
    measures: list[dict] = field(default_factory=list)
    source_reports: list[dict] = field(default_factory=list)
    gap_analyses: list[dict] = field(default_factory=list)


@dataclass
class RationalizationAction:
    report_id: str
    report_name: str
    action: str  # retire, merge, migrate, keep
    reason: str
    priority: int  # 1=highest
    estimated_savings_hours: float = 0.0


def propose_canonical_dataset(
    cluster_reports: list[dict],
    cluster_measures: list[dict],
    cluster_name: str,
) -> CanonicalDatasetProposal:
    """Propose a canonical dataset for a cluster of related reports.

    Strategy:
    1. Union all fields to form the superset
    2. Identify shared dimensions (fields appearing in 50%+ of reports)
    3. Select canonical measures (most-used version of each)
    4. Determine grain from most common granularity
    5. Compute gap analysis per report
    """
    all_fields: Counter[str] = Counter()
    report_field_sets: list[set[str]] = []

    for r in cluster_reports:
        fields = extract_field_set(r)
        report_field_sets.append(fields)
        for f in fields:
            all_fields[f] += 1

    n_reports = len(cluster_reports)
    if n_reports == 0:
        return CanonicalDatasetProposal(name=cluster_name, description="Empty cluster")

    # Shared dimensions: fields in 50%+ of reports
    threshold = max(1, n_reports // 2)
    dimensions = sorted([f for f, count in all_fields.items() if count >= threshold])

    # Canonical measures: group by normalized name, pick most common expression
    measure_groups: dict[str, list[dict]] = {}
    for m in cluster_measures:
        norm = normalize_name(m.get("name", ""))
        if norm not in measure_groups:
            measure_groups[norm] = []
        measure_groups[norm].append(m)

    canonical_measures = []
    for norm_name, group in measure_groups.items():
        # Pick the expression with the highest usage
        best = max(group, key=lambda m: m.get("access_count", 0))
        canonical_measures.append(
            {
                "name": best.get("name", norm_name),
                "expression": best.get("expression", ""),
                "data_type": best.get("data_type", ""),
                "source_count": len(group),
            }
        )

    # Determine grain (heuristic: look for common grain-indicating fields)
    grain_indicators = ["date", "day", "month", "year", "week", "quarter"]
    grain_fields = [
        f for f in dimensions if any(g in f.lower() for g in grain_indicators)
    ]
    grain = ", ".join(grain_fields[:3]) if grain_fields else None

    # Gap analysis per report
    canonical_field_set = set(dimensions) | {normalize_name(m["name"]) for m in canonical_measures}
    gap_analyses = []
    for i, r in enumerate(cluster_reports):
        report_fields = report_field_sets[i] if i < len(report_field_sets) else set()
        missing = sorted(canonical_field_set - report_fields)
        extra = sorted(report_fields - canonical_field_set)
        common = canonical_field_set & report_fields
        compat = len(common) / len(canonical_field_set) if canonical_field_set else 1.0

        gap_analyses.append(
            {
                "report_id": r.get("id", ""),
                "report_name": r.get("name", ""),
                "missing_fields": missing,
                "extra_fields": extra,
                "compatibility_score": round(compat, 3),
            }
        )

    return CanonicalDatasetProposal(
        name=f"Canonical - {cluster_name}",
        description=f"Canonical dataset derived from {n_reports} related reports in cluster '{cluster_name}'",
        grain=grain,
        dimensions=dimensions,
        measures=canonical_measures,
        source_reports=[{"id": r.get("id"), "name": r.get("name")} for r in cluster_reports],
        gap_analyses=gap_analyses,
    )


def generate_rationalization_actions(
    reports: list[dict],
    exact_duplicate_groups: list[list[int]],
    near_duplicate_groups: list[list[int]],
    family_groups: list[list[int]],
) -> list[RationalizationAction]:
    """Generate rationalization action for each report.

    Logic:
    - Exact duplicates (non-primary): retire
    - Near duplicates (non-primary): merge
    - Family members not in dup groups: migrate to canonical
    - Others: keep
    """
    actions: dict[int, RationalizationAction] = {}
    MAINTENANCE_HOURS_PER_REPORT = 4.0  # avg quarterly hours

    # Mark exact duplicate non-primaries for retirement
    for group in exact_duplicate_groups:
        # Primary = highest access count
        primary_idx = max(group, key=lambda i: reports[i].get("access_count", 0))
        for idx in group:
            if idx == primary_idx:
                continue
            actions[idx] = RationalizationAction(
                report_id=reports[idx].get("id", ""),
                report_name=reports[idx].get("name", ""),
                action="retire",
                reason="Exact duplicate of a more frequently used report",
                priority=1,
                estimated_savings_hours=MAINTENANCE_HOURS_PER_REPORT,
            )

    # Mark near-duplicate non-primaries for merge
    for group in near_duplicate_groups:
        primary_idx = max(group, key=lambda i: reports[i].get("access_count", 0))
        for idx in group:
            if idx in actions or idx == primary_idx:
                continue
            actions[idx] = RationalizationAction(
                report_id=reports[idx].get("id", ""),
                report_name=reports[idx].get("name", ""),
                action="merge",
                reason="Near-duplicate; should be merged into canonical version",
                priority=2,
                estimated_savings_hours=MAINTENANCE_HOURS_PER_REPORT * 0.75,
            )

    # Mark family members for migration
    for group in family_groups:
        for idx in group:
            if idx not in actions:
                actions[idx] = RationalizationAction(
                    report_id=reports[idx].get("id", ""),
                    report_name=reports[idx].get("name", ""),
                    action="migrate",
                    reason="Part of a report family; should adopt canonical dataset",
                    priority=3,
                    estimated_savings_hours=MAINTENANCE_HOURS_PER_REPORT * 0.25,
                )

    # Everything else: keep
    for i, r in enumerate(reports):
        if i not in actions:
            actions[i] = RationalizationAction(
                report_id=r.get("id", ""),
                report_name=r.get("name", ""),
                action="keep",
                reason="Unique report; retain as-is",
                priority=4,
                estimated_savings_hours=0,
            )

    return sorted(actions.values(), key=lambda a: a.priority)
