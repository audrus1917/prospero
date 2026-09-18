"""Normalize HeadHunter vacancy payloads into domain models."""

import re
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from job_agent.collectors.base import SourceVacancy
from job_agent.models.vacancy import Vacancy

_HTML_TAG = re.compile(r"<[^>]+>")


class _NamedValue(BaseModel):
    """Parse HeadHunter objects represented by a display name."""

    name: str = ""


class _Salary(BaseModel):
    """Parse an optional HeadHunter salary range."""

    model_config = ConfigDict(populate_by_name=True)

    salary_from: Decimal | None = Field(default=None, alias="from")
    salary_to: Decimal | None = Field(default=None, alias="to")
    currency: str | None = None


class HHVacancyPayload(BaseModel):
    """Fields consumed from a HeadHunter vacancy response."""

    id: str
    name: str
    alternate_url: str
    description: str = ""
    employer: _NamedValue = Field(default_factory=_NamedValue)
    area: _NamedValue = Field(default_factory=_NamedValue)
    schedule: _NamedValue = Field(default_factory=_NamedValue)
    salary: _Salary | None = None
    published_at: datetime | None = None


def normalize_hh_vacancy(source: SourceVacancy) -> Vacancy:
    """Convert a HeadHunter response into the source-independent model."""
    payload = HHVacancyPayload.model_validate(source.payload)
    salary = payload.salary
    return Vacancy(
        external_id=source.external_id,
        source=source.source,
        company=payload.employer.name or "Unknown",
        title=payload.name,
        url=payload.alternate_url,
        description=_HTML_TAG.sub(" ", payload.description).strip(),
        location=payload.area.name or None,
        remote=payload.schedule.name.casefold() == "удаленная работа",
        salary_from=salary.salary_from if salary else None,
        salary_to=salary.salary_to if salary else None,
        salary_currency=salary.currency if salary else None,
        published_at=payload.published_at,
    )
