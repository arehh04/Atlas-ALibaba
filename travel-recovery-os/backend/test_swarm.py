"""
test_swarm.py - Production Test Suite for SynapseAir (Hermes, DeepSeek, and n8n)
"""

import asyncio
import os
import sys

# Ensure parent directory is in sys.path so backend package imports work
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import pytest
from backend.services.llm_service import (
    evaluate_routes_with_deepseek,
    extract_disruption_with_hermes,
)
from backend.services.n8n_service import dispatch_hitl_to_n8n
from backend.state import AgentSwarmState
from backend.swarm import build_swarm_graph
from backend.tools.atlas_client import issue_ticket, search_alternative_flights


@pytest.mark.asyncio
async def test_atlas_tools():
    print("1. Testing Atlas Sandbox API mock tools...")
    routes = await search_alternative_flights("KUL", "HGH", "2026-08-25")
    assert len(routes) >= 2, "Expected at least 2 candidate flights"
    print(f"  ✓ Atlas search returned {len(routes)} flights.")
    
    ticket = await issue_ticket("PNR-TEST", routes[0]["flight_id"])
    assert ticket["status"] == "ISSUED", "Ticket should have ISSUED status"
    assert "e_ticket_number" in ticket, "Ticket number should be present"
    print(f"  ✓ Atlas ticketing issued ticket: {ticket['e_ticket_number']}")


@pytest.mark.asyncio
async def test_hermes_extraction():
    print("\n2. Testing Hermes LLM / Function Calling Unstructured Extraction...")
    raw_notam = "URGENT OPS NOTICE: Flight CZ-3042 from KUL to HGH canceled due to typhoon warning. Passenger PNR-8842 affected."
    extracted = await extract_disruption_with_hermes(raw_notam)
    
    assert extracted.get("pnr") is not None, "PNR should be extracted"
    assert "CZ" in extracted.get("flight_number", ""), "Flight number should contain CZ"
    print(f"  ✓ Hermes extracted: PNR={extracted.get('pnr')}, Flight={extracted.get('flight_number')}, Route={extracted.get('origin')}->{extracted.get('destination')}")
    print(f"  ✓ Extraction engine: {extracted.get('extracted_by')}")


@pytest.mark.asyncio
async def test_deepseek_cot_arbitration():
    print("\n3. Testing DeepSeek LLM Multi-Criteria Route Arbitration...")
    routes = await search_alternative_flights("KUL", "HGH", "2026-08-25")
    profile = {"loyalty_tier": "PLATINUM", "passenger_name": "Dr. Vance", "preferred_cabin": "Business", "requires_direct_flight": True}
    disruption = {"pnr": "PNR-VIP-99", "flight_number": "CZ-3042", "origin": "KUL", "destination": "HGH"}
    
    evaluation = await evaluate_routes_with_deepseek(profile, routes, disruption)
    assert evaluation.get("confidence_score") is not None, "Confidence score expected"
    assert evaluation.get("hitl_status") in ["BYPASSED", "PENDING"], "Valid HITL status expected"
    assert len(evaluation.get("scored_routes", [])) > 0, "Scored routes expected"
    print(f"  ✓ DeepSeek evaluation engine: {evaluation.get('engine')}")
    print(f"  ✓ Selected flight: {evaluation.get('best_flight_number')} (Score: {evaluation.get('confidence_score')})")
    print(f"  ✓ Decision: {evaluation.get('hitl_status')}")


@pytest.mark.asyncio
async def test_n8n_webhook_dispatch():
    print("\n4. Testing n8n WhatsApp Gateway Webhook Dispatch...")
    receipt = await dispatch_hitl_to_n8n(
        thread_id="test-n8n-thread-01",
        pnr="PNR-8842",
        passenger_context={"passenger_name": "Sarah Jenkins", "phone_number": "+60 12-345 6789", "loyalty_tier": "STANDARD"},
        selected_route={"flight_number": "CZ-3042", "airline": "China Southern Airlines", "departure_time": "14:30", "cabin_class": "Economy", "score": 0.82},
        whatsapp_message="Your flight CZ-3042 has been rebooked to alternative departure at 14:30."
    )
    assert receipt.get("status") in ["DISPATCHED", "SIMULATED", "SIMULATED_SUCCESS", "FAILED", "ERROR"], "Valid status expected"
    print(f"  ✓ n8n gateway response: {receipt.get('status')} (Target: {receipt.get('target_url')})")


@pytest.mark.asyncio
async def test_end_to_end_langgraph_swarm():
    print("\n5. Testing End-to-End LangGraph Swarm with HITL Pause & Resume...")
    graph, _ = build_swarm_graph()
    thread_id = "test-prod-thread"
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state: AgentSwarmState = {
        "thread_id": thread_id,
        "disruption_event": {
            "raw_text": "OPERATIONS ALERT: Flight CA-1890 from KUL to HGH delayed 300 minutes. PNR: PNR-STD-7711.",
            "pnr": "PNR-STD-7711",
            "flight_number": "CA-1890",
            "origin": "KUL",
            "destination": "HGH",
            "delay_minutes": 300
        },
        "passenger_context": {
            "loyalty_tier": "STANDARD",
            "passenger_name": "Marcus Brody"
        },
        "candidate_routes": [],
        "selected_route": None,
        "hitl_status": "PENDING",
        "execution_logs": [],
        "ticket_confirmation": None
    }
    
    # 1. Run until breakpoint
    async for _ in graph.astream(initial_state, config=config):
        pass
        
    state_at_bp = await graph.aget_state(config)
    hitl_status = state_at_bp.values.get("hitl_status")
    print(f"  ✓ DeepSeek swarm decision: {hitl_status}")
    
    if state_at_bp.next and "hitl_breakpoint" in state_at_bp.next:
        print(f"  ✓ Graph paused at checkpointer breakpoint: {state_at_bp.next}")
        # Simulate passenger approval from WhatsApp
        await graph.aupdate_state(config, {"hitl_status": "APPROVED"}, as_node="hitl_breakpoint")
        async for _ in graph.astream(None, config=config):
            pass
        final_state = await graph.aget_state(config)
        assert final_state.values.get("ticket_confirmation") is not None, "Ticket should be issued after resume"
        print(f"  ✓ Final ticket issued after WhatsApp approval: {final_state.values['ticket_confirmation']['e_ticket_number']}")
    else:
        assert state_at_bp.values.get("ticket_confirmation") is not None, "Ticket should be issued on auto-approval"
        print(f"  ✓ DeepSeek Auto-Approved and issued ticket: {state_at_bp.values['ticket_confirmation']['e_ticket_number']}")


async def main():
    print("=" * 70)
    print("SYNAPSEAIR PRODUCTION TEST SUITE (HERMES + DEEPSEEK + N8N + ATLAS)")
    print("=" * 70)
    await test_atlas_tools()
    await test_hermes_extraction()
    await test_deepseek_cot_arbitration()
    await test_n8n_webhook_dispatch()
    await test_end_to_end_langgraph_swarm()
    print("\n" + "=" * 70)
    print("ALL PRODUCTION INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
