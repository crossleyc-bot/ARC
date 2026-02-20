import uuid
from datetime import datetime

from pydantic import BaseModel


class CanonicalDatasetResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    cluster_id: uuid.UUID | None
    name: str
    description: str | None
    grain: str | None
    dimensions: list | None
    measures_def: list | None
    status: str
    created_at: datetime
    updated_at: datetime
    gap_analysis_count: int = 0

    model_config = {"from_attributes": True}


class CanonicalDatasetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    grain: str | None = None
    dimensions: list | None = None
    measures_def: list | None = None


class GapAnalysisResponse(BaseModel):
    id: uuid.UUID
    canonical_id: uuid.UUID
    report_id: uuid.UUID
    report_name: str = ""
    missing_fields: list | None
    extra_fields: list | None
    compatibility_score: float | None

    model_config = {"from_attributes": True}


class CanonicalDetailResponse(CanonicalDatasetResponse):
    gap_analyses: list[GapAnalysisResponse] = []
    cluster_name: str | None = None


class CanonicalizeTriggerResponse(BaseModel):
    project_id: uuid.UUID
    status: str
    message: str
