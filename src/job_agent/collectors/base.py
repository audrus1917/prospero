"""Define source vacancy data and the collector interface."""

from typing import Protocol

from pydantic import BaseModel, Field


class SourceVacancy(BaseModel):
    """Source-level vacancy data awaiting normalization."""

    external_id: str
    source: str
    payload: dict[str, object] = Field(default_factory=dict)


class CollectorError(RuntimeError):
    """Raised when a vacancy source cannot be read reliably."""


class VacancyCollector(Protocol):
    """Structural interface implemented by external collectors."""

    async def collect(
        self, query: str, *, page: int = 0, per_page: int = 20
    ) -> list[SourceVacancy]:
        """Collect one page of source vacancies."""
