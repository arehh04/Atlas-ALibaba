<template>
  <div class="ops-card p-4 sm:p-5">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-warm-200 pb-3 mb-4 gap-2">
      <div class="flex items-center gap-2">
        <div class="w-6 h-6 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/>
          </svg>
        </div>
        <h2 class="font-display font-semibold text-sm text-warm-900">Disruption History & Analytics</h2>
      </div>
      <div class="flex items-center gap-2">
        <select v-model="filterTier" class="bg-white border border-warm-200 rounded-xl px-2.5 py-1.5 text-[11px] text-warm-700 font-mono focus:outline-none focus:border-brand-purple/40 transition-all">
          <option value="">All Tiers</option>
          <option value="PLATINUM">PLATINUM</option>
          <option value="GOLD">GOLD</option>
          <option value="SILVER">SILVER</option>
          <option value="STANDARD">STANDARD</option>
        </select>
        <button @click="fetchData" class="px-3 py-1.5 rounded-xl bg-white hover:bg-warm-100 text-warm-600 border border-warm-200 text-[11px] transition">Refresh</button>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3 mb-4">
      <div class="p-2.5 sm:p-3 rounded-2xl bg-warm-100 border border-warm-200 text-center">
        <div class="text-xl sm:text-2xl font-bold text-brand-purple font-display">{{ stats.total_disruptions || 0 }}</div>
        <div class="text-[9px] sm:text-[10px] text-warm-500 uppercase font-mono">Total Events</div>
      </div>
      <div class="p-2.5 sm:p-3 rounded-2xl bg-warm-100 border border-warm-200 text-center">
        <div class="text-xl sm:text-2xl font-bold text-success-dark font-display">{{ stats.auto_approve_rate || 0 }}%</div>
        <div class="text-[9px] sm:text-[10px] text-warm-500 uppercase font-mono">Auto-Approved</div>
      </div>
      <div class="p-2.5 sm:p-3 rounded-2xl bg-warm-100 border border-warm-200 text-center">
        <div class="text-xl sm:text-2xl font-bold text-warning-dark font-display">{{ stats.hitl_rate || 0 }}%</div>
        <div class="text-[9px] sm:text-[10px] text-warm-500 uppercase font-mono">HITL Required</div>
      </div>
      <div class="p-2.5 sm:p-3 rounded-2xl bg-warm-100 border border-warm-200 text-center">
        <div class="text-xl sm:text-2xl font-bold text-brand-blue font-display">{{ stats.avg_resolution_seconds || 0 }}s</div>
        <div class="text-[9px] sm:text-[10px] text-warm-500 uppercase font-mono">Avg Resolution</div>
      </div>
    </div>

    <!-- Timeline Table -->
    <div class="overflow-x-auto -mx-4 sm:mx-0 px-4 sm:px-0">
      <table class="w-full text-xs min-w-[600px] sm:min-w-0">
        <thead>
          <tr class="text-warm-500 font-mono text-[10px] uppercase border-b border-warm-200">
            <th class="text-left py-2 px-2">Time</th>
            <th class="text-left px-2">PNR</th>
            <th class="text-left px-2">Flight</th>
            <th class="text-left px-2">Route</th>
            <th class="text-left px-2">Tier</th>
            <th class="text-left px-2">Status</th>
            <th class="text-left px-2">Reason</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in disruptions" :key="d.thread_id" class="border-b border-warm-200/60 hover:bg-warm-50 transition">
            <td class="py-2 px-2 text-warm-500 font-mono text-[10px]">{{ formatTime(d.created_at) }}</td>
            <td class="px-2 text-brand-purple font-mono font-bold">{{ d.pnr }}</td>
            <td class="px-2 text-warning-dark font-mono">{{ d.flight_number }}</td>
            <td class="px-2 text-warm-700">{{ d.origin }} → {{ d.destination }}</td>
            <td class="px-2">
              <span class="px-1.5 py-0.5 rounded-lg text-[10px] font-medium" :class="tierBadge(d.loyalty_tier)">{{ d.loyalty_tier }}</span>
            </td>
            <td class="px-2">
              <span class="px-1.5 py-0.5 rounded-lg text-[10px] font-medium" :class="statusBadge(d.hitl_status)">{{ d.hitl_status }}</span>
            </td>
            <td class="px-2 text-warm-500 max-w-[120px] sm:max-w-[200px] truncate">{{ d.disruption_reason }}</td>
          </tr>
          <tr v-if="disruptions.length === 0">
            <td colspan="7" class="py-6 text-center text-warm-400 italic">No disruption history yet. Trigger a scenario to populate.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { apiClient } from '../services/api'

const disruptions = ref([])
const stats = reactive({
  total_disruptions: 0,
  auto_approve_rate: 0,
  hitl_rate: 0,
  avg_resolution_seconds: 0,
})
const filterTier = ref('')

async function fetchData() {
  try {
    const [histData, statsData] = await Promise.all([
      apiClient.getHistory({ limit: 20, loyalty_tier: filterTier.value || undefined }),
      apiClient.getStats(),
    ])
    disruptions.value = histData.disruptions || []
    Object.assign(stats, statsData)
  } catch (e) {
    console.warn('History fetch failed:', e)
  }
}

function formatTime(iso) {
  if (!iso) return '-'
  try { return new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }
  catch { return iso }
}

function tierBadge(tier) {
  const map = { PLATINUM: 'bg-brand-lavender text-brand-purple border border-brand-purple/20', GOLD: 'bg-warning-light text-warning-dark border border-warning/20', SILVER: 'bg-warm-100 text-warm-700 border border-warm-200', STANDARD: 'bg-warm-100 text-warm-500 border border-warm-200' }
  return map[tier] || map.STANDARD
}

function statusBadge(status) {
  const map = { BYPASSED: 'bg-success-light text-success-dark border border-success/20', APPROVED: 'bg-success-light text-success-dark border border-success/20', PENDING: 'bg-warning-light text-warning-dark border border-warning/20', REJECTED: 'bg-danger-light text-danger-dark border border-danger/20', ERROR: 'bg-danger-light text-danger-dark border border-danger/20' }
  return map[status] || 'bg-warm-100 text-warm-500 border border-warm-200'
}

watch(filterTier, fetchData)
onMounted(fetchData)
</script>
