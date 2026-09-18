"""Create vacancy and vacancy analysis tables.

Revision ID: 0001
Revises:
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vacancy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("remote", sa.Boolean(), nullable=False),
        sa.Column("salary_from", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("salary_to", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("filtered_reason", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id", name="uq_vacancy_source_id"),
    )
    for column in ("external_id", "source", "company", "title", "remote", "published_at"):
        op.create_index(f"ix_vacancy_{column}", "vacancy", [column])
    op.create_table(
        "vacancyanalysis",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), nullable=False),
        sa.Column("technical_score", sa.Integer(), nullable=False),
        sa.Column("seniority_score", sa.Integer(), nullable=False),
        sa.Column("domain_score", sa.Integer(), nullable=False),
        sa.Column("location_score", sa.Integer(), nullable=False),
        sa.Column("salary_score", sa.Integer(), nullable=False),
        sa.Column("final_score", sa.Integer(), nullable=False),
        sa.Column("recommended", sa.Boolean(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("gaps", sa.JSON(), nullable=False),
        sa.Column("missing_keywords", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancy.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vacancy_id", name="uq_analysis_vacancy_id"),
    )
    for column in ("vacancy_id", "final_score", "recommended"):
        op.create_index(f"ix_vacancyanalysis_{column}", "vacancyanalysis", [column])


def downgrade() -> None:
    op.drop_table("vacancyanalysis")
    op.drop_table("vacancy")
