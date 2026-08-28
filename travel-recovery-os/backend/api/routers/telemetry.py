import asyncio
import json

from backend.services.telemetry_service import get_event_history, subscribe, unsubscribe
from backend.swarm import swarm_graph
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["telemetry"])

@router.get(
    "/stream/{thread_id}",
    summary="SSE live telemetry stream",
    description="Server-Sent Events stream for real-time agent activity. Replays historical events first, then streams live. Sends keep-alive every 15s.",
    response_description="text/event-stream with JSON event payloads",
)
async def stream_telemetry(thread_id: str, request: Request):
    """SSE live log stream adhering to text/event-stream specification."""
    queue = await subscribe(thread_id)
    history = await get_event_history(thread_id)
    
    async def event_generator():
        for hist_event in history:
            yield f"data: {json.dumps(hist_event)}\n\n"
                
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            await unsubscribe(thread_id, queue)
                
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get(
    "/threads/{thread_id}/state",
    summary="Inspect thread state",
    description="Returns the current LangGraph checkpointer state for a given thread, including agent outputs and pending nodes.",
    responses={
        200: {"description": "Thread state snapshot"},
        404: {"description": "Thread not found"},
    },
)
async def get_thread_state(thread_id: str):
    """Inspect current LangGraph checkpointer state."""
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state_snapshot = await swarm_graph.aget_state(config)
    except Exception:
        raise HTTPException(status_code=404, detail="Thread state not found")
    if not state_snapshot.values:
        raise HTTPException(status_code=404, detail="Thread state not found")
    return {
        "thread_id": thread_id,
        "values": state_snapshot.values,
        "next": state_snapshot.next,
        "created_at": state_snapshot.created_at
    }
