/**
 * useGeneration Composable
 *
 * State management and business logic for batch generation jobs.
 * Provides reactive state, actions, and Socket.IO integration for
 * real-time progress updates.
 *
 * @module composables/useGeneration
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSnackbar } from '@/composables/useSnackbar'
import { generationApi } from '@/services/generationApi'
import { getSocket } from '@/services/socketService'
import { i18n } from '@/i18n'

/**
 * Generation job statuses
 */
export const JOB_STATUS = {
  CREATED: 'created',
  QUEUED: 'queued',
  RUNNING: 'running',
  PAUSED: 'paused',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
}

/**
 * Output statuses
 */
export const OUTPUT_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  RETRYING: 'retrying',
  SKIPPED: 'skipped'
}

/**
 * Composable for managing batch generation jobs.
 *
 * @param {Object} [options] - Configuration options
 * @param {boolean} [options.autoLoadJobs=false] - Auto-load jobs on mount
 * @param {number} [options.watchJobId=null] - Job ID to watch for updates
 * @returns {Object} Generation state and actions
 *
 * @example
 * const {
 *   jobs,
 *   currentJob,
 *   isLoading,
 *   loadJobs,
 *   createJob,
 *   startJob
 * } = useGeneration({ autoLoadJobs: true })
 */
export function useGeneration(options = {}) {
  const { autoLoadJobs = false, watchJobId = null } = options

  // ---------------------------------------------------------------------------
  // STATE
  // ---------------------------------------------------------------------------

  /** @type {import('vue').Ref<Array>} List of jobs */
  const jobs = ref([])

  /** @type {import('vue').Ref<Object|null>} Currently selected job */
  const currentJob = ref(null)

  /** @type {import('vue').Ref<Array>} Outputs for current job */
  const outputs = ref([])

  /** @type {import('vue').Ref<Object>} Pagination state for outputs */
  const outputsPagination = ref({
    page: 1,
    pages: 1,
    total: 0,
    perPage: 50
  })

  /** @type {import('vue').Ref<boolean>} Loading state */
  const isLoading = ref(false)

  /** @type {import('vue').Ref<boolean>} Outputs loading state */
  const isLoadingOutputs = ref(false)

  /** @type {import('vue').Ref<string|null>} Error message */
  const error = ref(null)

  /** @type {import('vue').Ref<Object|null>} Cost estimate */
  const costEstimate = ref(null)

  // Snackbar notifications
  const { showSuccess, showError } = useSnackbar()

  // ---------------------------------------------------------------------------
  // COMPUTED
  // ---------------------------------------------------------------------------

  /**
   * Active jobs (running or queued)
   */
  const activeJobs = computed(() =>
    jobs.value.filter(j => j.status === JOB_STATUS.RUNNING || j.status === JOB_STATUS.QUEUED)
  )

  /**
   * Completed jobs
   */
  const completedJobs = computed(() =>
    jobs.value.filter(j => j.status === JOB_STATUS.COMPLETED)
  )

  /**
   * Whether current job is active
   */
  const isJobActive = computed(() =>
    currentJob.value?.status === JOB_STATUS.RUNNING ||
    currentJob.value?.status === JOB_STATUS.QUEUED
  )

  /**
   * Progress percentage for current job
   */
  const progressPercent = computed(() =>
    currentJob.value?.progress?.percent ?? 0
  )

  // ---------------------------------------------------------------------------
  // ACTIONS - JOB MANAGEMENT
  // ---------------------------------------------------------------------------

  /**
   * Load all jobs for the current user.
   *
   * @param {Object} [params] - Query parameters
   * @returns {Promise<void>}
   */
  async function loadJobs(params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const response = await generationApi.getJobs(params)
      jobs.value = response.data.jobs || []
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load jobs'
      console.error('[useGeneration] loadJobs error:', err)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load a specific job by ID.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<Object|null>} Job data or null on error
   */
  async function loadJob(jobId) {
    isLoading.value = true
    error.value = null

    try {
      const response = await generationApi.getJob(jobId)
      currentJob.value = response.data.job
      return currentJob.value
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load job'
      console.error('[useGeneration] loadJob error:', err)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new generation job.
   *
   * @param {Object} data - Job creation data
   * @returns {Promise<Object|null>} Created job or null on error
   */
  async function createJob(data) {
    isLoading.value = true
    error.value = null

    try {
      const response = await generationApi.createJob(data)
      const job = response.data.job

      // Add to jobs list
      jobs.value.unshift(job)
      currentJob.value = job

      showSuccess(`Job "${job.name}" erstellt`)
      return job
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to create job'
      showError(error.value)
      console.error('[useGeneration] createJob error:', err)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a job.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<boolean>} Success status
   */
  async function deleteJob(jobId) {
    try {
      await generationApi.deleteJob(jobId)

      // Remove from jobs list
      jobs.value = jobs.value.filter(j => j.id !== jobId)

      // Clear current job if deleted
      if (currentJob.value?.id === jobId) {
        currentJob.value = null
      }

      showSuccess(i18n.global.t('auto.cd71853b87'))
      return true
    } catch (err) {
      showError(err.response?.data?.error || 'Failed to delete job')
      return false
    }
  }

  // ---------------------------------------------------------------------------
  // ACTIONS - JOB LIFECYCLE
  // ---------------------------------------------------------------------------

  /**
   * Start a job.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<boolean>} Success status
   */
  async function startJob(jobId) {
    try {
      const response = await generationApi.startJob(jobId)
      _updateJobInList(response.data.job)
      showSuccess('Job gestartet')
      return true
    } catch (err) {
      showError(err.response?.data?.error || 'Failed to start job')
      return false
    }
  }

  /**
   * Pause a job.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<boolean>} Success status
   */
  async function pauseJob(jobId) {
    try {
      const response = await generationApi.pauseJob(jobId)
      _updateJobInList(response.data.job)
      showSuccess('Job pausiert')
      return true
    } catch (err) {
      showError(err.response?.data?.error || 'Failed to pause job')
      return false
    }
  }

  /**
   * Cancel a job.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<boolean>} Success status
   */
  async function cancelJob(jobId) {
    try {
      const response = await generationApi.cancelJob(jobId)
      _updateJobInList(response.data.job)
      showSuccess('Job abgebrochen')
      return true
    } catch (err) {
      showError(err.response?.data?.error || 'Failed to cancel job')
      return false
    }
  }

  // ---------------------------------------------------------------------------
  // ACTIONS - OUTPUTS
  // ---------------------------------------------------------------------------

  /**
   * Load outputs for a job.
   *
   * @param {number} jobId - Job ID
   * @param {Object} [params] - Query parameters
   * @returns {Promise<void>}
   */
  async function loadOutputs(jobId, params = {}) {
    isLoadingOutputs.value = true

    try {
      const response = await generationApi.getOutputs(jobId, {
        page: params.page || outputsPagination.value.page,
        per_page: params.perPage || outputsPagination.value.perPage,
        status: params.status,
        include_prompts: params.includePrompts || false
      })

      outputs.value = response.data.items || []
      outputsPagination.value = {
        page: response.data.page,
        pages: response.data.pages,
        total: response.data.total,
        perPage: response.data.per_page
      }
    } catch (err) {
      console.error('[useGeneration] loadOutputs error:', err)
    } finally {
      isLoadingOutputs.value = false
    }
  }

  /**
   * Load a single output with full details including rendered prompts.
   *
   * @param {number} outputId - Output ID
   * @returns {Promise<Object|null>} Output with prompts or null on error
   */
  async function loadOutput(outputId) {
    try {
      const response = await generationApi.getOutput(outputId)
      return response.data.output
    } catch (err) {
      console.error('[useGeneration] loadOutput error:', err)
      showError(err.response?.data?.error || 'Failed to load output details')
      return null
    }
  }

  // ---------------------------------------------------------------------------
  // ACTIONS - EXPORT
  // ---------------------------------------------------------------------------

  /**
   * Download outputs as CSV.
   *
   * @param {number} jobId - Job ID
   * @param {Object} [options] - Export options
   */
  async function downloadCsv(jobId, options = {}) {
    try {
      const response = await generationApi.exportCsv(jobId, options)

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `generation_${jobId}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      showSuccess('CSV heruntergeladen')
    } catch (err) {
      showError('CSV-Export fehlgeschlagen')
    }
  }

  /**
   * Download outputs as JSON.
   *
   * @param {number} jobId - Job ID
   * @param {Object} [options] - Export options
   */
  async function downloadJson(jobId, options = {}) {
    try {
      const response = await generationApi.exportJson(jobId, options)

      // Create download link
      const data = JSON.stringify(response.data.export, null, 2)
      const blob = new Blob([data], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `generation_${jobId}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      showSuccess('JSON heruntergeladen')
    } catch (err) {
      showError('JSON-Export fehlgeschlagen')
    }
  }

  // ---------------------------------------------------------------------------
  // ACTIONS - SCENARIO CREATION
  // ---------------------------------------------------------------------------

  /**
   * Create an evaluation scenario from job outputs.
   *
   * @param {number} jobId - Job ID
   * @param {Object} data - Scenario creation data
   * @returns {Promise<Object|null>} Created scenario info or null on error
   */
  async function createScenario(jobId, data) {
    try {
      const response = await generationApi.createScenario(jobId, data)
      showSuccess(`Szenario "${data.scenario_name}" erstellt`)
      return response.data
    } catch (err) {
      showError(err.response?.data?.error || 'Failed to create scenario')
      return null
    }
  }

  // ---------------------------------------------------------------------------
  // ACTIONS - ESTIMATION
  // ---------------------------------------------------------------------------

  /**
   * Estimate cost for a configuration.
   *
   * @param {Object} config - Job configuration
   * @returns {Promise<Object|null>} Cost estimate or null on error
   */
  async function estimateCost(config) {
    try {
      const response = await generationApi.estimateCost(config)
      costEstimate.value = response.data.estimate
      return costEstimate.value
    } catch (err) {
      console.error('[useGeneration] estimateCost error:', err)
      return null
    }
  }

  // ---------------------------------------------------------------------------
  // SOCKET.IO INTEGRATION
  // ---------------------------------------------------------------------------

  /**
   * Setup Socket.IO listeners for real-time updates.
   */
  function setupSocketListeners() {
    const socket = getSocket()
    if (!socket) return

    // Job started
    socket.on('generation:job:started', (data) => {
      if (data.job_id === currentJob.value?.id) {
        currentJob.value.status = JOB_STATUS.QUEUED
      }
    })

    // Job progress
    socket.on('generation:job:progress', (data) => {
      if (data.job_id === currentJob.value?.id) {
        currentJob.value.completed_items = data.completed
        currentJob.value.failed_items = data.failed
        currentJob.value.total_cost_usd = data.cost_usd
        if (currentJob.value.progress) {
          currentJob.value.progress.completed = data.completed
          currentJob.value.progress.failed = data.failed
          currentJob.value.progress.percent = data.percent
        }
      }
      _updateJobProgressInList(data.job_id, data)
    })

    // Job completed
    socket.on('generation:job:completed', (data) => {
      if (data.job_id === currentJob.value?.id) {
        currentJob.value.status = JOB_STATUS.COMPLETED
        currentJob.value.completed_items = data.completed
        currentJob.value.failed_items = data.failed
        showSuccess(`Job abgeschlossen: ${data.completed} Outputs`)
      }
      _updateJobStatusInList(data.job_id, JOB_STATUS.COMPLETED)
    })

    // Job failed
    socket.on('generation:job:failed', (data) => {
      if (data.job_id === currentJob.value?.id) {
        currentJob.value.status = JOB_STATUS.FAILED
        currentJob.value.error_message = data.error
        showError(`Job fehlgeschlagen: ${data.error}`)
      }
      _updateJobStatusInList(data.job_id, JOB_STATUS.FAILED)
    })

    // Budget exceeded
    socket.on('generation:job:budget_exceeded', (data) => {
      if (data.job_id === currentJob.value?.id) {
        currentJob.value.status = JOB_STATUS.PAUSED
        showError(`Budget-Limit erreicht: $${data.cost.toFixed(2)}`)
      }
    })

    // Item completed
    socket.on('generation:item:completed', (data) => {
      if (data.job_id === currentJob.value?.id) {
        // Update output in list if visible
        const output = outputs.value.find(o => o.id === data.output_id)
        if (output) {
          output.status = OUTPUT_STATUS.COMPLETED
          output.content_preview = data.content_preview
        }
      }
    })

    // Item failed
    socket.on('generation:item:failed', (data) => {
      if (data.job_id === currentJob.value?.id) {
        const output = outputs.value.find(o => o.id === data.output_id)
        if (output) {
          output.status = OUTPUT_STATUS.FAILED
          output.error_message = data.error
        }
      }
    })
  }

  /**
   * Remove Socket.IO listeners.
   */
  function removeSocketListeners() {
    const socket = getSocket()
    if (!socket) return

    socket.off('generation:job:started')
    socket.off('generation:job:progress')
    socket.off('generation:job:completed')
    socket.off('generation:job:failed')
    socket.off('generation:job:budget_exceeded')
    socket.off('generation:item:completed')
    socket.off('generation:item:failed')
  }

  // ---------------------------------------------------------------------------
  // HELPERS
  // ---------------------------------------------------------------------------

  /**
   * Update a job in the jobs list.
   */
  function _updateJobInList(job) {
    const index = jobs.value.findIndex(j => j.id === job.id)
    if (index !== -1) {
      jobs.value[index] = { ...jobs.value[index], ...job }
    }
    if (currentJob.value?.id === job.id) {
      currentJob.value = { ...currentJob.value, ...job }
    }
  }

  /**
   * Update job status in the list.
   */
  function _updateJobStatusInList(jobId, status) {
    const job = jobs.value.find(j => j.id === jobId)
    if (job) {
      job.status = status
    }
  }

  /**
   * Update job progress in the list.
   */
  function _updateJobProgressInList(jobId, data) {
    const job = jobs.value.find(j => j.id === jobId)
    if (job) {
      job.completed_items = data.completed
      job.progress_percent = data.percent
    }
  }

  // ---------------------------------------------------------------------------
  // LIFECYCLE
  // ---------------------------------------------------------------------------

  onMounted(() => {
    setupSocketListeners()

    if (autoLoadJobs) {
      loadJobs()
    }

    if (watchJobId) {
      loadJob(watchJobId)
    }
  })

  onUnmounted(() => {
    removeSocketListeners()
  })

  // ---------------------------------------------------------------------------
  // RETURN
  // ---------------------------------------------------------------------------

  return {
    // State
    jobs,
    currentJob,
    outputs,
    outputsPagination,
    isLoading,
    isLoadingOutputs,
    error,
    costEstimate,

    // Computed
    activeJobs,
    completedJobs,
    isJobActive,
    progressPercent,

    // Actions - Job Management
    loadJobs,
    loadJob,
    createJob,
    deleteJob,

    // Actions - Lifecycle
    startJob,
    pauseJob,
    cancelJob,

    // Actions - Outputs
    loadOutputs,
    loadOutput,

    // Actions - Export
    downloadCsv,
    downloadJson,

    // Actions - Scenario
    createScenario,

    // Actions - Estimation
    estimateCost,

    // Constants
    JOB_STATUS,
    OUTPUT_STATUS
  }
}

export default useGeneration
