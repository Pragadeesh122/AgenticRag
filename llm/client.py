"""OpenAI-compatible facade over provider router."""

from __future__ import annotations

import time
from typing import Any

from llm.factory import LLMProviderRegistry
from observability.metrics import (
    estimate_cost_usd,
    observe_llm_outcome,
    observe_llm_output_speed,
    observe_llm_ttft,
)

_STREAM_USAGE_PROVIDERS = {"openai", "grok"}


def _field(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _extract_usage(obj: Any):
    return _field(obj, "usage", None)


def _extract_delta_content(chunk: Any) -> str:
    choices = _field(chunk, "choices", None)
    if not choices:
        return ""
    first_choice = choices[0]
    delta = _field(first_choice, "delta", None)
    if not delta:
        return ""
    content = _field(delta, "content", "")
    return content or ""


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
        provider_name = resolved.provider.name
        resolved_model = resolved.model
        call_kwargs = dict(kwargs)

        if (
            stream
            and "stream_options" not in call_kwargs
            and provider_name in _STREAM_USAGE_PROVIDERS
        ):
            call_kwargs["stream_options"] = {"include_usage": True}

        started = time.perf_counter()
        try:
            response = resolved.provider.chat_completion(
                model=resolved_model,
                messages=messages,
                stream=stream,
                **call_kwargs,
            )
        except Exception:
            observe_llm_outcome(
                operation="completion",
                provider=provider_name,
                model=resolved_model,
                stream=stream,
                status="error",
                duration_seconds=time.perf_counter() - started,
            )
            raise

        if not stream:
            usage = _extract_usage(response)
            status = "success" if usage is not None else "usage_missing"
            cost_usd = (
                estimate_cost_usd(
                    provider=provider_name,
                    model=resolved_model,
                    usage=usage,
                    operation="completion",
                )
                if usage is not None
                else None
            )
            observe_llm_outcome(
                operation="completion",
                provider=provider_name,
                model=resolved_model,
                stream=False,
                status=status,
                duration_seconds=time.perf_counter() - started,
                usage=usage,
                cost_usd=cost_usd,
            )
            return response

        return self._instrument_stream(
            stream_obj=response,
            provider=provider_name,
            model=resolved_model,
            operation="completion",
            started=started,
        )

    def _instrument_stream(
        self,
        *,
        stream_obj: Any,
        provider: str,
        model: str,
        operation: str,
        started: float,
    ):
        def _generator():
            usage = None
            first_token_at = None
            ttft_emitted = False
            ended_at = started
            try:
                for chunk in stream_obj:
                    ended_at = time.perf_counter()
                    if not ttft_emitted and _extract_delta_content(chunk):
                        ttft = ended_at - started
                        observe_llm_ttft(provider=provider, model=model, seconds=ttft)
                        first_token_at = ended_at
                        ttft_emitted = True

                    chunk_usage = _extract_usage(chunk)
                    if chunk_usage is not None:
                        usage = chunk_usage

                    yield chunk
            except Exception:
                observe_llm_outcome(
                    operation=operation,
                    provider=provider,
                    model=model,
                    stream=True,
                    status="error",
                    duration_seconds=time.perf_counter() - started,
                )
                raise

            status = "success" if usage is not None else "usage_missing"
            total_duration = max(ended_at - started, 0.0)
            cost_usd = (
                estimate_cost_usd(
                    provider=provider,
                    model=model,
                    usage=usage,
                    operation=operation,
                )
                if usage is not None
                else None
            )
            observe_llm_outcome(
                operation=operation,
                provider=provider,
                model=model,
                stream=True,
                status=status,
                duration_seconds=total_duration,
                usage=usage,
                cost_usd=cost_usd,
            )

            if usage is not None and first_token_at is not None:
                completion_tokens = int(_field(usage, "completion_tokens", 0) or 0)
                output_elapsed = max(ended_at - first_token_at, 1e-6)
                if completion_tokens > 0:
                    observe_llm_output_speed(
                        provider=provider,
                        model=model,
                        tokens_per_second=completion_tokens / output_elapsed,
                    )

        return _generator()


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
        provider_name = resolved.provider.name
        resolved_model = resolved.model
        started = time.perf_counter()
        try:
            response = resolved.provider.embedding(
                model=resolved_model,
                input=input,
                **kwargs,
            )
        except Exception:
            observe_llm_outcome(
                operation="embedding",
                provider=provider_name,
                model=resolved_model,
                stream=False,
                status="error",
                duration_seconds=time.perf_counter() - started,
            )
            raise

        usage = _extract_usage(response)
        status = "success" if usage is not None else "usage_missing"
        cost_usd = (
            estimate_cost_usd(
                provider=provider_name,
                model=resolved_model,
                usage=usage,
                operation="embedding",
            )
            if usage is not None
            else None
        )
        observe_llm_outcome(
            operation="embedding",
            provider=provider_name,
            model=resolved_model,
            stream=False,
            status=status,
            duration_seconds=time.perf_counter() - started,
            usage=usage,
            cost_usd=cost_usd,
        )
        return response


class LLMClient:
    """Compatibility client with `.chat.completions.create` and `.embeddings.create`."""

    def __init__(self, registry: LLMProviderRegistry):
        self.chat = _ChatFacade(registry)
        self.embeddings = _EmbeddingFacade(registry)
        self.chat_provider = "dynamic"
        self.embedding_provider = "dynamic"
