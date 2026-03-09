/**
 * useScenarioStats Composable Tests
 *
 * Tests for real-time scenario statistics composable.
 * Validates stats computation, polling, socket event handling, and lifecycle.
 * Test IDs: SCEN_STATS_001 - SCEN_STATS_050
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
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

vi.mock('@/composables/useAuth', () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn(() => 'test-token')
  }))
}))

vi.mock('@/composables/useModelRegistry', () => ({
  useModelRegistry: vi.fn(() => ({
    updateRegistry: vi.fn()
  }))
}))

// Mock Vue lifecycle hooks since we're testing outside a component
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onMounted: vi.fn((cb) => cb()),
    onUnmounted: vi.fn()
  }
})

import axios from 'axios'
import { useScenarioStats } from '@/views/ScenarioManager/composables/useScenarioStats'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createStatsPayload(overrides = {}) {
  return {
    scenario_id: 42,
    function_type: 'ranking',
    kind: 'progress',
    stats: {
      rater_stats: [],
      evaluator_stats: [],
      user_stats: [],
      ...overrides
    }
  }
}

function getSocketHandler(eventName) {
  const calls = mockSocket.on.mock.calls.filter(c => c[0] === eventName)
  return calls.length > 0 ? calls[calls.length - 1][1] : null
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useScenarioStats', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    mockSocket.connected = false
    mockSocket.on.mockReset()
    mockSocket.off.mockReset()
    mockSocket.emit.mockReset()
    // Mock document.addEventListener/removeEventListener
    vi.spyOn(document, 'addEventListener').mockImplementation(() => {})
    vi.spyOn(document, 'removeEventListener').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  // =========================================================================
  // Initial State
  // =========================================================================

  describe('initial state', () => {
    it('SCEN_STATS_001: starts with null/empty values', () => {
      const scenarioId = ref(null)
      const result = useScenarioStats(scenarioId)

      expect(result.stats.value).toBeNull()
      expect(result.raterStats.value).toEqual([])
      expect(result.evaluatorStats.value).toEqual([])
      expect(result.llmStats.value).toEqual([])
      expect(result.humanStats.value).toEqual([])
      expect(result.agreementMetrics.value).toBeNull()
      expect(result.connected.value).toBe(false)
      expect(result.loading.value).toBe(false)
      expect(result.error.value).toBeNull()
      expect(result.functionType.value).toBeNull()
    })

    it('SCEN_STATS_002: overallProgress is 0 when no stats', () => {
      const scenarioId = ref(null)
      const result = useScenarioStats(scenarioId)
      expect(result.overallProgress.value).toBe(0)
    })

    it('SCEN_STATS_003: humanProgress returns zero state', () => {
      const scenarioId = ref(null)
      const result = useScenarioStats(scenarioId)
      expect(result.humanProgress.value).toEqual({ done: 0, total: 0, percent: 0 })
    })

    it('SCEN_STATS_004: llmProgress returns zero state with errors', () => {
      const scenarioId = ref(null)
      const result = useScenarioStats(scenarioId)
      expect(result.llmProgress.value).toEqual({ done: 0, total: 0, errors: 0, percent: 0 })
    })

    it('SCEN_STATS_005: hasHumans and hasLLMs are false initially', () => {
      const scenarioId = ref(null)
      const result = useScenarioStats(scenarioId)
      expect(result.hasHumans.value).toBe(false)
      expect(result.hasLLMs.value).toBe(false)
    })
  })

  // =========================================================================
  // Socket Connection
  // =========================================================================

  describe('socket connection', () => {
    it('SCEN_STATS_006: connects and registers socket handlers when scenarioId is set', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      useScenarioStats(scenarioId)

      await nextTick()

      // Should register event handlers
      const registeredEvents = mockSocket.on.mock.calls.map(c => c[0])
      expect(registeredEvents).toContain('scenario:stats')
      expect(registeredEvents).toContain('scenario:stats_updated')
      expect(registeredEvents).toContain('scenario:error')
      expect(registeredEvents).toContain('connect')
      expect(registeredEvents).toContain('disconnect')
    })

    it('SCEN_STATS_007: subscribes to scenario room when socket is already connected', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      useScenarioStats(scenarioId)

      await nextTick()

      expect(mockSocket.emit).toHaveBeenCalledWith('scenario:subscribe', { scenario_id: 42 })
    })

    it('SCEN_STATS_008: does not subscribe when socket is not connected', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = false
      useScenarioStats(scenarioId)

      await nextTick()

      const subscribeCalls = mockSocket.emit.mock.calls.filter(c => c[0] === 'scenario:subscribe')
      expect(subscribeCalls).toHaveLength(0)
    })
  })

  // =========================================================================
  // Stats Processing - Progress (Ranking/Rating)
  // =========================================================================

  describe('processStatsPayload - progress stats', () => {
    it('SCEN_STATS_009: processes rater_stats and evaluator_stats', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'ranking',
        kind: 'progress',
        stats: {
          rater_stats: [{ username: 'user1', total_threads: 10, done_threads: 5 }],
          evaluator_stats: [
            { username: 'user2', total_threads: 10, done_threads: 8, is_llm: false },
            { username: 'gpt-4', total_threads: 10, done_threads: 10, is_llm: true }
          ]
        }
      })

      expect(result.raterStats.value).toHaveLength(1)
      expect(result.evaluatorStats.value).toHaveLength(2)
      expect(result.llmStats.value).toHaveLength(1)
      expect(result.humanStats.value).toHaveLength(2) // 1 rater + 1 human evaluator
      expect(result.functionType.value).toBe('ranking')
    })

    it('SCEN_STATS_010: computes overallProgress correctly', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'ranking',
        kind: 'progress',
        stats: {
          rater_stats: [{ username: 'user1', total_threads: 10, done_threads: 5 }],
          evaluator_stats: [{ username: 'user2', total_threads: 10, done_threads: 10, is_llm: false }]
        }
      })

      // 15 done out of 20 total = 75%
      expect(result.overallProgress.value).toBe(75)
    })

    it('SCEN_STATS_011: computes humanProgress correctly', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'rating',
        kind: 'progress',
        stats: {
          rater_stats: [{ username: 'user1', total_threads: 10, done_threads: 3 }],
          evaluator_stats: [
            { username: 'user2', total_threads: 10, done_threads: 7, is_llm: false },
            { username: 'gpt', total_threads: 10, done_threads: 10, is_llm: true }
          ]
        }
      })

      expect(result.humanProgress.value).toEqual({ done: 10, total: 20, percent: 50 })
    })

    it('SCEN_STATS_012: computes llmProgress with errors', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'rating',
        kind: 'progress',
        stats: {
          rater_stats: [],
          evaluator_stats: [
            { username: 'llm1', total_threads: 10, done_threads: 6, error_threads: 2, is_llm: true },
            { username: 'llm2', total_threads: 10, done_threads: 8, error_threads: 1, is_llm: true }
          ]
        }
      })

      expect(result.llmProgress.value).toEqual({ done: 14, total: 20, errors: 3, percent: 70 })
    })

    it('SCEN_STATS_013: hasHumans and hasLLMs computed correctly', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'ranking',
        kind: 'progress',
        stats: {
          rater_stats: [{ username: 'user1', total_threads: 10 }],
          evaluator_stats: [{ username: 'gpt', is_llm: true, total_threads: 10 }]
        }
      })

      expect(result.hasHumans.value).toBe(true)
      expect(result.hasLLMs.value).toBe(true)
    })
  })

  // =========================================================================
  // Stats Processing - Authenticity
  // =========================================================================

  describe('processStatsPayload - authenticity stats', () => {
    it('SCEN_STATS_014: processes authenticity stats with user_stats', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'authenticity',
        kind: 'authenticity',
        stats: {
          user_stats: [
            { username: 'user1', role: 'Evaluator', is_llm: false, total_threads: 10, done_threads: 5 },
            { username: 'user2', role: 'Viewer', is_llm: false, total_threads: 10, done_threads: 3 }
          ],
          krippendorff_alpha: 0.75,
          alpha_interpretation: 'substantial',
          overall_accuracy: 0.85
        }
      })

      // Evaluator role goes to raterStats, Viewer goes to evaluatorStats
      expect(result.raterStats.value).toHaveLength(1)
      expect(result.raterStats.value[0].username).toBe('user1')
      expect(result.evaluatorStats.value).toHaveLength(1)
      expect(result.evaluatorStats.value[0].username).toBe('user2')
    })

    it('SCEN_STATS_015: computes agreement metrics with F1 score', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'authenticity',
        kind: 'authenticity',
        stats: {
          user_stats: [
            { username: 'u1', role: 'Evaluator', is_llm: false, fake_correct: 8, fake_incorrect: 2, real_incorrect: 1, real_correct: 9 }
          ],
          krippendorff_alpha: 0.8,
          alpha_interpretation: 'excellent',
          overall_accuracy: 0.9
        }
      })

      expect(result.agreementMetrics.value).toBeDefined()
      expect(result.agreementMetrics.value.alpha).toBe(0.8)
      expect(result.agreementMetrics.value.interpretation).toBe('excellent')
      expect(result.agreementMetrics.value.accuracy).toBe(0.9)
      // F1 = 2 * precision * recall / (precision + recall)
      // precision = 8 / (8+2) = 0.8, recall = 8 / (8+1) = 0.8889
      // F1 = 2 * 0.8 * 0.8889 / (0.8 + 0.8889) ~ 0.8421 => 84.2
      expect(result.agreementMetrics.value.f1Score).toBeCloseTo(84.2, 0)
    })

    it('SCEN_STATS_016: handles zero fake_correct gracefully (F1 = null)', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'authenticity',
        kind: 'authenticity',
        stats: {
          user_stats: [],
          krippendorff_alpha: undefined
        }
      })

      expect(result.agreementMetrics.value.f1Score).toBeNull()
    })
  })

  // =========================================================================
  // stats_updated Event
  // =========================================================================

  describe('stats_updated event', () => {
    it('SCEN_STATS_017: ignores updates for different scenario_id', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats_updated')
      handler({
        scenario_id: 999, // Different scenario
        function_type: 'ranking',
        stats: {
          rater_stats: [{ username: 'x', total_threads: 1, done_threads: 1 }],
          evaluator_stats: []
        }
      })

      // Stats should remain empty
      expect(result.raterStats.value).toEqual([])
    })

    it('SCEN_STATS_018: processes updates for matching scenario_id', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats_updated')
      handler({
        scenario_id: 42,
        function_type: 'ranking',
        stats: {
          rater_stats: [{ username: 'user1', total_threads: 10, done_threads: 10 }],
          evaluator_stats: []
        }
      })

      expect(result.raterStats.value).toHaveLength(1)
    })
  })

  // =========================================================================
  // Error Handling
  // =========================================================================

  describe('error handling', () => {
    it('SCEN_STATS_019: handles socket error events', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:error')
      handler({ error: 'Something went wrong' })

      expect(result.error.value).toBe('Something went wrong')
    })

    it('SCEN_STATS_020: handles socket error with no message', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:error')
      handler({})

      expect(result.error.value).toBe('Unknown error')
    })
  })

  // =========================================================================
  // fetchStats (REST fallback)
  // =========================================================================

  describe('fetchStats', () => {
    it('SCEN_STATS_021: fetches stats via REST API', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          function_type: 'ranking',
          kind: 'progress',
          stats: {
            rater_stats: [{ username: 'u1', total_threads: 5, done_threads: 3 }],
            evaluator_stats: []
          }
        }
      })

      const scenarioId = ref(null)
      const result = useScenarioStats(scenarioId)

      await result.fetchStats(42)

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios/42/stats', {
        headers: { Authorization: 'Bearer test-token' }
      })
      expect(result.raterStats.value).toHaveLength(1)
      expect(result.loading.value).toBe(false)
    })

    it('SCEN_STATS_022: silently handles 404 errors', async () => {
      axios.get.mockRejectedValueOnce({ response: { status: 404 } })

      const scenarioId = ref(null)
      const result = useScenarioStats(scenarioId)

      await result.fetchStats(42)

      expect(result.error.value).toBeNull()
      expect(result.loading.value).toBe(false)
    })

    it('SCEN_STATS_023: sets error for non-404 failures', async () => {
      axios.get.mockRejectedValueOnce({
        response: { status: 500, data: { error: 'Server error' } }
      })

      const scenarioId = ref(null)
      const result = useScenarioStats(scenarioId)

      await result.fetchStats(42)

      expect(result.error.value).toBe('Server error')
      expect(result.loading.value).toBe(false)
    })

    it('SCEN_STATS_024: does nothing when scenarioId is falsy', async () => {
      const scenarioId = ref(null)
      const result = useScenarioStats(scenarioId)

      await result.fetchStats(null)
      expect(axios.get).not.toHaveBeenCalled()
    })
  })

  // =========================================================================
  // refresh
  // =========================================================================

  describe('refresh', () => {
    it('SCEN_STATS_025: calls fetchStats with current scenario id', async () => {
      axios.get.mockResolvedValue({
        data: {
          function_type: 'ranking',
          stats: { rater_stats: [], evaluator_stats: [] }
        }
      })

      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()
      // Clear the initial fetchStats call
      axios.get.mockClear()

      axios.get.mockResolvedValueOnce({
        data: {
          function_type: 'ranking',
          stats: { rater_stats: [], evaluator_stats: [] }
        }
      })

      await result.refresh()

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios/42/stats', expect.any(Object))
    })
  })

  // =========================================================================
  // userStatsList
  // =========================================================================

  describe('userStatsList', () => {
    it('SCEN_STATS_026: formats raters correctly', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'ranking',
        stats: {
          rater_stats: [{
            username: 'rater1',
            user_id: 'uid1',
            total_threads: 10,
            done_threads: 7,
            progressing_threads: 2,
            not_started_threads: 1,
            progress_percent: 70
          }],
          evaluator_stats: []
        }
      })

      const list = result.userStatsList.value
      expect(list).toHaveLength(1)
      expect(list[0].name).toBe('rater1')
      expect(list[0].role).toBe('EVALUATOR')
      expect(list[0].isLLM).toBe(false)
      expect(list[0].completed).toBe(7)
      expect(list[0].total).toBe(10)
      expect(list[0].progress).toBe(70)
    })

    it('SCEN_STATS_027: formats LLM evaluators with model_id', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'rating',
        stats: {
          rater_stats: [],
          evaluator_stats: [{
            username: 'gpt-4',
            user_id: 'llm:gpt-4',
            model_id: 'Global/OpenAI/gpt-4',
            is_llm: true,
            total_threads: 10,
            done_threads: 10,
            error_threads: 0
          }]
        }
      })

      const list = result.userStatsList.value
      expect(list).toHaveLength(1)
      expect(list[0].role).toBe('LLM')
      expect(list[0].isLLM).toBe(true)
      expect(list[0].modelId).toBe('Global/OpenAI/gpt-4')
      expect(list[0].errorCount).toBe(0)
    })

    it('SCEN_STATS_028: extracts model_id from user_id prefix for LLMs', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'rating',
        stats: {
          rater_stats: [],
          evaluator_stats: [{
            username: 'mistral',
            user_id: 'llm:mistral-7b',
            is_llm: true,
            total_threads: 5,
            done_threads: 3
          }]
        }
      })

      const list = result.userStatsList.value
      expect(list[0].modelId).toBe('mistral-7b')
    })

    it('SCEN_STATS_029: combines raters, human evaluators, and LLM evaluators', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'ranking',
        stats: {
          rater_stats: [{ username: 'rater1', total_threads: 10, done_threads: 5 }],
          evaluator_stats: [
            { username: 'eval1', is_llm: false, total_threads: 10, done_threads: 8 },
            { username: 'llm1', is_llm: true, total_threads: 10, done_threads: 10 }
          ]
        }
      })

      const list = result.userStatsList.value
      expect(list).toHaveLength(3)
    })
  })

  // =========================================================================
  // allEvaluatorStats computed
  // =========================================================================

  describe('allEvaluatorStats', () => {
    it('SCEN_STATS_030: combines human and LLM evaluators with humans first', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'rating',
        stats: {
          rater_stats: [],
          evaluator_stats: [
            { username: 'llm1', is_llm: true },
            { username: 'human1', is_llm: false },
            { username: 'llm2', is_llm: true },
            { username: 'human2', is_llm: false }
          ]
        }
      })

      const all = result.allEvaluatorStats.value
      expect(all).toHaveLength(4)
      // Humans first, then LLMs
      expect(all[0].username).toBe('human1')
      expect(all[1].username).toBe('human2')
      expect(all[2].username).toBe('llm1')
      expect(all[3].username).toBe('llm2')
    })
  })

  // =========================================================================
  // Agreement Metrics for ranking/rating
  // =========================================================================

  describe('agreement metrics (ranking/rating)', () => {
    it('SCEN_STATS_031: extracts krippendorff_alpha for ranking', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'ranking',
        kind: 'progress',
        stats: {
          rater_stats: [],
          evaluator_stats: [],
          krippendorff_alpha: 0.65,
          alpha_interpretation: 'moderate'
        }
      })

      expect(result.agreementMetrics.value).toEqual({
        alpha: 0.65,
        interpretation: 'moderate',
        accuracy: null
      })
    })
  })

  // =========================================================================
  // Model Registry Integration
  // =========================================================================

  describe('model registry', () => {
    it('SCEN_STATS_032: calls updateRegistry when model_registry is present', async () => {
      const { useModelRegistry } = await import('@/composables/useModelRegistry')
      const mockUpdateRegistry = vi.fn()
      useModelRegistry.mockReturnValue({ updateRegistry: mockUpdateRegistry })

      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      const registryData = { 'model-1': { display_name: 'Test Model' } }
      handler({
        scenario_id: 42,
        function_type: 'ranking',
        stats: {
          rater_stats: [],
          evaluator_stats: [],
          model_registry: registryData
        }
      })

      expect(mockUpdateRegistry).toHaveBeenCalledWith(registryData)
    })
  })

  // =========================================================================
  // Disconnect
  // =========================================================================

  describe('disconnect', () => {
    it('SCEN_STATS_033: cleans up socket handlers on disconnect', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      result.disconnect()

      // Should have called off for all event handlers
      const offEvents = mockSocket.off.mock.calls.map(c => c[0])
      expect(offEvents).toContain('scenario:stats')
      expect(offEvents).toContain('scenario:stats_updated')
      expect(offEvents).toContain('scenario:error')
      expect(offEvents).toContain('connect')
      expect(offEvents).toContain('disconnect')
    })

    it('SCEN_STATS_034: emits unsubscribe when actively subscribed', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      result.disconnect()

      expect(mockSocket.emit).toHaveBeenCalledWith('scenario:unsubscribe', { scenario_id: 42 })
    })
  })

  // =========================================================================
  // Edge Cases
  // =========================================================================

  describe('edge cases', () => {
    it('SCEN_STATS_035: overallProgress returns 0 when totalThreads is 0', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'ranking',
        stats: {
          rater_stats: [{ username: 'u1', total_threads: 0, done_threads: 0 }],
          evaluator_stats: []
        }
      })

      expect(result.overallProgress.value).toBe(0)
    })

    it('SCEN_STATS_036: handles voted_count fallback for done_threads', async () => {
      const scenarioId = ref(42)
      mockSocket.connected = true
      const result = useScenarioStats(scenarioId)

      await nextTick()

      const handler = getSocketHandler('scenario:stats')
      handler({
        scenario_id: 42,
        function_type: 'ranking',
        stats: {
          rater_stats: [{ username: 'u1', total_threads: 10, voted_count: 7 }],
          evaluator_stats: []
        }
      })

      // Should use voted_count as fallback
      expect(result.overallProgress.value).toBe(70)
    })

    it('SCEN_STATS_037: connect does nothing when scenarioId is null', () => {
      const scenarioId = ref(null)
      const result = useScenarioStats(scenarioId)

      result.connect(null)

      // Should not emit or register handlers
      expect(mockSocket.on).not.toHaveBeenCalled()
    })
  })
})
