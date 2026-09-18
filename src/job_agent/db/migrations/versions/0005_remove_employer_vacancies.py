"""Remove employer-owned vacancy storage.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove data that belongs to the separate employer application."""
    op.drop_table("employervacancy")


def downgrade() -> None:
    """Restore the legacy table for migration rollback compatibility."""
    op.create_table(
        "employervacancy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id", name="uq_employer_vacancy_source_id"),
    )
    op.create_index("ix_employervacancy_source", "employervacancy", ["source"])
    op.create_index("ix_employervacancy_external_id", "employervacancy", ["external_id"])
    op.create_index("ix_employervacancy_title", "employervacancy", ["title"])
