import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import async_session
from app.engine.canonicalizer import (
    generate_rationalization_actions,
    propose_canonical_dataset,
)
from app.engine.clustering import (
    find_exact_duplicates,
    find_near_duplicates,
    find_report_families,
    select_primary_report,
)
from app.engine.kpi_detector import detect_kpi_conflicts
from app.engine.similarity import build_similarity_matrix
from app.models.canonical import CanonicalDataset, CanonicalGapAnalysis, KPIConflict
from app.models.cluster import ReportCluster, ReportClusterMembership
from app.models.dataset import Dataset
from app.models.measure import Measure
from app.models.report import Report

logger = logging.getLogger(__name__)


async def run_analysis(project_id: uuid.UUID, status_tracker: dict | None = None) -> None:
    """Run the full analysis pipeline for a project.

    Steps:
    1. Load all reports and measures
    2. Compute similarity matrix
    3. Find exact duplicates
    4. Find near duplicates
    5. Find report families
    6. Detect KPI conflicts
    7. Generate rationalization actions
    8. (Optional) Run AI analysis for ambiguous cases
    """

    def update_status(progress: float, step: str):
        if status_tracker and str(project_id) in status_tracker:
            status_tracker[str(project_id)].progress = progress
            status_tracker[str(project_id)].current_step = step

    async with async_session() as db:
        try:
            update_status(0.05, "Loading reports and measures")

            # Load reports
            result = await db.execute(
                select(Report)
                .where(Report.project_id == project_id)
                .options(selectinload(Report.measures))
            )
            reports = result.scalars().all()

            if not reports:
                update_status(1.0, "No reports to analyze")
                if status_tracker and str(project_id) in status_tracker:
                    status_tracker[str(project_id)].status = "completed"
                return

            # Build report dicts for engine
            report_dicts = []
            for r in reports:
                report_dicts.append(
                    {
                        "id": str(r.id),
                        "name": r.name,
                        "path": r.path,
                        "report_type": r.report_type,
                        "fields_used": r.fields_used or [],
                        "content_hash": r.content_hash,
                        "access_count": r.access_count,
                        "raw_metadata": r.raw_metadata or {},
                        "measures": [
                            {
                                "name": m.name,
                                "expression": m.expression,
                                "data_type": m.data_type,
                            }
                            for m in r.measures
                        ],
                    }
                )

            # Clear existing clusters for this project
            update_status(0.1, "Clearing previous analysis results")
            existing_clusters = await db.execute(
                select(ReportCluster).where(ReportCluster.project_id == project_id)
            )
            for cluster in existing_clusters.scalars().all():
                await db.delete(cluster)
            await db.flush()

            # Step 1: Compute similarity matrix
            update_status(0.2, "Computing similarity matrix")
            sim_matrix = build_similarity_matrix(report_dicts)

            # Step 2: Find exact duplicates
            update_status(0.35, "Finding exact duplicates")
            content_hashes = [r.get("content_hash") for r in report_dicts]
            exact_groups = find_exact_duplicates(
                [r["id"] for r in report_dicts], content_hashes
            )

            for i, group in enumerate(exact_groups):
                primary_idx = select_primary_report(
                    group, [r.get("access_count", 0) for r in report_dicts]
                )
                cluster = ReportCluster(
                    project_id=project_id,
                    name=f"Exact Duplicate Group {i + 1}",
                    cluster_type="exact_duplicate",
                    similarity_score=1.0,
                )
                db.add(cluster)
                await db.flush()

                for idx in group:
                    role = "primary" if idx == primary_idx else "duplicate"
                    membership = ReportClusterMembership(
                        cluster_id=cluster.id,
                        report_id=uuid.UUID(report_dicts[idx]["id"]),
                        role=role,
                    )
                    db.add(membership)

            # Step 3: Find near duplicates
            update_status(0.5, "Finding near duplicates")
            near_groups = find_near_duplicates(sim_matrix, threshold=0.75)

            for i, group in enumerate(near_groups):
                # Skip if already covered by exact duplicates
                if any(
                    set(group).issubset(set(eg)) for eg in exact_groups
                ):
                    continue

                primary_idx = select_primary_report(
                    group, [r.get("access_count", 0) for r in report_dicts]
                )
                avg_sim = sum(
                    sim_matrix[a][b] for a in group for b in group if a != b
                ) / max(1, len(group) * (len(group) - 1))

                cluster = ReportCluster(
                    project_id=project_id,
                    name=f"Near Duplicate Group {i + 1}",
                    cluster_type="near_duplicate",
                    similarity_score=round(float(avg_sim), 3),
                )
                db.add(cluster)
                await db.flush()

                for idx in group:
                    role = "primary" if idx == primary_idx else "related"
                    membership = ReportClusterMembership(
                        cluster_id=cluster.id,
                        report_id=uuid.UUID(report_dicts[idx]["id"]),
                        role=role,
                    )
                    db.add(membership)

            # Step 4: Find report families
            update_status(0.65, "Finding report families")
            family_groups = find_report_families(sim_matrix)

            for i, group in enumerate(family_groups):
                primary_idx = select_primary_report(
                    group, [r.get("access_count", 0) for r in report_dicts]
                )
                avg_sim = sum(
                    sim_matrix[a][b] for a in group for b in group if a != b
                ) / max(1, len(group) * (len(group) - 1))

                cluster = ReportCluster(
                    project_id=project_id,
                    name=f"Report Family {i + 1}",
                    cluster_type="family",
                    similarity_score=round(float(avg_sim), 3),
                )
                db.add(cluster)
                await db.flush()

                for idx in group:
                    role = "primary" if idx == primary_idx else "related"
                    membership = ReportClusterMembership(
                        cluster_id=cluster.id,
                        report_id=uuid.UUID(report_dicts[idx]["id"]),
                        role=role,
                    )
                    db.add(membership)

            # Step 5: Detect KPI conflicts
            update_status(0.8, "Detecting KPI conflicts")

            # Load all measures across the project
            all_measures_result = await db.execute(
                select(Measure)
                .join(Dataset, Measure.dataset_id == Dataset.id, isouter=True)
                .join(Report, Measure.report_id == Report.id, isouter=True)
                .where(
                    (Report.project_id == project_id) | (Dataset.project_id == project_id)
                )
            )
            all_measures = all_measures_result.scalars().all()

            measure_dicts = [
                {
                    "name": m.name,
                    "expression": m.expression,
                    "dataset_name": "",
                    "report_name": "",
                    "access_count": 0,
                }
                for m in all_measures
            ]

            # Clear existing KPI conflicts
            existing_conflicts = await db.execute(
                select(KPIConflict).where(KPIConflict.project_id == project_id)
            )
            for conflict in existing_conflicts.scalars().all():
                await db.delete(conflict)
            await db.flush()

            conflicts = detect_kpi_conflicts(measure_dicts)
            for c in conflicts:
                kpi_conflict = KPIConflict(
                    project_id=project_id,
                    measure_name=c.measure_name,
                    conflicting_measures=c.conflicting_definitions,
                    severity=c.severity,
                    status="open",
                )
                db.add(kpi_conflict)

            # Step 6: Generate rationalization actions
            update_status(0.9, "Generating rationalization actions")
            actions = generate_rationalization_actions(
                report_dicts, exact_groups, near_groups, family_groups
            )

            for action in actions:
                try:
                    report_uuid = uuid.UUID(action.report_id)
                    report = await db.get(Report, report_uuid)
                    if report:
                        report.rationalization_action = action.action
                        report.rationalization_score = action.estimated_savings_hours
                except (ValueError, Exception):
                    pass

            await db.commit()

            update_status(1.0, "Analysis complete")
            if status_tracker and str(project_id) in status_tracker:
                status_tracker[str(project_id)].status = "completed"

            logger.info(
                f"Analysis complete for project {project_id}: "
                f"{len(exact_groups)} exact dup groups, "
                f"{len(near_groups)} near dup groups, "
                f"{len(family_groups)} families, "
                f"{len(conflicts)} KPI conflicts"
            )

        except Exception as e:
            logger.error(f"Analysis failed for project {project_id}: {e}")
            if status_tracker and str(project_id) in status_tracker:
                status_tracker[str(project_id)].status = "error"
                status_tracker[str(project_id)].error = str(e)


async def run_canonicalization(project_id: uuid.UUID) -> None:
    """Generate canonical dataset recommendations for all clusters."""
    async with async_session() as db:
        try:
            # Load clusters with members
            result = await db.execute(
                select(ReportCluster)
                .where(ReportCluster.project_id == project_id)
                .options(
                    selectinload(ReportCluster.memberships).selectinload(
                        ReportClusterMembership.report
                    )
                )
            )
            clusters = result.scalars().all()

            # Clear existing canonical datasets
            existing = await db.execute(
                select(CanonicalDataset).where(CanonicalDataset.project_id == project_id)
            )
            for cd in existing.scalars().all():
                await db.delete(cd)
            await db.flush()

            for cluster in clusters:
                if len(cluster.memberships) < 2:
                    continue

                # Build report and measure dicts
                cluster_reports = []
                cluster_measures = []
                for membership in cluster.memberships:
                    r = membership.report
                    cluster_reports.append(
                        {
                            "id": str(r.id),
                            "name": r.name,
                            "fields_used": r.fields_used or [],
                            "raw_metadata": r.raw_metadata or {},
                            "access_count": r.access_count,
                        }
                    )

                    # Load measures for this report
                    measures_result = await db.execute(
                        select(Measure).where(Measure.report_id == r.id)
                    )
                    for m in measures_result.scalars().all():
                        cluster_measures.append(
                            {
                                "name": m.name,
                                "expression": m.expression,
                                "data_type": m.data_type,
                                "access_count": r.access_count,
                            }
                        )

                proposal = propose_canonical_dataset(
                    cluster_reports, cluster_measures, cluster.name
                )

                canonical = CanonicalDataset(
                    project_id=project_id,
                    cluster_id=cluster.id,
                    name=proposal.name,
                    description=proposal.description,
                    grain=proposal.grain,
                    dimensions=proposal.dimensions,
                    measures_def=proposal.measures,
                    status="proposed",
                )
                db.add(canonical)
                await db.flush()

                # Store gap analyses
                for gap in proposal.gap_analyses:
                    try:
                        report_uuid = uuid.UUID(gap["report_id"])
                        ga = CanonicalGapAnalysis(
                            canonical_id=canonical.id,
                            report_id=report_uuid,
                            missing_fields=gap["missing_fields"],
                            extra_fields=gap["extra_fields"],
                            compatibility_score=gap["compatibility_score"],
                        )
                        db.add(ga)
                    except (ValueError, KeyError):
                        pass

            await db.commit()
            logger.info(f"Canonicalization complete for project {project_id}")

        except Exception as e:
            logger.error(f"Canonicalization failed for project {project_id}: {e}")
