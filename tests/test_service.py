import asyncio

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from job_agent.collectors.base import SourceVacancy
from job_agent.llm.heuristic import HeuristicProvider
from job_agent.matching.profile import CandidateProfile
from job_agent.models.vacancy import Vacancy
from job_agent.models.vacancy_analysis import VacancyAnalysis
from job_agent.services.vacancy import VacancyService


class StubCollector:
    async def collect(
        self, query: str, *, page: int = 0, per_page: int = 20
    ) -> list[SourceVacancy]:
        del query, page, per_page
        return [
            SourceVacancy(
                external_id="1",
                source="hh",
                payload={
                    "id": "1",
                    "name": "Senior Python Developer",
                    "alternate_url": "https://hh.ru/vacancy/1",
                    "description": "Python FastAPI PostgreSQL Docker Redis",
                    "employer": {"name": "Acme"},
                    "area": {"name": "Remote"},
                    "schedule": {"name": "Удаленная работа"},
                    "salary": {"from": 250000, "to": 300000, "currency": "RUB"},
                },
            )
        ]


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def make_profile() -> CandidateProfile:
    return CandidateProfile(
        target_roles=["Senior Python Developer"],
        primary_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        secondary_skills=["Redis"],
    )


def test_collection_deduplicates_and_analysis_is_replaceable() -> None:
    with make_session() as session:
        service = VacancyService(session, StubCollector(), HeuristicProvider(), make_profile())

        first = asyncio.run(service.collect("python", page=0, per_page=20, analyze_new=True))
        second = asyncio.run(service.collect("python", page=0, per_page=20))
        vacancy = session.exec(select(Vacancy)).one()
        assert vacancy.id is not None
        first_analysis = session.exec(select(VacancyAnalysis)).one()
        second_analysis = asyncio.run(service.analyze(vacancy.id))

        assert first.created == 1
        assert second.duplicates == 1
        assert first.analyzed == 1
        assert first.analysis_failed == 0
        assert first_analysis.recommended is True
        assert second_analysis.analyzed_at > first_analysis.analyzed_at
        assert len(session.exec(select(VacancyAnalysis)).all()) == 1
