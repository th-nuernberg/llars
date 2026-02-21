/**
 * useEvaluationSession - Generic Evaluation Session Management
 *
 * Manages evaluation sessions for all evaluation types (rating, ranking,
 * comparison, etc.). Provides navigation, progress tracking, and Socket.IO
 * integration for real-time updates.
 *
 * Features:
 *   - Load evaluation items from scenario
 *   - Navigate between items (next/previous)
 *   - Track progress (completed/total)
 *   - Socket.IO real-time updates
 *   - Persist evaluation results
 *
 * Usage:
 *   const { items, currentItem, progress, goNext, goPrev, submitEvaluation }
 *     = useEvaluationSession(scenarioId, functionType)
 */

import { ref, computed, onMounted, onUnmounted, readonly } from 'vue'
import axios from 'axios'
import { getSocket } from '@/services/socketService'

export const SESSION_STATUS = {
  LOADING: 'loading',
  READY: 'ready',
  SUBMITTING: 'submitting',
  COMPLETED: 'completed',
  ERROR: 'error'
}

// Map function_type_id to function type name
const FUNCTION_TYPE_MAP = {
  1: 'ranking',
  2: 'rating',
  3: 'mail_rating',
  4: 'comparison',
  5: 'authenticity',
  7: 'labeling'
}

/**
 * Generic evaluation session composable
 * @param {number} scenarioId - Scenario ID
 * @param {string} functionType - Evaluation type (optional, derived from scenario if not provided)
 * @returns {Object} Session state and methods
 */
export function useEvaluationSession(scenarioId, functionType = null) {
  // ===== State =====
  const status = ref(SESSION_STATUS.LOADING)
  const items = ref([])
  const currentIndex = ref(0)
  const scenario = ref(null)
  const config = ref(null)
  const error = ref(null)

  // Progress tracking
  const progress = ref({
    total: 0,
    completed: 0,
    remaining: 0
  })

  // Socket.IO connection state
  const connected = ref(false)
  let socket = null

  // ===== Computed =====

  const currentItem = computed(() => {
    if (items.value.length === 0 || currentIndex.value < 0) return null
    return items.value[currentIndex.value] || null
  })

  const hasNext = computed(() => {
    return currentIndex.value < items.value.length - 1
  })

  const hasPrev = computed(() => {
    return currentIndex.value > 0
  })

  const progressPercent = computed(() => {
    if (progress.value.total === 0) return 0
    return Math.round((progress.value.completed / progress.value.total) * 100)
  })

  const isComplete = computed(() => {
    return progress.value.completed >= progress.value.total && progress.value.total > 0
  })

  const isLoading = computed(() => status.value === SESSION_STATUS.LOADING)
  const isReady = computed(() => status.value === SESSION_STATUS.READY)

  // ===== Navigation =====

  function goToItem(index) {
    if (index < 0 || index >= items.value.length) return false
    currentIndex.value = index
    return true
  }

  function goNext() {
    if (!hasNext.value) return false
    currentIndex.value++
    return true
  }

  function goPrev() {
    if (!hasPrev.value) return false
    currentIndex.value--
    return true
  }

  function goToFirstIncomplete() {
    const index = items.value.findIndex(item => !item.evaluated)
    if (index >= 0) {
      currentIndex.value = index
      return true
    }
    return false
  }

  function goToItemById(itemId) {
    if (!itemId) return false
    const id = Number(itemId)
    const index = items.value.findIndex(item =>
      item.id === id || item.thread_id === id || item.item_id === id
    )
    if (index >= 0) {
      currentIndex.value = index
      return true
    }
    return false
  }

  // ===== API Methods =====

  /**
   * Load session data from backend
   */
  async function loadSession() {
    if (!scenarioId) {
      error.value = 'No scenario ID provided'
      status.value = SESSION_STATUS.ERROR
      return
    }

    status.value = SESSION_STATUS.LOADING
    error.value = null

    try {
      const response = await axios.get(`/api/evaluation/session/${scenarioId}`)
      const data = response.data

      scenario.value = data.scenario
      config.value = data.config
      items.value = data.items || []

      // Update progress
      progress.value = {
        total: items.value.length,
        completed: items.value.filter(i => i.evaluated).length,
        remaining: items.value.filter(i => !i.evaluated).length
      }

      // Go to first incomplete item
      if (!goToFirstIncomplete() && items.value.length > 0) {
        currentIndex.value = 0
      }

      status.value = SESSION_STATUS.READY
    } catch (err) {
      console.error('Failed to load evaluation session:', err)
      error.value = err.response?.data?.error || err.message
      status.value = SESSION_STATUS.ERROR
    }
  }

  /**
   * Submit an evaluation result
   * @param {number} itemId - Item being evaluated (thread_id, feature_id, etc.)
   * @param {Object} evaluationData - The evaluation data to submit
   * @returns {Promise<Object>} Result of submission
   */
  async function submitEvaluation(itemId, evaluationData) {
    if (!itemId || !evaluationData) {
      throw new Error('Item ID and evaluation data are required')
    }

    status.value = SESSION_STATUS.SUBMITTING

    try {
      // Get function type from parameter or from loaded scenario
      const effectiveFunctionType = functionType ||
        FUNCTION_TYPE_MAP[scenario.value?.function_type_id] ||
        'rating'

      const response = await axios.post(
        `/api/evaluation/session/${scenarioId}/items/${itemId}/evaluate`,
        {
          function_type: effectiveFunctionType,
          ...evaluationData
        }
      )

      // Update local item state
      const itemIndex = items.value.findIndex(
        i => i.id === itemId || i.thread_id === itemId || i.feature_id === itemId
      )
      if (itemIndex >= 0) {
        items.value[itemIndex].evaluated = true
        items.value[itemIndex].evaluation = response.data.evaluation
      }

      // Update progress
      progress.value.completed = items.value.filter(i => i.evaluated).length
      progress.value.remaining = items.value.filter(i => !i.evaluated).length

      status.value = SESSION_STATUS.READY

      // Check if session is complete
      if (isComplete.value) {
        status.value = SESSION_STATUS.COMPLETED
      }

      return response.data
    } catch (err) {
      console.error('Failed to submit evaluation:', err)
      error.value = err.response?.data?.error || err.message
      status.value = SESSION_STATUS.READY
      throw err
    }
  }

  // ===== Socket.IO Integration =====

  function setupSocket() {
    if (!scenarioId) return

    socket = getSocket()

    socket.on('connect', () => {
      connected.value = true
      socket.emit('evaluation:join_session', { scenario_id: scenarioId })
    })

    socket.on('disconnect', () => {
      connected.value = false
    })

    // Listen for evaluation updates from other users
    socket.on('evaluation:item_evaluated', handleItemEvaluated)
    socket.on('evaluation:progress_update', handleProgressUpdate)

    // If already connected, join immediately
    if (socket.connected) {
      connected.value = true
      socket.emit('evaluation:join_session', { scenario_id: scenarioId })
    }
  }

  function handleItemEvaluated(data) {
    if (data.scenario_id !== scenarioId) return

    // Update item if evaluated by another user (for collaborative scenarios)
    const itemIndex = items.value.findIndex(i =>
      i.id === data.item_id || i.thread_id === data.item_id
    )
    if (itemIndex >= 0) {
      // Only update evaluation_count or other metadata, not overwrite user's own evaluation
      if (data.evaluation_count !== undefined) {
        items.value[itemIndex].evaluation_count = data.evaluation_count
      }
    }
  }

  function handleProgressUpdate(data) {
    if (data.scenario_id !== scenarioId) return

    // Update overall progress from server
    if (data.progress) {
      // Keep local completed count for current user
      const localCompleted = items.value.filter(i => i.evaluated).length
      progress.value = {
        ...progress.value,
        total: data.progress.total || progress.value.total,
        completed: localCompleted
      }
    }
  }

  function disconnectSocket() {
    if (!socket) return

    if (socket.connected && scenarioId) {
      socket.emit('evaluation:leave_session', { scenario_id: scenarioId })
    }

    socket.off('evaluation:item_evaluated', handleItemEvaluated)
    socket.off('evaluation:progress_update', handleProgressUpdate)
  }

  // ===== Utility Methods =====

  function clearError() {
    error.value = null
    if (status.value === SESSION_STATUS.ERROR) {
      status.value = SESSION_STATUS.READY
    }
  }

  function reset() {
    status.value = SESSION_STATUS.LOADING
    items.value = []
    currentIndex.value = 0
    scenario.value = null
    config.value = null
    progress.value = { total: 0, completed: 0, remaining: 0 }
    error.value = null
  }

  /**
   * Mark an item as completed and update progress
   * @param {number} itemId - The item ID to mark as completed
   */
  function markItemCompleted(itemId) {
    if (!itemId) return

    const id = Number(itemId)
    const itemIndex = items.value.findIndex(item =>
      item.id === id || item.thread_id === id || item.item_id === id
    )

    if (itemIndex >= 0 && !items.value[itemIndex].evaluated) {
      // Replace the item to ensure reactivity
      items.value = items.value.map((item, idx) =>
        idx === itemIndex
          ? { ...item, evaluated: true, status: 'Done' }
          : item
      )

      // Update progress (force new object for reactivity)
      const completed = items.value.filter(i => i.evaluated).length
      progress.value = {
        total: items.value.length,
        completed,
        remaining: items.value.length - completed
      }
    }
  }

  // ===== Lifecycle =====

  onMounted(() => {
    loadSession()
    setupSocket()
  })

  onUnmounted(() => {
    disconnectSocket()
  })

  return {
    // State (readonly for safety)
    status: readonly(status),
    items: readonly(items),
    scenario: readonly(scenario),
    config: readonly(config),
    error: readonly(error),
    progress: readonly(progress),
    connected: readonly(connected),

    // Computed
    currentItem,
    currentIndex: readonly(currentIndex),
    hasNext,
    hasPrev,
    progressPercent,
    isComplete,
    isLoading,
    isReady,

    // Navigation
    goToItem,
    goToItemById,
    goNext,
    goPrev,
    goToFirstIncomplete,

    // Actions
    loadSession,
    submitEvaluation,
    markItemCompleted,
    clearError,
    reset
  }
}
