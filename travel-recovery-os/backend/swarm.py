"""
swarm.py - LangGraph StateGraph Orchestration for SynapseAir

Implements:
1. Parallel execution of Profile, Scout, and Baggage agents following Sentinel.
2. Arbiter node aggregation and conditional routing.
3. Compensation node for passenger rights calculation.
4. Human-in-the-Loop breakpoint pause / resume with durable SQLite checkpointer.
5. Final automated ticketing execution via Atlas API.
"""

from datetime import datetime
from typing import Any, Dict, Literal
from langgraph.graph import StateGraph, END, START

try:
    from .state import AgentSwarmState, ExecutionLog
    from .agents.sentinel import sentinel_node
    from .agents.profile import profile_agent_node as profile_node
    from .agents.scout import scout_node
    from .agents.arbiter import arbiter_node
    from .agents.baggage import baggage_node
    from .agents.compensation import compensation_node
    from .agents.multileg import multileg_node
    from .tools.atlas_client import issue_ticket
    from .store.sqlite_checkpointer import checkpointer, checkpointer_provider
except (ImportError, ValueError):
    from backend.state import AgentSwarmState, ExecutionLog
    from backend.agents.sentinel import sentinel_node
    from backend.agents.profile import profile_agent_node as profile_node
    from backend.agents.scout import scout_node
    from backend.agents.arbiter import arbiter_node
    from backend.agents.baggage import baggage_node
    from backend.agents.compensation import compensation_node
    from backend.agents.multileg import multileg_node
    from backend.tools.atlas_client import issue_ticket
    from backend.store.sqlite_checkpointer import checkpointer, checkpointer_provider


async def execution_node(state: AgentSwarmState) -> Dict[str, Any]:
    """
    Execution Node: Issues the final rebooked ticket via Atlas API once approved or bypassed.
    """
    selected_route = state.get("selected_route")
    event = state.get("disruption_event", {})
    pnr = event.get("pnr", "UNKNOWN_PNR")

    if not selected_route:
        log_entry: ExecutionLog = {
            "timestamp": datetime.now().isoformat(),
            "node": "execution",
            "agent_name": "Atlas Ticketing Executor",
            "level": "ERROR",
            "message": "❌ Execution failed: No candidate route was selected for ticketing.",
            "data": {"pnr": pnr}
        }
        return {"execution_logs": [log_entry]}

    flight_id = selected_route.get("flight_id", "ATLAS-AUTO")
    ticket_receipt = await issue_ticket(pnr, flight_id)

    now_iso = datetime.now().isoformat()
    log_entry = {
        "timestamp": now_iso,
        "node": "execution",
        "agent_name": "Atlas Ticketing Executor",
        "level": "SUCCESS",
        "message": f"🎟️ Ticket ISSUED successfully via Atlas API! PNR {pnr} confirmed on {selected_route.get('flight_number')} ({selected_route.get('cabin_class')}). E-Ticket: {ticket_receipt.get('e_ticket_number')}.",
        "data": {
            "ticket": ticket_receipt,
            "flight": selected_route
        }
    }

    return {
        "ticket_confirmation": ticket_receipt,
        "execution_logs": [log_entry]
    }


def route_after_arbiter(state: AgentSwarmState) -> Literal["compensation_node", "execution_node", "hitl_breakpoint"]:
    """
    Conditional routing function evaluating Arbiter's consensus decision.
    Always routes through compensation_node first for passenger rights evaluation,
    then to HITL or execution based on Arbiter decision.
    """
    status = state.get("hitl_status", "PENDING")
    # Route to compensation calculation first, then it will forward to HITL or execution
    if state.get("compensation_result") is None:
        return "compensation_node"
    if status == "BYPASSED" or status == "APPROVED":
        return "execution_node"
    return "hitl_breakpoint"


def route_after_compensation(state: AgentSwarmState) -> Literal["hitl_breakpoint", "execution_node"]:
    """Routes after compensation calculation based on HITL status."""
    status = state.get("hitl_status", "PENDING")
    if status == "BYPASSED" or status == "APPROVED":
        return "execution_node"
    return "hitl_breakpoint"


def should_spawn_multileg(state: AgentSwarmState) -> Literal["multileg_and_forward", "forward_only"]:
    """Determines if multi-leg agent should be spawned based on disruption complexity."""
    disruption = state.get("disruption_event", {})
    # If disruption mentions connections or multi-leg, spawn the agent
    reason = (disruption.get("reason", "") + " " + disruption.get("raw_text", "")).lower()
    if any(kw in reason for kw in ["connection", "connecting", "multi-leg", "missed connection", "transfer"]):
        return "multileg_and_forward"
    return "forward_only"


async def hitl_breakpoint_node(state: AgentSwarmState) -> Dict[str, Any]:
    """
    HITL Breakpoint Node: Pauses execution waiting for passenger approval via n8n / WhatsApp.
    """
    pnr = state.get("disruption_event", {}).get("pnr", "PNR")
    selected_flight = state.get("selected_route", {}).get("flight_number", "FLT")
    compensation = state.get("compensation_result", {})

    comp_msg = ""
    if compensation and compensation.get("eligible"):
        comp_msg = f" Compensation: ${compensation.get('amount_usd', 0)} under {compensation.get('regulation', 'N/A')}."

    log_entry: ExecutionLog = {
        "timestamp": datetime.now().isoformat(),
        "node": "hitl_breakpoint",
        "agent_name": "HITL n8n Gateway",
        "level": "WARN",
        "message": f"⏸️ Graph paused at HITL breakpoint. WhatsApp consent message dispatched to passenger for flight {selected_flight} (PNR: {pnr}).{comp_msg}",
        "data": {
            "pnr": pnr,
            "status": "WAITING_FOR_WHATSAPP_REPLY",
            "compensation": compensation
        }
    }
    return {
        "execution_logs": [log_entry]
    }


def build_swarm_graph():
    """
    Constructs and compiles the SynapseAir LangGraph StateGraph.

    Graph Topology:
    START -> Sentinel -> [Profile || Scout || Baggage || (conditional) MultiLeg] -> Arbiter -> Compensation -> HITL/Execution -> END
    """
    workflow = StateGraph(AgentSwarmState)

    # Register Nodes
    workflow.add_node("sentinel", sentinel_node)
    workflow.add_node("profile", profile_node)
    workflow.add_node("scout", scout_node)
    workflow.add_node("baggage", baggage_node)
    workflow.add_node("arbiter", arbiter_node)
    workflow.add_node("compensation_node", compensation_node)
    workflow.add_node("multileg", multileg_node)
    workflow.add_node("hitl_breakpoint", hitl_breakpoint_node)
    workflow.add_node("execution_node", execution_node)

    # Edges: Start -> Sentinel
    workflow.add_edge(START, "sentinel")

    # Parallel fan-out: Sentinel -> Profile, Scout, Baggage, MultiLeg
    workflow.add_edge("sentinel", "profile")
    workflow.add_edge("sentinel", "scout")
    workflow.add_edge("sentinel", "baggage")
    workflow.add_edge("sentinel", "multileg")

    # Fan-in: Profile, Scout, Baggage, & MultiLeg -> Arbiter
    workflow.add_edge("profile", "arbiter")
    workflow.add_edge("scout", "arbiter")
    workflow.add_edge("baggage", "arbiter")
    workflow.add_edge("multileg", "arbiter")

    # Conditional Routing from Arbiter -> Compensation or HITL/Execution
    workflow.add_conditional_edges(
        "arbiter",
        route_after_arbiter,
        {
            "compensation_node": "compensation_node",
            "execution_node": "execution_node",
            "hitl_breakpoint": "hitl_breakpoint"
        }
    )

    # From compensation to HITL or execution
    workflow.add_conditional_edges(
        "compensation_node",
        route_after_compensation,
        {
            "execution_node": "execution_node",
            "hitl_breakpoint": "hitl_breakpoint"
        }
    )

    # From hitl_breakpoint to execution_node (executed upon resume)
    workflow.add_edge("hitl_breakpoint", "execution_node")
    workflow.add_edge("execution_node", END)

    # Compile with durable checkpointer and interrupt before hitl_breakpoint node
    compiled_graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["hitl_breakpoint"]
    )
    return compiled_graph, checkpointer


# Global compiled graph instance & checkpointer
swarm_graph, swarm_checkpointer = build_swarm_graph()
