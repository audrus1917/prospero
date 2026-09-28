"""Coordinate matching local resume and vacancy documents."""

from dataclasses import dataclass
from pathlib import Path

from job_agent.documents.base import LocalDocument
from job_agent.documents.local import extract_document_text, list_documents
from job_agent.llm.base import DocumentAnalysisProvider
from job_agent.matching.models import DocumentMatchResult

MAX_BATCH_SIZE = 20


class DocumentBatchError(ValueError):
    """Raised when a document matching request exceeds safe batch limits."""


@dataclass(frozen=True, slots=True)
class PDFMatch:
    """A scored match between one resume and one vacancy document."""

    vacancy_file: str
    final_score: int
    result: DocumentMatchResult


class DocumentMatchingService:
    """Discover local documents and compare vacancies with a selected resume."""

    def __init__(
        self,
        resumes_path: Path,
        vacancies_path: Path,
        provider: DocumentAnalysisProvider,
    ) -> None:
        """Initialize the workflow with document roots and an analysis provider."""
        self._resumes_path = resumes_path
        self._vacancies_path = vacancies_path
        self._provider = provider

    def list_resumes(self) -> list[LocalDocument]:
        """List resume documents available for matching."""
        return list_documents(self._resumes_path)

    def list_vacancies(self) -> list[LocalDocument]:
        """List vacancy documents available for matching."""
        return list_documents(self._vacancies_path)

    async def analyze(
        self, resume_file: str, vacancy_files: list[str] | None = None
    ) -> list[PDFMatch]:
        """Compare one resume with selected vacancy documents.

        Args:
            resume_file: Filename of the resume document.
            vacancy_files: Vacancy filenames, or ``None`` to compare all available documents.

        Returns:
            Matches ordered by descending deterministic final score.

        Raises:
            DocumentBatchError: If the vacancy selection is empty, duplicated, or too large.
            DocumentError: If a selected document cannot be read safely.
            LLMResponseError: If the analysis provider returns an invalid response.
        """
        selected_files = vacancy_files or [item.name for item in self.list_vacancies()]
        if not selected_files:
            raise DocumentBatchError("No vacancy documents were found")
        if len(selected_files) > MAX_BATCH_SIZE:
            raise DocumentBatchError(f"A batch cannot contain more than {MAX_BATCH_SIZE} files")
        if len(set(selected_files)) != len(selected_files):
            raise DocumentBatchError("Vacancy document filenames must be unique")

        resume_text = extract_document_text(self._resumes_path, resume_file)
        matches: list[PDFMatch] = []
        for vacancy_file in selected_files:
            vacancy_text = extract_document_text(self._vacancies_path, vacancy_file)
            result = await self._provider.analyze_documents(resume_text, vacancy_text)
            final_score = round(
                result.technical_score * 0.65
                + result.seniority_score * 0.20
                + result.domain_score * 0.15
            )
            matches.append(
                PDFMatch(
                    vacancy_file=vacancy_file,
                    final_score=max(0, min(100, final_score)),
                    result=result,
                )
            )
        return sorted(matches, key=lambda match: match.final_score, reverse=True)
