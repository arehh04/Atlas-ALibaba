"""
agents/baggage.py - Baggage Transfer Evaluation Agent

Responsible for:
1. Evaluating checked baggage transfer feasibility for rebooked flights.
2. Checking interline baggage agreements between airlines.
3. Assessing special item handling (sports equipment, pets, fragile items).
4. Estimating baggage transfer time requirements.
"""

from datetime import datetime
from typing import Any, Dict, List

try:
    from state import AgentSwarmState, BaggageContext, ExecutionLog, AgentMessage
except ImportError:
    from backend.state import AgentSwarmState, BaggageContext, ExecutionLog, AgentMessage


# Known interline baggage agreements (mock data for demonstration)
INTERLINE_AGREEMENTS = {
    ("China Southern Airlines", "Air China"): True,
    ("China Southern Airlines", "Singapore Airlines"): True,
    ("Singapore Airlines", "Malaysia Airlines"): True,
    ("Air China", "China Southern Airlines"): True,
    ("Cathay Pacific", "Singapore Airlines"): True,
    ("Malaysia Airlines", "Singapore Airlines"): True,
}

# Special item transfer difficulty ratings
SPECIAL_ITEM_DIFFICULTY = {
    "sports_equipment": {"extra_time_min": 30, "risk": "MEDIUM"},
    "pet": {"extra_time_min": 45, "risk": "HIGH"},
    "fragile": {"extra_time_min": 15, "risk": "MEDIUM"},
    "musical_instrument": {"extra_time_min": 20, "risk": "MEDIUM"},
    "medical_equipment": {"extra_time_min": 10, "risk": "LOW"},
}


def _check_interline_agreement(original_airline: str, new_airline: str) -> bool:
    """Checks if two airlines have an interline baggage agreement."""
    if original_airline == new_airline:
        return True
    return INTERLINE_AGREEMENTS.get((original_airline, new_airline), False)


def _estimate_transfer_time(
    checked_bags: int,
    special_items: List[str],
    interline_eligible: bool,
    layovers: int,
) -> int:
    """Estimates baggage transfer time in minutes."""
    base_time = 15 if interline_eligible else 30
    bag_time = checked_bags * 5
    special_time = sum(
        SPECIAL_ITEM_DIFFICULTY.get(item, {}).get("extra_time_min", 10)
        for item in special_items
    )
    layover_overhead = layovers * 10
    return base_time + bag_time + special_time + layover_overhead


async def baggage_node(state: AgentSwarmState) -> Dict[str, Any]:
    """
    Baggage Agent Node: Evaluates baggage transfer feasibility for the disrupted passenger.
    """
    disruption = state.get("disruption_event", {})
    passenger = state.get("passenger_context", {})
    original_airline = disruption.get("airline", "Unknown Airline")

    # Derive baggage context from passenger profile and loyalty tier
    tier = (passenger.get("loyalty_tier") or "STANDARD").upper()

    # Higher tier passengers get more generous baggage allowances
    if tier == "PLATINUM":
        checked_bags = 3
        special_items: List[str] = []
    elif tier == "GOLD":
        checked_bags = 2
        special_items = []
    elif tier == "SILVER":
        checked_bags = 2
        special_items = []
    else:
        checked_bags = 1
        special_items = []

    # For now, assume same-airline rebooking is likely (interline = True)
    # The actual new airline will be determined by Scout, but we estimate
    interline_eligible = True  # Conservative: assume yes for parallel execution

    transfer_time = _estimate_transfer_time(
        checked_bags, special_items, interline_eligible, layovers=0
    )

    baggage_ctx: BaggageContext = {
        "checked_bags": checked_bags,
        "special_items": special_items,
        "interline_eligible": interline_eligible,
        "baggage_transfer_confirmed": True,
        "transfer_notes": f"{checked_bags} checked bag(s) eligible for automatic transfer. Estimated transfer time: {transfer_time} minutes.",
        "estimated_transfer_time_minutes": transfer_time,
    }

    now_iso = datetime.now().isoformat()
    log_entry: ExecutionLog = {
        "timestamp": now_iso,
        "node": "baggage",
        "agent_name": "Baggage Transfer Agent",
        "level": "INFO",
        "message": f"🧳 Baggage evaluation complete: {checked_bags} bag(s), interline eligible: {interline_eligible}, transfer time: {transfer_time}min.",
        "data": {
            "baggage_context": dict(baggage_ctx),
            "loyalty_tier": tier,
            "original_airline": original_airline,
        }
    }

    # Publish agent message for Arbiter to consider baggage feasibility
    agent_msg: AgentMessage = {
        "from_agent": "baggage",
        "to_agent": "arbiter",
        "message_type": "NOTIFICATION",
        "payload": {
            "baggage_transfer_time_minutes": transfer_time,
            "interline_eligible": interline_eligible,
            "checked_bags": checked_bags,
        },
        "timestamp": now_iso,
        "correlation_id": state.get("thread_id", ""),
    }

    return {
        "baggage_context": baggage_ctx,
        "execution_logs": [log_entry],
        "agent_messages": [agent_msg],
    }
