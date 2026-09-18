"""Add persistent local PDF processing catalog.

Revision ID: 0003
Revises: 0002
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pdfdocument",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("processing_status", sa.String(length=16), nullable=False),
        sa.Column("processing_error", sa.String(length=255), nullable=True),
        sa.Column("processing_attempts", sa.Integer(), nullable=False),
        sa.Column("parser_version", sa.String(length=64), nullable=True),
        sa.Column("classifier_version", sa.String(length=64), nullable=True),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "filename", name="uq_pdfdocument_kind_file"),
    )
    op.create_index("ix_pdfdocument_kind", "pdfdocument", ["kind"])
    op.create_index("ix_pdfdocument_filename", "pdfdocument", ["filename"])
    op.create_index("ix_pdfdocument_processing_status", "pdfdocument", ["processing_status"])


def downgrade() -> None:
    op.drop_table("pdfdocument")
