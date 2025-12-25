/**
 * useSystemHealth - Composable for System Health Socket.IO subscriptions
 *
 * Manages connections to host, api, and websocket metrics streams.
 */

import { ref, onBeforeUnmount } from 'vue'
import { io } from 'socket.io-client'
import { useAuth } from '@/composables/useAuth'

const SOCKET_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin
const NAMESPACE = '/admin'

// Shared socket instance (same as docker monitor)
let socket = null
let socketRefCount = 0

function getSocket() {
  if (socket && socket.connected) {
    socketRefCount++
    return socket
  }

  const auth = useAuth()
  const token = auth.getToken()

  socket = io(`${SOCKET_URL}${NAMESPACE}`, {
    transports: ['polling', 'websocket'],
    query: { token },
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
  })

  socketRefCount = 1
  return socket
}

function releaseSocket() {
  socketRefCount--
  if (socketRefCount <= 0 && socket) {
    socket.disconnect()
    socket = null
    socketRefCount = 0
  }
}

/**
 * Host Metrics Subscription
 */
export function useHostMetrics() {
  const connected = ref(false)
  const loading = ref(true)
  const error = ref(null)
  const data = ref(null)

  // History for charts
  const cpuHistory = ref([])
  const memoryHistory = ref([])
  const networkHistory = ref([])
  const MAX_HISTORY = 60

  let sock = null

  function connect() {
    sock = getSocket()

    sock.on('connect', () => {
      connected.value = true
      error.value = null
      sock.emit('host:subscribe', {})
    })

    sock.on('disconnect', () => {
      connected.value = false
    })

    sock.on('host:subscribed', () => {
      loading.value = false
    })

    sock.on('host:stats', (snapshot) => {
      data.value = snapshot
      loading.value = false

      // Update history
      if (snapshot.ok) {
        cpuHistory.value.push(snapshot.cpu?.percent ?? 0)
        if (cpuHistory.value.length > MAX_HISTORY) cpuHistory.value.shift()

        memoryHistory.value.push(snapshot.memory?.ram?.percent ?? 0)
        if (memoryHistory.value.length > MAX_HISTORY) memoryHistory.value.shift()

        const netRate = (snapshot.network?.rates?.bytes_recv_sec ?? 0) +
                        (snapshot.network?.rates?.bytes_sent_sec ?? 0)
        networkHistory.value.push(netRate / 1024) // KB/s
        if (networkHistory.value.length > MAX_HISTORY) networkHistory.value.shift()
      }
    })

    sock.on('health:error', (err) => {
      error.value = err.message
    })

    if (sock.connected) {
      connected.value = true
      sock.emit('host:subscribe', {})
    }
  }

  function disconnect() {
    if (sock) {
      sock.emit('host:unsubscribe', {})
      sock.off('host:subscribed')
      sock.off('host:stats')
      releaseSocket()
      sock = null
    }
  }

  onBeforeUnmount(() => {
    disconnect()
  })

  return {
    connected,
    loading,
    error,
    data,
    cpuHistory,
    memoryHistory,
    networkHistory,
    connect,
    disconnect,
  }
}

/**
 * API Performance Metrics Subscription
 */
export function useApiMetrics() {
  const connected = ref(false)
  const loading = ref(true)
  const error = ref(null)
  const data = ref(null)

  // History for charts
  const requestRateHistory = ref([])
  const latencyHistory = ref([])
  const errorRateHistory = ref([])
  const MAX_HISTORY = 60

  let sock = null

  function connect(window = '5min') {
    sock = getSocket()

    sock.on('connect', () => {
      connected.value = true
      error.value = null
      sock.emit('api:subscribe', { window })
    })

    sock.on('disconnect', () => {
      connected.value = false
    })

    sock.on('api:subscribed', () => {
      loading.value = false
    })

    sock.on('api:stats', (snapshot) => {
      data.value = snapshot
      loading.value = false

      // Update history from stats
      if (snapshot.ok && snapshot.stats) {
        requestRateHistory.value.push(snapshot.stats.requests_per_sec ?? 0)
        if (requestRateHistory.value.length > MAX_HISTORY) requestRateHistory.value.shift()

        latencyHistory.value.push(snapshot.stats.avg_latency_ms ?? 0)
        if (latencyHistory.value.length > MAX_HISTORY) latencyHistory.value.shift()

        errorRateHistory.value.push(snapshot.stats.error_rate ?? 0)
        if (errorRateHistory.value.length > MAX_HISTORY) errorRateHistory.value.shift()
      }
    })

    sock.on('health:error', (err) => {
      error.value = err.message
    })

    if (sock.connected) {
      connected.value = true
      sock.emit('api:subscribe', { window })
    }
  }

  function disconnect() {
    if (sock) {
      sock.emit('api:unsubscribe', {})
      sock.off('api:subscribed')
      sock.off('api:stats')
      releaseSocket()
      sock = null
    }
  }

  onBeforeUnmount(() => {
    disconnect()
  })

  return {
    connected,
    loading,
    error,
    data,
    requestRateHistory,
    latencyHistory,
    errorRateHistory,
    connect,
    disconnect,
  }
}

/**
 * WebSocket Metrics Subscription
 */
export function useWebSocketMetrics() {
  const connected = ref(false)
  const loading = ref(true)
  const error = ref(null)
  const data = ref(null)

  // History for charts
  const connectionHistory = ref([])
  const messageInHistory = ref([])
  const messageOutHistory = ref([])
  const MAX_HISTORY = 60

  let sock = null

  function connect() {
    sock = getSocket()

    sock.on('connect', () => {
      connected.value = true
      error.value = null
      sock.emit('ws:subscribe', {})
    })

    sock.on('disconnect', () => {
      connected.value = false
    })

    sock.on('ws:subscribed', () => {
      loading.value = false
    })

    sock.on('ws:stats', (snapshot) => {
      data.value = snapshot
      loading.value = false

      // Update history
      if (snapshot.ok) {
        connectionHistory.value.push(snapshot.total_connections ?? 0)
        if (connectionHistory.value.length > MAX_HISTORY) connectionHistory.value.shift()

        messageInHistory.value.push(snapshot.rates?.messages_in_per_sec ?? 0)
        if (messageInHistory.value.length > MAX_HISTORY) messageInHistory.value.shift()

        messageOutHistory.value.push(snapshot.rates?.messages_out_per_sec ?? 0)
        if (messageOutHistory.value.length > MAX_HISTORY) messageOutHistory.value.shift()
      }
    })

    sock.on('health:error', (err) => {
      error.value = err.message
    })

    if (sock.connected) {
      connected.value = true
      sock.emit('ws:subscribe', {})
    }
  }

  function disconnect() {
    if (sock) {
      sock.emit('ws:unsubscribe', {})
      sock.off('ws:subscribed')
      sock.off('ws:stats')
      releaseSocket()
      sock = null
    }
  }

  onBeforeUnmount(() => {
    disconnect()
  })

  return {
    connected,
    loading,
    error,
    data,
    connectionHistory,
    messageInHistory,
    messageOutHistory,
    connect,
    disconnect,
  }
}
