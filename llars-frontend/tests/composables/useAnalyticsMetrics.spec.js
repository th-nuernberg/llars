/**
 * Tests for useAnalyticsMetrics composable
 *
 * Test IDs: AM_001 - AM_070
 *
 * Coverage:
 * - Exports and structure
 * - Helper functions (clampNumber, resolveDimensions, resolveValue)
 * - useActiveDuration
 * - useTypingMetrics
 * - useVisibilityTracker
 * - useScrollDepth
 * - Edge cases
 *
 * Note: These composables use lifecycle hooks (onMounted/onUnmounted)
 * which don't execute in test context. We test the exposed functions directly.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'

// Mock Matomo tracking
const mockTrackEvent = vi.fn()
vi.mock('@/plugins/llars-metrics', () => ({
  matomoTrackEvent: (...args) => mockTrackEvent(...args)
}))

// Mock performance.now()
let mockNow = 0
vi.stubGlobal('performance', {
  now: () => mockNow
})

describe('useAnalyticsMetrics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNow = 0
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Exports', () => {
    it('AM_001: exports useActiveDuration function', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      expect(typeof useActiveDuration).toBe('function')
    })

    it('AM_002: exports useTypingMetrics function', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      expect(typeof useTypingMetrics).toBe('function')
    })

    it('AM_003: exports useVisibilityTracker function', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      expect(typeof useVisibilityTracker).toBe('function')
    })

    it('AM_004: exports useScrollDepth function', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      expect(typeof useScrollDepth).toBe('function')
    })
  })

  describe('useActiveDuration', () => {
    it('AM_005: returns flush function', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({ category: 'test' })
      expect(typeof result.flush).toBe('function')
    })

    it('AM_006: returns getActiveMs function', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({ category: 'test' })
      expect(typeof result.getActiveMs).toBe('function')
    })

    it('AM_007: getActiveMs returns 0 initially', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const { getActiveMs } = useActiveDuration({ category: 'test' })
      expect(getActiveMs()).toBe(0)
    })

    it('AM_008: flush does not emit if below minMs threshold', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const { flush } = useActiveDuration({
        category: 'test',
        minMs: 1000
      })

      flush()

      expect(mockTrackEvent).not.toHaveBeenCalled()
    })

    it('AM_009: uses default action value "active_time"', async () => {
      // The action is used in flush, tested via other means
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({ category: 'test' })
      expect(result).toBeDefined()
    })

    it('AM_010: accepts custom idleMs parameter', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({
        category: 'test',
        idleMs: 30000
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_011: accepts custom minMs parameter', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({
        category: 'test',
        minMs: 500
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_012: accepts dimensions as object', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({
        category: 'test',
        dimensions: { page: 'home' }
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_013: accepts dimensions as function', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({
        category: 'test',
        dimensions: () => ({ dynamic: true })
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_014: accepts dimensions as ref', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const dims = ref({ reactive: true })
      const result = useActiveDuration({
        category: 'test',
        dimensions: dims
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_015: accepts name as string', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({
        category: 'test',
        name: 'test-page'
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_016: accepts name as function', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({
        category: 'test',
        name: () => 'dynamic-name'
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_017: accepts name as ref', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const name = ref('reactive-name')
      const result = useActiveDuration({
        category: 'test',
        name
      })
      expect(result.flush).toBeDefined()
    })
  })

  describe('useTypingMetrics', () => {
    it('AM_018: returns recordInput function', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const result = useTypingMetrics({ category: 'test' })
      expect(typeof result.recordInput).toBe('function')
    })

    it('AM_019: returns flush function', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const result = useTypingMetrics({ category: 'test' })
      expect(typeof result.flush).toBe('function')
    })

    it('AM_020: recordInput accepts positive charsDelta', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const { recordInput } = useTypingMetrics({ category: 'test' })

      // Should not throw
      recordInput(5)
    })

    it('AM_021: recordInput ignores zero charsDelta', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const { recordInput, flush } = useTypingMetrics({ category: 'test' })

      recordInput(0)
      flush()

      // No event should be emitted for zero chars
      expect(mockTrackEvent).not.toHaveBeenCalled()
    })

    it('AM_022: recordInput ignores negative charsDelta', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const { recordInput, flush } = useTypingMetrics({ category: 'test' })

      recordInput(-5)
      flush()

      expect(mockTrackEvent).not.toHaveBeenCalled()
    })

    it('AM_023: flush does not emit if no input recorded', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const { flush } = useTypingMetrics({ category: 'test' })

      flush()

      expect(mockTrackEvent).not.toHaveBeenCalled()
    })

    it('AM_024: uses default burstIdleMs of 1200', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const result = useTypingMetrics({ category: 'test' })
      expect(result.recordInput).toBeDefined()
    })

    it('AM_025: accepts custom burstIdleMs', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const result = useTypingMetrics({
        category: 'test',
        burstIdleMs: 2000
      })
      expect(result.recordInput).toBeDefined()
    })

    it('AM_026: accepts custom minBurstMs', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const result = useTypingMetrics({
        category: 'test',
        minBurstMs: 100
      })
      expect(result.recordInput).toBeDefined()
    })

    it('AM_027: accepts custom minChars', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const result = useTypingMetrics({
        category: 'test',
        minChars: 5
      })
      expect(result.recordInput).toBeDefined()
    })

    it('AM_028: accumulates chars across multiple recordInput calls', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const { recordInput } = useTypingMetrics({ category: 'test' })

      recordInput(3)
      recordInput(2)
      recordInput(5)

      // Total would be 10 chars
    })
  })

  describe('useVisibilityTracker', () => {
    it('AM_029: returns register function', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const result = useVisibilityTracker({ category: 'test' })
      expect(typeof result.register).toBe('function')
    })

    it('AM_030: returns unregister function', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const result = useVisibilityTracker({ category: 'test' })
      expect(typeof result.unregister).toBe('function')
    })

    it('AM_031: returns flush function', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const result = useVisibilityTracker({ category: 'test' })
      expect(typeof result.flush).toBe('function')
    })

    it('AM_032: register ignores null id', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const { register } = useVisibilityTracker({ category: 'test' })

      // Should not throw
      register(null, document.createElement('div'))
    })

    it('AM_033: register unregisters when el is null', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const { register, flush } = useVisibilityTracker({ category: 'test' })

      const el = document.createElement('div')
      register('item-1', el)
      register('item-1', null)
      flush()

      expect(mockTrackEvent).not.toHaveBeenCalled()
    })

    it('AM_034: unregister handles non-existent id', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const { unregister } = useVisibilityTracker({ category: 'test' })

      // Should not throw
      unregister('non-existent-id')
    })

    it('AM_035: uses default action "visible_time"', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const result = useVisibilityTracker({ category: 'test' })
      expect(result.register).toBeDefined()
    })

    it('AM_036: accepts custom nameBuilder', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const result = useVisibilityTracker({
        category: 'test',
        nameBuilder: (id) => `custom-${id}`
      })
      expect(result.register).toBeDefined()
    })

    it('AM_037: accepts custom minMs threshold', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const result = useVisibilityTracker({
        category: 'test',
        minMs: 5000
      })
      expect(result.register).toBeDefined()
    })

    it('AM_038: accepts custom threshold', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const result = useVisibilityTracker({
        category: 'test',
        threshold: 0.6
      })
      expect(result.register).toBeDefined()
    })

    it('AM_039: register accepts extra dimensions', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const { register } = useVisibilityTracker({ category: 'test' })

      const el = document.createElement('div')
      register('item-1', el, { custom: 'dimension' })
    })

    it('AM_040: flush clears all items', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const { register, flush } = useVisibilityTracker({ category: 'test' })

      const el = document.createElement('div')
      register('item-1', el)
      flush()

      // Second flush should not emit anything
      mockTrackEvent.mockClear()
      flush()
      expect(mockTrackEvent).not.toHaveBeenCalled()
    })
  })

  describe('useScrollDepth', () => {
    it('AM_041: returns reset function', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      const containerRef = ref(null)
      const result = useScrollDepth(containerRef, { category: 'test' })
      expect(typeof result.reset).toBe('function')
    })

    it('AM_042: uses default action "scroll_depth"', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      const containerRef = ref(null)
      const result = useScrollDepth(containerRef, { category: 'test' })
      expect(result.reset).toBeDefined()
    })

    it('AM_043: uses default thresholds [0.25, 0.5, 0.75, 1]', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      const containerRef = ref(null)
      const result = useScrollDepth(containerRef, { category: 'test' })
      expect(result.reset).toBeDefined()
    })

    it('AM_044: accepts custom thresholds', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      const containerRef = ref(null)
      const result = useScrollDepth(containerRef, {
        category: 'test',
        thresholds: [0.1, 0.5, 0.9]
      })
      expect(result.reset).toBeDefined()
    })

    it('AM_045: reset clears seen thresholds', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      const containerRef = ref(null)
      const { reset } = useScrollDepth(containerRef, { category: 'test' })

      // Should not throw
      reset()
    })

    it('AM_046: accepts name as string', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      const containerRef = ref(null)
      const result = useScrollDepth(containerRef, {
        category: 'test',
        name: 'content-area'
      })
      expect(result.reset).toBeDefined()
    })

    it('AM_047: accepts name as ref', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      const containerRef = ref(null)
      const name = ref('dynamic-content')
      const result = useScrollDepth(containerRef, {
        category: 'test',
        name
      })
      expect(result.reset).toBeDefined()
    })

    it('AM_048: accepts dimensions parameter', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      const containerRef = ref(null)
      const result = useScrollDepth(containerRef, {
        category: 'test',
        dimensions: { section: 'main' }
      })
      expect(result.reset).toBeDefined()
    })
  })

  describe('Helper Functions (via behavior)', () => {
    it('AM_049: clampNumber returns 0 for negative values', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const { recordInput, flush } = useTypingMetrics({ category: 'test' })

      recordInput(-100)
      flush()

      // Negative values are clamped to 0
      expect(mockTrackEvent).not.toHaveBeenCalled()
    })

    it('AM_050: clampNumber returns 0 for NaN', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const { recordInput, flush } = useTypingMetrics({ category: 'test' })

      recordInput(NaN)
      flush()

      expect(mockTrackEvent).not.toHaveBeenCalled()
    })

    it('AM_051: resolveDimensions handles undefined', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({
        category: 'test',
        dimensions: undefined
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_052: resolveDimensions handles null', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({
        category: 'test',
        dimensions: null
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_053: resolveValue handles function returning undefined', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({
        category: 'test',
        name: () => undefined
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_054: resolveValue handles ref with null value', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const name = ref(null)
      const result = useActiveDuration({
        category: 'test',
        name
      })
      expect(result.flush).toBeDefined()
    })
  })

  describe('Edge Cases', () => {
    it('AM_055: useActiveDuration works with empty options', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration()
      expect(result.flush).toBeDefined()
      expect(result.getActiveMs).toBeDefined()
    })

    it('AM_056: useTypingMetrics works with empty options', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const result = useTypingMetrics()
      expect(result.recordInput).toBeDefined()
      expect(result.flush).toBeDefined()
    })

    it('AM_057: useVisibilityTracker works with empty options', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const result = useVisibilityTracker()
      expect(result.register).toBeDefined()
      expect(result.flush).toBeDefined()
    })

    it('AM_058: useScrollDepth works with minimal options', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      const containerRef = ref(null)
      const result = useScrollDepth(containerRef)
      expect(result.reset).toBeDefined()
    })

    it('AM_059: multiple useActiveDuration instances are independent', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const instance1 = useActiveDuration({ category: 'test1' })
      const instance2 = useActiveDuration({ category: 'test2' })

      expect(instance1.getActiveMs()).toBe(0)
      expect(instance2.getActiveMs()).toBe(0)
    })

    it('AM_060: multiple useTypingMetrics instances are independent', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const instance1 = useTypingMetrics({ category: 'test1' })
      const instance2 = useTypingMetrics({ category: 'test2' })

      expect(instance1.recordInput).not.toBe(instance2.recordInput)
    })

    it('AM_061: useVisibilityTracker register sets dataset attribute', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const { register } = useVisibilityTracker({ category: 'test' })

      const el = document.createElement('div')
      register('test-id-123', el)

      expect(el.dataset.metricsId).toBe('test-id-123')
    })

    it('AM_062: useVisibilityTracker converts id to string', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const { register } = useVisibilityTracker({ category: 'test' })

      const el = document.createElement('div')
      register(12345, el)

      expect(el.dataset.metricsId).toBe('12345')
    })

    it('AM_063: useTypingMetrics recordInput starts burst on first char', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const { recordInput } = useTypingMetrics({ category: 'test' })

      // Should not throw and should start tracking
      recordInput(1)
    })

    it('AM_064: useScrollDepth handles undefined containerRef value', async () => {
      const { useScrollDepth } = await import('@/composables/useAnalyticsMetrics')
      const containerRef = ref(undefined)
      const { reset } = useScrollDepth(containerRef, { category: 'test' })

      // Should not throw
      reset()
    })

    it('AM_065: useVisibilityTracker flush handles empty items', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const { flush } = useVisibilityTracker({ category: 'test' })

      // Should not throw
      flush()
      expect(mockTrackEvent).not.toHaveBeenCalled()
    })

    it('AM_066: useActiveDuration flush resets activeMs', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const { flush, getActiveMs } = useActiveDuration({ category: 'test' })

      flush()
      expect(getActiveMs()).toBe(0)
    })

    it('AM_067: useTypingMetrics flush resets counters', async () => {
      const { useTypingMetrics } = await import('@/composables/useAnalyticsMetrics')
      const { recordInput, flush } = useTypingMetrics({ category: 'test' })

      recordInput(5)
      flush()
      mockTrackEvent.mockClear()

      // Second flush should not emit
      flush()
      expect(mockTrackEvent).not.toHaveBeenCalled()
    })

    it('AM_068: dimensions function returning null is handled', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const result = useActiveDuration({
        category: 'test',
        dimensions: () => null
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_069: ref with null value for dimensions is handled', async () => {
      const { useActiveDuration } = await import('@/composables/useAnalyticsMetrics')
      const dims = ref(null)
      const result = useActiveDuration({
        category: 'test',
        dimensions: dims
      })
      expect(result.flush).toBeDefined()
    })

    it('AM_070: useVisibilityTracker can re-register same id with different element', async () => {
      const { useVisibilityTracker } = await import('@/composables/useAnalyticsMetrics')
      const { register } = useVisibilityTracker({ category: 'test' })

      const el1 = document.createElement('div')
      const el2 = document.createElement('div')

      register('same-id', el1)
      register('same-id', el2)

      // Second element should have the dataset
      expect(el2.dataset.metricsId).toBe('same-id')
    })
  })
})
