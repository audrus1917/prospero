"""Calculate deterministic vacancy match scores."""

from dataclasses import dataclass

from job_agent.matching.models import MatchResult


@dataclass(frozen=True, slots=True)
class ScoreWeights:
    """Weights used for deterministic final-score calculation."""

    technical: float = 0.45
    seniority: float = 0.20
    domain: float = 0.15
    location: float = 0.10
    salary: float = 0.10


DEFAULT_SCORE_WEIGHTS = ScoreWeights()


def calculate_score(
    result: MatchResult,
    *,
    location_score: int,
    salary_score: int,
    weights: ScoreWeights = DEFAULT_SCORE_WEIGHTS,
) -> int:
    """Calculate a bounded deterministic vacancy score."""
    score = (
        result.technical_score * weights.technical
        + result.seniority_score * weights.seniority
        + result.domain_score * weights.domain
        + location_score * weights.location
        + salary_score * weights.salary
    )
    return max(0, min(100, round(score)))
