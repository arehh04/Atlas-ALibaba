<template>
  <div class="rounded-[2rem] border-2 border-warm-300 bg-white shadow-soft-lg overflow-hidden flex flex-col h-full max-h-[600px] sm:max-h-[700px] w-full max-w-sm font-sans text-warm-900 ring-1 ring-warm-200">
    
    <!-- Phone Top Status Bar -->
    <div class="bg-warm-800 px-4 py-1.5 flex items-center justify-between text-[10px] text-warm-300 font-mono select-none rounded-t-[1.85rem]">
      <span class="font-semibold text-warm-200">{{ currentTime }}</span>
      <div class="flex items-center gap-1.5 text-[9px]">
        <span>5G</span>
        <span>100%</span>
      </div>
    </div>

    <!-- Countdown Timer Banner -->
    <div v-if="countdownActive" class="bg-warning-light border-b border-warning/20 px-3 py-2 flex items-center justify-between">
      <div class="flex items-center gap-2 text-[10px] text-warning-dark">
        <svg class="w-3.5 h-3.5 animate-pulse-soft" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <span class="font-semibold">Seat release in:</span>
      </div>
      <span class="text-sm font-mono font-bold text-warning-dark">{{ countdownDisplay }}</span>
    </div>

    <!-- Chat Header -->
    <div class="bg-warm-800 px-3.5 py-2.5 flex items-center justify-between border-b border-warm-700">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-full bg-brand-gradient flex items-center justify-center font-bold text-white text-xs shadow-soft">
          <img src="../assets/synapseair-logo.webp" alt="SA" class="w-6 h-6 rounded-full" />
        </div>
        <div>
          <div class="flex items-center gap-1">
            <h4 class="font-bold text-xs text-warm-100">SynapseAir Support</h4>
            <svg class="w-3.5 h-3.5 text-success fill-current" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <p class="text-[10px] text-success">
            {{ isAiTyping ? 'typing...' : 'Verified Support Channel' }}
          </p>
        </div>
      </div>

      <span class="text-[10px] px-2 py-0.5 rounded-lg bg-warm-700 text-warm-300 font-mono">
        Live
      </span>
    </div>

    <!-- Messages Container -->
    <div ref="chatBox" class="flex-1 p-3 overflow-y-auto space-y-2.5 bg-[#F3F1FA] text-xs">
      
      <div class="text-center my-1">
        <span class="text-[10px] text-warm-600 bg-white px-2.5 py-1 rounded-full border border-warm-200 font-mono inline-flex items-center gap-1 shadow-soft">
          🔒 Secure Flight Support Channel
        </span>
      </div>

      <!-- Messages Loop -->
      <div 
        v-for="(msg, idx) in chatMessages" 
        :key="idx"
        :class="msg.isUser ? 'flex justify-end' : 'flex justify-start'">
        
        <div 
          class="max-w-[88%] rounded-2xl p-3 shadow-soft relative"
          :class="msg.isUser ? 'bg-brand-gradient text-white rounded-br-md' : 'bg-white text-warm-800 rounded-bl-md border border-warm-200'">
          
          <div v-if="!msg.isUser" class="text-[10px] font-bold text-brand-purple mb-1">
            SynapseAir Recovery Team
          </div>

          <p class="leading-relaxed text-xs whitespace-pre-line">{{ msg.text }}</p>

          <!-- Flight Comparison Carousel -->
          <div v-if="msg.showCarousel && flightCandidates.length > 0" class="mt-2.5 space-y-2">
            <div class="text-[10px] text-warm-500 font-mono text-center">
              Option {{ candidateIndex + 1 }} of {{ flightCandidates.length }}
            </div>
            <div class="p-2.5 rounded-xl bg-warm-100 border border-warm-200 text-xs space-y-1.5">
              <div class="flex items-center justify-between text-warm-900 font-bold pb-1 border-b border-warm-200">
                <span class="text-brand-purple font-mono">{{ currentCandidate.flight_number }}</span>
                <span class="px-1.5 rounded text-[10px] font-bold"
                  :class="currentCandidate.score >= 0.8 ? 'bg-success-light text-success-dark' : currentCandidate.score >= 0.6 ? 'bg-warning-light text-warning-dark' : 'bg-danger-light text-danger-dark'">
                  {{ Math.round((currentCandidate.score || 0) * 100) }}%
                </span>
              </div>
              <div class="flex items-center justify-between text-warm-700 text-[11px]">
                <span>{{ currentCandidate.origin || props.pnr?.split('-')[1] || '—' }} ➔ {{ currentCandidate.destination || '—' }}</span>
                <span>{{ currentCandidate.departure_time || '—' }}</span>
              </div>
              <div class="flex items-center justify-between text-[10px] text-warm-500">
                <span>{{ currentCandidate.airline || 'Partner Airline' }}</span>
                <span>{{ currentCandidate.cabin_class || 'Business' }}</span>
              </div>
            </div>
            <div class="flex items-center justify-between" v-if="flightCandidates.length > 1">
              <button @click="prevCandidate" class="text-[10px] px-3 py-1.5 rounded-lg bg-white hover:bg-warm-100 text-warm-600 border border-warm-200 transition disabled:opacity-30" :disabled="candidateIndex === 0">◀ Prev</button>
              <button @click="nextCandidate" class="text-[10px] px-3 py-1.5 rounded-lg bg-white hover:bg-warm-100 text-warm-600 border border-warm-200 transition disabled:opacity-30" :disabled="candidateIndex === flightCandidates.length - 1">Next ▶</button>
            </div>
          </div>

          <!-- Rebooking Flight Card Preview -->
          <div v-if="msg.flight && !msg.showCarousel" class="mt-2.5 p-2.5 rounded-xl bg-warm-100 border border-warm-200 text-xs space-y-1.5">
            <div class="flex items-center justify-between text-warm-900 font-bold pb-1 border-b border-warm-200">
              <span class="text-brand-purple font-mono">{{ msg.flight.flight_number }}</span>
              <span class="text-success-dark bg-success-light px-1.5 rounded text-[10px]">
                {{ msg.flight.cabin_class || 'Business' }}
              </span>
            </div>
            <div class="flex items-center justify-between text-warm-700 text-[11px]">
              <span>{{ msg.flight.origin }} ➔ {{ msg.flight.destination }}</span>
              <span>Departure: {{ msg.flight.departure_time }}</span>
            </div>
          </div>

          <!-- Baggage Transfer Confirmation -->
          <div v-if="msg.showBaggage && baggageInformation" class="mt-2 p-2 rounded-xl bg-warm-100 border border-warm-200 text-[10px] space-y-1">
            <div class="flex items-center gap-1 text-brand-blue font-bold">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
              </svg>
              Baggage Transfer
            </div>
            <div class="text-warm-600">
              Checked bags: <span class="text-warm-900 font-semibold">{{ baggageInformation.checked_bags || 0 }}</span>
            </div>
            <div v-if="baggageInformation.special_items" class="text-warm-600">
              Special: <span class="text-brand-purple">{{ baggageInformation.special_items }}</span>
            </div>
            <div class="text-warm-600">
              Interline: <span :class="baggageInformation.interline_eligible ? 'text-success-dark' : 'text-danger-dark'">
                {{ baggageInformation.interline_eligible ? 'Eligible' : 'Not eligible' }}
              </span>
            </div>
            <div v-if="baggageInformation.confirmed" class="text-success-dark font-bold pt-0.5">
              ✓ Baggage transfer confirmed
            </div>
          </div>

          <!-- Compensation Eligibility -->
          <div v-if="msg.showCompensation && compensationInformation" class="mt-2 p-2 rounded-xl bg-warm-100 border border-warm-200 text-[10px] space-y-1">
            <div class="flex items-center gap-1 text-warning-dark font-bold">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Passenger Rights
            </div>
            <div class="text-warm-600">
              Regulation: <span class="text-warm-900 font-semibold">{{ compensationInformation.regulation || 'N/A' }}</span>
            </div>
            <div class="text-warm-600">
              Eligible: <span :class="compensationInformation.eligible ? 'text-success-dark font-bold' : 'text-danger-dark'">
                {{ compensationInformation.eligible ? 'Yes' : 'No' }}
              </span>
            </div>
            <div v-if="compensationInformation.eligible && compensationInformation.amount_usd" class="text-success-dark font-bold">
              Compensation: {{ compensationInformation.currency || 'USD' }} {{ compensationInformation.amount_usd }}
            </div>
          </div>

          <!-- Action Buttons -->
          <div v-if="msg.showActions && !msg.actionResolved" class="mt-3 pt-2 border-t border-warm-200 flex flex-col gap-1.5">
            <button 
              @click="submitDecision('APPROVE', msg)"
              class="w-full py-2 px-3 rounded-xl bg-brand-gradient hover:shadow-glow-purple text-white font-bold text-xs transition shadow-soft-md flex items-center justify-center gap-1 active:scale-[0.98]">
              <span>✓ Accept Rebooking</span>
            </button>
            <button 
              @click="submitDecision('REJECT', msg)"
              class="w-full py-1.5 px-3 rounded-xl bg-white hover:bg-danger-light text-warm-600 border border-warm-200 text-xs transition">
              <span>✕ Decline / Search Other Flights</span>
            </button>
          </div>

          <!-- Stamped Action -->
          <div v-if="msg.actionResolved" class="mt-2 text-[10px] font-mono px-2 py-1 rounded-lg bg-success-light text-success-dark text-center font-bold">
            Response: {{ msg.actionResolved }} ✓
          </div>

          <div class="flex items-center justify-end gap-1 mt-1 text-[9px] text-warm-400 font-mono">
            <span>{{ msg.time }}</span>
            <span v-if="msg.isUser" class="text-brand-cyan">✓✓</span>
          </div>
        </div>

      </div>

      <!-- Typing Bubble -->
      <div v-if="isAiTyping" class="flex justify-start">
        <div class="bg-white rounded-2xl rounded-bl-md p-2.5 px-3 text-brand-purple flex items-center gap-1 shadow-soft border border-warm-200">
          <span class="w-1.5 h-1.5 rounded-full bg-brand-purple animate-bounce"></span>
          <span class="w-1.5 h-1.5 rounded-full bg-brand-blue animate-bounce [animation-delay:0.2s]"></span>
          <span class="w-1.5 h-1.5 rounded-full bg-brand-cyan animate-bounce [animation-delay:0.4s]"></span>
        </div>
      </div>

    </div>

    <!-- Input Bar -->
    <form @submit.prevent="handleUserMessage" class="bg-warm-800 p-2 flex items-center gap-2 border-t border-warm-700 rounded-b-[1.85rem]">
      <input 
        v-model="userQuery"
        type="text" 
        class="flex-1 bg-warm-700 border-none rounded-full px-3.5 py-2 text-xs text-warm-100 placeholder-warm-400 focus:outline-none focus:ring-1 focus:ring-brand-purple" 
        placeholder="Reply 'YES' or ask questions..."
      />
      <button 
        type="submit"
        :disabled="!userQuery.trim() || isAiTyping"
        class="w-9 h-9 sm:w-8 sm:h-8 rounded-full bg-brand-gradient hover:shadow-glow-purple text-white flex items-center justify-center disabled:opacity-40 transition shadow-soft">
        <svg class="w-4 h-4 fill-current ml-0.5" viewBox="0 0 24 24">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
        </svg>
      </button>
    </form>

  </div>
</template>

<script setup>
import { ref, reactive, watch, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { apiClient } from '../services/api'

const props = defineProps({
  hitlStatus: { type: String, default: 'IDLE' },
  isStreaming: { type: Boolean, default: false },
  solution: { type: Object, default: null },
  ticketReceipt: { type: Object, default: null },
  disruptionData: { type: Object, default: () => ({}) },
  passengerName: { type: String, default: 'Traveler' },
  pnr: { type: String, default: 'PNR' },
  candidateRoutes: { type: Array, default: () => [] },
  baggageContext: { type: Object, default: null },
  compensationResult: { type: Object, default: null }
})

const emit = defineEmits(['resolve'])

const currentTime = ref('12:00')
const isAiTyping = ref(false)
const userQuery = ref('')
const chatBox = ref(null)

// ── Countdown Timer ──────────────────────────────────────────────────────
const countdownActive = ref(false)
const countdownSeconds = ref(300)
let countdownInterval = null

const countdownDisplay = computed(() => {
  const m = Math.floor(countdownSeconds.value / 60)
  const s = countdownSeconds.value % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

function startCountdown(seconds = 300) {
  stopCountdown()
  countdownSeconds.value = seconds
  countdownActive.value = true
  countdownInterval = setInterval(() => {
    if (countdownSeconds.value <= 0) { stopCountdown(); return }
    countdownSeconds.value--
  }, 1000)
}

function stopCountdown() {
  if (countdownInterval) { clearInterval(countdownInterval); countdownInterval = null }
  countdownActive.value = false
}

// ── Flight Carousel ──────────────────────────────────────────────────────
const candidateIndex = ref(0)

const flightCandidates = computed(() => {
  if (props.candidateRoutes && props.candidateRoutes.length > 0) return props.candidateRoutes.slice(0, 3)
  if (props.solution) return [props.solution]
  return []
})

const currentCandidate = computed(() => {
  const list = flightCandidates.value
  if (list.length === 0) return {}
  return list[Math.min(candidateIndex.value, list.length - 1)]
})

function nextCandidate() { if (candidateIndex.value < flightCandidates.value.length - 1) candidateIndex.value++ }
function prevCandidate() { if (candidateIndex.value > 0) candidateIndex.value-- }

// ── Baggage & Compensation ───────────────────────────────────────────────
const baggageInformation = computed(() => props.baggageContext)
const compensationInformation = computed(() => props.compensationResult)

// ── Chat Messages ────────────────────────────────────────────────────────
const chatMessages = reactive([
  { isUser: false, text: "SynapseAir Priority Support channel ready.", time: "12:00 PM" }
])

function updateClock() {
  const d = new Date()
  currentTime.value = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function scrollToBottom() {
  nextTick(() => { if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight })
}

// ── Event Watchers: Real-Time WhatsApp Notifications ─────────────────────
const lastTicketNo = ref(null)
const lastBaggageKey = ref(null)
const lastCompKey = ref(null)
const lastHitlStatus = ref(null)

// 1. Initial Disruption Alert
watch(() => props.isStreaming, (streaming) => {
  if (streaming) {
    lastTicketNo.value = null
    lastBaggageKey.value = null
    lastCompKey.value = null
    lastHitlStatus.value = null

    const flight = props.disruptionData?.flight_number || props.pnr || 'Flight'
    const orig = props.disruptionData?.origin || 'SIN'
    const dest = props.disruptionData?.destination || 'KUL'
    const reason = props.disruptionData?.reason || 'Operational disruption'
    const name = props.passengerName || 'Traveler'

    chatMessages.push({
      isUser: false,
      text: `🚨 URGENT FLIGHT ALERT\nDear ${name}, your flight ${flight} (${orig} ➔ ${dest}) was disrupted (${reason}).\n\nSynapseAir AI Swarm is calculating your optimal recovery route right now...`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    scrollToBottom()
  }
})

// 2. Baggage Update
watch(() => props.baggageContext, (bag) => {
  if (bag && lastBaggageKey.value !== JSON.stringify(bag)) {
    lastBaggageKey.value = JSON.stringify(bag)
    chatMessages.push({
      isUser: false,
      text: `🧳 BAGGAGE ROUTING UPDATE\n${bag.checked_bags || 1} checked bag(s) identified. Auto-transfer to recovery connection confirmed at Gate B04.`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    scrollToBottom()
  }
})

// 3. Compensation Rights Update
watch(() => props.compensationResult, (comp) => {
  if (comp && comp.eligible && lastCompKey.value !== JSON.stringify(comp)) {
    lastCompKey.value = JSON.stringify(comp)
    chatMessages.push({
      isUser: false,
      text: `🛡️ PASSENGER RIGHTS COMPENSATION\nUnder ${comp.regulation || 'EU261'}, you are eligible for ${comp.currency || 'USD'} ${comp.amount_usd || 440} compensation. Direct claim recorded.`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    scrollToBottom()
  }
})

// 4. HITL vs Auto-Rebook Notification
watch(() => props.hitlStatus, (newStatus) => {
  if (!newStatus || newStatus === lastHitlStatus.value) return
  lastHitlStatus.value = newStatus

  if (newStatus === 'WAITING_FOR_PASSENGER') {
    startCountdown(300)
    isAiTyping.value = true
    setTimeout(() => {
      isAiTyping.value = false
      const name = props.passengerName || "Traveler"
      const flt = props.solution?.flight_number || "SQ-112"
      const dep = props.solution?.departure_time || "14:30"
      
      chatMessages.push({
        isUser: false,
        text: `Hi ${name}, we found a replacement flight on ${flt} departing at ${dep}. Please tap 'Accept' below to issue your ticket immediately.`,
        flight: props.solution,
        showCarousel: flightCandidates.value.length > 1,
        showActions: true,
        showBaggage: !!baggageInformation.value,
        showCompensation: !!compensationInformation.value,
        actionResolved: null,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      })
      scrollToBottom()
    }, 800)
  } else if (newStatus === 'BYPASSED') {
    stopCountdown()
    const name = props.passengerName || "VIP Traveler"
    const flt = props.solution?.flight_number || "SQ-112"
    const dep = props.solution?.departure_time || "14:30"
    const tier = props.disruptionData?.loyalty_tier || "VIP"

    chatMessages.push({
      isUser: false,
      text: `✨ VIP AUTO-REBOOKING ACTIVATED\nHello ${name}, based on your ${tier} tier status, your seat on ${flt} departing at ${dep} has been automatically secured. Zero airport queues required!`,
      flight: props.solution,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    scrollToBottom()
  } else if (newStatus === 'APPROVED' || newStatus === 'REJECTED') {
    stopCountdown()
  }
})

// 5. Official E-Ticket Issued
watch(() => props.ticketReceipt, (ticket) => {
  if (ticket && ticket.e_ticket_number && lastTicketNo.value !== ticket.e_ticket_number) {
    lastTicketNo.value = ticket.e_ticket_number
    chatMessages.push({
      isUser: false,
      text: `🎟️ OFFICIAL E-TICKET ISSUED\nTicket No: ${ticket.e_ticket_number}\nSeat: ${ticket.assigned_seat || '12A'}\nGate: B04\n\nYour boarding pass is ready. Proceed directly to security!`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    scrollToBottom()
  }
})

function submitDecision(decision, msgObj) {
  stopCountdown()
  if (msgObj) msgObj.actionResolved = decision === 'APPROVE' ? 'APPROVED' : 'DECLINED'

  chatMessages.push({
    isUser: true,
    text: decision === 'APPROVE' ? 'YES, Accept Rebooking' : 'NO, Search Alternatives',
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  })
  scrollToBottom()
  emit('resolve', decision)

  setTimeout(() => {
    if (decision === 'APPROVE') {
      chatMessages.push({
        isUser: false,
        text: `🎉 Confirmed! Your rebooking on ${props.solution?.flight_number || 'flight'} has been ticketed. Baggage transfers automatically.`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      })
    } else {
      chatMessages.push({
        isUser: false,
        text: "Understood. Our team is looking for alternative connections for you.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      })
    }
    scrollToBottom()
  }, 900)
}

async function handleUserMessage() {
  const query = userQuery.value.trim()
  if (!query) return

  chatMessages.push({ isUser: true, text: query, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) })
  userQuery.value = ''
  scrollToBottom()

  if (query.toUpperCase() === 'YES' || query.toUpperCase().includes('APPROV')) { submitDecision('APPROVE', null); return }

  isAiTyping.value = true
  try {
    const data = await apiClient.sendChatMessage({
      passenger_message: query,
      passenger_name: props.passengerName,
      pnr: props.pnr,
      flight_details: props.solution
    })
    isAiTyping.value = false
    chatMessages.push({ isUser: false, text: data.reply || "Your request is noted.", time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) })
    scrollToBottom()
  } catch (e) {
    isAiTyping.value = false
    chatMessages.push({ isUser: false, text: "Yes, baggage transfers automatically and your seat is reserved.", time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) })
    scrollToBottom()
  }
}

onMounted(() => { updateClock(); setInterval(updateClock, 30000) })
onUnmounted(() => { stopCountdown() })
</script>
