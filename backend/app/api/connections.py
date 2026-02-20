import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.connection import Connection
from app.models.dataset import Dataset
from app.models.project import Project
from app.models.report import Report
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionUpdate,
    SyncStatusResponse,
)
from app.services.harvest import run_harvest

router = APIRouter()


@router.post("/projects/{project_id}/connections", response_model=ConnectionResponse, status_code=201)
async def create_connection(
    project_id: uuid.UUID, data: ConnectionCreate, db: AsyncSession = Depends(get_db)
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if data.platform not in ("powerbi", "cognos"):
        raise HTTPException(status_code=400, detail="Platform must be 'powerbi' or 'cognos'")

    connection = Connection(
        project_id=project_id,
        platform=data.platform,
        name=data.name,
        config=data.config,
    )
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    return connection


@router.get("/projects/{project_id}/connections", response_model=list[ConnectionResponse])
async def list_connections(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Connection)
        .where(Connection.project_id == project_id)
        .order_by(Connection.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(connection_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    connection = await db.get(Connection, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: uuid.UUID, data: ConnectionUpdate, db: AsyncSession = Depends(get_db)
):
    connection = await db.get(Connection, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    if data.name is not None:
        connection.name = data.name
    if data.config is not None:
        connection.config = data.config

    await db.commit()
    await db.refresh(connection)
    return connection


@router.delete("/{connection_id}", status_code=204)
async def delete_connection(connection_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    connection = await db.get(Connection, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    await db.delete(connection)
    await db.commit()


@router.post("/{connection_id}/sync", response_model=SyncStatusResponse)
async def sync_connection(
    connection_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    connection = await db.get(Connection, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    if connection.status == "syncing":
        raise HTTPException(status_code=409, detail="Sync already in progress")

    connection.status = "syncing"
    connection.sync_error = None
    await db.commit()

    background_tasks.add_task(run_harvest, connection_id)

    return SyncStatusResponse(
        connection_id=connection.id,
        status="syncing",
        last_sync=connection.last_sync,
        sync_error=None,
    )


@router.get("/{connection_id}/sync-status", response_model=SyncStatusResponse)
async def get_sync_status(connection_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    connection = await db.get(Connection, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    report_count = await db.scalar(
        select(func.count(Report.id)).where(Report.connection_id == connection_id)
    )
    dataset_count = await db.scalar(
        select(func.count(Dataset.id)).where(Dataset.connection_id == connection_id)
    )

    return SyncStatusResponse(
        connection_id=connection.id,
        status=connection.status,
        last_sync=connection.last_sync,
        sync_error=connection.sync_error,
        report_count=report_count or 0,
        dataset_count=dataset_count or 0,
    )
