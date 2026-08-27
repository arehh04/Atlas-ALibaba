<template>
  <header class="bg-white/80 backdrop-blur-md sticky top-0 z-50 px-3 sm:px-6 py-2.5 sm:py-3 border-b border-warm-200 shadow-soft">
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
          </div>

          <p class="text-[11px] text-warm-500 mt-0.5 hidden sm:block">
            Smart flight disruption recovery &middot; AI-powered rebooking
          </p>
        </div>
      </div>

      <!-- Right: Live System Status -->
      <div class="flex items-center gap-1.5 sm:gap-2 text-[10px] sm:text-[11px] font-mono">
        
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
          <span class="text-warm-800 font-medium truncate max-w-[120px]">{{ systemStatus?.atlas_gds_provider || 'Atlas CLI' }}</span>
        </div>

        <!-- Latency -->
        <div class="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 sm:py-1.5 rounded-xl bg-white border border-warm-200 transition-colors hover:border-brand-blue/30">
          <span class="text-warm-500 hidden sm:inline">Ping</span>
          <span class="text-success font-bold">{{ latencyMs || 42 }}ms</span>
        </div>

      </div>

    </div>
  </header>
</template>

<script setup>
defineProps({
  activePnr: { type: String, default: '' },
  systemStatus: { type: Object, default: () => ({}) },
  latencyMs: { type: Number, default: 42 }
})
</script>
