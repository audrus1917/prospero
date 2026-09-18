"""Apply inexpensive deterministic vacancy rejection rules."""

from job_agent.matching.profile import CandidateProfile
from job_agent.models.vacancy import Vacancy


def rejection_reason(vacancy: Vacancy, profile: CandidateProfile) -> str | None:
    """Return the first inexpensive deterministic rejection reason."""
    title = vacancy.title.casefold()
    content = f"{vacancy.title} {vacancy.description}".casefold()
    for excluded_title in profile.excluded_titles:
        if excluded_title.casefold() in title:
            return f"Excluded title: {excluded_title}"
    for technology in profile.excluded_technologies:
        if technology.casefold() in content:
            return f"Excluded technology: {technology}"
    if profile.remote_required and not vacancy.remote:
        return "Remote work is required"
    if profile.allowed_locations and not vacancy.remote:
        location = (vacancy.location or "").casefold()
        if not any(allowed.casefold() in location for allowed in profile.allowed_locations):
            return "Location is outside the allowed list"
    return None
