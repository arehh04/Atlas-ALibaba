import { createApp } from 'vue'
import './assets/main.css'
import App from './App.vue'

const app = createApp(App)

// Global error handler for uncaught errors
app.config.errorHandler = (err, instance, info) => {
  console.error('[SynapseAir Global Error]', err, info)
}

// Catch unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('[SynapseAir Unhandled Rejection]', event.reason)
})

app.mount('#app')
