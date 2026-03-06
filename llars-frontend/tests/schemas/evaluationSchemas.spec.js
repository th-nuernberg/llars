/**
 * Evaluation Schemas Tests
 *
 * Tests for the unified evaluation data schemas used across LLARS.
 * Test IDs: SCHEMA_001 - SCHEMA_070
 */

import { describe, it, expect } from 'vitest'

import {
  SchemaVersion,
  EvaluationType,
  SourceType,
  ContentType,
  RankingMode,
  LabelingMode,
  FUNCTION_TYPE_MAP,
  EVALUATION_TYPE_TO_ID,
  createDefaultRankingBuckets,
  createDefaultScale,
  createDefaultRatingDimensions,
  createDefaultAuthenticityOptions,
  createSimpleRankingConfig,
  createRatingConfig,
  validateEvaluationData,
  isMultiGroupRanking,
  getRankingGroups,
  groupItemsByGroup,
  getLocalizedText
} from '@/schemas/evaluationSchemas'

// =============================================================================
// Enums / Constants
// =============================================================================

describe('evaluationSchemas - Enums & Constants', () => {
  it('SCHEMA_001: SchemaVersion contains V1_0', () => {
    expect(SchemaVersion.V1_0).toBe('1.0')
  })

  it('SCHEMA_002: SchemaVersion is frozen', () => {
    expect(Object.isFrozen(SchemaVersion)).toBe(true)
  })

  it('SCHEMA_003: EvaluationType contains all evaluation types', () => {
    expect(EvaluationType.RANKING).toBe('ranking')
    expect(EvaluationType.RATING).toBe('rating')
    expect(EvaluationType.MAIL_RATING).toBe('mail_rating')
    expect(EvaluationType.COMPARISON).toBe('comparison')
    expect(EvaluationType.AUTHENTICITY).toBe('authenticity')
    expect(EvaluationType.LABELING).toBe('labeling')
  })

  it('SCHEMA_004: EvaluationType is frozen', () => {
    expect(Object.isFrozen(EvaluationType)).toBe(true)
  })

  it('SCHEMA_005: EvaluationType has exactly 6 types', () => {
    expect(Object.keys(EvaluationType)).toHaveLength(6)
  })

  it('SCHEMA_006: SourceType contains human, llm, unknown', () => {
    expect(SourceType.HUMAN).toBe('human')
    expect(SourceType.LLM).toBe('llm')
    expect(SourceType.UNKNOWN).toBe('unknown')
  })

  it('SCHEMA_007: SourceType is frozen', () => {
    expect(Object.isFrozen(SourceType)).toBe(true)
  })

  it('SCHEMA_008: ContentType contains text and conversation', () => {
    expect(ContentType.TEXT).toBe('text')
    expect(ContentType.CONVERSATION).toBe('conversation')
  })

  it('SCHEMA_009: ContentType is frozen', () => {
    expect(Object.isFrozen(ContentType)).toBe(true)
  })

  it('SCHEMA_010: RankingMode contains simple and multi_group', () => {
    expect(RankingMode.SIMPLE).toBe('simple')
    expect(RankingMode.MULTI_GROUP).toBe('multi_group')
  })

  it('SCHEMA_011: RankingMode is frozen', () => {
    expect(Object.isFrozen(RankingMode)).toBe(true)
  })

  it('SCHEMA_012: LabelingMode contains single and multi', () => {
    expect(LabelingMode.SINGLE).toBe('single')
    expect(LabelingMode.MULTI).toBe('multi')
  })

  it('SCHEMA_013: LabelingMode is frozen', () => {
    expect(Object.isFrozen(LabelingMode)).toBe(true)
  })
})

describe('evaluationSchemas - FUNCTION_TYPE_MAP', () => {
  it('SCHEMA_014: maps function_type_id 1 to ranking', () => {
    expect(FUNCTION_TYPE_MAP[1]).toBe('ranking')
  })

  it('SCHEMA_015: maps function_type_id 2 to rating', () => {
    expect(FUNCTION_TYPE_MAP[2]).toBe('rating')
  })

  it('SCHEMA_016: maps function_type_id 3 to mail_rating', () => {
    expect(FUNCTION_TYPE_MAP[3]).toBe('mail_rating')
  })

  it('SCHEMA_017: maps function_type_id 4 to comparison', () => {
    expect(FUNCTION_TYPE_MAP[4]).toBe('comparison')
  })

  it('SCHEMA_018: maps function_type_id 5 to authenticity', () => {
    expect(FUNCTION_TYPE_MAP[5]).toBe('authenticity')
  })

  it('SCHEMA_019: maps function_type_id 7 to labeling', () => {
    expect(FUNCTION_TYPE_MAP[7]).toBe('labeling')
  })

  it('SCHEMA_020: does not map function_type_id 6', () => {
    expect(FUNCTION_TYPE_MAP[6]).toBeUndefined()
  })

  it('SCHEMA_021: is frozen', () => {
    expect(Object.isFrozen(FUNCTION_TYPE_MAP)).toBe(true)
  })
})

describe('evaluationSchemas - EVALUATION_TYPE_TO_ID', () => {
  it('SCHEMA_022: maps ranking to 1', () => {
    expect(EVALUATION_TYPE_TO_ID.ranking).toBe(1)
  })

  it('SCHEMA_023: maps rating to 2', () => {
    expect(EVALUATION_TYPE_TO_ID.rating).toBe(2)
  })

  it('SCHEMA_024: maps mail_rating to 3', () => {
    expect(EVALUATION_TYPE_TO_ID.mail_rating).toBe(3)
  })

  it('SCHEMA_025: maps comparison to 4', () => {
    expect(EVALUATION_TYPE_TO_ID.comparison).toBe(4)
  })

  it('SCHEMA_026: maps authenticity to 5', () => {
    expect(EVALUATION_TYPE_TO_ID.authenticity).toBe(5)
  })

  it('SCHEMA_027: maps labeling to 7', () => {
    expect(EVALUATION_TYPE_TO_ID.labeling).toBe(7)
  })

  it('SCHEMA_028: is frozen', () => {
    expect(Object.isFrozen(EVALUATION_TYPE_TO_ID)).toBe(true)
  })

  it('SCHEMA_029: FUNCTION_TYPE_MAP and EVALUATION_TYPE_TO_ID are inverse mappings', () => {
    for (const [id, type] of Object.entries(FUNCTION_TYPE_MAP)) {
      expect(EVALUATION_TYPE_TO_ID[type]).toBe(Number(id))
    }
    for (const [type, id] of Object.entries(EVALUATION_TYPE_TO_ID)) {
      expect(FUNCTION_TYPE_MAP[id]).toBe(type)
    }
  })
})

// =============================================================================
// Factory Functions
// =============================================================================

describe('evaluationSchemas - createDefaultRankingBuckets', () => {
  it('SCHEMA_030: returns 3 buckets', () => {
    const buckets = createDefaultRankingBuckets()
    expect(buckets).toHaveLength(3)
  })

  it('SCHEMA_031: buckets have correct ids', () => {
    const buckets = createDefaultRankingBuckets()
    expect(buckets.map(b => b.id)).toEqual(['good', 'moderate', 'poor'])
  })

  it('SCHEMA_032: each bucket has localized labels (de/en)', () => {
    const buckets = createDefaultRankingBuckets()
    for (const bucket of buckets) {
      expect(bucket.label).toHaveProperty('de')
      expect(bucket.label).toHaveProperty('en')
      expect(typeof bucket.label.de).toBe('string')
      expect(typeof bucket.label.en).toBe('string')
    }
  })

  it('SCHEMA_033: each bucket has a hex color', () => {
    const buckets = createDefaultRankingBuckets()
    for (const bucket of buckets) {
      expect(bucket.color).toMatch(/^#[0-9a-fA-F]{6}$/)
    }
  })

  it('SCHEMA_034: buckets are ordered 1, 2, 3', () => {
    const buckets = createDefaultRankingBuckets()
    expect(buckets.map(b => b.order)).toEqual([1, 2, 3])
  })

  it('SCHEMA_035: returns a new array on each call', () => {
    const a = createDefaultRankingBuckets()
    const b = createDefaultRankingBuckets()
    expect(a).not.toBe(b)
    expect(a).toEqual(b)
  })
})

describe('evaluationSchemas - createDefaultScale', () => {
  it('SCHEMA_036: returns scale with min=1 and max=5', () => {
    const scale = createDefaultScale()
    expect(scale.min).toBe(1)
    expect(scale.max).toBe(5)
  })

  it('SCHEMA_037: returns scale with step=1', () => {
    const scale = createDefaultScale()
    expect(scale.step).toBe(1)
  })

  it('SCHEMA_038: has labels for values 1 through 5', () => {
    const scale = createDefaultScale()
    expect(Object.keys(scale.labels)).toHaveLength(5)
    for (let i = 1; i <= 5; i++) {
      expect(scale.labels[String(i)]).toBeDefined()
      expect(scale.labels[String(i)]).toHaveProperty('de')
      expect(scale.labels[String(i)]).toHaveProperty('en')
    }
  })

  it('SCHEMA_039: returns a new object on each call', () => {
    const a = createDefaultScale()
    const b = createDefaultScale()
    expect(a).not.toBe(b)
    expect(a).toEqual(b)
  })
})

describe('evaluationSchemas - createDefaultRatingDimensions', () => {
  it('SCHEMA_040: returns 4 dimensions', () => {
    const dims = createDefaultRatingDimensions()
    expect(dims).toHaveLength(4)
  })

  it('SCHEMA_041: contains coherence, fluency, relevance, consistency', () => {
    const dims = createDefaultRatingDimensions()
    const ids = dims.map(d => d.id)
    expect(ids).toEqual(['coherence', 'fluency', 'relevance', 'consistency'])
  })

  it('SCHEMA_042: all dimensions have localized labels', () => {
    const dims = createDefaultRatingDimensions()
    for (const dim of dims) {
      expect(dim.label).toHaveProperty('de')
      expect(dim.label).toHaveProperty('en')
    }
  })

  it('SCHEMA_043: all dimensions have descriptions', () => {
    const dims = createDefaultRatingDimensions()
    for (const dim of dims) {
      expect(dim.description).toHaveProperty('de')
      expect(dim.description).toHaveProperty('en')
    }
  })

  it('SCHEMA_044: weights sum to 1.0', () => {
    const dims = createDefaultRatingDimensions()
    const total = dims.reduce((sum, d) => sum + d.weight, 0)
    expect(total).toBeCloseTo(1.0)
  })

  it('SCHEMA_045: each weight is 0.25', () => {
    const dims = createDefaultRatingDimensions()
    for (const dim of dims) {
      expect(dim.weight).toBe(0.25)
    }
  })
})

describe('evaluationSchemas - createDefaultAuthenticityOptions', () => {
  it('SCHEMA_046: returns 2 options', () => {
    const opts = createDefaultAuthenticityOptions()
    expect(opts).toHaveLength(2)
  })

  it('SCHEMA_047: contains human and ai options', () => {
    const opts = createDefaultAuthenticityOptions()
    expect(opts[0].id).toBe('human')
    expect(opts[1].id).toBe('ai')
  })

  it('SCHEMA_048: options have localized labels', () => {
    const opts = createDefaultAuthenticityOptions()
    for (const opt of opts) {
      expect(opt.label).toHaveProperty('de')
      expect(opt.label).toHaveProperty('en')
    }
  })
})

describe('evaluationSchemas - createSimpleRankingConfig', () => {
  it('SCHEMA_049: returns config with mode=simple', () => {
    const config = createSimpleRankingConfig()
    expect(config.mode).toBe('simple')
  })

  it('SCHEMA_050: uses default buckets when no options provided', () => {
    const config = createSimpleRankingConfig()
    expect(config.buckets).toHaveLength(3)
    expect(config.buckets[0].id).toBe('good')
  })

  it('SCHEMA_051: defaults allowTies to true', () => {
    const config = createSimpleRankingConfig()
    expect(config.allowTies).toBe(true)
  })

  it('SCHEMA_052: defaults requireComplete to true', () => {
    const config = createSimpleRankingConfig()
    expect(config.requireComplete).toBe(true)
  })

  it('SCHEMA_053: accepts custom buckets', () => {
    const customBuckets = [{ id: 'a', label: { de: 'A', en: 'A' }, color: '#000', order: 1 }]
    const config = createSimpleRankingConfig({ buckets: customBuckets })
    expect(config.buckets).toBe(customBuckets)
    expect(config.buckets).toHaveLength(1)
  })

  it('SCHEMA_054: allows disabling ties', () => {
    const config = createSimpleRankingConfig({ allowTies: false })
    expect(config.allowTies).toBe(false)
  })

  it('SCHEMA_055: allows disabling requireComplete', () => {
    const config = createSimpleRankingConfig({ requireComplete: false })
    expect(config.requireComplete).toBe(false)
  })
})

describe('evaluationSchemas - createRatingConfig', () => {
  it('SCHEMA_056: returns config with default scale', () => {
    const config = createRatingConfig()
    expect(config.scale.min).toBe(1)
    expect(config.scale.max).toBe(5)
  })

  it('SCHEMA_057: returns config with default dimensions', () => {
    const config = createRatingConfig()
    expect(config.dimensions).toHaveLength(4)
  })

  it('SCHEMA_058: defaults showOverall to true', () => {
    const config = createRatingConfig()
    expect(config.showOverall).toBe(true)
  })

  it('SCHEMA_059: accepts custom scale', () => {
    const customScale = { min: 0, max: 10, step: 2, labels: {} }
    const config = createRatingConfig({ scale: customScale })
    expect(config.scale).toBe(customScale)
  })

  it('SCHEMA_060: accepts custom dimensions', () => {
    const dims = [{ id: 'quality', label: { de: 'Qualitaet', en: 'Quality' }, weight: 1.0 }]
    const config = createRatingConfig({ dimensions: dims })
    expect(config.dimensions).toBe(dims)
  })

  it('SCHEMA_061: allows disabling showOverall', () => {
    const config = createRatingConfig({ showOverall: false })
    expect(config.showOverall).toBe(false)
  })
})

// =============================================================================
// Validation
// =============================================================================

describe('evaluationSchemas - validateEvaluationData', () => {
  const validData = {
    schema_version: '1.0',
    type: 'ranking',
    items: [
      { id: 'item_1', label: 'Item 1', source: { type: 'human' }, content: 'Text A' },
      { id: 'item_2', label: 'Item 2', source: { type: 'llm' }, content: 'Text B' }
    ],
    config: { mode: 'simple', buckets: [] }
  }

  it('SCHEMA_062: valid data returns valid=true and no errors', () => {
    const result = validateEvaluationData(validData)
    expect(result.valid).toBe(true)
    expect(result.errors).toHaveLength(0)
  })

  it('SCHEMA_063: null data returns valid=false with root error', () => {
    const result = validateEvaluationData(null)
    expect(result.valid).toBe(false)
    expect(result.errors).toEqual([{ field: 'root', message: 'Data is required' }])
  })

  it('SCHEMA_064: undefined data returns valid=false with root error', () => {
    const result = validateEvaluationData(undefined)
    expect(result.valid).toBe(false)
    expect(result.errors[0].field).toBe('root')
  })

  it('SCHEMA_065: missing schema_version produces error', () => {
    const data = { ...validData, schema_version: '' }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'schema_version')).toBe(true)
  })

  it('SCHEMA_066: missing type produces error', () => {
    const data = { ...validData, type: '' }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'type')).toBe(true)
  })

  it('SCHEMA_067: invalid type produces error', () => {
    const data = { ...validData, type: 'nonexistent_type' }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'type' && e.message.includes('Invalid type'))).toBe(true)
  })

  it('SCHEMA_068: missing items produces error', () => {
    const data = { ...validData, items: undefined }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'items')).toBe(true)
  })

  it('SCHEMA_069: non-array items produces error', () => {
    const data = { ...validData, items: 'not-an-array' }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'items')).toBe(true)
  })

  it('SCHEMA_070: empty items array produces warning', () => {
    const data = { ...validData, items: [] }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(true)
    expect(result.warnings).toHaveLength(1)
    expect(result.warnings[0].field).toBe('items')
  })

  it('SCHEMA_071: item missing id produces error', () => {
    const data = {
      ...validData,
      items: [{ label: 'X', source: { type: 'human' }, content: 'text' }]
    }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'items[0].id')).toBe(true)
  })

  it('SCHEMA_072: item missing label produces error', () => {
    const data = {
      ...validData,
      items: [{ id: 'item_1', source: { type: 'human' }, content: 'text' }]
    }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'items[0].label')).toBe(true)
  })

  it('SCHEMA_073: item missing source produces error', () => {
    const data = {
      ...validData,
      items: [{ id: 'item_1', label: 'X', content: 'text' }]
    }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'items[0].source')).toBe(true)
  })

  it('SCHEMA_074: item with null content produces error', () => {
    const data = {
      ...validData,
      items: [{ id: 'item_1', label: 'X', source: { type: 'human' }, content: null }]
    }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'items[0].content')).toBe(true)
  })

  it('SCHEMA_075: item with undefined content produces error', () => {
    const data = {
      ...validData,
      items: [{ id: 'item_1', label: 'X', source: { type: 'human' } }]
    }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'items[0].content')).toBe(true)
  })

  it('SCHEMA_076: item label containing source name produces warning', () => {
    const data = {
      ...validData,
      items: [
        { id: 'item_1', label: 'GPT-4 Summary', source: { type: 'llm', name: 'GPT-4' }, content: 'text' }
      ]
    }
    const result = validateEvaluationData(data)
    expect(result.warnings.some(w => w.field === 'items[0].label')).toBe(true)
  })

  it('SCHEMA_077: item label NOT containing source name produces no warning', () => {
    const data = {
      ...validData,
      items: [
        { id: 'item_1', label: 'Summary 1', source: { type: 'llm', name: 'GPT-4' }, content: 'text' }
      ]
    }
    const result = validateEvaluationData(data)
    expect(result.warnings.filter(w => w.field === 'items[0].label')).toHaveLength(0)
  })

  it('SCHEMA_078: missing config produces error', () => {
    const data = { ...validData, config: undefined }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'config')).toBe(true)
  })

  it('SCHEMA_079: validates multiple items independently', () => {
    const data = {
      ...validData,
      items: [
        { id: 'item_1', label: 'X', source: { type: 'human' }, content: 'text' },
        { label: 'Y', source: { type: 'human' }, content: 'text' }, // missing id
        { id: 'item_3', source: { type: 'human' }, content: 'text' } // missing label
      ]
    }
    const result = validateEvaluationData(data)
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.field === 'items[1].id')).toBe(true)
    expect(result.errors.some(e => e.field === 'items[2].label')).toBe(true)
  })

  it('SCHEMA_080: empty string content is allowed', () => {
    const data = {
      ...validData,
      items: [{ id: 'item_1', label: 'X', source: { type: 'human' }, content: '' }]
    }
    const result = validateEvaluationData(data)
    // empty string is not null/undefined, so no content error
    expect(result.errors.filter(e => e.field.includes('content'))).toHaveLength(0)
  })
})

// =============================================================================
// Helper Functions
// =============================================================================

describe('evaluationSchemas - isMultiGroupRanking', () => {
  it('SCHEMA_081: returns true for multi_group mode', () => {
    const data = { config: { mode: 'multi_group' } }
    expect(isMultiGroupRanking(data)).toBe(true)
  })

  it('SCHEMA_082: returns false for simple mode', () => {
    const data = { config: { mode: 'simple' } }
    expect(isMultiGroupRanking(data)).toBe(false)
  })

  it('SCHEMA_083: returns false for null data', () => {
    expect(isMultiGroupRanking(null)).toBe(false)
  })

  it('SCHEMA_084: returns false for missing config', () => {
    expect(isMultiGroupRanking({})).toBe(false)
  })

  it('SCHEMA_085: returns false for undefined', () => {
    expect(isMultiGroupRanking(undefined)).toBe(false)
  })
})

describe('evaluationSchemas - getRankingGroups', () => {
  it('SCHEMA_086: returns groups from multi_group config', () => {
    const groups = [{ id: 'g1', label: { de: 'G1', en: 'G1' }, buckets: [] }]
    const data = { config: { mode: 'multi_group', groups } }
    expect(getRankingGroups(data)).toBe(groups)
  })

  it('SCHEMA_087: returns empty array for simple mode', () => {
    const data = { config: { mode: 'simple' } }
    expect(getRankingGroups(data)).toEqual([])
  })

  it('SCHEMA_088: returns empty array when groups missing in multi_group config', () => {
    const data = { config: { mode: 'multi_group' } }
    expect(getRankingGroups(data)).toEqual([])
  })

  it('SCHEMA_089: returns empty array for null data', () => {
    expect(getRankingGroups(null)).toEqual([])
  })
})

describe('evaluationSchemas - groupItemsByGroup', () => {
  it('SCHEMA_090: groups items by group field', () => {
    const items = [
      { id: '1', group: 'a' },
      { id: '2', group: 'b' },
      { id: '3', group: 'a' }
    ]
    const result = groupItemsByGroup(items)
    expect(Object.keys(result)).toEqual(['a', 'b'])
    expect(result.a).toHaveLength(2)
    expect(result.b).toHaveLength(1)
  })

  it('SCHEMA_091: items without group go to default', () => {
    const items = [
      { id: '1' },
      { id: '2', group: 'a' }
    ]
    const result = groupItemsByGroup(items)
    expect(result.default).toHaveLength(1)
    expect(result.a).toHaveLength(1)
  })

  it('SCHEMA_092: returns empty object for null items', () => {
    expect(groupItemsByGroup(null)).toEqual({})
  })

  it('SCHEMA_093: returns empty object for undefined items', () => {
    expect(groupItemsByGroup(undefined)).toEqual({})
  })

  it('SCHEMA_094: handles empty array', () => {
    expect(groupItemsByGroup([])).toEqual({})
  })

  it('SCHEMA_095: all items without group go to default', () => {
    const items = [{ id: '1' }, { id: '2' }]
    const result = groupItemsByGroup(items)
    expect(Object.keys(result)).toEqual(['default'])
    expect(result.default).toHaveLength(2)
  })
})

describe('evaluationSchemas - getLocalizedText', () => {
  it('SCHEMA_096: returns German text by default', () => {
    const val = { de: 'Hallo', en: 'Hello' }
    expect(getLocalizedText(val)).toBe('Hallo')
  })

  it('SCHEMA_097: returns English text when locale=en', () => {
    const val = { de: 'Hallo', en: 'Hello' }
    expect(getLocalizedText(val, 'en')).toBe('Hello')
  })

  it('SCHEMA_098: returns plain string as-is', () => {
    expect(getLocalizedText('plain text')).toBe('plain text')
  })

  it('SCHEMA_099: returns empty string for null', () => {
    expect(getLocalizedText(null)).toBe('')
  })

  it('SCHEMA_100: returns empty string for undefined', () => {
    expect(getLocalizedText(undefined)).toBe('')
  })

  it('SCHEMA_101: falls back to de when requested locale missing', () => {
    const val = { de: 'Hallo' }
    expect(getLocalizedText(val, 'fr')).toBe('Hallo')
  })

  it('SCHEMA_102: falls back to en when de and requested locale missing', () => {
    const val = { en: 'Hello' }
    expect(getLocalizedText(val, 'fr')).toBe('Hello')
  })

  it('SCHEMA_103: returns empty string when no locales match', () => {
    const val = {}
    expect(getLocalizedText(val, 'fr')).toBe('')
  })

  it('SCHEMA_104: returns empty string for empty string input', () => {
    expect(getLocalizedText('')).toBe('')
  })
})
