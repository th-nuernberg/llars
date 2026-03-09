/**
 * useRatingEvaluation Composable Tests
 *
 * Tests for the rating-specific evaluation composable that extends useEvaluationSession.
 * Test IDs: RATE_EVAL_001 - RATE_EVAL_035
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'

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

let useRatingEvaluation

describe('useRatingEvaluation Composable', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    mockSocket.on.mockReset()
    mockSocket.off.mockReset()
    mockSocket.emit.mockReset()
    mockSocket.connected = false

    // Mock the session loading triggered by onMounted
    axios.get.mockResolvedValue({
      data: { scenario: { id: 1 }, config: {}, items: [] }
    })

    const module = await import('@/composables/useRatingEvaluation')
    useRatingEvaluation = module.useRatingEvaluation
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('RATE_EVAL_001: exports useRatingEvaluation function', () => {
      expect(typeof useRatingEvaluation).toBe('function')
    })

    it('RATE_EVAL_002: returns all expected properties', () => {
      const result = useRatingEvaluation(1)

      // Base session properties
      expect(result).toHaveProperty('status')
      expect(result).toHaveProperty('items')
      expect(result).toHaveProperty('currentIndex')

      // Rating-specific state
      expect(result).toHaveProperty('features')
      expect(result).toHaveProperty('currentFeatureIndex')
      expect(result).toHaveProperty('messages')
      expect(result).toHaveProperty('featureTypes')
      expect(result).toHaveProperty('activeFeatureType')
      expect(result).toHaveProperty('ratingInProgress')

      // Computed
      expect(result).toHaveProperty('currentThread')
      expect(result).toHaveProperty('currentFeature')
      expect(result).toHaveProperty('hasNextFeature')
      expect(result).toHaveProperty('hasPrevFeature')
      expect(result).toHaveProperty('featureProgress')
      expect(result).toHaveProperty('featuresByType')
      expect(result).toHaveProperty('currentFeatureType')

      // Feature Navigation
      expect(result).toHaveProperty('goToFeature')
      expect(result).toHaveProperty('goNextFeature')
      expect(result).toHaveProperty('goPrevFeature')
      expect(result).toHaveProperty('goToFirstIncompleteFeature')
      expect(result).toHaveProperty('selectFeatureByType')

      // Actions
      expect(result).toHaveProperty('loadThreadFeatures')
      expect(result).toHaveProperty('rateFeature')
      expect(result).toHaveProperty('markThreadComplete')

      // Edited content
      expect(result).toHaveProperty('editedContent')
      expect(result).toHaveProperty('setEditedContent')
      expect(result).toHaveProperty('hasEdits')
      expect(result).toHaveProperty('getEditedContent')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('RATE_EVAL_003: features is empty initially', () => {
      const result = useRatingEvaluation(1)

      expect(result.features.value).toEqual([])
    })

    it('RATE_EVAL_004: currentFeature is null with no features', () => {
      const result = useRatingEvaluation(1)

      expect(result.currentFeature.value).toBeNull()
    })

    it('RATE_EVAL_005: ratingInProgress is false initially', () => {
      const result = useRatingEvaluation(1)

      expect(result.ratingInProgress.value).toBe(false)
    })

    it('RATE_EVAL_006: currentFeatureIndex starts at 0', () => {
      const result = useRatingEvaluation(1)

      expect(result.currentFeatureIndex.value).toBe(0)
    })
  })

  // ==================== Feature Navigation ====================

  describe('Feature Navigation', () => {
    let rating

    beforeEach(() => {
      rating = useRatingEvaluation(1)
    })

    it('RATE_EVAL_007: goToFeature navigates to valid index', async () => {
      // We need to directly set features since they are readonly
      // The composable uses readonly(features), but the internal ref is writable
      // We test via loadThreadFeatures instead
      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 1, evaluated: false },
            { id: 2, evaluated: false },
            { id: 3, evaluated: false }
          ],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)

      const result = rating.goToFeature(2)

      expect(result).toBe(true)
      expect(rating.currentFeatureIndex.value).toBe(2)
    })

    it('RATE_EVAL_008: goToFeature rejects invalid index', async () => {
      axios.get.mockResolvedValueOnce({
        data: { features: [{ id: 1 }], messages: [], feature_types: [] }
      })

      await rating.loadThreadFeatures(1)

      const result = rating.goToFeature(5)

      expect(result).toBe(false)
    })

    it('RATE_EVAL_009: goToFeature rejects negative index', async () => {
      axios.get.mockResolvedValueOnce({
        data: { features: [{ id: 1 }], messages: [], feature_types: [] }
      })

      await rating.loadThreadFeatures(1)

      const result = rating.goToFeature(-1)

      expect(result).toBe(false)
    })

    it('RATE_EVAL_010: goNextFeature advances to next feature', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 1, evaluated: true },
            { id: 2, evaluated: false }
          ],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)
      rating.goToFeature(0)

      const result = rating.goNextFeature()

      expect(result).toBe(true)
      expect(rating.currentFeatureIndex.value).toBe(1)
    })

    it('RATE_EVAL_011: goNextFeature returns false at last feature', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          features: [{ id: 1, evaluated: true }],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)

      const result = rating.goNextFeature()

      expect(result).toBe(false)
    })

    it('RATE_EVAL_012: goPrevFeature goes to previous feature', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 1, evaluated: false },
            { id: 2, evaluated: false }
          ],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)
      rating.goToFeature(1)

      const result = rating.goPrevFeature()

      expect(result).toBe(true)
      expect(rating.currentFeatureIndex.value).toBe(0)
    })

    it('RATE_EVAL_013: goPrevFeature returns false at first feature', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          features: [{ id: 1, evaluated: false }],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)

      const result = rating.goPrevFeature()

      expect(result).toBe(false)
    })

    it('RATE_EVAL_014: goToFirstIncompleteFeature finds first unevaluated', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 1, evaluated: true },
            { id: 2, evaluated: false },
            { id: 3, evaluated: false }
          ],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)
      rating.goToFeature(2)

      const result = rating.goToFirstIncompleteFeature()

      expect(result).toBe(true)
      expect(rating.currentFeatureIndex.value).toBe(1)
    })

    it('RATE_EVAL_015: goToFirstIncompleteFeature returns false when all complete', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 1, evaluated: true },
            { id: 2, evaluated: true }
          ],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)

      const result = rating.goToFirstIncompleteFeature()

      expect(result).toBe(false)
    })
  })

  // ==================== Feature Progress ====================

  describe('Feature Progress', () => {
    it('RATE_EVAL_016: featureProgress tracks completion', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 1, evaluated: true },
            { id: 2, evaluated: false },
            { id: 3, evaluated: true }
          ],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)

      expect(rating.featureProgress.value.total).toBe(3)
      expect(rating.featureProgress.value.completed).toBe(2)
      expect(rating.featureProgress.value.percent).toBe(67)
    })

    it('RATE_EVAL_017: featureProgress is 0 for empty features', () => {
      const rating = useRatingEvaluation(1)

      expect(rating.featureProgress.value.total).toBe(0)
      expect(rating.featureProgress.value.completed).toBe(0)
      expect(rating.featureProgress.value.percent).toBe(0)
    })
  })

  // ==================== Features By Type ====================

  describe('Features By Type', () => {
    it('RATE_EVAL_018: featuresByType groups features correctly', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 1, feature_type: 'summary', evaluated: false },
            { id: 2, feature_type: 'summary', evaluated: false },
            { id: 3, feature_type: 'translation', evaluated: false }
          ],
          messages: [],
          feature_types: ['summary', 'translation']
        }
      })

      await rating.loadThreadFeatures(1)

      expect(rating.featuresByType.value.summary).toHaveLength(2)
      expect(rating.featuresByType.value.translation).toHaveLength(1)
    })

    it('RATE_EVAL_019: selectFeatureByType navigates to first feature of type', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 1, feature_type: 'summary', evaluated: false },
            { id: 2, feature_type: 'translation', evaluated: false },
            { id: 3, feature_type: 'translation', evaluated: false }
          ],
          messages: [],
          feature_types: ['summary', 'translation']
        }
      })

      await rating.loadThreadFeatures(1)

      rating.selectFeatureByType('translation')

      expect(rating.activeFeatureType.value).toBe('translation')
      expect(rating.currentFeatureIndex.value).toBe(1)
    })
  })

  // ==================== Rate Feature ====================

  describe('Rate Feature', () => {
    it('RATE_EVAL_020: rateFeature calls correct endpoint', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {
          features: [{ id: 10, evaluated: false }],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)

      axios.post.mockResolvedValue({
        data: { evaluation: { rating: 4 } }
      })

      await rating.rateFeature(10, 4, { autoAdvance: false })

      expect(axios.post).toHaveBeenCalledWith(
        '/api/evaluation/session/1/features/10/rate',
        expect.objectContaining({ rating: 4 })
      )
    })

    it('RATE_EVAL_021: rateFeature updates local feature state', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 10, evaluated: false },
            { id: 11, evaluated: false }
          ],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)

      axios.post.mockResolvedValue({
        data: { evaluation: { rating: 4 } }
      })

      await rating.rateFeature(10, 4, { autoAdvance: false })

      expect(rating.features.value[0].evaluated).toBe(true)
      expect(rating.features.value[0].rating).toBe(4)
    })

    it('RATE_EVAL_022: rateFeature throws on missing arguments', async () => {
      const rating = useRatingEvaluation(1)

      await expect(rating.rateFeature(null, 4)).rejects.toThrow(
        'Feature ID and rating are required'
      )

      await expect(rating.rateFeature(1, null)).rejects.toThrow(
        'Feature ID and rating are required'
      )
    })

    it('RATE_EVAL_023: rateFeature auto-advances to next feature', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 10, evaluated: false },
            { id: 11, evaluated: false }
          ],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)

      axios.post.mockResolvedValue({
        data: { evaluation: { rating: 5 } }
      })

      await rating.rateFeature(10, 5, { autoAdvance: true })

      expect(rating.currentFeatureIndex.value).toBe(1)
    })

    it('RATE_EVAL_024: rateFeature sends edited content', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {
          features: [{ id: 10, evaluated: false }],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)

      axios.post.mockResolvedValue({
        data: { evaluation: { rating: 3 } }
      })

      await rating.rateFeature(10, 3, {
        editedText: 'corrected text',
        autoAdvance: false
      })

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          edited_content: 'corrected text'
        })
      )
    })

    it('RATE_EVAL_025: rateFeature sends comment', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {
          features: [{ id: 10, evaluated: false }],
          messages: [],
          feature_types: []
        }
      })

      await rating.loadThreadFeatures(1)

      axios.post.mockResolvedValue({
        data: { evaluation: { rating: 2 } }
      })

      await rating.rateFeature(10, 2, {
        comment: 'needs improvement',
        autoAdvance: false
      })

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          comment: 'needs improvement'
        })
      )
    })
  })

  // ==================== Edited Content ====================

  describe('Edited Content', () => {
    it('RATE_EVAL_026: setEditedContent stores text', () => {
      const rating = useRatingEvaluation(1)

      rating.setEditedContent(10, 'edited text')

      expect(rating.getEditedContent(10)).toBe('edited text')
    })

    it('RATE_EVAL_027: hasEdits returns true for edited feature', () => {
      const rating = useRatingEvaluation(1)

      rating.setEditedContent(10, 'some edit')

      expect(rating.hasEdits(10)).toBe(true)
    })

    it('RATE_EVAL_028: hasEdits returns false for unedited feature', () => {
      const rating = useRatingEvaluation(1)

      expect(rating.hasEdits(10)).toBe(false)
    })

    it('RATE_EVAL_029: getEditedContent returns null for unedited feature', () => {
      const rating = useRatingEvaluation(1)

      expect(rating.getEditedContent(99)).toBeNull()
    })
  })

  // ==================== Load Thread Features ====================

  describe('Load Thread Features', () => {
    it('RATE_EVAL_030: loadThreadFeatures calls correct endpoint', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {
          features: [{ id: 1, evaluated: false }],
          messages: [{ sender: 'user', text: 'hello' }],
          feature_types: ['summary']
        }
      })

      await rating.loadThreadFeatures(42)

      expect(axios.get).toHaveBeenCalledWith(
        '/api/evaluation/session/1/threads/42/features'
      )
    })

    it('RATE_EVAL_031: loadThreadFeatures populates features and messages', async () => {
      const rating = useRatingEvaluation(1)

      const mockFeatures = [
        { id: 1, evaluated: false },
        { id: 2, evaluated: true }
      ]
      const mockMessages = [{ sender: 'user', text: 'hello' }]

      axios.get.mockResolvedValueOnce({
        data: {
          features: mockFeatures,
          messages: mockMessages,
          feature_types: ['summary']
        }
      })

      await rating.loadThreadFeatures(1)

      expect(rating.features.value).toHaveLength(2)
      expect(rating.messages.value).toHaveLength(1)
      expect(rating.featureTypes.value).toEqual(['summary'])
    })

    it('RATE_EVAL_032: loadThreadFeatures handles empty response', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {}
      })

      await rating.loadThreadFeatures(1)

      expect(rating.features.value).toEqual([])
      expect(rating.messages.value).toEqual([])
    })

    it('RATE_EVAL_033: loadThreadFeatures handles API error', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockRejectedValueOnce(new Error('Network error'))

      await rating.loadThreadFeatures(1)

      expect(rating.features.value).toEqual([])
      expect(rating.messages.value).toEqual([])
    })

    it('RATE_EVAL_034: loadThreadFeatures skips when no threadId', async () => {
      const rating = useRatingEvaluation(1)

      await rating.loadThreadFeatures(null)

      // No API call should be made for the features endpoint
      // Only the initial session load from onMounted
      const featureCalls = axios.get.mock.calls.filter(
        call => call[0].includes('/threads/')
      )
      expect(featureCalls).toHaveLength(0)
    })
  })

  // ==================== Current Feature Type ====================

  describe('Current Feature Type', () => {
    it('RATE_EVAL_035: currentFeatureType returns feature type', async () => {
      const rating = useRatingEvaluation(1)

      axios.get.mockResolvedValueOnce({
        data: {
          features: [
            { id: 1, feature_type: 'summary', evaluated: false }
          ],
          messages: [],
          feature_types: ['summary']
        }
      })

      await rating.loadThreadFeatures(1)

      expect(rating.currentFeatureType.value).toBe('summary')
    })
  })
})
