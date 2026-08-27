<template>
  <div class="min-h-screen bg-warm-100 text-warm-900 flex flex-col font-sans selection:bg-purple-200 selection:text-purple-900">
    
    <!-- Top Header -->
    <Navbar 
      :activePnr="disruptionData.pnr"
      :systemStatus="systemStatus"
      :latencyMs="streamLatencyMs"
    />

    <!-- Main Grid -->
    <main class="flex-1 p-4 md:p-6 max-w-[1750px] w-full mx-auto space-y-5">
      
      <!-- Top Section: Multi-Agent Pipeline Progress Tracker -->
      <ErrorBoundary fallback-title="Pipeline Display Error">
        <SwarmPipeline 
          :activeAgent="activeAgent"
          :stepTimes="stepExecutionTimes"
        />
      </ErrorBoundary>

      <!-- Middle Section: 3-Column Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        <!-- Left: Disruption Simulator (4 Cols) -->
        <div class="lg:col-span-4">
          <ErrorBoundary fallback-title="Disruption Simulator Error">
            <DisruptionControl 
              :isStreaming="isStreaming"
              @trigger="startDisruption" 
            />
          </ErrorBoundary>
        </div>

        <!-- Middle: Recovery Plan (4 Cols) -->
        <div class="lg:col-span-4">
          <ErrorBoundary fallback-title="Recovery Plan Error">
            <RecoveryProposal 
              :solution="proposedSolution"
              :hitlStatus="hitlStatus"
              :ticketReceipt="ticketReceipt"
            />
          </ErrorBoundary>
        </div>

        <!-- Right: WhatsApp Chat (3.5 Cols) -->
        <div class="lg:col-span-4 flex justify-center lg:justify-start">
          <ErrorBoundary fallback-title="Chat Interface Error">
            <MobileHitlMock 
              :hitlStatus="hitlStatus"
              :solution="proposedSolution"
              :passengerName="disruptionData.passenger_name"
              :pnr="disruptionData.pnr"
              :candidateRoutes="candidateRoutes"
              :baggageContext="baggageContext"
              :compensationResult="compensationResult"
              @resolve="resolveHitl"
            />
          </ErrorBoundary>
        </div>

      </div>

      <!-- Route Map -->
      <div class="animate-fade-in">
        <ErrorBoundary fallback-title="Route Map Error">
          <RouteMap
            :origin="disruptionData.origin"
            :destination="disruptionData.destination"
            :routes="candidateRoutes"
            :selected="proposedSolution"
          />
        </ErrorBoundary>
      </div>

      <!-- Agent Messages -->
      <div class="animate-fade-in">
        <ErrorBoundary fallback-title="Agent Messages Error">
          <AgentMessages :messages="agentMessages" />
        </ErrorBoundary>
      </div>

      <!-- Live Telemetry -->
      <div class="h-64 sm:h-72 md:h-80 animate-fade-in">
        <ErrorBoundary fallback-title="Telemetry Error">
          <LiveTerminal 
            :logs="logs" 
            @clear="clearLogs" 
          />
        </ErrorBoundary>
      </div>

      <!-- Historical Disruption Dashboard (collapsible) -->
      <details class="group ops-card transition-colors hover:border-warm-300">
        <summary class="cursor-pointer select-none px-5 py-3.5 text-sm font-display font-semibold text-warm-700 flex items-center gap-2.5 hover:text-warm-900 transition-colors">
          <svg class="w-4 h-4 transition-transform duration-200 group-open:rotate-90 text-warm-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
          </svg>
          Disruption History & Analytics
        </summary>
        <div class="px-5 pb-5 animate-slide-up">
          <ErrorBoundary fallback-title="History Dashboard Error">
            <HistoryDashboard />
          </ErrorBoundary>
        </div>
      </details>

    </main>

    <!-- Footer -->
    <footer class="border-t border-warm-200 py-4 px-4 sm:px-6 text-xs text-warm-500 font-sans">
      <div class="max-w-[1750px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
        <div class="flex items-center gap-2.5">
          <img src="./assets/synapseair-logo.webp" alt="" class="w-5 h-5 rounded-md" />
          <span class="text-warm-600 font-medium">SynapseAir</span>
          <span class="text-warm-300">|</span>
          <span class="text-warm-500">Smart Flight Recovery</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-warm-400">v2.1</span>
          <span class="text-warm-300">&middot;</span>
          <span class="text-gradient-brand font-semibold">Alibaba Cloud</span>
          <span class="text-warm-300">&times;</span>
          <span class="text-warm-500">Atlas AI</span>
        </div>
      </div>
    </footer>

  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import Navbar from './components/Navbar.vue'
import DisruptionControl from './components/DisruptionControl.vue'
import SwarmPipeline from './components/SwarmPipeline.vue'
import RecoveryProposal from './components/RecoveryProposal.vue'
import MobileHitlMock from './components/MobileHitlMock.vue'
import LiveTerminal from './components/LiveTerminal.vue'
import RouteMap from './components/RouteMap.vue'
import AgentMessages from './components/AgentMessages.vue'
import HistoryDashboard from './components/HistoryDashboard.vue'
import ErrorBoundary from './components/ErrorBoundary.vue'

import { useSwarmStream } from './composables/useSwarmStream'

const {
  activeAgent,
  isStreaming,
  hitlStatus,
  streamLatencyMs,
  systemStatus,
  disruptionData,
  proposedSolution,
  candidateRoutes,
  ticketReceipt,
  stepExecutionTimes,
  logs,
  baggageContext,
  compensationResult,
  agentMessages,
  fetchSystemStatus,
  startDisruption,
  resolveHitl,
  clearLogs
} = useSwarmStream()

onMounted(() => {
  fetchSystemStatus()
  setInterval(fetchSystemStatus, 15000)
})
</script>
