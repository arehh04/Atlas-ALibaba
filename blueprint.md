# SYSTEM CONTEXT

Act as a Principal AI Engineer. We are building "SynapseAir" for the Alibaba Cloud x Atlas Agentic AI Hackathon. The deadline is 6 days away. We need production-ready, highly modular Python code focused on demonstrating a multi-agent workflow for airline disruption recovery.

# PROJECT OVERVIEW

SynapseAir is an Autonomous Disruption Swarm. It intercepts flight cancellation webhooks, evaluates passenger constraints, queries the Atlas Sandbox API for alternative routes, scores them, and uses an n8n webhook to ping the user on WhatsApp for human-in-the-loop (HITL) 1-click rebooking.

# TECH STACK

- Backend: Python 3.12+, FastAPI, Pydantic v2
- Orchestration: LangGraph (StateGraph)
- LLMs: Deepseek V4 Flash (Main reasoning) and Hermes (Local function calling/parsing)
- Communication: n8n (External webhooks)

# FILE STRUCTURE TO GENERATE

Please scaffold the following repository structure and generate the complete code for each file:

/travel-recovery-os
├── main.py # FastAPI app and webhook endpoints
├── state.py # LangGraph TypedDict state definitions
├── swarm.py # LangGraph StateGraph compilation and routing logic
├── agents/
│ ├── **init**.py
│ ├── sentinel.py # Parses incoming webhook, initiates state
│ ├── profile.py # Mock passenger constraint logic
│ ├── scout.py # Atlas API mock tool caller
│ └── arbiter.py # Scores routes, decides if HITL is needed
├── tools/
│ ├── **init**.py
│ └── atlas_client.py # Mock functions for Atlas API (search_flights, book_pnr)
└── requirements.txt

# EXECUTION STEPS & CODE REQUIREMENTS

## STEP 1: Define the State (`state.py`)

Create a LangGraph `TypedDict` called `AgentSwarmState`. It must include:

- `disruption_event`: Dict containing PNR, canceled flight, and delay minutes.
- `passenger_context`: Dict with loyalty tier and max layover tolerance.
- `candidate_routes`: Annotated list (operator.add) of available flights.
- `selected_route`: Dict of the final chosen flight.
- `hitl_status`: String ('PENDING', 'APPROVED', 'REJECTED', 'BYPASSED').

## STEP 2: Build the Atlas Tools (`tools/atlas_client.py`)

Create mock asynchronous Python functions that simulate the Atlas Sandbox API:

- `search_alternative_flights(origin, destination, date)`: Returns JSON of 2-3 mock flights.
- `issue_ticket(pnr, new_flight_id)`: Simulates ticketing success.

## STEP 3: Implement the Agents (`agents/`)

Write the node functions for LangGraph. Use standard LangChain/LangGraph messaging.

- `sentinel_node`: Extracts data from the disruption payload.
- `profile_node`: Appends mock passenger rules (e.g., "Must be direct flight if Gold tier").
- `scout_node`: Uses the `search_alternative_flights` tool.
- `arbiter_node`: A deterministic or LLM-based function that scores the `candidate_routes`. If the score is high, set `hitl_status = 'BYPASSED'`. If ambiguous, set to `hitl_status = 'PENDING'`.

## STEP 4: Orchestrate the Graph (`swarm.py`)

Build the `StateGraph`.

- Set parallel execution for `profile_node` and `scout_node` after `sentinel_node`.
- Join them at `arbiter_node`.
- Add a conditional edge after `arbiter_node`: if `hitl_status == 'PENDING'`, route to a human-in-the-loop breakpoint (`interrupt_before`).
- Compile the graph using LangGraph's `MemorySaver` (SQLite checkpointer) so we can pause and resume state via n8n.

## STEP 5: FastAPI Endpoints (`main.py`)

Expose the following endpoints:

1. `POST /webhook/disruption`: Receives flight cancellation JSON. Initiates the LangGraph run using an async background task. Pings an external n8n webhook URL if `interrupt_before` is hit.
2. `POST /webhook/consensus`: Receives the user's WhatsApp reply (from n8n). Retrieves the paused LangGraph thread using its `thread_id` and resumes execution to finalize the booking.
3. `GET /stream/{thread_id}`: An SSE (Server-Sent Events) endpoint that yields real-time agent execution logs (for the hackathon demo UI).

# SYSTEM CONTEXT UPDATE: FULL-STACK AI APPLICATION

Instead of a basic Python backend, this is a Full-Stack application. The backend remains FastAPI + LangGraph, but the frontend will be a Vue 3 dashboard used to visualize the AI agents in real-time.

# DIRECTORY STRUCTURE UPDATE

/travel-recovery-os
├── /backend # (FastAPI, LangGraph, Agents, Tools go here)
└── /frontend # (Vue 3, Vite, TailwindCSS go here)

## STEP 6: Vue 3 Real-Time Command Center

Scaffold a Vite + Vue 3 frontend application in the `/frontend` directory.

- Install TailwindCSS for styling. Use a sleek, "Dark Mode Airline Operations" aesthetic (slate grays, neon blue/green accents).
- Create a main dashboard component (`SwarmDashboard.vue`) with three primary visual panels:
  1. Trigger Panel: A button to manually fire the mock disruption payload to the FastAPI backend.
  2. Agent Node Graph: A visual list or pipeline showing which agent is currently active (Sentinel -> Profile -> Scout -> Arbiter -> Execution).
  3. Live Telemetry Terminal: A mock "terminal" window that connects to the FastAPI `GET /stream/{thread_id}` endpoint via the browser's native `EventSource` API. It must auto-scroll and append JSON logs in real-time as the LangGraph state mutates.

## STEP 7: FastAPI CORS & SSE Adjustments

In `/backend/main.py`, you MUST include `CORSMiddleware` allowing origins for standard Vite local dev ports (http://localhost:5000). Ensure the `GET /stream/{thread_id}` endpoint formats its output strictly adhering to the Server-Sent Events (SSE) text/event-stream specification so the Vue frontend can consume it without parsing errors.

Ensure all code is clean, fully typed, heavily commented, and explicitly highlights where Qoder/Qwen and Atlas integrations occur. Output the complete code blocks for all files.
