from datetime import UTC, datetime

from fastapi.testclient import TestClient

from job_agent.api.dependencies import get_document_matching_service
from job_agent.documents.pdf import PDFDocument
from job_agent.main import app
from job_agent.matching.models import DocumentMatchResult
from job_agent.services.document_matching import PDFMatch


class StubDocumentService:
    def list_resumes(self) -> list[PDFDocument]:
        return [PDFDocument("resume.pdf", 1024, datetime.now(UTC))]

    def list_vacancies(self) -> list[PDFDocument]:
        return [PDFDocument("backend.pdf", 2048, datetime.now(UTC))]

    async def analyze(
        self, resume_file: str, vacancy_files: list[str] | None = None
    ) -> list[PDFMatch]:
        assert resume_file == "resume.pdf"
        assert vacancy_files == ["backend.pdf"]
        return [
            PDFMatch(
                vacancy_file="backend.pdf",
                final_score=84,
                result=DocumentMatchResult(
                    technical_score=90,
                    seniority_score=80,
                    domain_score=65,
                    strengths=["Python"],
                    gaps=["Kubernetes"],
                    missing_keywords=["Kubernetes"],
                    recommendations=["Mention Kubernetes only if it reflects real experience"],
                    explanation="Strong backend match.",
                ),
            )
        ]


def test_document_api() -> None:
    app.dependency_overrides[get_document_matching_service] = StubDocumentService
    try:
        with TestClient(app) as client:
            resumes = client.get("/documents/resumes")
            vacancies = client.get("/documents/vacancies")
            matches = client.post(
                "/documents/analyze",
                json={"resume_file": "resume.pdf", "vacancy_files": ["backend.pdf"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert resumes.status_code == 200
    assert resumes.json()[0]["name"] == "resume.pdf"
    assert vacancies.json()[0]["name"] == "backend.pdf"
    assert matches.status_code == 200
    assert matches.json()[0]["final_score"] == 84
    assert matches.json()[0]["recommendations"]
