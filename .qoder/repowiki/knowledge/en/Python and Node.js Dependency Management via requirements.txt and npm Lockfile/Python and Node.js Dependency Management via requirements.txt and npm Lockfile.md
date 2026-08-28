---
kind: dependency_management
name: Python and Node.js Dependency Management via requirements.txt and npm Lockfile
category: dependency_management
scope:
    - '**'
source_files:
    - travel-recovery-os/backend/requirements.txt
    - travel-recovery-os/frontend/package.json
    - travel-recovery-os/frontend/package-lock.json
    - travel-recovery-os/backend/Dockerfile
    - travel-recovery-os/frontend/Dockerfile
    - travel-recovery-os/docker-compose.yml
    - travel-recovery-os/.github/workflows/ci.yml
---

## What system/approach is used

The repository manages third-party dependencies using two separate, language-native package managers:

- **Python (backend)**: `pip` with a flat `requirements.txt` declaring minimum versions (`>=`) for each dependency. No virtual environment file or lockfile is committed; the Docker build installs directly from PyPI.
- **Node.js (frontend)**: `npm` with `package.json` plus a committed `package-lock.json`. The frontend Dockerfile uses `npm ci` to enforce an exact, reproducible install from the lockfile.

There is no vendoring of Python packages (no `vendor/` directory) and no private registry configuration — both ecosystems resolve against public registries (PyPI, npm registry). External services (Redis, n8n) are pulled as Docker images in `docker-compose.yml` rather than managed through application-level dependency files.

## Key files and packages

- `travel-recovery-os/backend/requirements.txt` — declares all Python runtime and tooling dependencies (FastAPI, uvicorn, langgraph, pydantic, httpx, redis, aiosqlite, openai, websockets, python-jose, structlog, OpenTelemetry packages).
- `travel-recovery-os/frontend/package.json` — lists Vue 3 runtime deps and dev/build toolchain (Vite, Tailwind, PostCSS, sharp).
- `travel-recovery-os/frontend/package-lock.json` — committed lockfile pinning exact transitive resolutions for deterministic builds.
- `travel-recovery-os/backend/Dockerfile` — installs Python deps via `pip install -r requirements.txt` during image build.
- `travel-recovery-os/frontend/Dockerfile` — multi-stage build that runs `npm ci` on the locked dependency set, then builds static assets served by nginx.
- `travel-recovery-os/docker-compose.yml` — pins service images to specific tags (`redis:7-alpine`, `n8nio/n8n:latest`) and orchestrates them alongside the app containers.
- `travel-recovery-os/.github/workflows/ci.yml` — CI installs backend deps via `pip install -r requirements.txt` and frontend deps via `npm ci` with cache keyed off `frontend/package-lock.json`.

## Architecture and conventions

- **Per-subproject manifests**: Each language subdirectory owns its own dependency declaration; there is no monorepo-style root manifest.
- **Minimum-version policy for Python**: All entries in `requirements.txt` use `>=X.Y.Z` (e.g. `fastapi>=0.110.0`, `langgraph>=0.0.25`). This allows pip to resolve the latest compatible version at install time rather than locking to a fixed version.
- **Lockfile-only determinism for Node**: The frontend relies on `package-lock.json` for reproducibility; the CI caches the npm install step using this file as the cache key.
- **Docker as the deployment boundary**: Both backends and frontends are containerized. The backend Dockerfile copies only `requirements.txt` before installing deps to maximize layer caching; the frontend Dockerfile copies `package.json` and `package-lock.json` first, then runs `npm ci` before copying source code.
- **External services as compose dependencies**: Redis and n8n are not installed into the app images but run as sibling services declared in `docker-compose.yml`, referenced via environment variables (`REDIS_URL=redis://redis:6379/0`).
- **CI mirrors production installs**: The GitHub Actions workflow installs the same dependency sets as the Dockerfiles — `pip install -r requirements.txt` for the backend and `npm ci` for the frontend — ensuring parity between local, CI, and container builds.

## Conventions and constraints

- **No Python lockfile**: There is no `Pipfile`, `pyproject.toml` resolver lock, or `requirements.lock`; Python dependency resolution happens at build time against PyPI with `>=` constraints. This means different environments may resolve to different patch/minor versions unless pinned externally.
- **Frontend lockfile is committed**: `frontend/package-lock.json` is tracked in version control and is required for `npm ci` to succeed in CI and Docker builds.
- **Tooling deps co-located with runtime deps**: In `requirements.txt`, test/lint/type-check tools (`pytest`, `pytest-asyncio`, `ruff`, `mypy`) are installed alongside runtime dependencies in CI, even though they are not listed in the base `requirements.txt` — they are added inline in the CI job steps.
- **Service images are pinned where feasible**: Redis is pinned to `redis:7-alpine`; n8n uses `n8nio/n8n:latest` (unpinned major tag), which is a deliberate choice noted by the loose tag.
- **No private registry or vendoring**: All dependencies resolve from public registries; there is no `GOPRIVATE`, `.npmrc` registry override, or vendored Python packages.