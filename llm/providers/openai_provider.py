"""OpenAI provider adapter."""

from __future__ import annotations

from llm.providers.litellm_provider import LiteLLMProvider


class OpenAIProvider(LiteLLMProvider):
    def __init__(self) -> None:
        super().__init__(
            name="openai",
            model_prefix="openai",
            default_chat_model="gpt-4o-mini",
            default_embedding_model="text-embedding-3-large",
        )
