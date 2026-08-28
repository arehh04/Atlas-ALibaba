---
kind: business_term
name: Business Glossary
category: business_term
scope:
    - '**'
---

### SynapseAir
- Definition：Internal product name for the autonomous airline disruption recovery system built for the Alibaba Cloud x Atlas Agentic AI Hackathon. The brand appears in the frontend logo, navbar, and documentation.
- Aliases：synapseair

### Disruption Signal
- Definition：Incoming flight cancellation or severe delay notification (either structured JSON or raw NOTAM/SMS text) that triggers the SynapseAir recovery workflow. Ingested via the `/webhook/disruption` endpoint and parsed by the Sentinel agent.
- Aliases：disruption trigger、disruption event

### HITL Breakpoint
- Definition：Human-in-the-Loop pause point in the LangGraph workflow where the Arbiter decides rebooking needs passenger consent. The graph interrupts at the `hitl_breakpoint` node and resumes only after a consensus reply arrives via `/webhook/consensus`.
- Aliases：HITL、human-in-the-loop breakpoint

### Consensus
- Definition：Passenger approval or rejection of a proposed rebooking, received through the `/webhook/consensus` endpoint (simulated via WhatsApp in the demo). Used to resume a paused LangGraph at the HITL breakpoint.
- Aliases：passenger consent、consensus reply

### BYPASSED / PENDING
- Definition：Arbiter decision states for a disruption recovery proposal. `BYPASSED` means the agent auto-approves the rebooking based on loyalty-tier SLAs; `PENDING` means passenger consent is required and the graph pauses at the HITL breakpoint.
- Aliases：auto-approved、needs-consent

### Thread
- Definition：A single disruption recovery session identified by a `thread_id`. Each thread carries its own LangGraph state, checkpointer records, and SSE stream. Unknown thread IDs return 404 from state inspection endpoints.
- Aliases：thread_id、recovery thread

### PNR
- Definition：Passenger Name Record — the booking reference used to identify the affected traveler throughout the recovery workflow. Displayed in the frontend navbar as the active PNR.
- Aliases：booking reference

### Loyalty Tier
- Definition：Passenger status level (PLATINUM, GOLD, SILVER, STANDARD) that drives SLA constraints and financial liability calculations in the Profile agent. Determines whether a rebooking can be auto-approved or requires consent.
- Aliases：tier、loyalty level

### Financial Arbitrage Engine
- Definition：In-house calculation layer that quantifies the dollar value of a recovery proposal — hotel penalty avoidance, SLA liability reduction, and airline savings — used to score and present recovery options to operators.
- Aliases：savings calculator、liability engine

### Command Center
- Definition：Frontend user-facing dashboard (Vue 3 dark-mode UI) that displays the live recovery pipeline, agent messages, route map, terminal logs, and mobile HITL simulator for operators monitoring disruption recoveries.
- Aliases：dashboard、ops console
