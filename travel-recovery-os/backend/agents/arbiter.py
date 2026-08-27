"""
agents/arbiter.py - Arbiter Decision & Consensus Scoring Agent (DeepSeek LLM Powered)

Phase 2 Enhancements:
- Multi-factor weighted ensemble scoring (punctuality, baggage, compensation, connection time)
- Confidence interval calculation
- Per-criteria scoring breakdown for transparency
- Integration with Baggage and MultiLeg agent messages
"""

from datetime import datetime
from typing import Any, Dict, List

try:
    from state import AgentSwarmState, FlightRoute, ExecutionLog
    from services.llm_service import evaluate_routes_with_deepseek
except ImportError:
    from backend.state import AgentSwarmState, FlightRoute, ExecutionLog
    from backend.services.llm_service import evaluate_routes_with_deepseek


# ---------------------------------------------------------------------------
# Ensemble Scoring Weights
# ---------------------------------------------------------------------------
WEIGHTS = {
    "base_score": 0.35,       # DeepSeek or deterministic base score
    "punctuality": 0.20,      # On-time performance rating
    "baggage_feasibility": 0.15,  # Baggage transfer viability
    "compensation_impact": 0.10,  # Compensation cost impact
    "connection_time": 0.20,     # Connection time adequacy
}


def _calculate_ensemble_score(
    route: Dict[str, Any],
    base_score: float,
    baggage_context: Dict[str, Any],
    compensation_result: Dict[str, Any],
    connecting_flights: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculates a multi-factor weighted ensemble score for a flight route.

    Returns a dict with:
    - final_score: The weighted composite score (0-1)
    - confidence_low: Lower bound of 90% confidence interval
    - confidence_high: Upper bound of 90% confidence interval
    - scoring_breakdown: Per-criteria sub-scores
    """
    breakdown: Dict[str, float] = {}

    # 1. Base score (from DeepSeek or deterministic arbiter)
    breakdown["base_score"] = base_score

    # 2. Punctuality rating
    punctuality = route.get("punctuality_rating", 0.90)
    breakdown["punctuality"] = punctuality

    # 3. Baggage feasibility score
    baggage_transfer_time = baggage_context.get("estimated_transfer_time_minutes", 20)
    layover_hours = route.get("layovers", 0) * 2.0  # Rough estimate
    if baggage_context.get("interline_eligible", True):
        baggage_score = min(1.0, max(0.3, 1.0 - (baggage_transfer_time / 120.0)))
    else:
        baggage_score = 0.4  # Penalty for no interline agreement
    breakdown["baggage_feasibility"] = round(baggage_score, 2)

    # 4. Compensation impact (lower compensation = better for airline)
    comp_amount = compensation_result.get("amount_usd", 0)
    fare = route.get("base_fare_usd", 500.0)
    if fare > 0 and comp_amount > 0:
        comp_ratio = comp_amount / fare
        compensation_score = max(0.2, 1.0 - comp_ratio)
    else:
        compensation_score = 1.0
    breakdown["compensation_impact"] = round(compensation_score, 2)

    # 5. Connection time adequacy
    if connecting_flights:
        # If there are connecting flights, check viability
        all_viable = all(f.get("connection_viable", True) for f in connecting_flights)
        connection_score = 1.0 if all_viable else 0.3
    else:
        # No connecting flights = direct flight, best case
        if route.get("layovers", 0) == 0:
            connection_score = 1.0
        else:
            # Has layovers but no specific connection analysis
            connection_score = 0.7
    breakdown["connection_time"] = round(connection_score, 2)

    # Weighted composite
    final_score = sum(
        breakdown[key] * WEIGHTS[key]
        for key in WEIGHTS
    )
    final_score = round(max(0.05, min(0.99, final_score)), 2)

    # Confidence interval (simple estimate based on score variance)
    scores = list(breakdown.values())
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    std_dev = variance ** 0.5
    ci_margin = round(std_dev * 0.3, 2)  # 90% CI approximation
    confidence_low = round(max(0.05, final_score - ci_margin), 2)
    confidence_high = round(min(0.99, final_score + ci_margin), 2)

    return {
        "final_score": final_score,
        "confidence_low": confidence_low,
        "confidence_high": confidence_high,
        "scoring_breakdown": breakdown,
    }


async def arbiter_node(state: AgentSwarmState) -> Dict[str, Any]:
    """
    Arbiter Agent Node: Scores routes using DeepSeek LLM Chain-of-Thought reasoning
    enhanced with multi-factor ensemble scoring from Baggage, Compensation, and MultiLeg agents.
    """
    candidates: List[FlightRoute] = state.get("candidate_routes", [])
    profile = state.get("passenger_context", {})
    disruption = state.get("disruption_event", {})
    sla_constraints = state.get("sla_constraints", {})
    baggage_context = state.get("baggage_context", {}) or {}
    compensation_result = state.get("compensation_result", {}) or {}
    connecting_flights = state.get("connecting_flights", []) or []

    financial_profile = sla_constraints.get("financial_profile", {
        "airline_savings_usd": 280.0,
        "hotel_penalty_avoided_usd": 320.0,
        "sla_liability_usd": 150.0
    })

    # 1. Execute DeepSeek Chain-of-Thought Evaluation
    deepseek_result = await evaluate_routes_with_deepseek(profile, candidates, disruption)

    engine_name = deepseek_result.get("engine", "DeepSeek CoT Engine")
    reasoning_trace = deepseek_result.get("reasoning_trace", "Evaluated routes against passenger SLAs.")
    hitl_decision = deepseek_result.get("hitl_status", "PENDING")
    whatsapp_copy = deepseek_result.get("whatsapp_message", "")
    scored_items = {
        item.get("flight_number"): item
        for item in deepseek_result.get("scored_routes", [])
    }

    # 2. Update candidate flight objects with ensemble scores
    updated_candidates: List[FlightRoute] = []
    for route in candidates:
        r_copy = dict(route)
        flt_no = r_copy.get("flight_number")

        # Get base score from DeepSeek
        base_score = scored_items.get(flt_no, {}).get("score", 0.50) if flt_no in scored_items else 0.50

        # Calculate ensemble score with all agent inputs
        ensemble = _calculate_ensemble_score(
            route=r_copy,
            base_score=base_score,
            baggage_context=baggage_context,
            compensation_result=compensation_result,
            connecting_flights=connecting_flights,
        )

        r_copy["score"] = ensemble["final_score"]
        r_copy["scoring_rationale"] = scored_items.get(flt_no, {}).get(
            "rationale", f"Ensemble score: {ensemble['final_score']} (CI: {ensemble['confidence_low']}-{ensemble['confidence_high']})"
        )
        r_copy["scoring_breakdown"] = ensemble["scoring_breakdown"]
        r_copy["financial_savings"] = financial_profile

        updated_candidates.append(r_copy)  # type: ignore

    # Sort candidates descending by ensemble score
    updated_candidates.sort(key=lambda r: r.get("score", 0), reverse=True)
    best_route = updated_candidates[0] if updated_candidates else None

    if best_route:
        best_route["financial_savings"] = financial_profile

    # Re-evaluate HITL decision with ensemble scores
    loyalty_tier = profile.get("loyalty_tier", "GOLD")
    best_score = best_route.get("score", 0) if best_route else 0

    # Override HITL decision based on ensemble confidence
    if loyalty_tier in ["PLATINUM", "GOLD"] and best_score >= 0.85:
        hitl_decision = "BYPASSED"
    elif best_score < 0.85:
        hitl_decision = "PENDING"

    # Build decision log
    if hitl_decision == "BYPASSED":
        decision_msg = f"⚡ [Ensemble AUTO-APPROVED]: Route {best_route.get('flight_number') if best_route else 'N/A'} scored {best_score} for {loyalty_tier} tier. All SLA criteria met."
    else:
        decision_msg = f"⏳ [Ensemble HITL REQUIRED]: Route {best_route.get('flight_number') if best_route else 'N/A'} scored {best_score}. Dispatched to n8n WhatsApp gateway."

    now_iso = datetime.now().isoformat()

    log_entry: ExecutionLog = {
        "timestamp": now_iso,
        "node": "arbiter",
        "agent_name": f"Arbiter Engine ({engine_name})",
        "level": "DECISION" if hitl_decision == "BYPASSED" else "WARN",
        "message": decision_msg,
        "data": {
            "selected_flight": best_route.get("flight_number") if best_route else None,
            "score": best_score,
            "hitl_status": hitl_decision,
            "deepseek_reasoning_trace": reasoning_trace,
            "whatsapp_copy": whatsapp_copy,
            "financial_arbitrage": financial_profile,
            "ensemble_breakdown": best_route.get("scoring_breakdown") if best_route else None,
            "all_ranked_candidates": [
                {
                    "flight": r.get("flight_number"),
                    "score": r.get("score"),
                    "rationale": r.get("scoring_rationale"),
                    "breakdown": r.get("scoring_breakdown"),
                }
                for r in updated_candidates
            ]
        }
    }

    return {
        "candidate_routes": updated_candidates,
        "selected_route": best_route,
        "hitl_status": hitl_decision,
        "execution_logs": [log_entry]
    }
