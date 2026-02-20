import logging

import httpx

from app.connectors.base import (
    BaseConnector,
    NormalizedDataset,
    NormalizedMeasure,
    NormalizedReport,
)

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://api.powerbi.com/v1.0/myorg"
AUTH_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


class PowerBIConnector(BaseConnector):
    def __init__(self, config: dict):
        super().__init__(config)
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self.tenant_id = config.get("tenant_id", "")
        self.workspace_ids = config.get("workspace_ids", [])
        self.access_token: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def authenticate(self) -> None:
        """Authenticate via Azure AD OAuth2 client credentials flow."""
        url = AUTH_URL.format(tenant_id=self.tenant_id)
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://analysis.windows.net/powerbi/api/.default",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            self.access_token = resp.json()["access_token"]

        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=60.0,
        )

    async def _get(self, path: str) -> dict:
        if not self._client:
            raise RuntimeError("Not authenticated")
        resp = await self._client.get(f"{GRAPH_API_BASE}{path}")
        resp.raise_for_status()
        return resp.json()

    async def _get_workspaces(self) -> list[dict]:
        """Get workspaces to scan. If specific IDs given, use those; otherwise get all."""
        if self.workspace_ids:
            workspaces = []
            for ws_id in self.workspace_ids:
                data = await self._get(f"/groups/{ws_id}")
                workspaces.append(data)
            return workspaces
        data = await self._get("/groups")
        return data.get("value", [])

    async def extract_reports(self) -> list[NormalizedReport]:
        reports = []
        workspaces = await self._get_workspaces()

        for ws in workspaces:
            ws_id = ws.get("id", ws.get("Id", ""))
            ws_name = ws.get("name", ws.get("Name", ""))
            try:
                data = await self._get(f"/groups/{ws_id}/reports")
                for r in data.get("value", []):
                    reports.append(
                        NormalizedReport(
                            external_id=r.get("id", ""),
                            name=r.get("name", ""),
                            path=f"/{ws_name}/{r.get('name', '')}",
                            report_type=r.get("reportType", "PowerBIReport"),
                            owner=r.get("createdBy", ""),
                            fields_used=[],
                            raw_metadata={
                                "workspace_id": ws_id,
                                "workspace_name": ws_name,
                                "dataset_id": r.get("datasetId", ""),
                                "web_url": r.get("webUrl", ""),
                                "embed_url": r.get("embedUrl", ""),
                            },
                        )
                    )
            except httpx.HTTPStatusError as e:
                logger.warning(f"Failed to get reports for workspace {ws_id}: {e}")

        return reports

    async def extract_datasets(self) -> list[NormalizedDataset]:
        datasets = []
        workspaces = await self._get_workspaces()

        for ws in workspaces:
            ws_id = ws.get("id", ws.get("Id", ""))
            try:
                data = await self._get(f"/groups/{ws_id}/datasets")
                for ds in data.get("value", []):
                    ds_id = ds.get("id", "")
                    tables = []
                    try:
                        tables_data = await self._get(
                            f"/groups/{ws_id}/datasets/{ds_id}/tables"
                        )
                        tables = [
                            {
                                "name": t.get("name", ""),
                                "columns": [
                                    {
                                        "name": c.get("name", ""),
                                        "dataType": c.get("dataType", ""),
                                    }
                                    for c in t.get("columns", [])
                                ],
                            }
                            for t in tables_data.get("value", [])
                        ]
                    except httpx.HTTPStatusError:
                        pass

                    datasets.append(
                        NormalizedDataset(
                            external_id=ds_id,
                            name=ds.get("name", ""),
                            description=ds.get("description", ""),
                            tables=tables,
                            refresh_schedule=ds.get("refreshSchedule", {}).get(
                                "frequency", None
                            )
                            if isinstance(ds.get("refreshSchedule"), dict)
                            else None,
                            raw_metadata={
                                "workspace_id": ws_id,
                                "configured_by": ds.get("configuredBy", ""),
                                "is_refreshable": ds.get("isRefreshable", False),
                            },
                        )
                    )
            except httpx.HTTPStatusError as e:
                logger.warning(f"Failed to get datasets for workspace {ws_id}: {e}")

        return datasets

    async def extract_measures(self) -> list[NormalizedMeasure]:
        measures = []
        workspaces = await self._get_workspaces()

        for ws in workspaces:
            ws_id = ws.get("id", ws.get("Id", ""))
            try:
                ds_data = await self._get(f"/groups/{ws_id}/datasets")
                for ds in ds_data.get("value", []):
                    ds_id = ds.get("id", "")
                    try:
                        m_data = await self._get(
                            f"/groups/{ws_id}/datasets/{ds_id}/measures"
                        )
                        for m in m_data.get("value", []):
                            measures.append(
                                NormalizedMeasure(
                                    name=m.get("name", ""),
                                    expression=m.get("expression", ""),
                                    data_type=m.get("dataType", ""),
                                    description=m.get("description", ""),
                                    is_kpi=m.get("isHidden", False) is False
                                    and "KPI" in m.get("name", "").upper(),
                                    dataset_external_id=ds_id,
                                )
                            )
                    except httpx.HTTPStatusError:
                        # Measures endpoint may not be available for all datasets
                        pass
            except httpx.HTTPStatusError as e:
                logger.warning(f"Failed to get measures for workspace {ws_id}: {e}")

        return measures

    async def close(self):
        if self._client:
            await self._client.aclose()
