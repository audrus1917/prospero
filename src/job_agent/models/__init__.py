"""Export database-backed domain models."""

from job_agent.models.application import Application, ApplicationStatus
from job_agent.models.pdf_document import (
    DocumentKind,
    DocumentProcessingStatus,
    PDFDocumentRecord,
)
from job_agent.models.vacancy import Vacancy
from job_agent.models.vacancy_analysis import VacancyAnalysis

__all__ = [
    "Application",
    "ApplicationStatus",
    "DocumentKind",
    "DocumentProcessingStatus",
    "PDFDocumentRecord",
    "Vacancy",
    "VacancyAnalysis",
]
