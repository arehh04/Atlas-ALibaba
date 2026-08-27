/**
 * useConnection.js — WebSocket / SSE transport layer.
 *
 * Handles bidirectional WebSocket with SSE fallback.
 * Exposes connect/disconnect and an onMessage callback.
 */

import { ref, readonly } from 'vue'
import { getStreamUrl, getWebSocketUrl } from '../services/api'

const connectionMode = ref('none') // 'websocket' | 'sse' | 'none'

let eventSource = null
let webSocket = null

export function useConnection() {

  /**
   * Open a real-time stream for the given thread.
   * @param {string} threadId
   * @param {(data: object) => void} onMessage — called for every parsed JSON event
   * @param {(err: Error) => void} [onError]
   */
  function connect(threadId, onMessage, onError) {
    closeConnections()

    // Primary real-time stream: Server-Sent Events (SSE)
    _openSSE(threadId, onMessage, onError)

    // Secondary bidirectional channel: WebSocket (for HITL consensus)
    try {
      _openWebSocket(threadId, onMessage, onError)
    } catch (e) {
      console.warn('WS initialization skipped:', e)
    }
  }

  function _openWebSocket(threadId, onMessage, onError) {
    const wsUrl = getWebSocketUrl(threadId)
    try {
      webSocket = new WebSocket(wsUrl)

      webSocket.onopen = () => {
        if (connectionMode.value === 'none') connectionMode.value = 'websocket'
      }

      webSocket.onmessage = (event) => {
        try {
          onMessage(JSON.parse(event.data))
        } catch {
          console.warn('Non-JSON WebSocket packet:', event.data)
        }
      }

      webSocket.onerror = (err) => {
        console.warn('WebSocket connection note:', err)
      }

      webSocket.onclose = () => {
        if (connectionMode.value === 'websocket') connectionMode.value = 'sse'
      }
    } catch (e) {
      console.warn('WebSocket init exception:', e)
    }
  }

  function _openSSE(threadId, onMessage, onError) {
    eventSource = new EventSource(getStreamUrl(threadId))
    connectionMode.value = 'sse'

    eventSource.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data))
      } catch {
        console.warn('Non-JSON SSE packet:', event.data)
      }
    }

    eventSource.onerror = (err) => {
      console.warn('SSE stream notice:', err)
      if (onError) onError(err)
    }
  }

  /**
   * Send a JSON payload via WebSocket (no-op if not connected).
   */
  function send(payload) {
    if (webSocket && webSocket.readyState === WebSocket.OPEN) {
      webSocket.send(JSON.stringify(payload))
    }
  }

  function closeConnections() {
    if (eventSource) { eventSource.close(); eventSource = null }
    if (webSocket) { webSocket.close(); webSocket = null }
    connectionMode.value = 'none'
  }

  return {
    connectionMode: readonly(connectionMode),
    connect,
    send,
    closeConnections,
  }
}
