import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from job_agent.models.application import ApplicationStatus
from job_agent.models.vacancy import Vacancy
from job_agent.services.application import (
    ApplicationConflictError,
    ApplicationService,
    ApplicationVacancyNotFoundError,
)


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def make_vacancy() -> Vacancy:
    return Vacancy(
        external_id="42",
        source="hh",
        company="Example",
        title="Senior Python Developer",
        url="https://example.test/42",
        description="Python and FastAPI",
    )


def test_application_lifecycle() -> None:
    with make_session() as session:
        vacancy = make_vacancy()
        session.add(vacancy)
        session.commit()
        session.refresh(vacancy)
        assert vacancy.id is not None

        service = ApplicationService(session)
        application = service.create(vacancy.id, notes="Promising role")
        updated = service.update(
            application.id or 0,
            status=ApplicationStatus.APPLIED,
            notes=None,
            update_notes=True,
        )

        assert updated.status is ApplicationStatus.APPLIED
        assert updated.notes is None
        assert updated.updated_at >= updated.created_at


def test_application_requires_vacancy() -> None:
    with make_session() as session, pytest.raises(ApplicationVacancyNotFoundError):
        ApplicationService(session).create(999)


def test_application_is_unique_per_vacancy() -> None:
    with make_session() as session:
        vacancy = make_vacancy()
        session.add(vacancy)
        session.commit()
        session.refresh(vacancy)
        assert vacancy.id is not None

        service = ApplicationService(session)
        service.create(vacancy.id)

        with pytest.raises(ApplicationConflictError):
            service.create(vacancy.id)
