/**
 * useGeneration Composable Tests
 *
 * Tests for batch generation job management composable.
 * Test IDs: GEN_001 - GEN_060
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock generationApi
const mockGenerationApi = {
  getJobs: vi.fn(),
  getJob: vi.fn(),
  createJob: vi.fn(),
  deleteJob: vi.fn(),
  startJob: vi.fn(),
  pauseJob: vi.fn(),
  cancelJob: vi.fn(),
  getOutputs: vi.fn(),
  getOutput: vi.fn(),
  exportCsv: vi.fn(),
  exportJson: vi.fn(),
  createScenario: vi.fn(),
  estimateCost: vi.fn()
}

vi.mock('@/services/generationApi', () => ({
  generationApi: mockGenerationApi
}))

// Mock useSnackbar
const mockShowSuccess = vi.fn()
const mockShowError = vi.fn()
vi.mock('@/composables/useSnackbar', () => ({
  useSnackbar: vi.fn(() => ({
    showSuccess: mockShowSuccess,
    showError: mockShowError
  }))
}))

// Mock socketService
const mockSocket = {
  on: vi.fn(),
  off: vi.fn(),
  emit: vi.fn(),
  connected: false
}
vi.mock('@/services/socketService', () => ({
  getSocket: vi.fn(() => mockSocket)
}))

// Mock i18n
vi.mock('@/i18n', () => ({
  i18n: {
    global: {
      t: vi.fn((key) => key)
    }
  }
}))

// Mock Vue lifecycle hooks
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onMounted: vi.fn((cb) => cb()),
    onUnmounted: vi.fn()
  }
})

let useGeneration, JOB_STATUS, OUTPUT_STATUS

describe('useGeneration', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    mockSocket.on.mockReset()
    mockSocket.off.mockReset()
    mockSocket.emit.mockReset()
    mockSocket.connected = false

    const module = await import('@/composables/useGeneration')
    useGeneration = module.useGeneration
    JOB_STATUS = module.JOB_STATUS
    OUTPUT_STATUS = module.OUTPUT_STATUS
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('GEN_001: exports useGeneration function', () => {
      expect(typeof useGeneration).toBe('function')
    })

    it('GEN_002: exports JOB_STATUS constants', () => {
      expect(JOB_STATUS).toBeDefined()
      expect(JOB_STATUS.CREATED).toBe('created')
      expect(JOB_STATUS.QUEUED).toBe('queued')
      expect(JOB_STATUS.RUNNING).toBe('running')
      expect(JOB_STATUS.PAUSED).toBe('paused')
      expect(JOB_STATUS.COMPLETED).toBe('completed')
      expect(JOB_STATUS.FAILED).toBe('failed')
      expect(JOB_STATUS.CANCELLED).toBe('cancelled')
    })

    it('GEN_003: exports OUTPUT_STATUS constants', () => {
      expect(OUTPUT_STATUS).toBeDefined()
      expect(OUTPUT_STATUS.PENDING).toBe('pending')
      expect(OUTPUT_STATUS.PROCESSING).toBe('processing')
      expect(OUTPUT_STATUS.COMPLETED).toBe('completed')
      expect(OUTPUT_STATUS.FAILED).toBe('failed')
      expect(OUTPUT_STATUS.RETRYING).toBe('retrying')
      expect(OUTPUT_STATUS.SKIPPED).toBe('skipped')
    })

    it('GEN_004: useGeneration returns all expected properties', () => {
      const result = useGeneration()
      // State
      expect(result).toHaveProperty('jobs')
      expect(result).toHaveProperty('currentJob')
      expect(result).toHaveProperty('outputs')
      expect(result).toHaveProperty('outputsPagination')
      expect(result).toHaveProperty('isLoading')
      expect(result).toHaveProperty('isLoadingOutputs')
      expect(result).toHaveProperty('error')
      expect(result).toHaveProperty('costEstimate')
      // Computed
      expect(result).toHaveProperty('activeJobs')
      expect(result).toHaveProperty('completedJobs')
      expect(result).toHaveProperty('isJobActive')
      expect(result).toHaveProperty('progressPercent')
      // Actions
      expect(typeof result.loadJobs).toBe('function')
      expect(typeof result.loadJob).toBe('function')
      expect(typeof result.createJob).toBe('function')
      expect(typeof result.deleteJob).toBe('function')
      expect(typeof result.startJob).toBe('function')
      expect(typeof result.pauseJob).toBe('function')
      expect(typeof result.cancelJob).toBe('function')
      expect(typeof result.loadOutputs).toBe('function')
      expect(typeof result.loadOutput).toBe('function')
      expect(typeof result.downloadCsv).toBe('function')
      expect(typeof result.downloadJson).toBe('function')
      expect(typeof result.createScenario).toBe('function')
      expect(typeof result.estimateCost).toBe('function')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('GEN_005: starts with empty jobs list', () => {
      const { jobs } = useGeneration()
      expect(jobs.value).toEqual([])
    })

    it('GEN_006: starts with null currentJob', () => {
      const { currentJob } = useGeneration()
      expect(currentJob.value).toBeNull()
    })

    it('GEN_007: starts with empty outputs', () => {
      const { outputs } = useGeneration()
      expect(outputs.value).toEqual([])
    })

    it('GEN_008: starts not loading', () => {
      const { isLoading, isLoadingOutputs } = useGeneration()
      expect(isLoading.value).toBe(false)
      expect(isLoadingOutputs.value).toBe(false)
    })

    it('GEN_009: starts with no error', () => {
      const { error } = useGeneration()
      expect(error.value).toBeNull()
    })

    it('GEN_010: starts with default pagination', () => {
      const { outputsPagination } = useGeneration()
      expect(outputsPagination.value.page).toBe(1)
      expect(outputsPagination.value.pages).toBe(1)
      expect(outputsPagination.value.total).toBe(0)
      expect(outputsPagination.value.perPage).toBe(50)
    })
  })

  // ==================== Computed Properties ====================

  describe('Computed Properties', () => {
    it('GEN_011: activeJobs filters running and queued jobs', () => {
      const { jobs, activeJobs } = useGeneration()
      jobs.value = [
        { id: 1, status: 'running' },
        { id: 2, status: 'queued' },
        { id: 3, status: 'completed' },
        { id: 4, status: 'failed' }
      ]
      expect(activeJobs.value).toHaveLength(2)
      expect(activeJobs.value.map(j => j.id)).toEqual([1, 2])
    })

    it('GEN_012: completedJobs filters completed jobs', () => {
      const { jobs, completedJobs } = useGeneration()
      jobs.value = [
        { id: 1, status: 'running' },
        { id: 2, status: 'completed' },
        { id: 3, status: 'completed' }
      ]
      expect(completedJobs.value).toHaveLength(2)
    })

    it('GEN_013: isJobActive returns true for running job', () => {
      const { currentJob, isJobActive } = useGeneration()
      currentJob.value = { id: 1, status: 'running' }
      expect(isJobActive.value).toBe(true)
    })

    it('GEN_014: isJobActive returns true for queued job', () => {
      const { currentJob, isJobActive } = useGeneration()
      currentJob.value = { id: 1, status: 'queued' }
      expect(isJobActive.value).toBe(true)
    })

    it('GEN_015: isJobActive returns false for completed job', () => {
      const { currentJob, isJobActive } = useGeneration()
      currentJob.value = { id: 1, status: 'completed' }
      expect(isJobActive.value).toBe(false)
    })

    it('GEN_016: isJobActive returns false when no current job', () => {
      const { isJobActive } = useGeneration()
      expect(isJobActive.value).toBe(false)
    })

    it('GEN_017: progressPercent returns progress from current job', () => {
      const { currentJob, progressPercent } = useGeneration()
      currentJob.value = { id: 1, progress: { percent: 75 } }
      expect(progressPercent.value).toBe(75)
    })

    it('GEN_018: progressPercent returns 0 when no progress', () => {
      const { currentJob, progressPercent } = useGeneration()
      currentJob.value = { id: 1 }
      expect(progressPercent.value).toBe(0)
    })

    it('GEN_019: progressPercent returns 0 when no current job', () => {
      const { progressPercent } = useGeneration()
      expect(progressPercent.value).toBe(0)
    })
  })

  // ==================== Job Management Actions ====================

  describe('loadJobs', () => {
    it('GEN_020: loads jobs successfully', async () => {
      mockGenerationApi.getJobs.mockResolvedValue({
        data: { jobs: [{ id: 1, name: 'Job 1' }, { id: 2, name: 'Job 2' }] }
      })

      const { loadJobs, jobs, isLoading, error } = useGeneration()
      await loadJobs()

      expect(jobs.value).toHaveLength(2)
      expect(jobs.value[0].name).toBe('Job 1')
      expect(isLoading.value).toBe(false)
      expect(error.value).toBeNull()
    })

    it('GEN_021: handles loadJobs error', async () => {
      mockGenerationApi.getJobs.mockRejectedValue({
        response: { data: { error: 'Server error' } }
      })

      const { loadJobs, error, isLoading } = useGeneration()
      await loadJobs()

      expect(error.value).toBe('Server error')
      expect(isLoading.value).toBe(false)
    })

    it('GEN_022: passes params to getJobs', async () => {
      mockGenerationApi.getJobs.mockResolvedValue({ data: { jobs: [] } })

      const { loadJobs } = useGeneration()
      await loadJobs({ status: 'running' })

      expect(mockGenerationApi.getJobs).toHaveBeenCalledWith({ status: 'running' })
    })

    it('GEN_023: sets isLoading during request', async () => {
      let resolvePromise
      mockGenerationApi.getJobs.mockReturnValue(
        new Promise(resolve => { resolvePromise = resolve })
      )

      const { loadJobs, isLoading } = useGeneration()
      const promise = loadJobs()
      expect(isLoading.value).toBe(true)

      resolvePromise({ data: { jobs: [] } })
      await promise
      expect(isLoading.value).toBe(false)
    })
  })

  describe('loadJob', () => {
    it('GEN_024: loads a single job', async () => {
      const job = { id: 5, name: 'Test Job', status: 'running' }
      mockGenerationApi.getJob.mockResolvedValue({ data: { job } })

      const { loadJob, currentJob } = useGeneration()
      const result = await loadJob(5)

      expect(result).toEqual(job)
      expect(currentJob.value).toEqual(job)
      expect(mockGenerationApi.getJob).toHaveBeenCalledWith(5)
    })

    it('GEN_025: returns null on loadJob error', async () => {
      mockGenerationApi.getJob.mockRejectedValue({
        response: { data: { error: 'Not found' } }
      })

      const { loadJob, error } = useGeneration()
      const result = await loadJob(999)

      expect(result).toBeNull()
      expect(error.value).toBe('Not found')
    })
  })

  describe('createJob', () => {
    it('GEN_026: creates job and adds to list', async () => {
      const job = { id: 10, name: 'New Job', status: 'created' }
      mockGenerationApi.createJob.mockResolvedValue({ data: { job } })

      const { createJob, jobs, currentJob } = useGeneration()
      const result = await createJob({ name: 'New Job' })

      expect(result).toEqual(job)
      expect(jobs.value[0]).toEqual(job)
      expect(currentJob.value).toEqual(job)
      expect(mockShowSuccess).toHaveBeenCalled()
    })

    it('GEN_027: returns null on createJob error', async () => {
      mockGenerationApi.createJob.mockRejectedValue({
        response: { data: { error: 'Validation failed' } }
      })

      const { createJob, error } = useGeneration()
      const result = await createJob({})

      expect(result).toBeNull()
      expect(error.value).toBe('Validation failed')
      expect(mockShowError).toHaveBeenCalledWith('Validation failed')
    })
  })

  describe('deleteJob', () => {
    it('GEN_028: deletes job and removes from list', async () => {
      mockGenerationApi.deleteJob.mockResolvedValue({})

      const { deleteJob, jobs, currentJob } = useGeneration()
      jobs.value = [{ id: 1 }, { id: 2 }, { id: 3 }]
      currentJob.value = { id: 2 }

      const result = await deleteJob(2)

      expect(result).toBe(true)
      expect(jobs.value).toHaveLength(2)
      expect(jobs.value.find(j => j.id === 2)).toBeUndefined()
      expect(currentJob.value).toBeNull()
      expect(mockShowSuccess).toHaveBeenCalled()
    })

    it('GEN_029: deleteJob does not clear currentJob if different id', async () => {
      mockGenerationApi.deleteJob.mockResolvedValue({})

      const { deleteJob, jobs, currentJob } = useGeneration()
      jobs.value = [{ id: 1 }, { id: 2 }]
      currentJob.value = { id: 1 }

      await deleteJob(2)

      expect(currentJob.value).toEqual({ id: 1 })
    })

    it('GEN_030: returns false on deleteJob error', async () => {
      mockGenerationApi.deleteJob.mockRejectedValue({
        response: { data: { error: 'Cannot delete' } }
      })

      const { deleteJob } = useGeneration()
      const result = await deleteJob(1)

      expect(result).toBe(false)
      expect(mockShowError).toHaveBeenCalled()
    })
  })

  // ==================== Job Lifecycle ====================

  describe('startJob', () => {
    it('GEN_031: starts a job and updates list', async () => {
      const updatedJob = { id: 1, status: 'queued' }
      mockGenerationApi.startJob.mockResolvedValue({ data: { job: updatedJob } })

      const { startJob, jobs, currentJob } = useGeneration()
      jobs.value = [{ id: 1, status: 'created' }]
      currentJob.value = { id: 1, status: 'created' }

      const result = await startJob(1)

      expect(result).toBe(true)
      expect(mockShowSuccess).toHaveBeenCalledWith('Job gestartet')
    })

    it('GEN_032: returns false on startJob error', async () => {
      mockGenerationApi.startJob.mockRejectedValue({
        response: { data: { error: 'Queue full' } }
      })

      const { startJob } = useGeneration()
      const result = await startJob(1)

      expect(result).toBe(false)
      expect(mockShowError).toHaveBeenCalled()
    })
  })

  describe('pauseJob', () => {
    it('GEN_033: pauses a job successfully', async () => {
      const updatedJob = { id: 1, status: 'paused' }
      mockGenerationApi.pauseJob.mockResolvedValue({ data: { job: updatedJob } })

      const { pauseJob } = useGeneration()
      const result = await pauseJob(1)

      expect(result).toBe(true)
      expect(mockShowSuccess).toHaveBeenCalledWith('Job pausiert')
    })

    it('GEN_034: returns false on pauseJob error', async () => {
      mockGenerationApi.pauseJob.mockRejectedValue({
        response: { data: { error: 'Cannot pause' } }
      })

      const { pauseJob } = useGeneration()
      const result = await pauseJob(1)

      expect(result).toBe(false)
    })
  })

  describe('cancelJob', () => {
    it('GEN_035: cancels a job successfully', async () => {
      const updatedJob = { id: 1, status: 'cancelled' }
      mockGenerationApi.cancelJob.mockResolvedValue({ data: { job: updatedJob } })

      const { cancelJob } = useGeneration()
      const result = await cancelJob(1)

      expect(result).toBe(true)
      expect(mockShowSuccess).toHaveBeenCalledWith('Job abgebrochen')
    })

    it('GEN_036: returns false on cancelJob error', async () => {
      mockGenerationApi.cancelJob.mockRejectedValue({
        response: { data: { error: 'Cannot cancel' } }
      })

      const { cancelJob } = useGeneration()
      const result = await cancelJob(1)

      expect(result).toBe(false)
    })
  })

  // ==================== Outputs ====================

  describe('loadOutputs', () => {
    it('GEN_037: loads outputs with pagination', async () => {
      mockGenerationApi.getOutputs.mockResolvedValue({
        data: {
          items: [{ id: 1 }, { id: 2 }],
          page: 1,
          pages: 3,
          total: 150,
          per_page: 50
        }
      })

      const { loadOutputs, outputs, outputsPagination, isLoadingOutputs } = useGeneration()
      await loadOutputs(1)

      expect(outputs.value).toHaveLength(2)
      expect(outputsPagination.value.page).toBe(1)
      expect(outputsPagination.value.pages).toBe(3)
      expect(outputsPagination.value.total).toBe(150)
      expect(isLoadingOutputs.value).toBe(false)
    })

    it('GEN_038: passes params to getOutputs', async () => {
      mockGenerationApi.getOutputs.mockResolvedValue({
        data: { items: [], page: 2, pages: 3, total: 100, per_page: 50 }
      })

      const { loadOutputs } = useGeneration()
      await loadOutputs(1, { page: 2, status: 'completed', includePrompts: true })

      expect(mockGenerationApi.getOutputs).toHaveBeenCalledWith(1, {
        page: 2,
        per_page: 50,
        status: 'completed',
        include_prompts: true
      })
    })

    it('GEN_039: handles loadOutputs error gracefully', async () => {
      mockGenerationApi.getOutputs.mockRejectedValue(new Error('Network error'))

      const { loadOutputs, isLoadingOutputs } = useGeneration()
      await loadOutputs(1)

      expect(isLoadingOutputs.value).toBe(false)
    })
  })

  describe('loadOutput', () => {
    it('GEN_040: loads a single output', async () => {
      const output = { id: 5, content: 'Generated text' }
      mockGenerationApi.getOutput.mockResolvedValue({ data: { output } })

      const { loadOutput } = useGeneration()
      const result = await loadOutput(5)

      expect(result).toEqual(output)
    })

    it('GEN_041: returns null on loadOutput error', async () => {
      mockGenerationApi.getOutput.mockRejectedValue({
        response: { data: { error: 'Not found' } }
      })

      const { loadOutput } = useGeneration()
      const result = await loadOutput(999)

      expect(result).toBeNull()
      expect(mockShowError).toHaveBeenCalled()
    })
  })

})
