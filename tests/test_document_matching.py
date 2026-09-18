import asyncio
from pathlib import Path

import pytest
from pypdf import PdfWriter

from job_agent.documents.pdf import PDFDocumentError, list_pdf_documents
from job_agent.matching.models import DocumentMatchResult
from job_agent.services.document_matching import DocumentBatchError, DocumentMatchingService


class StubDocumentProvider:
    async def analyze_documents(
        self, resume_text: str, vacancy_text: str
    ) -> DocumentMatchResult:
        del resume_text
        technical_score = 90 if "Python" in vacancy_text else 40
        return DocumentMatchResult(
            technical_score=technical_score,
            seniority_score=80,
            domain_score=70,
            strengths=["Explicit experience"],
            gaps=[],
            missing_keywords=[],
            recommendations=["Emphasize the relevant project"],
            explanation="Compared using explicit document facts.",
        )


def test_pdf_listing_is_local_and_sorted(tmp_path: Path) -> None:
    (tmp_path / "B.pdf").write_bytes(b"pdf")
    (tmp_path / "a.PDF").write_bytes(b"pdf")
    (tmp_path / "notes.txt").write_text("ignored")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "hidden.pdf").write_bytes(b"pdf")

    documents = list_pdf_documents(tmp_path)

    assert [document.name for document in documents] == ["a.PDF", "B.pdf"]


def test_pdf_path_traversal_is_rejected(tmp_path: Path) -> None:
    from job_agent.documents.pdf import extract_pdf_text

    with pytest.raises(PDFDocumentError, match="Invalid PDF filename"):
        extract_pdf_text(tmp_path, "../resume.pdf")


def test_image_only_pdf_requires_ocr(tmp_path: Path) -> None:
    from job_agent.documents.pdf import extract_pdf_text

    path = tmp_path / "scan.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with path.open("wb") as pdf_file:
        writer.write(pdf_file)

    with pytest.raises(PDFDocumentError, match="OCR may be required"):
        extract_pdf_text(tmp_path, path.name)


def test_document_matches_are_ranked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    resumes = tmp_path / "resumes"
    vacancies = tmp_path / "vacancies"
    resumes.mkdir()
    vacancies.mkdir()
    (resumes / "resume.pdf").write_bytes(b"pdf")
    (vacancies / "python.pdf").write_bytes(b"pdf")
    (vacancies / "other.pdf").write_bytes(b"pdf")

    texts = {
        "resume.pdf": "Senior Python developer",
        "python.pdf": "Python backend vacancy",
        "other.pdf": "Sales vacancy",
    }
    monkeypatch.setattr(
        "job_agent.services.document_matching.extract_pdf_text",
        lambda _directory, filename: texts[filename],
    )
    service = DocumentMatchingService(resumes, vacancies, StubDocumentProvider())

    matches = asyncio.run(service.analyze("resume.pdf"))

    assert [match.vacancy_file for match in matches] == ["python.pdf", "other.pdf"]
    assert matches[0].final_score == 85
    assert matches[1].final_score == 52


def test_empty_vacancy_directory_fails(tmp_path: Path) -> None:
    service = DocumentMatchingService(tmp_path, tmp_path / "missing", StubDocumentProvider())

    with pytest.raises(DocumentBatchError, match="No vacancy PDF"):
        asyncio.run(service.analyze("resume.pdf"))
