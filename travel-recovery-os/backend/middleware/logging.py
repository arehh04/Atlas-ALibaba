"""
logging.py - Structured Logging for SynapseAir

Provides:
  - ``setup_logging()`` -- configure structlog (JSON or console renderer)
  - ``get_logger()``    -- return a BoundLogger (or stdlib fallback)
  - ``LogContext``      -- context manager for temporary log field bindings

Gracefully falls back to Python stdlib ``logging`` when ``structlog`` is not installed.
"""

import logging
import sys
from contextlib import contextmanager
from typing import Any

# ---------------------------------------------------------------------------
# Optional structlog import
# ---------------------------------------------------------------------------
try:
    import structlog
    from structlog.types import BoundLogger

    _STRUCTLOG_AVAILABLE = True
except ImportError:
    _STRUCTLOG_AVAILABLE = False

_configured = False
_loggers: dict = {}


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def setup_logging(
    level: str = "INFO",
    json_output: bool = False,
    service_name: str = "synapseair",
) -> None:
    """
    Configure the logging subsystem.

    When ``structlog`` is available, processors are chained to produce either
    JSON lines (production) or coloured console output (development).  When
    structlog is unavailable, a standard ``logging.basicConfig`` call is used.
    """
    global _configured
    if _configured:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    if _STRUCTLOG_AVAILABLE:
        shared_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
        ]

        if json_output:
            renderer = structlog.processors.JSONRenderer()
        else:
            renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

        structlog.configure(
            processors=[
                *shared_processors,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)

        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(numeric_level)
    else:
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stderr,
        )

    _configured = True


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------

def get_logger(name: str | None = None, **bind_kwargs: Any):
    """
    Return a structured logger bound with *bind_kwargs*.

    Falls back to a plain ``logging.Logger`` when structlog is unavailable.
    """
    if not _STRUCTLOG_AVAILABLE:
        return logging.getLogger(name or __name__)

    logger = structlog.get_logger(name)
    if bind_kwargs:
        logger = logger.bind(**bind_kwargs)
    return logger


# ---------------------------------------------------------------------------
# Context binding
# ---------------------------------------------------------------------------

@contextmanager
def LogContext(**fields: Any):
    """
    Temporarily bind extra fields to the structlog context.

    Usage::

        with LogContext(thread_id="abc123", pnr="SQ108"):
            logger.info("processing disruption")
    """
    if not _STRUCTLOG_AVAILABLE:
        yield
        return

    import structlog.contextvars as ctx

    ctx.bind_contextvars(**fields)
    try:
        yield
    finally:
        ctx.unbind_contextvars(*fields.keys())
