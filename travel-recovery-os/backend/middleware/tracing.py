"""
tracing.py - OpenTelemetry Instrumentation for SynapseAir

Provides:
  - ``init_tracing()`` -- initialise OTel TracerProvider with console + optional OTLP exporters
  - ``trace_span()``   -- context manager for ad-hoc spans
  - ``get_trace_context()`` -- extract trace_id / span_id for SSE propagation
  - ``trace_agent_node()`` / ``trace_llm_call()`` -- convenience decorators

Gracefully degrades to no-ops when the ``opentelemetry`` packages are not installed.
"""

import functools
import os
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

# ---------------------------------------------------------------------------
# Optional OpenTelemetry imports
# ---------------------------------------------------------------------------
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False

_tracer: Optional[Any] = None


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_tracing(
    app: Optional[Any] = None,
    service_name: str = "synapseair",
    otlp_endpoint: Optional[str] = None,
) -> None:
    """
    Set up the global TracerProvider.

    If *otlp_endpoint* (or ``OTEL_ENDPOINT`` env var) is set, an OTLP exporter
    is added alongside the console exporter.  When the OTel SDK is not
    installed this function is a no-op.
    """
    global _tracer
    if not _OTEL_AVAILABLE:
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # Always export to console in development
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    endpoint = otlp_endpoint or os.getenv("OTEL_ENDPOINT")
    if endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        )

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name)

    # Instrument FastAPI if an app instance is provided
    if app is not None:
        try:
            FastAPIInstrumentor.instrument_app(app)
        except Exception:
            pass  # Best-effort instrumentation


# ---------------------------------------------------------------------------
# Span helpers
# ---------------------------------------------------------------------------

@contextmanager
def trace_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager that creates an OTel span.

    Falls back to a plain no-op context manager when OTel is unavailable.
    """
    if not _OTEL_AVAILABLE or _tracer is None:
        yield {}
        return

    with _tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        yield span


def get_trace_context() -> Dict[str, str]:
    """
    Return ``{"trace_id": ..., "span_id": ...}`` for the current active span.

    Useful for embedding trace context in SSE events so the frontend can
    correlate UI actions with backend traces.
    """
    if not _OTEL_AVAILABLE:
        return {"trace_id": "", "span_id": ""}

    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.trace_id:
        return {
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
        }
    return {"trace_id": "", "span_id": ""}


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def trace_agent_node(agent_name: str):
    """Decorator that wraps an agent node function in a traced span."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            with trace_span(
                f"agent.{agent_name}",
                attributes={"agent.name": agent_name},
            ):
                return await fn(*args, **kwargs)
        return wrapper
    return decorator


def trace_llm_call(model_name: str, operation: str = "completion"):
    """Decorator that traces an LLM API call with model metadata."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            with trace_span(
                f"llm.{operation}",
                attributes={
                    "llm.model": model_name,
                    "llm.operation": operation,
                },
            ):
                return await fn(*args, **kwargs)
        return wrapper
    return decorator
