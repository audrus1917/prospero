"""Discover and read supported local resume and vacancy documents."""

from datetime import UTC, datetime
from pathlib import Path

from job_agent.documents.base import DocumentError, LocalDocument
from job_agent.documents.pdf import extract_pdf_text

MAX_DOCUMENT_SIZE = 20 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 120_000
SUPPORTED_DOCUMENT_SUFFIXES = frozenset({".pdf", ".md", ".markdown"})


def list_documents(directory: Path) -> list[LocalDocument]:
    """List supported regular files without traversing nested directories."""
    if not directory.is_dir():
        return []
    documents: list[LocalDocument] = []
    for path in directory.iterdir():
        if not path.is_file() or path.suffix.casefold() not in SUPPORTED_DOCUMENT_SUFFIXES:
            continue
        stat = path.stat()
        documents.append(
            LocalDocument(
                name=path.name,
                size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, UTC),
            )
        )
    return sorted(documents, key=lambda document: document.name.casefold())


def extract_document_text(directory: Path, filename: str) -> str:
    """Extract bounded text from a supported file inside an allowed directory."""
    suffix = Path(filename).suffix.casefold()
    if Path(filename).name != filename or suffix not in SUPPORTED_DOCUMENT_SUFFIXES:
        raise DocumentError("Invalid document filename")
    if suffix == ".pdf":
        return extract_pdf_text(directory, filename)

    allowed_directory = directory.resolve()
    path = (directory / filename).resolve()
    if path.parent != allowed_directory or not path.is_file():
        raise DocumentError(f"Document file does not exist: {filename}")
    if path.stat().st_size > MAX_DOCUMENT_SIZE:
        raise DocumentError(f"Document file is larger than 20 MB: {filename}")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentError(f"Markdown file must be UTF-8 encoded: {filename}") from exc
    except OSError as exc:
        raise DocumentError(f"Cannot read Markdown file: {filename}") from exc
    if not text.strip():
        raise DocumentError(f"Markdown file is empty: {filename}")
    return text[:MAX_EXTRACTED_CHARACTERS]


def parser_version(filename: str) -> str:
    """Return the extractor version recorded for a supported document."""
    return "pypdf-1" if Path(filename).suffix.casefold() == ".pdf" else "markdown-1"
