import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.canonical import KPIConflict
from app.models.cluster import ReportCluster, ReportClusterMembership
from app.models.project import Project
from app.models.report import Report
from app.schemas.analysis import (
    AnalysisStatusResponse,
    AnalysisTriggerResponse,
    ClusterDetailResponse,
    ClusterMemberResponse,
    ClusterResponse,
    DashboardResponse,
    KPIConflictResponse,
    SimilarityMatrixResponse,
)
from app.services.analyze import run_analysis

router = APIRouter()

# In-memory analysis status tracking (in production, use Redis or DB)
_analysis_status: dict[str, AnalysisStatusResponse] = {}


@router.post("/projects/{project_id}/analyze", response_model=AnalysisTriggerResponse)
async def trigger_analysis(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    report_count = await db.scalar(
        select(func.count(Report.id)).where(Report.project_id == project_id)
    )
    if not report_count:
        raise HTTPException(status_code=400, detail="No reports to analyze. Run a sync first.")

    _analysis_status[str(project_id)] = AnalysisStatusResponse(
        project_id=project_id,
        status="running",
        progress=0.0,
        current_step="Initializing",
        error=None,
    )

    background_tasks.add_task(run_analysis, project_id, _analysis_status)

    return AnalysisTriggerResponse(
        project_id=project_id,
        status="running",
        message="Analysis started",
    )


@router.get("/projects/{project_id}/analysis/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(project_id: uuid.UUID):
    status = _analysis_status.get(str(project_id))
    if not status:
        return AnalysisStatusResponse(
            project_id=project_id,
            status="idle",
            progress=0.0,
            current_step=None,
            error=None,
        )
    return status


@router.get("/projects/{project_id}/clusters", response_model=list[ClusterResponse])
async def list_clusters(
    project_id: uuid.UUID,
    cluster_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ReportCluster)
        .where(ReportCluster.project_id == project_id)
        .options(selectinload(ReportCluster.memberships))
    )
    if cluster_type:
        query = query.where(ReportCluster.cluster_type == cluster_type)

    query = query.order_by(ReportCluster.created_at.desc())
    result = await db.execute(query)
    clusters = result.scalars().all()

    return [
        ClusterResponse(
            id=c.id,
            project_id=c.project_id,
            name=c.name,
            cluster_type=c.cluster_type,
            similarity_score=c.similarity_score,
            member_count=len(c.memberships),
            created_at=c.created_at,
        )
        for c in clusters
    ]


@router.get("/clusters/{cluster_id}", response_model=ClusterDetailResponse)
async def get_cluster(cluster_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ReportCluster)
        .where(ReportCluster.id == cluster_id)
        .options(
            selectinload(ReportCluster.memberships).selectinload(ReportClusterMembership.report)
        )
    )
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    members = [
        ClusterMemberResponse(
            report_id=m.report.id,
            report_name=m.report.name,
            role=m.role,
            platform=m.report.platform,
        )
        for m in cluster.memberships
    ]

    return ClusterDetailResponse(
        id=cluster.id,
        project_id=cluster.project_id,
        name=cluster.name,
        cluster_type=cluster.cluster_type,
        similarity_score=cluster.similarity_score,
        member_count=len(members),
        created_at=cluster.created_at,
        members=members,
        metadata=cluster.metadata,
    )


@router.get("/projects/{project_id}/kpi-conflicts", response_model=list[KPIConflictResponse])
async def list_kpi_conflicts(
    project_id: uuid.UUID,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(KPIConflict).where(KPIConflict.project_id == project_id)
    if status:
        query = query.where(KPIConflict.status == status)
    query = query.order_by(KPIConflict.severity.desc(), KPIConflict.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/kpi-conflicts/{conflict_id}", response_model=KPIConflictResponse)
async def update_kpi_conflict(
    conflict_id: uuid.UUID,
    resolution: str,
    status: str = "resolved",
    db: AsyncSession = Depends(get_db),
):
    conflict = await db.get(KPIConflict, conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="KPI conflict not found")
    conflict.resolution = resolution
    conflict.status = status
    await db.commit()
    await db.refresh(conflict)
    return conflict


@router.get("/projects/{project_id}/similarity-matrix", response_model=SimilarityMatrixResponse)
async def get_similarity_matrix(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report)
        .where(Report.project_id == project_id)
        .order_by(Report.name.asc())
    )
    reports = result.scalars().all()

    if not reports:
        return SimilarityMatrixResponse(report_ids=[], report_names=[], matrix=[])

    # Return identity matrix as placeholder; real matrix is computed by analysis engine
    n = len(reports)
    matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    return SimilarityMatrixResponse(
        report_ids=[r.id for r in reports],
        report_names=[r.name for r in reports],
        matrix=matrix,
    )


@router.get("/projects/{project_id}/dashboard", response_model=DashboardResponse)
async def get_dashboard(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from app.models.canonical import CanonicalDataset
    from app.models.dataset import Dataset
    from app.models.measure import Measure

    total_reports = await db.scalar(
        select(func.count(Report.id)).where(Report.project_id == project_id)
    ) or 0
    total_datasets = await db.scalar(
        select(func.count(Dataset.id)).where(Dataset.project_id == project_id)
    ) or 0
    total_measures = await db.scalar(
        select(func.count(Measure.id))
        .join(Report, Measure.report_id == Report.id, isouter=True)
        .join(Dataset, Measure.dataset_id == Dataset.id, isouter=True)
        .where((Report.project_id == project_id) | (Dataset.project_id == project_id))
    ) or 0

    dup_clusters = await db.scalar(
        select(func.count(ReportCluster.id)).where(
            ReportCluster.project_id == project_id,
            ReportCluster.cluster_type == "exact_duplicate",
        )
    ) or 0
    near_dup_clusters = await db.scalar(
        select(func.count(ReportCluster.id)).where(
            ReportCluster.project_id == project_id,
            ReportCluster.cluster_type == "near_duplicate",
        )
    ) or 0
    family_clusters = await db.scalar(
        select(func.count(ReportCluster.id)).where(
            ReportCluster.project_id == project_id,
            ReportCluster.cluster_type == "family",
        )
    ) or 0

    kpi_open = await db.scalar(
        select(func.count(KPIConflict.id)).where(
            KPIConflict.project_id == project_id, KPIConflict.status == "open"
        )
    ) or 0
    kpi_resolved = await db.scalar(
        select(func.count(KPIConflict.id)).where(
            KPIConflict.project_id == project_id, KPIConflict.status == "resolved"
        )
    ) or 0

    canonical_proposed = await db.scalar(
        select(func.count(CanonicalDataset.id)).where(
            CanonicalDataset.project_id == project_id, CanonicalDataset.status == "proposed"
        )
    ) or 0
    canonical_certified = await db.scalar(
        select(func.count(CanonicalDataset.id)).where(
            CanonicalDataset.project_id == project_id, CanonicalDataset.status == "certified"
        )
    ) or 0

    retire = await db.scalar(
        select(func.count(Report.id)).where(
            Report.project_id == project_id, Report.rationalization_action == "retire"
        )
    ) or 0
    merge = await db.scalar(
        select(func.count(Report.id)).where(
            Report.project_id == project_id, Report.rationalization_action == "merge"
        )
    ) or 0
    migrate = await db.scalar(
        select(func.count(Report.id)).where(
            Report.project_id == project_id, Report.rationalization_action == "migrate"
        )
    ) or 0
    keep = await db.scalar(
        select(func.count(Report.id)).where(
            Report.project_id == project_id, Report.rationalization_action == "keep"
        )
    ) or 0

    reduction_pct = ((retire + merge) / total_reports * 100) if total_reports > 0 else 0.0

    # Platform breakdown
    pbi_count = await db.scalar(
        select(func.count(Report.id)).where(
            Report.project_id == project_id, Report.platform == "powerbi"
        )
    ) or 0
    cognos_count = await db.scalar(
        select(func.count(Report.id)).where(
            Report.project_id == project_id, Report.platform == "cognos"
        )
    ) or 0

    return DashboardResponse(
        total_reports=total_reports,
        total_datasets=total_datasets,
        total_measures=total_measures,
        duplicate_clusters=dup_clusters,
        near_duplicate_clusters=near_dup_clusters,
        family_clusters=family_clusters,
        kpi_conflicts_open=kpi_open,
        kpi_conflicts_resolved=kpi_resolved,
        canonical_datasets_proposed=canonical_proposed,
        canonical_datasets_certified=canonical_certified,
        reports_to_retire=retire,
        reports_to_merge=merge,
        reports_to_migrate=migrate,
        reports_to_keep=keep,
        estimated_reduction_pct=round(reduction_pct, 1),
        platform_breakdown={"powerbi": pbi_count, "cognos": cognos_count},
    )
