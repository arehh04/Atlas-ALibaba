<template>
  <div class="ops-card p-4 sm:p-5 h-full flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-warm-200 pb-3 mb-4">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-xl bg-info-light flex items-center justify-center">
          <span class="text-sm">🌐</span>
        </div>
        <h3 class="font-display font-semibold text-sm text-warm-900">Flight Routes</h3>
      </div>
      <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-warm-100 text-warm-500 border border-warm-200">{{ routes.length }} routes</span>
    </div>

    <!-- SVG Map Container -->
    <div class="flex-1 min-h-[200px] sm:min-h-[260px] bg-brand-lavender-light rounded-2xl border border-warm-200 overflow-hidden relative">
      <svg viewBox="0 0 800 400" class="w-full h-full">
        <defs>
          <linearGradient id="routeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#8A4FFF" stop-opacity="0.8"/>
            <stop offset="100%" stop-color="#4FA8FF" stop-opacity="0.8"/>
          </linearGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        <!-- Grid -->
        <g stroke="#DDD8EB" stroke-width="0.5" opacity="0.5">
          <line v-for="i in 10" :key="'h'+i" x1="0" :y1="i*40" x2="800" :y2="i*40"/>
          <line v-for="i in 20" :key="'v'+i" :x1="i*40" y1="0" :x2="i*40" y2="400"/>
        </g>

        <!-- Flight Paths -->
        <g v-for="(route, idx) in routes" :key="'path-'+idx">
          <path :d="getArcPath(route)" fill="none" :stroke="route.id === selectedRouteId ? '#8A4FFF' : '#B8B2CC'"
            :stroke-width="route.id === selectedRouteId ? 3 : 1.5" stroke-dasharray="8 5" opacity="0.8">
            <animate attributeName="stroke-dashoffset" from="0" to="-26" dur="2s" repeatCount="indefinite"/>
          </path>
        </g>

        <!-- Origin/Hub Markers -->
        <g v-for="(hub, idx) in hubs" :key="'hub-'+idx">
          <circle :cx="hub.x" :cy="hub.y" r="6" :fill="hub.origin ? '#8A4FFF' : '#4FA8FF'" filter="url(#glow)"/>
          <circle :cx="hub.x" :cy="hub.y" r="6" :fill="hub.origin ? '#8A4FFF' : '#4FA8FF'" opacity="0.4">
            <animate attributeName="r" values="6;14;6" dur="2.5s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="0.4;0;0.4" dur="2.5s" repeatCount="indefinite"/>
          </circle>
          <text :x="hub.x + 12" :y="hub.y + 4" class="text-[11px] font-bold" :fill="hub.origin ? '#8A4FFF' : '#1E1B2E'" font-family="Outfit, sans-serif">{{ hub.code }}</text>
        </g>
      </svg>

      <!-- Legend -->
      <div class="absolute bottom-2 left-2 sm:bottom-3 sm:left-3 bg-white/95 backdrop-blur-sm border border-warm-200 rounded-xl p-2 sm:p-2.5 text-[10px] font-mono space-y-1.5 shadow-soft">
        <div v-for="(route, idx) in routes" :key="'leg-'+idx" class="flex items-center gap-2 cursor-pointer hover:text-brand-purple transition px-1.5 py-0.5 rounded-lg hover:bg-brand-lavender/50" @click="selectedRouteId = route.id">
          <span class="w-5 h-px border-t-2" :class="route.id === selectedRouteId ? 'border-brand-purple border-dashed' : 'border-warm-400 border-dotted'"></span>
          <span class="text-warm-700 font-medium">{{ route.origin }} → {{ route.destination }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  origin: { type: String, default: 'SIN' },
  destination: { type: String, default: 'KUL' }
})

const selectedRouteId = ref('recovery')

const airportCoords = {
  'SIN': { x: 620, y: 280 }, 'KUL': { x: 540, y: 250 }, 'BKK': { x: 550, y: 160 },
  'HGH': { x: 700, y: 120 }, 'PVG': { x: 720, y: 100 }, 'DXB': { x: 260, y: 140 },
  'LHR': { x: 150, y: 80 }, 'NRT': { x: 750, y: 100 }
}

const routes = computed(() => {
  const originCoords = airportCoords[props.origin] || { x: 400, y: 200 }
  const destCoords = airportCoords[props.destination] || { x: 600, y: 200 }
  return [
    { id: 'original', origin: props.origin, destination: props.destination, from: originCoords, to: destCoords, label: 'Original Route' },
    { id: 'recovery', origin: props.origin, destination: props.destination, from: originCoords, to: destCoords, label: 'Recovery Route' }
  ]
})

const hubs = computed(() => {
  const o = airportCoords[props.origin] || { x: 400, y: 200 }
  const d = airportCoords[props.destination] || { x: 600, y: 200 }
  return [
    { code: props.origin, x: o.x, y: o.y, origin: true },
    { code: props.destination, x: d.x, y: d.y, origin: false },
  ]
})

function getArcPath(route) {
  const dx = route.to.x - route.from.x, dy = route.to.y - route.from.y
  const cx = (route.from.x + route.to.x) / 2, cy = (route.from.y + route.to.y) / 2 - Math.sqrt(dx*dx + dy*dy) * 0.2
  return `M ${route.from.x} ${route.from.y} Q ${cx} ${cy} ${route.to.x} ${route.to.y}`
}
</script>
