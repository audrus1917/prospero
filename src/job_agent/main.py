"""Create and configure the Prospero FastAPI application."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from job_agent.api.applications import router as applications_router
from job_agent.api.documents import router as documents_router
from job_agent.api.vacancies import router as vacancies_router
from job_agent.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize shared HTTP clients for the application lifespan.

    Args:
        app: FastAPI application whose state receives the shared clients.

    Yields:
        Control to FastAPI while the shared clients are available.
    """
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    hh_headers = {"HH-User-Agent": settings.hh_user_agent}
    if settings.hh_access_token is not None:
        hh_headers["Authorization"] = f"Bearer {settings.hh_access_token.get_secret_value()}"
    async with httpx.AsyncClient(
        base_url="https://api.hh.ru",
        timeout=httpx.Timeout(settings.http_timeout),
        headers=hh_headers,
    ) as hh_client:
        llm_headers = (
            {"Authorization": f"Bearer {settings.openai_api_key}"}
            if settings.openai_api_key
            else {}
        )
        async with httpx.AsyncClient(
            base_url=settings.llm_base_url,
            timeout=httpx.Timeout(settings.llm_timeout),
            headers=llm_headers,
        ) as llm_client:
            app.state.hh_client = hh_client
            app.state.llm_client = llm_client
            yield


app = FastAPI(
    title="Prospero Job Agent",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(vacancies_router)
app.include_router(applications_router)
app.include_router(documents_router)

static_directory = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_directory), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    """Return the dashboard entry page."""
    return FileResponse(static_directory / "index.html")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return a basic application health indicator."""
    return {"status": "ok"}
