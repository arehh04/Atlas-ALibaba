---
kind: external_dependency
name: LangGraph StateGraph + MemorySaver checkpointer
slug: langgraph
category: external_dependency
category_hints:
    - framework_behavior
    - sdk_real_api
scope:
    - '**'
source_files:
    - backend/swarm.py
    - backend/state.py
---

### Role
Multi-agent orchestration runtime for the SynapseAir disruption-recovery workflow. The backend compiles a `StateGraph` with nodes (Sentinel → Profile ∥ Scout → Arbiter → HITL breakpoint → Execution) and uses `MemorySaver` as the in-memory checkpointer.

### Integration shape
- Graph definition lives in `backend/swarm.py`; state schema in `state.py`.
- Parallel branches merge via `Annotated[List, operator.add]` on `candidate_routes` / `execution_logs`.
- Human-in-the-loop is implemented with `interrupt_before=["hitl_breakpoint"]` — the graph pauses at the HITL node until consensus arrives via `/webhook/consensus`.

### Stable gotchas