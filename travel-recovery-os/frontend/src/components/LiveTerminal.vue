<template>
  <div class="ops-card p-3 sm:p-4 flex flex-col h-full font-mono text-xs">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-warm-200 pb-3 mb-3 gap-2">
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded-full bg-danger"></span>
          <span class="w-2.5 h-2.5 rounded-full bg-warning"></span>
          <span class="w-2.5 h-2.5 rounded-full bg-success"></span>
        </div>
        <h3 class="font-display font-semibold text-xs text-warm-900 flex items-center gap-2">
          <span>📡</span> Live Telemetry
          <span class="text-[10px] font-normal px-2 py-0.5 rounded-full bg-warm-100 text-warm-500 border border-warm-200">{{ filteredLogs.length }} events</span>
        </h3>
      </div>
      <div class="flex flex-wrap items-center gap-1.5 sm:gap-2 text-xs">
        <div class="flex items-center bg-warm-100 rounded-xl p-0.5 border border-warm-200 text-[11px]">
          <button @click="viewMode = 'friendly'" type="button" class="px-2.5 py-1 rounded-lg transition"
            :class="viewMode === 'friendly' ? 'bg-white text-warm-900 shadow-soft font-semibold' : 'text-warm-500 hover:text-warm-700'">✨ Friendly View</button>
          <button @click="viewMode = 'raw'" type="button" class="px-2.5 py-1 rounded-lg transition"
            :class="viewMode === 'raw' ? 'bg-white text-warm-900 shadow-soft font-semibold' : 'text-warm-500 hover:text-warm-700'">💻 Raw Terminal</button>
        </div>
        <div class="flex items-center bg-warm-100 rounded-xl p-0.5 border border-warm-200 text-[11px]">
          <button v-for="flt in ['all', 'sentinel', 'scout', 'arbiter']" :key="flt" @click="activeFilter = flt"
            class="px-2 sm:px-2.5 py-1 sm:py-0.5 rounded-lg capitalize transition"
            :class="activeFilter === flt ? 'bg-white text-warm-900 shadow-soft font-semibold' : 'text-warm-500 hover:text-warm-700'">{{ flt }}</button>
        </div>
        <input v-model="searchQuery" type="text" placeholder="Filter..." class="bg-white border border-warm-200 rounded-xl px-2.5 py-1.5 sm:py-1 text-[11px] text-warm-800 placeholder-warm-400 focus:outline-none focus:border-brand-purple/40 w-full sm:w-32 transition-all" />
        <button @click="downloadLogs" :disabled="logs.length === 0" class="px-2.5 py-1.5 sm:py-1 rounded-xl bg-white hover:bg-warm-50 text-warm-600 border border-warm-200 text-[11px] disabled:opacity-40 transition">Export</button>
        <button @click="emit('clear')" class="px-2.5 py-1.5 sm:py-1 rounded-xl bg-white hover:bg-warm-50 text-warm-600 border border-warm-200 text-[11px] transition">Clear</button>
      </div>
    </div>

    <!-- Friendly Activity Timeline View -->
    <div v-if="viewMode === 'friendly'" ref="friendlyWindow" class="flex-1 overflow-y-auto rounded-2xl bg-white border border-warm-200 p-3.5 space-y-2 text-xs font-sans">
      <div v-if="filteredLogs.length === 0" class="text-warm-400 py-8 text-center select-none flex flex-col items-center gap-2 font-mono text-xs">
        <span class="text-2xl">📡</span>
        <span>Telemetry ready. Trigger any disruption to watch the live multi-agent swarm in action.</span>
      </div>
      <div v-for="log in filteredLogs" :key="log.id" class="p-2.5 rounded-xl border border-warm-200/80 bg-warm-50 hover:bg-white hover:shadow-soft transition-all flex items-start gap-3 animate-fade-in">
        <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-sm font-bold shadow-soft" :class="getFriendlyIconBg(log)">
          <span>{{ getFriendlyIcon(log) }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between gap-2 mb-0.5">
            <span class="font-bold font-display text-xs text-warm-900 capitalize">{{ log.node || 'Agent' }}</span>
            <span class="text-[10px] font-mono text-warm-400">{{ formatTime(log.timestamp) }}</span>
          </div>
          <p class="text-warm-700 text-xs leading-relaxed font-medium">{{ log.message }}</p>
        </div>
      </div>
    </div>

    <!-- Raw Developer Terminal Output -->
    <div v-else ref="terminalWindow" class="flex-1 overflow-y-auto rounded-2xl bg-warm-900 border border-warm-700 p-3.5 space-y-1.5 text-xs leading-relaxed scanline-overlay font-mono">
      <div v-if="filteredLogs.length === 0" class="text-warm-500 italic py-8 text-center select-none flex flex-col items-center gap-2">
        <span class="text-2xl">📡</span>
        <span>Telemetry ready. Trigger a scenario to see live agent activity.</span>
      </div>
      <div v-for="log in filteredLogs" :key="log.id" class="flex items-start gap-2.5 group hover:bg-white/[0.03] p-1.5 rounded-lg transition animate-fade-in">
        <span class="text-warm-500 select-none shrink-0 text-[10px] tabular-nums">{{ formatTime(log.timestamp) }}</span>
        <span class="px-1.5 py-0.5 rounded-md font-semibold uppercase shrink-0 text-[9px] tracking-wider" :class="getTagStyle(log)">{{ log.node }}</span>
        <div class="flex-1 text-warm-300 break-words">
          <span>{{ log.message }}</span>
          <pre v-if="log.data" class="mt-1 text-[10px] text-brand-cyan/80 bg-black/30 p-2 rounded-lg border border-warm-700/40 overflow-x-auto">{{ JSON.stringify(log.data, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({ logs: { type: Array, default: () => [] } })
const emit = defineEmits(['clear'])
const viewMode = ref('friendly')
const activeFilter = ref('all')
const searchQuery = ref('')
const autoScroll = ref(true)
const terminalWindow = ref(null)
const friendlyWindow = ref(null)

const filteredLogs = computed(() => {
  return props.logs.filter(log => {
    const nodeMatches = activeFilter.value === 'all' || (log.node || '').toLowerCase().includes(activeFilter.value)
    const query = searchQuery.value.trim().toLowerCase()
    const textMatches = !query || (log.message || '').toLowerCase().includes(query) || (log.node || '').toLowerCase().includes(query)
    return nodeMatches && textMatches
  })
})

watch(() => props.logs.length, () => {
  if (autoScroll.value && terminalWindow.value) nextTick(() => { terminalWindow.value.scrollTop = terminalWindow.value.scrollHeight })
})

function formatTime(iso) {
  if (!iso) return new Date().toLocaleTimeString()
  try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) } catch { return iso }
}

function getTagStyle(log) {
  const n = (log.node || '').toLowerCase(), l = (log.level || '').toUpperCase()
  if (n.includes('sentinel')) return 'bg-blue-500/15 text-blue-300 border border-blue-500/20'
  if (n.includes('profile')) return 'bg-purple-500/15 text-purple-300 border border-purple-500/20'
  if (n.includes('scout')) return 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/20'
  if (n.includes('arbiter')) return 'bg-amber-500/15 text-amber-300 border border-amber-500/20'
  if (n.includes('execution') || l === 'SUCCESS') return 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/20'
  if (l === 'ERROR') return 'bg-rose-500/15 text-rose-300 border border-rose-500/20'
  return 'bg-warm-700/50 text-warm-400 border border-warm-600/50'
}

function getFriendlyIcon(log) {
  const n = (log.node || '').toLowerCase(), l = (log.level || '').toUpperCase()
  if (n.includes('sentinel')) return '🔍'
  if (n.includes('profile')) return '👤'
  if (n.includes('scout')) return '🔎'
  if (n.includes('baggage')) return '🧳'
  if (n.includes('arbiter')) return '📊'
  if (n.includes('compensation')) return '🛡️'
  if (n.includes('execution') || l === 'SUCCESS') return '🎟️'
  if (l === 'ERROR') return '⚠️'
  return '⚡'
}

function getFriendlyIconBg(log) {
  const n = (log.node || '').toLowerCase(), l = (log.level || '').toUpperCase()
  if (n.includes('sentinel')) return 'bg-info-light text-brand-blue'
  if (n.includes('profile')) return 'bg-brand-lavender text-brand-purple'
  if (n.includes('scout')) return 'bg-cyan-50 text-cyan-600'
  if (n.includes('baggage')) return 'bg-warm-100 text-warm-700'
  if (n.includes('arbiter')) return 'bg-warning-light text-warning-dark'
  if (n.includes('compensation')) return 'bg-emerald-50 text-emerald-700'
  if (n.includes('execution') || l === 'SUCCESS') return 'bg-success-light text-success-dark'
  if (l === 'ERROR') return 'bg-danger-light text-danger'
  return 'bg-brand-lavender text-brand-purple'
}

function downloadLogs() {
  const blob = new Blob([JSON.stringify(props.logs, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `synapseair-logs-${Date.now()}.json`; a.click()
  URL.revokeObjectURL(url)
}
</script>
