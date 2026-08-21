/**
 * useEvaluationSession Composable Tests
 *
 * Tests for the generic evaluation session management composable.
 * Test IDs: EVAL_SESS_001 - EVAL_SESS_040
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'

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

// Mock Vue lifecycle hooks to prevent errors outside component context
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onMounted: vi.fn((cb) => cb()),
    onUnmounted: vi.fn()
  }
})

import axios from 'axios'

let useEvaluationSession, SESSION_STATUS

describe('useEvaluationSession Composable', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    // Reset mock socket state
    mockSocket.on.mockReset()
    mockSocket.off.mockReset()
    mockSocket.emit.mockReset()
    mockSocket.connected = false

    const module = await import('@/composables/useEvaluationSession')
    useEvaluationSession = module.useEvaluationSession
    SESSION_STATUS = module.SESSION_STATUS
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('EVAL_SESS_001: exports useEvaluationSession function', () => {
      expect(typeof useEvaluationSession).toBe('function')
    })

    it('EVAL_SESS_002: exports SESSION_STATUS constants', () => {
      expect(SESSION_STATUS).toBeDefined()
      expect(SESSION_STATUS.LOADING).toBe('loading')
      expect(SESSION_STATUS.READY).toBe('ready')
      expect(SESSION_STATUS.SUBMITTING).toBe('submitting')
      expect(SESSION_STATUS.COMPLETED).toBe('completed')
      expect(SESSION_STATUS.ERROR).toBe('error')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('EVAL_SESS_003: returns all expected properties', () => {
      axios.get.mockResolvedValue({ data: { scenario: {}, config: {}, items: [] } })

      const session = useEvaluationSession(1)

      expect(session).toHaveProperty('status')
      expect(session).toHaveProperty('items')
      expect(session).toHaveProperty('scenario')
      expect(session).toHaveProperty('config')
      expect(session).toHaveProperty('error')
      expect(session).toHaveProperty('progress')
      expect(session).toHaveProperty('connected')
      expect(session).toHaveProperty('currentItem')
      expect(session).toHaveProperty('currentIndex')
      expect(session).toHaveProperty('hasNext')
      expect(session).toHaveProperty('hasPrev')
      expect(session).toHaveProperty('progressPercent')
      expect(session).toHaveProperty('isComplete')
      expect(session).toHaveProperty('isLoading')
      expect(session).toHaveProperty('isReady')
      expect(session).toHaveProperty('goToItem')
      expect(session).toHaveProperty('goToItemById')
      expect(session).toHaveProperty('goNext')
      expect(session).toHaveProperty('goPrev')
      expect(session).toHaveProperty('goToFirstIncomplete')
      expect(session).toHaveProperty('loadSession')
      expect(session).toHaveProperty('submitEvaluation')
      expect(session).toHaveProperty('markItemCompleted')
      expect(session).toHaveProperty('clearError')
      expect(session).toHaveProperty('reset')
    })

    it('EVAL_SESS_004: progress starts at zero', () => {
      axios.get.mockResolvedValue({ data: { scenario: {}, config: {}, items: [] } })

      const session = useEvaluationSession(1)

      expect(session.progress.value.total).toBe(0)
      expect(session.progress.value.completed).toBe(0)
      expect(session.progress.value.remaining).toBe(0)
    })

    it('EVAL_SESS_005: currentItem is null initially', () => {
      axios.get.mockResolvedValue({ data: { scenario: {}, config: {}, items: [] } })

      const session = useEvaluationSession(1)

      // currentItem depends on items being loaded
      expect(session.currentItem.value).toBeNull()
    })

    it('EVAL_SESS_006: connected is false initially', () => {
      axios.get.mockResolvedValue({ data: { scenario: {}, config: {}, items: [] } })

      const session = useEvaluationSession(1)

      expect(session.connected.value).toBe(false)
    })
  })

  // ==================== Session Loading ====================

  describe('Session Loading', () => {
    it('EVAL_SESS_007: loadSession calls correct API endpoint', async () => {
      axios.get.mockResolvedValue({
        data: {
          scenario: { id: 42, name: 'Test' },
          config: { type: 'rating' },
          items: []
        }
      })

      const session = useEvaluationSession(42)
      await session.loadSession()

      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/session/42')
    })

    it('EVAL_SESS_008: loadSession populates scenario and config', async () => {
      const mockScenario = { id: 42, name: 'Test Scenario' }
      const mockConfig = { type: 'rating', min: 1, max: 5 }

      axios.get.mockResolvedValue({
        data: { scenario: mockScenario, config: mockConfig, items: [] }
      })

      const session = useEvaluationSession(42)
      await session.loadSession()

      expect(session.scenario.value).toEqual(mockScenario)
      expect(session.config.value).toEqual(mockConfig)
    })

    it('EVAL_SESS_009: loadSession populates items and progress', async () => {
      const mockItems = [
        { id: 1, evaluated: false },
        { id: 2, evaluated: true },
        { id: 3, evaluated: false }
      ]

      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: mockItems }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      expect(session.items.value).toHaveLength(3)
      expect(session.progress.value.total).toBe(3)
      expect(session.progress.value.completed).toBe(1)
      expect(session.progress.value.remaining).toBe(2)
    })

    it('EVAL_SESS_010: loadSession sets status to READY on success', async () => {
      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: [] }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      expect(session.status.value).toBe(SESSION_STATUS.READY)
    })

    it('EVAL_SESS_011: loadSession sets status to ERROR on failure', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Not found' } }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      expect(session.status.value).toBe(SESSION_STATUS.ERROR)
      expect(session.error.value).toBe('Not found')
    })

    it('EVAL_SESS_012: loadSession handles missing scenarioId', async () => {
      const session = useEvaluationSession(null)
      await session.loadSession()

      expect(session.status.value).toBe(SESSION_STATUS.ERROR)
      expect(session.error.value).toBe('No scenario ID provided')
    })

    it('EVAL_SESS_013: loadSession navigates to first incomplete item', async () => {
      const mockItems = [
        { id: 1, evaluated: true },
        { id: 2, evaluated: true },
        { id: 3, evaluated: false }
      ]

      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: mockItems }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      expect(session.currentIndex.value).toBe(2)
      expect(session.currentItem.value.id).toBe(3)
    })

    it('EVAL_SESS_014: loadSession falls back to index 0 when all items complete', async () => {
      const mockItems = [
        { id: 1, evaluated: true },
        { id: 2, evaluated: true }
      ]

      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: mockItems }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      expect(session.currentIndex.value).toBe(0)
    })
  })

  // ==================== Navigation ====================

  describe('Navigation', () => {
    let session

    beforeEach(async () => {
      const mockItems = [
        { id: 1, evaluated: false },
        { id: 2, evaluated: false },
        { id: 3, evaluated: false }
      ]

      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: mockItems }
      })

      session = useEvaluationSession(1)
      await session.loadSession()
    })

    it('EVAL_SESS_015: goNext advances to next item', () => {
      const result = session.goNext()

      expect(result).toBe(true)
      expect(session.currentIndex.value).toBe(1)
    })

    it('EVAL_SESS_016: goNext returns false at last item', () => {
      session.goToItem(2) // Go to last item
      const result = session.goNext()

      expect(result).toBe(false)
      expect(session.currentIndex.value).toBe(2)
    })

    it('EVAL_SESS_017: goPrev goes back to previous item', () => {
      session.goNext() // Go to index 1
      const result = session.goPrev()

      expect(result).toBe(true)
      expect(session.currentIndex.value).toBe(0)
    })

    it('EVAL_SESS_018: goPrev returns false at first item', () => {
      const result = session.goPrev()

      expect(result).toBe(false)
      expect(session.currentIndex.value).toBe(0)
    })

    it('EVAL_SESS_019: goToItem navigates to valid index', () => {
      const result = session.goToItem(2)

      expect(result).toBe(true)
      expect(session.currentIndex.value).toBe(2)
    })

    it('EVAL_SESS_020: goToItem rejects invalid index', () => {
      const result = session.goToItem(5)

      expect(result).toBe(false)
    })

    it('EVAL_SESS_021: goToItem rejects negative index', () => {
      const result = session.goToItem(-1)

      expect(result).toBe(false)
    })

    it('EVAL_SESS_022: goToItemById finds item by id', () => {
      const result = session.goToItemById(2)

      expect(result).toBe(true)
      expect(session.currentIndex.value).toBe(1)
    })

    it('EVAL_SESS_023: goToItemById returns false for non-existent id', () => {
      const result = session.goToItemById(999)

      expect(result).toBe(false)
    })

    it('EVAL_SESS_024: goToItemById handles null id', () => {
      const result = session.goToItemById(null)

      expect(result).toBe(false)
    })

    it('EVAL_SESS_025: hasNext is true when not at last item', () => {
      expect(session.hasNext.value).toBe(true)
    })

    it('EVAL_SESS_026: hasNext is false at last item', () => {
      session.goToItem(2)
      expect(session.hasNext.value).toBe(false)
    })

    it('EVAL_SESS_027: hasPrev is false at first item', () => {
      expect(session.hasPrev.value).toBe(false)
    })

    it('EVAL_SESS_028: hasPrev is true when not at first item', () => {
      session.goNext()
      expect(session.hasPrev.value).toBe(true)
    })
  })

  // ==================== Progress ====================

  describe('Progress Tracking', () => {
    it('EVAL_SESS_029: progressPercent calculates correctly', async () => {
      const mockItems = [
        { id: 1, evaluated: true },
        { id: 2, evaluated: true },
        { id: 3, evaluated: false },
        { id: 4, evaluated: false }
      ]

      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: mockItems }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      expect(session.progressPercent.value).toBe(50)
    })

    it('EVAL_SESS_030: progressPercent is 0 for empty items', async () => {
      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: [] }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      expect(session.progressPercent.value).toBe(0)
    })

    it('EVAL_SESS_031: isComplete is true when all items evaluated', async () => {
      const mockItems = [
        { id: 1, evaluated: true },
        { id: 2, evaluated: true }
      ]

      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: mockItems }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      expect(session.isComplete.value).toBe(true)
    })

    it('EVAL_SESS_032: isComplete is false when items remain', async () => {
      const mockItems = [
        { id: 1, evaluated: true },
        { id: 2, evaluated: false }
      ]

      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: mockItems }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      expect(session.isComplete.value).toBe(false)
    })
  })

  // ==================== Submit Evaluation ====================

  describe('Submit Evaluation', () => {
    let session

    beforeEach(async () => {
      const mockItems = [
        { id: 1, evaluated: false },
        { id: 2, evaluated: false }
      ]

      axios.get.mockResolvedValue({
        data: {
          scenario: { id: 1, function_type_id: 2 },
          config: {},
          items: mockItems
        }
      })

      session = useEvaluationSession(1)
      await session.loadSession()
    })

    it('EVAL_SESS_033: submitEvaluation posts to correct endpoint', async () => {
      axios.post.mockResolvedValue({
        data: { evaluation: { rating: 5 } }
      })

      await session.submitEvaluation(1, { rating: 5 })

      expect(axios.post).toHaveBeenCalledWith(
        '/api/evaluation/session/1/items/1/evaluate',
        expect.objectContaining({
          function_type: 'rating',
          rating: 5
        })
      )
    })

    it('EVAL_SESS_034: submitEvaluation updates local item state', async () => {
      axios.post.mockResolvedValue({
        data: { evaluation: { rating: 5 } }
      })

      await session.submitEvaluation(1, { rating: 5 })

      expect(session.progress.value.completed).toBe(1)
    })

    it('EVAL_SESS_035: submitEvaluation throws on missing arguments', async () => {
      await expect(session.submitEvaluation(null, {})).rejects.toThrow(
        'Item ID and evaluation data are required'
      )

      await expect(session.submitEvaluation(1, null)).rejects.toThrow(
        'Item ID and evaluation data are required'
      )
    })

    it('EVAL_SESS_036: submitEvaluation sets COMPLETED when all done', async () => {
      // Submit evaluation for both items
      axios.post.mockResolvedValue({
        data: { evaluation: { rating: 5 } }
      })

      await session.submitEvaluation(1, { rating: 5 })
      await session.submitEvaluation(2, { rating: 4 })

      expect(session.status.value).toBe(SESSION_STATUS.COMPLETED)
    })

    it('EVAL_SESS_037: submitEvaluation uses provided function_type', async () => {
      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: [{ id: 1, evaluated: false }] }
      })

      const typedSession = useEvaluationSession(1, 'ranking')
      await typedSession.loadSession()

      axios.post.mockResolvedValue({ data: { evaluation: {} } })

      await typedSession.submitEvaluation(1, { bucket: 'good' })

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ function_type: 'ranking' })
      )
    })
  })

  // ==================== Mark Item Completed ====================

  describe('Mark Item Completed', () => {
    it('EVAL_SESS_038: markItemCompleted updates item and progress', async () => {
      const mockItems = [
        { id: 1, evaluated: false },
        { id: 2, evaluated: false }
      ]

      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: mockItems }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      session.markItemCompleted(1)

      expect(session.progress.value.completed).toBe(1)
      expect(session.progress.value.remaining).toBe(1)
    })

    it('EVAL_SESS_039: markItemCompleted ignores null id', async () => {
      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: [{ id: 1, evaluated: false }] }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      session.markItemCompleted(null)

      expect(session.progress.value.completed).toBe(0)
    })
  })

  // ==================== Reset & Utility ====================

  describe('Reset and Utility', () => {
    it('EVAL_SESS_040: reset clears all state', async () => {
      axios.get.mockResolvedValue({
        data: {
          scenario: { id: 1 },
          config: { type: 'rating' },
          items: [{ id: 1, evaluated: false }]
        }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      session.reset()

      expect(session.items.value).toHaveLength(0)
      expect(session.scenario.value).toBeNull()
      expect(session.config.value).toBeNull()
      expect(session.progress.value.total).toBe(0)
      expect(session.error.value).toBeNull()
    })

    it('EVAL_SESS_041: clearError resets error and status', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Some error' } }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      expect(session.status.value).toBe(SESSION_STATUS.ERROR)

      session.clearError()

      expect(session.error.value).toBeNull()
      expect(session.status.value).toBe(SESSION_STATUS.READY)
    })

    it('EVAL_SESS_042: goToFirstIncomplete navigates correctly', async () => {
      const mockItems = [
        { id: 1, evaluated: true },
        { id: 2, evaluated: false },
        { id: 3, evaluated: true }
      ]

      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: mockItems }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      session.goToItem(2) // Go to last
      const result = session.goToFirstIncomplete()

      expect(result).toBe(true)
      expect(session.currentIndex.value).toBe(1)
    })

    it('EVAL_SESS_043: goToFirstIncomplete returns false when all complete', async () => {
      const mockItems = [
        { id: 1, evaluated: true },
        { id: 2, evaluated: true }
      ]

      axios.get.mockResolvedValue({
        data: { scenario: {}, config: {}, items: mockItems }
      })

      const session = useEvaluationSession(1)
      await session.loadSession()

      const result = session.goToFirstIncomplete()

      expect(result).toBe(false)
    })
  })
})
