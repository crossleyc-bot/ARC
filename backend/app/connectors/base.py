from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class NormalizedReport:
    external_id: str
    name: str
    path: str | None = None
    report_type: str | None = None
    owner: str | None = None
    last_modified: str | None = None
    access_count: int = 0
    fields_used: list[str] = field(default_factory=list)
    raw_metadata: dict = field(default_factory=dict)


@dataclass
class NormalizedDataset:
    external_id: str
    name: str
    description: str | None = None
    tables: list[dict] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    refresh_schedule: str | None = None
    raw_metadata: dict = field(default_factory=dict)


@dataclass
class NormalizedMeasure:
    name: str
    expression: str | None = None
    data_type: str | None = None
    description: str | None = None
    is_kpi: bool = False
    dataset_external_id: str | None = None
    report_external_id: str | None = None


class BaseConnector(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def authenticate(self) -> None:
        """Authenticate with the BI platform."""

    @abstractmethod
    async def extract_reports(self) -> list[NormalizedReport]:
        """Extract and normalize all reports."""

    @abstractmethod
    async def extract_datasets(self) -> list[NormalizedDataset]:
        """Extract and normalize all datasets/packages."""

    @abstractmethod
    async def extract_measures(self) -> list[NormalizedMeasure]:
        """Extract and normalize all measures/calculations."""

    async def extract_all(
        self,
    ) -> tuple[list[NormalizedReport], list[NormalizedDataset], list[NormalizedMeasure]]:
        """Run full extraction pipeline."""
        await self.authenticate()
        reports = await self.extract_reports()
        datasets = await self.extract_datasets()
        measures = await self.extract_measures()
        return reports, datasets, measures
