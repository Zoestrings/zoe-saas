"""Protocol definition for LLM providers."""

from typing import Any, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol that all Zoe LLM providers must implement."""

    @property
    def name(self) -> str:
        """Unique provider identifier (e.g. 'groq', 'gemini', 'mock')."""
        ...

    def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        """Generate response text given system instructions and user message."""
        ...

    def classify(self, text: str, categories: List[str], **kwargs: Any) -> str:
        """Classify message text into one of the provided categories."""
        ...

