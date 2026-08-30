"""
agents/scout.py - Scout Inventory Discovery Agent

Responsible for:
1. Interacting with the Atlas Sandbox API tools.
2. Sourcing viable alternative flight routes across partner carriers.
3. Injecting candidates into the swarm state for Arbiter evaluation.
"""

from datetime import datetime
from typing import Any

try:
    from state import AgentMessage, AgentSwarmState, ExecutionLog, FlightRoute
    from tools.atlas_client import search_alternative_flights
except ImportError:
    from backend.state import AgentMessage, AgentSwarmState, ExecutionLog, FlightRoute
    from backend.tools.atlas_client import search_alternative_flights


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


async def scout_node(state: AgentSwarmState) -> dict[str, Any]:
    """
    Scout Agent Node: Queries Atlas Sandbox API for candidate routes.
    
    [ATLAS API INTEGRATION]
    Executes real-time flight inventory lookup based on disruption origin/destination.
    """
    st = _safe_state(state)
    event = st.get("disruption_event", {})
    origin = event.get("origin", "KUL")
    destination = event.get("destination", "HGH")
    scheduled_dep = event.get("scheduled_departure", datetime.now().strftime("%Y-%m-%d"))
    travel_date = scheduled_dep.split(" ")[0] if " " in scheduled_dep else scheduled_dep
    
    # Query Atlas Sandbox API tool
    raw_routes = await search_alternative_flights(origin, destination, travel_date)
    
    candidate_routes: list[FlightRoute] = []
    for r in raw_routes:
        candidate_routes.append({
            "flight_id": r["flight_id"],
            "flight_number": r["flight_number"],
            "airline": r["airline"],
            "origin": r["origin"],
            "destination": r["destination"],
            "departure_time": r["departure_time"],
            "arrival_time": r["arrival_time"],
            "duration_hours": r["duration_hours"],
            "layovers": r["layovers"],
            "stops_detail": r.get("stops_detail", []),
            "cabin_class": r["cabin_class"],
            "available_seats": r["available_seats"],
            "base_fare_usd": r["base_fare_usd"],
            "score": 0.0,
            "scoring_rationale": "Pending Arbiter evaluation"
        })
        
    now_iso = datetime.now().isoformat()
    
    log_entry: ExecutionLog = {
        "timestamp": now_iso,
        "node": "scout",
        "agent_name": "Scout Inventory Discovery",
        "level": "INFO",
        "message": f"🔍 Atlas API query returned {len(candidate_routes)} candidate routes between {origin} and {destination}.",
        "data": {
            "routes_count": len(candidate_routes),
            "flights": [f"{r['flight_number']} ({r['airline']}) - {r['departure_time']}" for r in candidate_routes]
        }
    }
    
    flight_summary = ", ".join([f"{r['flight_number']} ({r['airline']} @ {r['departure_time']})" for r in candidate_routes[:3]])
    agent_msg: AgentMessage = {
        "from_agent": "scout",
        "to_agent": "arbiter",
        "message_type": "RESPONSE",
        "text": f"🔍 Atlas API query complete: Retrieved {len(candidate_routes)} alternative routes ({flight_summary}). Relaying candidate inventory to Arbiter for ensemble scoring.",
        "payload": {
            "origin": origin,
            "destination": destination,
            "routes_count": len(candidate_routes),
            "candidates": [{"flight_number": r["flight_number"], "airline": r["airline"], "departure": r["departure_time"], "fare": r["base_fare_usd"]} for r in candidate_routes],
        },
        "timestamp": now_iso,
        "correlation_id": st.get("thread_id", ""),
    }

    return {
        "candidate_routes": candidate_routes,
        "execution_logs": [log_entry],
        "agent_messages": [agent_msg],
    }
