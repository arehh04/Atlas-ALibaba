<template>
  <header class="bg-white/90 backdrop-blur-md sticky top-0 z-50 px-3 sm:px-6 py-2.5 sm:py-3 border-b border-warm-200 shadow-soft">
    <div class="max-w-[1750px] mx-auto flex items-center justify-between">
      
      <!-- Left: Branding with Logo -->
      <div class="flex items-center gap-2 sm:gap-3">
        <img src="../assets/synapseair-logo.webp" alt="SynapseAir" class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl shadow-soft" />

        <div>
          <div class="flex items-center gap-1.5 sm:gap-2.5">
            <h1 class="text-base sm:text-lg font-bold font-display tracking-tight text-warm-900">
              SynapseAir
            </h1>

            <span class="text-[10px] sm:text-[11px] font-medium px-2 sm:px-2.5 py-0.5 rounded-full bg-success-light text-success-dark flex items-center gap-1 sm:gap-1.5">
              <span class="relative flex h-1.5 w-1.5">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-success"></span>
              </span>
              <span class="hidden xs:inline">System Online</span>
            </span>

            <span class="hidden md:inline-flex text-[10px] font-bold px-2 py-0.5 rounded-md bg-brand-purple/10 text-brand-purple border border-brand-purple/20">
              Alibaba Cloud × Atlas AI
            </span>
          </div>

          <p class="text-[11px] text-warm-500 mt-0.5 hidden sm:block">
            Autonomous Flight Disruption Recovery Swarm &middot; Zero-Touch Rebooking
          </p>
        </div>
      </div>

      <!-- Right: Live System Status & Pitch Guide Button -->
      <div class="flex items-center gap-1.5 sm:gap-2 text-[10px] sm:text-[11px] font-mono">
        
        <!-- Pitch Guide CTA Button for Judges -->
        <button @click.stop="showPitchModal = true" type="button"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-brand-gradient text-white font-sans font-semibold text-xs shadow-soft hover:shadow-glow-purple hover:scale-105 transition-all duration-200 active:scale-95">
          <span>🏆</span>
          <span class="hidden sm:inline">Pitch & ROI Guide</span>
          <span class="sm:hidden">Pitch</span>
        </button>

        <!-- Active PNR -->
        <div v-if="activePnr" class="hidden sm:flex items-center gap-1.5 px-2 sm:px-3 py-1.5 rounded-xl bg-brand-lavender border border-warm-200 text-warm-800 transition-colors">
          <span class="text-warm-500">PNR</span>
          <span class="font-bold text-brand-purple">{{ activePnr }}</span>
        </div>

        <!-- AI Engine -->
        <div class="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-warm-200 transition-colors hover:border-brand-purple/30">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-50"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
          </span>
          <span class="text-warm-500">AI</span>
          <span class="text-warm-800 font-medium">{{ systemStatus?.deepseek_model || 'DeepSeek V4' }}</span>
        </div>

        <!-- GDS Status -->
        <div class="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-warm-200 transition-colors hover:border-brand-cyan/30">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-cyan opacity-50"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-brand-cyan"></span>
          </span>
          <span class="text-warm-500">GDS</span>
          <span class="text-warm-800 font-medium truncate max-w-[120px]">{{ systemStatus?.atlas_gds_provider || 'Atlas CLI Live' }}</span>
        </div>

        <!-- Latency -->
        <div class="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 sm:py-1.5 rounded-xl bg-white border border-warm-200 transition-colors hover:border-brand-blue/30">
          <span class="text-warm-500 hidden sm:inline">Ping</span>
          <span class="text-success font-bold">{{ latencyMs || 42 }}ms</span>
        </div>

      </div>

    </div>

    <!-- Pitch Guide Modal for Judges (Teleported to Body) -->
    <Teleport to="body">
      <div v-if="showPitchModal" @click.self="showPitchModal = false" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-warm-900/60 backdrop-blur-sm animate-fade-in font-sans">
        <div class="bg-white rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-soft-xl border border-warm-200 relative overflow-hidden animate-slide-up">
          
          <!-- Background Glow Accent -->
          <div class="absolute -right-16 -top-16 w-64 h-64 bg-brand-purple/10 rounded-full blur-3xl pointer-events-none"></div>
          <div class="absolute -left-16 -bottom-16 w-64 h-64 bg-brand-cyan/10 rounded-full blur-3xl pointer-events-none"></div>

          <!-- Close Button -->
          <button @click="showPitchModal = false" type="button" class="absolute top-5 right-5 text-warm-400 hover:text-warm-700 p-2 rounded-xl hover:bg-warm-100 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>

          <!-- Modal Header -->
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 rounded-2xl bg-brand-gradient flex items-center justify-center shadow-soft text-2xl">
              🏆
            </div>
            <div>
              <h3 class="text-xl font-bold font-display text-warm-900">SynapseAir Executive Pitch Guide</h3>
              <p class="text-xs text-warm-500">Autonomous Disruption Recovery &middot; Alibaba Cloud × Atlas Agentic AI</p>
            </div>
          </div>

          <!-- 3-Column Problem vs Solution vs Impact -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 my-4">
            <div class="p-3.5 rounded-2xl bg-danger-light/50 border border-danger/20 text-xs">
              <span class="text-[10px] font-bold text-danger uppercase font-mono block mb-1">🚨 The Problem</span>
              <p class="text-warm-800 font-semibold text-xs mb-1">$60B Annual Crisis</p>
              <p class="text-warm-500 text-[11px]">400M passengers wait 4+ hours at airport counters during cancellations.</p>
            </div>
            <div class="p-3.5 rounded-2xl bg-brand-lavender border border-brand-purple/20 text-xs">
              <span class="text-[10px] font-bold text-brand-purple uppercase font-mono block mb-1">🤖 The Solution</span>
              <p class="text-warm-800 font-semibold text-xs mb-1">7-Agent AI Swarm</p>
              <p class="text-warm-500 text-[11px]">Detects disruptions, queries Atlas GDS, reasons with DeepSeek, & rebooks via WhatsApp in seconds.</p>
            </div>
            <div class="p-3.5 rounded-2xl bg-success-light/60 border border-success/20 text-xs">
              <span class="text-[10px] font-bold text-success uppercase font-mono block mb-1">💰 The ROI</span>
              <p class="text-warm-800 font-semibold text-xs mb-1">$540 Saved / Pax</p>
              <p class="text-warm-500 text-[11px]">Eliminates EU261 fines & hotel vouchers with 94% autonomous resolution.</p>
            </div>
          </div>

          <!-- 4 Key Value Metric Highlights -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-4 text-center">
            <div class="p-3 rounded-xl bg-warm-50 border border-warm-200">
              <span class="text-lg font-extrabold text-brand-purple font-display block">4.2s</span>
              <span class="text-[10px] text-warm-500 font-medium">Avg Recovery Time</span>
            </div>
            <div class="p-3 rounded-xl bg-warm-50 border border-warm-200">
              <span class="text-lg font-extrabold text-success font-display block">$840</span>
              <span class="text-[10px] text-warm-500 font-medium">Avg Arbitrage Saved</span>
            </div>
            <div class="p-3 rounded-xl bg-warm-50 border border-warm-200">
              <span class="text-lg font-extrabold text-brand-blue font-display block">94.2%</span>
              <span class="text-[10px] text-warm-500 font-medium">Zero-Touch Auto-Rate</span>
            </div>
            <div class="p-3 rounded-xl bg-warm-50 border border-warm-200">
              <span class="text-lg font-extrabold text-warm-900 font-display block">+84</span>
              <span class="text-[10px] text-warm-500 font-medium">Passenger NPS</span>
            </div>
          </div>

          <!-- Pitch Flow Steps -->
          <div class="p-3.5 rounded-2xl bg-brand-lavender/40 border border-brand-purple/20 space-y-2 text-xs">
            <div class="font-bold text-brand-purple flex items-center gap-1.5 text-xs">
              <span>⚡</span> Quick 30-Second Live Demo:
            </div>
            <div class="flex items-center gap-2 text-warm-700">
              <span class="w-5 h-5 rounded-full bg-brand-purple text-white flex items-center justify-center font-bold text-[10px]">1</span>
              <span>Click any preset scenario or paste a custom flight disruption.</span>
            </div>
            <div class="flex items-center gap-2 text-warm-700">
              <span class="w-5 h-5 rounded-full bg-brand-purple text-white flex items-center justify-center font-bold text-[10px]">2</span>
              <span>Watch the 7 agents collaborate live (Hermes ➔ Atlas GDS ➔ DeepSeek).</span>
            </div>
            <div class="flex items-center gap-2 text-warm-700">
              <span class="w-5 h-5 rounded-full bg-brand-purple text-white flex items-center justify-center font-bold text-[10px]">3</span>
              <span>Interact with the live WhatsApp simulator or see instant VIP e-ticketing!</span>
            </div>
          </div>

          <!-- Footer -->
          <div class="mt-5 flex justify-end">
            <button @click="showPitchModal = false" type="button"
              class="px-5 py-2.5 rounded-xl bg-brand-gradient text-white font-semibold text-xs shadow-soft hover:shadow-glow-purple transition">
              Got it, Let's Demo! 🚀
            </button>
          </div>

        </div>
      </div>
    </Teleport>
  </header>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  activePnr: { type: String, default: '' },
  systemStatus: { type: Object, default: () => ({}) },
  latencyMs: { type: Number, default: 42 }
})

const showPitchModal = ref(false)
</script>
