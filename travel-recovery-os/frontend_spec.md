# SYSTEM CONTEXT

Act as a Principal Frontend Architect and UI/UX Designer. We are building the real-time Command Center frontend for "SynapseAir" (travel-recovery-os) for the Alibaba Cloud x Atlas Agentic AI Hackathon.

The goal of this UI is to visually blow away hackathon judges during a 3-minute video by demonstrating real-time multi-agent orchestration, live telemetry streaming, and autonomous flight recovery.

# DESIGN SYSTEM & THEME

- Color Palette: Deep Slate/Space Navy background (#0B0F19, #0F172A), Electric/Cyan Blue (#3B82F6, #60A5FA), Neon Purple/Violet (#8B5CF6, #A855F7), and Crisp White (#FFFFFF, #F8FAFC).
- Aesthetic: Aerospace AI Command Center. Clean glassmorphism (subtle borders `border-white/10`, `backdrop-blur-xl`), glowing status badges, clean typography, and a live monospace terminal with syntax-highlighted streaming logs.
- Icons: Lucide Vue (`lucide-vue-next`).

# TECH STACK

- Vue 3 (Composition API, `<script setup>`)
- Vite
- Tailwind CSS v3+
- Lucide Vue Next
- Native Browser `EventSource` API (SSE)

# DIRECTORY STRUCTURE TO BUILD

Inside `/frontend`:
├── src/
│ ├── assets/
│ │ └── main.css # Tailwind directives and custom glow animations
│ ├── composables/
│ │ └── useSwarmStream.js # SSE connection & state management
│ ├── components/
│ │ ├── Navbar.vue # Top telemetry bar (Atlas API status, Qoder Engine, Active PNR)
│ │ ├── DisruptionControl.vue # Flight disruption scenario injector
│ │ ├── SwarmPipeline.vue # Visual 5-node agent state pipeline with live glow transitions
│ │ ├── LiveTerminal.vue # Monospace auto-scrolling SSE agent thought console
│ │ ├── RecoveryProposal.vue# Atlas rebooking decision card (scores, route, SLA savings)
│ │ └── MobileHitlMock.vue # Phone simulation showing WhatsApp HITL sync in real-time
│ ├── App.vue # Main responsive grid layout
│ └── main.js
├── tailwind.config.js
├── package.json
└── vite.config.js

# DETAILED COMPONENT SPECIFICATIONS

## 1. Composable (`src/composables/useSwarmStream.js`)

- Manages connection to `http://localhost:8000/stream/${threadId}` via `EventSource`.
- Maintains reactive states:
  - `activeAgent`: Current agent executing ('sentinel', 'profile', 'scout', 'arbiter', 'hitl', 'executor', 'completed').
  - `logs`: Array of raw terminal logs with timestamp.
  - `disruptionData`: PNR, flight number, delay duration, cause.
  - `proposedSolution`: Flight number, route, departure, confidence score, airline cost vs voucher savings.
  - `hitlStatus`: 'WAITING_FOR_PASSENGER', 'APPROVED', 'BYPASSED'.
- Exposes: `startDisruption(scenarioPayload)`, `resolveHitl(decision)`, `disconnect()`.

## 2. Header / Navbar (`Navbar.vue`)

- Title: **SynapseAir OS** with a glowing purple/blue badge: `AGENTIC SWARM ACTIVE`.
- Right stats:
  - Engine: `Qwen 3.8 Max (Qoder)` (Green pulsating dot).
  - GDS: `Atlas Sandbox Connected` (Blue pulsating dot).
  - Latency metric indicator: `~120ms`.

## 3. Disruption Injector Panel (`DisruptionControl.vue`)

- Provides quick 1-click test scenarios:
  1. `[CRITICAL] SQ108 Canceled - Changi Hub (Gold Member)`
  2. `[DELAY] MH128 +240m - Missed KUL Connection`
- "Trigger Autonomous Recovery" button featuring a gradient animation (`bg-gradient-to-r from-blue-600 to-purple-600 hover:shadow-lg hover:shadow-purple-500/25`).

## 4. Swarm Pipeline Visualizer (`SwarmPipeline.vue`)

- Displays 5 connected horizontal/vertical agent nodes:
  1. **Sentinel Agent** (Telemetry Ingestion)
  2. **Profile Agent** (SLA & Tier Evaluation)
  3. **Atlas Scout Agent** (Inventory Search)
  4. **Arbiter Agent** (Trade-off Scoring)
  5. **Execution Agent** (Ticket Re-issuance)
- Active nodes must feature an animated purple-to-blue pulse ring (`animate-pulse ring-2 ring-purple-400`).
- Completed nodes show a checkmark badge in neon cyan.

## 5. Live Agent Thought Terminal (`LiveTerminal.vue`)

- Dark glass container (`bg-slate-950/80 border border-slate-800 rounded-xl p-4 font-mono text-xs`).
- Header: `SYSTEM TELEMETRY / AGENT LOGS` with clear and auto-scroll toggle buttons.
- Syntax highlighting:
  - `[Sentinel]` -> Cyan text (#38BDF8)
  - `[Scout]` -> Purple text (#C084FC)
  - `[Arbiter]` -> Amber text (#FBBF24)
  - `[SUCCESS]` -> Neon green text (#4ADE80)
- Auto-scrolls smoothly to the bottom as new SSE packets arrive.

## 6. Recovery Proposal & HITL Card (`RecoveryProposal.vue` & `MobileHitlMock.vue`)

- Appears when the Arbiter agent produces a result.
- Displays:
  - **Proposed Route**: e.g., `SIN -> KUL via SQ112 (Dept: 14:30)`.
  - **Trade-off Score**: Circular gauge / progress bar showing `96% Optimal`.
  - **Financial Arbitrage**: "Airline Save: $280 vs. Hotel SLA Penalty".
- If `hitlStatus === 'WAITING_FOR_PASSENGER'`:
  - Show a glowing yellow warning: `PAUSED: PENDING PASSENGER CONSENT (WHATSAPP)`.
  - Beside it, render the `MobileHitlMock` showing a simulated WhatsApp chat bubble where the user replies "YES".

# EXECUTION INSTRUCTIONS

Generate the complete code for all specified Vue 3 components, the composable, Tailwind configuration, and root application layout. Ensure all code is production-ready, typed with JSDoc, and immediately runnable via `npm run dev`.
