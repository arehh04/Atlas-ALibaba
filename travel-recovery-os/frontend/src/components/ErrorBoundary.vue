<template>
  <div v-if="error" class="ops-card p-6 border-danger/30 bg-danger-light/30">
    <div class="flex items-start gap-3">
      <div class="w-10 h-10 rounded-xl bg-danger-light border border-danger/20 flex items-center justify-center shrink-0">
        <svg class="w-5 h-5 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <h3 class="font-display font-semibold text-sm text-danger-dark mb-1">
          {{ fallbackTitle }}
        </h3>
        <p class="text-xs text-warm-600 mb-3">
          {{ errorMessage }}
        </p>
        <button
          @click="resetError"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-warm-50 text-warm-700 border border-warm-200 text-xs font-medium transition"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182"/>
          </svg>
          Try Again
        </button>
      </div>
    </div>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured, computed } from 'vue'

const props = defineProps({
  fallbackTitle: { type: String, default: 'Something went wrong' },
  fallbackMessage: { type: String, default: '' }
})

const error = ref(null)

const errorMessage = computed(() => {
  if (props.fallbackMessage) return props.fallbackMessage
  if (error.value?.message) return error.value.message
  return 'An unexpected error occurred in this component.'
})

onErrorCaptured((err, instance, info) => {
  error.value = err
  console.error('[ErrorBoundary]', err, info)
  return false // prevent propagation
})

function resetError() {
  error.value = null
}
</script>
