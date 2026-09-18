"""Define the normalized vacancy persistence model."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class Vacancy(SQLModel, table=True):
    """A normalized vacancy independent of its external source."""

    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_vacancy_source_id"),)

    id: int | None = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, max_length=255)
    source: str = Field(index=True, max_length=50)
    company: str = Field(index=True, max_length=255)
    title: str = Field(index=True, max_length=255)
    url: str = Field(max_length=2048)
    description: str = Field(sa_column=Column(Text, nullable=False))
    location: str | None = Field(default=None, max_length=255)
    remote: bool = Field(default=False, index=True)
    salary_from: Decimal | None = Field(default=None, decimal_places=2, max_digits=14)
    salary_to: Decimal | None = Field(default=None, decimal_places=2, max_digits=14)
    salary_currency: str | None = Field(default=None, max_length=3)
    published_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    filtered_reason: str | None = Field(default=None, max_length=500)
