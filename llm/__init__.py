"""Provider-agnostic LLM client entrypoints."""

from llm.client import LLMClient
from llm.factory import get_llm_registry


def build_llm_client() -> LLMClient:
    return LLMClient(get_llm_registry())
