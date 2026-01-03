/**
 * useChatSocket.js
 * Composable for managing Socket.IO connection and chat streaming
 */
import { ref, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import { AUTH_STORAGE_KEYS, clearAuthStorage, getAuthStorageItem } from '@/utils/authStorage'

export function useChatSocket() {
  const socket = ref(null)
  const isConnected = ref(false)

  /**
   * Initialize Socket.IO connection
   */
  function initSocket() {
    if (socket.value) return // Already initialized

    const rawBase = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : '')
    const trimmedBase = String(rawBase || '').replace(/\/+$/, '')
    const baseUrl = trimmedBase.endsWith('/api')
      ? trimmedBase.slice(0, -4)
      : (trimmedBase || (typeof window !== 'undefined' ? window.location.origin : ''))
    const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true'
    const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling']

    socket.value = io(baseUrl, {
      path: '/socket.io/',
      transports: socketioTransports,
      upgrade: socketioEnableWebsocket
    })

    socket.value.on('connect', () => {
      console.log('ChatSocket: Connected')
      isConnected.value = true
    })

    socket.value.on('disconnect', () => {
      console.log('ChatSocket: Disconnected')
      isConnected.value = false
    })
  }

  /**
   * Disconnect Socket.IO connection
   */
  function disconnectSocket() {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
      isConnected.value = false
    }
  }

  /**
   * Send a chat message via Socket.IO
   */
  function sendMessage(chatbotId, message, sessionId, conversationId) {
    if (!socket.value?.connected) {
      console.warn('Socket not connected, cannot send message')
      return false
    }

    socket.value.emit('chatbot:stream', {
      chatbot_id: chatbotId,
      message,
      session_id: sessionId,
      conversation_id: conversationId,
      username: null,
      token: getAuthStorageItem(AUTH_STORAGE_KEYS.token)
    })
    return true
  }

  /**
   * Register event handlers for chat streaming
   * @param {Object} handlers - Event handler functions
   */
  function registerHandlers(handlers) {
    if (!socket.value) return

    const {
      onSources,
      onResponse,
      onComplete,
      onAgentStatus,
      onTitleGenerating,
      onTitleDelta,
      onTitleComplete,
      onError
    } = handlers

    // Sources are sent BEFORE streaming
    if (onSources) {
      socket.value.on('chatbot:sources', onSources)
    }

    // Streaming response chunks
    if (onResponse) {
      socket.value.on('chatbot:response', onResponse)
    }

    // Completion metadata
    if (onComplete) {
      socket.value.on('chatbot:complete', onComplete)
    }

    // Agent status updates (for ACT, ReAct, ReflAct modes)
    if (onAgentStatus) {
      socket.value.on('chatbot:agent_status', onAgentStatus)
    }

    // Title streaming events
    if (onTitleGenerating) {
      socket.value.on('chatbot:title_generating', onTitleGenerating)
    }

    if (onTitleDelta) {
      socket.value.on('chatbot:title_delta', onTitleDelta)
    }

    if (onTitleComplete) {
      socket.value.on('chatbot:title_complete', onTitleComplete)
    }

    // Error handling
    if (onError) {
      socket.value.on('chatbot:error', (data) => {
        const errMsg = String(data?.error || '')
        console.error('Chatbot error:', errMsg)

        const code = String(data?.code || '')
        const lower = errMsg.toLowerCase()
        const isAuthError = (
          code.startsWith('AUTH_') ||
          lower.includes('authentication required') ||
          lower.includes('authentication failed') ||
          lower.includes('jwt expired')
        )

        if (isAuthError) {
          clearAuthStorage()
          try {
            localStorage.removeItem('username')
          } catch {}

          const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
          window.location.href = `/login?redirect=${encodeURIComponent(current)}`
          return
        }

        onError(data)
      })
    }
  }

  /**
   * Unregister all event handlers
   */
  function unregisterHandlers() {
    if (!socket.value) return

    const events = [
      'chatbot:sources',
      'chatbot:response',
      'chatbot:complete',
      'chatbot:agent_status',
      'chatbot:title_generating',
      'chatbot:title_delta',
      'chatbot:title_complete',
      'chatbot:error'
    ]

    events.forEach(event => {
      socket.value.off(event)
    })
  }

  // Cleanup on unmount
  onUnmounted(() => {
    disconnectSocket()
  })

  return {
    // State
    socket,
    isConnected,

    // Connection management
    initSocket,
    disconnectSocket,

    // Messaging
    sendMessage,

    // Event handling
    registerHandlers,
    unregisterHandlers
  }
}
