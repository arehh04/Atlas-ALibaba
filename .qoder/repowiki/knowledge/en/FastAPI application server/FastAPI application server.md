---
kind: external_dependency
name: FastAPI application server
slug: fastapi
category: external_dependency
category_hints:
    - framework_behavior
scope:
    - '**'
source_files:
    - backend/main.py
    - backend/middleware/logging.py
    - backend/middleware/tracing.py
---

### Role
Web framework hosting REST endpoints (`/webhook/*`, `/stream/*`, `/threads/*`, `/api/*`, `/health`) plus OpenAPI docs.

### Integration shape
- App assembled in `backend/main.py` with lifespan hooks, middleware registration (logging, tracing, resilience), and router mounting.
- CORS is configured per-origin; development mode sets `allow_origins=["*"]` to accommodate dynamic Vite dev ports.

### Stable gotchas
- Structlog logger calls must pass positional `%s` format strings, not keyword args (stdlib Logger compatibility).
- Stale uvicorn processes on port 8000 must be killed before restart.