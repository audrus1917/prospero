"""Define provider-independent semantic analysis interfaces."""

from typing import Protocol

from job_agent.matching.models import DocumentMatchResult, MatchResult
from job_agent.matching.profile import CandidateProfile
from job_agent.models.vacancy import Vacancy


class LLMResponseError(RuntimeError):
    """Raised when semantic analysis does not return a valid response."""


class DocumentAnalysisProvider(Protocol):
    """Application-level interface for matching extracted documents."""

    async def analyze_documents(self, resume_text: str, vacancy_text: str) -> DocumentMatchResult:
        """Compare extracted resume text with extracted vacancy text."""


class LLMProvider(DocumentAnalysisProvider, Protocol):
    """Application-level interface for semantic vacancy matching."""

    async def analyze(self, vacancy: Vacancy, profile: CandidateProfile) -> MatchResult:
        """Compare trusted candidate facts with untrusted vacancy content."""
