"""Persist and query local PDF processing records."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, col, select

from job_agent.models.pdf_document import (
    DocumentKind,
    DocumentProcessingStatus,
    PDFDocumentRecord,
)


class PDFDocumentRepository:
    """Persistence operations for the local PDF processing catalog."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session."""
        self._session = session

    def sync_file(self, kind: DocumentKind, path: Path) -> PDFDocumentRecord:
        """Create or reset a catalog record when local file content changes.

        Args:
            kind: Semantic kind of the local PDF.
            path: Path to the PDF file.

        Returns:
            The flushed catalog record representing the current file.
        """
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        record = self._session.exec(
            select(PDFDocumentRecord).where(
                PDFDocumentRecord.kind == kind, PDFDocumentRecord.filename == path.name
            )
        ).first()
        now = datetime.now(UTC)
        if record is None:
            record = PDFDocumentRecord(
                kind=kind,
                filename=path.name,
                content_sha256=digest,
                file_size=path.stat().st_size,
            )
        elif record.content_sha256 != digest:
            record.content_sha256 = digest
            record.file_size = path.stat().st_size
            record.extracted_text = None
            record.processing_status = DocumentProcessingStatus.PENDING
            record.processing_error = None
            record.processing_attempts = 0
            record.categories = []
        record.updated_at = now
        self._session.add(record)
        self._session.flush()
        return record

    def pending(self, kind: DocumentKind | None = None) -> list[PDFDocumentRecord]:
        """List records waiting to be processed, optionally filtered by kind."""
        statement = select(PDFDocumentRecord).where(
            PDFDocumentRecord.processing_status == DocumentProcessingStatus.PENDING
        )
        if kind is not None:
            statement = statement.where(PDFDocumentRecord.kind == kind)
        return list(self._session.exec(statement).all())

    def list_records(self, kind: DocumentKind | None = None) -> list[PDFDocumentRecord]:
        """List catalog records, optionally filtered by document kind."""
        statement = select(PDFDocumentRecord).order_by(
            col(PDFDocumentRecord.kind), col(PDFDocumentRecord.filename)
        )
        if kind is not None:
            statement = statement.where(PDFDocumentRecord.kind == kind)
        return list(self._session.exec(statement).all())

    def mark_processed(
        self,
        record: PDFDocumentRecord,
        text: str,
        categories: list[dict[str, object]],
        parser_version: str,
        classifier_version: str,
    ) -> None:
        """Store successful extraction and classification results."""
        record.extracted_text = text
        record.categories = categories
        record.processing_status = DocumentProcessingStatus.PROCESSED
        record.processing_error = None
        record.parser_version = parser_version
        record.classifier_version = classifier_version
        record.updated_at = datetime.now(UTC)
        self._session.add(record)

    def mark_error(
        self,
        record: PDFDocumentRecord,
        status: DocumentProcessingStatus,
        error: str,
    ) -> None:
        """Record a failed processing attempt with a bounded error message."""
        record.processing_status = status
        record.processing_error = error[:255]
        record.processing_attempts += 1
        record.updated_at = datetime.now(UTC)
        self._session.add(record)
