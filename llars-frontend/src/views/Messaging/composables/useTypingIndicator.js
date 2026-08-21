/**
 * Typing indicator composable.
 * Emits typing events with debounce (every 2s), auto-clears after 5s.
 */
import { ref, readonly, computed, onUnmounted } from 'vue'
import socketService from '@/services/socketService'
import { useAuth } from '@/composables/useAuth'

const TYPING_EMIT_INTERVAL = 2000 // ms between emits
const TYPING_TIMEOUT = 5000 // ms before clearing remote typing

export function useTypingIndicator(conversationIdRef) {
  const { tokenParsed } = useAuth()
  const username = computed(() => tokenParsed.value?.preferred_username || '')

  const typingUsers = ref(new Set())
  let lastEmitTime = 0
  const remoteTimers = {}

  // ── Emit typing ─────────────────────────────────────────────────
  const emitTyping = () => {
    const now = Date.now()
    if (now - lastEmitTime < TYPING_EMIT_INTERVAL) return
    lastEmitTime = now

    const socket = socketService.getSocket()
    if (socket?.connected && conversationIdRef.value) {
      socket.emit('messaging:typing', {
        conversation_id: conversationIdRef.value,
        username: username.value,
        is_typing: true,
      })
    }
  }

  const stopTyping = () => {
    const socket = socketService.getSocket()
    if (socket?.connected && conversationIdRef.value) {
      socket.emit('messaging:typing', {
        conversation_id: conversationIdRef.value,
        username: username.value,
        is_typing: false,
      })
    }
    lastEmitTime = 0
  }

  // ── Listen for remote typing ────────────────────────────────────
  const setupListeners = () => {
    const socket = socketService.getSocket()
    if (!socket) return

    socket.on('messaging:typing', (data) => {
      if (data.conversation_id !== conversationIdRef.value) return
      if (data.username === username.value) return

      if (data.is_typing) {
        typingUsers.value.add(data.username)
        // Trigger reactivity
        typingUsers.value = new Set(typingUsers.value)

        // Auto-clear after timeout
        if (remoteTimers[data.username]) clearTimeout(remoteTimers[data.username])
        remoteTimers[data.username] = setTimeout(() => {
          typingUsers.value.delete(data.username)
          typingUsers.value = new Set(typingUsers.value)
          delete remoteTimers[data.username]
        }, TYPING_TIMEOUT)
      } else {
        typingUsers.value.delete(data.username)
        typingUsers.value = new Set(typingUsers.value)
        if (remoteTimers[data.username]) {
          clearTimeout(remoteTimers[data.username])
          delete remoteTimers[data.username]
        }
      }
    })
  }

  const cleanupListeners = () => {
    const socket = socketService.getSocket()
    if (socket) socket.off('messaging:typing')
    Object.values(remoteTimers).forEach(clearTimeout)
  }

  onUnmounted(() => {
    stopTyping()
    cleanupListeners()
  })

  return {
    typingUsers: readonly(typingUsers),
    emitTyping,
    stopTyping,
    setupListeners,
    cleanupListeners,
  }
}
