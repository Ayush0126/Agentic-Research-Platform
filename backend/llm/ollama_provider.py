import logging
from ollama import chat
from backend.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """LLM provider using local Ollama instance."""

    def __init__(self, model: str = "gemma2:9b"):
        self.model = model

    def generate(self, messages: list[dict], system_prompt: str = "") -> str:
        """Generate a response using local Ollama."""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        try:
            response = chat(
                model=self.model,
                messages=full_messages,
            )
            return response.message.content
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            chat(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception:
            return False
