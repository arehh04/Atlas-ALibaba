const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const API_TOKEN = import.meta.env.VITE_API_TOKEN || '';

export const getStreamUrl = (threadId) => `${API_BASE_URL}/stream/${threadId}`;

/**
 * Build standard headers with auth token when configured.
 */
function authHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (API_TOKEN) headers['Authorization'] = `Bearer ${API_TOKEN}`;
  return headers;
}

/**
 * Convert HTTP base URL to WebSocket URL for bidirectional communication.
 */
export const getWebSocketUrl = (threadId) => {
  const wsBase = API_BASE_URL.replace(/^http/, 'ws');
  return `${wsBase}/ws/${threadId}`;
};

export const apiClient = {
  async getSystemStatus() {
    const res = await fetch(`${API_BASE_URL}/api/system/status`);
    if (!res.ok) throw new Error('Failed to fetch system status');
    return res.json();
  },

  async triggerDisruption(payload, generatedId) {
    const res = await fetch(`${API_BASE_URL}/webhook/disruption`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        ...payload,
        thread_id: generatedId
      })
    });
    if (!res.ok) throw new Error('Failed to trigger disruption');
    return res.json();
  },

  async resolveConsensus(threadId, decision) {
    const res = await fetch(`${API_BASE_URL}/webhook/consensus`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        thread_id: threadId,
        action: decision,
        notes: `Passenger consensus: ${decision} via WhatsApp`
      })
    });
    if (!res.ok) throw new Error('Failed to post consensus');
    return res.json();
  },

  /**
   * Fetch paginated disruption history with optional filters.
   */
  async getHistory({ limit = 50, offset = 0, loyalty_tier, flight_number } = {}) {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (loyalty_tier) params.set('loyalty_tier', loyalty_tier);
    if (flight_number) params.set('flight_number', flight_number);
    const res = await fetch(`${API_BASE_URL}/api/history?${params}`);
    if (!res.ok) throw new Error('Failed to fetch history');
    return res.json();
  },

  /**
   * Fetch aggregate analytics (avg resolution time, HITL rate, etc.).
   */
  async getStats() {
    const res = await fetch(`${API_BASE_URL}/api/history/stats`);
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
  },

  /**
   * Fetch full detail for a single disruption run.
   */
  async getDisruptionDetail(threadId) {
    const res = await fetch(`${API_BASE_URL}/api/history/${threadId}`);
    if (!res.ok) throw new Error('Failed to fetch disruption detail');
    return res.json();
  },

  /**
   * Send a conversational message to the n8n-powered AI assistant.
   */
  async sendChatMessage({ passenger_message, passenger_name, pnr, flight_details }) {
    const res = await fetch(`${API_BASE_URL}/api/n8n/chat`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ passenger_message, passenger_name, pnr, flight_details })
    });
    if (!res.ok) throw new Error('Failed to send chat message');
    return res.json();
  }
};
