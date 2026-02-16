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

// Module-level subscription generation counter.
// Prevents race condition where old composable's onUnmounted fires AFTER
// new composable's connect(), canceling the new subscription on the shared socket.
let subscriptionGeneration = 0

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
  let mySubscriptionGeneration = 0

  // ===== Polling Fallback =====
  // Periodic REST API refresh to catch missed socket events
  let pollingInterval = null
  const POLLING_INTERVAL_MS = 15000 // 15 seconds
  let lastSocketUpdate = 0 // Timestamp of last socket-based update

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
   * Whether there are any human evaluators
   */
  const hasHumans = computed(() => {
    const human = [...raterStats.value, ...evaluatorStats.value.filter(e => !e.is_llm)]
    return human.length > 0
  })

  /**
   * Whether there are any LLM evaluators
   */
  const hasLLMs = computed(() => {
    return evaluatorStats.value.some(e => e.is_llm)
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
        role: 'EVALUATOR',
        isLLM: false,
        completed: rater.done_threads || rater.voted_count || 0,
        total: rater.total_threads || 0,
        inProgress: rater.progressing_threads || 0,
        notStarted: rater.not_started_threads || rater.pending_count || 0,
        accuracy: rater.accuracy_percent,
        f1Score: rater.f1_score_percent,
        progress: rater.progress_percent ?? (rater.total_threads > 0
          ? Math.round(((rater.done_threads || 0) / rater.total_threads) * 100)
          : 0),
        // Confusion matrix data
        fake_correct: rater.fake_correct,
        fake_incorrect: rater.fake_incorrect,
        real_correct: rater.real_correct,
        real_incorrect: rater.real_incorrect,
        votedThreads: rater.voted_threads || [],
        pendingThreads: rater.pending_threads || []
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
        f1Score: evaluator.f1_score_percent,
        progress: evaluator.progress_percent ?? (evaluator.total_threads > 0
          ? Math.round(((evaluator.done_threads || 0) / evaluator.total_threads) * 100)
          : 0),
        // Confusion matrix data
        fake_correct: evaluator.fake_correct,
        fake_incorrect: evaluator.fake_incorrect,
        real_correct: evaluator.real_correct,
        real_incorrect: evaluator.real_incorrect,
        votedThreads: evaluator.voted_threads || [],
        pendingThreads: evaluator.pending_threads || []
      })
    }

    // Add LLM evaluators
    for (const llm of evaluatorStats.value.filter(e => e.is_llm)) {
      // Extract model_id, cleaning any "llm:" prefix from user_id if model_id not present
      const rawModelId = llm.model_id || (llm.user_id?.startsWith('llm:') ? llm.user_id.slice(4) : null)
      const modelId = rawModelId || llm.username

      result.push({
        id: modelId,
        name: llm.username || modelId,
        username: llm.username,
        role: 'LLM',
        isLLM: true,
        modelId: modelId,
        model_id: modelId, // Keep snake_case for compatibility
        user_id: llm.user_id,
        completed: llm.done_threads || llm.voted_count || 0,
        total: llm.total_threads || 0,
        inProgress: 0,
        notStarted: llm.not_started_threads || llm.pending_count || 0,
        accuracy: llm.accuracy_percent,
        f1Score: llm.f1_score_percent,
        progress: llm.progress_percent ?? (llm.total_threads > 0
          ? Math.round(((llm.done_threads || llm.voted_count || 0) / llm.total_threads) * 100)
          : 0),
        // Confusion matrix data
        fake_correct: llm.fake_correct,
        fake_incorrect: llm.fake_incorrect,
        real_correct: llm.real_correct,
        real_incorrect: llm.real_incorrect,
        votedThreads: llm.voted_threads || llm.done_threads_list || [],
        pendingThreads: llm.pending_threads || llm.not_started_threads_list || []
      })
    }

    return result
  })

  // ===== Socket Event Handlers =====

  function handleStats(data) {
    console.log('[ScenarioStats] Received initial stats event:', {
      receivedScenarioId: data.scenario_id,
      currentScenarioId,
      match: data.scenario_id === currentScenarioId
    })
    if (data.scenario_id !== currentScenarioId) {
      console.warn('[ScenarioStats] Initial stats - Scenario ID mismatch, ignoring')
      return
    }
    lastSocketUpdate = Date.now()
    processStatsPayload(data)
  }

  function handleStatsUpdated(data) {
    console.log('[ScenarioStats] Received stats_updated event:', {
      receivedScenarioId: data.scenario_id,
      currentScenarioId,
      match: data.scenario_id === currentScenarioId,
      typeOfReceived: typeof data.scenario_id,
      typeOfCurrent: typeof currentScenarioId
    })
    if (data.scenario_id !== currentScenarioId) {
      console.warn('[ScenarioStats] Scenario ID mismatch, ignoring update')
      return
    }
    console.log('[ScenarioStats] Processing payload with evaluator_stats:', data.stats?.evaluator_stats?.length || 0)
    lastSocketUpdate = Date.now()
    processStatsPayload(data)
  }

  function processStatsPayload(data) {
    console.log('[ScenarioStats] processStatsPayload called with function_type:', data.function_type)
    functionType.value = data.function_type
    stats.value = data.stats

    if (data.kind === 'authenticity' || data.function_type === 'authenticity') {
      // Authenticity stats have user_stats array
      const userStats = data.stats?.user_stats || []
      // Note: Backend returns role as 'Evaluator'/'Viewer' (capitalized), so use case-insensitive comparison
      // EVALUATOR can interact (rate/evaluate), VIEWER is read-only
      raterStats.value = userStats.filter(u => u.role?.toLowerCase() === 'evaluator' && !u.is_llm)
      evaluatorStats.value = userStats.filter(u => u.role?.toLowerCase() === 'viewer' || u.is_llm)

      // Calculate overall F1 Score from all evaluators
      let totalFakeCorrect = 0
      let totalFakeIncorrect = 0
      let totalRealIncorrect = 0
      for (const user of userStats) {
        totalFakeCorrect += user.fake_correct || 0
        totalFakeIncorrect += user.fake_incorrect || 0
        totalRealIncorrect += user.real_incorrect || 0
      }
      const precision = (totalFakeCorrect + totalFakeIncorrect) > 0
        ? totalFakeCorrect / (totalFakeCorrect + totalFakeIncorrect)
        : 0
      const recall = (totalFakeCorrect + totalRealIncorrect) > 0
        ? totalFakeCorrect / (totalFakeCorrect + totalRealIncorrect)
        : 0
      const overallF1 = (precision + recall) > 0
        ? Math.round(2 * precision * recall / (precision + recall) * 1000) / 10
        : null

      agreementMetrics.value = {
        alpha: data.stats?.krippendorff_alpha,
        interpretation: data.stats?.alpha_interpretation,
        accuracy: data.stats?.overall_accuracy,
        f1Score: overallF1
      }
    } else {
      // Progress stats have rater_stats and evaluator_stats arrays
      raterStats.value = data.stats?.rater_stats || []
      evaluatorStats.value = data.stats?.evaluator_stats || []
      // Also extract agreement metrics for ranking/rating scenarios
      if (data.stats?.krippendorff_alpha !== undefined || data.stats?.alpha_interpretation) {
        agreementMetrics.value = {
          alpha: data.stats?.krippendorff_alpha,
          interpretation: data.stats?.alpha_interpretation,
          accuracy: null
        }
      }
    }

    // Separate LLM and human stats
    llmStats.value = evaluatorStats.value.filter(e => e.is_llm)
    humanStats.value = [
      ...raterStats.value,
      ...evaluatorStats.value.filter(e => !e.is_llm)
    ]

    console.log('[ScenarioStats] After processing - LLM stats:', llmStats.value.map(s => ({
      model_id: s.model_id,
      done_threads: s.done_threads,
      total_threads: s.total_threads
    })))
  }

  function handleError(data) {
    error.value = data.error || 'Unknown error'
    console.error('[ScenarioStats] Socket error:', data)
  }

  // ===== Polling Fallback Functions =====

  function startPolling() {
    stopPolling()
    pollingInterval = setInterval(async () => {
      if (!currentScenarioId) return
      // Only poll if we haven't received a socket update recently
      const timeSinceLastSocket = Date.now() - lastSocketUpdate
      if (timeSinceLastSocket > POLLING_INTERVAL_MS) {
        console.log('[ScenarioStats] Polling fallback - no socket update for', Math.round(timeSinceLastSocket / 1000), 's, refreshing via REST')
        await fetchStats(currentScenarioId)
      }
    }, POLLING_INTERVAL_MS)
  }

  function stopPolling() {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
    }
  }

  // ===== Tab Visibility Handler =====
  // Re-subscribe to socket room when browser tab becomes visible again.
  // Browsers throttle/disconnect sockets in hidden tabs, losing room membership.
  let visibilityHandler = null

  function setupVisibilityHandler() {
    if (typeof document === 'undefined') return
    visibilityHandler = () => {
      if (document.visibilityState === 'visible' && currentScenarioId) {
        console.log('[ScenarioStats] Tab visible - re-subscribing and refreshing stats')
        // Re-subscribe to room (may have been lost during tab suspension)
        if (socket?.connected) {
          socket.emit('scenario:subscribe', { scenario_id: currentScenarioId })
        }
        // Always fetch fresh stats via REST as immediate catch-up
        fetchStats(currentScenarioId)
      }
    }
    document.addEventListener('visibilitychange', visibilityHandler)
  }

  function cleanupVisibilityHandler() {
    if (visibilityHandler && typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', visibilityHandler)
      visibilityHandler = null
    }
  }

  // ===== Socket Connection =====

  // Store handler references for proper cleanup
  let connectHandler = null
  let disconnectHandler = null

  function connect(scenarioId) {
    if (!scenarioId) return

    // Disconnect from previous scenario if different
    if (currentScenarioId && currentScenarioId !== scenarioId) {
      disconnect()
    }

    currentScenarioId = scenarioId
    mySubscriptionGeneration = ++subscriptionGeneration
    lastSocketUpdate = Date.now() // Grace period before first poll
    socket = getSocket()

    if (!socket) {
      console.error('[ScenarioStats] Socket not available')
      return
    }

    // Create handlers with proper references for cleanup
    connectHandler = () => {
      connected.value = true
      console.log('[ScenarioStats] Socket connected, subscribing to scenario:', currentScenarioId)
      // Use currentScenarioId instead of scenarioId to always subscribe to the latest
      if (currentScenarioId) {
        socket.emit('scenario:subscribe', { scenario_id: currentScenarioId })
      }
    }

    disconnectHandler = () => {
      connected.value = false
      console.log('[ScenarioStats] Socket disconnected')
    }

    socket.on('connect', connectHandler)
    socket.on('disconnect', disconnectHandler)

    // Register event handlers
    socket.on('scenario:stats', handleStats)
    socket.on('scenario:stats_updated', handleStatsUpdated)
    socket.on('scenario:error', handleError)

    // If already connected, subscribe immediately
    if (socket.connected) {
      connected.value = true
      console.log('[ScenarioStats] Socket already connected, subscribing to scenario:', scenarioId)
      socket.emit('scenario:subscribe', { scenario_id: scenarioId })
    } else {
      console.log('[ScenarioStats] Socket not connected yet, will subscribe on connect for scenario:', scenarioId)
    }

    // Start polling fallback to catch missed socket events
    startPolling()

    // Re-subscribe when tab becomes visible again
    setupVisibilityHandler()
  }

  function disconnect() {
    stopPolling()
    cleanupVisibilityHandler()

    if (!socket) return

    // Only emit unsubscribe if no newer composable instance has connected.
    // When navigating between scenarios, Vue mounts the new component BEFORE
    // unmounting the old one. Both share the singleton socket, so the old
    // instance's onUnmounted must not cancel the new instance's subscription.
    const isStillActiveSubscriber = mySubscriptionGeneration === subscriptionGeneration

    if (socket.connected && currentScenarioId && isStillActiveSubscriber) {
      console.log('[ScenarioStats] Unsubscribing from scenario:', currentScenarioId)
      socket.emit('scenario:unsubscribe', { scenario_id: currentScenarioId })
    } else if (!isStillActiveSubscriber && currentScenarioId) {
      console.log('[ScenarioStats] Skipping unsubscribe - newer subscriber active for scenario:', currentScenarioId)
    }

    // Always clean up this instance's event handlers
    if (connectHandler) {
      socket.off('connect', connectHandler)
      connectHandler = null
    }
    if (disconnectHandler) {
      socket.off('disconnect', disconnectHandler)
      disconnectHandler = null
    }
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
      // Also handle nested stats structure from get_scenario_stats_payload
      const statsData = data.stats || data
      processStatsPayload({
        scenario_id: scenarioId,
        function_type: data.function_type,
        kind: data.kind || 'progress',
        stats: {
          rater_stats: statsData.rater_stats || [],
          evaluator_stats: statsData.evaluator_stats || [],
          user_stats: statsData.user_stats || [],
          // Agreement metrics - check both direct and nested locations
          krippendorff_alpha: statsData.krippendorff_alpha ?? data.agreement_metrics?.alpha,
          alpha_interpretation: statsData.alpha_interpretation ?? data.agreement_metrics?.interpretation,
          overall_accuracy: statsData.overall_accuracy ?? data.overall_accuracy,
          // Include authenticity stats if present
          vote_distribution: statsData.vote_distribution || data.vote_distribution,
          // Include rating/dimension stats
          rating_distribution: statsData.rating_distribution || data.rating_distribution,
          dimension_averages: statsData.dimension_averages || data.dimension_averages,
          // Unified pairwise agreement - prefer pairwise_agreement, fallback to ranking_agreement
          pairwise_agreement: statsData.pairwise_agreement || data.pairwise_agreement ||
                              statsData.ranking_agreement || data.ranking_agreement,
          // Include ranking stats
          bucket_distribution: statsData.bucket_distribution || data.bucket_distribution,
          provenance_analysis: statsData.provenance_analysis || data.provenance_analysis,
          ranking_agreement: statsData.ranking_agreement || data.ranking_agreement  // Deprecated
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
    stopPolling()
    cleanupVisibilityHandler()
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
    hasHumans,
    hasLLMs,

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
