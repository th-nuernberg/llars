import { onUnmounted } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { getSocket } from '@/services/socketService'

export function usePresenceHeartbeat(options = {}) {
  const auth = useAuth()
  const heartbeatMs = Number(options.heartbeatMs || 30000)
  const activityThrottleMs = Number(options.activityThrottleMs || 5000)

  let socket = null
  let heartbeatTimer = null
  let lastActivitySent = 0
  let started = false

  const sendHeartbeat = () => {
    if (socket?.connected) {
      socket.emit('presence:heartbeat', {})
    }
  }

  const sendActivity = () => {
    if (socket?.connected) {
      socket.emit('presence:activity', {})
    }
  }

  const onActivity = () => {
    const now = Date.now()
    if (now - lastActivitySent < activityThrottleMs) return
    lastActivitySent = now
    sendActivity()
  }

  const onVisibilityChange = () => {
    if (document.visibilityState === 'visible') {
      onActivity()
      sendHeartbeat()
    }
  }

  const onConnect = () => {
    sendHeartbeat()
    sendActivity()
  }

  const start = () => {
    if (started || !auth.isAuthenticated.value) return
    started = true

    socket = getSocket()
    if (!socket) return

    socket.on('connect', onConnect)
    sendHeartbeat()
    sendActivity()

    if (typeof window !== 'undefined') {
      heartbeatTimer = window.setInterval(sendHeartbeat, heartbeatMs)
      window.addEventListener('keydown', onActivity, true)
      window.addEventListener('pointerdown', onActivity, true)
      window.addEventListener('scroll', onActivity, true)
    }
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', onVisibilityChange)
    }
  }

  const stop = () => {
    if (!started) return
    started = false

    if (heartbeatTimer) {
      window.clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }

    if (typeof window !== 'undefined') {
      window.removeEventListener('keydown', onActivity, true)
      window.removeEventListener('pointerdown', onActivity, true)
      window.removeEventListener('scroll', onActivity, true)
    }
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }

    if (socket) {
      socket.off('connect', onConnect)
    }
    socket = null
  }

  onUnmounted(stop)

  return { start, stop }
}
