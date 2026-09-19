import logging
from backend.llm.base import LLMProvider
from backend.llm.groq_provider import GroqProvider
from backend.llm.ollama_provider import OllamaProvider
from backend.config import settings

logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    """
    Factory function to get the configured LLM provider.
    Falls back to Ollama if Groq is not available.
    """
    if settings.llm_provider == "groq" and settings.groq_api_key:
        logger.info(f"Using Groq provider with model: {settings.groq_model}")
        provider = GroqProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        if provider.is_available():
            return provider
        logger.warning("Groq provider not available, falling back to Ollama")

    logger.info(f"Using Ollama provider with model: {settings.ollama_model}")
    return OllamaProvider(model=settings.ollama_model)
