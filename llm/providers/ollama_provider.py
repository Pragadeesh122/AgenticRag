"""Local/open-source Ollama provider adapter (e.g. Llama models)."""

from __future__ import annotations

import os
from typing import Any

from llm.providers.litellm_provider import LiteLLMProvider


class OllamaProvider(LiteLLMProvider):
    def __init__(self) -> None:
        super().__init__(
            name="ollama",
            model_prefix="ollama",
            default_chat_model="llama3.1:8b",
            default_embedding_model="nomic-embed-text",
        )

    def _completion_extra_kwargs(self) -> dict[str, Any]:
        return {"api_base": os.getenv("OLLAMA_HOST", "http://localhost:11434")}

    def _embedding_extra_kwargs(self) -> dict[str, Any]:
        return {"api_base": os.getenv("OLLAMA_HOST", "http://localhost:11434")}
