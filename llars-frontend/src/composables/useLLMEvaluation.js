/**
 * LLM Evaluation Composable
 *
 * Manages real-time LLM evaluation monitoring via Socket.IO.
 * Provides live progress tracking, result streaming, and agreement metrics.
 *
 * Events:
 *   llm_eval:progress - Real-time progress updates
 *   llm_eval:result - Individual evaluation result
 *   llm_eval:completed - Scenario evaluation completed
 *   llm_eval:error - Evaluation error occurred
 */

import { ref, computed, onMounted, onUnmounted, readonly } from 'vue'
import axios from 'axios'
import { getSocket } from '@/services/socketService'

/**
 * Evaluation status constants
 */
export const EVAL_STATUS = {
  IDLE: 'idle',
  RUNNING: 'running',
  COMPLETED: 'completed',
  ERROR: 'error'
}

/**
 * Task type constants
 */
export const TASK_TYPES = {
  RANKING: 'ranking',
  RATING: 'rating',
  AUTHENTICITY: 'authenticity',
  MAIL_RATING: 'mail_rating',
  COMPARISON: 'comparison',
  TEXT_CLASSIFICATION: 'text_classification'
}

/**
 * LLM Evaluation composable
 * @param {number} scenarioId - Scenario ID to monitor
 * @returns {Object} Evaluation state and methods
 */
export function useLLMEvaluation(scenarioId) {
  // ===== State =====
  const status = ref(EVAL_STATUS.IDLE)
  const progress = ref({
    total: 0,
    completed: 0,
    pending: 0,
    failed: 0,
    percent: 0
  })
  const results = ref([])
  const currentEvaluation = ref(null)
  const agreementMetrics = ref(null)
  const tokenUsage = ref({
    total_tokens: 0,
    total_cost_usd: 0,
    by_model: []
  })
  const error = ref(null)
  const connected = ref(false)

  // ===== Socket Reference =====
  let socket = null

  // ===== Computed =====
  const isRunning = computed(() => status.value === EVAL_STATUS.RUNNING)
  const isCompleted = computed(() => status.value === EVAL_STATUS.COMPLETED)
  const hasError = computed(() => status.value === EVAL_STATUS.ERROR || error.value !== null)

  const progressPercent = computed(() => {
    if (progress.value.total === 0) return 0
    return Math.round((progress.value.completed / progress.value.total) * 100)
  })

  const sortedResults = computed(() => {
    return [...results.value].sort((a, b) => {
      // Sort by timestamp descending (newest first)
      return new Date(b.created_at) - new Date(a.created_at)
    })
  })

  // ===== Socket Event Handlers =====
  function handleProgress(data) {
    if (data.scenario_id !== scenarioId) return

    progress.value = {
      total: data.total || 0,
      completed: data.completed || 0,
      pending: data.pending || 0,
      failed: data.failed || 0,
      percent: data.percent || 0
    }

    if (data.current_evaluation) {
      currentEvaluation.value = data.current_evaluation
    }

    status.value = EVAL_STATUS.RUNNING
  }

  function handleResult(data) {
    if (data.scenario_id !== scenarioId) return

    // Add result to list, replacing if same ID exists
    const existingIndex = results.value.findIndex(r => r.id === data.result.id)
    if (existingIndex >= 0) {
      results.value[existingIndex] = data.result
    } else {
      results.value.push(data.result)
    }

    // Update token usage if provided
    if (data.token_usage) {
      tokenUsage.value = {
        total_tokens: tokenUsage.value.total_tokens + (data.token_usage.total_tokens || 0),
        total_cost_usd: tokenUsage.value.total_cost_usd + (data.token_usage.cost_usd || 0),
        by_model: tokenUsage.value.by_model
      }
    }

    currentEvaluation.value = null
  }

  function handleCompleted(data) {
    if (data.scenario_id !== scenarioId) return

    status.value = EVAL_STATUS.COMPLETED
    currentEvaluation.value = null

    // Update final metrics
    if (data.summary) {
      progress.value = {
        total: data.summary.total || progress.value.total,
        completed: data.summary.completed || progress.value.completed,
        pending: 0,
        failed: data.summary.failed || 0,
        percent: 100
      }
    }

    if (data.agreement_metrics) {
      agreementMetrics.value = data.agreement_metrics
    }
  }

  function handleError(data) {
    if (data.scenario_id !== scenarioId) return

    error.value = data.error || 'Unknown error occurred'
    status.value = EVAL_STATUS.ERROR
    currentEvaluation.value = null
  }

  // ===== Socket Connection =====
  function connect() {
    if (socket && socket.connected) return

    socket = getSocket()

    socket.on('connect', () => {
      connected.value = true
      // Join scenario room
      socket.emit('llm_eval:join_scenario', { scenario_id: scenarioId })
    })

    socket.on('disconnect', () => {
      connected.value = false
    })

    // Register event handlers
    socket.on('llm_eval:progress', handleProgress)
    socket.on('llm_eval:result', handleResult)
    socket.on('llm_eval:completed', handleCompleted)
    socket.on('llm_eval:error', handleError)

    // If already connected, join room immediately
    if (socket.connected) {
      connected.value = true
      socket.emit('llm_eval:join_scenario', { scenario_id: scenarioId })
    }
  }

  function disconnect() {
    if (!socket) return

    // Leave scenario room
    if (socket.connected) {
      socket.emit('llm_eval:leave_scenario', { scenario_id: scenarioId })
    }

    // Remove event handlers
    socket.off('llm_eval:progress', handleProgress)
    socket.off('llm_eval:result', handleResult)
    socket.off('llm_eval:completed', handleCompleted)
    socket.off('llm_eval:error', handleError)
  }

  // ===== API Methods =====
  async function fetchProgress() {
    try {
      const response = await axios.get(`/api/evaluation/llm/${scenarioId}/progress`)
      if (response.data) {
        progress.value = response.data.progress || progress.value
        results.value = response.data.results || []
        agreementMetrics.value = response.data.agreement_metrics || null
        tokenUsage.value = response.data.token_usage || tokenUsage.value

        if (response.data.status) {
          status.value = response.data.status
        }
      }
    } catch (err) {
      console.error('Error fetching LLM evaluation progress:', err)
      error.value = err.response?.data?.error || err.message
    }
  }

  async function fetchResult(resultId) {
    try {
      const response = await axios.get(`/api/evaluation/llm/result/${resultId}`)
      return response.data
    } catch (err) {
      console.error('Error fetching LLM result:', err)
      throw err
    }
  }

  async function fetchAgreementMetrics() {
    try {
      const response = await axios.get(`/api/evaluation/${scenarioId}/agreement-metrics`)
      agreementMetrics.value = response.data
      return response.data
    } catch (err) {
      console.error('Error fetching agreement metrics:', err)
      throw err
    }
  }

  async function startEvaluation(options = {}) {
    try {
      error.value = null
      status.value = EVAL_STATUS.RUNNING

      const response = await axios.post(`/api/evaluation/llm/${scenarioId}/start`, {
        model_id: options.modelId,
        prompt_template_id: options.promptTemplateId,
        ...options
      })

      return response.data
    } catch (err) {
      status.value = EVAL_STATUS.ERROR
      error.value = err.response?.data?.error || err.message
      throw err
    }
  }

  async function stopEvaluation() {
    try {
      const response = await axios.post(`/api/evaluation/llm/${scenarioId}/stop`)
      status.value = EVAL_STATUS.IDLE
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || err.message
      throw err
    }
  }

  // ===== Utility Methods =====
  function clearError() {
    error.value = null
    if (status.value === EVAL_STATUS.ERROR) {
      status.value = EVAL_STATUS.IDLE
    }
  }

  function reset() {
    status.value = EVAL_STATUS.IDLE
    progress.value = { total: 0, completed: 0, pending: 0, failed: 0, percent: 0 }
    results.value = []
    currentEvaluation.value = null
    agreementMetrics.value = null
    tokenUsage.value = { total_tokens: 0, total_cost_usd: 0, by_model: [] }
    error.value = null
  }

  // ===== Lifecycle =====
  onMounted(() => {
    connect()
    fetchProgress()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    // State (readonly)
    status: readonly(status),
    progress: readonly(progress),
    results: readonly(results),
    currentEvaluation: readonly(currentEvaluation),
    agreementMetrics: readonly(agreementMetrics),
    tokenUsage: readonly(tokenUsage),
    error: readonly(error),
    connected: readonly(connected),

    // Computed
    isRunning,
    isCompleted,
    hasError,
    progressPercent,
    sortedResults,

    // Methods
    fetchProgress,
    fetchResult,
    fetchAgreementMetrics,
    startEvaluation,
    stopEvaluation,
    clearError,
    reset,
    connect,
    disconnect
  }
}
