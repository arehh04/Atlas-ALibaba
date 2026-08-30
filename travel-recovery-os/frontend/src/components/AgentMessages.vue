<template>
  <div class="ops-card p-3 sm:p-4 flex flex-col h-full font-sans text-xs">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-warm-200 pb-3 mb-3 shrink-0">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-lg bg-brand-lavender border border-brand-purple/20 flex items-center justify-center shadow-xs">
          <svg class="w-4 h-4 text-brand-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"/>
          </svg>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="font-display font-semibold text-xs text-warm-900">Agent Swarm Group Chat</h3>
            <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Live Bus
            </span>
          </div>
          <p class="text-[10px] text-warm-500 font-mono">Autonomous inter-agent dialogue (A2A)</p>
        </div>
      </div>
      <span class="text-[10px] font-mono px-2.5 py-1 rounded-full bg-warm-100 text-warm-600 border border-warm-200 font-semibold shadow-2xs">
        {{ messages.length }} {{ messages.length === 1 ? 'msg' : 'msgs' }}
      </span>
    </div>

    <!-- Messages Container -->
    <div ref="messageList" class="flex-1 overflow-y-auto space-y-3 pr-1">
      <!-- Empty State -->
      <div v-if="messages.length === 0" class="text-warm-400 py-8 text-center text-xs flex flex-col items-center justify-center gap-2.5 h-full">
        <div class="w-10 h-10 rounded-xl bg-warm-100 border border-warm-200 flex items-center justify-center text-warm-400 shadow-2xs">
          <svg class="w-5 h-5 text-warm-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-.66 0-1.306-.025-1.95-.072C12.66 17.004 12 16.096 12 14.894V10.608c0-.97.616-1.813 1.5-2.097a44.18 44.18 0 016.75 0zM3.75 14.894V10.608c0-1.136.847-2.1 1.98-2.193.34-.027.68-.052 1.02-.072v-3.091l3 3c.66 0 1.306.025 1.95.072C12.84 8.396 13.5 9.304 13.5 10.506v4.286c0 .97-.616 1.813-1.5 2.097a44.18 44.18 0 01-6.75 0c-.884-.284-1.5-1.128-1.5-2.097z"/>
          </svg>
        </div>
        <div class="text-center">
          <p class="font-medium text-warm-600 text-xs">Waiting for Swarm Execution</p>
          <p class="text-[11px] text-warm-400 mt-0.5">Trigger a disruption to watch agents converse and negotiate in real time.</p>
        </div>
      </div>

      <!-- Chat Bubble Message Item -->
      <div 
        v-for="(msg, idx) in messages" 
        :key="idx" 
        class="flex items-start gap-2.5 p-3 rounded-xl border transition-all duration-200 animate-fade-in shadow-2xs hover:shadow-xs" 
        :class="getMessageCardStyle(msg)"
      >
        <!-- Agent Avatar -->
        <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-display font-bold text-[11px] shadow-2xs border" :class="getAgentBadge(msg.from_agent)">
          {{ getAgentIcon(msg.from_agent) }}
        </div>

        <div class="flex-1 min-w-0">
          <!-- Sender & Routing Header -->
          <div class="flex items-center gap-1.5 mb-1.5 flex-wrap">
            <span class="font-semibold text-xs" :class="getAgentColor(msg.from_agent)">
              {{ getAgentDisplayName(msg.from_agent) }}
            </span>
            
            <span class="text-warm-400 text-[10px]">→</span>
            
            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-warm-100 text-warm-600 border border-warm-200">
              {{ getRecipientDisplayName(msg.to_agent) }}
            </span>

            <span class="text-[9px] font-mono px-1.5 py-0.5 rounded font-semibold uppercase tracking-wider ml-1" :class="getTypeBadge(msg.message_type)">
              {{ msg.message_type || 'MSG' }}
            </span>

            <span class="ml-auto text-warm-400 font-mono text-[10px] shrink-0">
              {{ formatTime(msg.timestamp) }}
            </span>
          </div>

          <!-- Conversational Speech Bubble Text -->
          <div class="text-warm-900 text-xs leading-relaxed font-normal bg-white/90 p-2.5 rounded-lg border border-warm-200 shadow-2xs mb-2">
            {{ getMessageText(msg) }}
          </div>

          <!-- Collapsible Payload Inspector -->
          <div v-if="hasPayload(msg)" class="mt-1">
            <button 
              @click="togglePayload(idx)" 
              class="inline-flex items-center gap-1 text-[10px] font-mono text-warm-500 hover:text-brand-purple transition-colors cursor-pointer"
            >
              <svg class="w-3 h-3 transition-transform" :class="{ 'rotate-90': expandedPayloads[idx] }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5"/>
              </svg>
              <span>{{ expandedPayloads[idx] ? 'Hide Structured Payload' : 'View Structured Payload JSON' }}</span>
            </button>

            <div v-if="expandedPayloads[idx]" class="mt-1.5 animate-fade-in">
              <pre class="text-[10px] font-mono text-brand-blue bg-warm-50 p-2.5 rounded-lg border border-warm-200 overflow-x-auto whitespace-pre-wrap leading-tight">{{ JSON.stringify(msg.payload, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, reactive } from 'vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  }
})

const messageList = ref(null)
const expandedPayloads = reactive({})

function togglePayload(idx) {
  expandedPayloads[idx] = !expandedPayloads[idx]
}

function getAgentDisplayName(agent) {
  const map = {
    sentinel: 'Sentinel Interceptor',
    profile: 'Profile Analyzer',
    scout: 'Atlas Scout',
    arbiter: 'Arbiter Consensus',
    baggage: 'Baggage Operations',
    compensation: 'Passenger Rights Desk',
    multileg: 'Multi-Leg Coordinator',
    execution: 'Atlas Ticketing Engine'
  }
  return map[agent] || agent || 'Agent'
}

function getRecipientDisplayName(to) {
  if (!to || to === '*') return 'All Agents (Broadcast)'
  const map = {
    arbiter: 'Arbiter Engine',
    sentinel: 'Sentinel Agent',
    profile: 'Profile Agent',
    scout: 'Atlas Scout',
    execution: 'Ticketing Engine'
  }
  return map[to] || to
}

function getAgentIcon(agent) {
  const icons = {
    sentinel: '🚨',
    profile: '👤',
    scout: '🔍',
    arbiter: '🎯',
    baggage: '🧳',
    compensation: '⚖️',
    multileg: '✈️',
    execution: '🎟️'
  }
  return icons[agent] || '🤖'
}

function getAgentBadge(agent) {
  const map = {
    sentinel: 'bg-blue-50 text-blue-700 border-blue-200',
    profile: 'bg-purple-50 text-purple-700 border-purple-200',
    scout: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    arbiter: 'bg-amber-50 text-amber-700 border-amber-200',
    baggage: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    compensation: 'bg-rose-50 text-rose-700 border-rose-200',
    multileg: 'bg-teal-50 text-teal-700 border-teal-200',
    execution: 'bg-emerald-50 text-emerald-700 border-emerald-200'
  }
  return map[agent] || 'bg-warm-100 text-warm-700 border-warm-200'
}

function getAgentColor(agent) {
  const map = {
    sentinel: 'text-blue-700 font-semibold',
    profile: 'text-purple-700 font-semibold',
    scout: 'text-cyan-700 font-semibold',
    arbiter: 'text-amber-700 font-semibold',
    baggage: 'text-indigo-700 font-semibold',
    compensation: 'text-rose-700 font-semibold',
    multileg: 'text-teal-700 font-semibold',
    execution: 'text-emerald-700 font-semibold'
  }
  return map[agent] || 'text-warm-800'
}

function getTypeBadge(type) {
  const map = {
    NOTIFICATION: 'bg-blue-50 text-blue-700 border border-blue-200',
    REQUEST: 'bg-amber-50 text-amber-700 border border-amber-200',
    RESPONSE: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    WARNING: 'bg-rose-50 text-rose-700 border border-rose-200'
  }
  return map[type] || 'bg-warm-100 text-warm-600 border border-warm-200'
}

function getMessageCardStyle(msg) {
  if (msg.message_type === 'WARNING') return 'bg-rose-50/40 border-rose-200'
  if (msg.from_agent === 'arbiter') return 'bg-amber-50/30 border-amber-200'
  if (msg.from_agent === 'execution') return 'bg-emerald-50/30 border-emerald-200'
  return 'bg-white border-warm-200'
}

function getMessageText(msg) {
  if (msg.text) return msg.text
  if (msg.message) return msg.message
  if (msg.content) return msg.content
  if (msg.summary) return msg.summary
  if (msg.payload && typeof msg.payload === 'object') {
    if (msg.payload.message) return msg.payload.message
    if (msg.payload.reason) return `Disruption reason: ${msg.payload.reason}`
  }
  return 'Inter-agent state synchronization payload exchanged.'
}

function hasPayload(msg) {
  return msg.payload && typeof msg.payload === 'object' && Object.keys(msg.payload).length > 0
}

function formatTime(ts) {
  if (!ts) return ''
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ts
  }
}

watch(() => props.messages.length, () => {
  nextTick(() => {
    if (messageList.value) {
      messageList.value.scrollTop = messageList.value.scrollHeight
    }
  })
})
</script>
