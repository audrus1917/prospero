"""Define the persisted vacancy analysis model."""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class VacancyAnalysis(SQLModel, table=True):
    """Validated semantic analysis and deterministic score for a vacancy."""

    __table_args__ = (UniqueConstraint("vacancy_id", name="uq_analysis_vacancy_id"),)

    id: int | None = Field(default=None, primary_key=True)
    vacancy_id: int = Field(foreign_key="vacancy.id", index=True)
    technical_score: int
    seniority_score: int
    domain_score: int
    location_score: int
    salary_score: int
    final_score: int = Field(index=True)
    recommended: bool = Field(index=True)
    strengths: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    gaps: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    missing_keywords: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    explanation: str = Field(sa_column=Column(Text, nullable=False))
    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
