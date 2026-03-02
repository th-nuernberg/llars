/**
 * Active chat composable.
 * Manages messages for the currently active conversation, send/receive, pagination.
 */
import { ref, readonly, watch, computed } from 'vue'
import axios from 'axios'
import socketService from '@/services/socketService'
import { useAuth } from '@/composables/useAuth'

export function useChat(conversationIdRef) {
  const { tokenParsed } = useAuth()
  const username = computed(() => tokenParsed.value?.preferred_username || '')

  const messages = ref([])
  const isLoading = ref(false)
  const hasMore = ref(true)
  const PAGE_SIZE = 50

  // ── Fetch Messages ──────────────────────────────────────────────
  const fetchMessages = async (beforeId = null) => {
    const convId = conversationIdRef.value
    if (!convId) return

    isLoading.value = true
    try {
      const params = { limit: PAGE_SIZE }
      if (beforeId) params.before_id = beforeId

      const { data } = await axios.get(
        `/api/messaging/conversations/${convId}/messages`,
        { params }
      )
      const fetched = data.messages || []
      hasMore.value = fetched.length >= PAGE_SIZE

      if (beforeId) {
        messages.value = [...fetched, ...messages.value]
      } else {
        messages.value = fetched
      }
    } catch (err) {
      console.error('[Chat] Failed to fetch messages:', err)
    } finally {
      isLoading.value = false
    }
  }

  const loadMore = async () => {
    if (!hasMore.value || isLoading.value || messages.value.length === 0) return
    const oldestId = messages.value[0]?.id
    await fetchMessages(oldestId)
  }

  // ── Send Message ────────────────────────────────────────────────
  const sendMessage = async (content, options = {}) => {
    const convId = conversationIdRef.value
    if (!convId || !content?.trim()) return null

    const socket = socketService.getSocket()
    if (socket?.connected) {
      socket.emit('messaging:send', {
        conversation_id: convId,
        sender: username.value,
        content: content.trim(),
        message_type: options.messageType || 'text',
        reply_to_id: options.replyToId || null,
        encryption_metadata: options.encryptionMetadata || null,
      })
      return true
    }

    // REST fallback
    try {
      const { data } = await axios.post(
        `/api/messaging/conversations/${convId}/messages`,
        {
          content: content.trim(),
          message_type: options.messageType || 'text',
          reply_to_id: options.replyToId || null,
          encryption_metadata: options.encryptionMetadata || null,
        }
      )
      messages.value.push(data.message)
      return data.message
    } catch (err) {
      console.error('[Chat] Failed to send message:', err)
      return null
    }
  }

  // ── Edit / Delete ───────────────────────────────────────────────
  const editMessage = async (messageId, newContent) => {
    const socket = socketService.getSocket()
    if (socket?.connected) {
      socket.emit('messaging:edit', {
        message_id: messageId,
        username: username.value,
        content: newContent,
      })
      return true
    }

    try {
      await axios.put(`/api/messaging/messages/${messageId}`, {
        content: newContent,
      })
      const idx = messages.value.findIndex((m) => m.id === messageId)
      if (idx >= 0) {
        messages.value[idx].content = newContent
        messages.value[idx].is_edited = true
      }
      return true
    } catch (err) {
      console.error('[Chat] Failed to edit message:', err)
      return false
    }
  }

  const deleteMessage = async (messageId) => {
    const convId = conversationIdRef.value
    const socket = socketService.getSocket()
    if (socket?.connected) {
      socket.emit('messaging:delete', {
        message_id: messageId,
        username: username.value,
        conversation_id: convId,
      })
      return true
    }

    try {
      await axios.delete(`/api/messaging/messages/${messageId}`)
      const idx = messages.value.findIndex((m) => m.id === messageId)
      if (idx >= 0) {
        messages.value[idx].is_deleted = true
        messages.value[idx].content = null
      }
      return true
    } catch (err) {
      console.error('[Chat] Failed to delete message:', err)
      return false
    }
  }

  // ── Reactions ─────────────────────────────────────────────────
  const toggleReaction = (messageId, emoji) => {
    const socket = socketService.getSocket()
    if (socket?.connected) {
      socket.emit('messaging:react', {
        message_id: messageId,
        username: username.value,
        emoji,
      })
    }
  }

  // ── Mark as Read ────────────────────────────────────────────────
  const markAsRead = async () => {
    const convId = conversationIdRef.value
    if (!convId || messages.value.length === 0) return

    const lastMsg = messages.value[messages.value.length - 1]
    const socket = socketService.getSocket()
    if (socket?.connected) {
      socket.emit('messaging:read', {
        conversation_id: convId,
        username: username.value,
        up_to_message_id: lastMsg.id,
      })
    } else {
      try {
        await axios.post(`/api/messaging/conversations/${convId}/read`, {
          up_to_message_id: lastMsg.id,
        })
      } catch (err) {
        console.error('[Chat] Failed to mark as read:', err)
      }
    }
  }

  // ── Socket Listeners ────────────────────────────────────────────
  const setupSocketListeners = () => {
    const socket = socketService.getSocket()
    if (!socket) return

    socket.on('messaging:new_message', (msg) => {
      if (msg.conversation_id === conversationIdRef.value) {
        // Avoid duplicates
        if (!messages.value.find((m) => m.id === msg.id)) {
          messages.value.push(msg)
        }
      }
    })

    socket.on('messaging:message_edited', (data) => {
      if (data.conversation_id === conversationIdRef.value) {
        const idx = messages.value.findIndex((m) => m.id === data.message_id)
        if (idx >= 0) {
          messages.value[idx].content = data.content
          messages.value[idx].is_edited = true
          messages.value[idx].edited_at = data.edited_at
        }
      }
    })

    socket.on('messaging:message_deleted', (data) => {
      if (data.conversation_id === conversationIdRef.value) {
        const idx = messages.value.findIndex((m) => m.id === data.message_id)
        if (idx >= 0) {
          messages.value[idx].is_deleted = true
          messages.value[idx].content = null
        }
      }
    })

    socket.on('messaging:reaction_updated', (data) => {
      const idx = messages.value.findIndex((m) => m.id === data.message_id)
      if (idx >= 0) {
        messages.value[idx].reactions = data.reactions
      }
    })
  }

  const cleanupSocketListeners = () => {
    const socket = socketService.getSocket()
    if (socket) {
      socket.off('messaging:new_message')
      socket.off('messaging:message_edited')
      socket.off('messaging:message_deleted')
      socket.off('messaging:reaction_updated')
    }
  }

  // ── Watch conversation changes ──────────────────────────────────
  watch(conversationIdRef, (newId) => {
    messages.value = []
    hasMore.value = true
    if (newId) {
      fetchMessages()
      const socket = socketService.getSocket()
      if (socket) {
        socket.emit('messaging:join_chat', { conversation_id: newId })
      }
    }
  })

  // Initial load if conversationIdRef already has a value (singleton state from previous visit)
  if (conversationIdRef.value) {
    fetchMessages()
  }

  return {
    messages: readonly(messages),
    isLoading: readonly(isLoading),
    hasMore: readonly(hasMore),
    fetchMessages,
    loadMore,
    sendMessage,
    editMessage,
    deleteMessage,
    toggleReaction,
    markAsRead,
    setupSocketListeners,
    cleanupSocketListeners,
  }
}
