---
kind: external_dependency
name: n8n workflow engine (WhatsApp Business gateway)
slug: n8n
category: external_dependency
category_hints:
    - vendor_identity
    - client_constraint
scope:
    - '**'
source_files:
    - backend/services/n8n_service.py
    - n8n/synapseair_workflow.json
    - docker-compose.yml
---

### Role
Workflow automation platform used as the outbound channel for passenger communication (WhatsApp Business API). The backend dispatches webhooks to an n8n instance to send/receive passenger messages and log events.

### Integration shape
- `backend/services/n8n_service.py` posts to n8n webhooks and reads audit logs via `/api/n8n/events`.
- Frontend ships a prebuilt workflow JSON (`n8n/synapseair_workflow.json`) describing the WhatsApp flow.
- Docker Compose spins up an n8n container alongside backend/frontend.

### Stable constraints
- n8n must be reachable at the configured base URL; unreachable instances degrade gracefully but block WhatsApp delivery.
- Events are persisted in SQLite on the backend side as an audit trail.