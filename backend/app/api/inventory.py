import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.dataset import Dataset
from app.models.measure import Measure
from app.models.report import Report
from app.schemas.dataset import DatasetDetailResponse, DatasetResponse, PaginatedDatasetsResponse
from app.schemas.report import (
    MeasureResponse,
    PaginatedReportsResponse,
    ReportDetailResponse,
    ReportResponse,
)

router = APIRouter()


@router.get("/projects/{project_id}/reports", response_model=PaginatedReportsResponse)
async def list_reports(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    platform: str | None = None,
    report_type: str | None = None,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    db: AsyncSession = Depends(get_db),
):
    query = select(Report).where(Report.project_id == project_id)

    if platform:
        query = query.where(Report.platform == platform)
    if report_type:
        query = query.where(Report.report_type == report_type)
    if search:
        query = query.where(Report.name.ilike(f"%{search}%"))

    sort_col = getattr(Report, sort_by, Report.name)
    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

    total = await db.scalar(
        select(func.count()).select_from(query.subquery())
    )

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)

    return PaginatedReportsResponse(
        items=result.scalars().all(),
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/reports/{report_id}", response_model=ReportDetailResponse)
async def get_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).where(Report.id == report_id).options(selectinload(Report.measures))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportDetailResponse(
        **{c.name: getattr(report, c.name) for c in Report.__table__.columns},
        measures=[MeasureResponse.model_validate(m) for m in report.measures],
    )


@router.get("/projects/{project_id}/datasets", response_model=PaginatedDatasetsResponse)
async def list_datasets(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    platform: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Dataset).where(Dataset.project_id == project_id)

    if platform:
        query = query.where(Dataset.platform == platform)
    if search:
        query = query.where(Dataset.name.ilike(f"%{search}%"))

    query = query.order_by(Dataset.name.asc())

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)

    return PaginatedDatasetsResponse(
        items=result.scalars().all(),
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/datasets/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(dataset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id).options(selectinload(Dataset.measures))
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return DatasetDetailResponse(
        **{c.name: getattr(dataset, c.name) for c in Dataset.__table__.columns},
        measures=[MeasureResponse.model_validate(m) for m in dataset.measures],
    )


@router.get("/projects/{project_id}/measures", response_model=list[MeasureResponse])
async def list_measures(
    project_id: uuid.UUID,
    is_kpi: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Measure)
        .join(Report, Measure.report_id == Report.id, isouter=True)
        .join(Dataset, Measure.dataset_id == Dataset.id, isouter=True)
        .where(
            (Report.project_id == project_id) | (Dataset.project_id == project_id)
        )
    )

    if is_kpi is not None:
        query = query.where(Measure.is_kpi == is_kpi)
    if search:
        query = query.where(Measure.name.ilike(f"%{search}%"))

    query = query.order_by(Measure.name.asc())
    result = await db.execute(query)
    return result.scalars().all()
