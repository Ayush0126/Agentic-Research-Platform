from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, messages: list[dict], system_prompt: str = "") -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system_prompt: Optional system-level instruction.

        Returns:
            The generated text response.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is currently available."""
        pass
