"""Helpers for normalizing model responses across SDK/provider shapes."""

from __future__ import annotations

from typing import Any


def _field(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def extract_embedding_vectors(response: Any) -> list[list[float]]:
    """Return embedding vectors from either object-style or dict-style response."""
    data = _field(response, "data", []) or []
    vectors: list[list[float]] = []
    for item in data:
        embedding = _field(item, "embedding", None)
        if embedding is not None:
            vectors.append(embedding)
    return vectors


def extract_first_embedding(response: Any) -> list[float]:
    vectors = extract_embedding_vectors(response)
    if not vectors:
        raise ValueError("Embedding response contained no vectors")
    return vectors[0]


def extract_first_text(response: Any, default: str = "") -> str:
    choices = _field(response, "choices", []) or []
    if not choices:
        return default
    first = choices[0]
    message = _field(first, "message", {}) or {}
    content = _field(message, "content", default)
    return content if content is not None else default


def usage_tokens(usage: Any) -> tuple[int, int]:
    prompt = int(_field(usage, "prompt_tokens", 0) or 0)
    completion = int(_field(usage, "completion_tokens", 0) or 0)
    return prompt, completion
