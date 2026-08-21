/**
 * usePipeline Composable Tests
 *
 * Tests for pipeline run management, computed state, and Socket.IO integration.
 * Test IDs: PIPE_001 - PIPE_045
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('@/services/pipelineApi', () => ({
  pipelineApi: {
    getRuns: vi.fn(),
    getRun: vi.fn(),
    createRun: vi.fn(),
    startRun: vi.fn(),
    pauseRun: vi.fn(),
    cancelRun: vi.fn(),
    deleteRun: vi.fn(),
    submitReview: vi.fn()
  }
}))

const { mockShowSuccess, mockShowError } = vi.hoisted(() => ({
  mockShowSuccess: vi.fn(),
  mockShowError: vi.fn()
}))

vi.mock('@/composables/useSnackbar', () => ({
  useSnackbar: vi.fn(() => ({
    showSuccess: mockShowSuccess,
    showError: mockShowError
  }))
}))

vi.mock('vue-i18n', () => ({
  useI18n: vi.fn(() => ({
    t: vi.fn((key) => key)
  }))
}))

const mockSocket = {
  connected: false,
  on: vi.fn(),
  off: vi.fn(),
  emit: vi.fn()
}

vi.mock('@/services/socketService', () => ({
  getSocket: vi.fn(() => mockSocket)
}))

// Mock lifecycle hooks since tests run outside components
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onMounted: vi.fn((cb) => cb()),
    onUnmounted: vi.fn()
  }
})

import { pipelineApi } from '@/services/pipelineApi'
import { usePipeline, RUN_STATUS } from '@/views/Pipeline/composables/usePipeline'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getSocketHandler(eventName) {
  const calls = mockSocket.on.mock.calls.filter(c => c[0] === eventName)
  return calls.length > 0 ? calls[calls.length - 1][1] : null
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('RUN_STATUS', () => {
  it('PIPE_001: defines all expected statuses', () => {
    expect(RUN_STATUS.CREATED).toBe('created')
    expect(RUN_STATUS.RUNNING).toBe('running')
    expect(RUN_STATUS.PAUSED).toBe('paused')
    expect(RUN_STATUS.WAITING_FOR_REVIEW).toBe('waiting_for_review')
    expect(RUN_STATUS.COMPLETED).toBe('completed')
    expect(RUN_STATUS.FAILED).toBe('failed')
    expect(RUN_STATUS.CANCELLED).toBe('cancelled')
  })
})

describe('usePipeline', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSocket.connected = false
    mockSocket.on.mockReset()
    mockSocket.off.mockReset()
    mockSocket.emit.mockReset()
  })

  // =========================================================================
  // Initial State
  // =========================================================================

  describe('initial state', () => {
    it('PIPE_002: starts with empty state', () => {
      const p = usePipeline()

      expect(p.runs.value).toEqual([])
      expect(p.currentRun.value).toBeNull()
      expect(p.iterations.value).toEqual([])
      expect(p.livePhase.value).toBeNull()
      expect(p.isLoading.value).toBe(false)
      expect(p.error.value).toBeNull()
    })

    it('PIPE_003: computed values are default when no data', () => {
      const p = usePipeline()

      expect(p.isRunActive.value).toBe(false)
      expect(p.activeRuns.value).toEqual([])
      expect(p.progressPercent.value).toBe(0)
      expect(p.budgetPercent.value).toBe(0)
      expect(p.bestConfig.value).toBeNull()
      expect(p.scoreHistory.value).toEqual([])
    })
  })

  // =========================================================================
  // Computed Properties
  // =========================================================================

  describe('computed properties', () => {
    it('PIPE_004: isRunActive is true for RUNNING status', () => {
      const p = usePipeline()
      p.currentRun.value = { status: RUN_STATUS.RUNNING }
      expect(p.isRunActive.value).toBe(true)
    })

    it('PIPE_005: isRunActive is true for WAITING_FOR_REVIEW', () => {
      const p = usePipeline()
      p.currentRun.value = { status: RUN_STATUS.WAITING_FOR_REVIEW }
      expect(p.isRunActive.value).toBe(true)
    })

    it('PIPE_006: isRunActive is false for COMPLETED', () => {
      const p = usePipeline()
      p.currentRun.value = { status: RUN_STATUS.COMPLETED }
      expect(p.isRunActive.value).toBe(false)
    })

    it('PIPE_007: isRunActive is false for FAILED', () => {
      const p = usePipeline()
      p.currentRun.value = { status: RUN_STATUS.FAILED }
      expect(p.isRunActive.value).toBe(false)
    })

    it('PIPE_008: activeRuns filters running and waiting runs', () => {
      const p = usePipeline()
      p.runs.value = [
        { id: 1, status: RUN_STATUS.RUNNING },
        { id: 2, status: RUN_STATUS.COMPLETED },
        { id: 3, status: RUN_STATUS.WAITING_FOR_REVIEW },
        { id: 4, status: RUN_STATUS.FAILED }
      ]

      expect(p.activeRuns.value.map(r => r.id)).toEqual([1, 3])
    })

    it('PIPE_009: progressPercent calculates correctly', () => {
      const p = usePipeline()
      p.currentRun.value = { current_iteration: 3, max_iterations: 10 }
      expect(p.progressPercent.value).toBe(30)
    })

    it('PIPE_010: progressPercent is 0 when max_iterations is 0', () => {
      const p = usePipeline()
      p.currentRun.value = { current_iteration: 0, max_iterations: 0 }
      expect(p.progressPercent.value).toBe(0)
    })

    it('PIPE_011: budgetPercent reads from currentRun.budget', () => {
      const p = usePipeline()
      p.currentRun.value = { budget: { percent: 65 } }
      expect(p.budgetPercent.value).toBe(65)
    })

    it('PIPE_012: bestConfig reads from currentRun', () => {
      const p = usePipeline()
      p.currentRun.value = { best_config: { model: 'gpt-4', prompt: 'test' } }
      expect(p.bestConfig.value).toEqual({ model: 'gpt-4', prompt: 'test' })
    })

    it('PIPE_013: scoreHistory filters completed iterations', () => {
      const p = usePipeline()
      p.iterations.value = [
        { iteration_number: 1, status: 'completed', scores: { avg_score: 0.8 } },
        { iteration_number: 2, status: 'running', scores: null },
        { iteration_number: 3, status: 'completed', scores: { avg_score: 0.9 } }
      ]

      expect(p.scoreHistory.value).toHaveLength(2)
      expect(p.scoreHistory.value[0].iteration).toBe(1)
      expect(p.scoreHistory.value[0].avgScore).toBe(0.8)
      expect(p.scoreHistory.value[1].avgScore).toBe(0.9)
    })
  })

  // =========================================================================
  // loadRuns
  // =========================================================================

  describe('loadRuns', () => {
    it('PIPE_014: fetches runs and populates state', async () => {
      const mockRuns = [{ id: 1, status: 'running' }, { id: 2, status: 'completed' }]
      pipelineApi.getRuns.mockResolvedValueOnce({ data: { runs: mockRuns } })

      const p = usePipeline()
      await p.loadRuns({ status: 'running' })

      expect(pipelineApi.getRuns).toHaveBeenCalledWith({ status: 'running' })
      expect(p.runs.value).toEqual(mockRuns)
      expect(p.isLoading.value).toBe(false)
    })

    it('PIPE_015: sets error on failure', async () => {
      pipelineApi.getRuns.mockRejectedValueOnce({
        response: { data: { error: 'Server error' } }
      })

      const p = usePipeline()
      await p.loadRuns()

      expect(p.error.value).toBe('Server error')
      expect(p.isLoading.value).toBe(false)
    })

    it('PIPE_016: handles missing runs key', async () => {
      pipelineApi.getRuns.mockResolvedValueOnce({ data: {} })

      const p = usePipeline()
      await p.loadRuns()

      expect(p.runs.value).toEqual([])
    })
  })

  // =========================================================================
  // loadRun
  // =========================================================================

  describe('loadRun', () => {
    it('PIPE_017: fetches single run with iterations', async () => {
      const mockRun = {
        id: 1,
        status: 'running',
        iterations: [
          { iteration_number: 1, status: 'completed', scores: {} }
        ]
      }
      pipelineApi.getRun.mockResolvedValueOnce({ data: { run: mockRun } })

      const p = usePipeline()
      const result = await p.loadRun(1)

      expect(result).toEqual(mockRun)
      expect(p.currentRun.value).toEqual(mockRun)
      expect(p.iterations.value).toHaveLength(1)
    })

    it('PIPE_018: returns null on failure', async () => {
      pipelineApi.getRun.mockRejectedValueOnce({
        response: { data: { error: 'Not found' } }
      })

      const p = usePipeline()
      const result = await p.loadRun(999)

      expect(result).toBeNull()
      expect(p.error.value).toBe('Not found')
    })
  })

  // =========================================================================
  // createRun
  // =========================================================================

  describe('createRun', () => {
    it('PIPE_019: creates run and adds to list', async () => {
      const newRun = { id: 5, status: 'created', name: 'Test Run' }
      pipelineApi.createRun.mockResolvedValueOnce({ data: { run: newRun } })

      const p = usePipeline()
      p.runs.value = [{ id: 1 }]
      const result = await p.createRun({ name: 'Test Run' })

      expect(result).toEqual(newRun)
      expect(p.runs.value[0]).toEqual(newRun) // Prepended
      expect(p.currentRun.value).toEqual(newRun)
      expect(mockShowSuccess).toHaveBeenCalled()
    })

    it('PIPE_020: shows error on create failure', async () => {
      pipelineApi.createRun.mockRejectedValueOnce({
        response: { data: { error: 'Invalid config' } }
      })

      const p = usePipeline()
      const result = await p.createRun({})

      expect(result).toBeNull()
      expect(mockShowError).toHaveBeenCalledWith('Invalid config')
    })
  })

  // =========================================================================
  // startRun
  // =========================================================================

  describe('startRun', () => {
    it('PIPE_021: starts run and updates list', async () => {
      const updatedRun = { id: 1, status: 'running' }
      pipelineApi.startRun.mockResolvedValueOnce({ data: { run: updatedRun } })

      const p = usePipeline()
      p.runs.value = [{ id: 1, status: 'created' }]
      p.currentRun.value = { id: 1, status: 'created' }

      await p.startRun(1)

      expect(p.runs.value[0].status).toBe('running')
      expect(p.currentRun.value.status).toBe('running')
      expect(mockShowSuccess).toHaveBeenCalled()
    })

    it('PIPE_022: shows error on start failure', async () => {
      pipelineApi.startRun.mockRejectedValueOnce({
        response: { data: { error: 'Already running' } }
      })

      const p = usePipeline()
      await p.startRun(1)

      expect(mockShowError).toHaveBeenCalledWith('Already running')
    })
  })

  // =========================================================================
  // pauseRun
  // =========================================================================

  describe('pauseRun', () => {
    it('PIPE_023: pauses run and updates state', async () => {
      const updatedRun = { id: 1, status: 'paused' }
      pipelineApi.pauseRun.mockResolvedValueOnce({ data: { run: updatedRun } })

      const p = usePipeline()
      p.runs.value = [{ id: 1, status: 'running' }]
      p.currentRun.value = { id: 1, status: 'running' }

      await p.pauseRun(1)

      expect(p.currentRun.value.status).toBe('paused')
      expect(mockShowSuccess).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // cancelRun
  // =========================================================================

  describe('cancelRun', () => {
    it('PIPE_024: cancels run and updates state', async () => {
      const updatedRun = { id: 1, status: 'cancelled' }
      pipelineApi.cancelRun.mockResolvedValueOnce({ data: { run: updatedRun } })

      const p = usePipeline()
      p.runs.value = [{ id: 1, status: 'running' }]
      p.currentRun.value = { id: 1, status: 'running' }

      await p.cancelRun(1)

      expect(p.currentRun.value.status).toBe('cancelled')
      expect(mockShowSuccess).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // deleteRun
  // =========================================================================

  describe('deleteRun', () => {
    it('PIPE_025: deletes run and removes from list', async () => {
      pipelineApi.deleteRun.mockResolvedValueOnce({})

      const p = usePipeline()
      p.runs.value = [{ id: 1 }, { id: 2 }, { id: 3 }]
      p.currentRun.value = { id: 2 }

      await p.deleteRun(2)

      expect(p.runs.value.map(r => r.id)).toEqual([1, 3])
      expect(p.currentRun.value).toBeNull()
      expect(mockShowSuccess).toHaveBeenCalled()
    })

    it('PIPE_026: does not clear currentRun if different id', async () => {
      pipelineApi.deleteRun.mockResolvedValueOnce({})

      const p = usePipeline()
      p.runs.value = [{ id: 1 }, { id: 2 }]
      p.currentRun.value = { id: 1 }

      await p.deleteRun(2)

      expect(p.currentRun.value.id).toBe(1)
    })
  })

  // =========================================================================
  // submitReview
  // =========================================================================

  describe('submitReview', () => {
    it('PIPE_027: submits review and updates state', async () => {
      const updatedRun = { id: 1, status: 'running' }
      pipelineApi.submitReview.mockResolvedValueOnce({ data: { run: updatedRun } })

      const p = usePipeline()
      p.runs.value = [{ id: 1, status: 'waiting_for_review' }]
      p.currentRun.value = { id: 1, status: 'waiting_for_review' }

      await p.submitReview(1, 'continue')

      expect(pipelineApi.submitReview).toHaveBeenCalledWith(1, 'continue')
      expect(p.currentRun.value.status).toBe('running')
      expect(mockShowSuccess).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // Socket.IO Listeners
  // =========================================================================

  describe('socket listeners', () => {
    it('PIPE_028: setupSocketListeners registers all handlers', () => {
      mockSocket.connected = true
      const p = usePipeline()

      p.setupSocketListeners(42)

      const events = mockSocket.on.mock.calls.map(c => c[0])
      expect(events).toContain('connect')
      expect(events).toContain('pipeline:iteration:started')
      expect(events).toContain('pipeline:iteration:phase_changed')
      expect(events).toContain('pipeline:iteration:completed')
      expect(events).toContain('pipeline:run:waiting_for_review')
      expect(events).toContain('pipeline:run:completed')
      expect(events).toContain('pipeline:run:failed')
      expect(events).toContain('pipeline:run:paused')
    })

    it('PIPE_029: joins room when socket is connected', () => {
      mockSocket.connected = true
      const p = usePipeline()

      p.setupSocketListeners(42)

      expect(mockSocket.emit).toHaveBeenCalledWith('pipeline:join_run', { run_id: 42 })
    })

    it('PIPE_030: iteration:started updates livePhase and current_iteration', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.currentRun.value = { id: 42, current_iteration: 0 }
      p.setupSocketListeners(42)

      const handler = getSocketHandler('pipeline:iteration:started')
      handler({ run_id: 42, phase: 'generating', iteration: 3 })

      expect(p.livePhase.value).toEqual({ phase: 'generating', iteration: 3 })
      expect(p.currentRun.value.current_iteration).toBe(3)
    })

    it('PIPE_031: iteration:started ignores different run_id', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.currentRun.value = { id: 42, current_iteration: 0 }
      p.setupSocketListeners(42)

      const handler = getSocketHandler('pipeline:iteration:started')
      handler({ run_id: 999, phase: 'generating', iteration: 3 })

      expect(p.livePhase.value).toBeNull()
    })

    it('PIPE_032: phase_changed updates livePhase', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.setupSocketListeners(42)

      const handler = getSocketHandler('pipeline:iteration:phase_changed')
      handler({ run_id: 42, phase: 'evaluating', iteration: 2 })

      expect(p.livePhase.value).toEqual({ phase: 'evaluating', iteration: 2 })
    })

    it('PIPE_033: iteration:completed adds new iteration', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.currentRun.value = { id: 42 }
      p.iterations.value = []
      p.setupSocketListeners(42)

      const handler = getSocketHandler('pipeline:iteration:completed')
      handler({
        run_id: 42,
        iteration: 1,
        scores: { avg_score: 0.85 },
        reasoning: 'Improved prompt',
        delta: 0.05,
        best_so_far: { model: 'gpt-4' }
      })

      expect(p.iterations.value).toHaveLength(1)
      expect(p.iterations.value[0].scores.avg_score).toBe(0.85)
      expect(p.iterations.value[0].status).toBe('completed')
      expect(p.currentRun.value.best_config).toEqual({ model: 'gpt-4' })
      expect(p.livePhase.value).toBeNull()
    })

    it('PIPE_034: iteration:completed updates existing iteration', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.currentRun.value = { id: 42 }
      p.iterations.value = [{ iteration_number: 1, status: 'running' }]
      p.setupSocketListeners(42)

      const handler = getSocketHandler('pipeline:iteration:completed')
      handler({
        run_id: 42,
        iteration: 1,
        scores: { avg_score: 0.9 },
        reasoning: 'Done',
        delta: 0.1
      })

      expect(p.iterations.value).toHaveLength(1)
      expect(p.iterations.value[0].status).toBe('completed')
      expect(p.iterations.value[0].scores.avg_score).toBe(0.9)
    })

    it('PIPE_035: run:waiting_for_review sets status', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.currentRun.value = { id: 42, status: 'running', best_config: null }
      p.setupSocketListeners(42)

      const handler = getSocketHandler('pipeline:run:waiting_for_review')
      handler({ run_id: 42, best_config: { prompt: 'best' } })

      expect(p.currentRun.value.status).toBe(RUN_STATUS.WAITING_FOR_REVIEW)
      expect(p.currentRun.value.best_config).toEqual({ prompt: 'best' })
      expect(p.livePhase.value).toBeNull()
    })

    it('PIPE_036: run:completed sets COMPLETED status', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.currentRun.value = { id: 42, status: 'running' }
      p.setupSocketListeners(42)

      const handler = getSocketHandler('pipeline:run:completed')
      handler({ run_id: 42, status: 'completed', best_config: { final: true } })

      expect(p.currentRun.value.status).toBe(RUN_STATUS.COMPLETED)
      expect(p.currentRun.value.best_config).toEqual({ final: true })
    })

    it('PIPE_037: run:completed sets CANCELLED when status is cancelled', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.currentRun.value = { id: 42, status: 'running' }
      p.setupSocketListeners(42)

      const handler = getSocketHandler('pipeline:run:completed')
      handler({ run_id: 42, status: 'cancelled' })

      expect(p.currentRun.value.status).toBe(RUN_STATUS.CANCELLED)
    })

    it('PIPE_038: run:failed sets FAILED status and shows error', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.currentRun.value = { id: 42, status: 'running' }
      p.setupSocketListeners(42)

      const handler = getSocketHandler('pipeline:run:failed')
      handler({ run_id: 42, error: 'Model timeout' })

      expect(p.currentRun.value.status).toBe(RUN_STATUS.FAILED)
      expect(p.currentRun.value.error_message).toBe('Model timeout')
      expect(mockShowError).toHaveBeenCalledWith('Model timeout')
    })

    it('PIPE_039: run:paused sets PAUSED status', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.currentRun.value = { id: 42, status: 'running' }
      p.setupSocketListeners(42)

      const handler = getSocketHandler('pipeline:run:paused')
      handler({ run_id: 42 })

      expect(p.currentRun.value.status).toBe(RUN_STATUS.PAUSED)
      expect(p.livePhase.value).toBeNull()
    })
  })

  // =========================================================================
  // removeSocketListeners
  // =========================================================================

  describe('removeSocketListeners', () => {
    it('PIPE_040: removes all socket event listeners', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.setupSocketListeners(42)

      mockSocket.off.mockClear()
      p.removeSocketListeners()

      const offEvents = mockSocket.off.mock.calls.map(c => c[0])
      expect(offEvents).toContain('connect')
      expect(offEvents).toContain('pipeline:iteration:started')
      expect(offEvents).toContain('pipeline:iteration:phase_changed')
      expect(offEvents).toContain('pipeline:iteration:completed')
      expect(offEvents).toContain('pipeline:run:waiting_for_review')
      expect(offEvents).toContain('pipeline:run:completed')
      expect(offEvents).toContain('pipeline:run:failed')
      expect(offEvents).toContain('pipeline:run:paused')
    })

    it('PIPE_041: emits leave_run when socket handler exists', () => {
      mockSocket.connected = true
      const p = usePipeline()
      p.setupSocketListeners(42)

      mockSocket.emit.mockClear()
      p.removeSocketListeners()

      expect(mockSocket.emit).toHaveBeenCalledWith('pipeline:leave_run', expect.any(Object))
    })
  })

  // =========================================================================
  // Options: autoLoadRuns & watchRunId
  // =========================================================================

  describe('options', () => {
    it('PIPE_042: autoLoadRuns=true calls loadRuns on mount', async () => {
      pipelineApi.getRuns.mockResolvedValueOnce({ data: { runs: [] } })

      usePipeline({ autoLoadRuns: true })

      expect(pipelineApi.getRuns).toHaveBeenCalled()
    })

    it('PIPE_043: watchRunId loads run and sets up socket listeners', async () => {
      const mockRun = { id: 5, status: 'running', iterations: [] }
      pipelineApi.getRun.mockResolvedValueOnce({ data: { run: mockRun } })
      mockSocket.connected = true

      usePipeline({ watchRunId: 5 })

      expect(pipelineApi.getRun).toHaveBeenCalledWith(5)
      expect(mockSocket.emit).toHaveBeenCalledWith('pipeline:join_run', { run_id: 5 })
    })
  })

  // =========================================================================
  // Return interface
  // =========================================================================

  describe('return interface', () => {
    it('PIPE_044: exposes all expected methods and state', () => {
      const p = usePipeline()

      // State
      expect(p.runs).toBeDefined()
      expect(p.currentRun).toBeDefined()
      expect(p.iterations).toBeDefined()
      expect(p.livePhase).toBeDefined()
      expect(p.isLoading).toBeDefined()
      expect(p.error).toBeDefined()

      // Computed
      expect(p.isRunActive).toBeDefined()
      expect(p.activeRuns).toBeDefined()
      expect(p.progressPercent).toBeDefined()
      expect(p.budgetPercent).toBeDefined()
      expect(p.bestConfig).toBeDefined()
      expect(p.scoreHistory).toBeDefined()

      // Actions
      const actions = ['loadRuns', 'loadRun', 'createRun', 'startRun',
        'pauseRun', 'cancelRun', 'deleteRun', 'submitReview',
        'setupSocketListeners', 'removeSocketListeners']
      for (const a of actions) {
        expect(typeof p[a], `${a} should be a function`).toBe('function')
      }
    })

    it('PIPE_045: exposes RUN_STATUS constant', () => {
      const p = usePipeline()
      expect(p.RUN_STATUS).toBeDefined()
      expect(p.RUN_STATUS.RUNNING).toBe('running')
    })
  })
})
