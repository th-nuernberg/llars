/**
 * useDimensionalRating Composable Tests
 *
 * Tests for the multi-dimensional item rating composable.
 * Test IDs: DIM_RATE_001 - DIM_RATE_040
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

import axios from 'axios'

let useDimensionalRating

describe('useDimensionalRating Composable', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    vi.useFakeTimers()

    const module = await import('@/composables/useDimensionalRating')
    useDimensionalRating = module.useDimensionalRating
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('DIM_RATE_001: exports useDimensionalRating function', () => {
      expect(typeof useDimensionalRating).toBe('function')
    })

    it('DIM_RATE_002: returns all expected properties', () => {
      const scenarioId = ref(1)
      const result = useDimensionalRating(scenarioId)

      // State
      expect(result).toHaveProperty('items')
      expect(result).toHaveProperty('currentItem')
      expect(result).toHaveProperty('currentItemIndex')
      expect(result).toHaveProperty('messages')
      expect(result).toHaveProperty('content')
      expect(result).toHaveProperty('config')
      expect(result).toHaveProperty('dimensionRatings')
      expect(result).toHaveProperty('feedback')
      expect(result).toHaveProperty('existingRating')
      expect(result).toHaveProperty('autoSaveEnabled')

      // Loading states
      expect(result).toHaveProperty('loading')
      expect(result).toHaveProperty('loadingItem')
      expect(result).toHaveProperty('submitting')
      expect(result).toHaveProperty('saving')
      expect(result).toHaveProperty('error')

      // Computed
      expect(result).toHaveProperty('dimensions')
      expect(result).toHaveProperty('scaleMin')
      expect(result).toHaveProperty('scaleMax')
      expect(result).toHaveProperty('scaleStep')
      expect(result).toHaveProperty('scaleLabels')
      expect(result).toHaveProperty('overallScore')
      expect(result).toHaveProperty('ratedDimensionCount')
      expect(result).toHaveProperty('canSubmit')
      expect(result).toHaveProperty('progress')
      expect(result).toHaveProperty('hasNext')
      expect(result).toHaveProperty('hasPrev')
      expect(result).toHaveProperty('currentItemStatus')

      // Methods
      expect(result).toHaveProperty('loadConfig')
      expect(result).toHaveProperty('loadItems')
      expect(result).toHaveProperty('loadItem')
      expect(result).toHaveProperty('setDimensionRating')
      expect(result).toHaveProperty('submitRating')
      expect(result).toHaveProperty('goToItem')
      expect(result).toHaveProperty('goNext')
      expect(result).toHaveProperty('goPrev')
      expect(result).toHaveProperty('findNextUnevaluated')
      expect(result).toHaveProperty('reset')
    })
  })

  // ==================== Dimensions from Config ====================

  describe('Dimension Initialization', () => {
    it('DIM_RATE_003: dimensions derived from config', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'coherence', name: { de: 'Kohaerenz' }, weight: 0.25 },
          { id: 'fluency', name: { de: 'Fluessigkeit' }, weight: 0.25 }
        ],
        min: 1, max: 5, step: 1
      }

      expect(rating.dimensions.value).toHaveLength(2)
      expect(rating.dimensions.value[0].id).toBe('coherence')
      expect(rating.dimensions.value[1].id).toBe('fluency')
    })

    it('DIM_RATE_004: dimensions empty when no config', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      expect(rating.dimensions.value).toEqual([])
    })

    it('DIM_RATE_005: scaleMin defaults to 1', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      expect(rating.scaleMin.value).toBe(1)
    })

    it('DIM_RATE_006: scaleMax defaults to 5', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      expect(rating.scaleMax.value).toBe(5)
    })

    it('DIM_RATE_007: scaleStep defaults to 1', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      expect(rating.scaleStep.value).toBe(1)
    })

    it('DIM_RATE_008: scale settings read from config', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = { min: 2, max: 10, step: 2, labels: { '2': 'Bad', '10': 'Good' } }

      expect(rating.scaleMin.value).toBe(2)
      expect(rating.scaleMax.value).toBe(10)
      expect(rating.scaleStep.value).toBe(2)
      expect(rating.scaleLabels.value).toEqual({ '2': 'Bad', '10': 'Good' })
    })

    it('DIM_RATE_008b: scaleMin falls back to 1 for falsy min (0)', () => {
      // Note: config.value?.min || 1 treats 0 as falsy - this is existing behavior
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = { min: 0, max: 5, step: 1 }

      // 0 || 1 === 1 (falsy fallback in source)
      expect(rating.scaleMin.value).toBe(1)
    })
  })

  // ==================== Rating Value Management ====================

  describe('Rating Value Management', () => {
    it('DIM_RATE_009: setDimensionRating updates dimensionRatings', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [{ id: 'coherence', weight: 0.5 }, { id: 'fluency', weight: 0.5 }]
      }
      rating.autoSaveEnabled.value = false

      rating.setDimensionRating('coherence', 4)

      expect(rating.dimensionRatings.value.coherence).toBe(4)
    })

    it('DIM_RATE_010: setDimensionRating preserves other dimension values', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [{ id: 'coherence', weight: 0.5 }, { id: 'fluency', weight: 0.5 }]
      }
      rating.autoSaveEnabled.value = false

      rating.setDimensionRating('coherence', 4)
      rating.setDimensionRating('fluency', 3)

      expect(rating.dimensionRatings.value.coherence).toBe(4)
      expect(rating.dimensionRatings.value.fluency).toBe(3)
    })

    it('DIM_RATE_011: ratedDimensionCount tracks rated dimensions', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'coherence', weight: 0.5 },
          { id: 'fluency', weight: 0.5 }
        ]
      }
      rating.autoSaveEnabled.value = false

      expect(rating.ratedDimensionCount.value).toBe(0)

      rating.setDimensionRating('coherence', 4)
      expect(rating.ratedDimensionCount.value).toBe(1)

      rating.setDimensionRating('fluency', 3)
      expect(rating.ratedDimensionCount.value).toBe(2)
    })
  })

  // ==================== Weight Calculation & Overall Score ====================

  describe('Overall Score Computation', () => {
    it('DIM_RATE_012: overallScore is null with no ratings', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'coherence', weight: 0.5 },
          { id: 'fluency', weight: 0.5 }
        ]
      }

      expect(rating.overallScore.value).toBeNull()
    })

    it('DIM_RATE_013: overallScore computes weighted average', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'coherence', weight: 0.75 },
          { id: 'fluency', weight: 0.25 }
        ]
      }
      rating.autoSaveEnabled.value = false

      rating.setDimensionRating('coherence', 4) // 4 * 0.75 = 3.0
      rating.setDimensionRating('fluency', 2)   // 2 * 0.25 = 0.5

      // weighted average = 3.5 / 1.0 = 3.5
      expect(rating.overallScore.value).toBe(3.5)
    })

    it('DIM_RATE_014: overallScore with equal weights', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'a', weight: 1 },
          { id: 'b', weight: 1 },
          { id: 'c', weight: 1 }
        ]
      }
      rating.autoSaveEnabled.value = false

      rating.setDimensionRating('a', 3)
      rating.setDimensionRating('b', 4)
      rating.setDimensionRating('c', 5)

      // average = (3+4+5)/3 = 4.0
      expect(rating.overallScore.value).toBe(4)
    })

    it('DIM_RATE_015: overallScore with partial ratings', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'a', weight: 0.5 },
          { id: 'b', weight: 0.5 }
        ]
      }
      rating.autoSaveEnabled.value = false

      rating.setDimensionRating('a', 4)
      // Only 'a' is rated: 4 * 0.5 / 0.5 = 4.0
      expect(rating.overallScore.value).toBe(4)
    })

    it('DIM_RATE_016: overallScore uses default weight 1 when not specified', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'a' },  // No weight
          { id: 'b' }   // No weight
        ]
      }
      rating.autoSaveEnabled.value = false

      rating.setDimensionRating('a', 3)
      rating.setDimensionRating('b', 5)

      // Default weight 1: (3*1 + 5*1) / 2 = 4.0
      expect(rating.overallScore.value).toBe(4)
    })

    it('DIM_RATE_017: overallScore is null with no dimensions', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = { dimensions: [] }

      expect(rating.overallScore.value).toBeNull()
    })
  })

  // ==================== Validation (canSubmit) ====================

  describe('Validation', () => {
    it('DIM_RATE_018: canSubmit is false when no dimensions rated', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'coherence', weight: 0.5 },
          { id: 'fluency', weight: 0.5 }
        ]
      }

      expect(rating.canSubmit.value).toBe(false)
    })

    it('DIM_RATE_019: canSubmit is false when partially rated', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'coherence', weight: 0.5 },
          { id: 'fluency', weight: 0.5 }
        ]
      }
      rating.autoSaveEnabled.value = false

      rating.setDimensionRating('coherence', 4)

      expect(rating.canSubmit.value).toBe(false)
    })

    it('DIM_RATE_020: canSubmit is true when all dimensions rated', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'coherence', weight: 0.5 },
          { id: 'fluency', weight: 0.5 }
        ]
      }
      rating.autoSaveEnabled.value = false

      rating.setDimensionRating('coherence', 4)
      rating.setDimensionRating('fluency', 3)

      expect(rating.canSubmit.value).toBe(true)
    })

    it('DIM_RATE_021: canSubmit is true with empty dimensions array', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = { dimensions: [] }

      // every() on empty array returns true
      expect(rating.canSubmit.value).toBe(true)
    })
  })

  // ==================== Progress ====================

  describe('Progress', () => {
    it('DIM_RATE_022: progress tracks completed items', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.items.value = [
        { item_id: 1, evaluated: true },
        { item_id: 2, evaluated: false, status: 'Progressing' },
        { item_id: 3, evaluated: false }
      ]

      expect(rating.progress.value.total).toBe(3)
      expect(rating.progress.value.completed).toBe(1)
      expect(rating.progress.value.inProgress).toBe(1)
      expect(rating.progress.value.notStarted).toBe(1)
      expect(rating.progress.value.percent).toBe(33)
    })

    it('DIM_RATE_023: progress percent is 0 for empty items', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      expect(rating.progress.value.percent).toBe(0)
    })

    it('DIM_RATE_024: progress percent is 100 when all complete', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.items.value = [
        { item_id: 1, evaluated: true },
        { item_id: 2, evaluated: true }
      ]

      expect(rating.progress.value.percent).toBe(100)
    })
  })

  // ==================== Navigation ====================

  describe('Navigation', () => {
    it('DIM_RATE_025: hasNext is true when not at last item', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.items.value = [
        { item_id: 1 },
        { item_id: 2 }
      ]
      rating.currentItemIndex.value = 0

      expect(rating.hasNext.value).toBe(true)
    })

    it('DIM_RATE_026: hasNext is false at last item', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.items.value = [
        { item_id: 1 },
        { item_id: 2 }
      ]
      rating.currentItemIndex.value = 1

      expect(rating.hasNext.value).toBe(false)
    })

    it('DIM_RATE_027: hasPrev is false at first item', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.items.value = [{ item_id: 1 }, { item_id: 2 }]
      rating.currentItemIndex.value = 0

      expect(rating.hasPrev.value).toBe(false)
    })

    it('DIM_RATE_028: hasPrev is true when not at first item', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.items.value = [{ item_id: 1 }, { item_id: 2 }]
      rating.currentItemIndex.value = 1

      expect(rating.hasPrev.value).toBe(true)
    })

    it('DIM_RATE_029: findNextUnevaluated returns correct index', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.items.value = [
        { item_id: 1, evaluated: true },
        { item_id: 2, evaluated: true },
        { item_id: 3, evaluated: false }
      ]
      rating.currentItemIndex.value = 0

      expect(rating.findNextUnevaluated()).toBe(2)
    })

    it('DIM_RATE_030: findNextUnevaluated returns -1 when all evaluated', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.items.value = [
        { item_id: 1, evaluated: true },
        { item_id: 2, evaluated: true }
      ]
      rating.currentItemIndex.value = 0

      expect(rating.findNextUnevaluated()).toBe(-1)
    })
  })

  // ==================== Current Item Status ====================

  describe('Current Item Status', () => {
    it('DIM_RATE_031: currentItemStatus is pending when no item', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      expect(rating.currentItemStatus.value).toBe('pending')
    })

    it('DIM_RATE_032: currentItemStatus is done when item is evaluated', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.currentItem.value = { item_id: 1, evaluated: true, status: 'Done' }

      expect(rating.currentItemStatus.value).toBe('done')
    })

    it('DIM_RATE_033: currentItemStatus is done when all dimensions rated', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [{ id: 'a', weight: 1 }]
      }
      rating.currentItem.value = { item_id: 1, evaluated: false }
      rating.autoSaveEnabled.value = false
      rating.setDimensionRating('a', 5)

      expect(rating.currentItemStatus.value).toBe('done')
    })

    it('DIM_RATE_034: currentItemStatus is in_progress when partially rated', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.config.value = {
        dimensions: [
          { id: 'a', weight: 0.5 },
          { id: 'b', weight: 0.5 }
        ]
      }
      rating.currentItem.value = { item_id: 1, evaluated: false }
      rating.autoSaveEnabled.value = false
      rating.setDimensionRating('a', 3)

      expect(rating.currentItemStatus.value).toBe('in_progress')
    })
  })

  // ==================== Load Items ====================

  describe('Load Items', () => {
    it('DIM_RATE_035: loadItems calls config and items endpoints', async () => {
      const scenarioId = ref(42)
      const rating = useDimensionalRating(scenarioId)

      axios.get
        .mockResolvedValueOnce({ data: { config: { dimensions: [] } } })  // config
        .mockResolvedValueOnce({ data: { items: [{ item_id: 1 }] } })     // items
        .mockResolvedValueOnce({ data: { item: { item_id: 1 }, messages: [], content: '' } }) // loadItem

      await rating.loadItems()

      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/rating/42/config')
      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/rating/42/items')
    })

    it('DIM_RATE_036: loadItems sets error on failure', async () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      axios.get.mockRejectedValue({
        response: { data: { message: 'Server error' } }
      })

      await rating.loadItems()

      expect(rating.error.value).toBe('Server error')
      expect(rating.loading.value).toBe(false)
    })
  })

  // ==================== Submit Rating ====================

  describe('Submit Rating', () => {
    it('DIM_RATE_037: submitRating returns success result', async () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.currentItem.value = { item_id: 10 }
      rating.items.value = [{ item_id: 10, evaluated: false }]

      axios.post.mockResolvedValue({
        data: { rating: { status: 'Done', overall_score: 4.2 } }
      })

      const result = await rating.submitRating({ autoAdvance: false })

      expect(result.success).toBe(true)
      expect(result.rating.status).toBe('Done')
    })

    it('DIM_RATE_038: submitRating returns error on failure', async () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.currentItem.value = { item_id: 10 }

      axios.post.mockRejectedValue({
        response: { data: { message: 'Validation error' } }
      })

      const result = await rating.submitRating({ autoAdvance: false })

      expect(result.success).toBe(false)
      expect(result.error).toBe('Validation error')
    })

    it('DIM_RATE_039: submitRating returns error when no item selected', async () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      const result = await rating.submitRating()

      expect(result.success).toBe(false)
      expect(result.error).toBe('No item selected')
    })
  })

  // ==================== Reset ====================

  describe('Reset', () => {
    it('DIM_RATE_040: reset clears all state', () => {
      const scenarioId = ref(1)
      const rating = useDimensionalRating(scenarioId)

      rating.items.value = [{ item_id: 1 }]
      rating.currentItem.value = { item_id: 1 }
      rating.config.value = { dimensions: [] }
      rating.dimensionRatings.value = { a: 5 }
      rating.feedback.value = 'some feedback'
      rating.error.value = 'some error'

      rating.reset()

      expect(rating.items.value).toHaveLength(0)
      expect(rating.currentItem.value).toBeNull()
      expect(rating.config.value).toBeNull()
      expect(rating.dimensionRatings.value).toEqual({})
      expect(rating.feedback.value).toBe('')
      expect(rating.error.value).toBeNull()
    })
  })
})
