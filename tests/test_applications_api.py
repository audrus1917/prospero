from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from job_agent.db.database import get_session
from job_agent.main import app
from job_agent.models.vacancy import Vacancy


def test_application_api_lifecycle() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    with Session(engine) as session:
        vacancy = Vacancy(
            external_id="api-42",
            source="hh",
            company="Example",
            title="Senior Python Developer",
            url="https://example.test/api-42",
            description="Python and FastAPI",
        )
        session.add(vacancy)
        session.commit()
        session.refresh(vacancy)
        assert vacancy.id is not None
        vacancy_id = vacancy.id

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            created = client.post(
                "/applications",
                json={"vacancy_id": vacancy_id, "status": "shortlisted", "notes": "Review"},
            )
            assert created.status_code == 201
            application_id = created.json()["id"]

            updated = client.patch(
                f"/applications/{application_id}",
                json={"status": "applied", "notes": None},
            )
            listed = client.get("/applications")
    finally:
        app.dependency_overrides.clear()

    assert updated.status_code == 200
    assert updated.json()["status"] == "applied"
    assert updated.json()["notes"] is None
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [application_id]
