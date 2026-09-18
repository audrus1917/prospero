"""Define and load the structured candidate profile."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    """A factual employment period used as matching evidence."""

    company: str
    role: str
    period: str
    highlights: list[str]
    skills: list[str]


class LanguageLevel(BaseModel):
    """A language and its explicitly stated proficiency."""

    language: str
    level: str


class CandidateProfile(BaseModel):
    """Structured candidate facts used for filtering and matching."""

    headline: str | None = None
    summary: str | None = None
    commercial_experience_years: int | None = Field(default=None, ge=0)
    target_roles: list[str]
    primary_skills: list[str]
    secondary_skills: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    languages: list[LanguageLevel] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    current_location: str | None = None
    work_formats: list[str] = Field(default_factory=list)
    excluded_titles: list[str] = Field(default_factory=list)
    excluded_technologies: list[str] = Field(default_factory=list)
    allowed_locations: list[str] = Field(default_factory=list)
    remote_required: bool = False
    minimum_salary: int | None = None
    salary_currency: str = "RUB"


def load_candidate_profile(path: Path) -> CandidateProfile:
    """Load and validate a candidate profile YAML file."""
    with path.open(encoding="utf-8") as profile_file:
        contents = yaml.safe_load(profile_file)
    return CandidateProfile.model_validate(contents)
