import uuid
from datetime import datetime

from pydantic import BaseModel


class AnalysisTriggerResponse(BaseModel):
    project_id: uuid.UUID
    status: str
    message: str


class AnalysisStatusResponse(BaseModel):
    project_id: uuid.UUID
    status: str  # pending, running, completed, error
    progress: float  # 0.0 - 1.0
    current_step: str | None
    error: str | None


class ClusterResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    cluster_type: str
    similarity_score: float | None
    member_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ClusterDetailResponse(ClusterResponse):
    members: list["ClusterMemberResponse"] = []
    metadata: dict | None


class ClusterMemberResponse(BaseModel):
    report_id: uuid.UUID
    report_name: str
    role: str
    platform: str

    model_config = {"from_attributes": True}


class KPIConflictResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    measure_name: str
    conflicting_measures: list | None
    severity: str
    resolution: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SimilarityMatrixResponse(BaseModel):
    report_ids: list[uuid.UUID]
    report_names: list[str]
    matrix: list[list[float]]


class DashboardResponse(BaseModel):
    total_reports: int
    total_datasets: int
    total_measures: int
    duplicate_clusters: int
    near_duplicate_clusters: int
    family_clusters: int
    kpi_conflicts_open: int
    kpi_conflicts_resolved: int
    canonical_datasets_proposed: int
    canonical_datasets_certified: int
    reports_to_retire: int
    reports_to_merge: int
    reports_to_migrate: int
    reports_to_keep: int
    estimated_reduction_pct: float
    platform_breakdown: dict
