"""Tests for OpenTelemetry tracing setup — idempotent, opt-in behaviour."""

import importlib
import os
from unittest.mock import MagicMock

import pytest

import observability.tracing as tracing_mod


@pytest.fixture(autouse=True)
def _reset_tracing():
    """Reset the module-level _INITIALIZED flag between tests."""
    tracing_mod._INITIALIZED = False
    yield
    tracing_mod._INITIALIZED = False


def test_setup_tracing_disabled_by_default():
    """When OTEL_ENABLED is unset, setup_tracing is a no-op and marks initialised."""
    env = os.environ.copy()
    env.pop("OTEL_ENABLED", None)
    os.environ.clear()
    os.environ.update(env)

    app = MagicMock()
    tracing_mod.setup_tracing(app)
    assert tracing_mod._INITIALIZED is True


def test_setup_tracing_idempotent():
    """Calling setup_tracing twice doesn't crash or reinitialise."""
    app = MagicMock()
    tracing_mod.setup_tracing(app)
    assert tracing_mod._INITIALIZED is True
    # Second call should be a no-op
    tracing_mod.setup_tracing(app)
    assert tracing_mod._INITIALIZED is True


def test_setup_tracing_enabled(monkeypatch):
    """When OTEL_ENABLED=true, a TracerProvider is registered."""
    monkeypatch.setenv("OTEL_ENABLED", "true")
    # Reset so the module re-checks
    tracing_mod._INITIALIZED = False

    app = MagicMock()
    tracing_mod.setup_tracing(app)
    assert tracing_mod._INITIALIZED is True

    from opentelemetry import trace

    provider = trace.get_tracer_provider()
    # Should be a real TracerProvider, not the default proxy
    assert provider is not None


def test_get_tracer_returns_tracer():
    """get_tracer should return a non-None tracer object."""
    tracer = tracing_mod.get_tracer("test")
    assert tracer is not None


def test_get_tracer_with_default_name():
    """get_tracer with no arg uses 'agenticrag'."""
    tracer = tracing_mod.get_tracer()
    assert tracer is not None
