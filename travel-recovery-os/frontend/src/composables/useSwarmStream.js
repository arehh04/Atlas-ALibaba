/**
 * useSwarmStream.js — Reactive state management for the SynapseAir swarm.
 *
 * Orchestrates: system status polling, disruption triggering, HITL consensus,
 * telemetry logging, and real-time event routing from the connection layer.
 *
 * Transport is delegated to useConnection (WebSocket → SSE fallback).
 */

import { ref, reactive, readonly, onUnmounted } from 'vue'
import { apiClient } from '../services/api'
import { useConnection } from './useConnection'

// ── Shared State (module-level singleton) ─────────────────────────────────

const activeAgent = ref('idle')
const isStreaming = ref(false)
const threadId = ref('')
const hitlStatus = ref('IDLE')
const streamLatencyMs = ref(0)

const systemStatus = reactive({
  deepseek_model: 'deepseek-v4-flash',
  hermes_model: 'nvidia/nemotron-3.5-lightning:free',
  atlas_gds_provider: 'Atlas Flight CLI Live',
  n8n_status: 'Connected',
  backend_status: 'Healthy'
})

const disruptionData = reactive({
  pnr: 'SQ108-SIN',
  flight_number: 'SQ-108',
  airline: 'Singapore Airlines',
  origin: 'SIN',
  destination: 'KUL',
  travel_date: new Date().toISOString().split('T')[0],
  delay_minutes: 240,
  reason: 'Aircraft Hydraulic Sensor Fault (AOG)',
  loyalty_tier: 'GOLD',
  passenger_name: 'Dr. Alexander Vance',
  phone_number: '+65 9123 4567'
})

const proposedSolution = ref(null)
const candidateRoutes = ref([])
const ticketReceipt = ref(null)
const logs = ref([])
const stepExecutionTimes = reactive({
  sentinel: null, profile: null, scout: null, baggage: null,
  arbiter: null, compensation: null, multileg: null, executor: null
})

const baggageContext = ref(null)
const compensationResult = ref(null)
const agentMessages = ref([])

let stepStartTimestamp = 0

// ── Transport layer ───────────────────────────────────────────────────────
const { connectionMode, connect: connectTransport, send: sendWs, closeConnections } = useConnection()

// ── Exported Composable ───────────────────────────────────────────────────

export function useSwarmStream() {

  // ── System Status ──────────────────────────────────────────────────────

  async function fetchSystemStatus() {
    const t0 = performance.now()
    try {
      const data = await apiClient.getSystemStatus()
      streamLatencyMs.value = Math.round(performance.now() - t0)
      systemStatus.deepseek_model = data.deepseek?.model || 'deepseek-v4-flash'
      systemStatus.hermes_model = data.hermes?.model?.split('/')[1] || data.hermes?.model || 'hermes-3'
      systemStatus.atlas_gds_provider = data.atlas_gds?.provider || 'Atlas CLI Live'
      systemStatus.n8n_status = data.n8n?.status || 'Connected'
      systemStatus.backend_status = data.status || 'Healthy'
    } catch {
      streamLatencyMs.value = Math.round(performance.now() - t0)
    }
  }

  // ── Logging ────────────────────────────────────────────────────────────

  function appendLog(event) {
    logs.value.push({
      id: Date.now() + Math.random(),
      timestamp: event.timestamp || new Date().toISOString(),
      node: event.node || event.type || 'SYSTEM',
      level: event.log?.level || event.level || 'INFO',
      message: event.message || event.log?.message || JSON.stringify(event),
      data: event.data || event.log?.data || null
    })
  }

  // ── Event Handler ──────────────────────────────────────────────────────

  function handleEvent(event) {
    appendLog(event)

    if (event.type === 'AGENT_STEP') {
      _handleAgentStep(event)
    } else if (event.type === 'HITL_REQUIRED') {
      _handleHitlRequired(event)
    } else if (event.type === 'AGENT_MESSAGE') {
      agentMessages.value.push(event.message || event)
    } else if (event.type === 'WORKFLOW_NODE_ERROR') {
      console.warn('Node error:', event.node, event.error)
    } else if (event.type === 'WORKFLOW_COMPLETE') {
      activeAgent.value = 'completed'
      isStreaming.value = false
      if (event.ticket) ticketReceipt.value = event.ticket
    }
  }

  function _handleAgentStep(event) {
    const node = event.node
    const update = event.state_update || {}
    const logData = event.log?.data || {}
    const now = Date.now()

    if (node === 'sentinel') {
      stepExecutionTimes.sentinel = Math.max(120, now - stepStartTimestamp)
      activeAgent.value = 'sentinel'
      stepStartTimestamp = now
      setTimeout(() => { if (activeAgent.value === 'sentinel') activeAgent.value = 'profile' }, 500)
    } else if (node === 'profile') {
      stepExecutionTimes.profile = Math.max(95, now - stepStartTimestamp)
      activeAgent.value = 'profile'
    } else if (node === 'scout') {
      stepExecutionTimes.scout = Math.max(340, now - stepStartTimestamp)
      activeAgent.value = 'scout'
      if (update.candidate_routes) candidateRoutes.value = update.candidate_routes
    } else if (node === 'baggage') {
      stepExecutionTimes.baggage = Math.max(80, now - stepStartTimestamp)
      activeAgent.value = 'baggage'
      if (update.baggage_context) baggageContext.value = update.baggage_context
    } else if (node === 'arbiter') {
      stepExecutionTimes.arbiter = Math.max(680, now - stepStartTimestamp)
      activeAgent.value = 'arbiter'
      if (update.candidate_routes) candidateRoutes.value = update.candidate_routes
      if (update.selected_route) {
        const sel = update.selected_route
        const fin = sel.financial_savings || logData.financial_arbitrage || {
          airline_savings_usd: 280, hotel_penalty_avoided_usd: 320, sla_liability_usd: 150
        }
        proposedSolution.value = {
          flight_number: sel.flight_number,
          airline: sel.airline || 'Partner Airline',
          origin: sel.origin || disruptionData.origin,
          destination: sel.destination || disruptionData.destination,
          departure_time: sel.departure_time || '14:30',
          arrival_time: sel.arrival_time || '15:45',
          cabin_class: sel.cabin_class || 'Business',
          confidence_score: sel.score || 0.90,
          score_percentage: Math.round((sel.score || 0.90) * 100),
          base_fare_usd: sel.base_fare_usd || 180.0,
          financial_savings: fin,
          rationale: sel.scoring_rationale || logData.deepseek_reasoning_trace || 'Optimal route matching loyalty SLA and travel schedule.',
          whatsapp_copy: logData.whatsapp_copy || `Hi ${disruptionData.passenger_name}, your flight was disrupted. We reserved seat on ${sel.flight_number} departing at ${sel.departure_time}.`
        }
      }
      if (update.hitl_status === 'BYPASSED') hitlStatus.value = 'BYPASSED'
    } else if (node === 'compensation') {
      stepExecutionTimes.compensation = Math.max(60, now - stepStartTimestamp)
      activeAgent.value = 'compensation'
      if (update.compensation_result) compensationResult.value = update.compensation_result
    } else if (node === 'multileg') {
      stepExecutionTimes.multileg = Math.max(100, now - stepStartTimestamp)
      activeAgent.value = 'multileg'
    } else if (node === 'execution_node') {
      stepExecutionTimes.executor = Math.max(210, now - stepStartTimestamp)
      activeAgent.value = 'executor'
      if (update.ticket_confirmation) ticketReceipt.value = update.ticket_confirmation
    }
  }

  function _handleHitlRequired(event) {
    activeAgent.value = 'hitl'
    hitlStatus.value = 'WAITING_FOR_PASSENGER'
    if (event.selected_route && !proposedSolution.value) {
      const sel = event.selected_route
      proposedSolution.value = {
        flight_number: sel.flight_number,
        airline: sel.airline,
        origin: disruptionData.origin,
        destination: disruptionData.destination,
        departure_time: sel.departure_time,
        cabin_class: sel.cabin_class,
        score_percentage: Math.round((sel.score || 0.85) * 100),
        financial_savings: sel.financial_savings || { airline_savings_usd: 220, hotel_penalty_avoided_usd: 280 },
        rationale: sel.scoring_rationale || 'Alternative candidate requiring passenger WhatsApp consent.',
        whatsapp_copy: `Hi ${disruptionData.passenger_name}, seat reserved on ${sel.flight_number}. Please confirm below.`
      }
    }
  }

  // ── Actions ────────────────────────────────────────────────────────────

  async function startDisruption(payload) {
    isStreaming.value = true
    activeAgent.value = 'sentinel'
    hitlStatus.value = 'IDLE'
    proposedSolution.value = null
    ticketReceipt.value = null
    candidateRoutes.value = []
    baggageContext.value = null
    compensationResult.value = null
    agentMessages.value = []
    Object.assign(disruptionData, payload)

    const generatedId = payload.thread_id || `synapse-${Date.now().toString().slice(-6)}`
    threadId.value = generatedId
    stepStartTimestamp = Date.now()
    Object.keys(stepExecutionTimes).forEach(k => stepExecutionTimes[k] = null)

    connectTransport(generatedId, handleEvent)

    try {
      const result = await apiClient.triggerDisruption(payload, generatedId)
      console.log('Disruption swarm started:', result)
    } catch (err) {
      console.error('Failed to trigger recovery swarm:', err)
      appendLog({ level: 'ERROR', node: 'sentinel', message: `Disruption trigger failed: ${err.message}` })
      isStreaming.value = false
    }
  }

  async function resolveHitl(decision = 'APPROVE') {
    if (!threadId.value) return
    hitlStatus.value = decision === 'APPROVE' ? 'APPROVED' : 'REJECTED'
    activeAgent.value = decision === 'APPROVE' ? 'executor' : 'completed'

    // Send via WebSocket (if connected)
    sendWs({ type: 'HITL_DECISION', action: decision, thread_id: threadId.value })

    // REST fallback for durability
    try {
      const data = await apiClient.resolveConsensus(threadId.value, decision)
      console.log('Consensus resolved:', data)
    } catch (err) {
      console.error('Failed to post consensus:', err)
    }
  }

  function disconnect() {
    closeConnections()
    isStreaming.value = false
  }

  function clearLogs() {
    logs.value = []
  }

  onUnmounted(closeConnections)

  return {
    activeAgent, isStreaming, threadId, hitlStatus,
    streamLatencyMs: readonly(streamLatencyMs),
    systemStatus: readonly(systemStatus),
    disruptionData, proposedSolution, candidateRoutes, ticketReceipt,
    stepExecutionTimes: readonly(stepExecutionTimes),
    logs: readonly(logs),
    connectionMode,
    baggageContext, compensationResult, agentMessages,
    fetchSystemStatus, startDisruption, resolveHitl, disconnect, clearLogs
  }
}
