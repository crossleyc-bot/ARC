import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import BaseConnector, NormalizedDataset, NormalizedMeasure, NormalizedReport
from app.connectors.cognos import CognosConnector
from app.connectors.powerbi import PowerBIConnector
from app.database import async_session
from app.engine.normalizer import compute_content_hash, normalize_name
from app.models.connection import Connection
from app.models.dataset import Dataset
from app.models.measure import Measure
from app.models.report import Report

logger = logging.getLogger(__name__)


def get_connector(connection: Connection) -> BaseConnector:
    """Factory function to get the appropriate connector."""
    if connection.platform == "powerbi":
        return PowerBIConnector(connection.config)
    elif connection.platform == "cognos":
        return CognosConnector(connection.config)
    else:
        raise ValueError(f"Unknown platform: {connection.platform}")


async def run_harvest(connection_id: uuid.UUID) -> None:
    """Run the full harvest pipeline for a connection.

    This runs as a background task:
    1. Authenticate with the BI platform
    2. Extract reports, datasets, measures
    3. Normalize and store in DB
    4. Update connection status
    """
    async with async_session() as db:
        try:
            connection = await db.get(Connection, connection_id)
            if not connection:
                logger.error(f"Connection {connection_id} not found")
                return

            logger.info(f"Starting harvest for connection {connection.name} ({connection.platform})")

            connector = get_connector(connection)

            try:
                reports, datasets, measures = await connector.extract_all()
            finally:
                if hasattr(connector, "close"):
                    await connector.close()

            # Store reports
            await _store_reports(db, connection, reports)

            # Store datasets
            dataset_map = await _store_datasets(db, connection, datasets)

            # Store measures
            await _store_measures(db, connection, measures, dataset_map)

            # Update connection status
            connection.status = "synced"
            connection.last_sync = datetime.now(timezone.utc)
            connection.sync_error = None
            await db.commit()

            logger.info(
                f"Harvest complete: {len(reports)} reports, "
                f"{len(datasets)} datasets, {len(measures)} measures"
            )

        except Exception as e:
            logger.error(f"Harvest failed for connection {connection_id}: {e}")
            try:
                connection = await db.get(Connection, connection_id)
                if connection:
                    connection.status = "error"
                    connection.sync_error = str(e)[:1000]
                    await db.commit()
            except Exception:
                pass


async def _store_reports(
    db: AsyncSession, connection: Connection, reports: list[NormalizedReport]
) -> dict[str, uuid.UUID]:
    """Store normalized reports in DB. Returns mapping of external_id -> db id."""
    report_map = {}
    for r in reports:
        # Check if report already exists (upsert by external_id + connection)
        existing = await db.execute(
            select(Report).where(
                Report.connection_id == connection.id,
                Report.external_id == r.external_id,
            )
        )
        report = existing.scalar_one_or_none()

        content_hash = compute_content_hash(
            {
                "name": r.name,
                "fields_used": r.fields_used,
                "report_type": r.report_type,
                "raw_metadata": r.raw_metadata,
            }
        )

        if report:
            report.name = r.name
            report.path = r.path
            report.report_type = r.report_type
            report.owner = r.owner
            report.access_count = r.access_count
            report.raw_metadata = r.raw_metadata
            report.content_hash = content_hash
            report.fields_used = r.fields_used
        else:
            report = Report(
                project_id=connection.project_id,
                connection_id=connection.id,
                platform=connection.platform,
                external_id=r.external_id,
                name=r.name,
                path=r.path,
                report_type=r.report_type,
                owner=r.owner,
                access_count=r.access_count,
                raw_metadata=r.raw_metadata,
                content_hash=content_hash,
                fields_used=r.fields_used,
            )
            db.add(report)

        await db.flush()
        report_map[r.external_id] = report.id

    await db.commit()
    return report_map


async def _store_datasets(
    db: AsyncSession, connection: Connection, datasets: list[NormalizedDataset]
) -> dict[str, uuid.UUID]:
    """Store normalized datasets in DB. Returns mapping of external_id -> db id."""
    dataset_map = {}
    for ds in datasets:
        existing = await db.execute(
            select(Dataset).where(
                Dataset.connection_id == connection.id,
                Dataset.external_id == ds.external_id,
            )
        )
        dataset = existing.scalar_one_or_none()

        if dataset:
            dataset.name = ds.name
            dataset.description = ds.description
            dataset.tables = ds.tables
            dataset.relationships_meta = ds.relationships
            dataset.refresh_schedule = ds.refresh_schedule
            dataset.raw_metadata = ds.raw_metadata
        else:
            dataset = Dataset(
                project_id=connection.project_id,
                connection_id=connection.id,
                platform=connection.platform,
                external_id=ds.external_id,
                name=ds.name,
                description=ds.description,
                tables=ds.tables,
                relationships_meta=ds.relationships,
                refresh_schedule=ds.refresh_schedule,
                raw_metadata=ds.raw_metadata,
            )
            db.add(dataset)

        await db.flush()
        dataset_map[ds.external_id] = dataset.id

    await db.commit()
    return dataset_map


async def _store_measures(
    db: AsyncSession,
    connection: Connection,
    measures: list[NormalizedMeasure],
    dataset_map: dict[str, uuid.UUID],
) -> None:
    """Store normalized measures in DB."""
    for m in measures:
        dataset_id = dataset_map.get(m.dataset_external_id) if m.dataset_external_id else None

        measure = Measure(
            dataset_id=dataset_id,
            name=m.name,
            expression=m.expression,
            data_type=m.data_type,
            description=m.description,
            is_kpi=m.is_kpi,
            normalized_name=normalize_name(m.name),
        )
        db.add(measure)

    await db.commit()
