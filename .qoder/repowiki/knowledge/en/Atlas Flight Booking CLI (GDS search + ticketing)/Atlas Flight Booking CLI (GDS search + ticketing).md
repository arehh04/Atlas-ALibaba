---
kind: external_dependency
name: Atlas Flight Booking CLI (GDS search + ticketing)
slug: atlas-flight-booking-cli
category: external_dependency
category_hints:
    - client_constraint
    - migration_status
scope:
    - '**'
source_files:
    - backend/tools/atlas_client.py
    - backend/agents/scout.py
---

### Role
External GDS interface used by the Scout agent to query live flight inventory and issue tickets. Invoked as a CLI process from Python; if the CLI is not installed the code falls back to a high-fidelity sandbox returning three realistic mock flights (China Southern, Air China, Singapore Airlines).

### Integration shape
- `backend/tools/atlas_client.py` wraps the CLI invocation and exposes search/ticket methods consumed by `agents/scout.py`.
- All Atlas calls are wrapped with graceful degradation — the system remains fully functional without internet or the CLI installed.

### Stable constraints
- Requires the Atlas CLI to be installed on the host; otherwise the sandbox mode activates automatically.
- Ticket issuance goes through the same CLI; there is no direct HTTP client path.