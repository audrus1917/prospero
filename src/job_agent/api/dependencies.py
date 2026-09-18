"""Provide request-scoped FastAPI application dependencies."""

from collections.abc import Generator
from typing import Annotated

import httpx
from fastapi import Depends, Request
from sqlmodel import Session

from job_agent.collectors.hh import HHCollector
from job_agent.config.settings import Settings, get_settings
from job_agent.db.database import get_session
from job_agent.llm.factory import build_llm_provider
from job_agent.matching.classification import DocumentClassifier
from job_agent.matching.profile import load_candidate_profile
from job_agent.services.document_matching import DocumentMatchingService
from job_agent.services.pdf_processing import PDFProcessingService
from job_agent.services.vacancy import VacancyService

SessionDependency = Annotated[Session, Depends(get_session)]


def get_vacancy_service(
    request: Request,
    session: SessionDependency,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Generator[VacancyService, None, None]:
    """Build a request-scoped vacancy workflow from application dependencies."""
    hh_client: httpx.AsyncClient = request.app.state.hh_client
    llm_client: httpx.AsyncClient = request.app.state.llm_client
    profile = load_candidate_profile(settings.candidate_profile_path)
    yield VacancyService(
        session,
        HHCollector(hh_client),
        build_llm_provider(settings, llm_client),
        profile,
    )


VacancyServiceDependency = Annotated[VacancyService, Depends(get_vacancy_service)]


def get_document_matching_service(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentMatchingService:
    """Build the configured local-PDF matching workflow."""
    llm_client: httpx.AsyncClient = request.app.state.llm_client
    return DocumentMatchingService(
        settings.pdf_resumes_path,
        settings.pdf_vacancies_path,
        build_llm_provider(settings, llm_client),
    )


DocumentMatchingServiceDependency = Annotated[
    DocumentMatchingService, Depends(get_document_matching_service)
]


def get_pdf_processing_service(
    session: SessionDependency,
    settings: Annotated[Settings, Depends(get_settings)],
) -> PDFProcessingService:
    """Build the local PDF catalog and classification workflow."""
    return PDFProcessingService(
        session,
        settings.pdf_resumes_path,
        settings.pdf_vacancies_path,
        DocumentClassifier.from_file(settings.category_taxonomy_path),
    )


PDFProcessingServiceDependency = Annotated[
    PDFProcessingService, Depends(get_pdf_processing_service)
]
