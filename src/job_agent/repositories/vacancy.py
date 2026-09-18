"""Persist and query vacancies and their analyses."""

from sqlalchemy import or_
from sqlmodel import Session, col, select

from job_agent.models.application import Application, ApplicationStatus
from job_agent.models.vacancy import Vacancy
from job_agent.models.vacancy_analysis import VacancyAnalysis


class VacancyRepository:
    """Persistence operations for vacancies and analyses."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session."""
        self._session = session

    def add_if_new(self, vacancy: Vacancy) -> bool:
        """Add a vacancy unless its source identifier already exists.

        Returns:
            ``True`` when the vacancy was added, otherwise ``False``.
        """
        existing = self._session.exec(
            select(Vacancy.id).where(
                Vacancy.source == vacancy.source, Vacancy.external_id == vacancy.external_id
            )
        ).first()
        if existing is not None:
            return False
        self._session.add(vacancy)
        self._session.flush()
        return True

    def get(self, vacancy_id: int) -> Vacancy | None:
        """Return a vacancy by identifier, if it exists."""
        return self._session.get(Vacancy, vacancy_id)

    def list_with_details(
        self,
        *,
        query: str | None,
        remote: bool | None,
        state: str,
        application_status: ApplicationStatus | None,
        limit: int,
        offset: int,
    ) -> list[tuple[Vacancy, VacancyAnalysis | None, Application | None]]:
        """List vacancies with joined analysis and application details.

        Args:
            query: Optional title or company search text.
            remote: Optional remote-work filter.
            state: Analysis or filtering state to select.
            application_status: Optional application-stage filter.
            limit: Maximum number of rows to return.
            offset: Number of rows to skip.

        Returns:
            Vacancy rows paired with optional analysis and application records.
        """
        statement = (
            select(Vacancy, VacancyAnalysis, Application)
            .join(
                VacancyAnalysis,
                col(VacancyAnalysis.vacancy_id) == col(Vacancy.id),
                isouter=True,
            )
            .join(
                Application,
                col(Application.vacancy_id) == col(Vacancy.id),
                isouter=True,
            )
        )
        if query:
            pattern = f"%{query.strip()}%"
            statement = statement.where(
                or_(col(Vacancy.title).ilike(pattern), col(Vacancy.company).ilike(pattern))
            )
        if remote is not None:
            statement = statement.where(Vacancy.remote == remote)
        if state == "recommended":
            statement = statement.where(col(VacancyAnalysis.recommended).is_(True))
        elif state == "other":
            statement = statement.where(col(VacancyAnalysis.recommended).is_(False))
        elif state == "unanalyzed":
            statement = statement.where(
                col(VacancyAnalysis.id).is_(None), col(Vacancy.filtered_reason).is_(None)
            )
        elif state == "filtered":
            statement = statement.where(col(Vacancy.filtered_reason).is_not(None))
        if application_status is not None:
            statement = statement.where(Application.status == application_status)
        statement = (
            statement.order_by(
                col(VacancyAnalysis.final_score).desc().nulls_last(),
                col(Vacancy.published_at).desc().nulls_last(),
                col(Vacancy.id).desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.exec(statement).all())

    def save_analysis(self, analysis: VacancyAnalysis) -> VacancyAnalysis:
        """Replace a vacancy analysis without committing the transaction."""
        previous = self._session.exec(
            select(VacancyAnalysis).where(VacancyAnalysis.vacancy_id == analysis.vacancy_id)
        ).first()
        if previous is not None:
            self._session.delete(previous)
            self._session.flush()
        self._session.add(analysis)
        self._session.flush()
        return analysis

    def list_recommended(self, *, limit: int, offset: int) -> list[tuple[Vacancy, VacancyAnalysis]]:
        """Return a page of recommended vacancies ordered by score."""
        statement = (
            select(Vacancy, VacancyAnalysis)
            .join(VacancyAnalysis, col(VacancyAnalysis.vacancy_id) == col(Vacancy.id))
            .where(col(VacancyAnalysis.recommended).is_(True))
            .order_by(col(VacancyAnalysis.final_score).desc(), col(Vacancy.id).desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.exec(statement).all())
