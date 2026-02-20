import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReportCluster(Base):
    __tablename__ = "report_clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    cluster_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # exact_duplicate, near_duplicate, family
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="clusters")
    memberships = relationship(
        "ReportClusterMembership", back_populates="cluster", cascade="all, delete-orphan"
    )
    canonical_dataset = relationship(
        "CanonicalDataset", back_populates="cluster", uselist=False
    )


class ReportClusterMembership(Base):
    __tablename__ = "report_cluster_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("report_clusters.id", ondelete="CASCADE"), nullable=False
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(50), default="related"
    )  # primary, duplicate, related

    cluster = relationship("ReportCluster", back_populates="memberships")
    report = relationship("Report", back_populates="cluster_memberships")
