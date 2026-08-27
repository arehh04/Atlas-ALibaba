<template>
  <div class="ops-card p-3 sm:p-4 flex flex-col h-full font-mono text-xs">
    <div class="flex items-center justify-between border-b border-warm-200 pb-3 mb-3">
      <div class="flex items-center gap-2.5">
        <div class="w-6 h-6 rounded-lg bg-brand-lavender border border-brand-purple/20 flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-brand-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"/>
          </svg>
        </div>
        <h3 class="font-display font-semibold text-xs text-warm-900">Agent Messages</h3>
        <span class="text-[10px] px-2 py-0.5 rounded-full bg-warm-100 text-warm-500 border border-warm-200">{{ messages.length }}</span>
      </div>
    </div>

    <div ref="messageList" class="flex-1 overflow-y-auto space-y-2 p-2">
      <div v-if="messages.length === 0" class="text-warm-400 italic py-6 text-center text-[11px] flex flex-col items-center gap-2">
        <svg class="w-6 h-6 text-warm-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"/>
        </svg>
        Agent messages appear during swarm execution
      </div>

      <div v-for="(msg, idx) in messages" :key="idx" class="flex gap-2.5 p-2.5 rounded-xl transition-all duration-200 animate-fade-in" :class="getMessageBg(msg)">
        <!-- Agent Avatar -->
        <div class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-[10px] font-bold border" :class="getAgentBadge(msg.from_agent)">
          {{ getAgentIcon(msg.from_agent) }}
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-1.5 sm:gap-2 mb-0.5 flex-wrap">
            <span class="font-bold text-[11px]" :class="getAgentColor(msg.from_agent)">{{ msg.from_agent }}</span>
            <span class="text-warm-400 text-[10px]">→</span>
            <span class="text-warm-500 text-[10px]">{{ msg.to_agent === '*' ? 'broadcast' : msg.to_agent }}</span>
            <span class="ml-auto text-warm-400 text-[10px] shrink-0">{{ formatTime(msg.timestamp) }}</span>
          </div>
          <div class="text-[10px] px-1.5 py-0.5 rounded-md inline-block mb-1" :class="getTypeBadge(msg.message_type)">{{ msg.message_type }}</div>
          <pre class="text-[10px] text-brand-blue bg-warm-100 p-2 rounded-lg border border-warm-200 overflow-x-auto whitespace-pre-wrap">{{ JSON.stringify(msg.payload, null, 1) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({ messages: { type: Array, default: () => [] } })
const messageList = ref(null)

function getAgentIcon(agent) {
  const icons = { sentinel: 'S', profile: 'P', scout: 'Sc', arbiter: 'A', baggage: 'B', compensation: 'C', multileg: 'M' }
  return icons[agent] || agent?.[0]?.toUpperCase() || '?'
}

function getAgentBadge(agent) {
  const map = {
    sentinel: 'bg-info-light text-blue-600 border-blue-200',
    profile: 'bg-brand-lavender text-brand-purple border-brand-purple/20',
    scout: 'bg-cyan-50 text-cyan-600 border-cyan-200',
    arbiter: 'bg-warning-light text-amber-600 border-amber-200',
    baggage: 'bg-indigo-50 text-indigo-600 border-indigo-200',
    compensation: 'bg-danger-light text-rose-600 border-rose-200',
    multileg: 'bg-teal-50 text-teal-600 border-teal-200'
  }
  return map[agent] || 'bg-warm-100 text-warm-600 border-warm-200'
}

function getAgentColor(agent) {
  const map = { sentinel: 'text-blue-600', profile: 'text-brand-purple', scout: 'text-cyan-600', arbiter: 'text-amber-600', baggage: 'text-indigo-600', compensation: 'text-rose-600', multileg: 'text-teal-600' }
  return map[agent] || 'text-warm-700'
}

function getTypeBadge(type) {
  const map = {
    NOTIFICATION: 'bg-info-light text-blue-600 border border-blue-200',
    REQUEST: 'bg-warning-light text-amber-600 border border-amber-200',
    RESPONSE: 'bg-success-light text-emerald-600 border border-emerald-200',
    WARNING: 'bg-danger-light text-rose-600 border border-rose-200'
  }
  return map[type] || 'bg-warm-100 text-warm-500 border border-warm-200'
}

function getMessageBg(msg) {
  return msg.message_type === 'WARNING' ? 'bg-danger-light/50' : 'bg-white'
}

function formatTime(ts) {
  if (!ts) return ''
  try { return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) } catch { return ts }
}

watch(() => props.messages.length, () => { nextTick(() => { if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight }) })
</script>
