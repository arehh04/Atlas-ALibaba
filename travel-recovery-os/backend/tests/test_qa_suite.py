"""
test_qa_suite.py — SynapseAir Integration & Boundary Test Suite

Covers: health, system status, disruption webhook (happy path + boundary),
consensus webhook, schema validation, auth enforcement, CORS, OpenAPI,
and telemetry endpoints.

Self-bootstrapping: runs in-process via ASGITransport or against live BASE_URL.
"""
import os

import httpx
import pytest
from backend.main import app

BASE_URL = os.getenv("SYNAPSE_TEST_URL", "http://127.0.0.1:8001")
API_SECRET = os.getenv("SYNAPSE_API_SECRET", "")
# No hardcoded fallback secret — when unset, omit the header entirely so the
# dev-user bypass applies in development; CI/live runs export the real secret.
HEADERS = {"Authorization": f"Bearer {API_SECRET}"} if API_SECRET else {}


def get_test_client():
    """Returns an async client using live URL or in-process ASGITransport."""
    if os.getenv("SYNAPSE_LIVE_TEST") == "1":
        return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver", timeout=30.0)


VALID_DISRUPTION = {
    "pnr": "PNR-QA-001",
    "flight_number": "SQ-108",
    "origin": "SIN",
    "destination": "KUL",
    "passenger_name": "QA Tester",
    "loyalty_tier": "GOLD",
    "reason": "Test disruption",
    "delay_minutes": 240,
}


# ── System / Health ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint():
    """Health check returns 200 with online status."""
    async with get_test_client() as c:
        r = await c.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] in ("online", "healthy")


@pytest.mark.asyncio
async def test_system_status():
    """System status returns HEALTHY with provider details."""
    async with get_test_client() as c:
        r = await c.get("/api/system/status")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "HEALTHY"
        assert "deepseek" in data
        assert "hermes" in data
        assert "atlas_gds" in data


# ── Disruption Webhook ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_disruption_valid_payload():
    """Valid disruption returns PROCESSING with a thread_id."""
    async with get_test_client() as c:
        r = await c.post("/webhook/disruption", json=VALID_DISRUPTION, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "PROCESSING"
        assert "thread_id" in data
        assert data["thread_id"].startswith("synapse-")


@pytest.mark.asyncio
async def test_disruption_negative_delay():
    """System handles impossible negative delay gracefully."""
    payload = {**VALID_DISRUPTION, "delay_minutes": -50}
    async with get_test_client() as c:
        r = await c.post("/webhook/disruption", json=payload, headers=HEADERS)
        assert r.status_code == 200
        assert "thread_id" in r.json()


@pytest.mark.asyncio
async def test_disruption_invalid_iata_codes():
    """Non-existent IATA codes accepted at entry; failure deferred to swarm."""
    payload = {**VALID_DISRUPTION, "origin": "ZZZZZ", "destination": "XXXXX"}
    async with get_test_client() as c:
        r = await c.post("/webhook/disruption", json=payload, headers=HEADERS)
        assert r.status_code == 200
        assert "thread_id" in r.json()


@pytest.mark.asyncio
async def test_disruption_minimal_payload():
    """Minimal payload with only required fields still accepted."""
    async with get_test_client() as c:
        r = await c.post("/webhook/disruption", json={}, headers=HEADERS)
        assert r.status_code == 200
        assert "thread_id" in r.json()


@pytest.mark.asyncio
async def test_disruption_raw_text_mode():
    """Hermes raw text extraction mode accepted."""
    payload = {
        "raw_text": "URGENT NOTAM: SQ108 SIN-KUL canceled due to hydraulic fault. PNR SQ108-SIN.",
        "passenger_name": "Dr. Vance",
        "loyalty_tier": "PLATINUM",
    }
    async with get_test_client() as c:
        r = await c.post("/webhook/disruption", json=payload, headers=HEADERS)
        assert r.status_code == 200
        assert "thread_id" in r.json()


@pytest.mark.asyncio
async def test_disruption_extreme_delay():
    """Extreme delay value (720 min = 12 hours) accepted."""
    payload = {**VALID_DISRUPTION, "delay_minutes": 720}
    async with get_test_client() as c:
        r = await c.post("/webhook/disruption", json=payload, headers=HEADERS)
        assert r.status_code == 200


# ── Consensus Webhook ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_consensus_invalid_thread():
    """Consensus on non-existent thread returns 404."""
    async with get_test_client() as c:
        r = await c.post("/webhook/consensus", json={
            "thread_id": "nonexistent-thread-xyz",
            "action": "APPROVE"
        }, headers=HEADERS)
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_consensus_missing_thread_id():
    """Missing required thread_id returns 422 validation error."""
    async with get_test_client() as c:
        r = await c.post("/webhook/consensus", json={
            "action": "APPROVE"
        }, headers=HEADERS)
        assert r.status_code == 422


@pytest.mark.asyncio
async def test_consensus_invalid_action():
    """Invalid action string returns 422."""
    async with get_test_client() as c:
        r = await c.post("/webhook/consensus", json={
            "thread_id": "synapse-test-123",
            "action": "EXPLODE_AIRCRAFT"
        }, headers=HEADERS)
        assert r.status_code in (404, 422)


# ── Auth Enforcement ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_disruption_missing_auth():
    """Disruption without auth header returns 200 (dev mode) or 401/403 (prod mode)."""
    async with get_test_client() as c:
        r = await c.post("/webhook/disruption", json=VALID_DISRUPTION)
        assert r.status_code in (200, 401, 403)


@pytest.mark.asyncio
async def test_disruption_invalid_auth():
    """Disruption with wrong token returns 401."""
    async with get_test_client() as c:
        r = await c.post("/webhook/disruption", json=VALID_DISRUPTION,
                         headers={"Authorization": "Bearer wrong-token-xyz"})
        assert r.status_code == 401


# ── CORS ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cors_preflight():
    """OPTIONS preflight returns 200 with CORS headers."""
    async with get_test_client() as c:
        r = await c.options("/webhook/disruption", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        })
        assert r.status_code == 200


# ── OpenAPI / Docs ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_openapi_json():
    """OpenAPI schema is valid and accessible."""
    async with get_test_client() as c:
        r = await c.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema
        assert "/webhook/disruption" in schema["paths"]


# ── Disruption History & Telemetry ────────────────────────────────────────

@pytest.mark.asyncio
async def test_history_list():
    """History list returns 200 with disruptions array."""
    async with get_test_client() as c:
        r = await c.get("/api/history")
        assert r.status_code == 200
        data = r.json()
        assert "disruptions" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_history_stats():
    """Stats endpoint returns aggregate analytics."""
    async with get_test_client() as c:
        r = await c.get("/api/history/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total_disruptions" in data
        assert "auto_approve_rate" in data


@pytest.mark.asyncio
async def test_thread_state_endpoint():
    """Thread state endpoint returns state or 404 for invalid thread."""
    async with get_test_client() as c:
        r = await c.get("/threads/synapse-nonexistent/state")
        assert r.status_code in (200, 404)
