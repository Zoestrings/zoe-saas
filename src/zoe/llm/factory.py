"""Factory helper initializing LLM router or provider from project secrets."""

from typing import Any, Optional

from zoe.llm.mock import MockLLMClient
from zoe.llm.providers.gemini_provider import GeminiProvider
from zoe.llm.providers.groq_provider import GroqProvider
from zoe.llm.router import LLMRouter
from zoe.settings import load_project_secrets
from zoe.utils.logging import get_logger

logger = get_logger("zoe.llm.factory")


def get_llm_client(project_id: str = "live_test") -> Any:
    """Instantiate GroqProvider/LLMRouter from project secrets, falling back to MockLLMClient."""
    secrets = load_project_secrets(project_id)
    groq_key = secrets.get("groq_api_key") or secrets.get("provider_api_key")
    gemini_key = secrets.get("gemini_api_key")

    if not groq_key or "YOUR_GROQ_API_KEY" in str(groq_key):
        logger.info(
            "No valid Groq API key found in secrets for project '%s'; defaulting to MockLLMClient",
            project_id,
        )
        return MockLLMClient()

    try:
        primary = GroqProvider(api_key=groq_key, model="llama-3.1-8b-instant")
        fallback = GeminiProvider(api_key=gemini_key) if gemini_key else None
        approved = {"groq"}
        if fallback:
            approved.add("gemini")

        logger.info("Initialized GroqProvider as primary LLM for project '%s'", project_id)
        return LLMRouter(primary=primary, fallback=fallback, approved_providers=approved)
    except Exception as exc:
        logger.warning("Failed to initialize real LLM provider (%s); defaulting to MockLLMClient", str(exc))
        return MockLLMClient()

