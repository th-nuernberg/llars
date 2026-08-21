/**
 * useAnonymizationPipeline Composable
 *
 * State management and Socket.IO integration for the anonymization pipeline.
 * Provides real-time NER progress updates via WebSocket rooms.
 *
 * @module composables/useAnonymizationPipeline
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSnackbar } from '@/composables/useSnackbar'
import { getSocket } from '@/services/socketService'
import axios from 'axios'

/**
 * Conversation statuses
 */
export const CONVERSATION_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  ERROR: 'error'
}

/**
 * Composable for managing anonymization pipeline with live Socket.IO updates.
 *
 * @param {Object} [options] - Configuration options
 * @param {boolean} [options.autoJoinOverview=true] - Auto-join overview room on mount
 * @param {number} [options.watchConversationId=null] - Conversation ID to watch
 * @returns {Object} Anonymization pipeline state and actions
 */
export function useAnonymizationPipeline(options = {}) {
  const { autoJoinOverview = true, watchConversationId = null } = options

  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------

  const conversations = ref([])
  const totalConversations = ref(0)
  const loading = ref(false)
  const availableModels = ref([])
  const availableCourses = ref([])
  const hasConversationsWithoutModel = ref(false)
  const statusCounts = ref({ pending: 0, in_progress: 0, completed: 0, error: 0 })

  /** NER progress tracking per conversation: { [convId]: { percent, message_number, total_messages, entities_found } } */
  const nerProgress = ref({})

  /** Active batch progress: { completed, failed, total, percent } or null */
  const batchProgress = ref(null)

  let socketConnectHandler = null
  const { showSuccess, showError } = useSnackbar()

  // ---------------------------------------------------------------------------
  // COMPUTED
  // ---------------------------------------------------------------------------

  const activeNerJobs = computed(() =>
    Object.keys(nerProgress.value).map(Number)
  )

  const isBatchRunning = computed(() =>
    batchProgress.value !== null && batchProgress.value.percent < 100
  )

  // ---------------------------------------------------------------------------
  // ACTIONS
  // ---------------------------------------------------------------------------

  async function loadConversations(params = {}) {
    loading.value = true
    try {
      const response = await axios.get('/api/anonymization/conversations', { params })
      conversations.value = response.data.conversations
      totalConversations.value = response.data.total
      availableModels.value = Array.isArray(response.data.available_models) ? response.data.available_models : []
      availableCourses.value = Array.isArray(response.data.available_courses) ? response.data.available_courses : []
      hasConversationsWithoutModel.value = Boolean(response.data.has_conversations_without_model)
      if (response.data.status_counts) statusCounts.value = response.data.status_counts
    } catch (err) {
      showError('Failed to load conversations')
      console.error('[useAnonymizationPipeline] loadConversations error:', err)
    } finally {
      loading.value = false
    }
  }

  async function runNer(conversationId, { force = false } = {}) {
    try {
      const response = await axios.post(`/api/anonymization/conversations/${conversationId}/run-ner`, { force })
      if (response.data.started) {
        nerProgress.value = {
          ...nerProgress.value,
          [conversationId]: { percent: 0, message_number: 0, total_messages: 0, entities_found: 0 }
        }
        _updateConversationStatus(conversationId, CONVERSATION_STATUS.IN_PROGRESS)
      }
      return response.data
    } catch (err) {
      showError(err.response?.data?.error || 'NER processing failed')
      console.error('[useAnonymizationPipeline] runNer error:', err)
      return null
    }
  }

  async function batchRunNer({ conversationIds = null, force = false } = {}) {
    try {
      const payload = { force }
      if (conversationIds) payload.conversation_ids = conversationIds
      const response = await axios.post('/api/anonymization/batch-ner', payload)
      if (response.data.started) {
        batchProgress.value = { completed: 0, failed: 0, total: response.data.count, percent: 0 }
        for (const id of response.data.conversation_ids) {
          nerProgress.value = {
            ...nerProgress.value,
            [id]: { percent: 0, message_number: 0, total_messages: 0, entities_found: 0 }
          }
          _updateConversationStatus(id, CONVERSATION_STATUS.IN_PROGRESS)
        }
      }
      return response.data
    } catch (err) {
      showError(err.response?.data?.error || 'Batch NER failed')
      console.error('[useAnonymizationPipeline] batchRunNer error:', err)
      return null
    }
  }

  async function importConversations(file, { runNer = false } = {}) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('run_ner', String(runNer))

    try {
      const response = await axios.post('/api/anonymization/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      showSuccess(`Imported ${response.data.imported_count} conversation(s)`)
      if (response.data.failed_count > 0) {
        showError(`${response.data.failed_count} conversation(s) could not be imported`)
      }

      if (response.data.ner_started) {
        const ids = response.data.conversations.map(c => c.id)
        batchProgress.value = { completed: 0, failed: 0, total: ids.length, percent: 0 }
        for (const id of ids) {
          nerProgress.value = {
            ...nerProgress.value,
            [id]: { percent: 0, message_number: 0, total_messages: 0, entities_found: 0 }
          }
        }
      }

      return response.data
    } catch (err) {
      showError(err.response?.data?.error || 'Import failed')
      console.error('[useAnonymizationPipeline] import error:', err)
      return null
    }
  }

  function isNerRunning(conversationId) {
    return conversationId in nerProgress.value
  }

  function getNerProgress(conversationId) {
    return nerProgress.value[conversationId] || null
  }

  // ---------------------------------------------------------------------------
  // SOCKET.IO INTEGRATION
  // ---------------------------------------------------------------------------

  function setupSocketListeners() {
    const socket = getSocket()
    if (!socket) return

    if (autoJoinOverview) {
      socketConnectHandler = () => {
        socket.emit('anonymization:join_overview')
      }
      if (socket.connected) {
        socketConnectHandler()
      }
      socket.on('connect', socketConnectHandler)
    }

    if (watchConversationId) {
      const joinConv = () => {
        socket.emit('anonymization:join_conversation', { conversation_id: watchConversationId })
      }
      if (socket.connected) joinConv()
      socket.on('connect', joinConv)
    }

    // Batch events
    socket.on('anonymization:batch:started', (data) => {
      batchProgress.value = { completed: 0, failed: 0, total: data.total, percent: 0 }
    })

    socket.on('anonymization:batch:progress', (data) => {
      batchProgress.value = {
        completed: data.completed,
        failed: data.failed,
        total: data.total,
        percent: data.percent
      }
    })

    socket.on('anonymization:batch:completed', (data) => {
      batchProgress.value = {
        completed: data.completed,
        failed: data.failed,
        total: data.total,
        percent: 100
      }
      if (data.failed > 0) {
        showError(`NER batch: ${data.failed} conversation(s) failed`)
      } else {
        showSuccess(`NER completed for ${data.completed} conversation(s)`)
      }
      // Clear batch progress after short delay
      setTimeout(() => { batchProgress.value = null }, 3000)
    })

    // Conversation-level events
    socket.on('anonymization:conversation:ner_started', (data) => {
      nerProgress.value = {
        ...nerProgress.value,
        [data.conversation_id]: {
          percent: 0,
          message_number: 0,
          total_messages: data.total_messages,
          entities_found: 0
        }
      }
      _updateConversationStatus(data.conversation_id, CONVERSATION_STATUS.IN_PROGRESS)
    })

    socket.on('anonymization:conversation:ner_progress', (data) => {
      nerProgress.value = {
        ...nerProgress.value,
        [data.conversation_id]: {
          percent: data.percent,
          message_number: data.message_number,
          total_messages: data.total_messages,
          entities_found: data.entities_found || 0
        }
      }
    })

    socket.on('anonymization:conversation:ner_completed', (data) => {
      // Remove from progress tracking
      const next = { ...nerProgress.value }
      delete next[data.conversation_id]
      nerProgress.value = next

      // Update conversation in list
      _updateConversationInList(data.conversation_id, {
        status: data.status,
        entity_count: data.entity_count,
        message_count: data.message_count
      })
    })

    socket.on('anonymization:conversation:ner_failed', (data) => {
      const next = { ...nerProgress.value }
      delete next[data.conversation_id]
      nerProgress.value = next

      _updateConversationStatus(data.conversation_id, CONVERSATION_STATUS.ERROR)
      showError(`NER failed for conversation: ${data.error}`)
    })
  }

  function removeSocketListeners() {
    const socket = getSocket()
    if (!socket) return

    if (socketConnectHandler) {
      socket.emit('anonymization:leave_overview')
      socket.off('connect', socketConnectHandler)
      socketConnectHandler = null
    }

    if (watchConversationId) {
      socket.emit('anonymization:leave_conversation', { conversation_id: watchConversationId })
    }

    socket.off('anonymization:batch:started')
    socket.off('anonymization:batch:progress')
    socket.off('anonymization:batch:completed')
    socket.off('anonymization:conversation:ner_started')
    socket.off('anonymization:conversation:ner_progress')
    socket.off('anonymization:conversation:ner_completed')
    socket.off('anonymization:conversation:ner_failed')
  }

  // ---------------------------------------------------------------------------
  // HELPERS
  // ---------------------------------------------------------------------------

  function _updateConversationStatus(conversationId, status) {
    const conv = conversations.value.find(c => c.id === conversationId)
    if (conv) conv.status = status
  }

  function _updateConversationInList(conversationId, updates) {
    const conv = conversations.value.find(c => c.id === conversationId)
    if (conv) {
      Object.assign(conv, updates)
    }
  }

  // ---------------------------------------------------------------------------
  // LIFECYCLE
  // ---------------------------------------------------------------------------

  onMounted(() => {
    setupSocketListeners()
  })

  onUnmounted(() => {
    removeSocketListeners()
  })

  // ---------------------------------------------------------------------------
  // RETURN
  // ---------------------------------------------------------------------------

  return {
    // State
    conversations,
    totalConversations,
    loading,
    availableModels,
    availableCourses,
    hasConversationsWithoutModel,
    statusCounts,
    nerProgress,
    batchProgress,

    // Computed
    activeNerJobs,
    isBatchRunning,

    // Actions
    loadConversations,
    runNer,
    batchRunNer,
    importConversations,
    isNerRunning,
    getNerProgress,

    // Constants
    CONVERSATION_STATUS
  }
}

export default useAnonymizationPipeline
