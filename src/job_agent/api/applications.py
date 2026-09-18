"""Expose HTTP endpoints for application tracking."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from job_agent.api.dependencies import SessionDependency
from job_agent.api.schemas import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from job_agent.repositories.application import ApplicationRepository
from job_agent.services.application import (
    ApplicationConflictError,
    ApplicationNotFoundError,
    ApplicationService,
    ApplicationVacancyNotFoundError,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationResponse])
def list_applications(
    session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ApplicationResponse]:
    """List application records ordered by their latest update.

    Args:
        session: Request-scoped database session.
        limit: Maximum number of records to return.
        offset: Number of records to skip.

    Returns:
        Serialized application records for the requested page.
    """
    applications = ApplicationRepository(session).list(limit=limit, offset=offset)
    return [
        ApplicationResponse.model_validate(application, from_attributes=True)
        for application in applications
    ]


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate, session: SessionDependency
) -> ApplicationResponse:
    """Create an application record for an existing vacancy.

    Args:
        payload: Initial application state.
        session: Request-scoped database session.

    Returns:
        The newly created application record.

    Raises:
        HTTPException: If the vacancy is missing or already has an application.
    """
    try:
        application = ApplicationService(session).create(
            payload.vacancy_id, status=payload.status, notes=payload.notes
        )
    except ApplicationVacancyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ApplicationConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ApplicationResponse.model_validate(application, from_attributes=True)


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    session: SessionDependency,
) -> ApplicationResponse:
    """Partially update an application record.

    Args:
        application_id: Database identifier of the application.
        payload: Fields to update.
        session: Request-scoped database session.

    Returns:
        The updated application record.

    Raises:
        HTTPException: If the application does not exist.
    """
    try:
        application = ApplicationService(session).update(
            application_id,
            status=payload.status,
            notes=payload.notes,
            update_notes="notes" in payload.model_fields_set,
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApplicationResponse.model_validate(application, from_attributes=True)
