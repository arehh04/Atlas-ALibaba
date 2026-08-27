import shutil
from datetime import datetime
from fastapi import APIRouter

from backend.config import settings

router = APIRouter(tags=["system"])

@router.get("/health", summary="Detailed health check")
async def health():
    """Returns service health with individual provider statuses (DeepSeek, Hermes, n8n)."""
    return {
        "status": "online",
        "service": "SynapseAir Autonomous Disruption Swarm",
        "version": "2.0.0",
        "providers": {
            "deepseek": bool(settings.DEEPSEEK_API_KEY),
            "hermes_base": settings.HERMES_API_BASE,
            "n8n_configured": bool(settings.N8N_WEBHOOK_URL)
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/api/system/status", summary="Full system status")
async def get_system_status():
    """Returns dynamic health, active LLM model names, GDS status, and integration statuses."""
    atlas_cli = bool(shutil.which("atlas-flight"))
    
    return {
        "status": "HEALTHY",
        "deepseek": {
            "active": bool(settings.DEEPSEEK_API_KEY),
            "model": settings.DEEPSEEK_MODEL,
            "endpoint": settings.DEEPSEEK_BASE_URL
        },
        "hermes": {
            "active": bool(settings.HERMES_API_KEY),
            "model": settings.HERMES_MODEL,
            "endpoint": settings.HERMES_API_BASE
        },
        "atlas_gds": {
            "status": "LIVE_CLI_ACTIVE" if atlas_cli else "SANDBOX_GDS",
            "cli_installed": atlas_cli,
            "provider": "Official Atlas Flight Booking CLI (0.3.12)" if atlas_cli else "Atlas Sandbox API"
        },
        "n8n": {
            "status": "CONNECTED" if settings.N8N_WEBHOOK_URL else "SIMULATOR_RELAY",
            "webhook_target": settings.N8N_WEBHOOK_URL or "In-App WhatsApp Simulator",
            "api_connected": bool(settings.N8N_API_KEY)
        },
        "timestamp": datetime.now().isoformat()
    }
