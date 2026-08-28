---
kind: build_system
name: Dockerized Multi-Service Build & CI/CD Pipeline for SynapseAir
category: build_system
scope:
    - '**'
source_files:
    - travel-recovery-os/Dockerfile
    - travel-recovery-os/backend/Dockerfile
    - travel-recovery-os/frontend/Dockerfile
    - travel-recovery-os/docker-compose.yml
    - travel-recovery-os/.github/workflows/ci.yml
    - travel-recovery-os/.github/workflows/deploy.yml
    - travel-recovery-os/frontend/package.json
    - travel-recovery-os/backend/requirements.txt
---

## Build System Overview

SynapseAir uses a Docker-centric build system with GitHub Actions for CI/CD, orchestrating three services: a Python/FastAPI backend, a Vue 3 frontend, and an n8n workflow engine, all composed via `docker-compose.yml`.

## Key Files and Packages

- **Root Dockerfile** (`travel-recovery-os/Dockerfile`): Single-image entrypoint that installs Python 3.12 dependencies from `backend/requirements.txt`, sets `PYTHONPATH=/app`, exposes ports 7860/8000/8001, and runs Uvicorn on the configurable `$PORT` (default 7860 for Hugging Face Spaces).
- **Backend Dockerfile** (`travel-recovery-os/backend/Dockerfile`): Identical pattern — `python:3.12-slim`, layer-cached pip install of `requirements.txt`, healthcheck against `/health`, same port/env conventions as root image.
- **Frontend Dockerfile** (`travel-recovery-os/frontend/Dockerfile`): Two-stage build using `node:20-alpine` to run `npm ci` + `vite build`, then serves static assets via `nginx:alpine` with a custom `nginx.conf`; exposes port 80.
- **Compose file** (`travel-recovery-os/docker-compose.yml`): Defines four services — `redis` (redis:7-alpine), `backend` (depends on redis healthy), `frontend` (depends on backend healthy), and `n8n` (n8nio/n8n:latest). Uses named volumes for Redis data, backend SQLite data (`backend-data`), and n8n state. Backend is configured with `REDIS_URL=redis://redis:6379/0` and `ENVIRONMENT=production`.
- **CI pipeline** (`travel-recovery-os/.github/workflows/ci.yml`): Three parallel jobs — `backend` (Python 3.12, ruff lint, mypy type check, pytest with `ENVIRONMENT=development`), `frontend` (Node 20, `npm ci`, lint, `vite build`), and `docker` (only on `refs/heads/main`) which logs into GHCR and pushes `ghcr.io/${{ github.repository }}/backend:{sha,latest}` and `frontend:{sha,latest}` images.
- **Deploy pipeline** (`travel-recovery-os/.github/workflows/deploy.yml`): Triggers on push to `main` or `workflow_dispatch`, SSHes into a production host via `appleboy/ssh-action` using `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_PATH` secrets, runs `git pull origin main`, `docker compose pull`, then `docker compose up -d --build`. Waits up to 30×5s for `/health` to return `healthy`, then runs smoke tests against `/api/system/status` and `/api/history`.
- **Frontend build config** (`travel-recovery-os/frontend/package.json`): Vite-based project with scripts `dev`, `build`, `preview`; uses Tailwind CSS, PostCSS, and Vue 3.

## Architecture and Conventions

- **Multi-service containerization**: Each service has its own `Dockerfile` under its directory; the root `Dockerfile` exists primarily for single-container deployment scenarios (e.g., Hugging Face Spaces) while `docker-compose.yml` is the canonical local/dev orchestration.
- **Layer caching best practice**: Both backend Dockerfiles copy `requirements.txt` first and run `pip install` before copying application code, maximizing Docker layer cache hits.
- **Health-driven orchestration**: Services declare `healthcheck` blocks (Redis via `redis-cli ping`, backend via `curl /health`, compose-level depends_on with `condition: service_healthy`). The deploy pipeline also polls `/health` before running smoke tests.
- **Port convention**: Backend listens on a dynamic `$PORT` env var defaulting to 7860 (Hugging Face Spaces convention); compose maps it to host 8000. Frontend always serves on 80 via nginx.
- **Environment configuration**: Secrets and runtime config are passed via `.env` files mounted through `env_file` in compose; CI injects minimal test env vars (`ENVIRONMENT`, `SYNAPSE_API_SECRET`).
- **Image tagging strategy**: CI tags every pushed image with both `latest` and the commit SHA (`ghcr.io/${{ github.repository }}/{service}:{sha}`), enabling reproducible deployments.

## Conventions and Constraints

- **Python toolchain enforced by CI**: Ruff for linting, mypy for type checking, and pytest for testing must pass; the CI job runs them sequentially in the `backend` job and fails the pipeline on any error.
- **Frontend build gate**: The `frontend` CI job requires `npm ci` + `vite build` to succeed; artifacts are not published but the build step validates the bundle.
- **Docker-only publish path**: Image publishing to GHCR is gated behind `if: github.ref == 'refs/heads/main'`, so only main branch pushes produce images.
- **Deployment requires production environment**: The deploy workflow references `environment: production`, implying GitHub Environments secrets are required; it pulls pre-built images via `docker compose pull` before rebuilding, suggesting a preferred flow of CI-built images over source builds at deploy time.
- **SQLite persistence**: The backend creates `/app/data` inside the image and mounts `backend-data` volume in compose, indicating event/state persistence across restarts.
- **No Makefile or shell build scripts**: All build logic lives in Dockerfiles, `package.json` scripts, and GitHub Actions YAML — there are no top-level Makefiles or build scripts in this repository.