"""LLM client interface for summarization."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from LLM API."""
    content: str


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def chat(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Send a chat request to the LLM.

        Args:
            system_prompt: System prompt/instructions
            user_message: User input text

        Returns:
            LLMResponse with generated content
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider/model name."""
        pass
