"""
state.py - LangGraph State Definition for SynapseAir (Travel Recovery OS)

Defines the central TypedDict state schema managed by LangGraph across the
multi-agent disruption recovery workflow.

Phase 2 Enhancements:
- BaggageContext for baggage transfer evaluation
- CompensationResult for passenger rights calculation
- ConnectingFlight for multi-leg disruption handling
- AgentMessage for inter-agent communication bus
- error_state for per-node failure tracking
"""

import operator
from typing import Annotated, Any

from typing_extensions import TypedDict


class DisruptionEvent(TypedDict, total=False):
    """Payload details for incoming flight cancellation / delay."""
    raw_text: str
    pnr: str
    flight_number: str
    airline: str
    origin: str
    destination: str
    scheduled_departure: str
    delay_minutes: int
    reason: str


class PassengerContext(TypedDict, total=False):
    """Passenger loyalty profile and constraint rules."""
    passenger_id: str
    passenger_name: str
    phone_number: str
    loyalty_tier: str  # e.g., 'PLATINUM', 'GOLD', 'SILVER', 'STANDARD'
    max_layover_hours: float
    requires_direct_flight: bool
    preferred_cabin: str
    seat_preference: str  # 'WINDOW', 'AISLE'
    dietary_requirements: str | None


class FlightRoute(TypedDict, total=False):
    """Candidate or selected alternative flight route from Atlas API."""
    flight_id: str
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration_hours: float
    layovers: int
    stops_detail: list[str]
    cabin_class: str
    available_seats: int
    base_fare_usd: float
    score: float  # Computed by Arbiter agent
    scoring_rationale: str
    financial_savings: dict[str, float] | None
    scoring_breakdown: dict[str, Any] | None


class ExecutionLog(TypedDict, total=False):
    """Telemetry log entry emitted during agent node execution for SSE streaming."""
    timestamp: str
    node: str
    agent_name: str
    level: str  # 'INFO', 'WARN', 'DECISION', 'SUCCESS', 'ERROR'
    message: str
    data: dict[str, Any]


# ---------------------------------------------------------------------------
# Phase 2: New TypedDicts for Enhanced Agents
# ---------------------------------------------------------------------------

class BaggageContext(TypedDict, total=False):
    """Baggage transfer evaluation results from the Baggage Agent."""
    checked_bags: int
    special_items: list[str]  # e.g., 'sports_equipment', 'pet', 'fragile'
    interline_eligible: bool
    baggage_transfer_confirmed: bool
    transfer_notes: str
    estimated_transfer_time_minutes: int


class CompensationResult(TypedDict, total=False):
    """Passenger rights compensation calculation from the Compensation Agent."""
    regulation: str  # 'EU261', 'DOT', 'MAS', 'NONE'
    eligible: bool
    amount_usd: float
    currency: str
    reason: str
    details: str


class ConnectingFlight(TypedDict, total=False):
    """Multi-leg flight segment for connecting itinerary disruptions."""
    segment_number: int
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    connection_time_minutes: int
    minimum_connection_time_minutes: int
    connection_viable: bool
    status: str  # 'ON_TIME', 'DELAYED', 'CANCELLED', 'MISSED'


class AgentMessage(TypedDict, total=False):
    """Inter-agent communication message for the message bus."""
    from_agent: str
    to_agent: str  # '*' for broadcast
    message_type: str  # 'REQUEST', 'RESPONSE', 'NOTIFICATION', 'WARNING'
    text: str  # Conversational text message for group chat display
    payload: dict[str, Any]
    timestamp: str
    correlation_id: str


# ---------------------------------------------------------------------------
# Central Swarm State
# ---------------------------------------------------------------------------

class AgentSwarmState(TypedDict, total=False):
    """
    Central LangGraph State Schema for the SynapseAir Disruption Recovery Swarm.

    Fields:
      - disruption_event: Ingested disruption payload (PNR, canceled flight, delay).
      - passenger_context: Resolved passenger profile and constraints.
      - candidate_routes: List of alternative routes found by Scout (via Atlas API),
                          combined via operator.add reducer for parallel branch merging.
      - selected_route: Final chosen optimal flight evaluated by Arbiter.
      - hitl_status: Decision flag ('PENDING', 'APPROVED', 'REJECTED', 'BYPASSED').
      - execution_logs: Additive log collection for real-time telemetry streaming.
      - ticket_confirmation: Resulting e-ticket and updated PNR record from Atlas.
      - thread_id: Unique trace identifier for session checkpoints and SSE subscription.
      - sla_constraints: Derived SLA rules from Profile Agent.
      - baggage_context: Baggage transfer evaluation from Baggage Agent.
      - compensation_result: Passenger rights compensation from Compensation Agent.
      - connecting_flights: Multi-leg flight segments from MultiLeg Agent.
      - agent_messages: Inter-agent communication messages.
      - error_state: Per-node error tracking for resilience.
    """
    thread_id: str
    disruption_event: DisruptionEvent
    passenger_context: PassengerContext
    candidate_routes: Annotated[list[FlightRoute], operator.add]
    selected_route: FlightRoute | None
    hitl_status: str  # 'PENDING' | 'APPROVED' | 'REJECTED' | 'BYPASSED'
    execution_logs: Annotated[list[ExecutionLog], operator.add]
    ticket_confirmation: dict[str, Any] | None
    sla_constraints: dict[str, Any] | None

    # Phase 2: Enhanced state fields
    baggage_context: BaggageContext | None
    compensation_result: CompensationResult | None
    connecting_flights: Annotated[list[ConnectingFlight], operator.add]
    agent_messages: Annotated[list[AgentMessage], operator.add]
    error_state: dict[str, Any] | None
