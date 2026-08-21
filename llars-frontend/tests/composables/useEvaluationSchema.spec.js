/**
 * useEvaluationSchema Composable Tests
 *
 * Tests for the schema-based evaluation data composable.
 * Test IDs: EVAL_SCHEMA_001 - EVAL_SCHEMA_035
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: vi.fn(() => ({
    locale: { value: 'de' }
  }))
}))

// Mock evaluationSchemas
vi.mock('@/schemas/evaluationSchemas', () => ({
  validateEvaluationData: vi.fn((data) => {
    if (!data || !data.type) {
      return {
        valid: false,
        errors: [{ message: 'Missing type field' }],
        warnings: []
      }
    }
    return { valid: true, errors: [], warnings: [] }
  }),
  isMultiGroupRanking: vi.fn((data) => {
    return data?.config?.mode === 'multi_group'
  }),
  getRankingGroups: vi.fn((data) => {
    return data?.config?.groups || []
  }),
  groupItemsByGroup: vi.fn((items) => {
    if (!items) return {}
    const grouped = {}
    items.forEach(item => {
      const group = item.group || 'default'
      if (!grouped[group]) grouped[group] = []
      grouped[group].push(item)
    })
    return grouped
  }),
  getLocalizedText: vi.fn((value, locale) => {
    if (typeof value === 'string') return value
    if (value && typeof value === 'object') return value[locale] || value.de || value.en || ''
    return ''
  }),
  EvaluationType: {
    RANKING: 'ranking',
    RATING: 'rating',
    MAIL_RATING: 'mail_rating',
    COMPARISON: 'comparison',
    AUTHENTICITY: 'authenticity',
    LABELING: 'labeling'
  },
  RankingMode: {
    SIMPLE: 'simple',
    MULTI_GROUP: 'multi_group'
  }
}))

import axios from 'axios'
import { validateEvaluationData } from '@/schemas/evaluationSchemas'

let useEvaluationSchema

describe('useEvaluationSchema Composable', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    const module = await import('@/composables/useEvaluationSchema')
    useEvaluationSchema = module.useEvaluationSchema
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('EVAL_SCHEMA_001: exports useEvaluationSchema function', () => {
      expect(typeof useEvaluationSchema).toBe('function')
    })

    it('EVAL_SCHEMA_002: returns all expected properties', () => {
      const result = useEvaluationSchema()

      // State
      expect(result).toHaveProperty('data')
      expect(result).toHaveProperty('error')
      expect(result).toHaveProperty('isLoading')

      // Validation
      expect(result).toHaveProperty('isValid')
      expect(result).toHaveProperty('errors')
      expect(result).toHaveProperty('warnings')

      // Computed
      expect(result).toHaveProperty('type')
      expect(result).toHaveProperty('schemaVersion')
      expect(result).toHaveProperty('reference')
      expect(result).toHaveProperty('items')
      expect(result).toHaveProperty('config')
      expect(result).toHaveProperty('groundTruth')

      // Ranking-specific
      expect(result).toHaveProperty('isMultiGroup')
      expect(result).toHaveProperty('groups')
      expect(result).toHaveProperty('groupedItems')
      expect(result).toHaveProperty('buckets')

      // Rating-specific
      expect(result).toHaveProperty('dimensions')
      expect(result).toHaveProperty('scale')

      // Type checks
      expect(result).toHaveProperty('isRanking')
      expect(result).toHaveProperty('isRating')
      expect(result).toHaveProperty('isMailRating')
      expect(result).toHaveProperty('isComparison')
      expect(result).toHaveProperty('isAuthenticity')
      expect(result).toHaveProperty('isLabeling')
      expect(result).toHaveProperty('isType')

      // Methods
      expect(result).toHaveProperty('setData')
      expect(result).toHaveProperty('clear')
      expect(result).toHaveProperty('fetchItem')
      expect(result).toHaveProperty('fetchItemsBatch')
      expect(result).toHaveProperty('fetchScenarioOverview')
      expect(result).toHaveProperty('localize')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('EVAL_SCHEMA_003: data is null initially', () => {
      const schema = useEvaluationSchema()

      expect(schema.data.value).toBeNull()
    })

    it('EVAL_SCHEMA_004: isValid is false initially', () => {
      const schema = useEvaluationSchema()

      expect(schema.isValid.value).toBe(false)
    })

    it('EVAL_SCHEMA_005: type is null initially', () => {
      const schema = useEvaluationSchema()

      expect(schema.type.value).toBeNull()
    })

    it('EVAL_SCHEMA_006: items is empty initially', () => {
      const schema = useEvaluationSchema()

      expect(schema.items.value).toEqual([])
    })

    it('EVAL_SCHEMA_007: isLoading is false initially', () => {
      const schema = useEvaluationSchema()

      expect(schema.isLoading.value).toBe(false)
    })
  })

  // ==================== setData - Schema Validation ====================

  describe('Schema Parsing and Validation', () => {
    it('EVAL_SCHEMA_008: setData validates and stores valid data', () => {
      const schema = useEvaluationSchema()

      const validData = {
        schema_version: '1.0',
        type: 'ranking',
        reference: { type: 'text', content: 'test' },
        items: [{ id: 'item_1', label: 'Item 1' }],
        config: { buckets: [] }
      }

      const result = schema.setData(validData)

      expect(result).toBe(true)
      expect(schema.isValid.value).toBe(true)
      expect(schema.data.value).toEqual(validData)
      expect(schema.error.value).toBeNull()
    })

    it('EVAL_SCHEMA_009: setData rejects invalid data', () => {
      const schema = useEvaluationSchema()

      const invalidData = { no_type: true }

      const result = schema.setData(invalidData)

      expect(result).toBe(false)
      expect(schema.isValid.value).toBe(false)
      expect(schema.error.value).toBeTruthy()
    })

    it('EVAL_SCHEMA_010: setData rejects null data', () => {
      const schema = useEvaluationSchema()

      const result = schema.setData(null)

      expect(result).toBe(false)
      expect(schema.isValid.value).toBe(false)
    })

    it('EVAL_SCHEMA_011: setData calls validateEvaluationData', () => {
      const schema = useEvaluationSchema()

      const data = { type: 'rating' }
      schema.setData(data)

      expect(validateEvaluationData).toHaveBeenCalledWith(data)
    })
  })

  // ==================== Schema Type Detection ====================

  describe('Schema Type Detection', () => {
    it('EVAL_SCHEMA_012: type computed from data', () => {
      const schema = useEvaluationSchema()

      schema.setData({ type: 'ranking', items: [] })

      expect(schema.type.value).toBe('ranking')
    })

    it('EVAL_SCHEMA_013: isRanking computed correctly', () => {
      const schema = useEvaluationSchema()

      schema.setData({ type: 'ranking', items: [] })

      expect(schema.isRanking.value).toBe(true)
      expect(schema.isRating.value).toBe(false)
    })

    it('EVAL_SCHEMA_014: isRating computed correctly', () => {
      const schema = useEvaluationSchema()

      schema.setData({ type: 'rating', items: [] })

      expect(schema.isRating.value).toBe(true)
      expect(schema.isRanking.value).toBe(false)
    })

    it('EVAL_SCHEMA_015: isComparison computed correctly', () => {
      const schema = useEvaluationSchema()

      schema.setData({ type: 'comparison', items: [] })

      expect(schema.isComparison.value).toBe(true)
    })

    it('EVAL_SCHEMA_016: isAuthenticity computed correctly', () => {
      const schema = useEvaluationSchema()

      schema.setData({ type: 'authenticity', items: [] })

      expect(schema.isAuthenticity.value).toBe(true)
    })

    it('EVAL_SCHEMA_017: isMailRating computed correctly', () => {
      const schema = useEvaluationSchema()

      schema.setData({ type: 'mail_rating', items: [] })

      expect(schema.isMailRating.value).toBe(true)
    })

    it('EVAL_SCHEMA_018: isLabeling computed correctly', () => {
      const schema = useEvaluationSchema()

      schema.setData({ type: 'labeling', items: [] })

      expect(schema.isLabeling.value).toBe(true)
    })

    it('EVAL_SCHEMA_019: isType method checks type', () => {
      const schema = useEvaluationSchema()

      schema.setData({ type: 'ranking', items: [] })

      expect(schema.isType('ranking')).toBe(true)
      expect(schema.isType('rating')).toBe(false)
    })
  })

  // ==================== Config Extraction ====================

  describe('Config Extraction', () => {
    it('EVAL_SCHEMA_020: config extracted from data', () => {
      const schema = useEvaluationSchema()

      const data = {
        type: 'ranking',
        items: [],
        config: { buckets: [{ id: 'good', name: 'Good' }], mode: 'simple' }
      }

      schema.setData(data)

      expect(schema.config.value).toEqual(data.config)
    })

    it('EVAL_SCHEMA_021: buckets extracted from ranking config', () => {
      const schema = useEvaluationSchema()

      schema.setData({
        type: 'ranking',
        items: [],
        config: {
          buckets: [
            { id: 'good', name: 'Good' },
            { id: 'bad', name: 'Bad' }
          ]
        }
      })

      expect(schema.buckets.value).toHaveLength(2)
      expect(schema.buckets.value[0].id).toBe('good')
    })

    it('EVAL_SCHEMA_022: dimensions extracted from rating config', () => {
      const schema = useEvaluationSchema()

      schema.setData({
        type: 'rating',
        items: [],
        config: {
          dimensions: [
            { id: 'coherence', name: 'Coherence', weight: 0.5 },
            { id: 'fluency', name: 'Fluency', weight: 0.5 }
          ]
        }
      })

      expect(schema.dimensions.value).toHaveLength(2)
    })

    it('EVAL_SCHEMA_023: scale extracted from rating config', () => {
      const schema = useEvaluationSchema()

      schema.setData({
        type: 'rating',
        items: [],
        config: {
          scale: { min: 1, max: 5, step: 1 }
        }
      })

      expect(schema.scale.value).toEqual({ min: 1, max: 5, step: 1 })
    })

    it('EVAL_SCHEMA_024: reference extracted from data', () => {
      const schema = useEvaluationSchema()

      schema.setData({
        type: 'ranking',
        items: [],
        reference: { type: 'text', label: 'Source', content: 'Test content' }
      })

      expect(schema.reference.value.type).toBe('text')
      expect(schema.reference.value.content).toBe('Test content')
    })

    it('EVAL_SCHEMA_025: schemaVersion extracted from data', () => {
      const schema = useEvaluationSchema()

      schema.setData({
        type: 'ranking',
        schema_version: '1.0',
        items: []
      })

      expect(schema.schemaVersion.value).toBe('1.0')
    })

    it('EVAL_SCHEMA_026: groundTruth extracted when present', () => {
      const schema = useEvaluationSchema()

      schema.setData({
        type: 'ranking',
        items: [],
        ground_truth: { correct_item: 'item_1' }
      })

      expect(schema.groundTruth.value).toEqual({ correct_item: 'item_1' })
    })
  })

  // ==================== Clear ====================

  describe('Clear', () => {
    it('EVAL_SCHEMA_027: clear resets all state', () => {
      const schema = useEvaluationSchema()

      schema.setData({ type: 'ranking', items: [] })

      expect(schema.isValid.value).toBe(true)

      schema.clear()

      expect(schema.data.value).toBeNull()
      expect(schema.error.value).toBeNull()
      expect(schema.isValid.value).toBe(false)
    })
  })

  // ==================== fetchItem ====================

  describe('Fetch Item', () => {
    it('EVAL_SCHEMA_028: fetchItem calls correct endpoint', async () => {
      const schema = useEvaluationSchema()

      axios.get.mockResolvedValue({
        data: { type: 'ranking', items: [] }
      })

      await schema.fetchItem(42, 10)

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios/42/items/10/schema')
    })

    it('EVAL_SCHEMA_029: fetchItem includes ground truth param', async () => {
      const schema = useEvaluationSchema()

      axios.get.mockResolvedValue({
        data: { type: 'ranking', items: [] }
      })

      await schema.fetchItem(42, 10, { includeGroundTruth: true })

      expect(axios.get).toHaveBeenCalledWith(
        '/api/scenarios/42/items/10/schema?include_ground_truth=true'
      )
    })

    it('EVAL_SCHEMA_030: fetchItem returns true on success', async () => {
      const schema = useEvaluationSchema()

      axios.get.mockResolvedValue({
        data: { type: 'ranking', items: [] }
      })

      const result = await schema.fetchItem(1, 1)

      expect(result).toBe(true)
      expect(schema.isLoading.value).toBe(false)
    })

    it('EVAL_SCHEMA_031: fetchItem sets error on failure', async () => {
      const schema = useEvaluationSchema()

      axios.get.mockRejectedValue({
        response: { data: { error: 'Not found' } }
      })

      const result = await schema.fetchItem(1, 999)

      expect(result).toBe(false)
      expect(schema.error.value).toBe('Not found')
      expect(schema.isLoading.value).toBe(false)
    })
  })

  // ==================== fetchItemsBatch ====================

  describe('Fetch Items Batch', () => {
    it('EVAL_SCHEMA_032: fetchItemsBatch calls batch endpoint', async () => {
      const schema = useEvaluationSchema()

      axios.post.mockResolvedValue({
        data: { items: [{ type: 'ranking' }] }
      })

      const result = await schema.fetchItemsBatch(42, [1, 2, 3])

      expect(axios.post).toHaveBeenCalledWith(
        '/api/scenarios/42/items/schema/batch',
        expect.objectContaining({
          item_ids: [1, 2, 3],
          include_ground_truth: false
        })
      )
      expect(result).toHaveLength(1)
    })

    it('EVAL_SCHEMA_033: fetchItemsBatch returns empty on error', async () => {
      const schema = useEvaluationSchema()

      axios.post.mockRejectedValue(new Error('Network error'))

      const result = await schema.fetchItemsBatch(42, [1, 2])

      expect(result).toEqual([])
      expect(schema.error.value).toBeTruthy()
    })
  })

  // ==================== fetchScenarioOverview ====================

  describe('Fetch Scenario Overview', () => {
    it('EVAL_SCHEMA_034: fetchScenarioOverview calls correct endpoint', async () => {
      const schema = useEvaluationSchema()

      axios.get.mockResolvedValue({
        data: { scenario: { id: 42 }, items_count: 10 }
      })

      const result = await schema.fetchScenarioOverview(42)

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios/42/schema')
      expect(result).toBeTruthy()
    })
  })

  // ==================== Localize ====================

  describe('Localize', () => {
    it('EVAL_SCHEMA_035: localize returns localized text', () => {
      const schema = useEvaluationSchema()

      const result = schema.localize({ de: 'Kohaerenz', en: 'Coherence' })

      expect(result).toBe('Kohaerenz')
    })
  })
})
