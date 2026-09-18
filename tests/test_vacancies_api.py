from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from job_agent.db.database import get_session
from job_agent.main import app
from job_agent.models.application import Application, ApplicationStatus
from job_agent.models.vacancy import Vacancy
from job_agent.models.vacancy_analysis import VacancyAnalysis


def test_vacancy_list_filters_and_dashboard() -> None:
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
        recommended = Vacancy(
            external_id="recommended",
            source="hh",
            company="Acme",
            title="Senior Python Developer",
            url="https://example.test/recommended",
            description="Python and FastAPI",
            remote=True,
        )
        filtered = Vacancy(
            external_id="filtered",
            source="hh",
            company="Legacy Corp",
            title="1C Developer",
            url="https://example.test/filtered",
            description="Legacy platform",
            filtered_reason="Excluded technology: 1C",
        )
        session.add(recommended)
        session.add(filtered)
        session.commit()
        session.refresh(recommended)
        assert recommended.id is not None
        session.add(
            VacancyAnalysis(
                vacancy_id=recommended.id,
                technical_score=90,
                seniority_score=90,
                domain_score=80,
                location_score=100,
                salary_score=50,
                final_score=86,
                recommended=True,
                strengths=["Python"],
                gaps=[],
                missing_keywords=[],
                explanation="Strong explicit match.",
            )
        )
        session.add(
            Application(
                vacancy_id=recommended.id,
                status=ApplicationStatus.SHORTLISTED,
            )
        )
        session.commit()

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            dashboard = client.get("/")
            recommended_response = client.get(
                "/vacancies",
                params={
                    "query": "acme",
                    "remote": True,
                    "vacancy_state": "recommended",
                    "application_status": "shortlisted",
                },
            )
            filtered_response = client.get(
                "/vacancies", params={"vacancy_state": "filtered"}
            )
    finally:
        app.dependency_overrides.clear()

    assert dashboard.status_code == 200
    assert "Prospero" in dashboard.text
    assert 'id="app"' in dashboard.text
    assert "/static/assets/" in dashboard.text
    assert recommended_response.status_code == 200
    rows = recommended_response.json()
    assert [row["vacancy"]["external_id"] for row in rows] == ["recommended"]
    assert rows[0]["analysis"]["final_score"] == 86
    assert rows[0]["application"]["status"] == "shortlisted"
    assert [row["vacancy"]["external_id"] for row in filtered_response.json()] == [
        "filtered"
    ]
