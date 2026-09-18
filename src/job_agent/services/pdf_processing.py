"""Catalog, extract, and classify local PDF documents."""

from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session

from job_agent.documents.pdf import PDFDocumentError, extract_pdf_text, list_pdf_documents
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
    """Catalog, extract, and classify local PDFs with isolated failures."""

    parser_version = "pypdf-1"

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
        """Process pending local PDFs while isolating per-file failures.

        Returns:
            Aggregate counts for all discovered documents.
        """
        seen = processed = needs_ocr = failed = 0
        for kind, directory in self._paths.items():
            for document in list_pdf_documents(directory):
                record = self._repository.sync_file(kind, directory / document.name)
                seen += 1
                if record.processing_status != DocumentProcessingStatus.PENDING:
                    continue
                try:
                    text = extract_pdf_text(directory, document.name)
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
                        self.parser_version,
                        self._classifier.version,
                    )
                    processed += 1
                except PDFDocumentError as exc:
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
