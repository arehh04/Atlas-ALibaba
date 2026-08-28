"""
services/telemetry_service.py - Real-Time SSE Broadcaster with Redis-Backed Persistence

Delegates to store/redis_broker.py for durable pub/sub and event history.
Falls back to in-memory mode when Redis is unavailable.
Includes PII masking for passenger data before broadcast.
"""

import copy
import re
from typing import Any

from backend.store.redis_broker import (
    broadcast_event as _redis_broadcast,
)
from backend.store.redis_broker import (
    get_event_history as _redis_history,
)
from backend.store.redis_broker import (
    get_fallback_history,
    get_fallback_listeners,
)
from backend.store.redis_broker import (
    subscribe_thread as _redis_subscribe,
)
from backend.store.redis_broker import (
    unsubscribe_thread as _redis_unsubscribe,
)


def mask_pii(data: dict) -> dict:
    """Masks personally identifiable information before SSE broadcast."""
    masked = copy.deepcopy(data)

    def apply_mask(ctx):
        if ctx.get("phone_number"):
            ctx["phone_number"] = re.sub(r'\d', '*', ctx["phone_number"][:-4]) + ctx["phone_number"][-4:]
        if ctx.get("passenger_name"):
            parts = ctx["passenger_name"].split()
            if len(parts) > 1:
                ctx["passenger_name"] = f"{parts[0]} {parts[-1][0]}***"

    if "state_update" in masked and isinstance(masked["state_update"], dict):
        if "passenger_context" in masked["state_update"]:
            apply_mask(masked["state_update"]["passenger_context"])

    if "passenger_context" in masked and isinstance(masked["passenger_context"], dict):
        apply_mask(masked["passenger_context"])

    return masked


async def broadcast_event(thread_id: str, event_data: dict[str, Any]):
    """Broadcast an SSE event payload to all active client streams for thread_id (Redis-backed) and WebSocket."""
    masked_event = mask_pii(event_data)
    await _redis_broadcast(thread_id, masked_event)
    try:
        from backend.services.websocket_manager import ws_manager
        await ws_manager.send_json(thread_id, masked_event)
    except Exception:
        pass


async def subscribe(thread_id: str):
    """Creates a subscription queue for real-time SSE events."""
    return await _redis_subscribe(thread_id)


async def unsubscribe(thread_id: str, queue):
    """Removes a subscription queue."""
    await _redis_unsubscribe(thread_id, queue)


async def get_event_history(thread_id: str) -> list[dict[str, Any]]:
    """Retrieves persisted event history for a thread."""
    return await _redis_history(thread_id)


def get_thread_listeners():
    """Returns the in-memory fallback listeners (for SSE endpoint compatibility)."""
    return get_fallback_listeners()


def get_thread_event_history():
    """Returns the in-memory fallback history (for SSE endpoint compatibility)."""
    return get_fallback_history()
