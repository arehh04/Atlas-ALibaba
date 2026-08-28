---
kind: logging_system
name: Structured Logging with structlog and stdlib Fallback
category: logging_system
scope:
    - '**'
source_files:
    - travel-recovery-os/backend/middleware/logging.py
    - travel-recovery-os/backend/main.py
    - travel-recovery-os/backend/config.py
    - travel-recovery-os/backend/middleware/resilience.py
    - travel-recovery-os/backend/tools/atlas_client.py
---

## What system/approach is used

The backend uses **structlog** as the primary structured logging framework, with an automatic fallback to Python's stdlib `logging` when structlog is not installed. The middleware layer centralizes all logging configuration and provides a unified logger factory (`get_logger`) and context manager (`LogContext`) for per-request field binding.

- **Primary framework**: `structlog` (optional dependency) — configured with a processor pipeline that adds log level, ISO timestamp, stack info, Unicode decoding, and merges context variables from `structlog.contextvars`.
- **Fallback**: When structlog is unavailable, `setup_logging` falls back to `logging.basicConfig` with a plain text format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`.
- **Output sink**: All logs are written to `sys.stderr` via a single `StreamHandler` attached to the root logger.
- **Structured fields**: When structlog is active, every log line is emitted as JSON lines (production) or coloured console output (development), automatically including fields bound via `bind()` or `LogContext`.

## Key files and packages

- `backend/middleware/logging.py` — Core logging subsystem: `setup_logging`, `get_logger`, `LogContext`.
- `backend/main.py` — Application entry point; calls `setup_logging(...)` during FastAPI lifespan startup and obtains module-level loggers via `get_logger(__name__)`.
- `backend/config.py` — Declares `LOG_LEVEL` (default `INFO`) and `LOG_JSON` (default `False`) settings loaded from environment/`.env` profiles.
- `backend/middleware/resilience.py` — Uses stdlib `logging.getLogger("synapseair.resilience")` directly (bypasses structlog wrapper).
- `backend/tools/atlas_client.py` — Uses stdlib `logging.getLogger(__name__)` directly.

## Architecture and conventions

1. **Single initialization point**: `setup_logging(level, json_output, service_name)` is called once in the FastAPI lifespan (startup). It is idempotent via a `_configured` global flag — subsequent calls are no-ops.
2. **Environment-driven configuration**:
   - `LOG_LEVEL` env var controls numeric log level (resolved via `getattr(logging, level.upper(), logging.INFO)`).
   - `LOG_JSON` env var toggles between `JSONRenderer` (production) and `ConsoleRenderer(colors=sys.stderr.isatty())` (development).
   - Service name defaults to `"synapseair"` and can be passed through `service_name`.
3. **Logger acquisition pattern**: Modules obtain a logger via `from backend.middleware.logging import get_logger; logger = get_logger(__name__)`. This returns either a `structlog.stdlib.BoundLogger` or a stdlib `logging.Logger` depending on availability.
4. **Contextual field binding**: `LogContext(**fields)` is a context manager that temporarily binds extra fields into the structlog context using `structlog.contextvars.bind_contextvars`, automatically unbinding on exit. Example usage documented in the module docstring: `with LogContext(thread_id="abc123", pnr="SQ108"): logger.info("processing disruption")`.
5. **Processor chain** (when structlog is available):
   - `merge_contextvars` — pulls in context-bound fields.
   - `add_log_level` — injects the log level as a structured field.
   - `TimeStamper(fmt="iso")` — ISO-format timestamp.
   - `StackInfoRenderer` — includes stack traces.
   - `UnicodeDecoder` — decodes byte strings.
   - `ProcessorFormatter.wrap_for_formatter` — bridges structlog to stdlib handlers.
6. **Mixed usage observed**: Some modules (`resilience.py`, `atlas_client.py`) use `logging.getLogger(...)` directly rather than the centralized `get_logger`, which means they bypass structlog's structured output and fall back to plain text formatting. This is a deviation from the intended convention.
7. **Log levels used**: `info`, `warning`, `error` are observed across the codebase; `debug` is available but not actively used in production paths.

## Conventions and constraints

- **Always initialize via `setup_logging`**: Logging must be configured through `setup_logging` in the application lifespan; direct `basicConfig` calls elsewhere would conflict with the single-handler setup.
- **Use `get_logger(__name__)` for new modules**: New code should obtain loggers through the provided factory to ensure consistent behavior whether structlog is present or not.
- **Prefer `LogContext` for request-scoped fields**: To attach contextual metadata (e.g., `thread_id`, `pnr`, `request_id`) to all logs within a scope, wrap the block with `LogContext(...)` rather than passing fields manually.
- **Production vs development output**: Set `LOG_JSON=true` for structured JSON output suitable for log aggregation pipelines; leave it `false` for human-readable coloured console output during development.
- **No file sinks**: There are no file-based handlers configured — all output goes to stderr, relying on the container/runtime (Docker, systemd, etc.) to capture and forward logs.
- **No log rotation**: No rotation policy is implemented; log volume management is delegated to the deployment environment.