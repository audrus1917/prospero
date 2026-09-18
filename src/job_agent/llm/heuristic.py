"""Provide deterministic local vacancy and document matching."""

import re

from job_agent.matching.models import DocumentMatchResult, MatchResult
from job_agent.matching.profile import CandidateProfile
from job_agent.models.vacancy import Vacancy


class HeuristicProvider:
    """Deterministic local provider for development and the self-contained MVP."""

    async def analyze(self, vacancy: Vacancy, profile: CandidateProfile) -> MatchResult:
        """Estimate semantic fields without inventing candidate experience."""
        content = f"{vacancy.title} {vacancy.description}".casefold()
        primary = [skill for skill in profile.primary_skills if skill.casefold() in content]
        secondary = [skill for skill in profile.secondary_skills if skill.casefold() in content]
        missing = [skill for skill in profile.primary_skills if skill.casefold() not in content]
        technical = round(100 * len(primary) / max(1, len(profile.primary_skills)))
        role_match = any(
            role.casefold() in vacancy.title.casefold() for role in profile.target_roles
        )
        seniority = 100 if role_match else (75 if "senior" in vacancy.title.casefold() else 55)
        domain = min(100, 50 + 10 * len(secondary))
        strengths = [f"Vacancy explicitly mentions {skill}" for skill in primary + secondary]
        gaps = [f"Vacancy does not mention profile skill {skill}" for skill in missing]
        explanation = (
            "Local deterministic analysis based only on explicit candidate skills and vacancy text."
        )
        return MatchResult(
            technical_score=technical,
            seniority_score=seniority,
            domain_score=domain,
            strengths=strengths,
            gaps=gaps,
            missing_keywords=missing,
            explanation=explanation,
        )

    async def analyze_documents(self, resume_text: str, vacancy_text: str) -> DocumentMatchResult:
        """Provide a local lexical comparison for PDF documents."""
        resume_terms = self._terms(resume_text)
        vacancy_terms = self._terms(vacancy_text)
        matching = sorted(resume_terms & vacancy_terms)
        missing = sorted(vacancy_terms - resume_terms)
        coverage = round(100 * len(matching) / max(1, len(vacancy_terms)))
        senior_terms = {"senior", "lead", "ведущий", "старший"}
        vacancy_is_senior = bool(vacancy_terms & senior_terms)
        resume_is_senior = bool(resume_terms & senior_terms)
        seniority = 90 if vacancy_is_senior == resume_is_senior else 45
        missing_keywords = missing[:15]
        return DocumentMatchResult(
            technical_score=coverage,
            seniority_score=seniority,
            domain_score=coverage,
            strengths=[f"Both documents explicitly mention {term}" for term in matching[:15]],
            gaps=[f"Resume does not explicitly mention {term}" for term in missing_keywords],
            missing_keywords=missing_keywords,
            recommendations=[
                f"Mention {term} only if it reflects real experience"
                for term in missing_keywords[:8]
            ],
            explanation="Local lexical comparison of terms explicitly present in both PDFs.",
        )

    @staticmethod
    def _terms(text: str) -> set[str]:
        """Extract normalized lexical terms while excluding common stop words."""
        stop_words = {
            "and",
            "for",
            "the",
            "with",
            "your",
            "для",
            "или",
            "как",
            "при",
            "это",
            "что",
            "опыт",
            "работы",
        }
        terms = {term.casefold() for term in re.findall(r"[^\W\d_][\w+#.-]{2,}", text)}
        return terms - stop_words
