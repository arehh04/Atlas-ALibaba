"""
agents/multileg.py - Multi-Leg Disruption Coordination Agent

Responsible for:
1. Handling connecting flight disruptions and missed connections.
2. Evaluating minimum connection times (MCT) at transfer airports.
3. Coordinating rebooking across multiple flight segments.
4. Publishing messages to dependent agents about connection viability.
"""

from datetime import datetime
from typing import Any

try:
    from state import AgentMessage, AgentSwarmState, ConnectingFlight, ExecutionLog
except ImportError:
    from backend.state import (
        AgentMessage,
        AgentSwarmState,
        ConnectingFlight,
        ExecutionLog,
    )


# Minimum Connection Times (MCT) in minutes by airport
MCT_BY_AIRPORT = {
    "SIN": {"domestic": 45, "international": 60},
    "KUL": {"domestic": 45, "international": 75},
    "HGH": {"domestic": 60, "international": 90},
    "PVG": {"domestic": 60, "international": 120},
    "DXB": {"domestic": 60, "international": 90},
    "LHR": {"domestic": 60, "international": 90},
    "NRT": {"domestic": 60, "international": 90},
    "BKK": {"domestic": 45, "international": 75},
    "HKG": {"domestic": 45, "international": 60},
    "ICN": {"domestic": 45, "international": 70},
}

DEFAULT_MCT = {"domestic": 60, "international": 90}


def _get_mct(airport: str, connection_type: str = "international") -> int:
    """Returns minimum connection time in minutes for an airport."""
    airport_mct = MCT_BY_AIRPORT.get(airport, DEFAULT_MCT)
    return airport_mct.get(connection_type, 90)


def _analyze_connection_viability(
    origin: str,
    destination: str,
    delay_minutes: int,
    reason: str,
) -> list[ConnectingFlight]:
    """
    Analyzes potential multi-leg disruption impact.
    If the original flight was a connection, evaluates whether downstream
    segments are still viable given the delay.
    """
    # Check if the disruption reason mentions connections
    reason_lower = reason.lower()
    is_connection_disruption = any(
        kw in reason_lower for kw in ["connection", "connecting", "transfer", "missed"]
    )

    if not is_connection_disruption:
        return []

    # Mock: Simulate a downstream connecting flight that may be missed
    mct_at_destination = _get_mct(destination)
    remaining_connection_time = max(0, 120 - delay_minutes)  # Assume 2h original layover

    connecting: ConnectingFlight = {
        "segment_number": 2,
        "flight_number": f"CONN-{destination[:3]}01",
        "airline": "Partner Carrier",
        "origin": destination,
        "destination": "FINAL",
        "departure_time": "",
        "arrival_time": "",
        "connection_time_minutes": remaining_connection_time,
        "minimum_connection_time_minutes": mct_at_destination,
        "connection_viable": remaining_connection_time >= mct_at_destination,
        "status": "MISSED" if remaining_connection_time < mct_at_destination else "AT_RISK",
    }

    return [connecting]


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


async def multileg_node(state: AgentSwarmState) -> dict[str, Any]:
    """
    Multi-Leg Agent Node: Evaluates connecting flight disruptions.

    Runs in parallel with Profile and Scout after Sentinel.
    Publishes connection viability information for the Arbiter.
    """
    st = _safe_state(state)
    disruption = st.get("disruption_event", {})
    origin = disruption.get("origin", "KUL")
    destination = disruption.get("destination", "HGH")
    delay_minutes = disruption.get("delay_minutes", 0)
    reason = disruption.get("reason", "")

    # Analyze multi-leg impact
    connecting_flights = _analyze_connection_viability(origin, destination, delay_minutes, reason)

    now_iso = datetime.now().isoformat()

    if connecting_flights:
        missed = [f for f in connecting_flights if f.get("status") == "MISSED"]
        at_risk = [f for f in connecting_flights if f.get("status") == "AT_RISK"]

        log_msg = f"🔗 Multi-leg analysis: {len(connecting_flights)} connecting segment(s) evaluated."
        if missed:
            log_msg += f" {len(missed)} MISSED connection(s) detected."
        if at_risk:
            log_msg += f" {len(at_risk)} AT-RISK connection(s)."

        log_entry: ExecutionLog = {
            "timestamp": now_iso,
            "node": "multileg",
            "agent_name": "Multi-Leg Coordination Agent",
            "level": "WARN" if missed else "INFO",
            "message": log_msg,
            "data": {
                "connecting_flights": [dict(f) for f in connecting_flights],
                "missed_connections": len(missed),
                "at_risk_connections": len(at_risk),
            }
        }
    else:
        log_entry = {
            "timestamp": now_iso,
            "node": "multileg",
            "agent_name": "Multi-Leg Coordination Agent",
            "level": "INFO",
            "message": "🔗 Multi-leg analysis: No connecting flight disruption detected. Single-leg itinerary.",
            "data": {"connecting_flights": [], "is_single_leg": True}
        }

    # Publish message to Arbiter about connection viability
    agent_msg: AgentMessage = {
        "from_agent": "multileg",
        "to_agent": "arbiter",
        "message_type": "NOTIFICATION",
        "payload": {
            "has_connecting_flights": len(connecting_flights) > 0,
            "missed_connections": len([f for f in connecting_flights if f.get("status") == "MISSED"]),
            "requires_multi_leg_rebooking": any(
                f.get("status") == "MISSED" for f in connecting_flights
            ),
        },
        "timestamp": now_iso,
        "correlation_id": state.get("thread_id", ""),
    }

    return {
        "connecting_flights": connecting_flights,
        "execution_logs": [log_entry],
        "agent_messages": [agent_msg],
    }
