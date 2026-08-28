# Execution Control & Flow Management

<cite>
**Referenced Files in This Document**
- [swarm.py](file://travel-recovery-os/backend/swarm.py)
- [state.py](file://travel-recovery-os/backend/state.py)
- [swarm_runner.py](file://travel-recovery-os/backend/services/swarm_runner.py)
- [arbiter.py](file://travel-recovery-os/backend/agents/arbiter.py)
- [sentinel.py](file://travel-recovery-os/backend/agents/sentinel.py)
- [sqlite_checkpointer.py](file://travel-recovery-os/backend/store/sqlite_checkpointer.py)
- [event_store.py](file://travel-recovery-os/backend/store/event_store.py)
- [n8n_service.py](file://travel-recovery-os/backend/services/n8n_service.py)
- [resilience.py](file://travel-recovery-os/backend/middleware/resilience.py)
- [websocket.py](file://travel-recovery-os/backend/api/routers/websocket.py)
</cite>

## Table of Contents
1. Introduction
2. Project Structure
3. Core Components
4. Architecture Overview
5. Detailed Component Analysis
6. Dependency Analysis
7. Performance Considerations
8. Troubleshooting Guide
9. Conclusion

## Introduction
This document explains the execution control mechanisms that coordinate a multi-agent travel disruption recovery workflow. It focuses on:
- Conditional routing functions that direct flow based on agent outputs and state
- Human-in-the-loop (HITL) breakpoints with durable pause/resume
- Workflow interruption and resumption across distributed components
- Error handling strategies to maintain integrity during distributed agent processing

The system uses a LangGraph StateGraph to orchestrate agents, persists checkpoints for durability, and integrates external systems (n8n WhatsApp gateway, Atlas ticketing API) with resilience patterns.

## Project Structure
At a high level:
- The graph is defined and compiled in the swarm module, which wires nodes, edges, and conditional routing
- A runner executes the graph, streams telemetry, handles HITL pauses, and updates persistent records
- Agents perform specialized tasks (interception, scoring, compensation, baggage, multi-leg)
- External integrations are wrapped with retry and circuit breaker patterns
- A WebSocket endpoint enables bidirectional HITL decisions and resume flows
- SQLite stores both checkpoints and an audit trail for events and disruptions

```mermaid
graph TB
Client["Client / Frontend"] --> WS["WebSocket Endpoint"]
Runner["Swarm Runner"] --> Graph["LangGraph StateGraph"]
Graph --> Sentinel["Sentinel Node"]
Graph --> Profile["Profile Node"]
Graph --> Scout["Scout Node"]
Graph --> Baggage["Baggage Node"]
Graph --> MultiLeg["MultiLeg Node"]
Graph --> Arbiter["Arbiter Node"]
Graph --> Compensation["Compensation Node"]
Graph --> HITL["HITL Breakpoint"]
Graph --> Execution["Execution Node"]
HITL --> N8N["n8n Service"]
Execution --> Atlas["Atlas Ticketing"]
Runner --> Store["Event Store (SQLite)"]
Graph --> Checkpoint["Checkpointer (SQLite/Memory)"]
```

**Diagram sources**
- [swarm.py:162-227](file://travel-recovery-os/backend/swarm.py#L162-L227)
- [swarm_runner.py:36-216](file://travel-recovery-os/backend/services/swarm_runner.py#L36-L216)
- [n8n_service.py:51-202](file://travel-recovery-os/backend/services/n8n_service.py#L51-L202)
- [event_store.py:47-101](file://travel-recovery-os/backend/store/event_store.py#L47-L101)
- [sqlite_checkpointer.py:43-54](file://travel-recovery-os/backend/store/sqlite_checkpointer.py#L43-L54)

**Section sources**
- [swarm.py:162-227](file://travel-recovery-os/backend/swarm.py#L162-L227)
- [swarm_runner.py:36-216](file://travel-recovery-os/backend/services/swarm_runner.py#L36-L216)

## Core Components
- State schema defines the central data model shared by all nodes and services
- Swarm graph defines nodes, edges, and conditional routing logic
- Runner orchestrates execution, streaming, error detection, and persistence
- Arbiter computes ensemble scores and determines HITL bypass/approval thresholds
- n8n service dispatches HITL notifications and records durable audit trails
- Resilience middleware provides retry with backoff and circuit breakers
- WebSocket endpoint supports real-time HITL decisions and graph resume
- Event store persists disruption lifecycle and webhook interactions

**Section sources**
- [state.py:130-167](file://travel-recovery-os/backend/state.py#L130-L167)
- [swarm.py:162-227](file://travel-recovery-os/backend/swarm.py#L162-L227)
- [swarm_runner.py:36-216](file://travel-recovery-os/backend/services/swarm_runner.py#L36-L216)
- [arbiter.py:128-244](file://travel-recovery-os/backend/agents/arbiter.py#L128-L244)
- [n8n_service.py:51-202](file://travel-recovery-os/backend/services/n8n_service.py#L51-L202)
- [resilience.py:25-80](file://travel-recovery-os/backend/middleware/resilience.py#L25-L80)
- [websocket.py:21-195](file://travel-recovery-os/backend/api/routers/websocket.py#L21-L195)
- [event_store.py:166-239](file://travel-recovery-os/backend/store/event_store.py#L166-L239)

## Architecture Overview
The workflow begins with a disruption signal intercepted by the sentinel node, then fans out to parallel agents (profile, scout, baggage, and optionally multi-leg). Their outputs converge at the arbiter, which scores candidates and decides whether HITL is required. If needed, the graph pauses at the HITL breakpoint, sends a message via n8n, and waits for passenger consent. On approval or bypass, execution proceeds to issue a ticket; otherwise it remains paused or terminates with an error.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Runner as "Swarm Runner"
participant Graph as "LangGraph"
participant Arbiter as "Arbiter"
participant Comp as "Compensation"
participant HITL as "HITL Breakpoint"
participant N8N as "n8n Service"
participant Exec as "Execution Node"
participant Atlas as "Atlas API"
Client->>Runner : Start workflow
Runner->>Graph : astream(initial_state)
Graph->>Arbiter : Score routes + decide HITL
Arbiter-->>Graph : selected_route, hitl_status
Graph->>Comp : Calculate compensation
Comp-->>Graph : compensation_result
alt HITL required
Graph->>HITL : Pause before node
HITL->>N8N : Dispatch WhatsApp template
N8N-->>HITL : Audit record persisted
Note over HITL : Wait for passenger decision
Client->>Graph : Update state via WebSocket
Graph->>Exec : Resume if approved/bypassed
else Auto-approved/bypassed
Graph->>Exec : Issue ticket
end
Exec->>Atlas : Issue ticket
Atlas-->>Exec : Ticket receipt
Exec-->>Runner : Finalize and persist
```

**Diagram sources**
- [swarm.py:94-127](file://travel-recovery-os/backend/swarm.py#L94-L127)
- [swarm.py:130-160](file://travel-recovery-os/backend/swarm.py#L130-L160)
- [swarm_runner.py:133-198](file://travel-recovery-os/backend/services/swarm_runner.py#L133-L198)
- [n8n_service.py:51-202](file://travel-recovery-os/backend/services/n8n_service.py#L51-L202)
- [websocket.py:95-195](file://travel-recovery-os/backend/api/routers/websocket.py#L95-L195)

## Detailed Component Analysis

### Conditional Routing Functions
- route_after_arbiter: Routes first to compensation calculation, then to HITL or execution depending on hitl_status and presence of compensation result
- route_after_compensation: Routes to execution if status is BYPASSED or APPROVED; otherwise to HITL
- route_disruption_type: Chooses whether to spawn the multi-leg agent based on disruption keywords

These functions read the current state and return the next node name, enabling dynamic branching without hard-coded paths.

```mermaid
flowchart TD
Start(["After Arbiter"]) --> CheckComp{"Compensation Result Present?"}
CheckComp --> |No| ToComp["Route to Compensation"]
CheckComp --> |Yes| Status{"Hitl Status"}
Status --> |BYPASSED or APPROVED| ToExec["Route to Execution"]
Status --> |PENDING or REJECTED| ToHITL["Route to HITL Breakpoint"]
ToComp --> AfterComp["After Compensation"]
AfterComp --> NextStatus{"Hitl Status"}
NextStatus --> |BYPASSED or APPROVED| ToExec
NextStatus --> |PENDING or REJECTED| ToHITL
```

**Diagram sources**
- [swarm.py:94-127](file://travel-recovery-os/backend/swarm.py#L94-L127)

**Section sources**
- [swarm.py:94-127](file://travel-recovery-os/backend/swarm.py#L94-L127)

### Human-in-the-Loop Breakpoints
- The graph compiles with interrupt_before set to the HITL breakpoint node
- When reached, the runner detects the pause, dispatches a WhatsApp notification via n8n, and persists partial results
- The client can send a HITL decision via WebSocket; the server updates the graph state and resumes execution if approved

```mermaid
sequenceDiagram
participant Graph as "LangGraph"
participant Runner as "Swarm Runner"
participant N8N as "n8n Service"
participant WS as "WebSocket"
participant Exec as "Execution Node"
Graph->>Runner : Stream chunks
Runner->>Graph : Check next node
alt Paused at HITL
Runner->>N8N : Dispatch HITL notification
N8N-->>Runner : Persist event
WS->>Graph : Update hitl_status via aupdate_state
alt Approved
Graph->>Exec : Resume from checkpoint
else Rejected
Graph-->>Runner : Stay paused or terminate
end
end
```

**Diagram sources**
- [swarm.py:222-227](file://travel-recovery-os/backend/swarm.py#L222-L227)
- [swarm_runner.py:133-176](file://travel-recovery-os/backend/services/swarm_runner.py#L133-L176)
- [n8n_service.py:51-202](file://travel-recovery-os/backend/services/n8n_service.py#L51-L202)
- [websocket.py:95-195](file://travel-recovery-os/backend/api/routers/websocket.py#L95-L195)

**Section sources**
- [swarm.py:222-227](file://travel-recovery-os/backend/swarm.py#L222-L227)
- [swarm_runner.py:133-176](file://travel-recovery-os/backend/services/swarm_runner.py#L133-L176)
- [websocket.py:95-195](file://travel-recovery-os/backend/api/routers/websocket.py#L95-L195)

### Workflow Interruption and Resumption
- Durable checkpointer ensures state survives process restarts; currently configured to use memory saver but designed to support SQLite-based persistence
- On HITL pause, the runner persists disruption details and emits telemetry
- On approval, the graph resumes using the same thread_id, continuing from the checkpoint until completion

```mermaid
flowchart TD
Init["Start Workflow"] --> Run["Run astream()"]
Run --> CheckNext{"Next Node == HITL?"}
CheckNext --> |Yes| Pause["Pause at HITL"]
Pause --> Persist["Persist Disruption Record"]
Persist --> Wait["Wait for Decision"]
Wait --> Decision{"Decision Type"}
Decision --> |Approve| Resume["Resume from Checkpoint"]
Decision --> |Reject| EndPaused["Remain Paused/Terminate"]
CheckNext --> |No| Continue["Continue Execution"]
Resume --> Complete["Complete Workflow"]
Continue --> Complete
```

**Diagram sources**
- [sqlite_checkpointer.py:43-54](file://travel-recovery-os/backend/store/sqlite_checkpointer.py#L43-L54)
- [swarm_runner.py:133-198](file://travel-recovery-os/backend/services/swarm_runner.py#L133-L198)
- [websocket.py:143-195](file://travel-recovery-os/backend/api/routers/websocket.py#L143-L195)

**Section sources**
- [sqlite_checkpointer.py:43-54](file://travel-recovery-os/backend/store/sqlite_checkpointer.py#L43-L54)
- [swarm_runner.py:133-198](file://travel-recovery-os/backend/services/swarm_runner.py#L133-L198)
- [websocket.py:143-195](file://travel-recovery-os/backend/api/routers/websocket.py#L143-L195)

### Error Handling Strategies
- Per-node error detection: The runner tracks errors emitted by nodes and increments retry counters
- Max retries per node: Exceeding the threshold triggers escalation and telemetry
- Circuit breakers: External calls (LLM, Atlas, n8n) are protected by circuit breakers to avoid cascading failures
- Retry with backoff: Transient failures are retried with exponential backoff and jitter
- Persistent error state: Errors are recorded in the disruption record for observability

```mermaid
flowchart TD
Start(["Node Execution"]) --> EmitLogs["Emit Logs"]
EmitLogs --> IsError{"Level == ERROR?"}
IsError --> |No| Next["Proceed"]
IsError --> |Yes| IncRetry["Increment Retry Counter"]
IncRetry --> OverMax{"Exceeded Max Retries?"}
OverMax --> |No| Backoff["Backoff Retry"]
Backoff --> TryAgain["Retry Node"]
TryAgain --> EmitLogs
OverMax --> |Yes| Escalate["Escalate and Broadcast Error"]
Escalate --> PersistErr["Persist Error State"]
PersistErr --> Next
```

**Diagram sources**
- [swarm_runner.py:96-124](file://travel-recovery-os/backend/services/swarm_runner.py#L96-L124)
- [resilience.py:25-80](file://travel-recovery-os/backend/middleware/resilience.py#L25-L80)
- [resilience.py:97-213](file://travel-recovery-os/backend/middleware/resilience.py#L97-L213)
- [event_store.py:206-239](file://travel-recovery-os/backend/store/event_store.py#L206-L239)

**Section sources**
- [swarm_runner.py:96-124](file://travel-recovery-os/backend/services/swarm_runner.py#L96-L124)
- [resilience.py:25-80](file://travel-recovery-os/backend/middleware/resilience.py#L25-L80)
- [resilience.py:97-213](file://travel-recovery-os/backend/middleware/resilience.py#L97-L213)
- [event_store.py:206-239](file://travel-recovery-os/backend/store/event_store.py#L206-L239)

### Complex Decision Trees and Integrity Maintenance
- Arbiter computes ensemble scores combining base score, punctuality, baggage feasibility, compensation impact, and connection time
- Confidence intervals and scoring breakdowns provide transparency and risk bounds
- Loyalty tier and score thresholds determine automatic bypass or HITL requirement
- State fields aggregate candidate routes and connecting flights via additive reducers, ensuring consistent merging across parallel branches
- Execution logs accumulate per node, providing a complete audit trail for each step

```mermaid
classDiagram
class AgentSwarmState {
+thread_id
+disruption_event
+passenger_context
+candidate_routes
+selected_route
+hitl_status
+execution_logs
+ticket_confirmation
+sla_constraints
+baggage_context
+compensation_result
+connecting_flights
+agent_messages
+error_state
}
class FlightRoute {
+flight_id
+flight_number
+airline
+origin
+destination
+departure_time
+arrival_time
+duration_hours
+layovers
+stops_detail
+cabin_class
+available_seats
+base_fare_usd
+score
+scoring_rationale
+financial_savings
+scoring_breakdown
}
class CompensationResult {
+regulation
+eligible
+amount_usd
+currency
+reason
+details
}
class ConnectingFlight {
+segment_number
+flight_number
+airline
+origin
+destination
+departure_time
+arrival_time
+connection_time_minutes
+minimum_connection_time_minutes
+connection_viable
+status
}
AgentSwarmState --> FlightRoute : "contains"
AgentSwarmState --> CompensationResult : "contains"
AgentSwarmState --> ConnectingFlight : "contains"
```

**Diagram sources**
- [state.py:20-167](file://travel-recovery-os/backend/state.py#L20-L167)

**Section sources**
- [arbiter.py:25-113](file://travel-recovery-os/backend/agents/arbiter.py#L25-L113)
- [arbiter.py:128-244](file://travel-recovery-os/backend/agents/arbiter.py#L128-L244)
- [state.py:130-167](file://travel-recovery-os/backend/state.py#L130-L167)

## Dependency Analysis
Key dependencies and coupling:
- Swarm depends on agents, tools, and checkpointer to build and compile the graph
- Runner depends on swarm graph, n8n service, telemetry, and event store
- Arbiter depends on LLM service and state models
- n8n service depends on resilience middleware and event store
- WebSocket endpoint depends on swarm graph and telemetry manager
- Event store provides persistence for both webhook events and disruption records

```mermaid
graph LR
Swarm["swarm.py"] --> Agents["agents/*"]
Swarm --> Tools["tools/atlas_client.py"]
Swarm --> Checkpointer["store/sqlite_checkpointer.py"]
Runner["services/swarm_runner.py"] --> Swarm
Runner --> N8N["services/n8n_service.py"]
Runner --> Telemetry["services/telemetry_service.py"]
Runner --> Store["store/event_store.py"]
Arbiter["agents/arbiter.py"] --> LLM["services/llm_service.py"]
N8N --> Resilience["middleware/resilience.py"]
N8N --> Store
WS["api/routers/websocket.py"] --> Swarm
WS --> Telemetry
```

**Diagram sources**
- [swarm.py:162-227](file://travel-recovery-os/backend/swarm.py#L162-L227)
- [swarm_runner.py:36-216](file://travel-recovery-os/backend/services/swarm_runner.py#L36-L216)
- [arbiter.py:128-244](file://travel-recovery-os/backend/agents/arbiter.py#L128-L244)
- [n8n_service.py:51-202](file://travel-recovery-os/backend/services/n8n_service.py#L51-L202)
- [websocket.py:21-195](file://travel-recovery-os/backend/api/routers/websocket.py#L21-L195)

**Section sources**
- [swarm.py:162-227](file://travel-recovery-os/backend/swarm.py#L162-L227)
- [swarm_runner.py:36-216](file://travel-recovery-os/backend/services/swarm_runner.py#L36-L216)
- [n8n_service.py:51-202](file://travel-recovery-os/backend/services/n8n_service.py#L51-L202)
- [websocket.py:21-195](file://travel-recovery-os/backend/api/routers/websocket.py#L21-L195)

## Performance Considerations
- Parallel fan-out reduces latency by executing profile, scout, baggage, and multi-leg concurrently
- Ensemble scoring consolidates multiple signals into a single decision metric, minimizing downstream complexity
- Circuit breakers prevent overload on external services and improve overall throughput under failure conditions
- Additive reducers merge lists efficiently across branches, avoiding expensive recomputation
- Streaming telemetry keeps clients updated without blocking execution

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and diagnostics:
- HITL not resuming: Verify WebSocket connection and ensure hitl_status is updated correctly; confirm graph state retrieval succeeds
- n8n dispatch failures: Check circuit breaker state and retry logs; inspect event store for HTTP responses and errors
- Node errors exceeding retries: Review execution logs for repeated errors; consider adjusting max retries or fixing upstream dependencies
- No active session: Ensure thread_id matches the original workflow run; confirm checkpoint exists and is accessible

**Section sources**
- [websocket.py:95-195](file://travel-recovery-os/backend/api/routers/websocket.py#L95-L195)
- [n8n_service.py:127-182](file://travel-recovery-os/backend/services/n8n_service.py#L127-L182)
- [swarm_runner.py:96-124](file://travel-recovery-os/backend/services/swarm_runner.py#L96-L124)
- [event_store.py:107-160](file://travel-recovery-os/backend/store/event_store.py#L107-L160)

## Conclusion
The system implements robust execution control through conditional routing, durable HITL breakpoints, and resilient integration patterns. The LangGraph StateGraph coordinates complex decision trees with transparent scoring and confidence bounds, while per-node error handling and circuit breakers preserve integrity across distributed agent processing. Persistence via SQLite ensures workflows can be interrupted and resumed reliably, and real-time communication via WebSocket enables responsive human oversight.

[No sources needed since this section summarizes without analyzing specific files]