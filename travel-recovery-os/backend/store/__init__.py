"""
store/ - Persistent storage layer for SynapseAir

Provides:
- Redis-backed SSE event bus (replaces in-memory dicts)
- SQLite LangGraph checkpointer (replaces MemorySaver)
- SQLite event store for n8n webhook audit trail
"""
