"""Create application tracking table.

Revision ID: 0002
Revises: 0001
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "application",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "new",
                "shortlisted",
                "applied",
                "hr",
                "technical",
                "final",
                "offer",
                "rejected",
                "withdrawn",
                name="applicationstatus",
            ),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancy.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vacancy_id", name="uq_application_vacancy_id"),
    )
    op.create_index("ix_application_vacancy_id", "application", ["vacancy_id"])
    op.create_index("ix_application_status", "application", ["status"])


def downgrade() -> None:
    op.drop_table("application")
    sa.Enum(name="applicationstatus").drop(op.get_bind(), checkfirst=True)
