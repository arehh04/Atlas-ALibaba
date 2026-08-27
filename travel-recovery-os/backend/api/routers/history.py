"""
api/routers/history.py - Historical Disruption Data API

Provides endpoints for querying past disruption runs, analytics, and statistics.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException

from backend.store.event_store import (
    get_disruptions,
    get_disruption_by_thread,
    get_disruption_stats,
)

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", summary="List disruption events")
async def list_disruptions(
    limit: int = 50,
    offset: int = 0,
    airline: Optional[str] = None,
    loyalty_tier: Optional[str] = None,
    status: Optional[str] = None,
):
    """Paginated list of past disruption events with optional filters.

    - **limit**: Max results (default 50)
    - **offset**: Pagination offset
    - **airline**: Filter by airline name
    - **loyalty_tier**: Filter by tier (PLATINUM/GOLD/SILVER/STANDARD)
    - **status**: Filter by HITL status (BYPASSED/APPROVED/REJECTED/PENDING)
    """
    results = get_disruptions(
        limit=limit,
        offset=offset,
        airline=airline,
        loyalty_tier=loyalty_tier,
        status=status,
    )
    return {
        "total": len(results),
        "limit": limit,
        "offset": offset,
        "disruptions": results,
    }


@router.get("/stats", summary="Disruption analytics")
async def disruption_statistics():
    """Aggregate analytics across all disruptions.

    Returns totals, auto-approve/HITL rates, average resolution time,
    and top 5 most common disruption routes.
    """
    return get_disruption_stats()


@router.get(
    "/{thread_id}",
    summary="Disruption detail",
    responses={
        200: {"description": "Full disruption event details"},
        404: {"description": "Disruption not found"},
    },
)
async def get_disruption_detail(thread_id: str):
    """Full detail of a specific disruption run by thread_id."""
    result = get_disruption_by_thread(thread_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Disruption {thread_id} not found")
    return result
