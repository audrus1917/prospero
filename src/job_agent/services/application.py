"""Implement application tracking workflows."""

from datetime import UTC, datetime

from sqlmodel import Session

from job_agent.models.application import Application, ApplicationStatus
from job_agent.repositories.application import ApplicationRepository
from job_agent.repositories.vacancy import VacancyRepository


class ApplicationNotFoundError(LookupError):
    """Raised when a requested application does not exist."""


class ApplicationConflictError(ValueError):
    """Raised when a vacancy already has an application."""


class ApplicationVacancyNotFoundError(LookupError):
    """Raised when an application references an unknown vacancy."""


class ApplicationService:
    """Create and update vacancy application tracking records."""

    def __init__(self, session: Session) -> None:
        """Initialize the workflow with a transaction-owning session."""
        self._session = session
        self._applications = ApplicationRepository(session)
        self._vacancies = VacancyRepository(session)

    def create(
        self,
        vacancy_id: int,
        *,
        status: ApplicationStatus = ApplicationStatus.NEW,
        notes: str | None = None,
    ) -> Application:
        """Create an application for an existing vacancy.

        Args:
            vacancy_id: Identifier of the vacancy being tracked.
            status: Initial application stage.
            notes: Optional user notes.

        Returns:
            The committed application record.

        Raises:
            ApplicationVacancyNotFoundError: If the vacancy does not exist.
            ApplicationConflictError: If the vacancy already has an application.
        """
        if self._vacancies.get(vacancy_id) is None:
            raise ApplicationVacancyNotFoundError(f"Vacancy {vacancy_id} does not exist")
        if self._applications.get_by_vacancy(vacancy_id) is not None:
            raise ApplicationConflictError(
                f"An application for vacancy {vacancy_id} already exists"
            )
        application = self._applications.add(
            Application(vacancy_id=vacancy_id, status=status, notes=notes)
        )
        self._session.commit()
        self._session.refresh(application)
        return application

    def update(
        self,
        application_id: int,
        *,
        status: ApplicationStatus | None = None,
        notes: str | None = None,
        update_notes: bool = False,
    ) -> Application:
        """Update selected fields of an application.

        Args:
            application_id: Identifier of the application to update.
            status: New stage, or ``None`` to preserve the current stage.
            notes: New notes value when ``update_notes`` is enabled.
            update_notes: Whether to replace the notes, including with ``None``.

        Returns:
            The committed application record.

        Raises:
            ApplicationNotFoundError: If the application does not exist.
        """
        application = self._applications.get(application_id)
        if application is None:
            raise ApplicationNotFoundError(f"Application {application_id} does not exist")
        if status is not None:
            application.status = status
        if update_notes:
            application.notes = notes
        application.updated_at = datetime.now(UTC)
        self._session.add(application)
        self._session.commit()
        self._session.refresh(application)
        return application
