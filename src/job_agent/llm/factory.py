"""Construct semantic analysis providers from application settings."""

from urllib.parse import urlparse

import httpx

from job_agent.config.settings import Settings
from job_agent.llm.base import LLMProvider
from job_agent.llm.heuristic import HeuristicProvider
from job_agent.llm.openai_compatible import OpenAICompatibleProvider


class LLMConfigurationError(ValueError):
    """Raised when the selected LLM provider lacks required configuration."""


def build_llm_provider(settings: Settings, client: httpx.AsyncClient) -> LLMProvider:
    """Build the configured semantic-analysis provider."""
    provider = settings.llm_provider.casefold()
    if provider == "heuristic":
        return HeuristicProvider()
    if provider == "openai":
        if not settings.openai_api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is required for LLM_PROVIDER=openai")
        if not settings.llm_model:
            raise LLMConfigurationError("LLM_MODEL is required for LLM_PROVIDER=openai")
        api_style = settings.llm_api_style.casefold()
        if api_style == "auto":
            api_style = (
                "chat"
                if urlparse(settings.llm_base_url).hostname == "api.deepseek.com"
                else "responses"
            )
        if api_style not in {"responses", "chat"}:
            raise LLMConfigurationError("LLM_API_STYLE must be auto, responses, or chat")
        return OpenAICompatibleProvider(client, settings.llm_model, api_style)
    raise LLMConfigurationError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
