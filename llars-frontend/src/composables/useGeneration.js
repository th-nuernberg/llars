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

  /** @type {import('vue').Ref<Array>} Jobs shared with current user (read-only) */
  const sharedJobs = ref([])

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
  let socketConnectHandler = null
  let socketHandlers = {} // Named handler references for targeted socket.off() cleanup

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
      sharedJobs.value = response.data.shared_jobs || []
    } catch (err) {
      error.value = err.response?.data?.error || i18n.global.t('generation.messages.loadJobsFailed')
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
      error.value = err.response?.data?.error || i18n.global.t('generation.messages.loadJobFailed')
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

      showSuccess(i18n.global.t('generation.messages.jobCreated', { name: job.name }))
      return job
    } catch (err) {
      error.value = err.response?.data?.error || i18n.global.t('generation.messages.createJobFailed')
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

      showSuccess(i18n.global.t('generation.messages.jobDeleted'))
      return true
    } catch (err) {
      showError(err.response?.data?.error || i18n.global.t('generation.messages.deleteJobFailed'))
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
      showSuccess(i18n.global.t('generation.messages.jobStarted'))
      return true
    } catch (err) {
      showError(err.response?.data?.error || i18n.global.t('generation.messages.startJobFailed'))
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
      showSuccess(i18n.global.t('generation.messages.jobPaused'))
      return true
    } catch (err) {
      showError(err.response?.data?.error || i18n.global.t('generation.messages.pauseJobFailed'))
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
      showSuccess(i18n.global.t('generation.messages.jobCancelled'))
      return true
    } catch (err) {
      showError(err.response?.data?.error || i18n.global.t('generation.messages.cancelJobFailed'))
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
      showError(err.response?.data?.error || i18n.global.t('generation.messages.loadOutputFailed'))
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

      showSuccess(i18n.global.t('generation.messages.csvDownloaded'))
    } catch (err) {
      showError(i18n.global.t('generation.messages.csvExportFailed'))
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

      showSuccess(i18n.global.t('generation.messages.jsonDownloaded'))
    } catch (err) {
      showError(i18n.global.t('generation.messages.jsonExportFailed'))
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
      showSuccess(i18n.global.t('generation.messages.scenarioCreated', { name: data.scenario_name }))
      return response.data
    } catch (err) {
      showError(err.response?.data?.error || i18n.global.t('generation.messages.createScenarioFailed'))
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
  // ACTIONS - SHARING
  // ---------------------------------------------------------------------------

  /**
   * Share a job with another user (read-only).
   *
   * @param {number} jobId - Job ID
   * @param {string} username - Target username
   * @returns {Promise<boolean>} Success status
   */
  async function shareJob(jobId, username) {
    try {
      await generationApi.shareJob(jobId, username)
      showSuccess(i18n.global.t('generation.share.shared'))
      return true
    } catch (err) {
      showError(err.response?.data?.error || i18n.global.t('generation.messages.shareJobFailed'))
      return false
    }
  }

  /**
   * Remove a share from a job.
   *
   * @param {number} jobId - Job ID
   * @param {string} username - Target username
   * @returns {Promise<boolean>} Success status
   */
  async function unshareJob(jobId, username) {
    try {
      await generationApi.unshareJob(jobId, username)
      showSuccess(i18n.global.t('generation.share.unshared'))
      return true
    } catch (err) {
      showError(err.response?.data?.error || i18n.global.t('generation.messages.unshareJobFailed'))
      return false
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

    const shouldJoinOverview = autoLoadJobs || watchJobId !== null
    if (shouldJoinOverview) {
      socketConnectHandler = () => {
        socket.emit('generation:join_overview')
      }
      if (socket.connected) {
        socketConnectHandler()
      }
      socket.on('connect', socketConnectHandler)
    }

    // Store handler references for proper cleanup (prevents removing other components' listeners)
    socketHandlers.onJobStarted = (data) => {
      if (data.job_id === currentJob.value?.id) {
        currentJob.value.status = JOB_STATUS.QUEUED
      }
    }
    socket.on('generation:job:started', socketHandlers.onJobStarted)

    socketHandlers.onJobProgress = (data) => {
      if (data.job_id === currentJob.value?.id) {
        if (!currentJob.value.cost) currentJob.value.cost = {}
        currentJob.value.cost.total_cost_usd = data.cost_usd
        if (currentJob.value.progress) {
          currentJob.value.progress.total = data.total
          currentJob.value.progress.completed = data.completed
          currentJob.value.progress.failed = data.failed
          currentJob.value.progress.percent = data.percent
        }
      }
      _updateJobProgressInList(data.job_id, data)
    }
    socket.on('generation:job:progress', socketHandlers.onJobProgress)

    socketHandlers.onJobCompleted = (data) => {
      if (data.job_id === currentJob.value?.id) {
        currentJob.value.status = JOB_STATUS.COMPLETED
        if (currentJob.value.progress) {
          currentJob.value.progress.completed = data.completed
          currentJob.value.progress.failed = data.failed
        }
        showSuccess(i18n.global.t('generation.messages.jobCompleted', { count: data.completed }))
      }
      _updateJobStatusInList(data.job_id, JOB_STATUS.COMPLETED)
    }
    socket.on('generation:job:completed', socketHandlers.onJobCompleted)

    socketHandlers.onJobFailed = (data) => {
      if (data.job_id === currentJob.value?.id) {
        currentJob.value.status = JOB_STATUS.FAILED
        currentJob.value.error_message = data.error
        showError(i18n.global.t('generation.messages.jobFailed', { error: data.error }))
      }
      _updateJobStatusInList(data.job_id, JOB_STATUS.FAILED)
    }
    socket.on('generation:job:failed', socketHandlers.onJobFailed)

    socketHandlers.onBudgetExceeded = (data) => {
      if (data.job_id === currentJob.value?.id) {
        currentJob.value.status = JOB_STATUS.PAUSED
        showError(i18n.global.t('generation.messages.budgetExceeded', { cost: data.cost.toFixed(2) }))
      }
    }
    socket.on('generation:job:budget_exceeded', socketHandlers.onBudgetExceeded)

    socketHandlers.onItemCompleted = (data) => {
      if (data.job_id === currentJob.value?.id) {
        const output = outputs.value.find(o => o.id === data.output_id)
        if (output) {
          output.status = OUTPUT_STATUS.COMPLETED
          output.content_preview = data.content_preview
        }
      }
    }
    socket.on('generation:item:completed', socketHandlers.onItemCompleted)

    socketHandlers.onItemFailed = (data) => {
      if (data.job_id === currentJob.value?.id) {
        const output = outputs.value.find(o => o.id === data.output_id)
        if (output) {
          output.status = OUTPUT_STATUS.FAILED
          output.error_message = data.error
        }
      }
    }
    socket.on('generation:item:failed', socketHandlers.onItemFailed)

    // Share updated — refresh job list so shared/unshared jobs appear/disappear
    socketHandlers.onShareUpdated = () => {
      loadJobs()
    }
    socket.on('generation:share_updated', socketHandlers.onShareUpdated)
  }

  /**
   * Remove Socket.IO listeners.
   */
  function removeSocketListeners() {
    const socket = getSocket()
    if (!socket) return

    if (socketConnectHandler) {
      socket.emit('generation:leave_overview')
      socket.off('connect', socketConnectHandler)
      socketConnectHandler = null
    }

    // Remove only our specific handlers (not other components' listeners for the same events)
    if (socketHandlers.onJobStarted) socket.off('generation:job:started', socketHandlers.onJobStarted)
    if (socketHandlers.onJobProgress) socket.off('generation:job:progress', socketHandlers.onJobProgress)
    if (socketHandlers.onJobCompleted) socket.off('generation:job:completed', socketHandlers.onJobCompleted)
    if (socketHandlers.onJobFailed) socket.off('generation:job:failed', socketHandlers.onJobFailed)
    if (socketHandlers.onBudgetExceeded) socket.off('generation:job:budget_exceeded', socketHandlers.onBudgetExceeded)
    if (socketHandlers.onItemCompleted) socket.off('generation:item:completed', socketHandlers.onItemCompleted)
    if (socketHandlers.onItemFailed) socket.off('generation:item:failed', socketHandlers.onItemFailed)
    if (socketHandlers.onShareUpdated) socket.off('generation:share_updated', socketHandlers.onShareUpdated)
    socketHandlers = {}
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
    sharedJobs,
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

    // Actions - Sharing
    shareJob,
    unshareJob,

    // Actions - Estimation
    estimateCost,

    // Constants
    JOB_STATUS,
    OUTPUT_STATUS
  }
}

export default useGeneration
