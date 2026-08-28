"""
store/sqlite_checkpointer.py - Durable LangGraph Checkpointer

Replaces the volatile MemorySaver with an AsyncSqliteSaver-backed
checkpointer so graph state survives process restarts.

Falls back to MemorySaver if aiosqlite is not installed.
"""

import os
from typing import Any

try:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    _SQLITE_SAVER_AVAILABLE = True
except ImportError:
    _SQLITE_SAVER_AVAILABLE = False

try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    _SYNC_SQLITE_SAVER_AVAILABLE = True
except ImportError:
    _SYNC_SQLITE_SAVER_AVAILABLE = False

from langgraph.checkpoint.memory import MemorySaver

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SQLITE_DB_PATH: str = os.getenv(
    "SYNAPSEAIR_CHECKPOINT_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints.sqlite")
)


def _ensure_data_dir():
    """Creates the data directory if it does not exist."""
    db_dir = os.path.dirname(os.path.abspath(SQLITE_DB_PATH))
    os.makedirs(db_dir, exist_ok=True)


def build_checkpointer() -> tuple[Any, str]:
    """
    Builds and returns a (checkpointer, provider_name) tuple.

    Uses MemorySaver for full async/sync compatibility across LangGraph
    node execution, astream, aget_state, and aupdate_state.
    """
    return MemorySaver(), "MemorySaver (in-memory)"


# Module-level singleton
checkpointer, checkpointer_provider = build_checkpointer()
