---
kind: external_dependency
name: Hermes 3 via Ollama (local text extraction)
slug: hermes-ollama
category: external_dependency
category_hints:
    - vendor_identity
    - client_constraint
scope:
    - '**'
source_files:
    - backend/agents/sentinel.py
---

### Role
Local LLM served by Ollama used by the Sentinel agent to extract structured disruption signals from unstructured NOTAM/SMS text via function calling.

### Integration shape
- Called from `agents/sentinel.py`; if the local model is unavailable, Sentinel falls back to a regex heuristic parser.
- Runs entirely on the host machine — no network required.

### Stable constraints
- Requires Ollama with the Hermes 3 model loaded locally.
- Graceful degradation means disruption ingestion still works without the model.