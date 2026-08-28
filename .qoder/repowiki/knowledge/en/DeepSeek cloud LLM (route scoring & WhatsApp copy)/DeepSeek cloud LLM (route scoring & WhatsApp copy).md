---
kind: external_dependency
name: DeepSeek cloud LLM (route scoring & WhatsApp copy)
slug: deepseek
category: external_dependency
category_hints:
    - vendor_identity
    - auth_protocol
scope:
    - '**'
source_files:
    - backend/agents/arbiter.py
    - backend/config.py
---

### Role
Cloud LLM provider used by the Arbiter agent for Chain-of-Thought route scoring and generating personalized WhatsApp notification copy. Also used for passenger chat responses.

### Integration shape
- Configured via environment variables consumed by `config.py` (Pydantic BaseSettings); credentials injected as API keys.
- Falls back to a deterministic scoring algorithm when the DeepSeek endpoint is unavailable.

### Stable constraints
- Optional dependency — the system degrades to rule-based scoring without it.
- Credentials are supplied through env-driven settings rather than hardcoded values.