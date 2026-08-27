<template>
  <div class="ops-card p-3 sm:p-5">
    
    <!-- Section Header -->
    <div class="flex items-center justify-between border-b border-warm-200 pb-3 mb-4">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-xl bg-brand-gradient flex items-center justify-center shadow-soft">
          <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
          </svg>
        </div>
        <h2 class="font-display font-semibold text-sm text-warm-900">
          Recovery Pipeline
        </h2>
      </div>

      <div class="flex items-center gap-2 text-xs font-mono">
        <span class="text-warm-500">Phase:</span>
        <span 
          class="font-semibold px-2.5 py-0.5 rounded-full border text-[11px] transition-all duration-300"
          :class="getStatusBadgeClass()">
          {{ getReadablePhaseName() }}
        </span>
      </div>
    </div>

    <!-- 5-Node Pipeline -->
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 sm:gap-3 relative">
      
      <template v-for="(step, idx) in steps" :key="step.key">
        <div 
          class="relative p-4 rounded-2xl border transition-all duration-300 flex flex-col justify-between group"
          :class="getCardClass(step.key)">
          <div>
            <div class="flex items-center justify-between mb-3">
              <span class="text-[10px] font-mono font-bold text-warm-400 bg-warm-100 w-6 h-6 rounded-lg flex items-center justify-center">{{ String(idx + 1).padStart(2, '0') }}</span>
              <span class="text-[10px] font-medium px-2 py-0.5 rounded-full transition-all duration-300" :class="getBadgeClass(step.key)">
                {{ getNodeStatusText(step.key) }}
              </span>
            </div>
            <div class="flex items-center gap-2 mb-1">
              <div class="w-5 h-5 rounded-lg flex items-center justify-center" :class="step.iconBg">
                <span class="text-sm" v-html="step.icon"></span>
              </div>
              <h3 class="font-display font-semibold text-xs text-warm-900">{{ step.title }}</h3>
            </div>
            <p class="text-[11px] text-warm-500">{{ step.desc }}</p>
          </div>
          <div class="mt-3 pt-2 border-t border-warm-200/60 text-[10px] font-mono text-warm-500 flex items-center justify-between">
            <span>{{ step.engine }}</span>
            <span class="text-warm-700 font-bold">{{ stepTimes?.[step.key] ? `${stepTimes[step.key]}ms` : step.ready }}</span>
          </div>
          <!-- Connector chevron -->
          <div v-if="idx < steps.length - 1" class="hidden md:flex absolute -right-2 top-1/2 -translate-y-1/2 z-10 w-5 h-5 items-center justify-center">
            <svg class="w-3.5 h-3.5 transition-colors" :class="isActivePast(step.key) ? 'text-brand-purple' : 'text-warm-300'" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5"/>
            </svg>
          </div>
        </div>
      </template>

    </div>

  </div>
</template>

<script setup>
const props = defineProps({
  activeAgent: { type: String, default: 'idle' },
  stepTimes: { type: Object, default: () => ({}) }
})

const steps = [
  { key: 'sentinel', title: 'Sentinel', desc: 'Detects disruptions', engine: 'Hermes AI', ready: 'Ready', icon: '🔍', iconBg: 'bg-info-light' },
  { key: 'profile', title: 'Profile', desc: 'Checks loyalty & SLAs', engine: 'SLA Engine', ready: 'Ready', icon: '👤', iconBg: 'bg-brand-lavender' },
  { key: 'scout', title: 'Scout', desc: 'Searches live flights', engine: 'Atlas GDS', ready: 'Live', icon: '🔎', iconBg: 'bg-info-light' },
  { key: 'arbiter', title: 'Arbiter', desc: 'Scores route options', engine: 'DeepSeek AI', ready: 'Reasoning', icon: '📊', iconBg: 'bg-warning-light' },
  { key: 'executor', title: 'Execution', desc: 'Books & confirms', engine: 'Atlas Booking', ready: 'Standby', icon: '✅', iconBg: 'bg-success-light' },
]

function getStepIndex(key) {
  const idx = steps.findIndex(s => s.key === key)
  return idx >= 0 ? idx + 1 : 0
}

function getCurrentIndex() {
  if (props.activeAgent === 'completed') return 6
  if (props.activeAgent === 'executor') return 5
  if (props.activeAgent === 'hitl') return 4
  if (props.activeAgent === 'arbiter') return 4
  if (props.activeAgent === 'scout') return 3
  if (props.activeAgent === 'profile') return 2
  if (props.activeAgent === 'sentinel') return 1
  return 0
}

function isActivePast(key) { return getCurrentIndex() > getStepIndex(key) }

function getNodeStatusText(key) {
  const ci = getCurrentIndex(), ni = getStepIndex(key)
  if (ci === 0) return 'Standby'
  if (props.activeAgent === key) return 'Running'
  if (props.activeAgent === 'hitl' && key === 'arbiter') return 'Awaiting'
  if (ci > ni) return 'Done'
  return 'Queued'
}

function getCardClass(key) {
  const ci = getCurrentIndex(), ni = getStepIndex(key)
  if (props.activeAgent === key) return 'bg-white border-brand-purple shadow-glow-purple ring-1 ring-brand-purple/20 animate-slide-up'
  if (props.activeAgent === 'hitl' && key === 'arbiter') return 'bg-warning-light border-warning/40 ring-1 ring-warning/20'
  if (ci > ni) return 'bg-success-light/50 border-success/30'
  return 'bg-white border-warm-200 hover:border-warm-300 hover:shadow-soft'
}

function getBadgeClass(key) {
  const ci = getCurrentIndex(), ni = getStepIndex(key)
  if (props.activeAgent === key) return 'bg-brand-purple/10 text-brand-purple border border-brand-purple/20'
  if (props.activeAgent === 'hitl' && key === 'arbiter') return 'bg-warning-light text-warning-dark border border-warning/20'
  if (ci > ni) return 'bg-success-light text-success-dark border border-success/20'
  return 'bg-warm-100 text-warm-500 border border-warm-200'
}

function getStatusBadgeClass() {
  if (props.activeAgent === 'idle') return 'bg-warm-100 text-warm-500 border-warm-200'
  if (props.activeAgent === 'hitl') return 'bg-warning-light text-warning-dark border-warning/20'
  if (props.activeAgent === 'completed') return 'bg-success-light text-success-dark border-success/20'
  return 'bg-brand-purple/10 text-brand-purple border-brand-purple/20'
}

function getReadablePhaseName() {
  const map = {
    idle: 'Standby', hitl: 'Awaiting Passenger', completed: 'Recovery Done',
    executor: 'Booking Ticket', arbiter: 'Scoring Routes', scout: 'Searching Flights',
    profile: 'Checking Loyalty', sentinel: 'Detecting Disruption'
  }
  return map[props.activeAgent] || props.activeAgent?.toUpperCase() || 'STANDBY'
}
</script>
