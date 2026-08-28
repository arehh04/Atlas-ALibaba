from typing import Any

from pydantic import BaseModel, Field


class DisruptionPayload(BaseModel):
    """Flight disruption event payload.

    Provide either structured fields (pnr, flight_number, origin, etc.)
    or a raw_text message for the Hermes AI parser to extract automatically.
    """
    raw_text: str | None = Field(
        None,
        description="Raw flight alert text for AI parsing. If provided, structured fields are optional fallbacks.",
        examples=["URGENT NOTAM: CZ3042 KUL-HGH canceled due to typhoon. PNR 8842."],
    )
    pnr: str | None = Field(
        "PNR-8842",
        description="Passenger Name Record / booking reference.",
        examples=["PNR-8842"],
    )
    flight_number: str | None = Field(
        "CZ-3042",
        description="IATA flight number.",
        examples=["CZ-3042"],
    )
    airline: str | None = Field(
        "China Southern Airlines",
        description="Operating airline name.",
        examples=["China Southern Airlines"],
    )
    origin: str | None = Field(
        "KUL",
        description="Origin airport IATA code.",
        examples=["KUL"],
    )
    destination: str | None = Field(
        "HGH",
        description="Destination airport IATA code.",
        examples=["HGH"],
    )
    scheduled_departure: str | None = Field(
        "2026-08-25 09:30",
        description="Scheduled departure date/time (YYYY-MM-DD HH:MM).",
        examples=["2026-08-25 09:30"],
    )
    delay_minutes: int | None = Field(
        default=240,
        description="Delay duration in minutes.",
        examples=[240],
    )
    reason: str | None = Field(
        "Severe Weather / Typhoon Flow Control",
        description="Human-readable disruption reason.",
        examples=["Severe Weather / Typhoon Flow Control"],
    )
    loyalty_tier: str | None = Field(
        default="GOLD",
        description="Passenger loyalty tier: PLATINUM, GOLD, SILVER, or STANDARD.",
        examples=["GOLD"],
    )
    passenger_name: str | None = Field(
        default="Sarah Jenkins",
        description="Full passenger name.",
        examples=["Sarah Jenkins"],
    )
    passenger_phone: str | None = Field(
        default="+60 12-345 6789",
        description="Passenger phone for WhatsApp HITL notifications.",
        examples=["+60 12-345 6789"],
    )
    n8n_webhook_url: str | None = Field(
        None,
        description="Override n8n webhook URL for this disruption (uses global config if omitted).",
    )
    thread_id: str | None = Field(
        None,
        description="Custom thread ID. Auto-generated if omitted.",
    )


class ConsensusPayload(BaseModel):
    """Passenger HITL consensus response."""
    thread_id: str = Field(
        ...,
        description="Swarm thread ID to resume.",
        examples=["synapse-123456"],
    )
    action: str = Field(
        ...,
        description="Passenger decision: APPROVE or REJECT.",
        examples=["APPROVE"],
    )
    selected_flight_id: str | None = Field(
        None,
        description="ID of the selected alternative flight (if multiple options were presented).",
    )
    notes: str | None = Field(
        "Approved via WhatsApp 1-click CTA",
        description="Optional notes from the passenger.",
        examples=["Approved via WhatsApp 1-click CTA"],
    )


class RawTextTestPayload(BaseModel):
    """Raw text input for testing the Hermes AI parser."""
    raw_text: str = Field(
        ...,
        description="Raw flight alert or NOTAM text to parse.",
        examples=["FLIGHT ALERT: Air China CA1890 from KUL to HGH grounded for maintenance. PNR: PNR-STD-5512."],
    )


class PassengerChatPayload(BaseModel):
    """Passenger chat message forwarded to the n8n AI assistant."""
    passenger_message: str = Field(
        ...,
        description="The passenger's chat message.",
        examples=["Can I get a window seat on the new flight?"],
    )
    passenger_name: str | None = Field(
        "Traveler",
        description="Passenger display name.",
        examples=["Traveler"],
    )
    pnr: str | None = Field(
        "PNR-DEMO",
        description="Booking reference for context.",
        examples=["PNR-DEMO"],
    )
    flight_details: dict[str, Any] | None = Field(
        None,
        description="Current proposed flight details for context.",
    )
