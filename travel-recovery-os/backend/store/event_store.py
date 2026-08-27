"""
store/event_store.py - SQLite Event Store for n8n Webhook Audit Trail

Replaces the in-memory _n8n_event_log list in n8n_service.py with a
persistent SQLite table so webhook dispatches survive process restarts.

Also provides a disruptions table for historical tracking (Phase 3).
"""

import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EVENT_DB_PATH: str = os.getenv(
    "SYNAPSEAIR_EVENT_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "events.sqlite")
)

_db_lock = threading.Lock()


def _ensure_data_dir():
    """Creates the data directory if it does not exist."""
    db_dir = os.path.dirname(os.path.abspath(EVENT_DB_PATH))
    os.makedirs(db_dir, exist_ok=True)


def _get_connection() -> sqlite3.Connection:
    """Returns a new SQLite connection (thread-safe via lock)."""
    _ensure_data_dir()
    conn = sqlite3.connect(EVENT_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ---------------------------------------------------------------------------
# Schema Initialization
# ---------------------------------------------------------------------------
def init_schema():
    """Creates tables if they do not exist."""
    with _db_lock:
        conn = _get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS n8n_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    event_type TEXT NOT NULL DEFAULT 'webhook',
                    status TEXT NOT NULL,
                    target_url TEXT,
                    latency_ms INTEGER,
                    payload_json TEXT,
                    response_body TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_n8n_thread
                    ON n8n_events(thread_id);

                CREATE TABLE IF NOT EXISTS disruptions (
                    thread_id TEXT PRIMARY KEY,
                    pnr TEXT,
                    flight_number TEXT,
                    airline TEXT,
                    origin TEXT,
                    destination TEXT,
                    disruption_reason TEXT,
                    delay_minutes INTEGER,
                    loyalty_tier TEXT,
                    passenger_name TEXT,
                    selected_route_json TEXT,
                    hitl_status TEXT DEFAULT 'PENDING',
                    ticket_confirmation_json TEXT,
                    financial_savings_json TEXT,
                    error_state TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    completed_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_disruptions_created
                    ON disruptions(created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_disruptions_pnr
                    ON disruptions(pnr);
            """)
            conn.commit()
        finally:
            conn.close()


# Initialize schema on module import
init_schema()


# ---------------------------------------------------------------------------
# n8n Event Operations
# ---------------------------------------------------------------------------
def insert_n8n_event(
    thread_id: str,
    status: str,
    target_url: str = "",
    latency_ms: int = 0,
    payload: Optional[Dict[str, Any]] = None,
    response_body: str = "",
    error: str = "",
    event_type: str = "webhook",
) -> int:
    """Inserts an n8n webhook event and returns its row ID."""
    with _db_lock:
        conn = _get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO n8n_events
                   (thread_id, event_type, status, target_url, latency_ms,
                    payload_json, response_body, error, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    thread_id,
                    event_type,
                    status,
                    target_url,
                    latency_ms,
                    json.dumps(payload) if payload else None,
                    response_body[:500] if response_body else None,
                    error,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0
        finally:
            conn.close()


def get_n8n_events(thread_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves n8n events, optionally filtered by thread_id."""
    with _db_lock:
        conn = _get_connection()
        try:
            if thread_id:
                rows = conn.execute(
                    "SELECT * FROM n8n_events WHERE thread_id = ? ORDER BY id DESC LIMIT ?",
                    (thread_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM n8n_events ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Disruption Record Operations (for History Dashboard - Phase 3)
# ---------------------------------------------------------------------------
def upsert_disruption(
    thread_id: str,
    pnr: str = "",
    flight_number: str = "",
    airline: str = "",
    origin: str = "",
    destination: str = "",
    disruption_reason: str = "",
    delay_minutes: int = 0,
    loyalty_tier: str = "",
    passenger_name: str = "",
):
    """Creates or updates a disruption record at workflow start."""
    with _db_lock:
        conn = _get_connection()
        try:
            conn.execute(
                """INSERT INTO disruptions
                   (thread_id, pnr, flight_number, airline, origin, destination,
                    disruption_reason, delay_minutes, loyalty_tier, passenger_name, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(thread_id) DO UPDATE SET
                    pnr=excluded.pnr, flight_number=excluded.flight_number,
                    airline=excluded.airline, origin=excluded.origin,
                    destination=excluded.destination,
                    disruption_reason=excluded.disruption_reason,
                    delay_minutes=excluded.delay_minutes,
                    loyalty_tier=excluded.loyalty_tier,
                    passenger_name=excluded.passenger_name""",
                (
                    thread_id, pnr, flight_number, airline, origin, destination,
                    disruption_reason, delay_minutes, loyalty_tier, passenger_name,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()


def update_disruption_result(
    thread_id: str,
    selected_route: Optional[Dict[str, Any]] = None,
    hitl_status: str = "",
    ticket_confirmation: Optional[Dict[str, Any]] = None,
    financial_savings: Optional[Dict[str, Any]] = None,
    error_state: str = "",
):
    """Updates a disruption record with final results."""
    with _db_lock:
        conn = _get_connection()
        try:
            conn.execute(
                """UPDATE disruptions SET
                    selected_route_json = ?,
                    hitl_status = ?,
                    ticket_confirmation_json = ?,
                    financial_savings_json = ?,
                    error_state = ?,
                    completed_at = ?
                   WHERE thread_id = ?""",
                (
                    json.dumps(selected_route) if selected_route else None,
                    hitl_status,
                    json.dumps(ticket_confirmation) if ticket_confirmation else None,
                    json.dumps(financial_savings) if financial_savings else None,
                    error_state,
                    datetime.now().isoformat(),
                    thread_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()


def get_disruptions(
    limit: int = 50,
    offset: int = 0,
    airline: Optional[str] = None,
    loyalty_tier: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves paginated disruption history with optional filters."""
    with _db_lock:
        conn = _get_connection()
        try:
            query = "SELECT * FROM disruptions WHERE 1=1"
            params: list = []

            if airline:
                query += " AND airline = ?"
                params.append(airline)
            if loyalty_tier:
                query += " AND loyalty_tier = ?"
                params.append(loyalty_tier)
            if status:
                query += " AND hitl_status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def get_disruption_by_thread(thread_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single disruption record by thread_id."""
    with _db_lock:
        conn = _get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM disruptions WHERE thread_id = ?", (thread_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


def get_disruption_stats() -> Dict[str, Any]:
    """Returns aggregate analytics across all disruptions."""
    with _db_lock:
        conn = _get_connection()
        try:
            total = conn.execute("SELECT COUNT(*) FROM disruptions").fetchone()[0]
            completed = conn.execute(
                "SELECT COUNT(*) FROM disruptions WHERE completed_at IS NOT NULL"
            ).fetchone()[0]
            auto_approved = conn.execute(
                "SELECT COUNT(*) FROM disruptions WHERE hitl_status = 'BYPASSED'"
            ).fetchone()[0]
            hitl_required = conn.execute(
                "SELECT COUNT(*) FROM disruptions WHERE hitl_status = 'PENDING' OR hitl_status = 'APPROVED'"
            ).fetchone()[0]
            rejected = conn.execute(
                "SELECT COUNT(*) FROM disruptions WHERE hitl_status = 'REJECTED'"
            ).fetchone()[0]

            # Average resolution time (seconds) for completed disruptions
            avg_time_row = conn.execute(
                """SELECT AVG(
                    julianday(completed_at) - julianday(created_at)
                   ) * 86400.0
                   FROM disruptions WHERE completed_at IS NOT NULL"""
            ).fetchone()
            avg_resolution_sec = round(avg_time_row[0] or 0, 1)

            # Top 5 routes by frequency
            top_routes = conn.execute(
                """SELECT origin || ' -> ' || destination AS route, COUNT(*) AS count
                   FROM disruptions GROUP BY route ORDER BY count DESC LIMIT 5"""
            ).fetchall()

            return {
                "total_disruptions": total,
                "completed": completed,
                "auto_approved": auto_approved,
                "hitl_required": hitl_required,
                "rejected": rejected,
                "auto_approve_rate": round(auto_approved / max(1, total) * 100, 1),
                "hitl_rate": round(hitl_required / max(1, total) * 100, 1),
                "avg_resolution_seconds": avg_resolution_sec,
                "top_routes": [dict(r) for r in top_routes],
            }
        finally:
            conn.close()
