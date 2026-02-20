import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.models.report import Report
from app.services.export import generate_excel_report, generate_json_export, generate_pdf_report

router = APIRouter()


@router.get("/projects/{project_id}/export/excel")
async def export_excel(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    report_count = await db.scalar(
        select(func.count(Report.id)).where(Report.project_id == project_id)
    )
    if not report_count:
        raise HTTPException(status_code=400, detail="No data to export")

    buffer = await generate_excel_report(project_id, db)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="ARC_{project.name}_Report.xlsx"'},
    )


@router.get("/projects/{project_id}/export/pdf")
async def export_pdf(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    report_count = await db.scalar(
        select(func.count(Report.id)).where(Report.project_id == project_id)
    )
    if not report_count:
        raise HTTPException(status_code=400, detail="No data to export")

    buffer = await generate_pdf_report(project_id, db)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="ARC_{project.name}_Executive_Summary.pdf"'
        },
    )


@router.get("/projects/{project_id}/export/json")
async def export_json(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    data = await generate_json_export(project_id, db)
    return data
