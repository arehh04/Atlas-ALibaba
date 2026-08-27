<template>
  <div class="ops-card p-4 sm:p-5 flex flex-col justify-between h-full">
    <div>
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-warm-200 pb-3 mb-4">
        <div class="flex items-center gap-2.5">
          <div class="w-7 h-7 rounded-xl bg-success-light flex items-center justify-center">
            <svg class="w-4 h-4 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.745 3.745 0 011.043 3.296A3.745 3.745 0 0121 12z"/>
            </svg>
          </div>
          <h2 class="font-display font-semibold text-sm text-warm-900">Recovery Plan</h2>
        </div>
        <span v-if="hitlStatus === 'WAITING_FOR_PASSENGER'" class="text-[11px] font-medium px-2.5 py-1 rounded-full bg-warning-light text-warning-dark border border-warning/20 flex items-center gap-1.5">
          <span class="relative flex h-1.5 w-1.5"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-warning opacity-75"></span><span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-warning"></span></span>
          Awaiting Passenger
        </span>
        <span v-else-if="hitlStatus === 'BYPASSED' || hitlStatus === 'APPROVED'" class="text-[11px] font-medium px-2.5 py-1 rounded-full bg-success-light text-success-dark border border-success/20 flex items-center gap-1.5">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/></svg>
          Confirmed
        </span>
      </div>

      <!-- Empty State -->
      <div v-if="!solution" class="flex flex-col items-center justify-center py-10 text-center animate-fade-in">
        <div class="w-14 h-14 rounded-2xl bg-warm-100 border border-warm-200 flex items-center justify-center mb-3">
          <svg class="w-7 h-7 text-warm-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"/>
          </svg>
        </div>
        <span class="text-warm-500 text-xs font-medium">Waiting for route analysis</span>
        <span class="text-warm-400 text-[11px] mt-1">Best alternatives will appear here</span>
      </div>

      <!-- Active Solution -->
      <div v-else class="space-y-3.5 text-xs animate-slide-up">
        <!-- Boarding Pass -->
        <div class="relative p-4 rounded-2xl bg-brand-lavender-light border border-warm-200 space-y-3 boarding-pass-edge overflow-hidden">
          <div class="absolute top-0 left-0 right-0 h-1 bg-brand-gradient rounded-t-2xl"></div>
          <div class="flex items-center justify-between">
            <span class="text-[10px] text-warm-500 font-mono uppercase tracking-wider">Replacement Flight</span>
            <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-brand-purple/10 text-brand-purple border border-brand-purple/20">
              {{ solution.cabin_class || 'Business' }} Class
            </span>
          </div>
          <div class="flex items-center justify-between py-2">
            <div>
              <div class="text-xl sm:text-3xl font-extrabold font-display text-warm-900 tracking-tight">{{ solution.origin }}</div>
              <div class="text-[11px] text-warm-500 mt-0.5">Dep {{ solution.departure_time?.split(' ')[1] || '14:30' }}</div>
            </div>
            <div class="flex-1 px-3 sm:px-5 flex flex-col items-center">
              <span class="text-[10px] font-mono text-brand-purple mb-1.5 font-bold">{{ solution.flight_number }}</span>
              <div class="w-full h-px bg-gradient-to-r from-brand-purple/30 via-warm-200 to-brand-cyan/30 relative flex items-center justify-center">
                <span class="text-brand-blue text-sm animate-float">✈</span>
              </div>
              <span class="text-[10px] text-warm-400 mt-1.5">{{ solution.airline }}</span>
            </div>
            <div class="text-right">
              <div class="text-xl sm:text-3xl font-extrabold font-display text-warm-900 tracking-tight">{{ solution.destination }}</div>
              <div class="text-[11px] text-warm-500 mt-0.5">Arr {{ solution.arrival_time?.split(' ')[1] || '15:45' }}</div>
            </div>
          </div>
          <!-- Score Ring -->
          <div class="pt-3 border-t border-warm-200/60">
            <div class="flex items-center gap-3">
              <div class="relative w-12 h-12 shrink-0">
                <svg class="w-12 h-12 -rotate-90" viewBox="0 0 48 48">
                  <circle cx="24" cy="24" r="19" fill="none" stroke="#EEEAF5" stroke-width="3"/>
                  <circle cx="24" cy="24" r="19" fill="none" stroke="#8A4FFF" stroke-width="3" stroke-linecap="round"
                    :stroke-dasharray="`${(solution.score_percentage || 96) * 1.19} 119`" class="transition-all duration-1000 ease-out"/>
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                  <span class="text-xs font-bold text-brand-purple">{{ solution.score_percentage || 96 }}</span>
                </div>
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between text-[11px] mb-1">
                  <span class="text-warm-500">SLA Match Score</span>
                  <span class="font-bold text-brand-purple">{{ solution.score_percentage || 96 }}%</span>
                </div>
                <div class="w-full h-2 bg-warm-200 rounded-full overflow-hidden">
                  <div class="h-full bg-brand-gradient rounded-full transition-all duration-1000 ease-out" :style="{ width: `${solution.score_percentage || 96}%` }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Savings -->
        <div class="p-3 sm:p-3.5 rounded-2xl bg-white border border-warm-200 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div class="flex items-start gap-2">
            <div class="w-8 h-8 rounded-xl bg-success-light flex items-center justify-center shrink-0">
              <span class="text-success text-sm">💰</span>
            </div>
            <div>
              <span class="text-[9px] text-warm-500 block uppercase font-mono tracking-wider">Savings</span>
              <span class="text-success-dark font-bold text-sm">${{ solution.financial_savings?.airline_savings_usd || 280 }}</span>
            </div>
          </div>
          <div class="flex items-start gap-2">
            <div class="w-8 h-8 rounded-xl bg-info-light flex items-center justify-center shrink-0">
              <span class="text-info text-sm">🛡️</span>
            </div>
            <div>
              <span class="text-[9px] text-warm-500 block uppercase font-mono tracking-wider">Penalty Avoided</span>
              <span class="text-warm-800 font-semibold">${{ solution.financial_savings?.hotel_penalty_avoided_usd || 350 }}</span>
            </div>
          </div>
        </div>

        <!-- AI Rationale -->
        <div class="p-3.5 rounded-2xl bg-warm-50 border border-warm-200 text-xs">
          <div class="font-display font-semibold text-warm-800 mb-1.5 flex items-center gap-2 text-[11px]">
            <span class="text-brand-purple">✨</span> AI Decision Summary
          </div>
          <p class="leading-relaxed text-warm-600 text-[11px]">{{ solution.rationale }}</p>
        </div>

        <!-- Ticket Confirmed -->
        <div v-if="ticketReceipt" class="p-3.5 rounded-2xl bg-success-light border border-success/20 flex items-center justify-between animate-slide-up">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-xl bg-success/20 flex items-center justify-center">
              <svg class="w-4 h-4 text-success-dark" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/></svg>
            </div>
            <div>
              <div class="font-display font-bold text-xs text-success-dark">E-Ticket Confirmed</div>
              <div class="text-[10px] font-mono text-success">{{ ticketReceipt.e_ticket_number }}</div>
            </div>
          </div>
          <div class="text-right text-[11px]">
            <span class="text-warm-500">Seat</span>
            <strong class="text-warm-900 ml-1">{{ ticketReceipt.assigned_seat || '12A' }}</strong>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  solution: { type: Object, default: null },
  hitlStatus: { type: String, default: 'IDLE' },
  ticketReceipt: { type: Object, default: null }
})
</script>
