---
kind: external_dependency
name: Vue 3 + Vite + TailwindCSS command center frontend
slug: vue3-vite
category: external_dependency
category_hints:
    - framework_behavior
scope:
    - '**'
source_files:
    - frontend/src/App.vue
    - frontend/src/composables/useSwarmStream.js
    - frontend/package.json
---

### Role
Dark-mode airline operations dashboard built with Vue 3 components, Vite 5 build tooling, and TailwindCSS 3 styling. Serves the SynapseAir Command Center UI.

### Integration shape
- Components: Navbar, SwarmPipeline, DisruptionControl, RecoveryProposal, MobileHitlMock, LiveTerminal, RouteMap, AgentMessages, HistoryDashboard, ErrorBoundary.
- Reactive state managed via composables (`useConnection.js`, `useSwarmStream.js`) connecting to backend SSE/WebSocket streams.
- Built into static assets served by nginx in Docker; dev server runs on a dynamic port (default 5173, may shift to 5174+).

### Stable gotchas
- Template syntax errors (e.g. misplaced closing parenthesis in template literals) break the Vite build.
- Dev server port is dynamic; CORS allowlist must include any localhost port the browser picks.