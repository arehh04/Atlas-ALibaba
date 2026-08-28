"""
services/n8n_service.py - Production n8n WhatsApp Gateway & Event Relay

Provides:
1. dispatch_hitl_to_n8n: Formats and dispatches interactive WhatsApp templates to n8n webhooks.
2. Durable SQLite audit trail for all n8n webhook interactions (replaces in-memory list).
3. answer_passenger_question: Conversational assistant for passenger WhatsApp chat.

Resilience: Webhook dispatch wrapped with retry and n8n circuit breaker.
"""

import time
from datetime import datetime
from typing import Any

import httpx
from openai import AsyncOpenAI

try:
    from ..config import settings
    from ..middleware.resilience import (
        CircuitBreakerOpen,
        n8n_breaker,
        retry_with_backoff,
    )
    from ..store.event_store import get_n8n_events, insert_n8n_event
except (ImportError, ValueError):
    from config import settings
    from middleware.resilience import (
        CircuitBreakerOpen,
        n8n_breaker,
        retry_with_backoff,
    )
    from store.event_store import get_n8n_events, insert_n8n_event


# ---------------------------------------------------------------------------
# Public API: get event log (from SQLite)
# ---------------------------------------------------------------------------
def get_n8n_event_log() -> list[dict[str, Any]]:
    """Returns all recorded n8n webhook interactions from SQLite."""
    return get_n8n_events(limit=200)


def _safe_dict(val: Any) -> dict[str, Any]:
    if isinstance(val, dict):
        return val
    if isinstance(val, (list, tuple)):
        for item in val:
            if isinstance(item, dict):
                return item
    if hasattr(val, "dict") and callable(val.dict):
        return val.dict()
    return {}


# ---------------------------------------------------------------------------
# Dispatch HITL to n8n
# ---------------------------------------------------------------------------
async def dispatch_hitl_to_n8n(
    thread_id: str,
    pnr: str,
    passenger_context: dict[str, Any],
    selected_route: dict[str, Any],
    whatsapp_message: str | None = None,
    custom_n8n_url: str | None = None
) -> dict[str, Any]:
    """
    Dispatches a structured HITL notification payload to an external n8n webhook
    and records it in the durable SQLite event store.

    Resilience: Wrapped with n8n circuit breaker and retry.
    """
    target_url = custom_n8n_url or settings.N8N_WEBHOOK_URL
    callback_url = settings.N8N_CONSENSUS_CALLBACK_URL

    pax_ctx = _safe_dict(passenger_context)
    sel_route = _safe_dict(selected_route)

    passenger_name = pax_ctx.get("passenger_name", "Valued Passenger")
    phone = pax_ctx.get("phone_number", "+60 12-345 6789")
    flight_num = sel_route.get("flight_number", "CZ-3042")
    airline = sel_route.get("airline", "Partner Carrier")
    dep_time = sel_route.get("departure_time", "14:30")

    # Standard WhatsApp Business API Template Envelope
    payload = {
        "event_type": "SYNAPSEAIR_HITL_REQUIRED",
        "thread_id": thread_id,
        "timestamp": datetime.now().isoformat(),
        "passenger": {
            "name": passenger_name,
            "phone_number": phone,
            "loyalty_tier": pax_ctx.get("loyalty_tier", "STANDARD")
        },
        "disruption": {
            "pnr": pnr,
            "recommended_flight": flight_num,
            "airline": airline,
            "departure_time": dep_time,
            "cabin_class": sel_route.get("cabin_class", "Economy"),
            "score": sel_route.get("score", 0.85)
        },
        "whatsapp_template": {
            "header": f"✈️ SynapseAir Flight Disruption Alert ({pnr})",
            "body": whatsapp_message or f"Hi {passenger_name}, your flight was disrupted. We reserved a seat on {flight_num} departing at {dep_time}.",
            "action_buttons": [
                {
                    "type": "quick_reply",
                    "text": "✓ 1-Click Accept Rebooking",
                    "payload": f"APPROVE:{thread_id}"
                },
                {
                    "type": "quick_reply",
                    "text": "✕ Decline / Alternatives",
                    "payload": f"REJECT:{thread_id}"
                }
            ]
        },
        "consensus_callback": {
            "url": callback_url,
            "method": "POST",
            "approve_payload": {
                "thread_id": thread_id,
                "action": "APPROVE",
                "notes": "Approved by passenger via WhatsApp CTA"
            },
            "reject_payload": {
                "thread_id": thread_id,
                "action": "REJECT",
                "notes": "Declined by passenger via WhatsApp CTA"
            }
        }
    }

    # Dispatch with circuit breaker + retry for real n8n targets
    if target_url and target_url.startswith("http"):
        async def _dispatch():
            start_t = time.time()
            async with httpx.AsyncClient() as client:
                resp = await client.post(target_url, json=payload, timeout=6.0)
                latency_ms = int((time.time() - start_t) * 1000)
                receipt = {
                    "status": "DISPATCHED" if resp.status_code < 400 else "FAILED",
                    "status_code": resp.status_code,
                    "target_url": target_url,
                    "latency_ms": latency_ms,
                    "response_body": resp.text[:200],
                    "timestamp": datetime.now().isoformat(),
                    "payload": payload
                }
                # Persist to SQLite
                insert_n8n_event(
                    thread_id=thread_id,
                    status=receipt["status"],
                    target_url=target_url,
                    latency_ms=latency_ms,
                    payload=payload,
                    response_body=resp.text[:500],
                    event_type="hitl_dispatch",
                )
                return receipt

        try:
            return await n8n_breaker.call(
                lambda: retry_with_backoff(
                    _dispatch,
                    max_retries=2,
                    base_delay=0.5,
                    operation_name="n8n_hitl_dispatch",
                )
            )
        except (CircuitBreakerOpen, Exception) as e:
            latency_ms = 0
            receipt = {
                "status": "ERROR",
                "target_url": target_url,
                "latency_ms": latency_ms,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "payload": payload
            }
            insert_n8n_event(
                thread_id=thread_id,
                status="ERROR",
                target_url=target_url,
                payload=payload,
                error=str(e),
                event_type="hitl_dispatch",
            )
            return receipt

    # In-App Simulated n8n Webhook Relay
    latency_ms = 42
    receipt = {
        "status": "SIMULATED_SUCCESS",
        "message": "Dispatched to In-App WhatsApp Simulator via n8n Relay",
        "target_url": target_url or "internal://n8n-whatsapp-simulator",
        "latency_ms": latency_ms,
        "timestamp": datetime.now().isoformat(),
        "payload": payload
    }
    insert_n8n_event(
        thread_id=thread_id,
        status="SIMULATED_SUCCESS",
        target_url=target_url or "internal://n8n-whatsapp-simulator",
        latency_ms=latency_ms,
        payload=payload,
        event_type="hitl_dispatch",
    )
    return receipt


# ---------------------------------------------------------------------------
# Passenger WhatsApp Chat Assistant
# ---------------------------------------------------------------------------
async def answer_passenger_question(
    passenger_message: str,
    passenger_name: str,
    pnr: str,
    flight_details: dict[str, Any]
) -> str:
    """
    Handles conversational questions from the passenger in WhatsApp
    (e.g., 'Will my baggage be transferred?', 'What time is boarding?').
    """
    flt_details = _safe_dict(flight_details)
    system_prompt = (
        f"You are the SynapseAir AI Operations Assistant replying to a passenger ({passenger_name}) on WhatsApp. "
        f"The passenger's original flight was disrupted. Recommended alternative flight is {flt_details.get('flight_number', 'alternative flight')} "
        f"({flt_details.get('airline', 'partner carrier')}) departing at {flt_details.get('departure_time', 'scheduled time')}. "
        "Baggage is automatically transferred, seats are reserved, and meals are included. "
        "Keep your reply under 2 sentences, friendly, reassuring, and concise like a real WhatsApp support agent."
    )

    # Try using DeepSeek or OpenRouter for answering
    if settings.DEEPSEEK_API_KEY:
        try:
            client = AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                timeout=8.0
            )
            resp = await client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": passenger_message}
                ],
                temperature=0.3
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            pass

    # Fallback contextual replies
    msg_lower = passenger_message.lower()
    if "bag" in msg_lower or "luggage" in msg_lower:
        return f"Yes {passenger_name}, your checked luggage will be automatically transferred to flight {flight_details.get('flight_number')}. No re-check required!"
    elif "time" in msg_lower or "board" in msg_lower:
        return f"Boarding for flight {flight_details.get('flight_number')} begins 45 minutes before departure ({flight_details.get('departure_time')})."
    elif "seat" in msg_lower or "cabin" in msg_lower:
        return f"You are confirmed in {flight_details.get('cabin_class', 'Economy')} class with complimentary seat selection."
    else:
        return f"Thank you for reaching out, {passenger_name}. Our operations team has secured your seat on {flight_details.get('flight_number')}. Tap 'Accept Rebooking' above to finalize your ticket!"
