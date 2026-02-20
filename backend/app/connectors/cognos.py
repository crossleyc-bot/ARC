import logging

import httpx

from app.connectors.base import (
    BaseConnector,
    NormalizedDataset,
    NormalizedMeasure,
    NormalizedReport,
)

logger = logging.getLogger(__name__)


class CognosConnector(BaseConnector):
    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get("base_url", "").rstrip("/")
        self.namespace = config.get("namespace", "")
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self._client: httpx.AsyncClient | None = None

    async def authenticate(self) -> None:
        """Authenticate via Cognos session API."""
        self._client = httpx.AsyncClient(timeout=60.0)
        auth_url = f"{self.base_url}/api/v1/session"
        payload = {
            "parameters": [
                {"name": "CAMNamespace", "value": self.namespace},
                {"name": "CAMUsername", "value": self.username},
                {"name": "CAMPassword", "value": self.password},
            ]
        }
        resp = await self._client.put(
            auth_url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        # Session cookie is automatically stored in the client

    async def _get(self, path: str, params: dict | None = None) -> dict:
        if not self._client:
            raise RuntimeError("Not authenticated")
        resp = await self._client.get(
            f"{self.base_url}{path}",
            params=params,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    async def _get_content_recursive(
        self, parent_id: str | None = None, path_prefix: str = ""
    ) -> list[dict]:
        """Recursively walk the Cognos content tree."""
        items = []
        endpoint = "/api/v1/content"
        if parent_id:
            endpoint = f"/api/v1/content/{parent_id}/items"

        try:
            data = await self._get(endpoint)
            for item in data.get("content", []):
                item_type = item.get("type", "")
                item_path = f"{path_prefix}/{item.get('defaultName', '')}"

                if item_type in ("report", "reportView", "query", "analysis"):
                    items.append({**item, "_path": item_path})
                elif item_type == "folder":
                    children = await self._get_content_recursive(item.get("id"), item_path)
                    items.extend(children)
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to get content for {parent_id}: {e}")

        return items

    async def extract_reports(self) -> list[NormalizedReport]:
        raw_items = await self._get_content_recursive()
        reports = []

        for item in raw_items:
            reports.append(
                NormalizedReport(
                    external_id=item.get("id", ""),
                    name=item.get("defaultName", ""),
                    path=item.get("_path", ""),
                    report_type=item.get("type", "report"),
                    owner=item.get("owner", {}).get("defaultName", "")
                    if isinstance(item.get("owner"), dict)
                    else "",
                    last_modified=item.get("modificationTime"),
                    fields_used=[],
                    raw_metadata={
                        "type": item.get("type"),
                        "package_id": item.get("metadataModelPackage", {}).get("id", "")
                        if isinstance(item.get("metadataModelPackage"), dict)
                        else "",
                        "creation_time": item.get("creationTime"),
                    },
                )
            )

        return reports

    async def extract_datasets(self) -> list[NormalizedDataset]:
        datasets = []
        try:
            data = await self._get("/api/v1/datasources")
            for ds in data.get("dataSources", data.get("datasources", [])):
                datasets.append(
                    NormalizedDataset(
                        external_id=ds.get("id", ""),
                        name=ds.get("defaultName", ds.get("name", "")),
                        description=ds.get("description", ""),
                        tables=[],
                        raw_metadata={
                            "type": ds.get("type", ""),
                            "connection_string": ds.get("connectionString", ""),
                            "gateway": ds.get("gateway", ""),
                        },
                    )
                )
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to get datasources: {e}")

        # Also try to get packages/data modules
        try:
            content = await self._get_content_recursive()
            for item in content:
                if item.get("type") in ("package", "dataModule"):
                    datasets.append(
                        NormalizedDataset(
                            external_id=item.get("id", ""),
                            name=item.get("defaultName", ""),
                            description="",
                            tables=[],
                            raw_metadata={
                                "type": item.get("type", ""),
                                "path": item.get("_path", ""),
                            },
                        )
                    )
        except Exception as e:
            logger.warning(f"Failed to get packages: {e}")

        return datasets

    async def extract_measures(self) -> list[NormalizedMeasure]:
        # Cognos measures are embedded within reports and packages
        # Full extraction requires parsing report specifications
        # For now, return measures found in data module metadata
        measures = []
        try:
            content = await self._get_content_recursive()
            for item in content:
                if item.get("type") == "dataModule":
                    module_id = item.get("id", "")
                    try:
                        detail = await self._get(f"/api/v1/content/{module_id}")
                        for calc in detail.get("calculations", []):
                            measures.append(
                                NormalizedMeasure(
                                    name=calc.get("name", ""),
                                    expression=calc.get("expression", ""),
                                    data_type=calc.get("dataType", ""),
                                    description=calc.get("description", ""),
                                    is_kpi="kpi" in calc.get("name", "").lower(),
                                    dataset_external_id=module_id,
                                )
                            )
                    except httpx.HTTPStatusError:
                        pass
        except Exception as e:
            logger.warning(f"Failed to extract measures: {e}")

        return measures

    async def close(self):
        if self._client:
            # End session
            try:
                await self._client.delete(f"{self.base_url}/api/v1/session")
            except Exception:
                pass
            await self._client.aclose()
