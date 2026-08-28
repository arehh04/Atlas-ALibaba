---
kind: configuration_system
name: Pydantic Settings-Based Environment Configuration with Profiled .env Files
category: configuration_system
scope:
    - '**'
source_files:
    - travel-recovery-os/backend/config.py
    - travel-recovery-os/backend/.env.example
    - travel-recovery-os/backend/.env
    - travel-recovery-os/backend/config.production.env.example
    - travel-recovery-os/docker-compose.yml
    - travel-recovery-os/backend/main.py
---

## Overview

The SynapseAir backend uses a centralized, Pydantic-based configuration system that loads settings from environment variables and profiled `.env` files. The single source of truth is `backend/config.py`, which defines a `Settings` class using `pydantic_settings.BaseSettings`. All modules import the module-level singleton `settings` to read runtime configuration.

## Mechanism

- **Profile selection**: The active environment profile is determined by the `ENVIRONMENT` OS env var (`development`, `staging`, `production`). A mapping selects the corresponding `.env` file: `.env` (dev), `.env.staging`, or `.env.production`. If `ENVIRONMENT` is set to an unknown value, it falls back to `.env`.
- **Loading order**: `BaseSettings` reads values from the selected `.env` file first, then overlays any actual OS environment variables (standard `pydantic_settings` precedence).
- **Validation & defaults**: Every setting has a typed default in the model. Optional secrets use `Optional[str] = ""`. A `field_validator` on `JWT_SECRET_KEY` falls back to `SYNAPSE_API_SECRET` when not explicitly set. A `model_validator(mode="after")` runs only when `ENVIRONMENT == "production"` and emits a `RuntimeWarning` listing any missing/placeholder critical keys (`SYNAPSE_API_SECRET`, `DEEPSEEK_API_KEY`, `JWT_SECRET_KEY`, `REDIS_URL`).
- **Case-insensitive loading**: `case_sensitive=False` allows env vars to be referenced uniformly.
- **Extra fields ignored**: `extra="ignore"` prevents failures if extra env vars are present.

## Configuration Sections

| Section | Key Examples | Purpose |
|---|---|---|
| Application | `APP_NAME`, `DEBUG`, `ENVIRONMENT`, `SYNAPSE_API_SECRET`, `REQUIRE_AUTH` | App identity, feature flags, auth toggle |
| DeepSeek LLM | `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL` | Primary reasoning / arbiter agent |
| Hermes LLM | `HERMES_API_BASE`, `HERMES_API_KEY`, `HERMES_MODEL` | Function-calling / parser agent (Ollama, OpenRouter, etc.) |
| n8n Gateway | `N8N_API_URL`, `N8N_API_KEY`, `N8N_WEBHOOK_URL`, `N8N_CONSENSUS_CALLBACK_URL` | WhatsApp HITL webhook relay |
| Atlas GDS | `ATLAS_ENV`, `ATLAS_CLIENT_ID`, `ATLAS_CLIENT_SECRET`, `ATLAS_BASE_URL`, `ATLAS_API_KEY` | Flight search / booking API |
| Redis | `REDIS_URL` | Broker / cache |
| JWT Auth | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` |
| Observability | `OTEL_ENDPOINT`, `LOG_LEVEL`, `LOG_JSON` |

## Consumption Pattern

Every module imports via `from config import settings` and accesses attributes directly (e.g., `settings.DEEPSEEK_API_KEY`, `settings.N8N_WEBHOOK_URL`). There is no per-module config; all access goes through the singleton. Notable usages:
- `api/routers/system.py` exposes configured provider status via `/health`.
- `api/dependencies.py` gates authentication based on `settings.REQUIRE_AUTH` and `settings.ENVIRONMENT`.
- `services/llm_service.py` constructs clients using `settings.DEEPSEEK_*` and `settings.HERMES_*`.
- `main.py` reads `LOG_LEVEL`, `LOG_JSON`, `FRONTEND_URL`, and `ENVIRONMENT` directly from `os.getenv` for startup behavior (CORS, test router mounting).

## Environment Profiles & Templates

- `backend/.env.example` — template for local development with placeholder values.
- `backend/.env` — checked-in local dev values (not for production).
- `backend/config.production.env.example` — production template instructing users to copy to `.env.production` and fill every field before deploy.
- `docker-compose.yml` sets `ENVIRONMENT=production` and passes `REDIS_URL` as an explicit environment variable, overriding the `.env` file for that service.

## Frontend Configuration

The frontend (Vue 3) has no application-level config loader in this repo snapshot. CORS origins are hardcoded in `backend/main.py` plus an optional `FRONTEND_URL` env var override. The frontend build config (`vite.config.js`, `tailwind.config.js`) contains build-time constants but no runtime configuration mechanism.

## Conventions Observed

1. **Single settings object**: All configuration flows through one `Settings` instance; modules never call `os.getenv` directly for business config.
2. **Typed defaults everywhere**: Even secrets have safe defaults so the app starts without crashing; validation happens at startup.
3. **Production guardrails**: Missing critical keys in production emit warnings rather than hard errors, allowing graceful degradation while alerting operators.
4. **Profiled .env files**: Separate `.env` files per environment, selected by `ENVIRONMENT`.
5. **Secrets via env vars**: No config files contain real secrets; templates use placeholders like `<your-api-key>`.
6. **Feature toggles via settings**: `REQUIRE_AUTH`, `DEBUG`, `LOG_JSON`, `ATLAS_ENV` act as runtime switches.