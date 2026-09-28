"""Catalog, extract, and classify local resume and vacancy documents."""

from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session

from job_agent.documents.base import DocumentError
from job_agent.documents.local import extract_document_text, list_documents, parser_version
from job_agent.matching.classification import DocumentClassifier
from job_agent.models.pdf_document import DocumentKind, DocumentProcessingStatus, PDFDocumentRecord
from job_agent.repositories.pdf_document import PDFDocumentRepository


@dataclass(frozen=True, slots=True)
class PDFProcessingSummary:
    """Counters produced by a local PDF processing run."""

    seen: int
    processed: int
    needs_ocr: int
    failed: int


class PDFProcessingService:
    """Catalog, extract, and classify local documents with isolated failures."""

    def __init__(
        self,
        session: Session,
        resumes_path: Path,
        vacancies_path: Path,
        classifier: DocumentClassifier,
    ) -> None:
        """Initialize the workflow with document roots and a classifier."""
        self._session = session
        self._paths = {DocumentKind.RESUME: resumes_path, DocumentKind.VACANCY: vacancies_path}
        self._classifier = classifier
        self._repository = PDFDocumentRepository(session)

    def list(self, kind: DocumentKind) -> list[PDFDocumentRecord]:
        """List catalog records for a document kind."""
        return self._repository.list_records(kind)

    def process(self) -> PDFProcessingSummary:
        """Process pending local documents while isolating per-file failures.

        Returns:
            Aggregate counts for all discovered documents.
        """
        seen = processed = needs_ocr = failed = 0
        for kind, directory in self._paths.items():
            for document in list_documents(directory):
                record = self._repository.sync_file(kind, directory / document.name)
                seen += 1
                if record.processing_status != DocumentProcessingStatus.PENDING:
                    continue
                try:
                    text = extract_document_text(directory, document.name)
                    categories = [
                        {
                            "slug": match.slug,
                            "name": match.name,
                            "confidence": match.confidence,
                            "evidence": match.evidence,
                        }
                        for match in self._classifier.classify(text)
                    ]
                    self._repository.mark_processed(
                        record,
                        text,
                        categories,
                        parser_version(document.name),
                        self._classifier.version,
                    )
                    processed += 1
                except DocumentError as exc:
                    status = (
                        DocumentProcessingStatus.NEEDS_OCR
                        if "OCR" in str(exc)
                        else DocumentProcessingStatus.FAILED
                    )
                    self._repository.mark_error(record, status, str(exc))
                    needs_ocr += status == DocumentProcessingStatus.NEEDS_OCR
                    failed += status == DocumentProcessingStatus.FAILED
        self._session.commit()
        return PDFProcessingSummary(seen, processed, needs_ocr, failed)
