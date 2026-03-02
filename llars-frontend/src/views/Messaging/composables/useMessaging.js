/**
 * Central messaging state composable.
 * Manages conversations list, active chat, total unread, and socket connection.
 */
import { ref, computed, readonly } from 'vue'
import axios from 'axios'
import socketService from '@/services/socketService'
import { useAuth } from '@/composables/useAuth'

// ── Shared singleton state ──────────────────────────────────────────
const conversations = ref([])
const activeConversationId = ref(null)
const totalUnread = ref(0)
const perConversationUnread = ref({})
const isLoading = ref(false)
const isInitialized = ref(false)

export function useMessaging() {
  const { tokenParsed } = useAuth()
  const username = computed(() => tokenParsed.value?.preferred_username || '')

  // ── Computed ─────────────────────────────────────────────────────
  const activeConversation = computed(() =>
    conversations.value.find((c) => c.id === activeConversationId.value) || null
  )

  const sortedConversations = computed(() =>
    [...conversations.value].sort((a, b) => {
      const dateA = a.last_message_at ? new Date(a.last_message_at) : new Date(a.created_at)
      const dateB = b.last_message_at ? new Date(b.last_message_at) : new Date(b.created_at)
      return dateB - dateA
    })
  )

  // ── API Methods ─────────────────────────────────────────────────
  const fetchConversations = async () => {
    isLoading.value = true
    try {
      const { data } = await axios.get('/api/messaging/conversations')
      conversations.value = data.conversations || []
    } catch (err) {
      console.error('[Messaging] Failed to fetch conversations:', err)
    } finally {
      isLoading.value = false
    }
  }

  const fetchUnreadCounts = async () => {
    try {
      const { data } = await axios.get('/api/messaging/unread')
      totalUnread.value = data.total || 0
      perConversationUnread.value = data.per_conversation || {}
    } catch (err) {
      console.error('[Messaging] Failed to fetch unread counts:', err)
    }
  }

  const setActiveConversation = (conversationId) => {
    activeConversationId.value = conversationId
  }

  const createDirectChat = async (otherUsername) => {
    const { data } = await axios.post('/api/messaging/conversations/direct', {
      username: otherUsername,
    })
    const conv = data.conversation
    // Add to list if not already there
    if (!conversations.value.find((c) => c.id === conv.id)) {
      conversations.value.unshift(conv)
    }
    return conv
  }

  const createGroupChat = async (name, members, description = null) => {
    const { data } = await axios.post('/api/messaging/conversations/group', {
      name,
      members,
      description,
    })
    const conv = data.conversation
    conversations.value.unshift(conv)
    return conv
  }

  // ── Socket.IO Setup ─────────────────────────────────────────────
  const initSocket = () => {
    if (isInitialized.value) return
    isInitialized.value = true

    const socket = socketService.getSocket()
    if (!socket) return

    // Join all messaging rooms
    socket.emit('messaging:join', { username: username.value })

    // Listen for unread updates
    socket.on('messaging:unread_update', (data) => {
      totalUnread.value = data.total || 0
      perConversationUnread.value = data.per_conversation || {}
    })

    // Listen for new messages to update conversation list
    socket.on('messaging:new_message', (msg) => {
      const convIndex = conversations.value.findIndex((c) => c.id === msg.conversation_id)
      if (convIndex >= 0) {
        const conv = conversations.value[convIndex]
        conv.last_message_at = msg.created_at
        conv.last_message_preview = msg.is_encrypted
          ? '[Encrypted]'
          : (msg.content || '').substring(0, 200)

        // Move to top
        conversations.value.splice(convIndex, 1)
        conversations.value.unshift(conv)
      }
    })

    // Member events
    socket.on('messaging:member_added', () => fetchConversations())
    socket.on('messaging:member_removed', () => fetchConversations())
  }

  const cleanup = () => {
    const socket = socketService.getSocket()
    if (socket) {
      socket.off('messaging:unread_update')
      socket.off('messaging:new_message')
      socket.off('messaging:member_added')
      socket.off('messaging:member_removed')
    }
    isInitialized.value = false
  }

  // ── Update conversation in list ──────────────────────────────────
  const updateConversationInList = (updatedConv) => {
    const idx = conversations.value.findIndex((c) => c.id === updatedConv.id)
    if (idx >= 0) {
      conversations.value[idx] = { ...conversations.value[idx], ...updatedConv }
    }
  }

  return {
    // State
    conversations: readonly(conversations),
    sortedConversations,
    activeConversationId: readonly(activeConversationId),
    activeConversation,
    totalUnread: readonly(totalUnread),
    perConversationUnread: readonly(perConversationUnread),
    isLoading: readonly(isLoading),

    // Methods
    fetchConversations,
    fetchUnreadCounts,
    setActiveConversation,
    createDirectChat,
    createGroupChat,
    updateConversationInList,
    initSocket,
    cleanup,
  }
}
