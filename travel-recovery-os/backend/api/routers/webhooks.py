import uuid
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from backend.api.dependencies import verify_api_key
from backend.schemas.api_models import DisruptionPayload, ConsensusPayload
from backend.state import AgentSwarmState, DisruptionEvent, PassengerContext
from backend.services.swarm_runner import run_swarm_pipeline
from backend.swarm import swarm_graph
from backend.services.telemetry_service import broadcast_event

router = APIRouter(prefix="/webhook", tags=["webhooks"])

@router.post(
    "/disruption",
    summary="Ingest flight disruption & trigger swarm",
    description="Accepts a structured or raw-text flight disruption event and starts the multi-agent recovery swarm. Returns a thread_id for tracking.",
    responses={
        200: {"description": "Swarm initiated successfully"},
        401: {"description": "Missing or invalid API key"},
    },
)
async def webhook_disruption(payload: DisruptionPayload, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Ingests flight cancellation (structured or raw text) and triggers the recovery swarm.
    """
    thread_id = payload.thread_id or f"synapse-{uuid.uuid4().hex[:8]}"
    
    event_dict: DisruptionEvent = {
        "raw_text": payload.raw_text,
        "pnr": payload.pnr or "PNR-8842",
        "flight_number": payload.flight_number or "CZ-3042",
        "airline": payload.airline or "China Southern Airlines",
        "origin": payload.origin or "KUL",
        "destination": payload.destination or "HGH",
        "scheduled_departure": payload.scheduled_departure or "2026-08-25 09:30",
        "delay_minutes": payload.delay_minutes or 240,
        "reason": payload.reason or "Severe Weather / Air Traffic Flow Control"
    }
    
    passenger_dict: PassengerContext = {
        "loyalty_tier": payload.loyalty_tier or "GOLD",
        "passenger_name": payload.passenger_name or "Sarah Jenkins",
        "phone_number": payload.passenger_phone or "+60 12-345 6789"
    }
    
    initial_state: AgentSwarmState = {
        "thread_id": thread_id,
        "disruption_event": event_dict,
        "passenger_context": passenger_dict,
        "candidate_routes": [],
        "selected_route": None,
        "hitl_status": "PENDING",
        "execution_logs": [],
        "ticket_confirmation": None
    }
    
    import asyncio
    asyncio.create_task(
        run_swarm_pipeline(
            thread_id=thread_id,
            initial_state=initial_state,
            n8n_webhook_url=payload.n8n_webhook_url
        )
    )
    
    return {
        "status": "PROCESSING",
        "thread_id": thread_id,
        "stream_url": f"/stream/{thread_id}",
        "message": f"SynapseAir Swarm initiated for thread {thread_id}."
    }

@router.post(
    "/consensus",
    summary="Submit passenger HITL decision",
    description="Receives a passenger's APPROVE/REJECT response (from WhatsApp or in-app) and resumes or stops the recovery workflow.",
    responses={
        200: {"description": "Decision processed; workflow resumed or stopped"},
        401: {"description": "Missing or invalid API key"},
        404: {"description": "No active session for the given thread_id"},
    },
)
async def webhook_consensus(payload: ConsensusPayload, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Receives passenger WhatsApp/n8n reply, updates checkpointer state, and resumes execution.
    """
    thread_id = payload.thread_id
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        current_state = await swarm_graph.aget_state(config)
    except Exception:
        current_state = None
    if not current_state or not current_state.values:
        raise HTTPException(status_code=404, detail=f"No active session found for thread_id {thread_id}")
        
    action_upper = payload.action.upper()
    hitl_status = "APPROVED" if "APPROV" in action_upper else "REJECTED"
    
    await swarm_graph.aupdate_state(
        config,
        {"hitl_status": hitl_status},
        as_node="hitl_breakpoint"
    )
    
    await broadcast_event(thread_id, {
        "type": "CONSENSUS_RECEIVED",
        "thread_id": thread_id,
        "timestamp": datetime.now().isoformat(),
        "action": hitl_status,
        "notes": payload.notes,
        "message": f"📲 WhatsApp Consensus received: Passenger {hitl_status} the rebooking option."
    })
    
    if hitl_status == "APPROVED":
        async def resume_graph():
            try:
                async for chunk in swarm_graph.astream(None, config=config):
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

                        for log in logs:
                            if not isinstance(log, dict):
                                log = {"message": str(log), "level": "INFO", "timestamp": datetime.now().isoformat()}

                            await broadcast_event(thread_id, {
                                "type": "AGENT_STEP",
                                "thread_id": thread_id,
                                "node": node_name,
                                "log": log,
                                "state_update": {k: v for k, v in node_output.items() if k != "execution_logs"}
                            })
                            
                final_state = await swarm_graph.aget_state(config)
                state_vals = final_state.values if isinstance(getattr(final_state, "values", None), dict) else {}
                ticket = state_vals.get("ticket_confirmation")
                await broadcast_event(thread_id, {
                    "type": "WORKFLOW_COMPLETE",
                    "thread_id": thread_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": f"✅ Resumed workflow complete. Ticket finalized.",
                    "ticket": ticket
                })
            except Exception as ex:
                await broadcast_event(thread_id, {
                    "type": "WORKFLOW_ERROR",
                    "thread_id": thread_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Resume error: {str(ex)}"
                })
                
        import asyncio
        asyncio.create_task(resume_graph())
        return {
            "status": "RESUMED",
            "thread_id": thread_id,
            "action": hitl_status,
            "message": "Graph resumed from checkpointer to finalize ticket."
        }
    else:
        return {
            "status": "REJECTED",
            "thread_id": thread_id,
            "action": hitl_status,
            "message": "Passenger rejected alternative route. Workflow stopped."
        }
