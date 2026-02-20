import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CanonicalDataset(Base):
    __tablename__ = "canonical_datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("report_clusters.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    grain: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dimensions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    measures_def: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="proposed"
    )  # proposed, approved, certified
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project = relationship("Project", back_populates="canonical_datasets")
    cluster = relationship("ReportCluster", back_populates="canonical_dataset")
    gap_analyses = relationship(
        "CanonicalGapAnalysis", back_populates="canonical_dataset", cascade="all, delete-orphan"
    )


class CanonicalGapAnalysis(Base):
    __tablename__ = "canonical_gap_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_datasets.id", ondelete="CASCADE"), nullable=False
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    missing_fields: Mapped[list | None] = mapped_column(JSON, nullable=True)
    extra_fields: Mapped[list | None] = mapped_column(JSON, nullable=True)
    compatibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    canonical_dataset = relationship("CanonicalDataset", back_populates="gap_analyses")
    report = relationship("Report", back_populates="gap_analyses")


class KPIConflict(Base):
    __tablename__ = "kpi_conflicts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    measure_name: Mapped[str] = mapped_column(String(500), nullable=False)
    conflicting_measures: Mapped[list | None] = mapped_column(JSON, nullable=True)
    severity: Mapped[str] = mapped_column(String(50), default="warning")  # critical, warning, info
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")  # open, resolved
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="kpi_conflicts")
