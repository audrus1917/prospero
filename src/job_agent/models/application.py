"""Define application tracking persistence models."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, Enum, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class ApplicationStatus(StrEnum):
    """Supported stages of a vacancy application."""

    NEW = "new"
    SHORTLISTED = "shortlisted"
    APPLIED = "applied"
    HR = "hr"
    TECHNICAL = "technical"
    FINAL = "final"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(SQLModel, table=True):
    """A candidate's application state for one vacancy."""

    __table_args__ = (UniqueConstraint("vacancy_id", name="uq_application_vacancy_id"),)

    id: int | None = Field(default=None, primary_key=True)
    vacancy_id: int = Field(foreign_key="vacancy.id", index=True)
    status: ApplicationStatus = Field(
        default=ApplicationStatus.NEW,
        sa_column=Column(
            Enum(
                ApplicationStatus,
                values_callable=lambda status: [value.value for value in status],
            ),
            nullable=False,
            index=True,
        ),
    )
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
