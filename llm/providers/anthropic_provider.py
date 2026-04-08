"""Anthropic Claude provider adapter."""

from __future__ import annotations

from llm.providers.litellm_provider import LiteLLMProvider


class AnthropicProvider(LiteLLMProvider):
    def __init__(self) -> None:
        super().__init__(
            name="anthropic",
            model_prefix="anthropic",
            default_chat_model="claude-haiku-4-5-20251001",
            default_embedding_model=None,
        )
