"""xAI Grok provider adapter."""

from __future__ import annotations

from llm.providers.litellm_provider import LiteLLMProvider


class GrokProvider(LiteLLMProvider):
    def __init__(self) -> None:
        super().__init__(
            name="grok",
            model_prefix="xai",
            default_chat_model="grok-2-latest",
            default_embedding_model=None,
        )
