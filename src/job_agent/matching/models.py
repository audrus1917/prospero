"""Define validated semantic matching results."""

from pydantic import BaseModel, ConfigDict, Field


class MatchResult(BaseModel):
    """Validated semantic matching output supplied by an LLM provider."""

    model_config = ConfigDict(extra="forbid")

    technical_score: int = Field(ge=0, le=100)
    seniority_score: int = Field(ge=0, le=100)
    domain_score: int = Field(ge=0, le=100)
    strengths: list[str]
    gaps: list[str]
    missing_keywords: list[str]
    explanation: str = Field(min_length=1, max_length=4000)


class DocumentMatchResult(MatchResult):
    """Validated comparison of a resume document with a vacancy document."""

    recommendations: list[str]
