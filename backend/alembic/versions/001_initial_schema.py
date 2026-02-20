"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-02-20

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Projects
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Connections
    op.create_table(
        "connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("config", postgresql.JSON, nullable=False),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_error", sa.String(1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Reports
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "connection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(500), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("path", sa.Text, nullable=True),
        sa.Column("report_type", sa.String(100), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_accessed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_count", sa.Integer, server_default="0"),
        sa.Column("raw_metadata", postgresql.JSON, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("fields_used", postgresql.JSON, nullable=True),
        sa.Column("rationalization_action", sa.String(50), nullable=True),
        sa.Column("rationalization_score", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Datasets
    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "connection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(500), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("tables", postgresql.JSON, nullable=True),
        sa.Column("relationships_meta", postgresql.JSON, nullable=True),
        sa.Column("refresh_schedule", sa.String(255), nullable=True),
        sa.Column("raw_metadata", postgresql.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Measures
    op.create_table(
        "measures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("datasets.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("expression", sa.Text, nullable=True),
        sa.Column("data_type", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_kpi", sa.Boolean, server_default="false"),
        sa.Column("normalized_name", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Report Clusters
    op.create_table(
        "report_clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("cluster_type", sa.String(50), nullable=False),
        sa.Column("similarity_score", sa.Float, nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Cluster Memberships
    op.create_table(
        "report_cluster_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "cluster_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("report_clusters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50), server_default="related"),
    )

    # Canonical Datasets
    op.create_table(
        "canonical_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cluster_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("report_clusters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("grain", sa.String(500), nullable=True),
        sa.Column("dimensions", postgresql.JSON, nullable=True),
        sa.Column("measures_def", postgresql.JSON, nullable=True),
        sa.Column("status", sa.String(50), server_default="proposed"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Canonical Gap Analyses
    op.create_table(
        "canonical_gap_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "canonical_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canonical_datasets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("missing_fields", postgresql.JSON, nullable=True),
        sa.Column("extra_fields", postgresql.JSON, nullable=True),
        sa.Column("compatibility_score", sa.Float, nullable=True),
    )

    # KPI Conflicts
    op.create_table(
        "kpi_conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("measure_name", sa.String(500), nullable=False),
        sa.Column("conflicting_measures", postgresql.JSON, nullable=True),
        sa.Column("severity", sa.String(50), server_default="warning"),
        sa.Column("resolution", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), server_default="open"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Indexes for common queries
    op.create_index("ix_reports_project_id", "reports", ["project_id"])
    op.create_index("ix_reports_connection_id", "reports", ["connection_id"])
    op.create_index("ix_reports_content_hash", "reports", ["content_hash"])
    op.create_index("ix_reports_platform", "reports", ["platform"])
    op.create_index("ix_datasets_project_id", "datasets", ["project_id"])
    op.create_index("ix_measures_dataset_id", "measures", ["dataset_id"])
    op.create_index("ix_measures_report_id", "measures", ["report_id"])
    op.create_index("ix_measures_normalized_name", "measures", ["normalized_name"])
    op.create_index("ix_clusters_project_id", "report_clusters", ["project_id"])
    op.create_index("ix_clusters_type", "report_clusters", ["cluster_type"])
    op.create_index(
        "ix_cluster_memberships_cluster_id",
        "report_cluster_memberships",
        ["cluster_id"],
    )
    op.create_index(
        "ix_cluster_memberships_report_id",
        "report_cluster_memberships",
        ["report_id"],
    )
    op.create_index(
        "ix_canonical_datasets_project_id", "canonical_datasets", ["project_id"]
    )
    op.create_index("ix_kpi_conflicts_project_id", "kpi_conflicts", ["project_id"])
    op.create_index("ix_kpi_conflicts_status", "kpi_conflicts", ["status"])


def downgrade() -> None:
    op.drop_table("kpi_conflicts")
    op.drop_table("canonical_gap_analyses")
    op.drop_table("canonical_datasets")
    op.drop_table("report_cluster_memberships")
    op.drop_table("report_clusters")
    op.drop_table("measures")
    op.drop_table("datasets")
    op.drop_table("reports")
    op.drop_table("connections")
    op.drop_table("projects")
