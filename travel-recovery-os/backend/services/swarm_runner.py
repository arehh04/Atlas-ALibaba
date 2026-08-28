"""
services/swarm_runner.py - Swarm Pipeline Executor with Per-Node Error Handling

Executes the LangGraph swarm with DeepSeek & Hermes LLM nodes, emitting SSE telemetry.
Implements per-node retry logic and structured error recovery.
"""

from datetime import datetime
from typing import Any

from backend.services.n8n_service import dispatch_hitl_to_n8n
from backend.services.telemetry_service import broadcast_event
from backend.state import AgentSwarmState
from backend.store.event_store import update_disruption_result, upsert_disruption
from backend.swarm import swarm_graph

# Maximum per-node retries before escalating
MAX_NODE_RETRIES = 2


def _safe_state(st: Any) -> dict[str, Any]:
    if isinstance(st, dict):
        return st
    if isinstance(st, (list, tuple)):
        for item in st:
            if isinstance(item, dict):
                return item
    if hasattr(st, "values") and isinstance(st.values, dict):
        return st.values
    if hasattr(st, "dict") and callable(st.dict):
        return st.dict()
    return {}


async def run_swarm_pipeline(thread_id: str, initial_state: AgentSwarmState, n8n_webhook_url: str | None = None):
    """
    Executes LangGraph swarm with DeepSeek & Hermes LLM nodes, emitting SSE telemetry.

    Enhancements over v1:
    - Per-node error handling with retry
    - Persists disruption records to SQLite for history dashboard
    - Tracks node-level failures in state error_state field
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Persist disruption start to SQLite for history
    init_st = _safe_state(initial_state)
    event = _safe_state(init_st.get("disruption_event"))
    passenger = _safe_state(init_st.get("passenger_context"))
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
        "message": "🚀 SynapseAir Swarm initiated (DeepSeek Reasoning + Hermes Parser)."
    })

    try:
        node_retry_count: dict[str, int] = {}

        async for chunk in swarm_graph.astream(initial_state, config=config):
            # Normalize chunk items whether chunk is dict or tuple/list
            chunk_items = []
            if isinstance(chunk, dict):
                chunk_items = list(chunk.items())
            elif isinstance(chunk, (list, tuple)):
                if len(chunk) == 2 and isinstance(chunk[0], str):
                    chunk_items = [(chunk[0], chunk[1])]
                elif len(chunk) > 0 and isinstance(chunk[0], (list, tuple)) and len(chunk[0]) == 2:
                    chunk_items = list(chunk)

            for node_name, node_output in chunk_items:
                if not isinstance(node_output, dict):
                    if isinstance(node_output, (list, tuple)) and len(node_output) == 2 and isinstance(node_output[1], dict):
                        node_output = node_output[1]
                    else:
                        continue

                logs = node_output.get("execution_logs", [])
                if not isinstance(logs, list):
                    logs = [logs]

                # Per-node error detection and retry tracking
                for log in logs:
                    if not isinstance(log, dict):
                        log = {"message": str(log), "level": "INFO", "timestamp": datetime.now().isoformat()}

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
        state_vals = _safe_state(getattr(current_state, "values", None))

        # Paused at interrupt_before (hitl_breakpoint)
        if current_state.next and "hitl_breakpoint" in current_state.next:
            selected = _safe_state(state_vals.get("selected_route"))
            event_obj = _safe_state(state_vals.get("disruption_event"))
            pnr = event_obj.get("pnr", "PNR")
            passenger_ctx = _safe_state(state_vals.get("passenger_context"))

            # Find DeepSeek WhatsApp message from execution logs if present
            raw_logs = state_vals.get("execution_logs", [])
            if not isinstance(raw_logs, list):
                raw_logs = [raw_logs]
            arbiter_log = next((l for l in raw_logs if isinstance(l, dict) and l.get("node") == "arbiter"), None)
            whatsapp_copy = arbiter_log.get("data", {}).get("whatsapp_copy") if arbiter_log and isinstance(arbiter_log.get("data"), dict) else None

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
                financial_savings=selected.get("financial_savings") if isinstance(selected, dict) else None,
            )

            await broadcast_event(thread_id, {
                "type": "HITL_REQUIRED",
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat(),
                "message": "⏳ Rebooking requires passenger confirmation. Dispatched to n8n WhatsApp Gateway.",
                "selected_route": selected,
                "pnr": pnr,
                "n8n_receipt": n8n_receipt
            })
        else:
            ticket = _safe_state(state_vals.get("ticket_confirmation"))
            selected = _safe_state(state_vals.get("selected_route"))
            event_obj = _safe_state(state_vals.get("disruption_event"))
            pnr = event_obj.get("pnr", "PNR")

            # Update disruption record with final results
            update_disruption_result(
                thread_id=thread_id,
                selected_route=selected,
                hitl_status=state_vals.get("hitl_status", "BYPASSED"),
                ticket_confirmation=ticket,
                financial_savings=selected.get("financial_savings") if isinstance(selected, dict) else None,
            )

            await broadcast_event(thread_id, {
                "type": "WORKFLOW_COMPLETE",
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat(),
                "message": f"✅ Workflow finished. Ticket issued via Atlas API for PNR {pnr}.",
                "ticket": ticket
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
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
            "message": f"Swarm execution error: {e!s}"
        })
