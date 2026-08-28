"""
main.py - SynapseAir FastAPI Engine with Hermes, DeepSeek LLM & n8n Gateway

Phase 4: Added lifespan manager, new routers (WebSocket, History),
         structured logging, OpenTelemetry tracing, and health endpoint.
"""

import os
from contextlib import asynccontextmanager

from backend.api.routers import history, system, telemetry, tests, webhooks, websocket
from backend.auth.rate_limiter import get_rate_limiter
from backend.middleware.logging import get_logger, setup_logging
from backend.middleware.tracing import init_tracing
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the FastAPI application."""
    # ── Startup ──────────────────────────────────────────────────────────
    setup_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        json_output=os.getenv("LOG_JSON", "false").lower() == "true",
        service_name="synapseair",
    )
    init_tracing(app=app, service_name="synapseair")
    logger.info("SynapseAir engine starting: environment=%s", os.getenv("ENVIRONMENT", "development"))
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────
    limiter = get_rate_limiter()
    await limiter.close()
    logger.info("SynapseAir engine stopped")


app = FastAPI(
    title="SynapseAir API",
    description=(
        "## SynapseAir Travel Recovery OS\n\n"
        "Autonomous multi-agent flight disruption recovery system powered by a LangGraph swarm "
        "of specialized AI agents (Sentinel → Profile → Scout → Arbiter → Executor).\n\n"
        "### Key Features\n"
        "- **Real-time SSE/WebSocket telemetry** — stream agent decisions live\n"
        "- **Human-in-the-Loop (HITL)** — passenger approval via WhatsApp/n8n or in-app\n"
        "- **Hermes AI** — natural language flight alert parsing\n"
        "- **DeepSeek AI** — route scoring and decision rationale\n"
        "- **Atlas GDS** — live flight search and booking\n\n"
        "### Authentication\n"
        "All webhook and data endpoints require a Bearer token in the `Authorization` header."
    ),
    version="2.1.0",
    lifespan=lifespan,
    contact={
        "name": "SynapseAir Team",
        "url": "https://github.com/synapseair",
    },
    license_info={
        "name": "MIT",
    },
    tags_metadata=[
        {"name": "system", "description": "Health checks and system status endpoints."},
        {"name": "webhooks", "description": "Disruption ingestion and passenger consensus (HITL) endpoints."},
        {"name": "telemetry", "description": "SSE streaming and thread state inspection."},
        {"name": "history", "description": "Query past disruption events and aggregate analytics."},
        {"name": "websocket", "description": "Bidirectional WebSocket for real-time telemetry and HITL."},
        {"name": "tests", "description": "Debug/test endpoints (non-production only)."},
    ],
)

# ---------------------------------------------------------------------------
# CORS Configuration for Vue 3 Frontend
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
]

_frontend_url = os.getenv("FRONTEND_URL")
if _frontend_url:
    ALLOWED_ORIGINS.append(_frontend_url)

# In development, allow all localhost origins (Vite may pick dynamic ports)
_use_regex = os.getenv("ENVIRONMENT", "development") == "development"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if not _use_regex else ["*"],
    allow_credentials=True if not _use_regex else False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Include Routers
# ---------------------------------------------------------------------------
app.include_router(system.router)
app.include_router(webhooks.router)
app.include_router(telemetry.router)
app.include_router(history.router)
app.include_router(websocket.router)

# Test/debug endpoints are only mounted in non-production environments
# to avoid exposing /api/test/* routes to end users.
if os.getenv("ENVIRONMENT", "development") != "production":
    app.include_router(tests.router)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"], summary="Quick health check")
async def health_check():
    """Lightweight health check returning service status and version."""
    return {"status": "healthy", "version": app.version}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
