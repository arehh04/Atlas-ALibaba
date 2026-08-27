# 🎬 SynapseAir Hackathon Demo & Pitch Guide
### Alibaba Cloud x Atlas Agentic AI Hackathon

Use this 3-minute script to demonstrate the full multi-agent swarm architecture to the judges.

---

## ⏱️ The 3-Minute Demo Flow

### 📍 Act 1: The Disruption (0:00 - 0:45)
1. Open the **Command Center** at `http://localhost:5173`.
2. Click the **`Hermes Raw`** tab under **1. Disruption Ingest**.
3. Paste an unstructured airline cancellation alert:
   > *"URGENT OPS ALERT: Flight CZ-3042 from KUL to HGH canceled due to super typhoon warning. Passenger Dr. Vance (PNR-VIP-8842) requires immediate VIP re-accommodation."*
4. Click **`⚡ Trigger Disruption Swarm`**.
5. **Key Talking Point**: *"Our Sentinel Agent uses Hermes to parse unstructured aviation NOTAMs in real-time without rigid schemas."*

---

### 📍 Act 2: Autonomous Multi-Agent Swarm (0:45 - 1:45)
1. Watch the **Interactive Pipeline** animate:
   - **Sentinel** derives the route (`KUL ➔ HGH`).
   - **Profile Agent** and **Scout Agent** execute **in parallel**:
     - Profile resolves VIP Platinum rules (*direct flights only, business cabin*).
     - Scout invokes the **official Atlas Flight Booking CLI** (`atlas-flight`) to query real-time live GDS inventory across airlines.
   - **Arbiter Agent** runs **DeepSeek LLM (`deepseek-v4-flash`)** Chain-of-Thought reasoning.
2. Show the **DeepSeek Reasoning Box** and candidate score breakdown in the UI.
3. **Key Talking Point**: *"DeepSeek performs multi-criteria optimization on Atlas GDS offers, cross-referencing customer loyalty SLAs to draft the ideal recovery plan."*

---

### 📍 Act 3: Human-in-the-Loop 1-Click Consensus (1:45 - 2:30)
1. For standard passengers with route changes, the LangGraph checkpointer **pauses** at the `hitl_breakpoint`.
2. **n8n WhatsApp Gateway** dispatches the personalized rebooking offer to the passenger's phone.
3. In the UI, click **`✓ 1-Click WhatsApp Approve`**.
4. The backend resumes execution from the checkpointer snapshot (`POST /webhook/consensus`), triggers the Atlas ticketing engine, and confirms e-ticket `784-XXXXXXXXXX`.
5. **Key Talking Point**: *"With LangGraph state checkpointers and n8n webhooks, passengers confirm rebookings in 1 click on WhatsApp with zero customer service queue time."*

---

## 📊 Summary of Tech Stack Highlights for Judges
- **Agent Orchestration**: LangGraph (`StateGraph`) with parallel fan-out, conditional edges, and `MemorySaver` checkpointer.
- **LLM Reasoning**: DeepSeek V4 (`deepseek-v4-flash`) for multi-criteria arbitration.
- **LLM Parsing**: Hermes (`nvidia/nemotron-3.5-lightning:free`) for unstructured NOTAM extraction.
- **Flight GDS Engine**: Official Atlas Flight Booking CLI (`atlas-flight`).
- **Communication Gateway**: n8n WhatsApp Business API Webhook.
- **Frontend Dashboard**: Vue 3 + Vite + TailwindCSS with native SSE Server-Sent Events real-time streaming.
