"""Thin span helpers that co-emit OTel spans + existing Prometheus metrics."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any

from observability.context import (
    get_agent_name,
    get_chat_type,
    get_project_hash,
    get_session_hash,
    get_user_hash,
)
from observability.tracing import get_tracer

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _set_context_attributes(span) -> None:
    """Copy observability ContextVars onto span attributes."""
    span.set_attribute("chat.type", get_chat_type())
    span.set_attribute("user.hash", get_user_hash())
    span.set_attribute("session.hash", get_session_hash())
    span.set_attribute("project.hash", get_project_hash())
    span.set_attribute("agent.name", get_agent_name())


def _safe_set(span, key: str, value: Any) -> None:
    if value is not None:
        span.set_attribute(key, value)


# ---------------------------------------------------------------------------
# Public context-manager helpers
# ---------------------------------------------------------------------------

@contextmanager
def chat_turn_span(*, span_name: str, chat_type: str):
    """Root span for a chat turn (general or project)."""
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span(span_name) as span:
        _set_context_attributes(span)
        span.set_attribute("chat.type", chat_type)
        yield span


@contextmanager
def agent_route_span(*, route_mode: str):
    """Span wrapping agent routing (classify + select).

    Caller is responsible for emitting ``observe_agent_route`` — this helper
    only manages the span so that the existing metric call-sites stay intact.
    """
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span("agent.route") as span:
        _set_context_attributes(span)
        span.set_attribute("route.mode", route_mode)
        yield span


@contextmanager
def classify_intent_span():
    """Child span for the classification LLM call inside agent routing."""
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span("agent.classify_intent") as span:
        span.set_attribute("gen_ai.operation.name", "classify")
        yield span


@contextmanager
def llm_completion_span(
    *,
    provider: str,
    model: str,
    stream: bool,
    operation: str = "completion",
):
    """Span wrapping an LLM completion or embedding call.

    For streaming, the caller should keep the context manager open for the
    generator's full lifetime (enter before yielding, exit in ``finally``).
    """
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span(f"llm.{operation}") as span:
        _set_context_attributes(span)
        span.set_attribute("gen_ai.system", provider)
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("stream", stream)
        yield span


def record_llm_usage(span, *, usage: Any, cost_usd: float | None, status: str) -> None:
    """Set final attributes on an LLM span after completion."""
    if span is None:
        return
    _safe_set(span, "status", status)
    if usage is not None:
        from llm.client import _field
        prompt = int(_field(usage, "prompt_tokens", 0) or 0)
        completion = int(_field(usage, "completion_tokens", 0) or 0)
        _safe_set(span, "gen_ai.usage.input_tokens", prompt)
        _safe_set(span, "gen_ai.usage.output_tokens", completion)
    if cost_usd is not None and cost_usd > 0:
        span.set_attribute("cost.usd", cost_usd)


def record_ttft_event(span, *, ttft_seconds: float) -> None:
    """Add a span event marking time-to-first-token."""
    if span is None:
        return
    span.add_event("ttft", attributes={"ttft.seconds": ttft_seconds})


@contextmanager
def retrieval_span(*, span_name: str = "retrieval.pipeline", **attrs):
    """Span for retrieval pipeline or sub-steps."""
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span(span_name) as span:
        _set_context_attributes(span)
        for k, v in attrs.items():
            _safe_set(span, k, v)
        yield span


@contextmanager
def tool_span(*, tool_name: str):
    """Span wrapping a single tool execution."""
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span("tool.execute") as span:
        _set_context_attributes(span)
        span.set_attribute("tool.name", tool_name)
        yield span


@contextmanager
def ingestion_span(*, span_name: str = "ingestion.document", **attrs):
    """Span for document ingestion pipeline or sub-steps."""
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span(span_name) as span:
        for k, v in attrs.items():
            _safe_set(span, k, v)
        yield span
