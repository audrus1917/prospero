from decimal import Decimal
from pathlib import Path

from job_agent.matching.filtering import rejection_reason
from job_agent.matching.models import MatchResult
from job_agent.matching.profile import CandidateProfile, load_candidate_profile
from job_agent.matching.scoring import calculate_score
from job_agent.models.vacancy import Vacancy


def profile(**overrides: object) -> CandidateProfile:
    values: dict[str, object] = {
        "target_roles": ["Senior Python Developer"],
        "primary_skills": ["Python", "FastAPI"],
        "excluded_titles": ["Frontend Developer"],
        "excluded_technologies": ["1C"],
    }
    values.update(overrides)
    return CandidateProfile.model_validate(values)


def vacancy(**overrides: object) -> Vacancy:
    values: dict[str, object] = {
        "external_id": "42",
        "source": "hh",
        "company": "Example",
        "title": "Senior Python Developer",
        "url": "https://example.test/42",
        "description": "Python and FastAPI",
    }
    values.update(overrides)
    return Vacancy.model_validate(values)


def test_filter_rejects_excluded_title_before_analysis() -> None:
    reason = rejection_reason(vacancy(title="Frontend Developer"), profile())

    assert reason == "Excluded title: Frontend Developer"


def test_filter_enforces_remote_requirement() -> None:
    reason = rejection_reason(vacancy(remote=False), profile(remote_required=True))

    assert reason == "Remote work is required"


def test_calculate_score_uses_deterministic_weights() -> None:
    result = MatchResult(
        technical_score=80,
        seniority_score=90,
        domain_score=60,
        strengths=[],
        gaps=[],
        missing_keywords=[],
        explanation="Evidence-based result",
    )

    assert calculate_score(result, location_score=100, salary_score=50) == 78


def test_salary_values_remain_decimal() -> None:
    result = vacancy(salary_from=Decimal("200000"))

    assert result.salary_from == Decimal("200000")


def test_example_profile_loads() -> None:
    candidate = load_candidate_profile(Path("config/candidate_profile.example.yaml"))

    assert candidate.commercial_experience_years == 8
    assert candidate.current_location == "Example City"
    assert candidate.experience[0].company == "Example Company"
    assert "Python" in candidate.experience[0].skills
    assert candidate.languages[0].level == "B2"
