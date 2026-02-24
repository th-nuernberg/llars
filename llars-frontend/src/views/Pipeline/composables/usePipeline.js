/**
 * usePipeline Composable
 *
 * State management and business logic for automated pipeline runs.
 * Provides reactive state, actions, and Socket.IO integration for
 * real-time progress updates (live-join pattern).
 *
 * @module views/Pipeline/composables/usePipeline
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSnackbar } from '@/composables/useSnackbar'
import { pipelineApi } from '@/services/pipelineApi'
import { getSocket } from '@/services/socketService'
import { useI18n } from 'vue-i18n'

/**
 * Pipeline run statuses
 */
export const RUN_STATUS = {
  CREATED: 'created',
  RUNNING: 'running',
  PAUSED: 'paused',
  WAITING_FOR_REVIEW: 'waiting_for_review',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
}

/**
 * Composable for managing automated pipeline runs.
 *
 * @param {Object} [options] - Configuration options
 * @param {boolean} [options.autoLoadRuns=false] - Auto-load runs on mount
 * @param {number|null} [options.watchRunId=null] - Run ID to watch for live updates
 * @returns {Object} Pipeline state and actions
 */
export function usePipeline(options = {}) {
  const { autoLoadRuns = false, watchRunId = null } = options

  const { showSuccess, showError } = useSnackbar()
  const { t } = useI18n()

  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------

  const runs = ref([])
  const currentRun = ref(null)
  const iterations = ref([])
  const livePhase = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  let socketConnectHandler = null

  // ---------------------------------------------------------------------------
  // COMPUTED
  // ---------------------------------------------------------------------------

  const isRunActive = computed(() => {
    if (!currentRun.value) return false
    return [RUN_STATUS.RUNNING, RUN_STATUS.WAITING_FOR_REVIEW].includes(currentRun.value.status)
  })

  const activeRuns = computed(() => {
    return runs.value.filter(r =>
      [RUN_STATUS.RUNNING, RUN_STATUS.WAITING_FOR_REVIEW].includes(r.status)
    )
  })

  const progressPercent = computed(() => {
    if (!currentRun.value) return 0
    const { current_iteration, max_iterations } = currentRun.value
    if (!max_iterations) return 0
    return Math.round((current_iteration / max_iterations) * 100)
  })

  const budgetPercent = computed(() => {
    return currentRun.value?.budget?.percent || 0
  })

  const bestConfig = computed(() => {
    return currentRun.value?.best_config || null
  })

  const scoreHistory = computed(() => {
    if (!iterations.value.length) return []
    return iterations.value
      .filter(it => it.scores && it.status === 'completed')
      .map(it => ({
        iteration: it.iteration_number,
        scores: it.scores,
        avgScore: it.scores?.avg_score || 0,
      }))
  })

  // ---------------------------------------------------------------------------
  // REST API ACTIONS
  // ---------------------------------------------------------------------------

  async function loadRuns(params = {}) {
    isLoading.value = true
    error.value = null
    try {
      const response = await pipelineApi.getRuns(params)
      runs.value = response.data.runs || []
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load runs'
    } finally {
      isLoading.value = false
    }
  }

  async function loadRun(runId) {
    isLoading.value = true
    error.value = null
    try {
      const response = await pipelineApi.getRun(runId)
      const run = response.data.run
      currentRun.value = run
      iterations.value = run.iterations || []
      return run
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load run'
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function createRun(data) {
    try {
      const response = await pipelineApi.createRun(data)
      const run = response.data.run
      runs.value.unshift(run)
      currentRun.value = run
      showSuccess(t('pipeline.messages.created'))
      return run
    } catch (err) {
      showError(err.response?.data?.error || t('pipeline.messages.createFailed'))
      return null
    }
  }

  async function startRun(runId) {
    try {
      const response = await pipelineApi.startRun(runId)
      _updateRunInList(response.data.run)
      if (currentRun.value?.id === runId) {
        currentRun.value = response.data.run
      }
      showSuccess(t('pipeline.messages.started'))
    } catch (err) {
      showError(err.response?.data?.error || t('pipeline.messages.startFailed'))
    }
  }

  async function pauseRun(runId) {
    try {
      const response = await pipelineApi.pauseRun(runId)
      _updateRunInList(response.data.run)
      if (currentRun.value?.id === runId) {
        currentRun.value = response.data.run
      }
      showSuccess(t('pipeline.messages.paused'))
    } catch (err) {
      showError(err.response?.data?.error || t('pipeline.messages.pauseFailed'))
    }
  }

  async function cancelRun(runId) {
    try {
      const response = await pipelineApi.cancelRun(runId)
      _updateRunInList(response.data.run)
      if (currentRun.value?.id === runId) {
        currentRun.value = response.data.run
      }
      showSuccess(t('pipeline.messages.cancelled'))
    } catch (err) {
      showError(err.response?.data?.error || t('pipeline.messages.cancelFailed'))
    }
  }

  async function deleteRun(runId) {
    try {
      await pipelineApi.deleteRun(runId)
      runs.value = runs.value.filter(r => r.id !== runId)
      if (currentRun.value?.id === runId) {
        currentRun.value = null
      }
      showSuccess(t('pipeline.messages.deleted'))
    } catch (err) {
      showError(err.response?.data?.error || t('pipeline.messages.deleteFailed'))
    }
  }

  async function submitReview(runId, decision) {
    try {
      const response = await pipelineApi.submitReview(runId, decision)
      _updateRunInList(response.data.run)
      if (currentRun.value?.id === runId) {
        currentRun.value = response.data.run
      }
      showSuccess(t('pipeline.messages.reviewSubmitted'))
    } catch (err) {
      showError(err.response?.data?.error || t('pipeline.messages.reviewFailed'))
    }
  }

  // ---------------------------------------------------------------------------
  // SOCKET.IO
  // ---------------------------------------------------------------------------

  function setupSocketListeners(runId) {
    const socket = getSocket()
    if (!socket) return

    socketConnectHandler = () => {
      socket.emit('pipeline:join_run', { run_id: runId })
    }

    if (socket.connected) {
      socketConnectHandler()
    }
    socket.on('connect', socketConnectHandler)

    socket.on('pipeline:iteration:started', (data) => {
      if (data.run_id !== runId) return
      livePhase.value = { phase: data.phase, iteration: data.iteration }
      if (currentRun.value) {
        currentRun.value.current_iteration = data.iteration
      }
    })

    socket.on('pipeline:iteration:phase_changed', (data) => {
      if (data.run_id !== runId) return
      livePhase.value = { phase: data.phase, iteration: data.iteration }
    })

    socket.on('pipeline:iteration:completed', (data) => {
      if (data.run_id !== runId) return
      livePhase.value = null

      // Add or update iteration in list
      const existing = iterations.value.find(
        it => it.iteration_number === data.iteration
      )
      if (existing) {
        Object.assign(existing, {
          scores: data.scores,
          agent_reasoning: data.reasoning,
          delta_to_best: data.delta,
          status: 'completed',
        })
      } else {
        iterations.value.push({
          iteration_number: data.iteration,
          scores: data.scores,
          agent_reasoning: data.reasoning,
          delta_to_best: data.delta,
          status: 'completed',
        })
      }

      // Update best config
      if (currentRun.value && data.best_so_far) {
        currentRun.value.best_config = data.best_so_far
      }
    })

    socket.on('pipeline:run:waiting_for_review', (data) => {
      if (data.run_id !== runId) return
      if (currentRun.value) {
        currentRun.value.status = RUN_STATUS.WAITING_FOR_REVIEW
        currentRun.value.best_config = data.best_config || currentRun.value.best_config
      }
      livePhase.value = null
    })

    socket.on('pipeline:run:completed', (data) => {
      if (data.run_id !== runId) return
      if (currentRun.value) {
        currentRun.value.status = data.status === 'cancelled'
          ? RUN_STATUS.CANCELLED
          : RUN_STATUS.COMPLETED
        currentRun.value.best_config = data.best_config || currentRun.value.best_config
      }
      livePhase.value = null
    })

    socket.on('pipeline:run:failed', (data) => {
      if (data.run_id !== runId) return
      if (currentRun.value) {
        currentRun.value.status = RUN_STATUS.FAILED
        currentRun.value.error_message = data.error
      }
      livePhase.value = null
      showError(data.error || t('pipeline.messages.runFailed'))
    })

    socket.on('pipeline:run:paused', (data) => {
      if (data.run_id !== runId) return
      if (currentRun.value) {
        currentRun.value.status = RUN_STATUS.PAUSED
      }
      livePhase.value = null
    })
  }

  function removeSocketListeners() {
    const socket = getSocket()
    if (!socket) return

    if (socketConnectHandler) {
      socket.off('connect', socketConnectHandler)
      socket.emit('pipeline:leave_run', {
        run_id: watchRunId || currentRun.value?.id,
      })
    }

    socket.off('pipeline:iteration:started')
    socket.off('pipeline:iteration:phase_changed')
    socket.off('pipeline:iteration:completed')
    socket.off('pipeline:run:waiting_for_review')
    socket.off('pipeline:run:completed')
    socket.off('pipeline:run:failed')
    socket.off('pipeline:run:paused')
  }

  // ---------------------------------------------------------------------------
  // INTERNAL HELPERS
  // ---------------------------------------------------------------------------

  function _updateRunInList(updatedRun) {
    const idx = runs.value.findIndex(r => r.id === updatedRun.id)
    if (idx >= 0) {
      runs.value[idx] = { ...runs.value[idx], ...updatedRun }
    }
  }

  // ---------------------------------------------------------------------------
  // LIFECYCLE
  // ---------------------------------------------------------------------------

  onMounted(() => {
    if (autoLoadRuns) loadRuns()
    if (watchRunId) {
      loadRun(watchRunId)
      setupSocketListeners(watchRunId)
    }
  })

  onUnmounted(() => {
    removeSocketListeners()
  })

  return {
    // State
    runs,
    currentRun,
    iterations,
    livePhase,
    isLoading,
    error,

    // Computed
    isRunActive,
    activeRuns,
    progressPercent,
    budgetPercent,
    bestConfig,
    scoreHistory,

    // Actions
    loadRuns,
    loadRun,
    createRun,
    startRun,
    pauseRun,
    cancelRun,
    deleteRun,
    submitReview,
    setupSocketListeners,
    removeSocketListeners,

    // Constants
    RUN_STATUS,
  }
}
