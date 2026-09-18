"""Define local PDF catalog persistence models."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, DateTime, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class DocumentKind(StrEnum):
    """Kinds of local PDF documents handled by the catalog."""

    RESUME = "resume"
    VACANCY = "vacancy"


class DocumentProcessingStatus(StrEnum):
    """Retryable states of local PDF processing."""

    PENDING = "pending"
    PROCESSED = "processed"
    NEEDS_OCR = "needs_ocr"
    FAILED = "failed"


class PDFDocumentRecord(SQLModel, table=True):
    """Metadata and derived processing state for one local PDF."""

    __tablename__ = "pdfdocument"

    __table_args__ = (UniqueConstraint("kind", "filename", name="uq_pdfdocument_kind_file"),)

    id: int | None = Field(default=None, primary_key=True)
    kind: DocumentKind = Field(index=True, max_length=16)
    filename: str = Field(index=True, max_length=255)
    content_sha256: str = Field(max_length=64)
    file_size: int
    extracted_text: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    processing_status: DocumentProcessingStatus = Field(
        default=DocumentProcessingStatus.PENDING, index=True, max_length=16
    )
    processing_error: str | None = Field(default=None, max_length=255)
    processing_attempts: int = Field(default=0, ge=0)
    parser_version: str | None = Field(default=None, max_length=64)
    classifier_version: str | None = Field(default=None, max_length=64)
    categories: list[dict[str, object]] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
