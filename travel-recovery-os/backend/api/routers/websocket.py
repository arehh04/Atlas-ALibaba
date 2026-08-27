"""
api/routers/websocket.py - WebSocket Endpoint for Bidirectional Communication

Provides a WebSocket endpoint at /ws/{thread_id} for:
1. Receiving real-time telemetry events (server -> client)
2. Sending HITL consensus decisions (client -> server)
3. Streaming agent messages
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.websocket_manager import ws_manager
from backend.services.telemetry_service import broadcast_event, get_event_history
from backend.swarm import swarm_graph

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """Bidirectional WebSocket for real-time telemetry and HITL decisions.

    **Client messages:**
    - `{"type": "PING"}` → responds with PONG
    - `{"type": "HITL_DECISION", "action": "APPROVE|REJECT", "notes": "..."}` → processes consensus

    **Server messages:**
    - `WS_CONNECTED` — connection confirmed
    - All SSE telemetry events replayed then streamed live
    - `HITL_CONFIRMED` — decision acknowledged
    - `WS_ERROR` — error details
    """
    await ws_manager.connect(thread_id, websocket)

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "WS_CONNECTED",
            "thread_id": thread_id,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })

        # Replay historical events
        history = await get_event_history(thread_id)
        for event in history:
            try:
                await websocket.send_json(event)
            except Exception:
                break

        # Listen for incoming client messages
        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type", "")

                if msg_type == "PING":
                    await websocket.send_json({"type": "PONG"})

                elif msg_type == "HITL_DECISION":
                    action = data.get("action", "APPROVE").upper()
                    notes = data.get("notes", "")
                    await _handle_hitl_decision(thread_id, action, notes, websocket)

                else:
                    await websocket.send_json({
                        "type": "WS_ERROR",
                        "message": f"Unknown message type: {msg_type}"
                    })

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "WS_ERROR",
                    "message": "Invalid JSON"
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "WS_ERROR",
                "message": str(e)
            })
        except Exception:
            pass
    finally:
        await ws_manager.disconnect(thread_id, websocket)


async def _handle_hitl_decision(thread_id: str, action: str, notes: str, websocket: WebSocket):
    """Handles a HITL decision received via WebSocket."""
    config = {"configurable": {"thread_id": thread_id}}

    try:
        current_state = await swarm_graph.aget_state(config)
        if not current_state.values:
            await websocket.send_json({
                "type": "WS_ERROR",
                "message": f"No active session for thread {thread_id}"
            })
            return

        hitl_status = "APPROVED" if "APPROV" in action else "REJECTED"

        await swarm_graph.aupdate_state(
            config,
            {"hitl_status": hitl_status},
            as_node="hitl_breakpoint"
        )

        await broadcast_event(thread_id, {
            "type": "CONSENSUS_RECEIVED",
            "thread_id": thread_id,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "action": hitl_status,
            "notes": notes,
            "message": f"📲 WebSocket Consensus: Passenger {hitl_status} the rebooking.",
            "source": "websocket"
        })

        await websocket.send_json({
            "type": "HITL_CONFIRMED",
            "action": hitl_status,
            "thread_id": thread_id,
        })

        # Resume graph if approved
        if hitl_status == "APPROVED":
            asyncio.create_task(_resume_graph(thread_id, config))

    except Exception as e:
        await websocket.send_json({
            "type": "WS_ERROR",
            "message": f"HITL processing error: {str(e)}"
        })


async def _resume_graph(thread_id: str, config: dict):
    """Resumes the LangGraph from checkpoint after HITL approval."""
    try:
        async for chunk in swarm_graph.astream(None, config=config):
            for node_name, node_output in chunk.items():
                logs = node_output.get("execution_logs", [])
                for log in logs:
                    await ws_manager.send_json(thread_id, {
                        "type": "AGENT_STEP",
                        "thread_id": thread_id,
                        "node": node_name,
                        "log": log,
                        "state_update": {k: v for k, v in node_output.items() if k != "execution_logs"}
                    })

        final_state = await swarm_graph.aget_state(config)
        ticket = final_state.values.get("ticket_confirmation")
        await ws_manager.send_json(thread_id, {
            "type": "WORKFLOW_COMPLETE",
            "thread_id": thread_id,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "message": "✅ Resumed workflow complete. Ticket finalized.",
            "ticket": ticket
        })
    except Exception as ex:
        await ws_manager.send_json(thread_id, {
            "type": "WORKFLOW_ERROR",
            "thread_id": thread_id,
            "message": f"Resume error: {str(ex)}"
        })
