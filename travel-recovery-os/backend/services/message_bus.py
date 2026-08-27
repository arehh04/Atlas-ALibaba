"""
services/message_bus.py - Agent-to-Agent Communication Bus

Provides a lightweight in-memory message bus for inter-agent communication.
Agents can publish messages to specific recipients or broadcast to all.

In production, this can be backed by Redis Pub/Sub for cross-process messaging.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio

try:
    from ..state import AgentMessage
except (ImportError, ValueError):
    from state import AgentMessage


# ---------------------------------------------------------------------------
# In-Memory Message Store
# ---------------------------------------------------------------------------
_message_store: Dict[str, List[AgentMessage]] = {}  # thread_id -> messages
_lock = asyncio.Lock()


async def publish_message(
    thread_id: str,
    from_agent: str,
    to_agent: str,
    message_type: str,
    payload: Dict[str, Any],
    correlation_id: str = "",
) -> AgentMessage:
    """
    Publishes a message to the agent message bus.

    Args:
        thread_id: The swarm thread this message belongs to.
        from_agent: Name of the sending agent.
        to_agent: Name of the recipient agent ('*' for broadcast).
        message_type: Type of message ('REQUEST', 'RESPONSE', 'NOTIFICATION', 'WARNING').
        payload: Arbitrary data payload.
        correlation_id: Optional correlation ID for request/response pairing.

    Returns:
        The created AgentMessage.
    """
    message: AgentMessage = {
        "from_agent": from_agent,
        "to_agent": to_agent,
        "message_type": message_type,
        "payload": payload,
        "timestamp": datetime.now().isoformat(),
        "correlation_id": correlation_id or thread_id,
    }

    async with _lock:
        if thread_id not in _message_store:
            _message_store[thread_id] = []
        _message_store[thread_id].append(message)

    return message


async def get_messages_for_agent(
    thread_id: str,
    agent_name: str,
    message_type: Optional[str] = None,
) -> List[AgentMessage]:
    """
    Retrieves all messages addressed to a specific agent in a thread.

    Args:
        thread_id: The swarm thread to query.
        agent_name: The agent to filter messages for.
        message_type: Optional filter by message type.

    Returns:
        List of matching AgentMessages.
    """
    async with _lock:
        messages = _message_store.get(thread_id, [])
        result = [
            m for m in messages
            if (m.get("to_agent") == agent_name or m.get("to_agent") == "*")
        ]
        if message_type:
            result = [m for m in result if m.get("message_type") == message_type]
        return result


async def get_all_messages(thread_id: str) -> List[AgentMessage]:
    """Returns all messages for a thread."""
    async with _lock:
        return list(_message_store.get(thread_id, []))


async def clear_messages(thread_id: str):
    """Clears all messages for a thread."""
    async with _lock:
        _message_store.pop(thread_id, None)


def get_message_store() -> Dict[str, List[AgentMessage]]:
    """Returns the raw message store (for inspection/debugging)."""
    return _message_store
