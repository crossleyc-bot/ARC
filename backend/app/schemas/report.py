import uuid
from datetime import datetime

from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    connection_id: uuid.UUID
    platform: str
    external_id: str
    name: str
    path: str | None
    report_type: str | None
    owner: str | None
    last_modified: datetime | None
    last_accessed: datetime | None
    access_count: int
    content_hash: str | None
    fields_used: list | None
    rationalization_action: str | None
    rationalization_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportDetailResponse(ReportResponse):
    measures: list["MeasureResponse"] = []
    cluster_names: list[str] = []


class MeasureResponse(BaseModel):
    id: uuid.UUID
    name: str
    expression: str | None
    data_type: str | None
    description: str | None
    is_kpi: bool
    normalized_name: str | None

    model_config = {"from_attributes": True}


class PaginatedReportsResponse(BaseModel):
    items: list[ReportResponse]
    total: int
    page: int
    page_size: int
