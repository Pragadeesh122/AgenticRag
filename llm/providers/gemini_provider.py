"""Google Gemini provider adapter."""

from __future__ import annotations

from llm.providers.litellm_provider import LiteLLMProvider


class GeminiProvider(LiteLLMProvider):
    def __init__(self) -> None:
        super().__init__(
            name="gemini",
            model_prefix="gemini",
            default_chat_model="gemini-2.5-flash-lite",
            default_embedding_model="text-embedding-004",
        )
