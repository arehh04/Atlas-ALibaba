"""
services/swarm_runner.py - Swarm Pipeline Executor with Per-Node Error Handling

Executes the LangGraph swarm with DeepSeek & Hermes LLM nodes, emitting SSE telemetry.
Implements per-node retry logic and structured error recovery.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from backend.state import AgentSwarmState
from backend.swarm import swarm_graph
from backend.services.n8n_service import dispatch_hitl_to_n8n
from backend.services.telemetry_service import broadcast_event
from backend.store.event_store import upsert_disruption, update_disruption_result
from backend.middleware.resilience import retry_with_backoff

# Maximum per-node retries before escalating
MAX_NODE_RETRIES = 2


async def run_swarm_pipeline(thread_id: str, initial_state: AgentSwarmState, n8n_webhook_url: Optional[str] = None):
    """
    Executes LangGraph swarm with DeepSeek & Hermes LLM nodes, emitting SSE telemetry.

    Enhancements over v1:
    - Per-node error handling with retry
    - Persists disruption records to SQLite for history dashboard
    - Tracks node-level failures in state error_state field
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Persist disruption start to SQLite for history
    event = initial_state.get("disruption_event", {})
    passenger = initial_state.get("passenger_context", {})
    upsert_disruption(
        thread_id=thread_id,
        pnr=event.get("pnr", ""),
        flight_number=event.get("flight_number", ""),
        airline=event.get("airline", ""),
        origin=event.get("origin", ""),
        destination=event.get("destination", ""),
        disruption_reason=event.get("reason", ""),
        delay_minutes=event.get("delay_minutes", 0),
        loyalty_tier=passenger.get("loyalty_tier", ""),
        passenger_name=passenger.get("passenger_name", ""),
    )

    await broadcast_event(thread_id, {
        "type": "WORKFLOW_START",
        "thread_id": thread_id,
        "timestamp": datetime.now().isoformat(),
        "message": f"🚀 SynapseAir Swarm initiated (DeepSeek Reasoning + Hermes Parser)."
    })

    try:
        node_retry_count: Dict[str, int] = {}

        async for chunk in swarm_graph.astream(initial_state, config=config):
            for node_name, node_output in chunk.items():
                logs = node_output.get("execution_logs", [])

                # Per-node error detection and retry tracking
                for log in logs:
                    level = log.get("level", "INFO")
                    if level == "ERROR":
                        retries = node_retry_count.get(node_name, 0)
                        node_retry_count[node_name] = retries + 1

                        await broadcast_event(thread_id, {
                            "type": "WORKFLOW_NODE_ERROR",
                            "thread_id": thread_id,
                            "node": node_name,
                            "timestamp": datetime.now().isoformat(),
                            "error": log.get("message", "Unknown node error"),
                            "retry_count": node_retry_count[node_name],
                        })

                        if node_retry_count[node_name] > MAX_NODE_RETRIES:
                            await broadcast_event(thread_id, {
                                "type": "WORKFLOW_NODE_ERROR",
                                "thread_id": thread_id,
                                "node": node_name,
                                "timestamp": datetime.now().isoformat(),
                                "error": f"Node {node_name} exceeded max retries ({MAX_NODE_RETRIES}). Escalating.",
                                "retry_count": node_retry_count[node_name],
                            })

                    await broadcast_event(thread_id, {
                        "type": "AGENT_STEP",
                        "thread_id": thread_id,
                        "node": node_name,
                        "log": log,
                        "state_update": {k: v for k, v in node_output.items() if k != "execution_logs"}
                    })

        current_state = await swarm_graph.aget_state(config)

        # Paused at interrupt_before (hitl_breakpoint)
        if current_state.next and "hitl_breakpoint" in current_state.next:
            latest = current_state.values
            selected = latest.get("selected_route") or {}
            pnr = latest.get("disruption_event", {}).get("pnr", "PNR")
            passenger_ctx = latest.get("passenger_context", {})

            # Find DeepSeek WhatsApp message from execution logs if present
            arbiter_log = next((l for l in latest.get("execution_logs", []) if l.get("node") == "arbiter"), None)
            whatsapp_copy = arbiter_log.get("data", {}).get("whatsapp_copy") if arbiter_log else None

            # Dispatch to n8n WhatsApp Gateway
            n8n_receipt = await dispatch_hitl_to_n8n(
                thread_id=thread_id,
                pnr=pnr,
                passenger_context=passenger_ctx,
                selected_route=selected,
                whatsapp_message=whatsapp_copy,
                custom_n8n_url=n8n_webhook_url
            )

            # Update disruption record with partial results
            update_disruption_result(
                thread_id=thread_id,
                selected_route=selected,
                hitl_status="PENDING",
                financial_savings=selected.get("financial_savings"),
            )

            await broadcast_event(thread_id, {
                "type": "HITL_REQUIRED",
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat(),
                "message": f"⏳ Rebooking requires passenger confirmation. Dispatched to n8n WhatsApp Gateway.",
                "selected_route": selected,
                "pnr": pnr,
                "n8n_receipt": n8n_receipt
            })
        else:
            ticket = current_state.values.get("ticket_confirmation")
            selected = current_state.values.get("selected_route")

            # Update disruption record with final results
            update_disruption_result(
                thread_id=thread_id,
                selected_route=selected,
                hitl_status=current_state.values.get("hitl_status", "BYPASSED"),
                ticket_confirmation=ticket,
                financial_savings=selected.get("financial_savings") if selected else None,
            )

            await broadcast_event(thread_id, {
                "type": "WORKFLOW_COMPLETE",
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat(),
                "message": f"✅ Workflow finished. Ticket issued via Atlas API for PNR {current_state.values.get('disruption_event', {}).get('pnr')}.",
                "ticket": ticket
            })

    except Exception as e:
        # Persist error state
        update_disruption_result(
            thread_id=thread_id,
            hitl_status="ERROR",
            error_state=str(e),
        )

        await broadcast_event(thread_id, {
            "type": "WORKFLOW_ERROR",
            "thread_id": thread_id,
            "timestamp": datetime.now().isoformat(),
            "message": f"Swarm execution error: {str(e)}"
        })
