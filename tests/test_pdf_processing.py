from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from job_agent.matching.classification import DocumentClassifier
from job_agent.models.pdf_document import DocumentKind, DocumentProcessingStatus, PDFDocumentRecord
from job_agent.services.pdf_processing import PDFProcessingService


def make_classifier(tmp_path: Path) -> DocumentClassifier:
    taxonomy = tmp_path / "categories.json"
    taxonomy.write_text(
        '{"categories":[{"slug":"python","name":"Python","keywords":["Python","FastAPI"]}],'
        '"skill_aliases":{"python":"Python","fastapi":"FastAPI"}}',
        encoding="utf-8",
    )
    return DocumentClassifier.from_file(taxonomy)


def test_processing_catalogs_and_classifies_documents(
    monkeypatch, tmp_path: Path
) -> None:
    resumes = tmp_path / "resumes"
    vacancies = tmp_path / "vacancies"
    resumes.mkdir()
    vacancies.mkdir()
    (resumes / "resume.pdf").write_bytes(b"resume")
    (vacancies / "vacancy.pdf").write_bytes(b"vacancy")

    monkeypatch.setattr(
        "job_agent.services.pdf_processing.extract_pdf_text",
        lambda _directory, filename: "Python FastAPI" if filename == "resume.pdf" else "Python",
    )
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        service = PDFProcessingService(
            session, resumes, vacancies, make_classifier(tmp_path)
        )
        summary = service.process()
        records = session.exec(select(PDFDocumentRecord)).all()

    assert summary.seen == 2
    assert summary.processed == 2
    assert all(record.processing_status is DocumentProcessingStatus.PROCESSED for record in records)
    resume_record = next(record for record in records if record.kind is DocumentKind.RESUME)
    assert resume_record.content_sha256
    assert resume_record.categories[0]["slug"] == "python"


def test_processing_keeps_ocr_failure_isolated(monkeypatch, tmp_path: Path) -> None:
    resumes = tmp_path / "resumes"
    vacancies = tmp_path / "vacancies"
    resumes.mkdir()
    vacancies.mkdir()
    (resumes / "scan.pdf").write_bytes(b"scan")

    def extract(_directory: Path, _filename: str) -> str:
        from job_agent.documents.pdf import PDFDocumentError

        raise PDFDocumentError("PDF contains no extractable text (OCR may be required)")

    monkeypatch.setattr("job_agent.services.pdf_processing.extract_pdf_text", extract)
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        summary = PDFProcessingService(
            session, resumes, vacancies, make_classifier(tmp_path)
        ).process()
        record = session.exec(select(PDFDocumentRecord)).one()

    assert summary.needs_ocr == 1
    assert summary.failed == 0
    assert record.processing_status is DocumentProcessingStatus.NEEDS_OCR
