"""
services/websocket_manager.py - WebSocket Connection Lifecycle Manager

Manages bidirectional WebSocket connections for real-time telemetry
and HITL consensus communication.
"""

import asyncio
from typing import Any

from fastapi import WebSocket


class WebSocketManager:
    """
    Manages WebSocket connections per thread_id.
    Supports multiple clients per thread (fan-out).
    """

    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, thread_id: str, websocket: WebSocket):
        """Accepts and registers a WebSocket connection for a thread."""
        await websocket.accept()
        async with self._lock:
            if thread_id not in self._connections:
                self._connections[thread_id] = set()
            self._connections[thread_id].add(websocket)

    async def disconnect(self, thread_id: str, websocket: WebSocket):
        """Removes a WebSocket connection."""
        async with self._lock:
            if thread_id in self._connections:
                self._connections[thread_id].discard(websocket)
                if not self._connections[thread_id]:
                    del self._connections[thread_id]

    async def send_json(self, thread_id: str, data: dict[str, Any]):
        """Sends a JSON message to all connected clients for a thread."""
        connections = self._connections.get(thread_id, set()).copy()
        dead: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            await self.disconnect(thread_id, ws)

    async def broadcast(self, data: dict[str, Any]):
        """Broadcasts to ALL connected clients across all threads."""
        all_threads = list(self._connections.keys())
        for thread_id in all_threads:
            await self.send_json(thread_id, data)

    def get_connection_count(self, thread_id: str | None = None) -> int:
        """Returns the number of active connections."""
        if thread_id:
            return len(self._connections.get(thread_id, set()))
        return sum(len(conns) for conns in self._connections.values())

    def get_active_threads(self) -> list[str]:
        """Returns list of thread IDs with active connections."""
        return list(self._connections.keys())


# Singleton instance
ws_manager = WebSocketManager()
