"""Persist and query vacancy applications."""

from sqlmodel import Session, col, select

from job_agent.models.application import Application


class ApplicationRepository:
    """Persistence operations for vacancy applications."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session."""
        self._session = session

    def add(self, application: Application) -> Application:
        """Add and flush an application without committing the transaction."""
        self._session.add(application)
        self._session.flush()
        return application

    def get(self, application_id: int) -> Application | None:
        """Return an application by identifier, if it exists."""
        return self._session.get(Application, application_id)

    def get_by_vacancy(self, vacancy_id: int) -> Application | None:
        """Return the application associated with a vacancy, if any."""
        return self._session.exec(
            select(Application).where(Application.vacancy_id == vacancy_id)
        ).first()

    def list(self, *, limit: int, offset: int) -> list[Application]:
        """Return a page of applications ordered by latest update."""
        statement = (
            select(Application)
            .order_by(col(Application.updated_at).desc(), col(Application.id).desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.exec(statement).all())
