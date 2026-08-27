<template>
  <div class="ops-card p-4 sm:p-5 flex flex-col justify-between h-full">
    
    <div>
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-warm-200 pb-3 mb-4">
        <div class="flex items-center gap-2.5">
          <div class="w-7 h-7 rounded-xl bg-danger-light flex items-center justify-center">
            <svg class="w-4 h-4 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z"/>
            </svg>
          </div>
          <h2 class="font-display font-semibold text-sm text-warm-900">
            Simulate a Disruption
          </h2>
        </div>

        <div class="flex items-center bg-warm-100 rounded-xl p-0.5 border border-warm-200 text-xs">
          <button @click="inputMode = 'scenarios'" type="button" class="px-2.5 py-1 rounded-lg transition font-medium text-[11px]"
            :class="inputMode === 'scenarios' ? 'bg-white text-warm-900 shadow-soft' : 'text-warm-500 hover:text-warm-700'">Scenarios</button>
          <button @click="inputMode = 'custom'" type="button" class="px-2.5 py-1 rounded-lg transition font-medium text-[11px]"
            :class="inputMode === 'custom' ? 'bg-white text-warm-900 shadow-soft' : 'text-warm-500 hover:text-warm-700'">Custom</button>
          <button @click="inputMode = 'hermes'" type="button" class="px-2.5 py-1 rounded-lg transition font-medium text-[11px]"
            :class="inputMode === 'hermes' ? 'bg-white text-brand-purple shadow-soft' : 'text-warm-500 hover:text-warm-700'">AI Parse</button>
        </div>
      </div>

      <!-- MODE 1: SCENARIOS -->
      <div v-if="inputMode === 'scenarios'" class="space-y-2.5 text-xs">
        <div class="flex items-center justify-between text-warm-500 text-xs mb-1">
          <span>Choose a scenario to simulate:</span>
          <span class="text-[10px] text-brand-purple font-semibold">1-Click Live AI Run</span>
        </div>

        <button v-for="preset in presets" :key="preset.id" @click="selectPreset(preset)" type="button"
          class="w-full p-3.5 rounded-2xl border text-left transition-all duration-200 group relative overflow-hidden"
          :class="selectedPresetId === preset.id ? 'bg-brand-lavender border-brand-purple/40 ring-1 ring-brand-purple/20 shadow-soft' : 'bg-white border-warm-200 hover:border-warm-300 hover:shadow-soft hover:translate-y-[-1px]'">
          
          <div class="flex items-center justify-between font-semibold text-warm-900 mb-1">
            <span :class="preset.titleColor">{{ preset.title }}</span>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-mono" :class="preset.badgeStyle">{{ preset.loyalty_tier }}</span>
          </div>

          <div class="flex items-center gap-1.5 text-[10px] text-brand-purple font-medium my-1">
            <span class="w-1.5 h-1.5 rounded-full bg-brand-purple"></span>
            <span>{{ preset.highlight }}</span>
          </div>

          <p class="text-[11px] text-warm-500">
            {{ preset.origin }} → {{ preset.destination }} · {{ preset.reason }} · {{ preset.delay_minutes }}m
          </p>
        </button>
      </div>

      <!-- MODE 2: CUSTOM FORM -->
      <form v-else-if="inputMode === 'custom'" @submit.prevent="triggerRecovery" class="space-y-3 text-xs">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <div>
            <label class="text-warm-600 block mb-1 font-medium">Booking Ref (PNR)</label>
            <input v-model="form.pnr" type="text" class="w-full bg-white border border-warm-200 rounded-xl px-3 py-2.5 text-warm-900 font-mono font-semibold focus:outline-none focus:border-brand-purple/50 focus:ring-2 focus:ring-brand-purple/10 transition-all" required />
          </div>
          <div>
            <label class="text-warm-600 block mb-1 font-medium">Flight Number</label>
            <input v-model="form.flight_number" type="text" class="w-full bg-white border border-warm-200 rounded-xl px-3 py-2.5 text-warm-800 font-mono font-semibold focus:outline-none focus:border-brand-purple/50 focus:ring-2 focus:ring-brand-purple/10 transition-all" required />
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <div>
            <label class="text-warm-600 block mb-1 font-medium">From</label>
            <select v-model="form.origin" class="w-full bg-white border border-warm-200 rounded-xl px-2.5 py-2.5 text-warm-800 font-mono focus:outline-none focus:border-brand-purple/50 transition-all">
              <option v-for="a in airports" :key="a.code" :value="a.code">{{ a.code }} - {{ a.name }}</option>
            </select>
          </div>
          <div>
            <label class="text-warm-600 block mb-1 font-medium">To</label>
            <select v-model="form.destination" class="w-full bg-white border border-warm-200 rounded-xl px-2.5 py-2.5 text-warm-800 font-mono focus:outline-none focus:border-brand-purple/50 transition-all">
              <option v-for="a in airports" :key="a.code" :value="a.code">{{ a.code }} - {{ a.name }}</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <div>
            <label class="text-warm-600 block mb-1 font-medium">Passenger Name</label>
            <input v-model="form.passenger_name" type="text" class="w-full bg-white border border-warm-200 rounded-xl px-3 py-2.5 text-warm-800 focus:outline-none focus:border-brand-purple/50 focus:ring-2 focus:ring-brand-purple/10 transition-all" />
          </div>
          <div>
            <label class="text-warm-600 block mb-1 font-medium">Loyalty Tier</label>
            <select v-model="form.loyalty_tier" class="w-full bg-white border border-warm-200 rounded-xl px-2.5 py-2.5 text-brand-purple font-semibold focus:outline-none focus:border-brand-purple/50 transition-all">
              <option value="PLATINUM">PLATINUM (Auto-Bypass)</option>
              <option value="GOLD">GOLD (Auto-Bypass)</option>
              <option value="SILVER">SILVER (WhatsApp Consent)</option>
              <option value="STANDARD">STANDARD (WhatsApp Consent)</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <div class="sm:col-span-2">
            <label class="text-warm-600 block mb-1 font-medium">Disruption Cause</label>
            <input v-model="form.reason" type="text" class="w-full bg-white border border-warm-200 rounded-xl px-3 py-2.5 text-warm-800 focus:outline-none focus:border-brand-purple/50 focus:ring-2 focus:ring-brand-purple/10 transition-all" />
          </div>
          <div>
            <label class="text-warm-600 block mb-1 font-medium">Delay (mins)</label>
            <input v-model.number="form.delay_minutes" type="number" min="30" max="720" class="w-full bg-white border border-warm-200 rounded-xl px-2 py-2.5 text-warm-800 font-mono font-semibold focus:outline-none focus:border-brand-purple/50 transition-all" />
          </div>
        </div>
      </form>

      <!-- MODE 3: AI TEXT PARSER -->
      <form v-else @submit.prevent="triggerRecovery" class="space-y-3 text-xs">
        <div class="p-3 rounded-xl bg-brand-lavender border border-brand-purple/20 text-brand-purple text-xs flex items-start gap-2">
          <span class="text-lg">🤖</span>
          <div>
            <strong>Hermes AI Parser Active</strong> — Paste any raw flight alert, NOTAM, or passenger SMS. The AI will extract flight details automatically.
          </div>
        </div>

        <!-- 1-Click Sample Alert Pills -->
        <div>
          <label class="text-warm-500 block mb-1 text-[11px]">Quick 1-Click Sample Messages:</label>
          <div class="flex flex-wrap gap-1.5 mb-2">
            <button type="button" @click="setRawSample(1)" class="px-2.5 py-1 rounded-lg bg-warm-100 hover:bg-brand-lavender text-warm-700 text-[10px] font-medium border border-warm-200 transition">
              ✈️ Changi Hydraulic Fault
            </button>
            <button type="button" @click="setRawSample(2)" class="px-2.5 py-1 rounded-lg bg-warm-100 hover:bg-brand-lavender text-warm-700 text-[10px] font-medium border border-warm-200 transition">
              🌪️ Typhoon Warning
            </button>
            <button type="button" @click="setRawSample(3)" class="px-2.5 py-1 rounded-lg bg-warm-100 hover:bg-brand-lavender text-warm-700 text-[10px] font-medium border border-warm-200 transition">
              ⏱️ ATC Ground Delay
            </button>
          </div>
        </div>

        <div>
          <label class="text-warm-600 block mb-1 font-medium">Raw Message Text</label>
          <textarea v-model="form.raw_text" rows="3"
            class="w-full bg-white border border-brand-purple/30 rounded-xl p-3 text-warm-900 font-mono text-xs focus:outline-none focus:border-brand-purple/50 focus:ring-2 focus:ring-brand-purple/10 transition-all"
            placeholder="e.g. URGENT: Flight SQ108 from SIN to KUL grounded due to hydraulic fault..." required></textarea>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <div>
            <label class="text-warm-600 block mb-1 font-medium">Passenger Name</label>
            <input v-model="form.passenger_name" type="text" class="w-full bg-white border border-warm-200 rounded-xl px-3 py-2.5 text-warm-800 focus:outline-none focus:border-brand-purple/50 focus:ring-2 focus:ring-brand-purple/10 transition-all" />
          </div>
          <div>
            <label class="text-warm-600 block mb-1 font-medium">Loyalty Tier</label>
            <select v-model="form.loyalty_tier" class="w-full bg-white border border-warm-200 rounded-xl px-2.5 py-2.5 text-brand-purple font-semibold focus:outline-none focus:border-brand-purple/50 transition-all">
              <option value="PLATINUM">PLATINUM (Auto-Bypass)</option>
              <option value="GOLD">GOLD (Auto-Bypass)</option>
              <option value="SILVER">SILVER (WhatsApp Consent)</option>
              <option value="STANDARD">STANDARD (WhatsApp Consent)</option>
            </select>
          </div>
        </div>
      </form>
    </div>

    <!-- CTA Button -->
    <div class="pt-4 mt-2">
      <button @click="triggerRecovery" :disabled="isStreaming"
        class="w-full py-3.5 px-4 rounded-2xl font-display font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2 relative overflow-hidden group shadow-soft-md"
        :class="isStreaming ? 'bg-warm-200 text-warm-500 cursor-not-allowed' : 'bg-brand-gradient text-white hover:shadow-glow-purple hover:-translate-y-0.5 active:translate-y-0'">
        <span v-if="!isStreaming" class="absolute inset-0 animate-shimmer opacity-40"></span>
        <svg v-if="isStreaming" class="animate-spin h-4 w-4 text-warm-500" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        <span v-else class="flex items-center gap-2 relative z-10">
          <span class="text-base">🚀</span>
          <span>Launch Autonomous Recovery Swarm</span>
        </span>
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const props = defineProps({ isStreaming: Boolean })
const emit = defineEmits(['trigger'])

const inputMode = ref('scenarios')
const selectedPresetId = ref('sq108')

const airports = [
  { code: 'KUL', name: 'Kuala Lumpur' }, { code: 'SIN', name: 'Singapore Changi' },
  { code: 'HGH', name: 'Hangzhou' }, { code: 'PVG', name: 'Shanghai' },
  { code: 'DXB', name: 'Dubai' }, { code: 'LHR', name: 'London Heathrow' },
  { code: 'NRT', name: 'Tokyo Narita' }, { code: 'BKK', name: 'Bangkok' },
]

const presets = [
  { id: 'sq108', title: 'SQ108 Canceled (Changi Hub)', highlight: '⚡ VIP Gold Auto-Bypass · Business Upgrade', titleColor: 'text-danger', badgeStyle: 'bg-warning-light text-warning-dark border border-warning/20', pnr: 'SQ108-SIN', flight_number: 'SQ-108', origin: 'SIN', destination: 'KUL', passenger_name: 'Dr. Alexander Vance', loyalty_tier: 'GOLD', reason: 'Aircraft Hydraulic Sensor Fault', delay_minutes: 240, raw_text: 'URGENT NOTAM: Singapore Airlines SQ108 SIN-KUL canceled due to hydraulic sensor fault. Passenger Dr. Vance requires immediate flight recovery.' },
  { id: 'mh128', title: 'MH128 Delayed Connection', highlight: '📱 Multi-Leg Baggage Transfer · WhatsApp HITL', titleColor: 'text-warning-dark', badgeStyle: 'bg-warm-100 text-warm-700 border border-warm-200', pnr: 'MH128-KUL', flight_number: 'MH-128', origin: 'KUL', destination: 'SIN', passenger_name: 'Marcus Brody', loyalty_tier: 'STANDARD', reason: 'Air Traffic Flow Control', delay_minutes: 320, raw_text: 'OPS ADVISORY: Flight MH128 KUL-SIN delayed 320 minutes due to flow hold. Passenger Marcus Brody will miss onward connection.' },
  { id: 'cz3042', title: 'CZ3042 Typhoon Grounding', highlight: '🌪️ Extreme Weather Reroute · Interline Partner', titleColor: 'text-brand-blue', badgeStyle: 'bg-brand-lavender text-brand-purple border border-brand-purple/20', pnr: 'CZ3042-VIP', flight_number: 'CZ-3042', origin: 'KUL', destination: 'HGH', passenger_name: 'Elena Rostova', loyalty_tier: 'PLATINUM', reason: 'Typhoon Flow Control', delay_minutes: 300, raw_text: 'WEATHER NOTAM: China Southern CZ3042 KUL-HGH grounded due to Typhoon Gaemi. Passenger Elena Rostova requires VIP direct rebooking.' }
]

const form = reactive({
  pnr: 'SQ108-SIN', flight_number: 'SQ-108', origin: 'SIN', destination: 'KUL',
  travel_date: new Date().toISOString().split('T')[0], passenger_name: 'Dr. Alexander Vance',
  loyalty_tier: 'GOLD', reason: 'Aircraft Hydraulic Sensor Fault (AOG)', delay_minutes: 240,
  raw_text: 'URGENT NOTAM: Singapore Airlines SQ108 SIN-KUL canceled due to hydraulic sensor fault.'
})

function setRawSample(id) {
  if (id === 1) {
    form.raw_text = "URGENT NOTAM: Singapore Airlines SQ108 SIN-KUL canceled due to aircraft hydraulic sensor fault (AOG). Passenger Dr. Alexander Vance requires immediate rebooking."
    form.passenger_name = "Dr. Alexander Vance"
    form.loyalty_tier = "GOLD"
  } else if (id === 2) {
    form.raw_text = "WEATHER NOTAM: China Southern CZ3042 KUL-HGH grounded due to Typhoon Gaemi. Passenger Elena Rostova requires VIP direct flight recovery."
    form.passenger_name = "Elena Rostova"
    form.loyalty_tier = "PLATINUM"
  } else {
    form.raw_text = "OPS ADVISORY: Flight MH128 KUL-SIN delayed 320 minutes due to Air Traffic Flow Control. Passenger Marcus Brody will miss onward connection."
    form.passenger_name = "Marcus Brody"
    form.loyalty_tier = "STANDARD"
  }
}

function selectPreset(preset) {
  selectedPresetId.value = preset.id
  Object.assign(form, { pnr: preset.pnr, flight_number: preset.flight_number, origin: preset.origin, destination: preset.destination, passenger_name: preset.passenger_name, loyalty_tier: preset.loyalty_tier, reason: preset.reason, delay_minutes: preset.delay_minutes, raw_text: preset.raw_text })
}

function triggerRecovery() {
  emit('trigger', { ...form, raw_text: inputMode.value === 'hermes' ? form.raw_text : null })
}
</script>
