"""
middleware/resilience.py - Retry and Circuit Breaker Patterns

Provides:
1. retry_with_backoff: Exponential backoff wrapper for async coroutines.
2. CircuitBreaker: State machine (CLOSED/OPEN/HALF_OPEN) that fast-fails
   after repeated failures and recovers after a cooldown period.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger("synapseair.resilience")

T = TypeVar("T")


# ---------------------------------------------------------------------------
# 1. Retry with Exponential Backoff
# ---------------------------------------------------------------------------
async def retry_with_backoff(
    coro_factory: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 15.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,),
    operation_name: str = "operation",
) -> Any:
    """
    Executes an async coroutine factory with exponential backoff retry.

    Args:
        coro_factory: A callable that returns an awaitable coroutine.
                      Must be a factory (not a coroutine) so it can be re-invoked.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        exponential_base: Multiplier for exponential growth.
        jitter: If True, adds random jitter to avoid thundering herd.
        retryable_exceptions: Tuple of exception types that trigger retry.
        operation_name: Human-readable name for logging.

    Returns:
        The result of the coroutine.

    Raises:
        The last exception if all retries are exhausted.
    """
    import random

    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await coro_factory()
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (exponential_base ** attempt), max_delay)
                if jitter:
                    delay = delay * (0.5 + random.random() * 0.5)

                logger.warning(
                    "[%s] Attempt %d/%d failed: %s. Retrying in %.1fs...",
                    operation_name, attempt + 1, max_retries + 1, str(e)[:100], delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "[%s] All %d attempts exhausted. Last error: %s",
                    operation_name, max_retries + 1, str(e)[:200],
                )

    raise last_exception  # type: ignore


# ---------------------------------------------------------------------------
# 2. Circuit Breaker
# ---------------------------------------------------------------------------
class CircuitState(Enum):
    CLOSED = "CLOSED"        # Normal operation, requests pass through
    OPEN = "OPEN"            # Failures exceeded threshold, requests fast-fail
    HALF_OPEN = "HALF_OPEN"  # Cooldown expired, testing with a single request


class CircuitBreakerOpen(Exception):
    """Raised when the circuit breaker is OPEN and rejecting requests."""


class CircuitBreaker:
    """
    Async circuit breaker with three states:

    - CLOSED: Requests pass through. Failures are counted.
    - OPEN: Requests fast-fail with CircuitBreakerOpen. Transitions to
      HALF_OPEN after cooldown_seconds elapse.
    - HALF_OPEN: One probe request is allowed through. Success resets
      to CLOSED; failure reopens to OPEN.

    Usage:
        breaker = CircuitBreaker(name="deepseek_llm", failure_threshold=3)

        try:
            result = await breaker.call(some_async_fn, arg1, arg2)
        except CircuitBreakerOpen:
            result = fallback_fn()
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Returns the current state, auto-transitioning OPEN -> HALF_OPEN on cooldown expiry."""
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info(
                    "[CircuitBreaker:%s] Cooldown expired (%.0fs). Transitioning to HALF_OPEN.",
                    self.name, elapsed,
                )
        return self._state

    async def call(self, coro_factory: Callable[[], Any], *args, **kwargs) -> Any:
        """
        Executes a coroutine through the circuit breaker.

        Args:
            coro_factory: An async callable (coroutine function or lambda).

        Returns:
            The coroutine result.

        Raises:
            CircuitBreakerOpen: If the circuit is OPEN and cooldown hasn't elapsed.
        """
        current_state = self.state

        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpen(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"{self._failure_count} consecutive failures."
            )

        if current_state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' is HALF_OPEN but probe limit reached."
                )
            self._half_open_calls += 1

        try:
            result = await coro_factory()
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        """Handles a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            logger.info(
                "[CircuitBreaker:%s] Probe succeeded. Closing circuit.", self.name
            )
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count += 1

    def _on_failure(self):
        """Handles a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._state == CircuitState.HALF_OPEN:
            logger.warning(
                "[CircuitBreaker:%s] Probe failed. Reopening circuit.", self.name
            )
            self._state = CircuitState.OPEN
        elif self._failure_count >= self.failure_threshold:
            logger.warning(
                "[CircuitBreaker:%s] Failure threshold reached (%d). Opening circuit.",
                self.name, self._failure_count,
            )
            self._state = CircuitState.OPEN

    def reset(self):
        """Manually resets the circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0


# ---------------------------------------------------------------------------
# Pre-built Circuit Breakers for SynapseAir Services
# ---------------------------------------------------------------------------
deepseek_breaker = CircuitBreaker(
    name="deepseek_llm",
    failure_threshold=3,
    cooldown_seconds=60.0,
)

hermes_breaker = CircuitBreaker(
    name="hermes_llm",
    failure_threshold=3,
    cooldown_seconds=45.0,
)

atlas_breaker = CircuitBreaker(
    name="atlas_api",
    failure_threshold=5,
    cooldown_seconds=30.0,
)

n8n_breaker = CircuitBreaker(
    name="n8n_webhook",
    failure_threshold=3,
    cooldown_seconds=30.0,
)
