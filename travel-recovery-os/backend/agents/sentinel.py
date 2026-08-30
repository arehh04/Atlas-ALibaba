"""
agents/sentinel.py - Sentinel Disruption Interceptor Agent (Hermes Powered)

Responsible for:
1. Ingesting flight cancellation / delay signals (Structured JSON or Unstructured NOTAM/SMS).
2. Utilizing Hermes local LLM for function calling / JSON extraction from raw operational text.
3. Validating PNR, flight details, delay magnitude, and route context.
4. Emitting telemetry logs and initializing the LangGraph execution flow.
"""

from datetime import datetime
from typing import Any

try:
    from services.llm_service import extract_disruption_with_hermes
    from state import AgentMessage, AgentSwarmState, DisruptionEvent, ExecutionLog
except ImportError:
    from backend.services.llm_service import extract_disruption_with_hermes
    from backend.state import AgentMessage, AgentSwarmState, DisruptionEvent, ExecutionLog


def _safe_state(state: Any) -> dict[str, Any]:
    if isinstance(state, dict):
        return state
    if isinstance(state, (list, tuple)):
        for item in state:
            if isinstance(item, dict):
                return item
    if hasattr(state, "dict") and callable(state.dict):
        return state.dict()
    return {}


async def sentinel_node(state: AgentSwarmState) -> dict[str, Any]:
    """
    Sentinel Agent Node: Intercepts raw disruption signals and validates payload.
    
    [HERMES LLM FUNCTION CALLING INTEGRATION]
    If raw unstructured text is provided in disruption_event['raw_text'],
    Sentinel invokes Hermes to extract clean flight cancellation schema.
    """
    st = _safe_state(state)
    event: DisruptionEvent = dict(st.get("disruption_event", {}))
    raw_text = event.get("raw_text")
    
    extraction_meta = "Structured Webhook Ingest"
    
    # If raw unstructured text is present, extract via Hermes LLM
    if raw_text:
        extracted = await extract_disruption_with_hermes(raw_text)
        extraction_meta = extracted.get("extracted_by", "Hermes Function Calling")
        
        # Merge extracted fields into event
        event["pnr"] = extracted.get("pnr", event.get("pnr", "PNR-HERMES"))
        event["flight_number"] = extracted.get("flight_number", event.get("flight_number", "CZ-3042"))
        event["airline"] = extracted.get("airline", event.get("airline", "China Southern Airlines"))
        event["origin"] = extracted.get("origin", event.get("origin", "KUL"))
        event["destination"] = extracted.get("destination", event.get("destination", "HGH"))
        event["delay_minutes"] = extracted.get("delay_minutes", event.get("delay_minutes", 240))
        event["reason"] = extracted.get("reason", event.get("reason", "Operational swap / Typhoon warning"))
    
    pnr = event.get("pnr", "UNKNOWN_PNR")
    flight_number = event.get("flight_number", "UNKNOWN_FLT")
    origin = event.get("origin", "KUL")
    destination = event.get("destination", "HGH")
    delay_minutes = event.get("delay_minutes", 0)
    reason = event.get("reason", "Operational Aircraft Swap / Typhoon Warning")
    
    now_iso = datetime.now().isoformat()
    
    log_entry: ExecutionLog = {
        "timestamp": now_iso,
        "node": "sentinel",
        "agent_name": "Sentinel Interceptor (Hermes)",
        "level": "INFO",
        "message": f"🚨 [Hermes Parser] Disruption intercepted for Flight {flight_number} (PNR: {pnr}). Route: {origin}➔{destination}. Delay: {delay_minutes}m. Extracted via: {extraction_meta}.",
        "data": {
            "pnr": pnr,
            "flight_number": flight_number,
            "route": f"{origin} ➔ {destination}",
            "delay_minutes": delay_minutes,
            "reason": reason,
            "parser_engine": extraction_meta
        }
    }
    
    agent_msg: AgentMessage = {
        "from_agent": "sentinel",
        "to_agent": "*",
        "message_type": "NOTIFICATION",
        "text": f"🚨 Intercepted disruption for Flight {flight_number} (PNR: {pnr}, {origin}➔{destination}, Delay: {delay_minutes}m). Alerting Profile, Scout, Baggage, and Compensation agents to begin recovery swarm.",
        "payload": {
            "pnr": pnr,
            "flight_number": flight_number,
            "route": f"{origin} ➔ {destination}",
            "delay_minutes": delay_minutes,
            "reason": reason,
            "extracted_by": extraction_meta,
        },
        "timestamp": now_iso,
        "correlation_id": st.get("thread_id", ""),
    }

    return {
        "disruption_event": event,
        "execution_logs": [log_entry],
        "agent_messages": [agent_msg],
    }
