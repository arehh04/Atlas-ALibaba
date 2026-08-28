import uuid
from datetime import datetime

from backend.schemas.api_models import PassengerChatPayload, RawTextTestPayload
from backend.services.llm_service import extract_disruption_with_hermes
from backend.services.n8n_service import (
    answer_passenger_question,
    dispatch_hitl_to_n8n,
    get_n8n_event_log,
)
from backend.tools.atlas_client import issue_ticket, search_alternative_flights
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["tests", "n8n_mocks"])

@router.post("/test/hermes")
async def test_hermes_endpoint(payload: RawTextTestPayload):
    """Test endpoint for Hermes unstructured extraction."""
    extracted = await extract_disruption_with_hermes(payload.raw_text)
    return {"status": "success", "extracted": extracted}

@router.get("/test/atlas/search")
async def test_atlas_search(origin: str = "KUL", destination: str = "HGH", date: str = "2026-08-25"):
    """Test endpoint for Atlas Sandbox flight inventory search."""
    routes = await search_alternative_flights(origin, destination, date)
    return {
        "status": "success",
        "provider": "Atlas Sandbox GDS API",
        "origin": origin,
        "destination": destination,
        "candidate_count": len(routes),
        "flights": routes
    }

@router.post("/test/atlas/ticket")
async def test_atlas_ticket(pnr: str = "PNR-DEMO-88", flight_id: str = "ATLAS-3042"):
    """Test endpoint for Atlas automated e-ticketing issuance."""
    receipt = await issue_ticket(pnr, flight_id)
    return {
        "status": "success",
        "provider": "Atlas Rebooking Engine",
        "ticket": receipt
    }

@router.post("/test/n8n")
async def test_n8n_endpoint(custom_url: str | None = None):
    """Test endpoint for outbound n8n WhatsApp webhook dispatch."""
    receipt = await dispatch_hitl_to_n8n(
        thread_id=f"test-{uuid.uuid4().hex[:6]}",
        pnr="PNR-DEMO-99",
        passenger_context={"passenger_name": "Sarah Jenkins", "phone_number": "+60 12-345 6789"},
        selected_route={"flight_number": "CZ-3042", "airline": "China Southern Airlines", "departure_time": "14:30"},
        whatsapp_message="Test message from SynapseAir",
        custom_n8n_url=custom_url
    )
    return receipt

@router.get("/n8n/events")
async def get_n8n_events_endpoint():
    """Returns the live audit log of n8n webhook dispatches and interactions."""
    events = get_n8n_event_log()
    return {"total": len(events), "events": events}

@router.post("/n8n/chat")
async def passenger_whatsapp_chat(payload: PassengerChatPayload):
    """Handles conversational questions asked by the passenger in the WhatsApp simulator."""
    reply = await answer_passenger_question(
        passenger_message=payload.passenger_message,
        passenger_name=payload.passenger_name or "Traveler",
        pnr=payload.pnr or "PNR-DEMO",
        flight_details=payload.flight_details or {"flight_number": "CZ-3042", "departure_time": "14:30", "airline": "China Southern"}
    )
    return {"status": "success", "reply": reply, "timestamp": datetime.now().isoformat()}
