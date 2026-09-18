"""Load typed application settings from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://prospero:prospero@localhost:5432/prospero"
    log_level: str = "INFO"
    http_timeout: float = Field(default=10.0, gt=0)
    llm_timeout: float = Field(default=60.0, gt=0)
    hh_user_agent: str = "ProsperoJobAgent/0.1"
    hh_access_token: SecretStr | None = None
    candidate_profile_path: Path = Path("config/candidate_profile.yaml")
    pdf_resumes_path: Path = Path("data/resumes")
    pdf_vacancies_path: Path = Path("data/vacancies")
    category_taxonomy_path: Path = Path("config/categories.json")
    llm_provider: str = "heuristic"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_style: str = "auto"
    llm_model: str | None = None
    openai_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()
