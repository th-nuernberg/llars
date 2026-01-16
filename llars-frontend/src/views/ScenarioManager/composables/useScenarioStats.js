/**
 * Composable for real-time scenario statistics via Socket.IO.
 *
 * Subscribes to scenario stats updates and provides live progress tracking
 * for human evaluators and LLM models.
 *
 * Events:
 *   scenario:stats - Initial stats payload after subscribing
 *   scenario:stats_updated - Real-time stats update
 */

import { ref, computed, onMounted, onUnmounted, watch, readonly } from 'vue'
import axios from 'axios'
import { getSocket } from '@/services/socketService'
import { useAuth } from '@/composables/useAuth'

/**
 * Scenario stats composable for real-time progress monitoring.
 *
 * @param {Ref<number>} scenarioIdRef - Reactive reference to scenario ID
 * @returns {Object} Stats state and methods
 */
export function useScenarioStats(scenarioIdRef) {
  const { getToken } = useAuth()

  // ===== State =====
  const stats = ref(null)
  const raterStats = ref([])
  const evaluatorStats = ref([])
  const llmStats = ref([])
  const humanStats = ref([])
  const agreementMetrics = ref(null)
  const connected = ref(false)
  const loading = ref(false)
  const error = ref(null)
  const functionType = ref(null)

  // ===== Socket Reference =====
  let socket = null
  let currentScenarioId = null

  // ===== Computed =====

  /**
   * Combined stats for all evaluators (human + LLM)
   */
  const allEvaluatorStats = computed(() => {
    const human = evaluatorStats.value.filter(e => !e.is_llm)
    const llm = evaluatorStats.value.filter(e => e.is_llm)
    return [...human, ...llm]
  })

  /**
   * Overall progress percentage
   */
  const overallProgress = computed(() => {
    const allStats = [...raterStats.value, ...evaluatorStats.value]
    if (allStats.length === 0) return 0

    const totalDone = allStats.reduce((sum, s) => sum + (s.done_threads || s.voted_count || 0), 0)
    const totalThreads = allStats.reduce((sum, s) => sum + (s.total_threads || 0), 0)

    if (totalThreads === 0) return 0
    return Math.round((totalDone / totalThreads) * 100)
  })

  /**
   * Human evaluator progress
   */
  const humanProgress = computed(() => {
    const human = [...raterStats.value, ...evaluatorStats.value.filter(e => !e.is_llm)]
    if (human.length === 0) return { done: 0, total: 0, percent: 0 }

    const done = human.reduce((sum, s) => sum + (s.done_threads || s.voted_count || 0), 0)
    const total = human.reduce((sum, s) => sum + (s.total_threads || 0), 0)

    return {
      done,
      total,
      percent: total > 0 ? Math.round((done / total) * 100) : 0
    }
  })

  /**
   * LLM evaluator progress
   */
  const llmProgress = computed(() => {
    const llm = evaluatorStats.value.filter(e => e.is_llm)
    if (llm.length === 0) return { done: 0, total: 0, percent: 0 }

    const done = llm.reduce((sum, s) => sum + (s.done_threads || s.voted_count || 0), 0)
    const total = llm.reduce((sum, s) => sum + (s.total_threads || 0), 0)

    return {
      done,
      total,
      percent: total > 0 ? Math.round((done / total) * 100) : 0
    }
  })

  /**
   * User stats formatted for display
   */
  const userStatsList = computed(() => {
    const result = []

    // Add raters
    for (const rater of raterStats.value) {
      result.push({
        id: rater.user_id || rater.username,
        name: rater.username,
        role: 'RATER',
        isLLM: false,
        completed: rater.done_threads || rater.voted_count || 0,
        total: rater.total_threads || 0,
        inProgress: rater.progressing_threads || 0,
        notStarted: rater.not_started_threads || rater.pending_count || 0,
        accuracy: rater.accuracy_percent,
        progress: rater.progress_percent ?? (rater.total_threads > 0
          ? Math.round(((rater.done_threads || 0) / rater.total_threads) * 100)
          : 0)
      })
    }

    // Add human evaluators
    for (const evaluator of evaluatorStats.value.filter(e => !e.is_llm)) {
      result.push({
        id: evaluator.user_id || evaluator.username,
        name: evaluator.username,
        role: 'EVALUATOR',
        isLLM: false,
        completed: evaluator.done_threads || evaluator.voted_count || 0,
        total: evaluator.total_threads || 0,
        inProgress: evaluator.progressing_threads || 0,
        notStarted: evaluator.not_started_threads || evaluator.pending_count || 0,
        accuracy: evaluator.accuracy_percent,
        progress: evaluator.progress_percent ?? (evaluator.total_threads > 0
          ? Math.round(((evaluator.done_threads || 0) / evaluator.total_threads) * 100)
          : 0)
      })
    }

    // Add LLM evaluators
    for (const llm of evaluatorStats.value.filter(e => e.is_llm)) {
      result.push({
        id: llm.model_id || llm.username,
        name: llm.username,
        role: 'LLM',
        isLLM: true,
        modelId: llm.model_id,
        completed: llm.done_threads || llm.voted_count || 0,
        total: llm.total_threads || 0,
        inProgress: 0,
        notStarted: llm.not_started_threads || llm.pending_count || 0,
        accuracy: llm.accuracy_percent,
        progress: llm.progress_percent ?? (llm.total_threads > 0
          ? Math.round(((llm.done_threads || 0) / llm.total_threads) * 100)
          : 0),
        votedThreads: llm.voted_threads || llm.done_threads_list || [],
        pendingThreads: llm.pending_threads || llm.not_started_threads_list || []
      })
    }

    return result
  })

  // ===== Socket Event Handlers =====

  function handleStats(data) {
    if (data.scenario_id !== currentScenarioId) return
    processStatsPayload(data)
  }

  function handleStatsUpdated(data) {
    if (data.scenario_id !== currentScenarioId) return
    processStatsPayload(data)
  }

  function processStatsPayload(data) {
    functionType.value = data.function_type
    stats.value = data.stats

    if (data.kind === 'authenticity' || data.function_type === 'authenticity') {
      // Authenticity stats have user_stats array
      const userStats = data.stats?.user_stats || []
      raterStats.value = userStats.filter(u => u.role === 'rater' && !u.is_llm)
      evaluatorStats.value = userStats.filter(u => u.role === 'evaluator' || u.is_llm)
      agreementMetrics.value = {
        alpha: data.stats?.krippendorff_alpha,
        interpretation: data.stats?.alpha_interpretation,
        accuracy: data.stats?.overall_accuracy
      }
    } else {
      // Progress stats have rater_stats and evaluator_stats arrays
      raterStats.value = data.stats?.rater_stats || []
      evaluatorStats.value = data.stats?.evaluator_stats || []
    }

    // Separate LLM and human stats
    llmStats.value = evaluatorStats.value.filter(e => e.is_llm)
    humanStats.value = [
      ...raterStats.value,
      ...evaluatorStats.value.filter(e => !e.is_llm)
    ]
  }

  function handleError(data) {
    error.value = data.error || 'Unknown error'
    console.error('[ScenarioStats] Socket error:', data)
  }

  // ===== Socket Connection =====

  function connect(scenarioId) {
    if (!scenarioId) return

    // Disconnect from previous scenario if different
    if (currentScenarioId && currentScenarioId !== scenarioId) {
      disconnect()
    }

    currentScenarioId = scenarioId
    socket = getSocket()

    if (!socket) {
      console.error('[ScenarioStats] Socket not available')
      return
    }

    socket.on('connect', () => {
      connected.value = true
      // Subscribe to scenario stats
      socket.emit('scenario:subscribe', { scenario_id: scenarioId })
    })

    socket.on('disconnect', () => {
      connected.value = false
    })

    // Register event handlers
    socket.on('scenario:stats', handleStats)
    socket.on('scenario:stats_updated', handleStatsUpdated)
    socket.on('scenario:error', handleError)

    // If already connected, subscribe immediately
    if (socket.connected) {
      connected.value = true
      socket.emit('scenario:subscribe', { scenario_id: scenarioId })
    }
  }

  function disconnect() {
    if (!socket) return

    // Unsubscribe from scenario stats
    if (socket.connected && currentScenarioId) {
      socket.emit('scenario:unsubscribe', { scenario_id: currentScenarioId })
    }

    // Remove event handlers
    socket.off('scenario:stats', handleStats)
    socket.off('scenario:stats_updated', handleStatsUpdated)
    socket.off('scenario:error', handleError)

    currentScenarioId = null
  }

  // ===== API Methods =====

  /**
   * Fetch stats via REST API (fallback/initial load)
   */
  async function fetchStats(scenarioId) {
    if (!scenarioId) return

    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`/api/scenarios/${scenarioId}/stats`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      })

      const data = response.data

      // Process response - API returns rater_stats and evaluator_stats directly
      processStatsPayload({
        scenario_id: scenarioId,
        function_type: data.function_type,
        kind: data.kind || 'progress',
        stats: {
          rater_stats: data.rater_stats || [],
          evaluator_stats: data.evaluator_stats || [],
          user_stats: data.user_stats || [],
          krippendorff_alpha: data.agreement_metrics?.alpha,
          overall_accuracy: data.overall_accuracy,
          // Include authenticity stats if present
          vote_distribution: data.vote_distribution
        }
      })

      return data
    } catch (err) {
      // Silently handle 404s for scenarios without data yet
      if (err.response?.status !== 404) {
        error.value = err.response?.data?.error || err.message
        console.error('[ScenarioStats] Error fetching stats:', err)
      }
      // Don't throw - allow UI to show empty state
    } finally {
      loading.value = false
    }
  }

  /**
   * Refresh stats by fetching from API
   */
  async function refresh() {
    if (currentScenarioId) {
      await fetchStats(currentScenarioId)
    }
  }

  // ===== Lifecycle =====

  // Watch for scenario ID changes
  watch(
    () => scenarioIdRef?.value,
    (newId, oldId) => {
      if (newId && newId !== oldId) {
        connect(newId)
        fetchStats(newId)
      }
    },
    { immediate: true }
  )

  onUnmounted(() => {
    disconnect()
  })

  return {
    // Raw stats
    stats: readonly(stats),
    raterStats: readonly(raterStats),
    evaluatorStats: readonly(evaluatorStats),
    llmStats: readonly(llmStats),
    humanStats: readonly(humanStats),
    agreementMetrics: readonly(agreementMetrics),
    functionType: readonly(functionType),

    // Computed
    allEvaluatorStats,
    overallProgress,
    humanProgress,
    llmProgress,
    userStatsList,

    // State
    connected: readonly(connected),
    loading: readonly(loading),
    error: readonly(error),

    // Methods
    connect,
    disconnect,
    fetchStats,
    refresh
  }
}
