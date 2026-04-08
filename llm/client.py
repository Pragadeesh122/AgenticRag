"""OpenAI-compatible facade over provider router."""

from __future__ import annotations

from typing import Any

from llm.factory import LLMProviderRegistry


class _ChatCompletionsFacade:
    def __init__(self, registry: LLMProviderRegistry):
        self._registry = registry

    def create(
        self,
        *,
        model: str | None = None,
        messages: list[dict],
        stream: bool = False,
        **kwargs: Any,
    ) -> Any:
        resolved = self._registry.resolve_chat(model)
        return resolved.provider.chat_completion(
            model=resolved.model,
            messages=messages,
            stream=stream,
            **kwargs,
        )


class _ChatFacade:
    def __init__(self, registry: LLMProviderRegistry):
        self.completions = _ChatCompletionsFacade(registry)


class _EmbeddingFacade:
    def __init__(self, registry: LLMProviderRegistry):
        self._registry = registry

    def create(
        self,
        *,
        input: str | list[str],
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        resolved = self._registry.resolve_embedding(model)
        return resolved.provider.embedding(
            model=resolved.model,
            input=input,
            **kwargs,
        )


class LLMClient:
    """Compatibility client with `.chat.completions.create` and `.embeddings.create`."""

    def __init__(self, registry: LLMProviderRegistry):
        self.chat = _ChatFacade(registry)
        self.embeddings = _EmbeddingFacade(registry)
        self.chat_provider = "dynamic"
        self.embedding_provider = "dynamic"
