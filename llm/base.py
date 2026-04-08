"""Base abstractions for provider-agnostic LLM access."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Abstract provider contract for chat completion + embeddings."""

    name: str

    @abstractmethod
    def chat_completion(
        self,
        *,
        model: str | None,
        messages: list[dict],
        stream: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Create a chat completion (streaming or non-streaming)."""

    @abstractmethod
    def embedding(
        self,
        *,
        model: str | None,
        input: str | list[str],
        **kwargs: Any,
    ) -> Any:
        """Create one or more embedding vectors."""

