"""Define validated semantic matching results."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    cover_letter: list[Annotated[str, Field(min_length=1, max_length=500)]] = Field(
        min_length=10, max_length=12
    )

    @field_validator("cover_letter")
    @classmethod
    def validate_cover_letter(cls, lines: list[str]) -> list[str]:
        """Ensure each item represents one non-empty line of the letter."""
        normalized = [line.strip() for line in lines]
        if any(not line or "\n" in line or "\r" in line for line in normalized):
            raise ValueError("cover letter must contain non-empty single lines")
        return normalized
