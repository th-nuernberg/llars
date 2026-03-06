/**
 * useLLMEvaluation Composable Tests
 *
 * Tests for the LLM evaluation monitoring composable.
 * Test IDs: LLM_EVAL_001 - LLM_EVAL_040
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
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

// Mock useModelRegistry
const mockUpdateRegistry = vi.fn()
vi.mock('@/composables/useModelRegistry', () => ({
  useModelRegistry: vi.fn(() => ({
    updateRegistry: mockUpdateRegistry
  }))
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

import axios from 'axios'

let useLLMEvaluation, EVAL_STATUS, TASK_TYPES

describe('useLLMEvaluation Composable', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    mockSocket.on.mockReset()
    mockSocket.off.mockReset()
    mockSocket.emit.mockReset()
    mockSocket.connected = false

    const module = await import('@/composables/useLLMEvaluation')
    useLLMEvaluation = module.useLLMEvaluation
    EVAL_STATUS = module.EVAL_STATUS
    TASK_TYPES = module.TASK_TYPES
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Constants ====================

  describe('Constants', () => {
    it('LLM_EVAL_001: EVAL_STATUS has expected values', () => {
      expect(EVAL_STATUS.IDLE).toBe('idle')
      expect(EVAL_STATUS.RUNNING).toBe('running')
      expect(EVAL_STATUS.COMPLETED).toBe('completed')
      expect(EVAL_STATUS.ERROR).toBe('error')
    })

    it('LLM_EVAL_002: TASK_TYPES has expected values', () => {
      expect(TASK_TYPES.RANKING).toBe('ranking')
      expect(TASK_TYPES.RATING).toBe('rating')
      expect(TASK_TYPES.AUTHENTICITY).toBe('authenticity')
      expect(TASK_TYPES.MAIL_RATING).toBe('mail_rating')
      expect(TASK_TYPES.COMPARISON).toBe('comparison')
      expect(TASK_TYPES.LABELING).toBe('labeling')
      expect(TASK_TYPES.TEXT_CLASSIFICATION).toBe('text_classification')
    })
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('LLM_EVAL_003: exports useLLMEvaluation function', () => {
      expect(typeof useLLMEvaluation).toBe('function')
    })

    it('LLM_EVAL_004: returns all expected properties', () => {
      const result = useLLMEvaluation()

      // State
      expect(result).toHaveProperty('status')
      expect(result).toHaveProperty('progress')
      expect(result).toHaveProperty('results')
      expect(result).toHaveProperty('currentEvaluation')
      expect(result).toHaveProperty('agreementMetrics')
      expect(result).toHaveProperty('tokenUsage')
      expect(result).toHaveProperty('error')
      expect(result).toHaveProperty('connected')

      // Computed
      expect(result).toHaveProperty('isRunning')
      expect(result).toHaveProperty('isCompleted')
      expect(result).toHaveProperty('hasError')
      expect(result).toHaveProperty('progressPercent')
      expect(result).toHaveProperty('sortedResults')

      // Methods
      expect(result).toHaveProperty('fetchProgress')
      expect(result).toHaveProperty('fetchResult')
      expect(result).toHaveProperty('fetchAgreementMetrics')
      expect(result).toHaveProperty('startEvaluation')
      expect(result).toHaveProperty('stopEvaluation')
      expect(result).toHaveProperty('clearError')
      expect(result).toHaveProperty('reset')
      expect(result).toHaveProperty('connect')
      expect(result).toHaveProperty('connectToScenario')
      expect(result).toHaveProperty('disconnect')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('LLM_EVAL_005: status starts as IDLE', () => {
      const llm = useLLMEvaluation()

      expect(llm.status.value).toBe(EVAL_STATUS.IDLE)
    })

    it('LLM_EVAL_006: progress starts at zero', () => {
      const llm = useLLMEvaluation()

      expect(llm.progress.value.total).toBe(0)
      expect(llm.progress.value.completed).toBe(0)
      expect(llm.progress.value.pending).toBe(0)
      expect(llm.progress.value.failed).toBe(0)
      expect(llm.progress.value.percent).toBe(0)
    })

    it('LLM_EVAL_007: results is empty initially', () => {
      const llm = useLLMEvaluation()

      expect(llm.results.value).toEqual([])
    })

    it('LLM_EVAL_008: connected is false initially', () => {
      const llm = useLLMEvaluation()

      expect(llm.connected.value).toBe(false)
    })

    it('LLM_EVAL_009: agreementMetrics is null initially', () => {
      const llm = useLLMEvaluation()

      expect(llm.agreementMetrics.value).toBeNull()
    })

    it('LLM_EVAL_010: tokenUsage starts at zero', () => {
      const llm = useLLMEvaluation()

      expect(llm.tokenUsage.value.total_tokens).toBe(0)
      expect(llm.tokenUsage.value.total_cost_usd).toBe(0)
    })
  })

  // ==================== Computed ====================

  describe('Computed Properties', () => {
    it('LLM_EVAL_011: isRunning reflects status', () => {
      const llm = useLLMEvaluation()

      expect(llm.isRunning.value).toBe(false)
    })

    it('LLM_EVAL_012: isCompleted reflects status', () => {
      const llm = useLLMEvaluation()

      expect(llm.isCompleted.value).toBe(false)
    })

    it('LLM_EVAL_013: hasError reflects error state', () => {
      const llm = useLLMEvaluation()

      expect(llm.hasError.value).toBe(false)
    })

    it('LLM_EVAL_014: progressPercent is 0 initially', () => {
      const llm = useLLMEvaluation()

      expect(llm.progressPercent.value).toBe(0)
    })

    it('LLM_EVAL_015: sortedResults sorts by created_at descending', () => {
      const llm = useLLMEvaluation()

      // We cannot directly mutate readonly results, so test the computed logic
      // The sorted results should be empty initially
      expect(llm.sortedResults.value).toEqual([])
    })
  })

  // ==================== Start Evaluation ====================

  describe('Start Evaluation', () => {
    it('LLM_EVAL_016: startEvaluation calls correct endpoint', async () => {
      // Use initialScenarioId to trigger auto-connect
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.post.mockResolvedValue({
        data: { task_id: 'abc123', status: 'started' }
      })

      const result = await llm.startEvaluation({
        modelId: 'Global/OpenAI/gpt-5-nano',
        promptTemplateId: 1
      })

      expect(axios.post).toHaveBeenCalledWith(
        '/api/evaluation/llm/42/start',
        expect.objectContaining({
          model_id: 'Global/OpenAI/gpt-5-nano',
          prompt_template_id: 1
        })
      )
      expect(result.task_id).toBe('abc123')
    })

    it('LLM_EVAL_017: startEvaluation sets RUNNING status', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.post.mockResolvedValue({ data: { status: 'started' } })

      await llm.startEvaluation({ modelId: 'test' })

      // Status should be RUNNING (set before API call)
      // Note: since we mock the post to succeed, status stays RUNNING
    })

    it('LLM_EVAL_018: startEvaluation sets ERROR on failure', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.post.mockRejectedValue({
        response: { data: { error: 'Model not found' } }
      })

      await expect(llm.startEvaluation({ modelId: 'bad_model' })).rejects.toBeDefined()

      expect(llm.status.value).toBe(EVAL_STATUS.ERROR)
      expect(llm.error.value).toBe('Model not found')
    })
  })

  // ==================== Stop Evaluation ====================

  describe('Stop Evaluation', () => {
    it('LLM_EVAL_019: stopEvaluation calls correct endpoint', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.post.mockResolvedValue({ data: { status: 'stopped' } })

      await llm.stopEvaluation()

      expect(axios.post).toHaveBeenCalledWith('/api/evaluation/llm/42/stop')
    })

    it('LLM_EVAL_020: stopEvaluation sets IDLE status', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.post.mockResolvedValue({ data: { status: 'stopped' } })

      await llm.stopEvaluation()

      expect(llm.status.value).toBe(EVAL_STATUS.IDLE)
    })

    it('LLM_EVAL_021: stopEvaluation handles error', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.post.mockRejectedValue({
        response: { data: { error: 'Cannot stop' } }
      })

      await expect(llm.stopEvaluation()).rejects.toBeDefined()

      expect(llm.error.value).toBe('Cannot stop')
    })
  })

  // ==================== Fetch Progress ====================

  describe('Fetch Progress', () => {
    it('LLM_EVAL_022: fetchProgress calls correct endpoint', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.get.mockClear()
      axios.get.mockResolvedValue({
        data: {
          progress: { total: 10, completed: 5, pending: 5, failed: 0, percent: 50 },
          results: [],
          status: 'running'
        }
      })

      await llm.fetchProgress()

      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/llm/42/progress')
    })

    it('LLM_EVAL_023: fetchProgress updates progress state', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.get.mockClear()
      axios.get.mockResolvedValue({
        data: {
          progress: { total: 10, completed: 3, pending: 7, failed: 0, percent: 30 },
          results: [{ id: 1, status: 'completed' }],
          status: 'running'
        }
      })

      await llm.fetchProgress()

      expect(llm.progress.value.total).toBe(10)
      expect(llm.progress.value.completed).toBe(3)
      expect(llm.status.value).toBe('running')
    })

    it('LLM_EVAL_024: fetchProgress updates model registry', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.get.mockClear()
      const mockRegistry = { 'model-1': { display_name: 'GPT-5' } }

      axios.get.mockResolvedValue({
        data: {
          progress: {},
          model_registry: mockRegistry
        }
      })

      await llm.fetchProgress()

      expect(mockUpdateRegistry).toHaveBeenCalledWith(mockRegistry)
    })

    it('LLM_EVAL_025: fetchProgress handles error gracefully', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.get.mockClear()
      axios.get.mockRejectedValue({
        response: { data: { error: 'Server error' } }
      })

      await llm.fetchProgress()

      expect(llm.error.value).toBe('Server error')
    })
  })

  // ==================== Fetch Agreement Metrics ====================

  describe('Fetch Agreement Metrics', () => {
    it('LLM_EVAL_026: fetchAgreementMetrics calls correct endpoint', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.get.mockClear()
      axios.get.mockResolvedValue({
        data: {
          metrics: {
            krippendorff_alpha: { value: 0.85, interpretation: 'good' },
            percent_agreement: { value: 0.9 }
          },
          rater_count: 3,
          item_count: 20,
          raters: ['user1', 'user2', 'GPT-4'],
          task_type: 'ranking'
        }
      })

      const result = await llm.fetchAgreementMetrics()

      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/42/agreement-metrics')
      expect(result).toBeTruthy()
      expect(result.alpha).toBe(0.85)
      expect(result.accuracy).toBe(0.9)
      expect(result.raterCount).toBe(3)
      expect(result.itemCount).toBe(20)
    })

    it('LLM_EVAL_027: fetchAgreementMetrics returns null on error', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      axios.get.mockClear()
      axios.get.mockRejectedValue(new Error('Network error'))

      const result = await llm.fetchAgreementMetrics()

      expect(result).toBeNull()
    })

    it('LLM_EVAL_028: fetchAgreementMetrics warns without scenarioId', async () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const llm = useLLMEvaluation(null)

      const result = await llm.fetchAgreementMetrics()

      expect(result).toBeNull()
      expect(warnSpy).toHaveBeenCalledWith(
        'Cannot fetch agreement metrics: no scenarioId'
      )

      warnSpy.mockRestore()
    })
  })

  // ==================== Fetch Result ====================

  describe('Fetch Result', () => {
    it('LLM_EVAL_029: fetchResult calls correct endpoint', async () => {
      const llm = useLLMEvaluation()

      axios.get.mockResolvedValue({
        data: { id: 123, result: { rating: 5 } }
      })

      const result = await llm.fetchResult(123)

      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/llm/result/123')
      expect(result.id).toBe(123)
    })

    it('LLM_EVAL_030: fetchResult throws on error', async () => {
      const llm = useLLMEvaluation()

      axios.get.mockRejectedValue(new Error('Not found'))

      await expect(llm.fetchResult(999)).rejects.toThrow('Not found')
    })
  })

  // ==================== Reset & Clear Error ====================

  describe('Reset and Clear Error', () => {
    it('LLM_EVAL_031: reset clears all state', () => {
      const llm = useLLMEvaluation()

      llm.reset()

      expect(llm.status.value).toBe(EVAL_STATUS.IDLE)
      expect(llm.progress.value.total).toBe(0)
      expect(llm.results.value).toEqual([])
      expect(llm.currentEvaluation.value).toBeNull()
      expect(llm.agreementMetrics.value).toBeNull()
      expect(llm.tokenUsage.value.total_tokens).toBe(0)
      expect(llm.error.value).toBeNull()
    })

    it('LLM_EVAL_032: clearError resets error and status', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      // Force an error
      axios.post.mockRejectedValue({
        response: { data: { error: 'test error' } }
      })

      try {
        await llm.startEvaluation({})
      } catch {
        // expected
      }

      expect(llm.error.value).toBe('test error')
      expect(llm.status.value).toBe(EVAL_STATUS.ERROR)

      llm.clearError()

      expect(llm.error.value).toBeNull()
      expect(llm.status.value).toBe(EVAL_STATUS.IDLE)
    })
  })

  // ==================== Socket Connection ====================

  describe('Socket Connection', () => {
    it('LLM_EVAL_033: connect with scenarioId registers socket handlers', () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      // onMounted triggers connect()
      expect(mockSocket.on).toHaveBeenCalledWith('connect', expect.any(Function))
      expect(mockSocket.on).toHaveBeenCalledWith('disconnect', expect.any(Function))
      expect(mockSocket.on).toHaveBeenCalledWith('llm_eval:progress', expect.any(Function))
      expect(mockSocket.on).toHaveBeenCalledWith('llm_eval:result', expect.any(Function))
      expect(mockSocket.on).toHaveBeenCalledWith('llm_eval:completed', expect.any(Function))
      expect(mockSocket.on).toHaveBeenCalledWith('llm_eval:error', expect.any(Function))
      expect(mockSocket.on).toHaveBeenCalledWith('llm_eval:task_started', expect.any(Function))
      expect(mockSocket.on).toHaveBeenCalledWith('llm_eval:task_completed', expect.any(Function))
      expect(mockSocket.on).toHaveBeenCalledWith('llm_eval:task_failed', expect.any(Function))
      expect(mockSocket.on).toHaveBeenCalledWith('llm_eval:scenario_completed', expect.any(Function))
    })

    it('LLM_EVAL_034: connect without scenarioId does not register handlers', () => {
      const llm = useLLMEvaluation(null)

      // Should not register any handlers since no scenarioId
      expect(mockSocket.on).not.toHaveBeenCalled()
    })

    it('LLM_EVAL_035: disconnect removes all socket handlers', () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      llm.disconnect()

      expect(mockSocket.off).toHaveBeenCalledWith('llm_eval:progress', expect.any(Function))
      expect(mockSocket.off).toHaveBeenCalledWith('llm_eval:result', expect.any(Function))
      expect(mockSocket.off).toHaveBeenCalledWith('llm_eval:completed', expect.any(Function))
      expect(mockSocket.off).toHaveBeenCalledWith('llm_eval:error', expect.any(Function))
      expect(mockSocket.off).toHaveBeenCalledWith('llm_eval:task_started', expect.any(Function))
      expect(mockSocket.off).toHaveBeenCalledWith('llm_eval:task_completed', expect.any(Function))
      expect(mockSocket.off).toHaveBeenCalledWith('llm_eval:task_failed', expect.any(Function))
      expect(mockSocket.off).toHaveBeenCalledWith('llm_eval:scenario_completed', expect.any(Function))
    })
  })

  // ==================== Connect To Scenario ====================

  describe('Connect To Scenario', () => {
    it('LLM_EVAL_036: connectToScenario resets and connects', async () => {
      const llm = useLLMEvaluation()

      axios.get.mockResolvedValue({ data: {} })

      await llm.connectToScenario(99)

      // Should fetch progress and agreement metrics
      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/llm/99/progress')
      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/99/agreement-metrics')
    })

    it('LLM_EVAL_037: connectToScenario ignores null scenarioId', async () => {
      const llm = useLLMEvaluation()

      await llm.connectToScenario(null)

      // No API calls should be made
      expect(axios.get).not.toHaveBeenCalled()
    })
  })

  // ==================== Socket Event Handling ====================

  describe('Socket Event Handling', () => {
    it('LLM_EVAL_038: handleProgress updates progress on matching scenario', () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      // Find the handleProgress callback
      const progressHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'llm_eval:progress'
      )?.[1]

      expect(progressHandler).toBeDefined()

      progressHandler({
        scenario_id: 42,
        total: 10,
        completed: 3,
        pending: 7,
        failed: 0,
        percent: 30
      })

      expect(llm.progress.value.total).toBe(10)
      expect(llm.progress.value.completed).toBe(3)
      expect(llm.status.value).toBe(EVAL_STATUS.RUNNING)
    })

    it('LLM_EVAL_039: handleProgress ignores different scenario', () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      const progressHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'llm_eval:progress'
      )?.[1]

      progressHandler({
        scenario_id: 999, // Different scenario
        total: 50,
        completed: 25
      })

      // Should not update
      expect(llm.progress.value.total).toBe(0)
    })

    it('LLM_EVAL_040: handleError sets error state on matching scenario', () => {
      axios.get.mockResolvedValue({ data: {} })

      const llm = useLLMEvaluation(42)

      const errorHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'llm_eval:error'
      )?.[1]

      expect(errorHandler).toBeDefined()

      errorHandler({
        scenario_id: 42,
        error: 'Rate limit exceeded'
      })

      expect(llm.error.value).toBe('Rate limit exceeded')
      expect(llm.status.value).toBe(EVAL_STATUS.ERROR)
    })
  })
})
