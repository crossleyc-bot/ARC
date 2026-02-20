import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.report import MeasureResponse


class DatasetResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    connection_id: uuid.UUID
    platform: str
    external_id: str
    name: str
    description: str | None
    tables: list | None
    relationships_meta: list | None
    refresh_schedule: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetDetailResponse(DatasetResponse):
    measures: list[MeasureResponse] = []


class PaginatedDatasetsResponse(BaseModel):
    items: list[DatasetResponse]
    total: int
    page: int
    page_size: int
