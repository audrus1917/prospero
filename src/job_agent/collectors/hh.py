"""Collect vacancies from the public HeadHunter API."""

import asyncio
import logging

import httpx

from job_agent.collectors.base import CollectorError, SourceVacancy

logger = logging.getLogger(__name__)


class HHCollector:
    """Collect vacancies from the public HeadHunter API."""

    source = "hh"
    base_url = "https://api.hh.ru"

    def __init__(self, client: httpx.AsyncClient) -> None:
        """Initialize the collector with a reusable HeadHunter client."""
        self._client = client

    async def collect(
        self, query: str, *, page: int = 0, per_page: int = 20
    ) -> list[SourceVacancy]:
        """Collect and enrich one search result page from HeadHunter.

        Args:
            query: Search text accepted by HeadHunter.
            page: Zero-based result page number.
            per_page: Maximum number of vacancies to collect.

        Returns:
            Source-level vacancies containing complete API payloads.

        Raises:
            CollectorError: If HeadHunter returns invalid or unavailable data.
        """
        try:
            response = await self._request(
                "/vacancies", params={"text": query, "page": page, "per_page": per_page}
            )
            items = response.json().get("items", [])
            vacancies: list[SourceVacancy] = []
            for item in items:
                detail = await self._request(f"/vacancies/{item['id']}")
                vacancies.append(
                    SourceVacancy(
                        external_id=str(item["id"]),
                        source=self.source,
                        payload=detail.json(),
                    )
                )
            logger.info("HH collection completed: query=%r count=%d", query, len(vacancies))
            return vacancies
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise CollectorError("HeadHunter returned an invalid or unavailable response") from exc

    async def _request(
        self, path: str, *, params: dict[str, str | int] | None = None
    ) -> httpx.Response:
        """Send a GET request with bounded retries for transient failures."""
        for attempt in range(3):
            response = await self._client.get(path, params=params)
            if response.status_code not in {429, 500, 502, 503, 504}:
                response.raise_for_status()
                return response
            if attempt == 2:
                response.raise_for_status()
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
            await asyncio.sleep(delay)
        raise AssertionError("retry loop must return or raise")
