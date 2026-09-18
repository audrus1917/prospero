"""Discover local PDF files and safely extract their text."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_PDF_SIZE = 20 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 120_000


class PDFDocumentError(ValueError):
    """Raised when a local PDF cannot be read safely."""


@dataclass(frozen=True, slots=True)
class PDFDocument:
    """Filesystem metadata for a discovered PDF document."""

    name: str
    size: int
    modified_at: datetime


def list_pdf_documents(directory: Path) -> list[PDFDocument]:
    """List regular PDF files without traversing nested directories."""
    if not directory.is_dir():
        return []
    documents = [
        PDFDocument(
            name=path.name,
            size=path.stat().st_size,
            modified_at=datetime.fromtimestamp(path.stat().st_mtime, UTC),
        )
        for path in directory.iterdir()
        if path.is_file() and path.suffix.casefold() == ".pdf"
    ]
    return sorted(documents, key=lambda document: document.name.casefold())


def extract_pdf_text(directory: Path, filename: str) -> str:
    """Extract bounded text from one PDF inside an allowed directory."""
    if Path(filename).name != filename or Path(filename).suffix.casefold() != ".pdf":
        raise PDFDocumentError("Invalid PDF filename")
    allowed_directory = directory.resolve()
    path = (directory / filename).resolve()
    if path.parent != allowed_directory or not path.is_file():
        raise PDFDocumentError(f"PDF file does not exist: {filename}")
    if path.stat().st_size > MAX_PDF_SIZE:
        raise PDFDocumentError(f"PDF file is larger than 20 MB: {filename}")
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise PDFDocumentError(f"Encrypted PDF is not supported: {filename}")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except (OSError, PdfReadError) as exc:
        raise PDFDocumentError(f"Cannot read PDF file: {filename}") from exc
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not normalized:
        raise PDFDocumentError(
            f"PDF contains no extractable text (OCR may be required): {filename}"
        )
    return normalized[:MAX_EXTRACTED_CHARACTERS]
