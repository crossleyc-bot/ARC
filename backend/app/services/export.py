import io
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.canonical import CanonicalDataset, CanonicalGapAnalysis, KPIConflict
from app.models.cluster import ReportCluster
from app.models.dataset import Dataset
from app.models.measure import Measure
from app.models.project import Project
from app.models.report import Report

logger = logging.getLogger(__name__)


async def generate_excel_report(project_id: uuid.UUID, db: AsyncSession) -> io.BytesIO:
    """Generate a comprehensive Excel workbook with all ARC analysis results."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()
    header_font = Font(bold=True, size=12)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font_white = Font(bold=True, size=11, color="FFFFFF")

    def write_header(ws, headers: list[str]):
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font_white
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

    # Sheet 1: Executive Summary
    ws_summary = wb.active
    ws_summary.title = "Executive Summary"
    ws_summary["A1"] = "ARC Analytics Rationalization Report"
    ws_summary["A1"].font = Font(bold=True, size=16)

    project = await db.get(Project, project_id)
    ws_summary["A3"] = f"Project: {project.name if project else 'N/A'}"
    ws_summary["A4"] = f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"

    total_reports = await db.scalar(
        select(func.count(Report.id)).where(Report.project_id == project_id)
    ) or 0
    retire_count = await db.scalar(
        select(func.count(Report.id)).where(
            Report.project_id == project_id, Report.rationalization_action == "retire"
        )
    ) or 0
    merge_count = await db.scalar(
        select(func.count(Report.id)).where(
            Report.project_id == project_id, Report.rationalization_action == "merge"
        )
    ) or 0

    ws_summary["A6"] = "Key Metrics"
    ws_summary["A6"].font = Font(bold=True, size=14)
    metrics = [
        ("Total Reports", total_reports),
        ("Reports to Retire", retire_count),
        ("Reports to Merge", merge_count),
        ("Estimated Reduction", f"{((retire_count + merge_count) / max(1, total_reports) * 100):.1f}%"),
    ]
    for i, (label, value) in enumerate(metrics):
        ws_summary.cell(row=7 + i, column=1, value=label).font = Font(bold=True)
        ws_summary.cell(row=7 + i, column=2, value=str(value))

    # Sheet 2: Report Inventory
    ws_inventory = wb.create_sheet("Report Inventory")
    write_header(
        ws_inventory,
        ["Name", "Platform", "Type", "Owner", "Path", "Access Count", "Action", "Content Hash"],
    )

    result = await db.execute(
        select(Report).where(Report.project_id == project_id).order_by(Report.name)
    )
    for row_idx, r in enumerate(result.scalars().all(), 2):
        ws_inventory.cell(row=row_idx, column=1, value=r.name)
        ws_inventory.cell(row=row_idx, column=2, value=r.platform)
        ws_inventory.cell(row=row_idx, column=3, value=r.report_type)
        ws_inventory.cell(row=row_idx, column=4, value=r.owner)
        ws_inventory.cell(row=row_idx, column=5, value=r.path)
        ws_inventory.cell(row=row_idx, column=6, value=r.access_count)
        ws_inventory.cell(row=row_idx, column=7, value=r.rationalization_action or "pending")
        ws_inventory.cell(row=row_idx, column=8, value=r.content_hash or "")

    # Sheet 3: Clusters
    ws_clusters = wb.create_sheet("Clusters")
    write_header(ws_clusters, ["Cluster Name", "Type", "Similarity Score", "Member Count"])

    cluster_result = await db.execute(
        select(ReportCluster)
        .where(ReportCluster.project_id == project_id)
        .options(selectinload(ReportCluster.memberships))
    )
    for row_idx, c in enumerate(cluster_result.scalars().all(), 2):
        ws_clusters.cell(row=row_idx, column=1, value=c.name)
        ws_clusters.cell(row=row_idx, column=2, value=c.cluster_type)
        ws_clusters.cell(row=row_idx, column=3, value=c.similarity_score)
        ws_clusters.cell(row=row_idx, column=4, value=len(c.memberships))

    # Sheet 4: KPI Conflicts
    ws_kpi = wb.create_sheet("KPI Conflicts")
    write_header(ws_kpi, ["Measure Name", "Severity", "Status", "Resolution", "Definitions"])

    kpi_result = await db.execute(
        select(KPIConflict).where(KPIConflict.project_id == project_id)
    )
    for row_idx, k in enumerate(kpi_result.scalars().all(), 2):
        ws_kpi.cell(row=row_idx, column=1, value=k.measure_name)
        ws_kpi.cell(row=row_idx, column=2, value=k.severity)
        ws_kpi.cell(row=row_idx, column=3, value=k.status)
        ws_kpi.cell(row=row_idx, column=4, value=k.resolution or "")
        ws_kpi.cell(row=row_idx, column=5, value=json.dumps(k.conflicting_measures or [])[:500])

    # Sheet 5: Canonical Datasets
    ws_canonical = wb.create_sheet("Canonical Datasets")
    write_header(ws_canonical, ["Name", "Status", "Grain", "Dimensions", "Measures"])

    cd_result = await db.execute(
        select(CanonicalDataset).where(CanonicalDataset.project_id == project_id)
    )
    for row_idx, cd in enumerate(cd_result.scalars().all(), 2):
        ws_canonical.cell(row=row_idx, column=1, value=cd.name)
        ws_canonical.cell(row=row_idx, column=2, value=cd.status)
        ws_canonical.cell(row=row_idx, column=3, value=cd.grain or "")
        ws_canonical.cell(row=row_idx, column=4, value=json.dumps(cd.dimensions or [])[:500])
        ws_canonical.cell(row=row_idx, column=5, value=json.dumps(cd.measures_def or [])[:500])

    # Sheet 6: Rationalization Roadmap
    ws_roadmap = wb.create_sheet("Roadmap")
    write_header(ws_roadmap, ["Report Name", "Action", "Priority", "Platform", "Est. Savings (hrs)"])

    roadmap_result = await db.execute(
        select(Report)
        .where(Report.project_id == project_id, Report.rationalization_action.isnot(None))
        .order_by(Report.rationalization_action, Report.name)
    )
    for row_idx, r in enumerate(roadmap_result.scalars().all(), 2):
        action = r.rationalization_action or ""
        priority_map = {"retire": 1, "merge": 2, "migrate": 3, "keep": 4}
        ws_roadmap.cell(row=row_idx, column=1, value=r.name)
        ws_roadmap.cell(row=row_idx, column=2, value=action)
        ws_roadmap.cell(row=row_idx, column=3, value=priority_map.get(action, 5))
        ws_roadmap.cell(row=row_idx, column=4, value=r.platform)
        ws_roadmap.cell(row=row_idx, column=5, value=r.rationalization_score or 0)

    # Auto-size columns (approximate)
    for ws in wb.worksheets:
        for col in ws.columns:
            max_length = 0
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 50)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


async def generate_pdf_report(project_id: uuid.UUID, db: AsyncSession) -> io.BytesIO:
    """Generate a PDF executive summary report."""
    project = await db.get(Project, project_id)
    project_name = project.name if project else "Unknown"

    total_reports = await db.scalar(
        select(func.count(Report.id)).where(Report.project_id == project_id)
    ) or 0
    total_datasets = await db.scalar(
        select(func.count(Dataset.id)).where(Dataset.project_id == project_id)
    ) or 0
    retire_count = await db.scalar(
        select(func.count(Report.id)).where(
            Report.project_id == project_id, Report.rationalization_action == "retire"
        )
    ) or 0
    merge_count = await db.scalar(
        select(func.count(Report.id)).where(
            Report.project_id == project_id, Report.rationalization_action == "merge"
        )
    ) or 0
    cluster_count = await db.scalar(
        select(func.count(ReportCluster.id)).where(ReportCluster.project_id == project_id)
    ) or 0
    kpi_count = await db.scalar(
        select(func.count(KPIConflict.id)).where(KPIConflict.project_id == project_id)
    ) or 0

    reduction_pct = ((retire_count + merge_count) / max(1, total_reports)) * 100

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica', Arial, sans-serif; margin: 40px; color: #333; }}
            h1 {{ color: #1a365d; border-bottom: 3px solid #4472C4; padding-bottom: 10px; }}
            h2 {{ color: #2d5aa0; margin-top: 30px; }}
            .metric-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
            .metric {{ background: #f0f4f8; padding: 20px; border-radius: 8px; text-align: center; }}
            .metric-value {{ font-size: 36px; font-weight: bold; color: #1a365d; }}
            .metric-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
            .highlight {{ background: #e6f3ff; padding: 15px; border-left: 4px solid #4472C4; margin: 15px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th {{ background: #4472C4; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 8px 10px; border-bottom: 1px solid #ddd; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <h1>ARC Executive Summary</h1>
        <p><strong>Project:</strong> {project_name}</p>
        <p><strong>Date:</strong> {datetime.now(timezone.utc).strftime('%B %d, %Y')}</p>

        <h2>Key Findings</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-value">{total_reports}</div>
                <div class="metric-label">Total Reports Analyzed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{total_datasets}</div>
                <div class="metric-label">Datasets Discovered</div>
            </div>
            <div class="metric">
                <div class="metric-value">{reduction_pct:.0f}%</div>
                <div class="metric-label">Estimated Report Reduction</div>
            </div>
            <div class="metric">
                <div class="metric-value">{cluster_count}</div>
                <div class="metric-label">Report Clusters Identified</div>
            </div>
        </div>

        <div class="highlight">
            <strong>Bottom Line:</strong> ARC analysis identified {retire_count} reports for retirement
            and {merge_count} reports for consolidation, representing a potential {reduction_pct:.0f}%
            reduction in report count and associated maintenance effort.
        </div>

        <h2>Rationalization Summary</h2>
        <table>
            <tr><th>Action</th><th>Count</th><th>Description</th></tr>
            <tr><td>Retire</td><td>{retire_count}</td><td>Exact duplicates to decommission</td></tr>
            <tr><td>Merge</td><td>{merge_count}</td><td>Near-duplicates to consolidate</td></tr>
            <tr><td>Migrate</td><td>{total_reports - retire_count - merge_count}</td><td>Unique reports to standardize</td></tr>
        </table>

        <h2>KPI Governance</h2>
        <p>{kpi_count} KPI definition conflicts were detected across the analytics environment.
        Resolving these conflicts is critical for establishing trusted, consistent reporting.</p>

        <h2>Recommendations</h2>
        <ol>
            <li><strong>Immediate:</strong> Retire {retire_count} identified exact duplicate reports</li>
            <li><strong>Short-term:</strong> Merge {merge_count} near-duplicate reports into canonical versions</li>
            <li><strong>Medium-term:</strong> Resolve {kpi_count} KPI conflicts and certify canonical definitions</li>
            <li><strong>Ongoing:</strong> Establish governance process for new report certification</li>
        </ol>

        <div class="footer">
            <p>Generated by ARC - Analytics Rationalization &amp; Canonicalization</p>
            <p>Intelligent Consolidation. Trusted Standardization. Measurable Impact.</p>
        </div>
    </body>
    </html>
    """

    try:
        from weasyprint import HTML

        buffer = io.BytesIO()
        HTML(string=html).write_pdf(buffer)
        buffer.seek(0)
        return buffer
    except ImportError:
        # Fallback: return HTML as bytes if weasyprint is not installed
        logger.warning("weasyprint not available, returning HTML instead of PDF")
        buffer = io.BytesIO(html.encode())
        buffer.seek(0)
        return buffer


async def generate_json_export(project_id: uuid.UUID, db: AsyncSession) -> dict:
    """Generate a comprehensive JSON export of all analysis data."""
    project = await db.get(Project, project_id)

    # Reports
    reports_result = await db.execute(
        select(Report).where(Report.project_id == project_id).order_by(Report.name)
    )
    reports = [
        {
            "id": str(r.id),
            "name": r.name,
            "platform": r.platform,
            "type": r.report_type,
            "owner": r.owner,
            "path": r.path,
            "access_count": r.access_count,
            "action": r.rationalization_action,
        }
        for r in reports_result.scalars().all()
    ]

    # Clusters
    clusters_result = await db.execute(
        select(ReportCluster)
        .where(ReportCluster.project_id == project_id)
        .options(selectinload(ReportCluster.memberships))
    )
    clusters = [
        {
            "id": str(c.id),
            "name": c.name,
            "type": c.cluster_type,
            "similarity_score": c.similarity_score,
            "member_count": len(c.memberships),
        }
        for c in clusters_result.scalars().all()
    ]

    # KPI Conflicts
    kpi_result = await db.execute(
        select(KPIConflict).where(KPIConflict.project_id == project_id)
    )
    kpi_conflicts = [
        {
            "id": str(k.id),
            "measure_name": k.measure_name,
            "severity": k.severity,
            "status": k.status,
            "definitions": k.conflicting_measures,
        }
        for k in kpi_result.scalars().all()
    ]

    # Canonical Datasets
    cd_result = await db.execute(
        select(CanonicalDataset).where(CanonicalDataset.project_id == project_id)
    )
    canonical = [
        {
            "id": str(cd.id),
            "name": cd.name,
            "status": cd.status,
            "grain": cd.grain,
            "dimensions": cd.dimensions,
            "measures": cd.measures_def,
        }
        for cd in cd_result.scalars().all()
    ]

    return {
        "project": {
            "id": str(project.id) if project else "",
            "name": project.name if project else "",
        },
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "reports": reports,
        "clusters": clusters,
        "kpi_conflicts": kpi_conflicts,
        "canonical_datasets": canonical,
    }
