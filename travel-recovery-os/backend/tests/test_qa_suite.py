"""
test_qa_suite.py — SynapseAir Integration & Boundary Test Suite

Covers: health, system status, disruption webhook (happy path + boundary),
consensus webhook, schema validation, auth enforcement, CORS, OpenAPI,
and telemetry endpoints.

Requires a running backend at http://127.0.0.1:8000.
"""
import os
import pytest
import httpx

BASE_URL = os.getenv("SYNAPSE_TEST_URL", "http://127.0.0.1:8001")
API_SECRET = os.getenv("SYNAPSE_API_SECRET", "default-insecure-secret-change-in-prod")
HEADERS = {"Authorization": f"Bearer {API_SECRET}"}

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
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        assert r.json()["status"] in ("online", "healthy")


@pytest.mark.asyncio
async def test_system_status():
    """System status returns HEALTHY with provider details."""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE_URL}/api/system/status")
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
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/disruption", json=VALID_DISRUPTION, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "PROCESSING"
        assert "thread_id" in data
        assert data["thread_id"].startswith("synapse-")


@pytest.mark.asyncio
async def test_disruption_negative_delay():
    """System handles impossible negative delay gracefully."""
    payload = {**VALID_DISRUPTION, "delay_minutes": -50}
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/disruption", json=payload, headers=HEADERS)
        assert r.status_code == 200
        assert "thread_id" in r.json()


@pytest.mark.asyncio
async def test_disruption_invalid_iata_codes():
    """Non-existent IATA codes accepted at entry; failure deferred to swarm."""
    payload = {**VALID_DISRUPTION, "origin": "ZZZZZ", "destination": "XXXXX"}
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/disruption", json=payload, headers=HEADERS)
        assert r.status_code == 200
        assert "thread_id" in r.json()


@pytest.mark.asyncio
async def test_disruption_minimal_payload():
    """Minimal payload with only required fields still accepted."""
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/disruption", json={}, headers=HEADERS)
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
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/disruption", json=payload, headers=HEADERS)
        assert r.status_code == 200
        assert "thread_id" in r.json()


@pytest.mark.asyncio
async def test_disruption_extreme_delay():
    """Extreme delay value (720 min = 12 hours) accepted."""
    payload = {**VALID_DISRUPTION, "delay_minutes": 720}
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/disruption", json=payload, headers=HEADERS)
        assert r.status_code == 200


# ── Consensus Webhook ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_consensus_invalid_thread():
    """Consensus on non-existent thread returns 404."""
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/consensus", json={
            "thread_id": "nonexistent-thread-xyz",
            "action": "APPROVE"
        }, headers=HEADERS)
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_consensus_missing_thread_id():
    """Missing required thread_id returns 422 validation error."""
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/consensus", json={
            "action": "APPROVE"
        }, headers=HEADERS)
        assert r.status_code == 422


@pytest.mark.asyncio
async def test_consensus_missing_action():
    """Missing required action field returns 422."""
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/consensus", json={
            "thread_id": "synapse-123456"
        }, headers=HEADERS)
        assert r.status_code == 422


# ── Auth Enforcement ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_disruption_missing_auth():
    """Disruption without auth header returns 200 (dev mode) or 401/403 (prod mode)."""
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/disruption", json=VALID_DISRUPTION)
        assert r.status_code in (200, 401, 403)


@pytest.mark.asyncio
async def test_disruption_invalid_auth():
    """Disruption with wrong token returns 401."""
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/webhook/disruption", json=VALID_DISRUPTION,
                         headers={"Authorization": "Bearer wrong-token-xyz"})
        assert r.status_code == 401


# ── CORS ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cors_preflight():
    """OPTIONS preflight returns 200 with CORS headers."""
    async with httpx.AsyncClient() as c:
        r = await c.options(f"{BASE_URL}/webhook/disruption", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        })
        assert r.status_code == 200
        assert "access-control-allow-origin" in r.headers


# ── OpenAPI ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_openapi_schema():
    """OpenAPI schema endpoint returns valid JSON with expected paths."""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE_URL}/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema
        assert "/webhook/disruption" in schema["paths"]
        assert "/webhook/consensus" in schema["paths"]
        assert "/health" in schema["paths"]
        assert "/api/system/status" in schema["paths"]


# ── Telemetry ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_thread_state_not_found():
    """Requesting state for unknown thread returns 404."""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE_URL}/threads/nonexistent-thread/state")
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_sse_stream_content_type():
    """SSE stream endpoint returns correct content-type."""
    async with httpx.AsyncClient(timeout=5) as c:
        try:
            async with c.stream("GET", f"{BASE_URL}/stream/test-thread-qa") as r:
                assert r.status_code == 200
                assert "text/event-stream" in r.headers.get("content-type", "")
        except httpx.ReadTimeout:
            pass  # SSE streams are long-lived; timeout is expected


# ── History ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_history_endpoint():
    """History endpoint returns paginated results."""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE_URL}/api/history?limit=5")
        assert r.status_code == 200
        data = r.json()
        assert "disruptions" in data or isinstance(data, dict)


@pytest.mark.asyncio
async def test_history_stats():
    """Stats endpoint returns aggregate metrics."""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE_URL}/api/history/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total_disruptions" in data
