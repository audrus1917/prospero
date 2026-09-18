"""Expose HTTP endpoints for vacancy collection and analysis."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from job_agent.api.dependencies import SessionDependency, VacancyServiceDependency
from job_agent.api.schemas import (
    AnalysisResponse,
    ApplicationResponse,
    CollectionRequest,
    CollectionResponse,
    RecommendedVacancyResponse,
    VacancyListItemResponse,
    VacancyResponse,
    VacancyState,
)
from job_agent.collectors.base import CollectorError
from job_agent.models.application import ApplicationStatus
from job_agent.models.vacancy import Vacancy
from job_agent.models.vacancy_analysis import VacancyAnalysis
from job_agent.repositories.vacancy import VacancyRepository
from job_agent.services.vacancy import VacancyNotFoundError, VacancyRejectedError

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


def _vacancy_response(vacancy: Vacancy) -> VacancyResponse:
    """Serialize a persisted vacancy for an API response."""
    if vacancy.id is None:
        raise RuntimeError("Persisted vacancy has no id")
    return VacancyResponse.model_validate(vacancy, from_attributes=True)


def _analysis_response(analysis: VacancyAnalysis) -> AnalysisResponse:
    """Serialize a persisted vacancy analysis for an API response."""
    return AnalysisResponse.model_validate(analysis, from_attributes=True)


@router.get("", response_model=list[VacancyListItemResponse])
def list_vacancies(
    session: SessionDependency,
    query: Annotated[str | None, Query(max_length=200)] = None,
    remote: bool | None = None,
    vacancy_state: VacancyState = VacancyState.ALL,
    application_status: ApplicationStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[VacancyListItemResponse]:
    """List vacancies with optional analysis and application details."""
    rows = VacancyRepository(session).list_with_details(
        query=query,
        remote=remote,
        state=vacancy_state,
        application_status=application_status,
        limit=limit,
        offset=offset,
    )
    return [
        VacancyListItemResponse(
            vacancy=_vacancy_response(vacancy),
            analysis=_analysis_response(analysis) if analysis is not None else None,
            application=(
                ApplicationResponse.model_validate(application, from_attributes=True)
                if application is not None
                else None
            ),
        )
        for vacancy, analysis, application in rows
    ]


@router.post("/collect", response_model=CollectionResponse)
async def collect_vacancies(
    payload: CollectionRequest, service: VacancyServiceDependency
) -> CollectionResponse:
    """Collect one vacancy page and optionally analyze new records.

    Raises:
        HTTPException: If the external vacancy source is unavailable.
    """
    try:
        summary = await service.collect(
            payload.query,
            page=payload.page,
            per_page=payload.per_page,
            analyze_new=payload.analyze,
        )
    except CollectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Vacancy source is temporarily unavailable",
        ) from exc
    return CollectionResponse.model_validate(summary, from_attributes=True)


@router.get("/recommended", response_model=list[RecommendedVacancyResponse])
def recommended_vacancies(
    session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[RecommendedVacancyResponse]:
    """List recommended vacancies ordered by descending score."""
    results = VacancyRepository(session).list_recommended(limit=limit, offset=offset)
    return [
        RecommendedVacancyResponse(
            vacancy=_vacancy_response(vacancy), analysis=_analysis_response(analysis)
        )
        for vacancy, analysis in results
    ]


@router.get("/{vacancy_id}", response_model=VacancyResponse)
def get_vacancy(vacancy_id: int, session: SessionDependency) -> VacancyResponse:
    """Return one vacancy by its database identifier.

    Raises:
        HTTPException: If the vacancy does not exist.
    """
    vacancy = VacancyRepository(session).get(vacancy_id)
    if vacancy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return _vacancy_response(vacancy)


@router.post("/{vacancy_id}/analyze", response_model=AnalysisResponse)
async def analyze_vacancy(vacancy_id: int, service: VacancyServiceDependency) -> AnalysisResponse:
    """Analyze one vacancy against the configured candidate profile.

    Raises:
        HTTPException: If the vacancy is missing or rejected by deterministic rules.
    """
    try:
        analysis = await service.analyze(vacancy_id)
    except VacancyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VacancyRejectedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _analysis_response(analysis)
