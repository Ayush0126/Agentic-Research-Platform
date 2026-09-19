import logging
import time
from abc import ABC, abstractmethod
from backend.llm.base import LLMProvider


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the research pipeline.

    Each agent has a name, role description, and system prompt.
    It uses an LLM provider to generate responses.
    """

    def __init__(self, llm: LLMProvider, name: str, role: str, system_prompt: str):
        self.llm = llm
        self.name = name
        self.role = role
        self.system_prompt = system_prompt

    def call_llm(self, user_message: str) -> str:
        """
        Send a message to the LLM with this agent's system prompt.

        Args:
            user_message: The message to send as the user role.

        Returns:
            The LLM's response text.
        """
        messages = [{"role": "user", "content": user_message}]
        return self.llm.generate(messages, system_prompt=self.system_prompt)

    @abstractmethod
    def run(self, input_data):
        """
        Execute this agent's task.

        Args:
            input_data: The input for this agent (type varies per agent).

        Returns:
            The agent's output (type varies per agent).
        """
        pass

    def execute(self, input_data) -> dict:
        """
        Wrapper that runs the agent with timing and error tracking.

        Returns:
            dict with 'result', 'duration', 'status', and 'agent_name'.
        """
        logger.info(f"[{self.name}] Starting execution...")
        start_time = time.time()
        try:
            result = self.run(input_data)
            duration = round(time.time() - start_time, 2)
            logger.info(f"[{self.name}] Completed in {duration}s")
            return {
                "result": result,
                "duration": duration,
                "status": "success",
                "agent_name": self.name,
            }
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            logger.error(f"[{self.name}] Failed after {duration}s: {e}")
            return {
                "result": None,
                "duration": duration,
                "status": f"error: {str(e)}",
                "agent_name": self.name,
            }
