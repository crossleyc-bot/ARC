import uuid
from datetime import datetime

from pydantic import BaseModel


class ConnectionCreate(BaseModel):
    platform: str  # 'powerbi' or 'cognos'
    name: str
    config: dict = {}


class ConnectionUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None


class ConnectionResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    platform: str
    name: str
    status: str
    last_sync: datetime | None
    sync_error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncStatusResponse(BaseModel):
    connection_id: uuid.UUID
    status: str
    last_sync: datetime | None
    sync_error: str | None
    report_count: int = 0
    dataset_count: int = 0
