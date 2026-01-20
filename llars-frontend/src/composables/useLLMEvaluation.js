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
  LABELING: 'labeling',
  TEXT_CLASSIFICATION: 'text_classification' // legacy alias
}

/**
 * LLM Evaluation composable
 * @param {number} [initialScenarioId] - Optional initial scenario ID to monitor
 * @returns {Object} Evaluation state and methods
 */
export function useLLMEvaluation(initialScenarioId = null) {
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

  // ===== Internal State =====
  let scenarioId = initialScenarioId

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

  // ===== Backend Task Event Handlers =====
  function handleTaskStarted(data) {
    if (data.scenario_id !== scenarioId) return

    status.value = EVAL_STATUS.RUNNING
    currentEvaluation.value = {
      model_id: data.model_id,
      thread_id: data.thread_id,
      status: 'running'
    }
  }

  function handleTaskCompleted(data) {
    if (data.scenario_id !== scenarioId) return

    // Update progress
    progress.value.completed += 1
    progress.value.percent = progress.value.total > 0
      ? Math.round((progress.value.completed / progress.value.total) * 100)
      : 0

    // Add result to list
    const result = {
      id: `${data.model_id}-${data.thread_id}`,
      model_id: data.model_id,
      thread_id: data.thread_id,
      task_type: data.task_type,
      status: 'completed',
      result: data.result,
      meta: data.meta,
      created_at: new Date().toISOString()
    }
    results.value.push(result)

    // Update token usage if provided
    if (data.meta) {
      tokenUsage.value.total_tokens += data.meta.tokens_used || 0
      tokenUsage.value.total_cost_usd += data.meta.cost_usd || 0
    }

    currentEvaluation.value = null
  }

  function handleTaskFailed(data) {
    if (data.scenario_id !== scenarioId) return

    // Update progress
    progress.value.failed = (progress.value.failed || 0) + 1

    // Add error result to list
    const result = {
      id: `${data.model_id}-${data.thread_id}`,
      model_id: data.model_id,
      thread_id: data.thread_id,
      task_type: data.task_type,
      status: 'failed',
      error: data.error,
      created_at: new Date().toISOString()
    }
    results.value.push(result)

    currentEvaluation.value = null
  }

  function handleScenarioCompleted(data) {
    if (data.scenario_id !== scenarioId) return

    status.value = EVAL_STATUS.COMPLETED
    currentEvaluation.value = null

    // Update final metrics from summary
    if (data.summary) {
      progress.value = {
        total: data.summary.total || progress.value.total,
        completed: data.summary.completed || progress.value.completed,
        pending: 0,
        failed: data.summary.failed || 0,
        percent: 100
      }
    }
  }

  // ===== Socket Connection =====
  function connect() {
    if (!scenarioId) return
    if (socket && socket.connected) return

    socket = getSocket()

    socket.on('connect', () => {
      connected.value = true
      // Join scenario room
      if (scenarioId) {
        socket.emit('llm_eval:join_scenario', { scenario_id: scenarioId })
      }
    })

    socket.on('disconnect', () => {
      connected.value = false
    })

    // Register event handlers (legacy names for backwards compatibility)
    socket.on('llm_eval:progress', handleProgress)
    socket.on('llm_eval:result', handleResult)
    socket.on('llm_eval:completed', handleCompleted)
    socket.on('llm_eval:error', handleError)

    // Register handlers for actual backend events
    socket.on('llm_eval:task_started', handleTaskStarted)
    socket.on('llm_eval:task_completed', handleTaskCompleted)
    socket.on('llm_eval:task_failed', handleTaskFailed)
    socket.on('llm_eval:scenario_completed', handleScenarioCompleted)

    // If already connected, join room immediately
    if (socket.connected) {
      connected.value = true
      if (scenarioId) {
        socket.emit('llm_eval:join_scenario', { scenario_id: scenarioId })
      }
    }
  }

  /**
   * Connect to a specific scenario for live evaluation updates
   * @param {number} newScenarioId - Scenario ID to connect to
   */
  async function connectToScenario(newScenarioId) {
    if (!newScenarioId) return

    // Disconnect from previous scenario if different
    if (scenarioId && scenarioId !== newScenarioId) {
      disconnect()
    }

    scenarioId = newScenarioId
    reset()
    connect()

    // Fetch initial data in parallel
    await Promise.all([
      fetchProgress(),
      fetchAgreementMetrics()
    ])
  }

  function disconnect() {
    if (!socket) return

    // Leave scenario room
    if (socket.connected && scenarioId) {
      socket.emit('llm_eval:leave_scenario', { scenario_id: scenarioId })
    }

    // Remove event handlers
    socket.off('llm_eval:progress', handleProgress)
    socket.off('llm_eval:result', handleResult)
    socket.off('llm_eval:completed', handleCompleted)
    socket.off('llm_eval:error', handleError)

    // Remove handlers for backend events
    socket.off('llm_eval:task_started', handleTaskStarted)
    socket.off('llm_eval:task_completed', handleTaskCompleted)
    socket.off('llm_eval:task_failed', handleTaskFailed)
    socket.off('llm_eval:scenario_completed', handleScenarioCompleted)
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
    if (!scenarioId) {
      console.warn('Cannot fetch agreement metrics: no scenarioId')
      return null
    }
    try {
      const response = await axios.get(`/api/evaluation/${scenarioId}/agreement-metrics`)
      const data = response.data

      // Transform API response to expected flat format
      const metrics = data.metrics || {}
      agreementMetrics.value = {
        // Core agreement metrics
        alpha: metrics.krippendorff_alpha?.value ?? null,
        kappa: metrics.cohens_kappa?.value ?? null,
        fleiss: metrics.fleiss_kappa?.value ?? null,
        kendall: metrics.kendall_tau?.value ?? null,
        spearman: metrics.spearman_rho?.value ?? null,
        accuracy: metrics.percent_agreement?.value ?? null,
        // New metrics
        icc: metrics.icc?.value ?? null,
        kendallW: metrics.kendall_w?.value ?? null,
        mae: metrics.mae?.value ?? null,
        rmse: metrics.rmse?.value ?? null,
        macroF1: metrics.macro_f1?.value ?? null,
        microF1: metrics.micro_f1?.value ?? null,
        // Interpretations
        interpretation: metrics.krippendorff_alpha?.interpretation ||
                       metrics.fleiss_kappa?.interpretation ||
                       metrics.cohens_kappa?.interpretation || null,
        iccInterpretation: metrics.icc?.interpretation ?? null,
        kendallWInterpretation: metrics.kendall_w?.interpretation ?? null,
        // Metadata
        raterCount: data.rater_count || 0,
        itemCount: data.item_count || 0,
        raters: data.raters || [],
        taskType: data.task_type || null,
        metricDescriptions: data.metric_descriptions || {}
      }
      return agreementMetrics.value
    } catch (err) {
      console.error('Error fetching agreement metrics:', err)
      // Don't throw - just return null to allow UI to handle gracefully
      return null
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
    // Only auto-connect if initialScenarioId was provided
    if (initialScenarioId) {
      connect()
      fetchProgress()
    }
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
    connectToScenario,
    disconnect
  }
}
