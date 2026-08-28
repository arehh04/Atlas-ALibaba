"""
store/redis_broker.py - Redis-Backed SSE Event Bus

Replaces the in-memory _thread_listeners and _thread_event_history dicts
in telemetry_service.py with Redis Pub/Sub and Stream persistence.

Features:
- Redis Pub/Sub for real-time fan-out to connected SSE clients
- Redis Streams for durable event history with TTL-based expiry
- Graceful fallback to in-memory mode when Redis is unavailable
"""

import asyncio
import json
import os
from typing import Any

try:
    import redis.asyncio as aioredis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REDIS_URL: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
STREAM_TTL_SECONDS: int = int(os.getenv("STREAM_TTL_SECONDS", "3600"))  # 1 hour
STREAM_PREFIX: str = "synapseair:events:"
CHANNEL_PREFIX: str = "synapseair:channel:"


# ---------------------------------------------------------------------------
# Redis Connection Singleton
# ---------------------------------------------------------------------------
_redis_pool: Any | None = None
_redis_failed: bool = False


async def get_redis() -> Any | None:
    """Returns a shared Redis connection, or None if Redis is unavailable."""
    global _redis_pool, _redis_failed
    if not _REDIS_AVAILABLE or _redis_failed:
        return None
    if os.getenv("USE_REDIS", "false").lower() not in ("true", "1"):
        _redis_failed = True
        return None
    if _redis_pool is None:
        try:
            _redis_pool = aioredis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.5,
                retry_on_timeout=False,
            )
            await _redis_pool.ping()
        except Exception:
            _redis_failed = True
            _redis_pool = None
    return _redis_pool


async def close_redis():
    """Closes the Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        try:
            await _redis_pool.close()
        except Exception:
            pass
        _redis_pool = None


# ---------------------------------------------------------------------------
# In-Memory Fallback State (mirrors old telemetry_service behavior)
# ---------------------------------------------------------------------------
_fallback_listeners: dict[str, list[asyncio.Queue]] = {}
_fallback_history: dict[str, list[dict[str, Any]]] = {}


# ---------------------------------------------------------------------------
# Public API: Broadcast & Subscribe
# ---------------------------------------------------------------------------
async def broadcast_event(thread_id: str, event_data: dict[str, Any]):
    """
    Broadcasts an SSE event to all active listeners for a given thread_id.

    Strategy:
    1. Persist event to Redis Stream (with TTL).
    2. Publish event to Redis Pub/Sub channel for real-time fan-out.
    3. Fallback to in-memory queues if Redis is unavailable.
    """
    serialized = json.dumps(event_data)

    r = await get_redis()
    if r is not None:
        try:
            stream_key = f"{STREAM_PREFIX}{thread_id}"
            channel_key = f"{CHANNEL_PREFIX}{thread_id}"

            # Persist to Redis Stream
            await r.xadd(stream_key, {"data": serialized}, maxlen=500)
            await r.expire(stream_key, STREAM_TTL_SECONDS)

            # Publish to Pub/Sub for live listeners
            await r.publish(channel_key, serialized)
            return
        except Exception:
            pass  # Fall through to in-memory fallback

    # In-memory fallback
    if thread_id not in _fallback_history:
        _fallback_history[thread_id] = []
    _fallback_history[thread_id].append(event_data)

    queues = _fallback_listeners.get(thread_id, [])
    for q in queues:
        await q.put(event_data)


async def subscribe_thread(thread_id: str) -> asyncio.Queue:
    """
    Creates a subscription queue for a thread_id.

    Returns an asyncio.Queue that will receive all future events.
    Uses Redis Pub/Sub when available, in-memory otherwise.
    """
    queue: asyncio.Queue = asyncio.Queue()

    r = await get_redis()
    if r is not None:
        try:
            # Register in-memory queue for local fan-out from pubsub listener
            if thread_id not in _fallback_listeners:
                _fallback_listeners[thread_id] = []
            _fallback_listeners[thread_id].append(queue)

            # Start a background task to read from Redis Pub/Sub
            asyncio.create_task(_redis_pubsub_reader(r, thread_id, queue))
            return queue
        except Exception:
            pass

    # Fallback
    if thread_id not in _fallback_listeners:
        _fallback_listeners[thread_id] = []
    _fallback_listeners[thread_id].append(queue)
    return queue


async def unsubscribe_thread(thread_id: str, queue: asyncio.Queue):
    """Removes a subscription queue for a thread_id."""
    listeners = _fallback_listeners.get(thread_id, [])
    if queue in listeners:
        listeners.remove(queue)


async def get_event_history(thread_id: str) -> list[dict[str, Any]]:
    """
    Retrieves historical events for a thread_id.

    Reads from Redis Stream first, falls back to in-memory history.
    """
    r = await get_redis()
    if r is not None:
        try:
            stream_key = f"{STREAM_PREFIX}{thread_id}"
            raw_entries = await r.xrange(stream_key)
            events = []
            for _entry_id, fields in raw_entries:
                data_str = fields.get("data", "{}")
                events.append(json.loads(data_str))
            return events
        except Exception:
            pass

    return list(_fallback_history.get(thread_id, []))


def get_fallback_listeners() -> dict[str, list[asyncio.Queue]]:
    """Returns the in-memory fallback listeners dict (for compatibility)."""
    return _fallback_listeners


def get_fallback_history() -> dict[str, list[dict[str, Any]]]:
    """Returns the in-memory fallback history dict (for compatibility)."""
    return _fallback_history


# ---------------------------------------------------------------------------
# Internal: Redis Pub/Sub Reader Task
# ---------------------------------------------------------------------------
async def _redis_pubsub_reader(r: Any, thread_id: str, queue: asyncio.Queue):
    """Background task that reads from Redis Pub/Sub and fans out to local queue."""
    channel_key = f"{CHANNEL_PREFIX}{thread_id}"
    try:
        pubsub = r.pubsub()
        await pubsub.subscribe(channel_key)
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    event_data = json.loads(message["data"])
                    await queue.put(event_data)
                except (json.JSONDecodeError, KeyError):
                    continue
    except asyncio.CancelledError:
        pass
    except Exception:
        pass
    finally:
        try:
            await pubsub.unsubscribe(channel_key)
            await pubsub.close()
        except Exception:
            pass
