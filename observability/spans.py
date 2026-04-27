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
    """Root span for a chat turn (general or project).

    Uses start_span instead of start_as_current_span so the ContextVar token
    is never attached/detached across asyncio yield boundaries.
    """
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    span = tracer.start_span(span_name)
    try:
        _set_context_attributes(span)
        span.set_attribute("chat.type", chat_type)
        yield span
    finally:
        span.end()


@contextmanager
def agent_route_span(*, route_mode: str):
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    span = tracer.start_span("agent.route")
    try:
        _set_context_attributes(span)
        span.set_attribute("route.mode", route_mode)
        yield span
    finally:
        span.end()


@contextmanager
def classify_intent_span():
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    span = tracer.start_span("agent.classify_intent")
    try:
        span.set_attribute("gen_ai.operation.name", "classify")
        yield span
    finally:
        span.end()


@contextmanager
def llm_completion_span(
    *,
    provider: str,
    model: str,
    stream: bool,
    operation: str = "completion",
):
    """Span wrapping an LLM completion or embedding call.

    Uses start_span so it is safe to hold open across sync generator yields
    without triggering ContextVar token errors on detach.
    The span is ended explicitly via span.end() — callers must NOT call
    span_ctx.__exit__() themselves; record_llm_usage before the span ends.
    """
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    span = tracer.start_span(f"llm.{operation}")
    try:
        _set_context_attributes(span)
        span.set_attribute("gen_ai.system", provider)
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("stream", stream)
        yield span
    finally:
        span.end()


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
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    span = tracer.start_span(span_name)
    try:
        _set_context_attributes(span)
        for k, v in attrs.items():
            _safe_set(span, k, v)
        yield span
    finally:
        span.end()


@contextmanager
def tool_span(*, tool_name: str):
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    span = tracer.start_span("tool.execute")
    try:
        _set_context_attributes(span)
        span.set_attribute("tool.name", tool_name)
        yield span
    finally:
        span.end()


@contextmanager
def ingestion_span(*, span_name: str = "ingestion.document", **attrs):
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    span = tracer.start_span(span_name)
    try:
        for k, v in attrs.items():
            _safe_set(span, k, v)
        yield span
    finally:
        span.end()


@contextmanager
def memory_extraction_span(*, phase: str, **attrs):
    """Span for the atomic memory extraction pipeline.

    ``phase`` is one of: ``extract``, ``embed``, ``consolidate``, ``persist``, ``summary``.
    """
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    span = tracer.start_span(f"memory.{phase}")
    try:
        _set_context_attributes(span)
        span.set_attribute("memory.phase", phase)
        for k, v in attrs.items():
            _safe_set(span, k, v)
        yield span
    finally:
        span.end()
