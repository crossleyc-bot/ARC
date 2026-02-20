import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.canonical import CanonicalDataset, CanonicalGapAnalysis
from app.models.cluster import ReportCluster
from app.models.project import Project
from app.models.report import Report
from app.schemas.canonical import (
    CanonicalDatasetResponse,
    CanonicalDatasetUpdate,
    CanonicalDetailResponse,
    CanonicalizeTriggerResponse,
    GapAnalysisResponse,
)
from app.services.analyze import run_canonicalization

router = APIRouter()


@router.post("/projects/{project_id}/canonicalize", response_model=CanonicalizeTriggerResponse)
async def trigger_canonicalization(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cluster_count = await db.scalar(
        select(func.count(ReportCluster.id)).where(ReportCluster.project_id == project_id)
    )
    if not cluster_count:
        raise HTTPException(status_code=400, detail="No clusters found. Run analysis first.")

    background_tasks.add_task(run_canonicalization, project_id)

    return CanonicalizeTriggerResponse(
        project_id=project_id,
        status="running",
        message="Canonicalization started",
    )


@router.get("/projects/{project_id}/canonical-datasets", response_model=list[CanonicalDatasetResponse])
async def list_canonical_datasets(
    project_id: uuid.UUID,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(CanonicalDataset)
        .where(CanonicalDataset.project_id == project_id)
        .options(selectinload(CanonicalDataset.gap_analyses))
    )
    if status:
        query = query.where(CanonicalDataset.status == status)
    query = query.order_by(CanonicalDataset.created_at.desc())
    result = await db.execute(query)
    datasets = result.scalars().all()

    return [
        CanonicalDatasetResponse(
            id=d.id,
            project_id=d.project_id,
            cluster_id=d.cluster_id,
            name=d.name,
            description=d.description,
            grain=d.grain,
            dimensions=d.dimensions,
            measures_def=d.measures_def,
            status=d.status,
            created_at=d.created_at,
            updated_at=d.updated_at,
            gap_analysis_count=len(d.gap_analyses),
        )
        for d in datasets
    ]


@router.get("/canonical-datasets/{canonical_id}", response_model=CanonicalDetailResponse)
async def get_canonical_dataset(canonical_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CanonicalDataset)
        .where(CanonicalDataset.id == canonical_id)
        .options(
            selectinload(CanonicalDataset.gap_analyses).selectinload(CanonicalGapAnalysis.report),
            selectinload(CanonicalDataset.cluster),
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Canonical dataset not found")

    gap_analyses = [
        GapAnalysisResponse(
            id=ga.id,
            canonical_id=ga.canonical_id,
            report_id=ga.report_id,
            report_name=ga.report.name if ga.report else "",
            missing_fields=ga.missing_fields,
            extra_fields=ga.extra_fields,
            compatibility_score=ga.compatibility_score,
        )
        for ga in dataset.gap_analyses
    ]

    return CanonicalDetailResponse(
        id=dataset.id,
        project_id=dataset.project_id,
        cluster_id=dataset.cluster_id,
        name=dataset.name,
        description=dataset.description,
        grain=dataset.grain,
        dimensions=dataset.dimensions,
        measures_def=dataset.measures_def,
        status=dataset.status,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        gap_analysis_count=len(gap_analyses),
        gap_analyses=gap_analyses,
        cluster_name=dataset.cluster.name if dataset.cluster else None,
    )


@router.put("/canonical-datasets/{canonical_id}", response_model=CanonicalDatasetResponse)
async def update_canonical_dataset(
    canonical_id: uuid.UUID,
    data: CanonicalDatasetUpdate,
    db: AsyncSession = Depends(get_db),
):
    dataset = await db.get(CanonicalDataset, canonical_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Canonical dataset not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dataset, field, value)

    await db.commit()
    await db.refresh(dataset)

    gap_count = await db.scalar(
        select(func.count(CanonicalGapAnalysis.id)).where(
            CanonicalGapAnalysis.canonical_id == canonical_id
        )
    )

    return CanonicalDatasetResponse(
        id=dataset.id,
        project_id=dataset.project_id,
        cluster_id=dataset.cluster_id,
        name=dataset.name,
        description=dataset.description,
        grain=dataset.grain,
        dimensions=dataset.dimensions,
        measures_def=dataset.measures_def,
        status=dataset.status,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        gap_analysis_count=gap_count or 0,
    )
