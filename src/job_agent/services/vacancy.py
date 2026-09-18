"""Coordinate vacancy collection, filtering, and analysis."""

import logging
from dataclasses import dataclass

from sqlmodel import Session

from job_agent.collectors.base import VacancyCollector
from job_agent.collectors.normalization import normalize_hh_vacancy
from job_agent.llm.base import LLMProvider, LLMResponseError
from job_agent.matching.filtering import rejection_reason
from job_agent.matching.profile import CandidateProfile
from job_agent.matching.scoring import calculate_score
from job_agent.models.vacancy import Vacancy
from job_agent.models.vacancy_analysis import VacancyAnalysis
from job_agent.repositories.vacancy import VacancyRepository


class VacancyNotFoundError(LookupError):
    """Raised when a requested vacancy does not exist."""


class VacancyRejectedError(ValueError):
    """Raised when deterministic rules reject a vacancy."""


@dataclass(frozen=True, slots=True)
class CollectionSummary:
    """Counters produced by a vacancy collection run."""

    fetched: int
    created: int
    duplicates: int
    rejected: int
    analyzed: int
    analysis_failed: int


logger = logging.getLogger(__name__)


class VacancyService:
    """Coordinate collection, filtering, analysis, and persistence."""

    recommendation_threshold = 70

    def __init__(
        self,
        session: Session,
        collector: VacancyCollector,
        llm_provider: LLMProvider,
        profile: CandidateProfile,
    ) -> None:
        """Initialize the workflow and its persistence repository."""
        self._session = session
        self._collector = collector
        self._llm_provider = llm_provider
        self._profile = profile
        self._repository = VacancyRepository(session)

    async def collect(
        self, query: str, *, page: int, per_page: int, analyze_new: bool = False
    ) -> CollectionSummary:
        """Collect, normalize, filter, and optionally analyze one source page.

        Args:
            query: Vacancy search query passed to the collector.
            page: Zero-based source page number.
            per_page: Maximum number of source records to request.
            analyze_new: Whether to analyze newly persisted, eligible vacancies.

        Returns:
            Aggregate counters for the collection run.

        Raises:
            CollectorError: If the external source cannot be read reliably.
        """
        sources = await self._collector.collect(query, page=page, per_page=per_page)
        created = rejected = 0
        pending_analysis_ids: list[int] = []
        for source in sources:
            vacancy = normalize_hh_vacancy(source)
            vacancy.filtered_reason = rejection_reason(vacancy, self._profile)
            if self._repository.add_if_new(vacancy):
                created += 1
                rejected += vacancy.filtered_reason is not None
                if vacancy.filtered_reason is None and vacancy.id is not None:
                    pending_analysis_ids.append(vacancy.id)
        self._session.commit()
        analyzed = analysis_failed = 0
        if analyze_new:
            for vacancy_id in pending_analysis_ids:
                try:
                    await self.analyze(vacancy_id)
                    analyzed += 1
                except LLMResponseError:
                    analysis_failed += 1
                    logger.exception("Vacancy analysis failed: vacancy_id=%d", vacancy_id)
        return CollectionSummary(
            fetched=len(sources),
            created=created,
            duplicates=len(sources) - created,
            rejected=rejected,
            analyzed=analyzed,
            analysis_failed=analysis_failed,
        )

    async def analyze(self, vacancy_id: int) -> VacancyAnalysis:
        """Analyze and score a persisted vacancy.

        Args:
            vacancy_id: Database identifier of the vacancy.

        Returns:
            The committed analysis record.

        Raises:
            VacancyNotFoundError: If the vacancy does not exist.
            VacancyRejectedError: If deterministic rules reject the vacancy.
            LLMResponseError: If semantic analysis fails validation.
        """
        vacancy = self._repository.get(vacancy_id)
        if vacancy is None:
            raise VacancyNotFoundError(f"Vacancy {vacancy_id} does not exist")
        reason = vacancy.filtered_reason or rejection_reason(vacancy, self._profile)
        if reason is not None:
            vacancy.filtered_reason = reason
            self._session.commit()
            raise VacancyRejectedError(reason)
        result = await self._llm_provider.analyze(vacancy, self._profile)
        location_score = self._location_score(vacancy)
        salary_score = self._salary_score(vacancy)
        final_score = calculate_score(
            result, location_score=location_score, salary_score=salary_score
        )
        analysis = VacancyAnalysis(
            vacancy_id=vacancy_id,
            technical_score=result.technical_score,
            seniority_score=result.seniority_score,
            domain_score=result.domain_score,
            location_score=location_score,
            salary_score=salary_score,
            final_score=final_score,
            recommended=final_score >= self.recommendation_threshold,
            strengths=result.strengths,
            gaps=result.gaps,
            missing_keywords=result.missing_keywords,
            explanation=result.explanation,
        )
        self._repository.save_analysis(analysis)
        self._session.commit()
        self._session.refresh(analysis)
        return analysis

    def _location_score(self, vacancy: Vacancy) -> int:
        """Calculate the deterministic location component of a match score."""
        if vacancy.remote:
            return 100
        if not self._profile.allowed_locations:
            return 80
        location = (vacancy.location or "").casefold()
        allowed = any(value.casefold() in location for value in self._profile.allowed_locations)
        return 100 if allowed else 0

    def _salary_score(self, vacancy: Vacancy) -> int:
        """Calculate the deterministic salary component of a match score."""
        minimum = self._profile.minimum_salary
        if minimum is None:
            return 80
        if vacancy.salary_currency != self._profile.salary_currency:
            return 30
        upper_bound = vacancy.salary_to or vacancy.salary_from
        if upper_bound is None:
            return 50
        return 100 if upper_bound >= minimum else max(0, round(float(upper_bound) / minimum * 100))
