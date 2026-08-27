"""
agents/compensation.py - Passenger Rights & Compensation Agent

Responsible for:
1. Calculating EU261/DOT/MAS passenger rights compensation based on delay,
   route jurisdiction, and disruption reason.
2. Determining compensation eligibility and amount.
3. Generating passenger-friendly compensation summary.
"""

from datetime import datetime
from typing import Any, Dict, Optional

try:
    from state import AgentSwarmState, CompensationResult, ExecutionLog
except ImportError:
    from backend.state import AgentSwarmState, CompensationResult, ExecutionLog


# ---------------------------------------------------------------------------
# Compensation Regulation Rules
# ---------------------------------------------------------------------------

# EU261 Compensation Tiers (EUR -> USD approximate)
EU261_COMPENSATION = {
    "short": {"max_km": 1500, "delay_hours": 2, "amount_eur": 250, "amount_usd": 275},
    "medium": {"min_km": 1501, "max_km": 3500, "delay_hours": 3, "amount_eur": 400, "amount_usd": 440},
    "long": {"min_km": 3501, "delay_hours": 4, "amount_eur": 600, "amount_usd": 660},
}

# DOT (US) Rules - Tarmac delay compensation
DOT_COMPENSATION = {
    "domestic_tarmac_3h": {"amount_usd": 1350, "note": "Up to $1,350 per passenger for 3+ hour tarmac delay"},
    "international_tarmac_4h": {"amount_usd": 1350, "note": "Up to $1,350 per passenger for 4+ hour tarmac delay"},
}

# MAS (Malaysia) Aviation Consumer Protection
MAS_COMPENSATION = {
    "delay_5h": {"amount_myr": 200, "amount_usd": 45, "note": "5+ hour delay compensation"},
    "cancellation": {"amount_myr": 500, "amount_usd": 110, "note": "Flight cancellation compensation"},
}


def _determine_jurisdiction(origin: str, destination: str, airline: str) -> str:
    """Determines which compensation regulation applies based on route."""
    eu_airports = {"LHR", "CDG", "FRA", "AMS", "MAD", "BCN", "FCO", "MUC", "ZRH", "VIE", "DUB", "HEL", "CPH", "OSL", "ARN"}
    us_airports = {"JFK", "LAX", "SFO", "ORD", "ATL", "DFW", "MIA", "BOS", "SEA", "IAD", "EWR", "IAH", "PHL", "CLT", "MCO"}
    my_airports = {"KUL", "PEN", "LGK", "JHB", "KCH", "BKI", "MYY"}

    # EU261: Departure from EU or arrival in EU on EU carrier
    if origin in eu_airports or destination in eu_airports:
        return "EU261"
    # DOT: US domestic or international flights involving US airports
    if origin in us_airports or destination in us_airports:
        return "DOT"
    # MAS: Malaysian airports
    if origin in my_airports or destination in my_airports:
        return "MAS"
    return "NONE"


def _calculate_distance_category(origin: str, destination: str) -> str:
    """Rough distance categorization based on airport pairs."""
    # Simplified distance estimation for demo purposes
    long_haul_pairs = [
        ("KUL", "LHR"), ("LHR", "KUL"), ("SIN", "LHR"), ("LHR", "SIN"),
        ("KUL", "JFK"), ("JFK", "KUL"), ("PVG", "LHR"), ("LHR", "PVG"),
    ]
    medium_haul_pairs = [
        ("KUL", "HGH"), ("HGH", "KUL"), ("KUL", "PVG"), ("PVG", "KUL"),
        ("SIN", "NRT"), ("NRT", "SIN"), ("KUL", "DXB"), ("DXB", "KUL"),
    ]

    pair = (origin, destination)
    if pair in long_haul_pairs:
        return "long"
    elif pair in medium_haul_pairs:
        return "medium"
    return "short"


def _is_extraordinary_circumstance(reason: str) -> bool:
    """Checks if the disruption reason qualifies as extraordinary circumstance (exempts airline from compensation)."""
    extraordinary_keywords = [
        "typhoon", "hurricane", "volcanic", "earthquake", "tsunami",
        "war", "terrorist", "air traffic control", "atc strike",
        "severe weather", "bird strike", "security threat"
    ]
    reason_lower = reason.lower()
    return any(kw in reason_lower for kw in extraordinary_keywords)


def _safe_state(state: Any) -> Dict[str, Any]:
    if isinstance(state, dict):
        return state
    if isinstance(state, (list, tuple)):
        for item in state:
            if isinstance(item, dict):
                return item
    if hasattr(state, "dict") and callable(getattr(state, "dict")):
        return state.dict()
    return {}


async def compensation_node(state: AgentSwarmState) -> Dict[str, Any]:
    """
    Compensation Agent Node: Calculates passenger rights and compensation eligibility.
    """
    st = _safe_state(state)
    disruption = st.get("disruption_event", {})
    passenger = st.get("passenger_context", {})

    origin = disruption.get("origin", "KUL")
    destination = disruption.get("destination", "HGH")
    airline = disruption.get("airline", "Unknown")
    delay_minutes = disruption.get("delay_minutes", 0)
    reason = disruption.get("reason", "Unknown")
    delay_hours = delay_minutes / 60.0

    jurisdiction = _determine_jurisdiction(origin, destination, airline)
    distance_cat = _calculate_distance_category(origin, destination)
    is_extraordinary = _is_extraordinary_circumstance(reason)

    # Calculate compensation based on jurisdiction
    eligible = False
    amount_usd = 0.0
    currency = "USD"
    details = ""

    if is_extraordinary:
        # Extraordinary circumstances exempt airline from mandatory compensation
        eligible = False
        amount_usd = 0.0
        details = f"Disruption caused by extraordinary circumstance ({reason}). Airline exempt from mandatory compensation under {jurisdiction}. Duty of care (meals, accommodation) still applies."

    elif jurisdiction == "EU261":
        tier = EU261_COMPENSATION.get(distance_cat, EU261_COMPENSATION["short"])
        if delay_hours >= tier["delay_hours"]:
            eligible = True
            amount_usd = tier["amount_usd"]
            currency = "EUR"
            details = f"EU261 applies: {delay_hours:.1f}h delay exceeds {tier['delay_hours']}h threshold for {distance_cat}-haul flight. Compensation: {tier['amount_eur']} EUR ({tier['amount_usd']} USD)."
        else:
            details = f"EU261 applies but delay ({delay_hours:.1f}h) does not meet {tier['delay_hours']}h threshold for {distance_cat}-haul flight."

    elif jurisdiction == "DOT":
        if delay_hours >= 3:
            eligible = True
            amount_usd = 1350
            details = f"DOT tarmac delay rules apply. Delay of {delay_hours:.1f}h triggers passenger compensation rights."
        else:
            details = f"DOT rules apply. Delay of {delay_hours:.1f}h below tarmac delay threshold."

    elif jurisdiction == "MAS":
        if delay_hours >= 5:
            eligible = True
            amount_usd = MAS_COMPENSATION["delay_5h"]["amount_usd"]
            details = f"MAS Aviation Consumer Protection applies. {delay_hours:.1f}h delay triggers MYR 200 ({MAS_COMPENSATION['delay_5h']['amount_usd']} USD) compensation."
        else:
            details = f"MAS rules apply. Delay of {delay_hours:.1f}h below 5h threshold for mandatory compensation."
    else:
        details = f"No specific jurisdiction applies for route {origin}-{destination}. Airline goodwill compensation may still be offered."

    compensation: CompensationResult = {
        "regulation": jurisdiction,
        "eligible": eligible,
        "amount_usd": amount_usd,
        "currency": currency,
        "reason": reason,
        "details": details,
    }

    now_iso = datetime.now().isoformat()
    level = "INFO" if not eligible else "DECISION"
    comp_msg = f"${amount_usd} compensation under {jurisdiction}" if eligible else f"No mandatory compensation ({jurisdiction})"

    log_entry: ExecutionLog = {
        "timestamp": now_iso,
        "node": "compensation",
        "agent_name": "Compensation Rights Agent",
        "level": level,
        "message": f"⚖️ Compensation evaluated: {comp_msg}. Jurisdiction: {jurisdiction}. Eligible: {eligible}. {details[:100]}",
        "data": {
            "compensation_result": dict(compensation),
            "jurisdiction": jurisdiction,
            "distance_category": distance_cat,
            "extraordinary_circumstance": is_extraordinary,
        }
    }

    return {
        "compensation_result": compensation,
        "execution_logs": [log_entry],
    }
