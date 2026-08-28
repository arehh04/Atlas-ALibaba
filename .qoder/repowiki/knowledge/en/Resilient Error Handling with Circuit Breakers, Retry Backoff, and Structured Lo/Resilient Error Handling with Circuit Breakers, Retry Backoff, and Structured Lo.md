---
kind: error_handling
name: Resilient Error Handling with Circuit Breakers, Retry Backoff, and Structured Logging
category: error_handling
scope:
    - '**'
source_files:
    - travel-recovery-os/backend/middleware/resilience.py
    - travel-recovery-os/backend/api/dependencies.py
    - travel-recovery-os/backend/services/swarm_runner.py
    - travel-recovery-os/backend/services/llm_service.py
    - travel-recovery-os/backend/auth/rate_limiter.py
    - travel-recovery-os/backend/middleware/logging.py
    - travel-recovery-os/frontend/src/components/ErrorBoundary.vue
---

## Overview

SynapseAir implements a layered error-handling strategy across its FastAPI backend and Vue 3 frontend. The backend relies on **FastAPI's `HTTPException`** for request-layer errors, a custom **resilience layer** (`retry_with_backoff`, `CircuitBreaker`) for external service calls (LLMs, Atlas API, n8n), structured **structlog-based logging**, and per-node error tracking inside the LangGraph swarm pipeline. The frontend uses a Vue `ErrorBoundary` component to catch rendering errors and present user-friendly fallbacks.

## Backend Error Types and Propagation

- **Request-layer errors**: `fastapi.HTTPException` is raised in `backend/api/dependencies.py` for authentication failures (`401 Missing API key`, `401 Invalid or missing API key`), authorization failures (`403 Scope '...' required`), and rate limiting (`429 Rate limit exceeded` with `Retry-After` header). These are the only HTTP error responses produced by the API; there is no global exception handler overriding FastAPI's default JSON response shape.
- **Custom domain exceptions**: `CircuitBreakerOpen` (in `backend/middleware/resilience.py`) signals that a circuit breaker has tripped and requests should be fast-failed. It is caught at the call site (e.g., LLM services) and converted into a graceful fallback rather than propagated as an HTTP error.
- **Swarm-level errors**: `services/swarm_runner.py` wraps the entire LangGraph `astream` loop in a bare `except Exception` block. On failure it persists the error via `update_disruption_result(thread_id, hitl_status="ERROR", error_state=str(e))` and broadcasts a `WORKFLOW_ERROR` SSE event. Per-node errors are detected from `execution_logs` entries with `level == "ERROR"`; after `MAX_NODE_RETRIES` (2) consecutive node errors, the runner escalates via a dedicated broadcast event.
- **Agent modules** (`agents/*`) use `try/except ImportError` blocks around optional dependencies (e.g., `langchain`, `langgraph`) so agents degrade gracefully when optional packages are missing — they do not raise application errors but simply skip functionality.

## Resilience Layer: Retry + Circuit Breaker

`backend/middleware/resilience.py` defines two reusable primitives:

| Primitive | Purpose | Behavior |
|---|---|---|
| `retry_with_backoff(coro_factory, max_retries=3, base_delay=1.0, ...)` | Exponential backoff retry for async coroutines | Logs attempt counts, applies jitter, raises the last exception after exhaustion |
| `CircuitBreaker(name, failure_threshold, cooldown_seconds)` | State machine (CLOSED → OPEN → HALF_OPEN) | Raises `CircuitBreakerOpen` when open; transitions to HALF_OPEN after cooldown; resets on success |

Pre-configured instances exist for each external dependency: `deepseek_breaker`, `hermes_breaker`, `atlas_breaker`, `n8n_breaker`. They are consumed in `services/llm_service.py` where both Hermes extraction and DeepSeek route scoring wrap their HTTP calls with `breaker.call(retry_with_backoff(...))`. When any of these fail (including `CircuitBreakerOpen`), the service falls back to deterministic regex/scoring functions (`_fallback_regex_extraction`, `_fallback_deterministic_arbiter`) instead of surfacing an error to the caller.

## Authentication & Rate-Limiting Errors

`backend/api/dependencies.py` implements a three-tier auth chain (legacy static key → JWT → managed API key) via `verify_api_key`, raising `HTTPException(401)` at each stage if none match. `verify_scope(required_scope)` returns `403 Forbidden` when the authenticated identity lacks the required scope. `rate_limit_dependency` checks a Redis-backed (or in-memory) sliding window limiter and raises `HTTPException(429)` with `Retry-After` and `X-RateLimit-*` headers when exceeded.

## Structured Logging as Error Context

`backend/middleware/logging.py` configures `structlog` (with JSON renderer in production) and provides `get_logger()` and a `LogContext` context manager for binding fields like `thread_id` and `pnr` to every log line. The resilience module logs retries and circuit-breaker state transitions under the `synapseair.resilience` logger. This structured logging is how errors are surfaced for observability — there is no centralized error-reporting SDK.

## Frontend Error Handling

`frontend/src/components/ErrorBoundary.vue` is a Vue component that uses `onErrorCaptured` to intercept child component errors, renders a styled danger card with a configurable title/message, and exposes a `resetError()` button to clear the captured error. It does not call the backend — it handles client-side rendering/runtime errors locally.

## Conventions Observed

1. **External calls are never called directly** — they go through `retry_with_backoff` and a `CircuitBreaker` instance specific to that dependency.
2. **Failures are degraded, not failed** — LLM services always return a result dict even when the LLM is down, using deterministic fallbacks.
3. **HTTP errors are expressed as `HTTPException`** with explicit `status_code` constants from `starlette.status` (`HTTP_401_UNAUTHORIZED`, `HTTP_403_FORBIDDEN`, `HTTP_429_TOO_MANY_REQUESTS`).
4. **Swarm execution errors are persisted and streamed** — errors update the SQLite disruption record (`hitl_status="ERROR"`, `error_state`) and emit a `WORKFLOW_ERROR` SSE event; per-node errors emit `WORKFLOW_NODE_ERROR` events with retry counts.
5. **Optional dependencies are guarded** — agent modules wrap imports in `try/except ImportError` so missing packages do not crash startup.
6. **No global exception handler** is registered in `main.py`; FastAPI's default exception-to-JSON conversion is used.
7. **Rate limits include response headers** (`Retry-After`, `X-RateLimit-Remaining`, `X-RateLimit-Limit`) so clients can back off programmatically.