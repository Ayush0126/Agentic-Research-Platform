import logging
import time
import re
from groq import Groq
from backend.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """LLM provider using Groq's free API (fast inference)."""

    def __init__(self, api_key: str, model: str = "qwen/qwen3.8-27b",
                 temperature: float = 0.3, max_tokens: int = 900):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._api_key = api_key
        self._client = None
        self._last_call_time = 0
        if api_key:
            try:
                self._client = Groq(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")

    def _rate_limit(self):
        """Wait between calls to respect free tier output token budget."""
        elapsed = time.time() - self._last_call_time
        # Free tier: 1000 output tokens/min. Each call uses ~400-900 tokens.
        # With fewer sources, 45s gap is sufficient.
        min_gap = 45
        if elapsed < min_gap:
            wait = min_gap - elapsed
            logger.info(f"Rate limiting: waiting {wait:.0f}s for token budget reset")
            time.sleep(wait)
        self._last_call_time = time.time()

    def generate(self, messages: list[dict], system_prompt: str = "") -> str:
        """Generate a response using Groq API with automatic retry on rate limits."""
        if not self._client:
            raise RuntimeError("Groq client not initialized. Check API key.")

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        self._rate_limit()

        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate_limit" in error_str:
                    # Extract wait time from error message if available
                    wait_match = re.search(r"try again in (\d+\.?\d*)", error_str, re.IGNORECASE)
                    wait_time = float(wait_match.group(1)) + 5 if wait_match else 65
                    wait_time = max(wait_time, 30)  # At least 30s
                    logger.warning(
                        f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                        f"Waiting {wait_time:.0f}s..."
                    )
                    time.sleep(wait_time)
                    self._last_call_time = time.time()
                else:
                    logger.error(f"Groq API error: {e}")
                    raise

        raise RuntimeError("Groq rate limit: max retries exceeded. Try again later.")

    def is_available(self) -> bool:
        """Check if Groq is available."""
        if not self._client:
            return False
        try:
            self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Say hello in one word."}],
                max_tokens=20,
            )
            return True
        except Exception:
            return False
