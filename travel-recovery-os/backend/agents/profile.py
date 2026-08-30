"""
agents/profile.py - Dynamic Passenger Profile & Loyalty SLA Agent

Calculates dynamic SLA constraints and financial liability metrics based on:
1. Passenger loyalty tier (PLATINUM, GOLD, SILVER, STANDARD)
2. Disruption delay magnitude & origin/destination market
3. Alliance rules (Direct flight requirements, cabin class eligibility, compensation budget)
"""

from datetime import datetime
from typing import Any

try:
    from state import AgentMessage, AgentSwarmState, ExecutionLog
except ImportError:
    from backend.state import AgentMessage, AgentSwarmState, ExecutionLog


def derive_financial_arbitrage(tier: str, delay_minutes: int) -> dict[str, float]:
    """Dynamically calculates airline liability and hotel SLA avoidance costs."""
    tier_upper = (tier or "STANDARD").upper()
    delay_hours = max(1.0, delay_minutes / 60.0)
    
    if tier_upper == "PLATINUM":
        hotel_cost = 450.0 if delay_hours >= 4 else 250.0
        sla_penalty = round(300.0 * (delay_hours / 3.0), 2)
        airline_savings = round(hotel_cost + sla_penalty, 2)
    elif tier_upper == "GOLD":
        hotel_cost = 320.0 if delay_hours >= 4 else 180.0
        sla_penalty = round(200.0 * (delay_hours / 3.0), 2)
        airline_savings = round(hotel_cost + sla_penalty, 2)
    elif tier_upper == "SILVER":
        hotel_cost = 220.0 if delay_hours >= 4 else 120.0
        sla_penalty = round(100.0 * (delay_hours / 3.0), 2)
        airline_savings = round(hotel_cost + sla_penalty, 2)
    else:
        hotel_cost = 150.0 if delay_hours >= 4 else 60.0
        sla_penalty = round(50.0 * (delay_hours / 3.0), 2)
        airline_savings = round(hotel_cost + sla_penalty, 2)
        
    return {
        "airline_savings_usd": airline_savings,
        "hotel_penalty_avoided_usd": hotel_cost,
        "sla_liability_usd": sla_penalty
    }


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


async def profile_agent_node(state: AgentSwarmState) -> dict[str, Any]:
    """
    Profile Agent: Evaluates loyalty SLA rules and financial liabilities.
    """
    st = _safe_state(state)
    pax_ctx = st.get("passenger_context", {})
    tier = (pax_ctx.get("loyalty_tier") or "STANDARD").upper()
    disruption = st.get("disruption_event", {})
    delay_mins = disruption.get("delay_minutes", 180)
    
    financials = derive_financial_arbitrage(tier, delay_mins)
    
    if tier == "PLATINUM":
        sla_rules = {
            "max_layovers": 0,
            "max_layover_hours": 0.0,
            "cabin_class_preference": "Business",
            "auto_approve_allowed": True,
            "min_carrier_rating": 0.90,
            "sla_tier": "VIP_PLATINUM",
            "financial_profile": financials
        }
    elif tier == "GOLD":
        sla_rules = {
            "max_layovers": 1,
            "max_layover_hours": 2.0,
            "cabin_class_preference": "Business",
            "auto_approve_allowed": True,
            "min_carrier_rating": 0.85,
            "sla_tier": "ELITE_GOLD",
            "financial_profile": financials
        }
    elif tier == "SILVER":
        sla_rules = {
            "max_layovers": 1,
            "max_layover_hours": 4.0,
            "cabin_class_preference": "Economy",
            "auto_approve_allowed": False,
            "min_carrier_rating": 0.80,
            "sla_tier": "TIER_SILVER",
            "financial_profile": financials
        }
    else:
        sla_rules = {
            "max_layovers": 2,
            "max_layover_hours": 6.0,
            "cabin_class_preference": "Economy",
            "auto_approve_allowed": False,
            "min_carrier_rating": 0.70,
            "sla_tier": "STANDARD",
            "financial_profile": financials
        }

    now_iso = datetime.now().isoformat()
    pax_name = pax_ctx.get("passenger_name", "Passenger")

    log_entry: ExecutionLog = {
        "timestamp": now_iso,
        "node": "profile",
        "level": "INFO",
        "message": f"Profile Agent derived SLA profile for {pax_name} ({tier}). Potential SLA avoidance: ${financials['airline_savings_usd']}.",
        "data": {
            "loyalty_tier": tier,
            "sla_rules": sla_rules,
            "financial_arbitrage": financials
        }
    }

    agent_msg: AgentMessage = {
        "from_agent": "profile",
        "to_agent": "arbiter",
        "message_type": "RESPONSE",
        "text": f"👤 Analyzed passenger {pax_name} ({tier} tier). Constraints: Max {sla_rules['max_layovers']} layover(s), {sla_rules['cabin_class_preference']} class preference. SLA liability avoidance: ${financials['airline_savings_usd']}.",
        "payload": {
            "loyalty_tier": tier,
            "passenger_name": pax_name,
            "max_layovers": sla_rules["max_layovers"],
            "cabin_class_preference": sla_rules["cabin_class_preference"],
            "financial_arbitrage": financials,
        },
        "timestamp": now_iso,
        "correlation_id": st.get("thread_id", ""),
    }

    return {
        "sla_constraints": sla_rules,
        "execution_logs": [log_entry],
        "agent_messages": [agent_msg],
    }
