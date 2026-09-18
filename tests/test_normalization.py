from decimal import Decimal

from job_agent.collectors.base import SourceVacancy
from job_agent.collectors.normalization import normalize_hh_vacancy


def test_normalize_hh_vacancy_maps_source_fields_and_removes_html() -> None:
    source = SourceVacancy(
        external_id="123",
        source="hh",
        payload={
            "id": "123",
            "name": "Senior Python Developer",
            "alternate_url": "https://hh.ru/vacancy/123",
            "description": "<p>Build <strong>APIs</strong></p>",
            "employer": {"name": "Acme"},
            "area": {"name": "Moscow"},
            "schedule": {"name": "Удаленная работа"},
            "salary": {"from": 200000, "to": 300000, "currency": "RUB"},
            "published_at": "2026-08-27T10:00:00+03:00",
        },
    )

    vacancy = normalize_hh_vacancy(source)

    assert vacancy.company == "Acme"
    assert vacancy.description == "Build  APIs"
    assert vacancy.remote is True
    assert vacancy.salary_from == Decimal("200000")
    assert vacancy.published_at is not None
